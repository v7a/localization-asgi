"""Tests the localization middleware and ASGI app."""

from base64 import b64decode, b64encode
import json

from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.testclient import TestClient

from localization_asgi import LocalizationMiddleware, LocalizationApp, TranslationConfiguration

current_scope: dict = {}


def make_client() -> TestClient:
    class PlainTextSessionMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            try:
                request.scope["session"] = json.loads(
                    b64decode(request.cookies["session"].encode("utf-8")).decode("utf-8")
                )
            except KeyError:
                request.scope["session"] = {}

            response = await call_next(request)
            response.set_cookie(
                "session",
                b64encode(json.dumps(request.scope["session"]).encode("utf-8")).decode("utf-8"),
            )
            return response

    def dump_scope(request):
        global current_scope
        current_scope = request.scope
        return Response()

    return TestClient(
        Starlette(
            routes=[Route("/dump", dump_scope), Mount("/", app=LocalizationApp())],
            middleware=[
                Middleware(PlainTextSessionMiddleware),
                Middleware(
                    LocalizationMiddleware,
                    config=TranslationConfiguration(default_domain="messages"),
                ),
            ],
        )
    )


def test_locale_parsing():
    client = make_client()
    client.get("/dump", headers={"accept-language": "en;q=0.5, de-DE;q=1.0"})
    assert current_scope["locales"] == ["de-DE", "en"]


def test_invalid_locales():
    client = make_client()
    client.get("/dump", headers={"accept-language": "en;q=0.5, de-DE;q=abc"})
    assert current_scope["locales"] == ["en"]


def test_no_locales():
    client = make_client()
    client.get("/dump")
    assert current_scope["locales"] == []


def test_preferred_locales():
    client = make_client()
    client.get("/set_locales?locales=en,de")
    client.get("/dump", headers={"accept-language": "fr"})
    assert current_scope["locales"] == ["en", "de"]


def test_translations_object():
    client = make_client()
    client.get("/dump")
    assert current_scope["translations"].gettext("hello") == "hello"


def test_good_redirect_no_netloc():
    client = make_client()
    client.get("/set_locales?locales=en&redirect=/dump")
    assert current_scope["locales"] == ["en"]


def test_good_redirect_with_netloc():
    client = make_client()
    client.get(f"/set_locales?locales=en&redirect={client.base_url}/dump")
    assert current_scope["locales"] == ["en"]


def test_malicious_redirect():
    client = make_client()
    resp = client.get(
        "/set_locales?locales=en&redirect=http://somemaliciousurl.com", allow_redirects=False
    )
    assert resp.headers["location"] == LocalizationApp().default_redirect_url


def test_endpoint_no_locales():
    client = make_client()
    client.get("/set_locales?locales=en")
    client.get("/set_locales")
    client.get("/dump")
    assert current_scope["locales"] == []
