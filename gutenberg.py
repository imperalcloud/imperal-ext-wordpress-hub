"""Explicit block content -> Gutenberg block markup.

Ported from WP Publisher's content renderer. This module is deliberately
document-agnostic: it turns a list of {type, text, level} blocks the CALLER
already decided on into post_content — no heuristics, no document parsing.
Anything about interpreting an input file stays out of scope here.
"""

from __future__ import annotations

import html
import json
import re
from urllib.parse import urlparse


# Matches markdown-style [anchor text](url) so callers can embed a REAL link
# inside paragraph/heading text -- without this, block text was always passed
# whole into html.escape(), so an <a href="..."> written directly into a
# block's text field got escaped into visible literal text like
# "&lt;a href=...&gt;" instead of ever becoming a clickable link. This was a
# real gap: nothing in this module could render an internal link, an external
# citation link, or a CTA link inside article body text -- only inside a
# separate image caption. The markdown syntax is deliberately narrow (no raw
# HTML passthrough) so the rest of the text is still safely escaped.
_INLINE_LINK_RE = re.compile(r"\[([^\]\[]+)\]\((https?://[^\s()]+)\)")


def _registrable_domain(url_or_domain: str) -> str:
    """Normalise a URL or bare domain to a comparable host: strip scheme,
    'www.' prefix, port and trailing slash, lowercase. Used ONLY to decide
    same-site vs external -- not a full public-suffix-list eTLD+1 parse,
    which this pipeline has never needed (site domains are known, single
    connected sites, not arbitrary third-party URLs)."""
    if not url_or_domain:
        return ""
    parsed = urlparse(url_or_domain if "://" in url_or_domain else f"//{url_or_domain}")
    host = (parsed.netloc or parsed.path or "").lower()
    host = host.split(":")[0]  # drop a port if present
    if host.startswith("www."):
        host = host[4:]
    return host


def _is_external_link(url: str, site_domain: str | None) -> bool:
    """A link is external when its host differs from the connected site's own
    host. Without a site_domain (no caller passed one) nothing can be judged
    external, so callers that skip it get the old plain-link behaviour."""
    if not site_domain:
        return False
    return _registrable_domain(url) != _registrable_domain(site_domain)


# Inline emphasis an article's Markdown carries (Article Writer's export uses all three). Each pattern runs on
# text that is ALREADY html-escaped, so the only tags that can appear are the ones written here.
_CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
_STRONG_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_EM_RE = re.compile(r"(?<![\*\w])\*(?=[^\s*])([^*\n]*?[^\s*])\*(?![\*\w])")


def _render_inline_marks(escaped: str) -> str:
    """``**bold**`` -> <strong>, ``*italic*`` -> <em>, `` `code` `` -> <code>, on text that is already
    html-escaped. Before this, the markers went to the page as they were: a published article showed literal
    ``**Primary Strength:**`` (live 2026-11-26, post 2248: 40 raw ``**`` and not one <strong>). What stands inside
    a code span is left exactly as written."""
    def marks(part: str) -> str:
        part = _STRONG_RE.sub(r"<strong>\1</strong>", part)
        return _EM_RE.sub(r"<em>\1</em>", part)
    out, last = [], 0
    for match in _CODE_SPAN_RE.finditer(escaped):
        out.append(marks(escaped[last:match.start()]))
        out.append(f"<code>{match.group(1)}</code>")
        last = match.end()
    out.append(marks(escaped[last:]))
    return "".join(out)


def _render_inline_links(text: str, site_domain: str | None = None) -> str:
    """Escape ``text`` for safe HTML output, EXCEPT for [anchor](https://url)
    spans, which become real <a href> tags with the anchor text and URL each
    individually escaped. Anything that isn't inside that exact syntax is
    escaped exactly as before -- this is additive, not a relaxation of the
    existing escaping guarantee.

    Pipeline rule (applies to every article published through this module):
    a link whose host differs from the connected site's own host -- i.e. an
    external link -- always opens in a new tab and is marked nofollow. This
    keeps the reader on the site's own tab and never hands page-rank equity
    to a destination this pipeline doesn't control or vet per-link. A link
    to the site's own domain is a normal, followed, same-tab link.
    """
    # Each link is set aside behind a placeholder first, so emphasis can be read across the WHOLE text -- a bold
    # that wraps a link (``**[anchor](url)**``) is one bold, not two stray pairs of asterisks around a link.
    links: list[str] = []

    def keep(match) -> str:
        anchor_text, url = match.group(1), match.group(2)
        escaped_url = html.escape(url, quote=True)
        escaped_anchor = _render_inline_marks(html.escape(anchor_text))
        if _is_external_link(url, site_domain):
            links.append(
                f'<a href="{escaped_url}" target="_blank" '
                f'rel="nofollow noopener noreferrer">{escaped_anchor}</a>'
            )
        else:
            links.append(f'<a href="{escaped_url}">{escaped_anchor}</a>')
        return f"\x00{len(links) - 1}\x00"

    held = _INLINE_LINK_RE.sub(keep, text.replace("\x00", ""))
    rendered = _render_inline_marks(html.escape(held))
    return re.sub(r"\x00(\d+)\x00", lambda m: links[int(m.group(1))], rendered)


def paragraph_block(text: str, site_domain: str | None = None) -> str:
    return f"<!-- wp:paragraph --><p>{_render_inline_links(text, site_domain)}</p><!-- /wp:paragraph -->"


def heading_block(text: str, level: int = 2, site_domain: str | None = None) -> str:
    escaped = _render_inline_links(text, site_domain)
    return (
        f'<!-- wp:heading {{"level":{level}}} -->'
        f'<h{level} class="wp-block-heading">{escaped}</h{level}>'
        f"<!-- /wp:heading -->"
    )


def list_block(items, ordered: bool = False, site_domain: str | None = None) -> str:
    """A real Gutenberg list: one ``wp:list`` holding a ``wp:list-item`` per item. Before this a bullet was its
    own paragraph, so a published article had no list at all (live 2026-11-26, post 2248: 0 <ul>, 0 <li>)."""
    rendered = "".join(
        f"<!-- wp:list-item --><li>{_render_inline_links(str(item), site_domain)}</li><!-- /wp:list-item -->"
        for item in (items or []) if str(item or "").strip())
    if not rendered:
        return ""
    tag, attrs = ("ol", ' {"ordered":true}') if ordered else ("ul", "")
    return f'<!-- wp:list{attrs} --><{tag} class="wp-block-list">{rendered}</{tag}><!-- /wp:list -->'


def table_block(rows, header: bool = True, site_domain: str | None = None) -> str:
    """A real Gutenberg table from rows of cell texts; the first row is the head when ``header``. Cell text goes
    through the same escaping and inline rendering as a paragraph -- no HTML is ever taken from the caller."""
    rows = [[str(c or "") for c in row] for row in (rows or []) if row]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]

    def line(cells, tag: str) -> str:
        return "<tr>" + "".join(f"<{tag}>{_render_inline_links(c.strip(), site_domain)}</{tag}>" for c in cells) + "</tr>"
    head = f"<thead>{line(rows[0], 'th')}</thead>" if header and len(rows) > 1 else ""
    body_rows = rows[1:] if head else rows
    body = "<tbody>" + "".join(line(r, "td") for r in body_rows) + "</tbody>"
    return ('<!-- wp:table --><figure class="wp-block-table"><table class="has-fixed-layout">'
            f"{head}{body}</table></figure><!-- /wp:table -->")


def image_block(media_id: int, media_url: str, alt: str = "", caption: str | None = None) -> str:
    """Gutenberg image block referencing an existing media library attachment.

    ``media_id``/``media_url`` come from a prior upload_media call — this
    function never fetches or uploads anything itself, it only renders markup
    that points at an attachment WordPress already has.
    """
    alt_attr = html.escape(alt, quote=True)
    figure = (
        f'<!-- wp:image {{"id":{media_id},"sizeSlug":"large","linkDestination":"none"}} -->'
        f'<figure class="wp-block-image size-large">'
        f'<img src="{html.escape(media_url, quote=True)}" alt="{alt_attr}" class="wp-image-{media_id}"/>'
    )
    if caption and caption.strip():
        figure += f"<figcaption class=\"wp-element-caption\">{html.escape(caption)}</figcaption>"
    figure += "</figure><!-- /wp:image -->"
    return figure


def faq_block(items, intro_text: str = "") -> str:
    """Render a visible Q&A list PLUS a FAQPage JSON-LD <script> block.

    Deliberately NOT the Rank Math proprietary `wp:rank-math/faq-block` --
    that markup is undocumented and site-specific (depends on exact plugin
    version). Standard schema.org JSON-LD works identically on every
    WordPress site regardless of which SEO plugin (or none) is installed,
    and is exactly what Google's rich-result parser reads. ``items`` is a
    list of {question, answer} dicts or PostBlockInput-style objects.
    """
    def _fields(item):
        if isinstance(item, dict):
            return item.get("question") or "", item.get("answer") or ""
        return getattr(item, "question", "") or "", getattr(item, "answer", "") or ""

    pairs = [(_fields(i)[0].strip(), _fields(i)[1].strip()) for i in (items or [])]
    pairs = [(q, a) for q, a in pairs if q and a]
    if not pairs:
        return ""

    visible = []
    if intro_text and intro_text.strip():
        visible.append(f"<p>{html.escape(intro_text.strip())}</p>")
    for q, a in pairs:
        visible.append(
            f"<h3 class=\"wp-block-heading\">{html.escape(q)}</h3>"
            f"<p>{html.escape(a)}</p>"
        )
    visible_html = (
        '<!-- wp:html -->'
        f'<div class="imperal-faq">{"".join(visible)}</div>'
        '<!-- /wp:html -->'
    )

    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in pairs
        ],
    }
    schema_html = (
        '<!-- wp:html -->'
        f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'
        '<!-- /wp:html -->'
    )
    return visible_html + schema_html


def _block_fields(block) -> tuple[str, str, int, int | None, str | None, str | None, list]:
    """Read {type, text, level, media_id, media_url, caption, faq_items} off a dict or pydantic model."""
    if isinstance(block, dict):
        return (block.get("type") or "paragraph", block.get("text") or "", block.get("level") or 2,
                block.get("media_id"), block.get("media_url"), block.get("caption"),
                block.get("faq_items") or [])
    return (getattr(block, "type", "paragraph") or "paragraph",
            getattr(block, "text", "") or "",
            getattr(block, "level", 2) or 2,
            getattr(block, "media_id", None),
            getattr(block, "media_url", None),
            getattr(block, "caption", None),
            getattr(block, "faq_items", None) or [])


def _block_extra(block, name: str, default):
    """One more field off a dict or pydantic block (the list / table fields ``_block_fields`` does not carry)."""
    value = block.get(name) if isinstance(block, dict) else getattr(block, name, None)
    return default if value is None else value


_HEADING_LINE_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_BULLET_LINE_RE = re.compile(r"^[-*+]\s+(.*\S)\s*$")
_ORDERED_LINE_RE = re.compile(r"^\d{1,3}[.)]\s+(.*\S)\s*$")
_TABLE_LINE_RE = re.compile(r"^\|(.+)\|\s*$")
_TABLE_RULE_CELL_RE = re.compile(r"^:?-{1,}:?$")


def _table_cells(line: str) -> list[str]:
    return [c.strip() for c in _TABLE_LINE_RE.match(line).group(1).split("|")]

# POST-CHECK: Article Writer's own authoring template uses bare scaffolding
# labels ("Intro", "CTA", their translations) as section markers while it is
# drafting -- they are meta-labels for the WRITER, never real article
# headings meant for a reader. Left in place they end up as a visible,
# meaningless <h2>Intro</h2> or <h2>CTA</h2> on the published page. This is
# deliberately an EXACT (not substring) match against the whole heading
# text, case-insensitive, so a real heading that merely happens to mention
# "cta" or start a sentence with "Introducere" (a full, real title) is never
# stripped -- only a heading whose ENTIRE text is one of these known
# scaffolding labels is dropped. Covers the two Article Writer sites in use
# (RO/RU) plus English/generic; safe to extend if a new label surfaces.
_SCAFFOLDING_HEADING_LABELS = {
    "intro", "introduction", "introducere", "введение", "вступление",
    "cta", "call to action", "apel la actiune", "apel la acțiune",
    "призыв к действию",
}


def _is_scaffolding_heading(text: str) -> bool:
    normalized = (text or "").strip().strip(":").strip().lower()
    return normalized in _SCAFFOLDING_HEADING_LABELS


def strip_scaffolding_headings(blocks: list | None) -> list:
    """Drop any heading block whose text is EXACTLY a known writer-template
    scaffolding label ("Intro", "CTA", ...) -- see
    _SCAFFOLDING_HEADING_LABELS for the exact, deliberately narrow rule.

    Only the heading itself is removed; the paragraph(s) that followed it
    (the real intro/CTA copy) are kept as ordinary content. Mandatory
    post-check run by create_post/update_post on every markdown-derived (and
    explicitly given) block list, so a published article never carries a
    bare, meaningless "Intro" or "CTA" heading regardless of which pipeline
    stage produced the blocks.
    """
    if not blocks:
        return blocks or []
    cleaned = []
    for block in blocks:
        block_type, text, level, media_id, media_url, caption, faq_items = _block_fields(block)
        if block_type == "heading" and _is_scaffolding_heading(text):
            continue
        cleaned.append(block)
    return cleaned


def markdown_to_blocks(markdown_text: str, *, skip_h1: bool = True) -> list[dict]:
    """Deterministically convert full article Markdown (Article Writer's own
    export shape: '# Title', '## Heading', blank-line-separated paragraphs,
    '- ' bullets, inline [anchor](url) links) into the {type, text, level}
    block dicts create_post/update_post expect.

    THIS is the missing pipeline link that caused internal/external/CTA links
    written correctly as markdown in an article (e.g. by Article Writer) to
    end up as plain 'anchor text (https://...)' on the live page instead of
    a real <a href>: without an automated converter, turning an article's
    markdown into create_post's blocks[] required a human (or an LLM) to
    manually retype each line into a block -- an error-prone step that can
    silently drop the [anchor](url) bracket syntax gutenberg.py already knows
    how to render. This function removes that manual step entirely: every
    [anchor](url) span in the source Markdown is passed through UNCHANGED
    into the resulting block's text, so blocks_to_content's existing inline-
    link rendering (see _render_inline_links) turns it into a real hyperlink
    with no re-typing involved.

    skip_h1=True (the default) drops the article's leading '# Title' line --
    matching the existing WordPress Hub convention that the H1 is the post's
    title field, not part of post_content.

    Consecutive bullet lines ('- item') become ONE list block {type: "list", items, ordered: False}; consecutive
    numbered lines ('1. item') one ordered list; consecutive pipe-table lines one table block {type: "table",
    rows, header} (header is True when the second line is the '|---|' rule, which is then dropped). Inline
    emphasis ('**bold**', '*italic*', '`code`') stays in the text exactly as written and is rendered by
    blocks_to_content, the same way an inline link is.

    Until 2026-11 a bullet became its own paragraph (this module had no list block) and a table line a paragraph
    of pipes: an article written with lists and a comparison table was published as headings and paragraphs only.
    """
    blocks: list[dict] = []
    seen_h1 = False
    run_kind, run = "", []          # the list or table being gathered: "ul" | "ol" | "table"

    def close_run() -> None:
        nonlocal run_kind, run
        if run_kind in ("ul", "ol") and run:
            blocks.append({"type": "list", "text": "", "items": run, "ordered": run_kind == "ol"})
        elif run_kind == "table" and run:
            header = len(run) > 1 and all(_TABLE_RULE_CELL_RE.match(c or "-") for c in run[1])
            rows = [r for i, r in enumerate(run) if not (header and i == 1)]
            blocks.append({"type": "table", "text": "", "rows": rows, "header": header})
        run_kind, run = "", []

    for raw_line in (markdown_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            close_run()
            continue
        heading_match = _HEADING_LINE_RE.match(line)
        if heading_match:
            close_run()
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            if level == 1 and skip_h1 and not seen_h1:
                seen_h1 = True
                continue
            blocks.append({"type": "heading", "text": text, "level": level})
            continue
        for kind, pattern in (("ul", _BULLET_LINE_RE), ("ol", _ORDERED_LINE_RE)):
            item = pattern.match(line)
            if item:
                if run_kind != kind:
                    close_run()
                    run_kind = kind
                run.append(item.group(1))
                break
        else:
            if _TABLE_LINE_RE.match(line):
                if run_kind != "table":
                    close_run()
                    run_kind = "table"
                run.append(_table_cells(line))
                continue
            close_run()
            blocks.append({"type": "paragraph", "text": line})
    close_run()
    return blocks


def blocks_to_content(blocks, site_domain: str | None = None) -> str:
    """Render explicit blocks (list of {type, text, level, media_id, media_url, caption, faq_items})
    into post_content.

    type == "heading" renders an <h{level}> block; type == "image" renders a
    Gutenberg image block from an existing attachment (media_id + media_url
    required — a block missing either is skipped, since there is nothing to
    render); type == "faq" renders a visible Q&A list plus FAQPage JSON-LD
    schema (skipped if faq_items is empty); anything else (including the
    default "paragraph") renders a plain paragraph block.

    site_domain (the connected site's own domain, e.g. from list_sites) is
    the pipeline's link policy switch: any inline [anchor](url) link whose
    host does NOT match it gets target="_blank" rel="nofollow noopener
    noreferrer" automatically -- external links always open in a new tab and
    never pass link equity, without a caller having to remember to mark each
    one by hand. A link to the site's own domain stays a normal same-tab,
    followed link. Omit site_domain to keep the old behaviour (no link ever
    gets marked external).

    NOTE on image_role: a block whose image_role names an external_images
    entry gets its media_id/media_url filled in by the caller (see
    handlers_posts.resolve_external_images) BEFORE this function runs -- this
    function only ever renders whatever media_id/media_url already sit on
    the block, regardless of how they got there.
    """
    rendered = []
    for block in blocks or []:
        btype, text, level, media_id, media_url, caption, faq_items = _block_fields(block)
        if btype == "image":
            if media_id and media_url:
                rendered.append(image_block(media_id, media_url, alt=text, caption=caption))
            continue
        if btype == "faq":
            rendered_faq = faq_block(faq_items, intro_text=text)
            if rendered_faq:
                rendered.append(rendered_faq)
            continue
        if btype == "list":
            rendered_list = list_block(_block_extra(block, "items", []), bool(_block_extra(block, "ordered", False)),
                                       site_domain)
            if rendered_list:
                rendered.append(rendered_list)
            continue
        if btype == "table":
            rendered_table = table_block(_block_extra(block, "rows", []), bool(_block_extra(block, "header", True)),
                                         site_domain)
            if rendered_table:
                rendered.append(rendered_table)
            continue
        if not text.strip():
            continue
        if btype == "heading":
            rendered.append(heading_block(text, level, site_domain))
        else:
            rendered.append(paragraph_block(text, site_domain))
    return "\n".join(rendered)
