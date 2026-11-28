from __future__ import annotations

from pydantic import BaseModel, Field
from imperal_sdk import sdl


class SiteRecord(sdl.Entity):
    name: str = ""
    url: str = ""
    domain: str = ""
    is_multisite: bool = False
    admin_email: str = ""
    wp_version: str = ""
    language: str = ""
    timezone: str = ""
    status: str = "active"
    last_sync: str = ""


class Post(sdl.Entity):
    title: str = ""
    status: str = "draft"
    date: str = ""
    modified: str = ""
    author: int = 0
    slug: str = ""
    excerpt: str = ""
    link: str = ""
    categories: list[int] = []
    tags: list[int] = []
    featured_media: int = 0
    comment_status: str = "open"
    ping_status: str = "open"
    format: str = "standard"


class Page(sdl.Entity):
    title: str = ""
    status: str = "draft"
    date: str = ""
    modified: str = ""
    author: int = 0
    slug: str = ""
    link: str = ""
    parent: int = 0
    menu_order: int = 0
    comment_status: str = "closed"


class Media(sdl.Entity):
    title: str = ""
    caption: str = ""
    alt_text: str = ""
    media_type: str = "image"
    mime_type: str = ""
    source_url: str = ""
    date: str = ""


class Category(sdl.Entity):
    name: str = ""
    slug: str = ""
    description: str = ""
    count: int = 0
    parent: int = 0


class Tag(sdl.Entity):
    name: str = ""
    slug: str = ""
    description: str = ""
    count: int = 0


class User(sdl.Entity):
    name: str = ""
    username: str = ""
    email: str = ""
    roles: list[str] = []
    avatar_url: str = ""


class Plugin(sdl.Entity):
    plugin: str = ""
    name: str = ""
    version: str = ""
    status: str = "inactive"
    author: str = ""
    description: str = ""
    update_available: bool = False


class Theme(sdl.Entity):
    stylesheet: str = ""
    name: str = ""
    version: str = ""
    status: str = "inactive"
    author: str = ""
    screenshot: str = ""
    update_available: bool = False


class WpComment(sdl.Entity):
    post: int = 0
    author_name: str = ""
    author_email: str = ""
    author_url: str = ""
    date: str = ""
    content: str = ""
    status: str = "hold"
    parent: int = 0


class WcProduct(sdl.Entity):
    name: str = ""
    slug: str = ""
    type: str = "simple"
    status: str = "publish"
    featured: bool = False
    sku: str = ""
    price: str = ""
    regular_price: str = ""
    sale_price: str = ""
    on_sale: bool = False
    stock_status: str = "instock"
    stock_quantity: int | None = None
    manage_stock: bool = False
    weight: str = ""
    categories: list[int] = []
    tags: list[int] = []
    images: list[str] = []
    short_description: str = ""
    description: str = ""


class WcCategory(sdl.Entity):
    name: str = ""
    slug: str = ""
    parent: int = 0
    description: str = ""
    image: str = ""
    count: int = 0


class WcOrder(sdl.Entity):
    number: str = ""
    status: str = "pending"
    currency: str = ""
    total: str = ""
    date_created: str = ""
    customer_id: int = 0
    billing_first_name: str = ""
    billing_last_name: str = ""
    billing_email: str = ""
    billing_phone: str = ""
    billing_city: str = ""
    billing_country: str = ""
    payment_method: str = ""
    payment_method_title: str = ""
    line_items_count: int = 0


class WcCoupon(sdl.Entity):
    code: str = ""
    amount: str = ""
    discount_type: str = "fixed_cart"
    description: str = ""
    date_expires: str = ""
    usage_count: int = 0
    usage_limit: int | None = None
    free_shipping: bool = False


class WcCustomer(sdl.Entity):
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    role: str = "customer"
    orders_count: int = 0
    total_spent: str = "0.00"
    avatar_url: str = ""


class WcShippingZone(sdl.Entity):
    name: str = ""
    order: int = 0


class WcTaxRate(sdl.Entity):
    country: str = ""
    state: str = ""
    postcode: str = ""
    city: str = ""
    rate: str = ""
    name: str = ""
    priority: int = 1
    compound: bool = False
    shipping: bool = True
    tax_class: str = "standard"


class WcRefund(sdl.Entity):
    date_created: str = ""
    amount: str = ""
    reason: str = ""
    refunded_by: int = 0


class WcReport(sdl.Entity):
    total_sales: str = ""
    net_sales: str = ""
    average_sales: str = ""
    total_orders: int = 0
    total_items: int = 0
    total_tax: str = ""
    total_shipping: str = ""
    total_refunds: str = ""
    total_discount: str = ""
    totals_grouped_by: str = ""


class SeoAnalysis(sdl.Entity):
    focus_kw: str = ""
    title_ok: bool = False
    meta_desc_ok: bool = False
    kw_in_title: bool = False
    kw_in_first_p: bool = False
    kw_density: float = 0.0
    word_count: int = 0
    readability_score: str = ""
    suggestions: list[str] = []


class BuildersDetected(sdl.Entity):
    gutenberg: bool = True
    elementor: bool = False
    bricks: bool = False
    divi: bool = False
    beaver: bool = False
    oxygen: bool = False
    wpbakery: bool = False
    active_theme: str = ""


class ElementorTemplate(sdl.Entity):
    title: str = ""
    type: str = "page"
    status: str = "publish"
    date: str = ""


class BricksTemplate(sdl.Entity):
    title: str = ""
    template_type: str = "section"
    status: str = "publish"
    date: str = ""


class Menu(sdl.Entity):
    name: str = ""
    slug: str = ""
    locations: list[str] = []
    count: int = 0


class MenuItem(sdl.Entity):
    menu_id: int = 0
    title: str = ""
    url: str = ""
    parent: int = 0
    order: int = 0
    target: str = ""
    type: str = "custom"
    object_id: int = 0


class BrokenLink(sdl.Entity):
    url: str = ""
    post_id: int = 0
    post_title: str = ""
    status_code: int = 0
    error: str = ""
    link_text: str = ""


class RedirectRule(sdl.Entity):
    source_url: str = ""
    target_url: str = ""
    action_code: int = 301
    group_id: int = 1
    match_type: str = "url"
    action_type: str = "url"
    action_data: str = ""


class WpSettings(sdl.Entity):
    title: str = ""
    description: str = ""
    url: str = ""
    email: str = ""
    timezone: str = ""
    date_format: str = ""
    time_format: str = ""
    language: str = ""
    start_of_week: int = 1
    posts_per_page: int = 10


class MaintenanceState(sdl.Entity):
    enabled: bool = False
    plugin: str = ""
    message: str = ""


class RankMathPostData(sdl.Entity):
    focus_keywords: list[str] = []
    seo_title: str = ""
    seo_description: str = ""
    robots: list[str] = []
    canonical_url: str = ""
    schema_type: str = ""
    score: int = 0
    is_pillar_content: bool = False


class RankMathStatus(sdl.Entity):
    active: bool = False
    version: str = ""
    modules_active: list[str] = []
    sitemap_url: str = ""
    has_pro: bool = False


class IndexNowSubmissionResult(sdl.Entity):
    host: str = ""
    urls_submitted: list[str] = []
    status_code: int = 0
    message: str = ""
    key_location: str = ""


class LlmstxtStatus(sdl.Entity):
    url: str = ""
    exists: bool = False
    size_bytes: int = 0
    updated_at: str = ""
    preview: str = ""


class PostMetaEntry(sdl.Entity):
    meta_id: int = 0
    post_id: int = 0
    key: str = ""
    value: str = ""


class TermMetaEntry(sdl.Entity):
    meta_id: int = 0
    term_id: int = 0
    key: str = ""
    value: str = ""


class WpCronEvent(sdl.Entity):
    hook: str = ""
    timestamp: int = 0
    schedule: str = ""
    args: list[str] = []
    time_human: str = ""


class WpCronRunResult(sdl.Entity):
    hook: str = ""
    executed_at: str = ""
    status: str = "success"
    output: str = ""


class RunWpCommandParams(BaseModel):
    site_id: str = Field(description="Site id from a previous list_sites call — never invent it")
    command: str = Field(min_length=1, max_length=2000, description="WP-CLI command string or subcommand, e.g. 'plugin list --status=active' or 'post list'")
    raw_args: str | None = Field(default=None, description="Optional raw arguments/flags passed directly to the command")
    timeout: int = Field(default=60, ge=5, le=600, description="Command execution timeout in seconds (default 60, up to 600)")


class WpCommandResult(sdl.Entity):
    """Result of executing an arbitrary WP-CLI command over SSH."""
    output: str = ""
    command: str = ""


class Order(sdl.Entity):
    total: str = ""
    currency: str = ""
    status: str = "pending"
    date_created: str = ""
    billing: dict = {}
    shipping: dict = {}
    line_items: list[dict] = []
    payment_method_title: str = ""
    customer_note: str = ""


class SshCred(sdl.Entity):
    host: str = ""
    port: int = 22
    user: str = ""
    wp_path: str = "/var/www/html"
    wp_bin: str = "wp"


class SiteHealth(sdl.Entity):
    wp_version: str = ""
    php_version: str = ""
    mysql_version: str = ""
    server_arch: str = ""
    writable_uploads: bool = True
    memory_limit: str = ""
    max_execution_time: int = 30
    https_enabled: bool = False
    core_updates_pending: bool = False
    issues_critical: int = 0
    issues_recommended: int = 0


class WpQueryPost(sdl.Entity):
    title: str = ""
    post_type: str = "post"
    post_status: str = "publish"
    author_name: str = ""
    date: str = ""
    excerpt: str = ""
    meta: dict[str, str] = {}


class RestRoute(sdl.Entity):
    route: str = ""
    namespace: str = ""
    methods: list[str] = []
    endpoints_count: int = 1


class BuilderAbilities(sdl.Entity):
    supports_gutenberg: bool = True
    supports_elementor: bool = False
    supports_bricks: bool = False
    supports_divi: bool = False
    has_acf: bool = False
    has_metabox: bool = False
    has_pods: bool = False
    has_woocommerce: bool = False
    has_rankmath: bool = False
    has_yoast: bool = False


class SecurityScanResult(sdl.Entity):
    scanner: str = "basic"
    wp_version_secure: bool = True
    admin_user_safe: bool = True
    file_edit_disabled: bool = False
    debug_mode_off: bool = True
    prefix_safe: bool = True
    xmlrpc_disabled: bool = False
    vulnerable_plugins: list[str] = []
    vulnerable_themes: list[str] = []
    score: int = 100


class BackupArchive(sdl.Entity):
    filename: str = ""
    size_bytes: int = 0
    created_at: str = ""
    path: str = ""
    kind: str = "full"


class LogEntry(sdl.Entity):
    timestamp: str = ""
    level: str = "notice"
    source: str = "debug.log"
    message: str = ""


class CustomPostType(sdl.Entity):
    name: str = ""
    label: str = ""
    description: str = ""
    public: bool = True
    hierarchical: bool = False
    supports: list[str] = []
    taxonomies: list[str] = []
    has_archive: bool = True
    rest_base: str = ""


class CustomTaxonomy(sdl.Entity):
    name: str = ""
    label: str = ""
    description: str = ""
    public: bool = True
    hierarchical: bool = False
    post_types: list[str] = []
    rest_base: str = ""


class BlockType(sdl.Entity):
    name: str = ""
    title: str = ""
    category: str = "common"
    icon: str = ""
    description: str = ""
    keywords: list[str] = []
    attributes: list[str] = []


class ReusableBlock(sdl.Entity):
    title: str = ""
    slug: str = ""
    status: str = "publish"
    date: str = ""
    content: str = ""


class Webhook(sdl.Entity):
    name: str = ""
    status: str = "active"
    topic: str = ""
    delivery_url: str = ""
    secret_preview: str = ""
    created_at: str = ""


class WebhookDelivery(sdl.Entity):
    webhook_id: int = 0
    duration: float = 0.0
    summary: str = ""
    request_headers: dict[str, str] = {}
    request_body: str = ""
    response_code: int = 200
    response_headers: dict[str, str] = {}
    response_body: str = ""
    created_at: str = ""


class ActionSchedulerAction(sdl.Entity):
    hook: str = ""
    status: str = "pending"
    scheduled_date: str = ""
    args: list[str] = []
    group: str = ""
    attempts: int = 0
    log_entries: list[str] = []


class RewriteRule(sdl.Entity):
    match: str = ""
    query: str = ""
    source: str = "other"


class CoreChecksumResult(sdl.Entity):
    all_ok: bool = True
    total_files: int = 0
    corrupted_files: list[str] = []
    added_files: list[str] = []
    missing_files: list[str] = []


class CoreVerification(sdl.Entity):
    wp_version: str = ""
    verified: bool = True
    signature_ok: bool = True
    files_checked: int = 0
    message: str = ""


class SmtpConfig(sdl.Entity):
    host: str = ""
    port: int = 587
    encryption: str = "tls"
    auth: bool = True
    user: str = ""
    from_email: str = ""
    from_name: str = ""
    plugin: str = ""


class MailLogEntry(sdl.Entity):
    to_email: str = ""
    subject: str = ""
    status: str = "sent"
    sent_at: str = ""
    error_message: str = ""


class SiteHealthFullReport(sdl.Entity):
    status: str = "good"
    passed_tests: int = 0
    recommended_count: int = 0
    critical_count: int = 0
    recommended_items: list[str] = []
    critical_items: list[str] = []


class UserSession(sdl.Entity):
    user_id: int = 0
    login_time: str = ""
    ip: str = ""
    expiration: str = ""
    user_agent: str = ""


class NetworkSite(sdl.Entity):
    blog_id: int = 1
    domain: str = ""
    path: str = "/"
    registered: str = ""
    last_updated: str = ""
    public: bool = True
    archived: bool = False
    mature: bool = False
    spam: bool = False
    deleted: bool = False


class PolylangLanguage(sdl.Entity):
    code: str = ""
    name: str = ""
    locale: str = ""
    is_default: bool = False
    order: int = 0
    flag_url: str = ""


class BricksFormSubmission(sdl.Entity):
    form_id: str = ""
    post_id: int = 0
    created_at: str = ""
    fields: dict[str, str] = {}
    user_ip: str = ""
    user_agent: str = ""


class BricksFormSummary(sdl.Entity):
    form_id: str = ""
    post_id: int = 0
    post_title: str = ""
    submissions_count: int = 0
    last_submission_at: str = ""


class FaqItemInput(BaseModel):
    question: str = Field(min_length=1, max_length=500, description="The FAQ question")
    answer: str = Field(min_length=1, max_length=5000, description="The answer to the question (HTML allowed: <a>, <strong>, <em>)")


class PostBlockInput(BaseModel):
    type: str = Field(
        description=(
            "Block type: 'paragraph', 'heading', 'image', 'quote', 'code', 'list', 'table', 'faq', 'callout', 'separator'. "
            "Use 'list' for bulleted or ordered lists (pass items=[...], ordered=False/True). "
            "Use 'table' for structured tabular data (pass rows=[[...]], headers=[...]). "
            "Use 'code' for preformatted source code or commands (language='bash', etc.). "
            "Use 'faq' for FAQ sections with schema markup. "
            "Use 'callout' for highlighted tip/warning boxes."
        )
    )
    content: str = Field(default="", description="Text content for paragraph, heading, quote, code, callout. Inline formatting supported: **bold**, *italic*, `code`, and HTML links <a href='...'>anchor</a>.")
    level: int = Field(default=2, ge=1, le=6, description="Heading level (1-6), used when type='heading'")
    image_id: int | None = Field(default=None, description="WordPress media attachment ID, used when type='image'")
    image_url: str | None = Field(default=None, description="Image source URL, used when type='image'")
    alt_text: str = Field(default="", description="Alt text for the image, used when type='image'")
    caption: str = Field(default="", description="Caption text below the image, used when type='image'")
    items: list[str] = Field(default=[], description="List items (plain text or with inline HTML), used when type='list'")
    ordered: bool = Field(default=False, description="True for numbered <ol>, False for bulleted <ul>, used when type='list'")
    headers: list[str] = Field(default=[], description="Table header cells, used when type='table'")
    rows: list[list[str]] = Field(default=[], description="Table data rows (list of row arrays), used when type='table'")
    faq_items: list[FaqItemInput] = Field(default=[], description="Array of {question, answer} pairs, used when type='faq'")
    callout_type: str = Field(default="info", description="Callout style: 'info' (blue), 'success' (green), 'warning' (yellow), 'error' (red)")
    citation: str = Field(default="", description="Quote citation / author attribution, used when type='quote'")
    language: str = Field(default="", description="Programming language for code block syntax highlighting (e.g. 'python', 'php', 'bash', 'json')")
