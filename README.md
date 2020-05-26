# ASGI localization app
An ASGI app that provides localization support for your web application.

## What is included?
* A middleware populating `scope["locales"]` with the request's `accept-language` values ordered by weight.
  * It also populates `scope["translations"]` with a user-defined translations instance (default: `gettext.GNUTranslations`)
  * It allows preferred locales regardless of `accept-language` by e.g. using sessions, `scope["locales"]` will then contain
    these
* An ASGI app exposing an endpoint to switch the preferred locales.

## Contributing
Before committing, run the following and check if it succeeds:
```sh
pip install --user -r requirements-dev.txt && \
black localization_asgi.py && \
pylint localization_asgi.py && \
pytest && \
coverage report --fail-under=100
```
