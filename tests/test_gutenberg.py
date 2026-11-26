"""Tests for gutenberg.py — explicit block -> Gutenberg markup rendering.

Deliberately document-agnostic: every test passes blocks the CALLER already
decided on (no document parsing, no heuristics exercised here).
"""

import json

from models import FaqItemInput, PostBlockInput
import gutenberg


def test_paragraph_block_escapes_html():
    out = gutenberg.paragraph_block("A & B < C")
    assert "wp:paragraph" in out
    assert "A &amp; B &lt; C" in out


def test_heading_block_renders_level():
    out = gutenberg.heading_block("Title", level=3)
    assert '"level":3' in out
    assert "<h3" in out and "</h3>" in out


def test_paragraph_block_renders_inline_link():
    """[anchor](url) syntax becomes a real <a href>, not escaped literal text --
    this is the fix for internal/external/CTA links inside article body text."""
    out = gutenberg.paragraph_block("See our [heat recovery guide](https://climtec.md/ru/guide/) for details.")
    assert '<a href="https://climtec.md/ru/guide/">heat recovery guide</a>' in out
    assert "&lt;a" not in out
    assert "[heat recovery guide]" not in out


def test_paragraph_block_inline_link_escapes_surrounding_text():
    out = gutenberg.paragraph_block("A & B [link text](https://x.com/) C < D")
    assert "A &amp; B" in out
    assert '<a href="https://x.com/">link text</a>' in out
    assert "C &lt; D" in out


def test_paragraph_block_inline_link_escapes_url_and_anchor():
    out = gutenberg.paragraph_block('[<script>](https://x.com/?a=1&b=2)')
    assert "<script>" not in out
    assert "&amp;b=2" in out


def test_heading_block_renders_inline_link():
    out = gutenberg.heading_block("Read [more](https://climtec.md/)", level=2)
    assert '<a href="https://climtec.md/">more</a>' in out


def test_paragraph_block_without_brackets_unaffected():
    """Plain text with no [..](..) syntax renders exactly as before."""
    out = gutenberg.paragraph_block("Just a plain sentence, no links here.")
    assert "<a href" not in out
    assert "Just a plain sentence, no links here." in out


def test_image_block_renders_id_url_alt():
    out = gutenberg.image_block(42, "https://x.com/pic.jpg", alt="A cat")
    assert "wp:image" in out
    assert '"id":42' in out
    assert 'src="https://x.com/pic.jpg"' in out
    assert 'alt="A cat"' in out
    assert "wp-image-42" in out


def test_image_block_with_caption():
    out = gutenberg.image_block(7, "https://x.com/pic.jpg", caption="A caption")
    assert "figcaption" in out
    assert "A caption" in out


def test_image_block_without_caption_omits_figcaption():
    out = gutenberg.image_block(7, "https://x.com/pic.jpg")
    assert "figcaption" not in out


def test_image_block_escapes_alt_and_url():
    out = gutenberg.image_block(1, 'https://x.com/pic.jpg?a=1&b=2', alt='"quoted" & <tag>')
    assert "&amp;" in out
    assert "<tag>" not in out


def test_blocks_to_content_renders_image_block_from_model():
    blocks = [
        PostBlockInput(type="heading", text="Intro", level=2),
        PostBlockInput(type="image", media_id=9, media_url="https://x.com/pic.jpg", text="Alt text"),
        PostBlockInput(type="paragraph", text="Body"),
    ]
    content = gutenberg.blocks_to_content(blocks)
    assert "wp:heading" in content
    assert "wp:image" in content
    assert 'alt="Alt text"' in content
    assert "wp-image-9" in content
    assert "Body" in content


def test_blocks_to_content_skips_image_block_without_media_id():
    """An image block with no media_id can't render anything meaningful —
    it is skipped rather than emitting a broken <img> with no src."""
    blocks = [PostBlockInput(type="image", text="orphan")]
    content = gutenberg.blocks_to_content(blocks)
    assert content == ""


def test_blocks_to_content_accepts_plain_dicts_too():
    blocks = [{"type": "image", "media_id": 3, "media_url": "https://x.com/a.jpg", "text": "alt"}]
    content = gutenberg.blocks_to_content(blocks)
    assert "wp-image-3" in content


# ─────────── faq_block: FAQPage JSON-LD + visible Q&A ───────────

def test_faq_block_renders_visible_qa_and_jsonld():
    items = [
        {"question": "What is X?", "answer": "X is Y."},
        {"question": "How much does it cost?", "answer": "It depends."},
    ]
    out = gutenberg.faq_block(items)
    assert "What is X?" in out
    assert "X is Y." in out
    assert "How much does it cost?" in out
    assert 'application/ld+json' in out
    # extract the JSON-LD payload and validate it's real, well-formed FAQPage schema
    start = out.index("<script type=\"application/ld+json\">") + len("<script type=\"application/ld+json\">")
    end = out.index("</script>", start)
    payload = json.loads(out[start:end])
    assert payload["@type"] == "FAQPage"
    assert len(payload["mainEntity"]) == 2
    assert payload["mainEntity"][0]["@type"] == "Question"
    assert payload["mainEntity"][0]["name"] == "What is X?"
    assert payload["mainEntity"][0]["acceptedAnswer"]["@type"] == "Answer"
    assert payload["mainEntity"][0]["acceptedAnswer"]["text"] == "X is Y."


def test_faq_block_accepts_faqiteminput_models():
    items = [FaqItemInput(question="Q1", answer="A1")]
    out = gutenberg.faq_block(items)
    assert "Q1" in out and "A1" in out


def test_faq_block_escapes_html_in_question_and_answer():
    items = [{"question": "A & B?", "answer": "<script>bad</script>"}]
    out = gutenberg.faq_block(items)
    assert "<script>bad</script>" not in out.split("application/ld+json")[0]  # not raw in visible html
    assert "&amp;" in out


def test_faq_block_skips_incomplete_items():
    items = [{"question": "", "answer": "orphan answer"}, {"question": "Real Q", "answer": "Real A"}]
    out = gutenberg.faq_block(items)
    assert "orphan answer" not in out
    assert "Real Q" in out


def test_faq_block_empty_items_renders_nothing():
    assert gutenberg.faq_block([]) == ""


def test_faq_block_with_intro_text():
    out = gutenberg.faq_block([{"question": "Q", "answer": "A"}], intro_text="Common questions:")
    assert "Common questions:" in out


def test_blocks_to_content_renders_faq_block_from_model():
    blocks = [
        PostBlockInput(type="heading", text="FAQ", level=2),
        PostBlockInput(type="faq", faq_items=[FaqItemInput(question="Q1", answer="A1")]),
    ]
    content = gutenberg.blocks_to_content(blocks)
    assert "Q1" in content
    assert "FAQPage" in content


# ─────────── external-link policy: nofollow + open in new tab ───────────
#
# Pipeline rule: every link whose host differs from the connected site's own
# domain (external) automatically gets target="_blank" rel="nofollow noopener
# noreferrer" -- no article writer or caller has to remember to mark it by
# hand. A same-site link stays a normal, followed, same-tab link. Without a
# site_domain at all (the old call shape), nothing is marked -- unchanged
# behaviour for any caller that hasn't opted in yet.

def test_paragraph_block_without_site_domain_marks_nothing_external():
    out = gutenberg.paragraph_block("See [a link](https://anywhere.example/) here.")
    assert '<a href="https://anywhere.example/">a link</a>' in out
    assert "nofollow" not in out
    assert "target=" not in out


def test_paragraph_block_external_link_gets_nofollow_and_new_tab():
    out = gutenberg.paragraph_block(
        "See [a source](https://en.wikipedia.org/wiki/Heat_recovery) here.",
        site_domain="https://climtec.md",
    )
    assert (
        '<a href="https://en.wikipedia.org/wiki/Heat_recovery" '
        'target="_blank" rel="nofollow noopener noreferrer">a source</a>' in out
    )


def test_paragraph_block_same_site_link_stays_plain():
    out = gutenberg.paragraph_block(
        "See our [other post](https://climtec.md/ru/other/) here.",
        site_domain="https://climtec.md",
    )
    assert '<a href="https://climtec.md/ru/other/">other post</a>' in out
    assert "nofollow" not in out
    assert "target=" not in out


def test_paragraph_block_www_prefix_still_counts_as_same_site():
    out = gutenberg.paragraph_block(
        "See [this page](https://www.climtec.md/ru/page/) here.",
        site_domain="climtec.md",
    )
    assert '<a href="https://www.climtec.md/ru/page/">this page</a>' in out
    assert "nofollow" not in out


def test_heading_block_external_link_gets_nofollow_and_new_tab():
    out = gutenberg.heading_block(
        "Read [more](https://external-site.com/)", level=2, site_domain="https://climtec.md",
    )
    assert (
        '<a href="https://external-site.com/" target="_blank" '
        'rel="nofollow noopener noreferrer">more</a>' in out
    )


def test_blocks_to_content_passes_site_domain_to_every_block():
    blocks = [
        {"type": "heading", "text": "See [ext](https://other.com/)", "level": 2},
        {"type": "paragraph", "text": "See [ext2](https://other.com/b/)"},
    ]
    content = gutenberg.blocks_to_content(blocks, site_domain="https://climtec.md")
    assert content.count("nofollow") == 2


def test_is_external_link_bare_domain_and_full_url_equivalent():
    assert gutenberg._is_external_link("https://climtec.md/ru/x/", "climtec.md") is False
    assert gutenberg._is_external_link("https://climtec.md/ru/x/", "https://climtec.md") is False
    assert gutenberg._is_external_link("https://other.com/x/", "https://climtec.md") is True


def test_markdown_to_blocks_output_renders_with_link_policy_end_to_end():
    """The full pipeline: article Markdown -> blocks -> content, with the
    external-link policy applied -- this is the actual bug-fix path."""
    markdown = (
        "# Title\n\n"
        "See our [internal page](https://climtec.md/ru/other/) and this "
        "[external source](https://en.wikipedia.org/wiki/X) too."
    )
    blocks = gutenberg.markdown_to_blocks(markdown)
    content = gutenberg.blocks_to_content(blocks, site_domain="climtec.md")
    assert '<a href="https://climtec.md/ru/other/">internal page</a>' in content
    assert (
        '<a href="https://en.wikipedia.org/wiki/X" target="_blank" '
        'rel="nofollow noopener noreferrer">external source</a>' in content
    )


# ─────────── markdown_to_blocks: the missing article-markdown -> blocks link ───────────
#
# This is the actual pipeline fix: an article's Markdown (e.g. straight from
# Article Writer) previously had to be manually retyped into {type, text,
# level} blocks by a human or an LLM before create_post/update_post could
# publish it -- an error-prone step that could (and did, on a real published
# climtec.md article) silently drop the [anchor](url) bracket syntax, so a
# correctly-written markdown link ended up as plain "anchor text (url)" on
# the live page. markdown_to_blocks() removes that manual step by converting
# deterministically, preserving [anchor](url) spans byte-for-byte so
# blocks_to_content's existing inline-link rendering still catches them.

def test_markdown_to_blocks_drops_h1_title_by_default():
    blocks = gutenberg.markdown_to_blocks("# The Title\n\nBody text.")
    assert blocks == [{"type": "paragraph", "text": "Body text."}]


def test_markdown_to_blocks_keeps_h1_when_requested():
    blocks = gutenberg.markdown_to_blocks("# The Title\n\nBody.", skip_h1=False)
    assert blocks[0] == {"type": "heading", "text": "The Title", "level": 1}


def test_markdown_to_blocks_renders_headings_with_level():
    blocks = gutenberg.markdown_to_blocks("## Section One\n\nSome text.\n\n### Sub section")
    assert blocks[0] == {"type": "heading", "text": "Section One", "level": 2}
    assert blocks[-1] == {"type": "heading", "text": "Sub section", "level": 3}


def test_markdown_to_blocks_gathers_bullets_into_one_list_block():
    blocks = gutenberg.markdown_to_blocks("- First point\n- Second point")
    assert blocks == [{"type": "list", "text": "", "items": ["First point", "Second point"], "ordered": False}]


def test_markdown_to_blocks_preserves_inline_link_syntax_unchanged():
    """The exact real-world regression: a paragraph mentioning how often to
    change filters, with a genuine markdown [anchor](url) link, must survive
    markdown_to_blocks with its bracket syntax intact so blocks_to_content
    still turns it into a real <a href> -- not into plain 'text (url)'."""
    md = (
        "Понимание долгосрочных расходов включает регулярность обслуживания — "
        "например, [как часто менять фильтры](https://climtec.md/ru/cat-de-des-se-schimba-filtrele-ru/)."
    )
    blocks = gutenberg.markdown_to_blocks(md)
    assert len(blocks) == 1
    assert "[как часто менять фильтры](https://climtec.md/ru/cat-de-des-se-schimba-filtrele-ru/)" in blocks[0]["text"]
    # And feeding that block into the existing renderer produces a real link,
    # never the flattened "anchor (url)" text the live bug produced.
    content = gutenberg.blocks_to_content(blocks)
    assert '<a href="https://climtec.md/ru/cat-de-des-se-schimba-filtrele-ru/">как часто менять фильтры</a>' in content
    assert "фильтры (https://" not in content


def test_markdown_to_blocks_skips_blank_lines():
    blocks = gutenberg.markdown_to_blocks("Para one.\n\n\nPara two.")
    assert blocks == [
        {"type": "paragraph", "text": "Para one."},
        {"type": "paragraph", "text": "Para two."},
    ]


def test_markdown_to_blocks_empty_input_returns_empty_list():
    assert gutenberg.markdown_to_blocks("") == []
    assert gutenberg.markdown_to_blocks(None) == []


# ─────────── strip_scaffolding_headings (post-check) ───────────

def test_strip_scaffolding_headings_drops_bare_intro_and_cta():
    blocks = [
        {"type": "heading", "text": "Intro", "level": 2},
        {"type": "paragraph", "text": "Real intro copy stays."},
        {"type": "heading", "text": "Real Section Title", "level": 2},
        {"type": "paragraph", "text": "Body."},
        {"type": "heading", "text": "CTA", "level": 2},
        {"type": "paragraph", "text": "Real CTA copy stays too."},
    ]
    out = gutenberg.strip_scaffolding_headings(blocks)
    texts = [b["text"] for b in out]
    assert "Intro" not in texts
    assert "CTA" not in texts
    assert "Real Section Title" in texts
    assert "Real intro copy stays." in texts
    assert "Real CTA copy stays too." in texts
    assert len(out) == 4


def test_strip_scaffolding_headings_is_case_and_language_insensitive_exact_match_only():
    blocks = [
        {"type": "heading", "text": "введение", "level": 2},
        {"type": "heading", "text": "Introducere", "level": 2},
        {"type": "heading", "text": "call to action", "level": 3},
        # Must NOT be stripped: a real heading that merely mentions the word.
        {"type": "heading", "text": "Introducere in sisteme de climatizare", "level": 2},
        {"type": "paragraph", "text": "CTA reminders inside a paragraph are never touched."},
    ]
    out = gutenberg.strip_scaffolding_headings(blocks)
    texts = [b["text"] for b in out]
    assert "введение" not in texts
    assert "Introducere" not in texts
    assert "call to action" not in texts
    assert "Introducere in sisteme de climatizare" in texts
    assert "CTA reminders inside a paragraph are never touched." in texts


def test_strip_scaffolding_headings_handles_none_and_pydantic_blocks():
    from models import PostBlockInput
    assert gutenberg.strip_scaffolding_headings(None) == []
    blocks = [
        PostBlockInput(type="heading", text="Intro", level=2),
        PostBlockInput(type="paragraph", text="Keep me"),
    ]
    out = gutenberg.strip_scaffolding_headings(blocks)
    assert len(out) == 1
    assert out[0].text == "Keep me"



# ─────────── an article's Markdown reaches the page as it was written (2026-11) ───────────
# Live 2026-11-26, post 2248 published from Article Writer's export: 40 raw "**" and not one <strong>, 0 <ul>,
# 0 <li>, 0 <table> -- bold markers went out as text, every bullet was its own paragraph, a table a paragraph of
# pipes. Nothing here loosens the escaping: the only tags that can appear are the ones this module writes.

ARTICLE = """# Title

Intro with **bold words**, *an aside* and `wp-config.php`.

## DirectAdmin

- **Primary Strength:** High stability and [LiteSpeed](https://example.com/ls) integration.
- **Resource Footprint:** Minimal (<100MB idle RAM overhead).

1. Back up the site
2. Switch DNS

| Panel | License |
|---|---|
| DirectAdmin | **Flat** |
| cPanel | Per account |

Closing line.
"""


def test_inline_bold_italic_and_code_render_as_html_and_nothing_else_does():
    out = gutenberg.paragraph_block("A **bold** and *soft* word, `x < y` in code, <b>raw</b> & 2 * 3 * 4.")
    assert "<strong>bold</strong>" in out and "<em>soft</em>" in out and "<code>x &lt; y</code>" in out
    assert "&lt;b&gt;raw&lt;/b&gt;" in out and "&amp;" in out      # caller HTML is still escaped text
    assert "2 * 3 * 4" in out                                        # arithmetic is not emphasis
    assert "**" not in out


def test_bold_around_a_link_and_inside_an_anchor():
    out = gutenberg.paragraph_block("See **[the guide](https://climtec.md/g/)** and [**this**](https://climtec.md/t/).",
                                    site_domain="climtec.md")
    assert '<strong><a href="https://climtec.md/g/">the guide</a></strong>' in out
    assert '<a href="https://climtec.md/t/"><strong>this</strong></a>' in out
    assert "**" not in out and "\x00" not in out


def test_text_inside_a_code_span_is_left_as_written():
    out = gutenberg.paragraph_block("Run `rm **/*.log` now")
    assert "<code>rm **/*.log</code>" in out and "<strong>" not in out


def test_an_articles_markdown_becomes_lists_a_table_and_emphasis():
    blocks = gutenberg.markdown_to_blocks(ARTICLE)
    assert [b["type"] for b in blocks] == ["paragraph", "heading", "list", "list", "table", "paragraph"]
    assert blocks[2]["ordered"] is False and len(blocks[2]["items"]) == 2
    assert blocks[3] == {"type": "list", "text": "", "items": ["Back up the site", "Switch DNS"], "ordered": True}
    assert blocks[4]["header"] is True
    assert blocks[4]["rows"] == [["Panel", "License"], ["DirectAdmin", "**Flat**"], ["cPanel", "Per account"]]

    html_out = gutenberg.blocks_to_content(blocks, site_domain="blog.example.org")
    assert html_out.count("<!-- wp:list -->") == 1 and html_out.count('<!-- wp:list {"ordered":true} -->') == 1
    assert html_out.count("<!-- wp:list-item -->") == 4 and html_out.count("</li>") == 4
    assert '<ul class="wp-block-list">' in html_out and '<ol class="wp-block-list">' in html_out
    assert "<li><strong>Primary Strength:</strong> High stability and <a href=" in html_out
    assert "Minimal (&lt;100MB idle RAM overhead)." in html_out
    assert '<figure class="wp-block-table"><table class="has-fixed-layout"><thead><tr><th>Panel</th>' in html_out
    assert "<td><strong>Flat</strong></td>" in html_out and html_out.count("<tr>") == 3
    assert "**" not in html_out and "|" not in html_out
    assert "<strong>bold words</strong>" in html_out and "<em>an aside</em>" in html_out


def test_a_list_ends_where_the_lines_stop_being_its_kind():
    blocks = gutenberg.markdown_to_blocks("- a\n- b\n1. c\nPlain\n- d")
    assert [(b["type"], b.get("items")) for b in blocks] == [
        ("list", ["a", "b"]), ("list", ["c"]), ("paragraph", None), ("list", ["d"])]
    assert blocks[1]["ordered"] is True


def test_a_table_without_a_rule_line_has_no_head_and_ragged_rows_are_squared():
    blocks = gutenberg.markdown_to_blocks("| a | b |\n| c |")
    assert blocks == [{"type": "table", "text": "", "rows": [["a", "b"], ["c"]], "header": False}]
    out = gutenberg.blocks_to_content(blocks)
    assert "<thead>" not in out and out.count("<td>") == 4


def test_list_and_table_blocks_from_the_callers_own_models():
    blocks = [PostBlockInput(type="list", items=["One", "Two **strong**"], ordered=True),
              PostBlockInput(type="table", rows=[["H1", "H2"], ["a", "<i>b</i>"]]),
              PostBlockInput(type="list", items=[]), PostBlockInput(type="table", rows=[])]
    out = gutenberg.blocks_to_content(blocks)
    assert out.count("<li>") == 2 and "<li>Two <strong>strong</strong></li>" in out
    assert "<th>H1</th>" in out and "<td>&lt;i&gt;b&lt;/i&gt;</td>" in out
    assert out.count("<ol ") == 1 and out.count("<table") == 1          # the empty ones render nothing


def test_a_fenced_block_stays_one_code_block_line_for_line():
    md = ("Review our guide.\n\n```\n   INCOMING <WEB> TRAFFIC\n        |\n   +---------+\n   | **WAF** |\n"
          "   +---------+\n```\n\nModern infrastructure:\n\n- one\n")
    blocks = gutenberg.markdown_to_blocks(md)
    assert [b["type"] for b in blocks] == ["paragraph", "code", "paragraph", "list"]
    assert blocks[1]["text"] == "   INCOMING <WEB> TRAFFIC\n        |\n   +---------+\n   | **WAF** |\n   +---------+"
    out = gutenberg.blocks_to_content(blocks)
    assert out.count("<!-- wp:code -->") == 1 and "```" not in out
    assert "   INCOMING &lt;WEB&gt; TRAFFIC\n        |" in out          # spacing and line breaks kept, text escaped
    assert "| **WAF** |" in out and "<strong>" not in out               # nothing inside a fence is read as Markdown


def test_a_fence_with_a_language_a_tilde_fence_and_a_fence_never_closed():
    assert gutenberg.markdown_to_blocks("```python\nx = 1\n```") == [{"type": "code", "text": "x = 1"}]
    assert gutenberg.markdown_to_blocks("~~~\n- not a list\n| not | a table |\n~~~") == [
        {"type": "code", "text": "- not a list\n| not | a table |"}]
    assert gutenberg.markdown_to_blocks("text\n```\nleft open") == [
        {"type": "paragraph", "text": "text"}, {"type": "code", "text": "left open"}]


def test_a_code_block_from_the_callers_own_model():
    out = gutenberg.blocks_to_content([PostBlockInput(type="code", text="a  b\n  c")])
    assert out == '<!-- wp:code --><pre class="wp-block-code"><code>a  b\n  c</code></pre><!-- /wp:code -->'
