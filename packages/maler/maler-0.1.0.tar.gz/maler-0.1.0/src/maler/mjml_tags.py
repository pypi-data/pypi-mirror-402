"""MJML Tags - Email templating components for temple.

This module provides MJML-specific HTML components for building responsive
email templates using the temple templating system.

Example Usage:
    from temple.mjml_tags import mjml, mj_body, mj_section, mj_column, mj_text
    
    email = mjml(
        mj_body(
            mj_section(
                mj_column(
                    mj_text("Hello World!")
                )
            )
        )
    )
"""

from maler.tags import Node, convert
from maler.renderer import Renderable
from typing import Any


# =============================================================================
# MJML DOCUMENT STRUCTURE
# =============================================================================

def mjml(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML root element."""
    return Node(name="mjml", body=convert(body), attributes=kwargs)


def mj_head(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML head element for metadata and styles."""
    return Node(name="mj-head", body=convert(body), attributes=kwargs)


def mj_body(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML body element for email content."""
    return Node(name="mj-body", body=convert(body), attributes=kwargs)


def mj_title(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML title element."""
    return Node(name="mj-title", body=convert(body), attributes=kwargs)


def mj_preview(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML preview element for email preview text."""
    return Node(name="mj-preview", body=convert(body), attributes=kwargs)


def mj_attributes(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML attributes element for default attribute values."""
    return Node(name="mj-attributes", body=convert(body), attributes=kwargs)


def mj_all(**kwargs: Any) -> Node:
    """Create an MJML all element for global attributes."""
    return Node(name="mj-all", attributes=kwargs)


def mj_style(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML style element for custom CSS."""
    return Node(name="mj-style", body=convert(body), attributes=kwargs)


# =============================================================================
# MJML LAYOUT COMPONENTS
# =============================================================================

def mj_section(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML section element (full-width container)."""
    return Node(name="mj-section", body=convert(body), attributes=kwargs)


def mj_column(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML column element (responsive column)."""
    return Node(name="mj-column", body=convert(body), attributes=kwargs)


def mj_group(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML group element for grouping columns."""
    return Node(name="mj-group", body=convert(body), attributes=kwargs)


def mj_wrapper(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML wrapper element for wrapping sections."""
    return Node(name="mj-wrapper", body=convert(body), attributes=kwargs)


# =============================================================================
# MJML CONTENT COMPONENTS
# =============================================================================

def mj_text(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML text element for text content."""
    return Node(name="mj-text", body=convert(body), attributes=kwargs)


def mj_button(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML button element for call-to-action buttons."""
    return Node(name="mj-button", body=convert(body), attributes=kwargs)


def mj_image(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML image element for images."""
    return Node(name="mj-image", body=convert(body), attributes=kwargs)


def mj_divider(**kwargs: Any) -> Node:
    """Create an MJML divider element for horizontal dividers."""
    return Node(name="mj-divider", attributes=kwargs)


def mj_spacer(**kwargs: Any) -> Node:
    """Create an MJML spacer element for vertical spacing."""
    return Node(name="mj-spacer", attributes=kwargs)


# =============================================================================
# MJML NAVIGATION COMPONENTS
# =============================================================================

def mj_navbar(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML navbar element for navigation bars."""
    return Node(name="mj-navbar", body=convert(body), attributes=kwargs)


def mj_navbar_link(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML navbar-link element for navigation links."""
    return Node(name="mj-navbar-link", body=convert(body), attributes=kwargs)


# =============================================================================
# MJML SOCIAL COMPONENTS
# =============================================================================

def mj_social(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML social element for social media links."""
    return Node(name="mj-social", body=convert(body), attributes=kwargs)


def mj_social_element(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML social-element for individual social links."""
    return Node(name="mj-social-element", body=convert(body), attributes=kwargs)


# =============================================================================
# MJML TABLE COMPONENTS
# =============================================================================

def mj_table(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML table element for tables."""
    return Node(name="mj-table", body=convert(body), attributes=kwargs)


# =============================================================================
# MJML INTERACTIVE COMPONENTS
# =============================================================================

def mj_accordion(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML accordion element for accordion menus."""
    return Node(name="mj-accordion", body=convert(body), attributes=kwargs)


def mj_accordion_element(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML accordion-element for accordion items."""
    return Node(name="mj-accordion-element", body=convert(body), attributes=kwargs)


def mj_accordion_title(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML accordion-title for accordion titles."""
    return Node(name="mj-accordion-title", body=convert(body), attributes=kwargs)


def mj_accordion_text(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML accordion-text for accordion content."""
    return Node(name="mj-accordion-text", body=convert(body), attributes=kwargs)


def mj_carousel(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML carousel element for image carousels."""
    return Node(name="mj-carousel", body=convert(body), attributes=kwargs)


def mj_carousel_image(**kwargs: Any) -> Node:
    """Create an MJML carousel-image for carousel images."""
    return Node(name="mj-carousel-image", attributes=kwargs)


# =============================================================================
# MJML UTILITY COMPONENTS
# =============================================================================

def mj_raw(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML raw element for raw HTML content."""
    return Node(name="mj-raw", body=convert(body), attributes=kwargs)


def mj_include(**kwargs: Any) -> Node:
    """Create an MJML include element for including external files."""
    return Node(name="mj-include", attributes=kwargs)


def mj_hero(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an MJML hero element for hero sections."""
    return Node(name="mj-hero", body=convert(body), attributes=kwargs)

