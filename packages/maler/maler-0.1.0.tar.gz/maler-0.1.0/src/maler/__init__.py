"""Temple - HTML templating library for Python.

Temple provides a type-safe, functional approach to generating HTML in Python.
All HTML5 elements are available as functions that return renderable components.

Example:
    from temple import div, h1, p, a
    
    page = div(
        h1("Welcome to Temple"),
        p("Build HTML with ", a("type safety", href="/docs")),
        class_="container"
    )
    
    html_output = page.render()
"""

# Import all components from tags module
from maler.fastapi import html_template, render_template
from maler.tags import (
    # Core classes
    Variable,
    UnsafeString,
    Concat,
    Node,
    RenderRequest,
    
    # Helper functions
    convert,
    for_each,
    if_,
    unwrap,
    
    # Document structure
    html,
    head,
    body,
    title,
    meta,
    base,
    link,
    
    # Headings
    h1,
    h2,
    h3,
    h4,
    h5,
    h6,
    
    # Text content
    p,
    div,
    span,
    a,
    strong,
    em,
    small,
    mark,
    del_,
    ins,
    sub,
    sup,
    code,
    pre,
    blockquote,
    cite,
    abbr,
    time,
    
    # Lists
    ul,
    ol,
    li,
    dl,
    dt,
    dd,
    
    # Tables
    table,
    thead,
    tbody,
    tfoot,
    tr,
    th,
    td,
    caption,
    colgroup,
    col,
    
    # Forms
    form,
    input,
    button,
    label,
    select,
    option,
    optgroup,
    textarea,
    fieldset,
    legend,
    datalist,
    output,
    progress,
    meter,
    
    # Semantic elements
    header,
    main,
    section,
    article,
    aside,
    nav,
    footer,
    figure,
    figcaption,
    
    # Media
    img,
    audio,
    video,
    source,
    track,
    canvas,
    svg,
    circle,
    path,
    embed,
    object_,
    param,
    iframe,
    
    # Interactive
    details,
    summary,
    dialog,
    
    # Scripting
    script,
    noscript,
    template,
    style,
    
    # Web components
    slot,
    kbd
)

# Define what gets exported when using "from temple import *"
__all__ = [
    # Core classes
    'Variable',
    'UnsafeString', 
    'Concat',
    'Node',
    'RenderRequest',
    
    # Helper functions
    'convert',
    'for_each',
    'if_',
    'unwrap',
    'html_template',
    'render_template',
    
    # Document structure
    'html',
    'head',
    'body',
    'title',
    'meta',
    'base',
    'link',
    
    # Headings
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    
    # Text content
    'p',
    'div',
    'span',
    'a',
    'strong',
    'em',
    'small',
    'mark',
    'del_',
    'ins',
    'sub',
    'sup',
    'code',
    'pre',
    'blockquote',
    'cite',
    'abbr',
    'time',
    
    # Lists
    'ul',
    'ol',
    'li',
    'dl',
    'dt',
    'dd',
    
    # Tables
    'table',
    'thead',
    'tbody',
    'tfoot',
    'tr',
    'th',
    'td',
    'caption',
    'colgroup',
    'col',
    
    # Forms
    'form',
    'input',
    'button',
    'label',
    'select',
    'option',
    'optgroup',
    'textarea',
    'fieldset',
    'legend',
    'datalist',
    'output',
    'progress',
    'meter',
    
    # Semantic elements
    'header',
    'main',
    'section',
    'article',
    'aside',
    'nav',
    'footer',
    'figure',
    'figcaption',
    
    # Media
    'img',
    'audio',
    'video',
    'source',
    'track',
    'canvas',
    'svg',
    'circle',
    'path',
    'embed',
    'object_',
    'param',
    'iframe',
    
    # Interactive
    'details',
    'summary',
    'dialog',
    
    # Scripting
    'script',
    'noscript',
    'template',
    'style',
    
    # Web components
    'slot',
    'kbd',
]

