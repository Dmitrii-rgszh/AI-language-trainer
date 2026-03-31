from app.content.bootstrap import bootstrap_content
from app.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as session:
        bootstrap_content(session)
        session.commit()
        print("Content bootstrap completed successfully.")


if __name__ == "__main__":
    main()

