import setuptools


with open("README.md", "r") as readme:
    setuptools.setup(
        name="localization-asgi",
        version="0.1",
        author="v7a",
        long_description=readme.read(),
        long_description_content_type="text/markdown",
        url="https://github.com/v7a/localization-asgi",
        keywords=["asgi", "localization", "middleware"],
        install_requires=["starlette>=0.13,<1"],
        py_modules=["localization_asgi"],
        license="MIT",
        project_urls={
            "Source": "https://github.com/v7a/localization-asgi",
            "Tracker": "https://github.com/v7a/localization-asgi/issues",
        },
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Programming Language :: Python :: 3 :: Only",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Topic :: Internet :: WWW/HTTP",
            "Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware",
        ],
    )
