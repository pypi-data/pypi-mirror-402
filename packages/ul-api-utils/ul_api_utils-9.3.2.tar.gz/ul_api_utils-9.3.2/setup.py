from os import path
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='ul_api_utils',
    version='9.3.2',
    description='Python api utils',
    author='Unic-lab',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email='',
    packages=find_packages(),
    package_data={
        "ul_api_utils": [
            'py.typed',
            "utils/flask_swagger_ui/templates/*.html",
            "utils/flask_swagger_ui/static/*.html",
            "utils/flask_swagger_ui/static/*.js",
            "utils/flask_swagger_ui/static/*.css",
            "utils/flask_swagger_ui/static/*.png",
            "utils/flask_swagger_ui/static/*.map",
            "conf/ul-debugger-main.js",
            "conf/ul-debugger-ui.js",
        ],
    },
    entry_points={
        "console_scripts": [
            'ulapiutls=ul_api_utils.main:main',
        ],
    },
    include_package_data=True,
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    platforms='any',
    install_requires=[
        "ul-unipipeline==2.0.6",
        "jinja2==3.1.6",
        "flask==3.1.0",
        "flask-wtf==1.2.2",
        "flask-limiter==3.10.1",
        "flask-caching==2.3.1",
        "flask-swagger-ui==4.11.1",
        "flask-monitoringdashboard==3.3.2",
        "pycryptodome==3.21.0",
        "pyjwt==2.10.1",
        "gunicorn==23.0.0",
        "gevent==24.11.1",
        "gevent-websocket==0.10.1",
        "pyyaml==6.0",
        "requests==2.32.0",
        "cryptography==44.0.2",
        "colored==1.4.3",
        "flask-socketio==5.5.1",
        "ormsgpack==1.8.0",
        "msgpack==1.1.0",
        "msgpack-types==0.5.0",
        "fastavro==1.10.0",
        "factory-boy==3.3.0",
        "sentry-sdk[flask]==2.22.0",
        "faker==37.0.0",
        "types-requests==2.32.0.20250306",
        "types-jinja2==2.11.9",
        "xlsxwriter==3.2.2",
        "werkzeug==3.1.3",
        "frozendict==2.4.4",
        "wtforms==3.0.1",
        "wtforms-alchemy==0.18.0",
        "pathvalidate==3.2.3",

        # "opentelemetry-sdk==1.8.0",
        # "opentelemetry-api==1.8.0",
        # "opentelemetry-instrumentation-flask==0.27b0",
        # "opentelemetry-instrumentation-requests==0.27b0",
        # "opentelemetry-exporter-jaeger==1.8.0",
        # "opentelemetry-instrumentation-sqlalchemy==0.27b0",
        # "ul-db-utils==5.1.0",        # ACTUALIZE, BUT DO NOT UNCOMMENT PLEASE
        # "ul-py-tool==2.1.4",        # ACTUALIZE, BUT DO NOT UNCOMMENT PLEASE
    ],
)
