from datetime import date
from typing import List, Literal, Optional
from pydantic_xml import BaseXmlModel, attr, element

from .event import Event


class Meet(BaseXmlModel, tag="MEET"):
    name: str = attr(name="name")
    year: int | date = attr(name="year")
    course: Literal["SCM", "LSM"] = attr(name="course")
    lanecount: int = attr(name="lanecount")
    timingdistance: Optional[int] = attr(name="timingdistance", default=None)
    feventsagegroups: str = attr(name="feventsagegroups")
    meventsagegroups: str = attr(name="meventsagegroups")
    xeventsagegroups: str = attr(name="xeventsagegroups")
    timestandardfilename: str = attr(name="timestandardfilename")
    disqualificationcodes: str = attr(name="disqualificationcodes")

    events: List[Event] = element(tag="EVENT", default_factory=list)
