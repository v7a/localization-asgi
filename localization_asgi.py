"""An ASGI app that provides localization support for your web application."""

from dataclasses import dataclass
from gettext import translation, NullTranslations, GNUTranslations
from typing import cast, Protocol, List, Any, Optional, Type, Tuple

from starlette.datastructures import Scope, URL
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Router, Route

__version__ = "0.1"


class ReadPreferredLocales(Protocol):
    """Read the preferred locales from an ASGI scope. Must return an empty list in case no
    preferred locales exist. Must not raise exceptions.
    """

    def __call__(self, scope: Scope) -> List[str]:
        pass


class WritePreferredLocales(Protocol):
    """Write the preferred locales to an ASGI scope."""

    def __call__(self, scope: Scope, locales: List[str]):
        pass


class GetDomain(Protocol):
    """Get the domain of the translations from an ASGI scope. This allows you to load specific
    translations depending on e.g. the path of a request.
    """

    def __call__(self, scope: Scope) -> Optional[str]:
        pass


@dataclass(frozen=True)
class TranslationConfiguration:
    """Configure the gettext translations querying."""

    # use this domain in case ``get_domain`` returns ``None``
    default_domain: str
    # root path of your locale directory structure (default: None = the gettext default)
    locale_root: Optional[str] = None
    get_domain: GetDomain = lambda scope: None
    translations_class: Type[NullTranslations] = GNUTranslations
    # if no mofiles are found, return NullTranslations instead of raising an error
    fallback: bool = True


def _default_read_locales(scope: Scope) -> List[str]:
    try:
        return scope["session"]["locales"]
    except KeyError:
        return []


def _default_write_locales(scope: Scope, locales: List[str]):
    scope["session"]["locales"] = locales


def _get_locales_and_weights(entry: str) -> Optional[Tuple[str, float]]:
    parts = entry.split(";q=")
    try:
        return (parts[0].strip(), float(parts[1].strip()) if len(parts) == 2 else 1.0)
    except ValueError:
        return None


def _get_sorted_locales(locales_weights: List[Optional[Tuple[str, float]]]) -> List[str]:
    valid_entries = [x for x in locales_weights if x]
    return [x[0] for x in sorted(valid_entries, key=lambda x: x[1], reverse=True)]


def _get_locales(request: Request) -> List[str]:
    try:
        entries = request.headers["accept-language"].split(",")
    except KeyError:
        return []

    return _get_sorted_locales([_get_locales_and_weights(entry) for entry in entries])


class LocalizationMiddleware(BaseHTTPMiddleware):
    """The localization middleware that populates the ASGI scope with the parsed and sorted
    'accept-language' header values.

    config: Translation querying configuration
    read_preferred_locales: Read preferred locales from an ASGI scope
    """

    def __init__(
        self,
        app: Any,
        config: TranslationConfiguration,
        read_preferred_locales: ReadPreferredLocales = _default_read_locales,
    ):
        super().__init__(app)
        self.config = config
        self.read_preferred = read_preferred_locales

    def _get_domain(self, request: Request) -> str:
        return self.config.get_domain(request.scope) or self.config.default_domain

    async def dispatch(self, request: Request, call_next):
        request.scope["locales"] = self.read_preferred(request.scope) or _get_locales(request)
        request.scope["translations"] = translation(
            self._get_domain(request),
            self.config.locale_root,
            # prioritize preferred locales over accept-language
            request.scope["locales"],
            cast(Any, self.config.translations_class),
            self.config.fallback,
        )
        return await call_next(request)


class LocalizationApp(Router):
    """An ASGI app exposing ``/set_locales`` to store a user's locale preference. The app is fully
    configurable in terms of how to store the locales and how to compose the redirect response. The
    endpoint expects the following optional query parameters:

    locales: A comma-separated list of locale identifiers (e.g. en-US) (default: empty)

    redirect: The URL to redirect to after saving the preference (default: "/")

    For security reasons, the netloc of the request's URL and the URL to redirect to must be the
    same, otherwise the default redirect URL is used.

    By default, the locales are written to scope["session"]["locales"] and should work as-is if
    a session middleware was installed that operates on scope["session"].
    """

    def __init__(
        self,
        write_preferred_locales: WritePreferredLocales = _default_write_locales,
        default_redirect_url: str = "/",
        default_locales: Optional[List[str]] = None,
        status_code: int = 303,
        additional_headers: Optional[dict] = None,
    ):
        super().__init__([Route("/set_locales", self._set_locales, name="set_locales")])
        self.write_preferred_locales = write_preferred_locales
        self.default_redirect_url = default_redirect_url
        self.default_locales = default_locales or []
        self.status_code = status_code
        self.additional_headers = additional_headers

    def _get_redirect_url(self, request: Request) -> str:
        try:
            redirect_to = URL(request.query_params["redirect"])
            if not redirect_to.netloc or redirect_to.netloc == request.url.netloc:
                return str(redirect_to)
        except (KeyError, ValueError):
            pass
        return self.default_redirect_url

    def _get_locales(self, request: Request) -> List[str]:
        try:
            return request.query_params["locales"].split(",")
        except KeyError:
            return self.default_locales

    def _set_locales(self, request: Request):
        self.write_preferred_locales(request.scope, self._get_locales(request))
        return RedirectResponse(
            self._get_redirect_url(request), self.status_code, self.additional_headers
        )
