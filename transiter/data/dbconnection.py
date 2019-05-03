"""
This module is responsible for the database session and transaction scope.
"""
import logging

import sqlalchemy.exc
from decorator import decorator
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import scoped_session, sessionmaker

from transiter import models, config

logger = logging.getLogger(__name__)


def build_extra_engine_params_from_config(database_config):
    """
    Build additional engine parameters based on the configuration. This is to take
    advantage of some optimizations available in specific driver.

    :param database_config: the database config
    :return: a dictionary of empty parameters
    """
    extra_params = {}
    if database_config.DRIVER == "postgresql":
        if database_config.DIALECT is None or database_config.DIALECT == "psycopg2":
            extra_params["use_batch_mode"] = True
    logger.debug("Extra connection params: " + str(extra_params))
    return extra_params


def create_engine():
    """
    Create a SQL Alchemy engine using config.DatabaseConfig.

    :return: the engine
    """
    drivername = config.DatabaseConfig.DRIVER
    if config.DatabaseConfig.DIALECT is not None:
        drivername += "+" + config.DatabaseConfig.DIALECT
    connection_url = URL(
        drivername,
        username=config.DatabaseConfig.USERNAME,
        password=config.DatabaseConfig.PASSWORD,
        host=config.DatabaseConfig.HOST,
        port=config.DatabaseConfig.PORT,
        database=config.DatabaseConfig.NAME,
    )
    extra_params = build_extra_engine_params_from_config(config.DatabaseConfig)
    return sqlalchemy.create_engine(connection_url, **extra_params)


engine = None
session_factory = None
Session = None


def ensure_db_connection():
    """
    Ensure that the SQL Alchemy engine and session factory have been initialized.
    """
    global engine, session_factory, Session
    if engine is not None:
        return
    engine = create_engine()
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)


class OutsideUnitOfWorkError(Exception):
    pass


class NestedUnitOfWorkError(Exception):
    pass


def get_session():
    """
    Get the current session.

    :return: the session
    :raises OutsideUnitOfWorkError: if this method is called from outside a UOW
    """
    global Session
    if Session is None or not Session.registry.has():
        raise OutsideUnitOfWorkError
    return Session()


@decorator
def unit_of_work(func, *args, **kw):
    """
    Decorator that handles beginning and ending a unit of work.
    """
    global Session
    ensure_db_connection()
    if Session.registry.has():
        raise NestedUnitOfWorkError
    session = Session()
    try:
        result = func(*args, **kw)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        Session.remove()

    return result


def rebuild_db():
    """
    Erase the Transiter schema if it exists and then rebuild it.
    """
    global engine
    ensure_db_connection()
    models.Base.metadata.drop_all(engine)
    models.Base.metadata.create_all(engine)
