"""Temple Tags - HTML component library for server-side rendering.

This module provides a comprehensive set of HTML components and utilities for building
web interfaces using a functional approach. Each HTML element is represented as a
function that returns a Node object, which can be rendered to HTML strings.

Key Features:
- Type-safe HTML generation
- Automatic HTML escaping for security
- Fluent API with method chaining
- Support for conditional rendering and loops
- Comprehensive coverage of HTML5 elements

Example Usage:
    from temple.tags import div, h1, p, a
    
    content = div(
        h1("Welcome"),
        p("This is a paragraph with a ", a("link", href="/page")),
        class_="container"
    )
    
    html_output = content.render()
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, Generic, TYPE_CHECKING

from maler.renderer import Renderable

if TYPE_CHECKING:
    from fastapi.responses import HTMLResponse


logger = logging.getLogger(__name__)


T = TypeVar("T")

@dataclass
class Variable(Renderable):
    """A wrapper for dynamic values that automatically escapes HTML content.
    
    Variables provide a safe way to inject dynamic content into HTML templates
    while preventing XSS attacks through automatic HTML escaping.
    
    Args:
        _value: The value to wrap. Can be any type that converts to string.
        
    Example:
        var = Variable("<script>alert('xss')</script>")
        # Renders as: &lt;script&gt;alert('xss')&lt;/script&gt;
    """

    _value: Any

    def render(self) -> str:
        """Render the variable value as HTML-escaped string."""
        import html
        return html.escape(f"{self._value}")

    def __iter__(self):
        return iter(
            Variable(val).render() if isinstance(val, str) else Variable(val)
            for val in self._value
        )

    def __format__(self, format_spec: str):
        return self._value.__format__(format_spec)

    def __len__(self) -> int:
        return len(self._value)

    def __str__(self) -> str:
        return self.render()

    def __bool__(self):
        if self._value is None:
            return False
        return bool(self._value)

    def __invert__(self):
        return ~self._value

    def __contains__(self, element):
        if isinstance(element, Variable):
            return element._value in self._value
        else:
            return element in self._value

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self._value == other._value
        else:
            return self._value == other

    def __gt__(self, other):
        if isinstance(other, Variable):
            return self._value > other._value
        else:
            return self._value > other

    def __lt__(self, other):
        if isinstance(other, Variable):
            return self._value < other._value
        else:
            return self._value < other

    def __le__(self, other):
        if isinstance(other, Variable):
            return self._value <= other._value
        else:
            return self._value <= other

    def __ge__(self, other):
        if isinstance(other, Variable):
            return self._value >= other._value
        else:
            return self._value >= other

    def __getitem__(self, item):
        return Variable(self._value[item])

    def __hash__(self) -> int:
        return hash(self._value)

    def __mul__(self, value: Any) -> Variable:
        return Variable(self._value * value)

    def __getattr__(self, name):
        """Access attributes of the wrapped value, returning new Variable instances."""

        if isinstance(self._value, dict) and not hasattr(self._value, name):
            val = self._value[name]
        else:
            val = getattr(self._value, name)

        if isinstance(val, str):
            return Variable(val)

        if isinstance(val, (int, float, datetime, timezone, date)):
            return val

        return Variable(val)

    def __call__(self, *args, **kwargs):
        """Call the wrapped value if callable, returning a new Variable."""
        val = self._value(*args, **kwargs)
        if isinstance(val, str):
            return Variable(val)
        return Variable(val)

@dataclass
class UnsafeString(Renderable):
    """A string that renders without HTML escaping.
    
    Use with caution! Only use when you're certain the content is safe
    or when you need to inject raw HTML content.
    
    Args:
        content: Raw string content to render without escaping.
        
    Example:
        unsafe = UnsafeString("<strong>Bold text</strong>")
        # Renders as: <strong>Bold text</strong>
    """

    content: str

    def render(self) -> str:
        """Render the content without HTML escaping."""

        if isinstance(self.content, Variable):
            return str(self.content._value)

        return self.content


@dataclass
class RenderRequest(Generic[T]):
    template: Callable[[T], Renderable]
    content: T

    def response(self) -> "HTMLResponse":
        from fastapi.responses import HTMLResponse 

        return HTMLResponse(
            content=self.template(Variable(self.content)).render() # type: ignore
        )



@dataclass(init=False)
class Concat(Renderable):
    values: list[Renderable]

    def __init__(self, values: list[Renderable | str]):
        self.values = [ convert(val) for val in values ]

    def render(self) -> str:
        return "".join([
            el.render() for el in self.values
        ])

@dataclass 
class ForEach(Generic[T]):

    values: list[T]
    content: Callable[[T], Renderable] | Callable[[T], list[Renderable]]

    def render(self) -> str:

        return "".join([
            convert(self.content(val)).render()
            for val in self.values
        ])


@dataclass 
class If:

    condition: bool
    content: Callable[[], Renderable | list[Renderable]]

    def render(self) -> str:
        if not self.condition:
            return ""
        content = self.content()
        if isinstance(content, list):
            return "".join([
                val.render() for val in content
            ])
        return content.render()

    def else_if(self, condition: bool, content: Callable[[], Renderable | list[Renderable]]) -> ElseIf:
        return ElseIf(
            [self, If(condition, content)]
        )

    def else_unwrap(self, value: T | None, content: Callable[[T], Renderable | list[Renderable]]) -> ElseIf:
        if not isinstance(value, Variable):
            return self.else_if(value != None, lambda: content(value)) # type: ignore
        else:
            return self.else_if(value._value != None, lambda: content(value))

    def else_(self, content: Callable[[], Renderable | list[Renderable]]) -> Renderable:
        return self.else_if(True, content)


@dataclass
class ElseIf:
    ifs: list[If]

    def render(self) -> str:
        for if_condition in self.ifs:
            if if_condition.condition:
                return if_condition.render()
        return ""

    def else_if(self, condition: bool, content: Callable[[], Renderable | list[Renderable]]) -> ElseIf:
        return ElseIf(
            [*self.ifs, If(condition, content)]
        )

    def else_(self, content: Callable[[], Renderable | list[Renderable]]) -> Renderable:
        return self.else_if(True, content)


def convert(value: Renderable | Any | list[Renderable | Any]) -> Renderable:
    """Convert various types to Renderable objects.
    
    This function handles the conversion of different input types to objects
    that implement the Renderable protocol. It's used internally by HTML
    element functions to process their content.
    
    Args:
        value: Input value to convert. Can be:
               - Renderable object (returned as-is)
               - String (wrapped in UnsafeString)
               - List/tuple (wrapped in Concat)
               - Other types (returned as-is, assuming they're Renderable)
    
    Returns:
        A Renderable object that can be rendered to HTML.
        
    Example:
        convert("Hello")  # Returns UnsafeString("Hello")
        convert(["A", "B"])  # Returns Concat([UnsafeString("A"), UnsafeString("B")])
    """
    if value is None:
        return UnsafeString("")

    if isinstance(value, bool):
        return UnsafeString(f"{value}".lower())

    if isinstance(value, (list, tuple)):
        return Concat([
            convert(val) for val in value
        ])

    if isinstance(value, str):
        return UnsafeString(value)

    if not hasattr(value, "render"):
        return Variable(value)
    else:
        return value


@dataclass
class Node(Renderable):
    """Represents an HTML element with attributes and content.
    
    The Node class is the foundation for all HTML elements in the temple system.
    It handles rendering HTML tags with proper attribute formatting and content.
    
    Args:
        name: The HTML tag name (e.g., 'div', 'span', 'h1')
        body: Optional content inside the element
        attributes: Dictionary of HTML attributes
        
    Example:
        node = Node("div", UnsafeString("Hello"), {"class": "greeting"})
        # Renders as: <div class="greeting">Hello</div>
    """

    name: str
    body: Renderable | None = field(default=None)
    attributes: dict[str, Any] = field(default_factory=dict)

    def render(self) -> str:
        """Render the HTML element as a string.
        
        Returns:
            Complete HTML element string with attributes and content.
            
        Raises:
            ValueError: If body doesn't implement Renderable protocol.
        """
        assert not callable(self.body), f"Found callable when expecting Renderable in '{self.name}'"
        attr = " ".join([
            f'{key}="{convert(value).render()}"'
            for key, value in self.attributes.items() 
        ])

        attrs = []
        for key, value in self.attributes.items():
            if value is None:
                continue

            attr_key = key.rstrip("_").replace("_", "-")
            if isinstance(value, bool):
                if value:
                    attrs.append(attr_key)
            else:
                attrs.append(f'{attr_key}="{convert(value).render()}"')


        attr = ""
        if attrs:
            attr = " " + " ".join(attrs)
        try:
            if self.body:
                return f"<{self.name}{attr}>{self.body.render()}</{self.name}>"
            else:
                return f"<{self.name}{attr}/>"
        except AttributeError as e: 
            raise ValueError(f"Unable to render {self.body}, make sure it is conforming to the Renderable protocol, {attr}") from e

    def with_class(self, values: str) -> "Node":
        """Add CSS class to the element. Returns self for method chaining."""
        self.attributes["class"] = values
        return self

    def with_type(self, value: str) -> "Node":
        """Add type attribute to the element. Returns self for method chaining."""
        self.attributes["type"] = value
        return self

    def with_for(self, value: str) -> "Node":
        """Add for attribute to the element. Returns self for method chaining."""
        self.attributes["for"] = value
        return self



# =============================================================================
# DOCUMENT STRUCTURE
# =============================================================================

def html(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML html element (document root)."""
    return Node(name="html", body=convert(body), attributes=kwargs)

def head(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML head element for document metadata."""
    return Node(name="head", body=convert(body), attributes=kwargs)

def body(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML body element for document content."""
    return Node(name="body", body=convert(body), attributes=kwargs)

def title(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML title element for document title."""
    return Node(name="title", body=convert(body), attributes=kwargs)

def meta(**kwargs: Any) -> Node:
    """Create an HTML meta element for document metadata."""
    return Node(name="meta", attributes=kwargs)


# =============================================================================
# BASIC HEADINGS (H1-H3 were already defined)
# =============================================================================

def h1(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML h1 heading element (highest level)."""
    return Node(name="h1", body=convert(body), attributes=kwargs)

def h2(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML h2 heading element."""
    return Node(name="h2", body=convert(body), attributes=kwargs)

def h3(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML h3 heading element."""
    return Node(name="h3", body=convert(body), attributes=kwargs)


# =============================================================================
# BASIC TEXT AND CONTENT
# =============================================================================

def div(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML div element for generic containers."""
    return Node(name="div", body=convert(body), attributes=kwargs)

def p(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML p element for paragraphs."""
    return Node(name="p", body=convert(body), attributes=kwargs)

def span(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML span element for inline content."""
    return Node(name="span", body=convert(body), attributes=kwargs)

def a(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML a element for links."""
    return Node(name="a", body=convert(body), attributes=kwargs)


# =============================================================================
# LISTS
# =============================================================================

def ul(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML ul element for unordered lists."""
    return Node(name="ul", body=convert(body), attributes=kwargs)

def ol(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML ol element for ordered lists."""
    return Node(name="ol", body=convert(body), attributes=kwargs)

def li(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML li element for list items."""
    return Node(name="li", body=convert(body), attributes=kwargs)

def dl(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML dl element for description lists."""
    return Node(name="dl", body=convert(body), attributes=kwargs)

def dt(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML dt element for description terms."""
    return Node(name="dt", body=convert(body), attributes=kwargs)

def dd(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML dd element for description details."""
    return Node(name="dd", body=convert(body), attributes=kwargs)


# =============================================================================
# NAVIGATION AND LAYOUT
# =============================================================================

def nav(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML nav element for navigation links."""
    return Node(name="nav", body=convert(body), attributes=kwargs)

def footer(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML footer element for page/section footers."""
    return Node(name="footer", body=convert(body), attributes=kwargs)


# =============================================================================
# TABLES (Basic table already defined)
# =============================================================================

def table(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML table element for tabular data."""
    return Node(name="table", body=convert(body), attributes=kwargs)


# =============================================================================
# MEDIA AND GRAPHICS
# =============================================================================

def img(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML img element for images."""
    return Node(name="img", body=convert(body), attributes=kwargs)

def svg(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML svg element for vector graphics."""
    return Node(name="svg", body=convert(body), attributes=kwargs)

def circle(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML svg element for vector graphics."""
    return Node(name="circle", body=convert(body), attributes=kwargs)

def path(**kwargs: Any) -> Node:
    """Create an HTML path element for SVG paths."""
    return Node(name="path", attributes=kwargs)


# =============================================================================
# FORMS AND INPUT (Basic form elements already defined)
# =============================================================================

def form(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML form element for user input forms."""
    return Node(name="form", body=convert(body), attributes=kwargs)

def input(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML input element for user input."""
    return Node(name="input", body=convert(body), attributes=kwargs)

def button(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML button element for clickable buttons."""
    return Node(name="button", body=convert(body), attributes=kwargs)

def label(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML label element for form labels."""
    return Node(name="label", body=convert(body), attributes=kwargs)


# =============================================================================
# SCRIPTING
# =============================================================================

def script(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML script element for JavaScript code."""
    return Node(name="script", body=convert(body), attributes=kwargs)

def for_each(values: list[T], content: Callable[[T], Renderable] | Callable[[T], list[Renderable]]) -> ForEach:
    """Create a loop component for rendering lists of items.
    
    This helper function creates a ForEach component that iterates over a list
    of values and renders content for each item using the provided function.
    
    Args:
        values: List of items to iterate over
        content: Function that takes an item and returns Renderable content
        
    Returns:
        ForEach component that renders the content for each item
        
    Example:
        users = [{'name': 'Alice'}, {'name': 'Bob'}]
        user_list = for_each(users, lambda user: li(user['name']))
    """
    return ForEach(values, content)

def if_(condition: bool, content: Callable[[], Renderable | list[Renderable]]) -> Renderable:
    """Create a conditional rendering component.
    
    Args:
        condition: Boolean condition to evaluate
        content: Function that returns content to render if condition is True
        
    Returns:
        If component that renders content conditionally
    """
    return If(condition, content)

def unwrap(value: T | None, content: Callable[[T], Renderable | list[Renderable]]) -> If:
    """Create a conditional rendering component.
    
    Args:
        condition: Boolean condition to evaluate
        content: Function that returns content to render if condition is True
        
    Returns:
        If component that renders content conditionally
    """
    if not isinstance(value, Variable):
        return If(value != None, lambda: content(value)) # type: ignore
    else:
        return If(value._value != None, lambda: content(value))



# =============================================================================
# HTML5 SEMANTIC ELEMENTS
# =============================================================================

def header(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML header element."""
    return Node(name="header", body=convert(body), attributes=kwargs)

def main(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML main element."""
    return Node(name="main", body=convert(body), attributes=kwargs)

def section(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML section element."""
    return Node(name="section", body=convert(body), attributes=kwargs)

def article(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML article element."""
    return Node(name="article", body=convert(body), attributes=kwargs)

def aside(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML aside element."""
    return Node(name="aside", body=convert(body), attributes=kwargs)

def figure(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML figure element."""
    return Node(name="figure", body=convert(body), attributes=kwargs)

def figcaption(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML figcaption element."""
    return Node(name="figcaption", body=convert(body), attributes=kwargs)


# =============================================================================
# HEADINGS AND TEXT CONTENT
# =============================================================================

def h4(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML h4 heading element."""
    return Node(name="h4", body=convert(body), attributes=kwargs)

def h5(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML h5 heading element."""
    return Node(name="h5", body=convert(body), attributes=kwargs)

def h6(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML h6 heading element."""
    return Node(name="h6", body=convert(body), attributes=kwargs)

def strong(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML strong element for important text."""
    return Node(name="strong", body=convert(body), attributes=kwargs)

def em(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML em element for emphasized text."""
    return Node(name="em", body=convert(body), attributes=kwargs)

def small(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML small element for fine print."""
    return Node(name="small", body=convert(body), attributes=kwargs)

def mark(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML mark element for highlighted text."""
    return Node(name="mark", body=convert(body), attributes=kwargs)

def del_(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML del element for deleted text."""
    return Node(name="del", body=convert(body), attributes=kwargs)

def ins(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML ins element for inserted text."""
    return Node(name="ins", body=convert(body), attributes=kwargs)

def sub(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML sub element for subscript text."""
    return Node(name="sub", body=convert(body), attributes=kwargs)

def sup(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML sup element for superscript text."""
    return Node(name="sup", body=convert(body), attributes=kwargs)

def code(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML code element for inline code."""
    return Node(name="code", body=convert(body), attributes=kwargs)

def pre(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML pre element for preformatted text."""
    return Node(name="pre", body=convert(body), attributes=kwargs)

def blockquote(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML blockquote element for quotations."""
    return Node(name="blockquote", body=convert(body), attributes=kwargs)

def cite(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML cite element for citation references."""
    return Node(name="cite", body=convert(body), attributes=kwargs)

def abbr(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML abbr element for abbreviations."""
    return Node(name="abbr", body=convert(body), attributes=kwargs)

def time(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML time element for dates and times."""
    return Node(name="time", body=convert(body), attributes=kwargs)


# =============================================================================
# FORM ELEMENTS
# =============================================================================

def fieldset(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML fieldset element for grouping form controls."""
    return Node(name="fieldset", body=convert(body), attributes=kwargs)

def legend(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML legend element for fieldset captions."""
    return Node(name="legend", body=convert(body), attributes=kwargs)

def select(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML select element for dropdown menus."""
    return Node(name="select", body=convert(body), attributes=kwargs)

def option(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML option element for select options."""
    return Node(name="option", body=convert(body), attributes=kwargs)

def optgroup(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML optgroup element for grouping select options."""
    return Node(name="optgroup", body=convert(body), attributes=kwargs)

def textarea(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML textarea element for multi-line text input."""
    return Node(name="textarea", body=convert(body), attributes=kwargs)

def datalist(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML datalist element for input suggestions."""
    return Node(name="datalist", body=convert(body), attributes=kwargs)

def output(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML output element for calculation results."""
    return Node(name="output", body=convert(body), attributes=kwargs)

def progress(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML progress element for progress bars."""
    return Node(name="progress", body=convert(body), attributes=kwargs)

def meter(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML meter element for scalar measurements."""
    return Node(name="meter", body=convert(body), attributes=kwargs)


# =============================================================================
# TABLE ELEMENTS
# =============================================================================

def thead(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML thead element for table headers."""
    return Node(name="thead", body=convert(body), attributes=kwargs)

def tbody(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML tbody element for table body content."""
    return Node(name="tbody", body=convert(body), attributes=kwargs)

def tfoot(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML tfoot element for table footers."""
    return Node(name="tfoot", body=convert(body), attributes=kwargs)

def tr(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML tr element for table rows."""
    return Node(name="tr", body=convert(body), attributes=kwargs)

def th(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML th element for table header cells."""
    return Node(name="th", body=convert(body), attributes=kwargs)

def td(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML td element for table data cells."""
    return Node(name="td", body=convert(body), attributes=kwargs)

def caption(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML caption element for table captions."""
    return Node(name="caption", body=convert(body), attributes=kwargs)

def colgroup(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML colgroup element for column groups."""
    return Node(name="colgroup", body=convert(body), attributes=kwargs)

def col(**kwargs: Any) -> Node:
    """Create an HTML col element for table columns."""
    return Node(name="col", attributes=kwargs)


# =============================================================================
# MULTIMEDIA ELEMENTS
# =============================================================================

def audio(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML audio element for audio content."""
    return Node(name="audio", body=convert(body), attributes=kwargs)

def video(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML video element for video content."""
    return Node(name="video", body=convert(body), attributes=kwargs)

def source(**kwargs: Any) -> Node:
    """Create an HTML source element for media resources."""
    return Node(name="source", attributes=kwargs)

def track(**kwargs: Any) -> Node:
    """Create an HTML track element for media tracks."""
    return Node(name="track", attributes=kwargs)

def canvas(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML canvas element for graphics."""
    return Node(name="canvas", body=convert(body), attributes=kwargs)

def embed(**kwargs: Any) -> Node:
    """Create an HTML embed element for embedded content."""
    return Node(name="embed", attributes=kwargs)

def object_(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML object element for embedded objects."""
    return Node(name="object", body=convert(body), attributes=kwargs)

def param(**kwargs: Any) -> Node:
    """Create an HTML param element for object parameters."""
    return Node(name="param", attributes=kwargs)

def iframe(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML iframe element for inline frames."""
    return Node(name="iframe", body=convert(body), attributes=kwargs)


# =============================================================================
# SCRIPTING AND STYLE ELEMENTS
# =============================================================================

def noscript(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML noscript element for fallback content."""
    return Node(name="noscript", body=convert(body), attributes=kwargs)

def template(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML template element for client-side templates."""
    return Node(name="template", body=convert(body), attributes=kwargs)

def style(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML style element for CSS styles."""
    return Node(name="style", body=convert(body), attributes=kwargs)

def link(**kwargs: Any) -> Node:
    """Create an HTML link element for external resources."""
    return Node(name="link", attributes=kwargs)

def base(**kwargs: Any) -> Node:
    """Create an HTML base element for document base URL."""
    return Node(name="base", attributes=kwargs)


# =============================================================================
# INTERACTIVE ELEMENTS
# =============================================================================

def details(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML details element for disclosure widgets."""
    return Node(name="details", body=convert(body), attributes=kwargs)

def summary(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML summary element for details summaries."""
    return Node(name="summary", body=convert(body), attributes=kwargs)

def dialog(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML dialog element for modal dialogs."""
    return Node(name="dialog", body=convert(body), attributes=kwargs)


# =============================================================================
# WEB COMPONENTS AND CUSTOM ELEMENTS
# =============================================================================

def slot(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML slot element for web component slots."""
    return Node(name="slot", body=convert(body), attributes=kwargs)

def kbd(*body: Renderable | str, **kwargs: Any) -> Node:
    """Create an HTML span element for inline content."""
    return Node(name="kbd", body=convert(body), attributes=kwargs)


