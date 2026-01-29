from sqlalchemy import Column, Integer, String
from app.core.base import Base


class {entity}(Base):
    __tablename__ = "{entity_snake}s"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
