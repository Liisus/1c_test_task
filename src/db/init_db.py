from src.app import create_app
from src.db.db import init_db


def main():
    app = create_app()
    with app.app_context():
        init_db()
    print("База данных готова.")


if __name__ == "__main__":
    main()
