from pathlib import Path

from flask import Flask

from config import GENERATED_DIR, DATA_DIR


BASE_DIR = Path(__file__).resolve().parent.parent


def create_app():
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    app.config["SECRET_KEY"] = (
        "local-development-only-change-before-deployment"
    )

    app.config["GENERATED_DIR"] = GENERATED_DIR
    app.config["DATA_DIR"] = DATA_DIR

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    from app.routes import main

    app.register_blueprint(main)

    return app
