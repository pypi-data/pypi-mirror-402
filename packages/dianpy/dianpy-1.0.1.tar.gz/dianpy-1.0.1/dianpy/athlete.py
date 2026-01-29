from typing import Literal
from pydantic_xml import BaseXmlModel, attr


class Athlete(BaseXmlModel, tag="ATHLETE"):
    firstname: str = attr(name="firstname")
    lastname: str = attr(name="lastname")
    gender: Literal["M", "F", "X"] = attr(name="gender")
    birthdate: str = attr(name="birthdate")
    club: str = attr(name="club")
    time: str = attr(name="time")
    heatnum: int = attr(name="heatnum")
    lanenum: int = attr(name="lanenum")
    entrytime: str = attr(name="entrytime")
    starttime: str = attr(name="starttime")
    completeddistance: int = attr(name="completeddistance")
    timemodified: str = attr(name="timemodified")
    disqualification: str = attr(name="disqualification")
