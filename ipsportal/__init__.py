import os
from collections.abc import Mapping
from typing import Any

from flask import Flask

from ipsportal import trace_jaeger

from .environment import SECRET_API_KEY

# overwrite default umask for file permissions: allow for group writes and disallow all world interactions
os.umask(7)


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY=SECRET_API_KEY)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db

    db.init_app(app)

    from ipsportal import api, data_api, resourceplot, run

    app.register_blueprint(run.bp)
    app.register_blueprint(resourceplot.bp)
    app.register_blueprint(trace_jaeger.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(data_api.bp)

    return app
