from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings


def create_database_engine(database_url: str):
    connect_args = {'check_same_thread': False} if database_url.startswith('sqlite') else {}
    engine_options = {'pool_pre_ping': True} if database_url.startswith(('mysql', 'postgresql')) else {}
    return create_engine(database_url, connect_args=connect_args, **engine_options)


engine = create_database_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
