from sqlmodel import create_engine

from aptrade.core.config import settings
from aptrade.database.models import base  # noqa

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
