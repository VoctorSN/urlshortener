import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class URLNotFoundException(Exception):
    def __init__(self, detail: str = "URL not found"):
        self.detail = detail


class ShortCodeExistsException(Exception):
    def __init__(self, detail: str = "Short code already exists"):
        self.detail = detail


class URLExpiredException(Exception):
    def __init__(self, detail: str = "URL has expired or been deactivated"):
        self.detail = detail


class InvalidURLException(Exception):
    def __init__(self, detail: str = "Invalid URL"):
        self.detail = detail


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI app."""

    @app.exception_handler(URLNotFoundException)
    async def url_not_found_handler(
        request: Request, exc: URLNotFoundException
    ) -> JSONResponse:
        logger.info(
            "domain_exception_handled event=url_not_found method=%s path=%s detail=%s",
            request.method,
            request.url.path,
            exc.detail,
        )
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @app.exception_handler(ShortCodeExistsException)
    async def short_code_exists_handler(
        request: Request, exc: ShortCodeExistsException
    ) -> JSONResponse:
        logger.warning(
            "domain_exception_handled event=short_code_exists method=%s path=%s detail=%s",
            request.method,
            request.url.path,
            exc.detail,
        )
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @app.exception_handler(URLExpiredException)
    async def url_expired_handler(
        request: Request, exc: URLExpiredException
    ) -> JSONResponse:
        logger.info(
            "domain_exception_handled event=url_expired method=%s path=%s detail=%s",
            request.method,
            request.url.path,
            exc.detail,
        )
        return JSONResponse(status_code=410, content={"detail": exc.detail})

    @app.exception_handler(InvalidURLException)
    async def invalid_url_handler(
        request: Request, exc: InvalidURLException
    ) -> JSONResponse:
        logger.info(
            "domain_exception_handled event=invalid_url method=%s path=%s detail=%s",
            request.method,
            request.url.path,
            exc.detail,
        )
        return JSONResponse(status_code=422, content={"detail": exc.detail})
