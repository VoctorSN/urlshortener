from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


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
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @app.exception_handler(ShortCodeExistsException)
    async def short_code_exists_handler(
        request: Request, exc: ShortCodeExistsException
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @app.exception_handler(URLExpiredException)
    async def url_expired_handler(
        request: Request, exc: URLExpiredException
    ) -> JSONResponse:
        return JSONResponse(status_code=410, content={"detail": exc.detail})

    @app.exception_handler(InvalidURLException)
    async def invalid_url_handler(
        request: Request, exc: InvalidURLException
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.detail})
