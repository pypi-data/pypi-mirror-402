from typing import Awaitable, Callable, ParamSpec, TypeVar, overload
from maler import Renderable
import inspect

from maler.tags import Variable

T = TypeVar("T")
P = ParamSpec("P")


def render_mjml(content: Renderable) -> str:
    import mrml 

    return mrml.to_html(
        content.render()
    ).content


@overload
def mjml_template(func: Callable[P, Renderable]) -> Callable[P, str]:
    ...

@overload
def mjml_template(func: Callable[P, Awaitable[Renderable]]) -> Callable[P, Awaitable[str]]:
    ...

def mjml_template(
    func: Callable[P, Renderable] | Callable[P, Awaitable[Renderable]]
) -> Callable[P, str] | Callable[P, Awaitable[str]]:

    if inspect.iscoroutinefunction(func):
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> str:

            content = await func( # type: ignore
                *[Variable(arg) for arg in args], 
                **{key: Variable(value) for key, value in kwargs.items()}
            )

            return render_mjml(content)

        return async_wrapper # type: ignore
    else:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> str:

            content = func( # type: ignore
                *[Variable(arg) for arg in args], 
                **{key: Variable(value) for key, value in kwargs.items()}
            )
            return render_mjml(content) # type: ignore

        return wrapper

    return other

