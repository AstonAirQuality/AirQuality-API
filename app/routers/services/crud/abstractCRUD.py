from db.database import SessionLocal


class abstractbaseCRUD:
    def __init__(self) -> None:
        self.db = SessionLocal()
