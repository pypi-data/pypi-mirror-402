from sqlalchemy import Column, Integer
from app.core.base import Base


class {class_name}(Base):
    __tablename__ = "{table_name}"

    id = Column(Integer, primary_key=True)
