from pathlib import Path

from flask import Flask

from ..db import db
from .views import bp


def create_app(test_config=None):
    root = Path(__file__).resolve().parents[2]
    app = Flask(
        __name__,
        template_folder=str(root / "templates"),
        static_folder=str(root / "static"),
        instance_path=str(root / "instance"),
        instance_relative_config=True,
    )
    app.config.from_mapping(DATABASE=str(Path(app.instance_path) / "diary.sqlite3"))
    app.config.from_pyfile("config.py", silent=True)
    if test_config is not None:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(bp)
    return app
