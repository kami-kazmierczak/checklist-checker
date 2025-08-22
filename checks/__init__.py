from .meta_tags import run as meta_tags
from .headings import run as headings
from .canonical import run as canonical
from .redirects import run as redirects
from .trailing_slash import run as trailing_slash
from .breadcrumbs_schema import run as breadcrumbs_schema
from .images_basic import run as images_basic
from .schema import run as schema_pages
from .blogpost_headings import run as blogpost_headings
from .home_paragraphs import run as home_paragraphs
from .clickable_elements import run as clickable_elements
from .nofollow_links import run as nofollow_links
from .blog_author import run as blog_author
from .alt_tags import run as alt_tags
from .pagination_title import run as pagination_title
from .lang_dir_in_url import run as lang_dir_in_url
from .blogpost_rating import run as blogpost_rating
from .psi import run as psi
from .webp import run as webp
from .faq import run as faq
from .contact_form_under_post import run as contact_form_under_post
from .cache import run as cache
from .blog_exist import run as blog_exist
from .related_products import run as related_products
from .home_latest_posts import run as home_latest_posts
from .error_page_404 import run as error_page_404
from .footer_year import run as footer_year

ALL_CHECKS = [
    ("meta_tags_coverage", meta_tags),
    ("headings_h1", headings),
    ("canonical_self_reference", canonical),
    ("redirects_core", redirects),
    ("trailing_slash_consistency", trailing_slash),
    ("breadcrumbs_presence", breadcrumbs_schema),
    ("images_weight_webp", images_basic),
    ("schema_pages", schema_pages),
    ("blogpost_headings", blogpost_headings),
    ("home_paragraphs", home_paragraphs),
    ("clickable_elements", clickable_elements),  
    ("nofollow_links_check", nofollow_links),
    ("blog_author", blog_author),
    ("alt_tags", alt_tags),
    ("pagination_title", pagination_title),
    ("lang_dir_in_url", lang_dir_in_url),
    ("blogpost_rating", blogpost_rating),
    ("psi", psi),
    ("webp_images", webp), 
    ("faq", faq),
    ("contact_form_under_post", contact_form_under_post),
    ("cache_headers", cache),
    ("blog_exists", blog_exist),
    ("error_page_404", error_page_404),
    ("Rok w stopce", footer_year),  


    # === PROBLEMATIC CHECKS ===
    # ("related_products", related_products),
    # ("home_latest_posts", home_latest_posts),
    # ===========================

]
