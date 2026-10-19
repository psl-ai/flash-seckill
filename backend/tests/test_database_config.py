from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]


def test_pymysql_driver_is_declared():
    requirements = (PROJECT_ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8")
    assert "PyMySQL" in requirements


def test_compose_uses_mysql_as_default_database():
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "mysql:8.4" in compose
    assert "mysql+pymysql://app:app@mysql:3306/miaoqiang" in compose
    assert "postgres:" not in compose


def test_env_example_exposes_mysql_settings():
    env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "DATABASE_URL=mysql+pymysql://app:app@mysql:3306/miaoqiang" in env_example
    assert "MYSQL_DATABASE=miaoqiang" in env_example


def test_mysql_engine_enables_connection_health_check():
    from app.db import create_database_engine

    engine = create_database_engine("mysql+pymysql://app:app@mysql:3306/miaoqiang")
    try:
        assert engine.pool._pre_ping is True
    finally:
        engine.dispose()
