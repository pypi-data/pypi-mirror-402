from typing import List, Literal
from pydantic_xml import BaseXmlModel, attr, element

from .athlete import Athlete


class Event(BaseXmlModel, tag="EVENT"):
    name: str = attr(name="name")
    gender: Literal["M", "F", "X"] = attr(name="gender")
    stroke: str = attr(name="stroke")
    distance: int = attr(name="distance")
    heatcount: int = attr(name="heatcount", default=0)
    relaycount: int = attr(name="relaycount", default=0)

    athletes: List[Athlete] = element(tag="ATHLETE", default_factory=list)
