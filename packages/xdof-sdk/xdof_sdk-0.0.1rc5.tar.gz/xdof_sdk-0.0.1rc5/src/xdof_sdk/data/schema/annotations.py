from pydantic import BaseModel


class Segment(BaseModel):
    from_frame: int
    to_frame: int
    label: str
    type: str


class Annotation(BaseModel):
    version: str
    annotations: list[Segment]
