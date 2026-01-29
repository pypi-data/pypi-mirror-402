import logging
from typing import TYPE_CHECKING, Callable, Awaitable, TypeVar
from maler.renderer import Renderable
from maler.tags import RenderRequest, Variable

from functools import wraps
import inspect


if TYPE_CHECKING:
    from fastapi import Response


RenderableFunction = Callable[..., RenderRequest] | Callable[..., Awaitable[RenderRequest]]

logger = logging.getLogger(__name__)

T = TypeVar("T")

def html_template(func: RenderableFunction):

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Response:
        from fastapi.responses import HTMLResponse 

        if inspect.iscoroutinefunction(func):
            res = await func(*args, **kwargs)
        else:
            res = func(*args, **kwargs)

        if not isinstance(res, RenderRequest):
            return res # type: ignore

        return HTMLResponse(
            content=res.template(
                Variable(res.content) # type: ignore
            ).render()
        )

    return wrapper


def render_template(template: Callable[[T], Renderable], failure_template: Callable[[Exception], Renderable] | None = None):
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi import Request, Response
    from pydantic import BaseModel

    def render(func: Callable[..., T] | Callable[..., Awaitable[T]]):

        signature = inspect.signature(func)

        req_name = None
        should_pass_request = False

        for param in signature.parameters.values():
            if isinstance(param.annotation, type) and issubclass(param.annotation, Request):
                req_name = param.name
                should_pass_request = True


        new_sig = None

        if req_name is None:
            req_name = "_raw_request"
            func.__signature__ = inspect.Signature(
                [
                    *signature.parameters.values(), 
                    inspect.Parameter(
                        name=req_name, 
                        kind=inspect._ParameterKind.KEYWORD_ONLY, 
                        annotation=Request
                    )
                ],
                return_annotation=signature.return_annotation
            )

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Response:
            req = kwargs[req_name]
            try:
                if not should_pass_request:
                    del kwargs[req_name]

                if inspect.iscoroutinefunction(func):
                    res = await func(*args, **kwargs)
                else:
                    res = func(*args, **kwargs)


                if isinstance(req, Request) and req.headers.get("Accept-Encoding") == "application/json":
                    if isinstance(res, BaseModel):
                        return Response(
                            content=res.model_dump_json(),
                            media_type="application/json"
                        )
                    elif isinstance(res, list):
                        return Response(
                            content="[" + ", ".join([
                                val.model_dump_json() if isinstance(val, BaseModel) else val
                                for val in res
                            ]) + "]",
                            media_type="application/json"
                        )
                    else:
                        return JSONResponse(content=res)

                return HTMLResponse(
                    content=template(Variable(res)).render() # type: ignore
                )
            except Exception as e:
                logger.exception(e)
                if isinstance(req, Request) and req.headers.get("Accept-Encoding") == "application/json":
                    raise e

                failure_temp = failure_template(e) if failure_template is not None else div("Ups! An error occurred!")
                return HTMLResponse(content=failure_temp.render())

        return wrapper
    return render


