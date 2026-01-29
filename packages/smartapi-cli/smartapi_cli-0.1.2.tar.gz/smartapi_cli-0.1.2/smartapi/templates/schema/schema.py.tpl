from pydantic import BaseModel


class {schema}Base(BaseModel):
    pass


class {schema}Create({schema}Base):
    pass


class {schema}Update({schema}Base):
    pass


class {schema}Response({schema}Base):
    id: int

    class Config:
        from_attributes = True
