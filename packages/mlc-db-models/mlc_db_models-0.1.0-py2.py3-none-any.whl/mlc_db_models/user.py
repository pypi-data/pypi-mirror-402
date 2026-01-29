from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column

from .base import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "sales"}

    id = mapped_column(UUID, primary_key=True)
    external_id = mapped_column(String)
    name = mapped_column(String)
