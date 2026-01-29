import inspect
from typing import Awaitable, Callable, Protocol, ParamSpec, overload

P = ParamSpec("P")


class Renderable(Protocol):
    def render(self) -> str:
        ...

@overload
def template(func: Callable[P, Renderable]) -> Callable[P, str]:
    ...

@overload
def template(func: Callable[P, Awaitable[Renderable]]) -> Callable[P, Awaitable[str]]:
    ...

def template(func: Callable[P, Renderable] | Callable[P, Awaitable[Renderable]]) -> Callable[P, str] | Callable[P, Awaitable[str]]:
    from maler.tags import Variable

    if inspect.iscoroutinefunction(func):
        async def inner(*args: P.args, **kwargs: P.kwargs) -> str: # type: ignore
            temp = await func( # type: ignore
                *[Variable(arg) for arg in args], 
                **{key: Variable(value) for key, value in kwargs.items()}
            )
            return temp.render()

        return inner

    else:
        def inner(*args: P.args, **kwargs: P.kwargs) -> str:
            temp = func( # type: ignore
                *[Variable(arg) for arg in args], 
                **{key: Variable(value) for key, value in kwargs.items()}
            )
            return temp.render() # type: ignore

        return inner

