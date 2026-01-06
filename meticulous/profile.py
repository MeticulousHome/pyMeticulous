from typing import List, Optional, Union
from pydantic import BaseModel, AnyUrl, Field


class PreviousAuthor(BaseModel):
    name: str
    author_id: str
    profile_id: str


class Display(BaseModel):
    image: Optional[Union[AnyUrl, str]] = None
    # RGB Value in the #AABBCC format
    accentColor: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class Variable(BaseModel):
    name: str
    key: str
    type: str
    value: float


class Dynamics(BaseModel):
    points: List[List[Union[float, str]]]
    over: str
    interpolation: str


class ExitTrigger(BaseModel):
    type: str
    value: Union[float, str]
    relative: Optional[bool] = None
    comparison: Optional[str] = None


class Limit(BaseModel):
    type: str
    value: Union[float, str]


class Stage(BaseModel):
    name: str
    key: str
    type: str
    dynamics: Dynamics
    exit_triggers: List[ExitTrigger]
    limits: Optional[List[Limit]] = None


class Profile(BaseModel):
    name: str
    id: str
    author: str
    author_id: str
    previous_authors: Optional[List[PreviousAuthor]] = None
    display: Optional[Display] = None
    last_changed: Optional[float] = None
    temperature: float
    final_weight: float
    variables: Optional[List[Variable]] = None
    stages: List[Stage]
