from pydantic import BaseModel


class {entity}Base(BaseModel):
    name: str


class {entity}Create({entity}Base):
    pass


class {entity}Update({entity}Base):
    pass


class {entity}Response({entity}Base):
    id: int

    class Config:
        from_attributes = True
