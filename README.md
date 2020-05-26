# ASGI localization app
An ASGI app that provides localization support for your web application.

## What is included?
* A middleware populating `scope["locales"]` with the request's `accept-language` values ordered by weight.
* It also populates `scope["translations"]` with a user-defined translations instance (default: `gettext.GNUTranslations`).
* It allows preferred locales regardless of `accept-language` by e.g. using sessions, `scope["locales"]` will then contain these.
* An ASGI app exposing an endpoint to switch the preferred locales.
* Sensible defaults for everything from configuring gettext to interfacing with the ASGI scope to read the preferred locales

## How?
A minimal example using [starlette](https://github.com/encode/starlette):
```python
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response
from starlette.routing import Route, Mount
from localization_asgi import LocalizationMiddleware, LocalizationApp, TranslationConfiguration

def hello_world(request):
    return Response(request["translations"].gettext("hello world"))

app = Starlette(
    routes=[Route("/", hello_world), Mount("/", app=LocalizationApp())],
    middleware=[
        Middleware(SessionMiddleware, secret_key="secret"),
        Middleware(
            LocalizationMiddleware, config=TranslationConfiguration(default_domain="messages")
        ),
    ],
)
```

For more information on how to configure the middleware or app, please consult the docstrings of
`LocalizationMiddleware`, `LocalizationApp` and `TranslationConfiguration`.

## Contributing
Before committing, run the following and check if it succeeds:
```sh
pip install --user -r requirements-dev.txt && \
black localization_asgi.py && \
pylint localization_asgi.py && \
pytest && \
coverage report --fail-under=100
```
