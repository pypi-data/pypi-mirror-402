from typing import Literal

from pydantic import field_validator
from pydantic_xml import BaseXmlModel, attr


class Athlete(BaseXmlModel, tag="ATHLETE"):
    firstname: str = attr(name="firstname")
    lastname: str = attr(name="lastname")
    gender: Literal["M", "F", "X"] = attr(name="gender")
    birthdate: str = attr(name="birthdate")
    club: str = attr(name="club")
    time: str = attr(name="time", default="")
    heatnum: int = attr(name="heatnum", default=-1)
    lanenum: int = attr(name="lanenum", default=-1)
    entrytime: str = attr(name="entrytime", default="")
    starttime: str = attr(name="starttime", default="")
    completeddistance: int = attr(name="completeddistance", default=0)
    timemodified: str = attr(name="timemodified", default="")
    disqualification: str = attr(name="disqualification", default="")

    @field_validator("gender", mode="before")
    @classmethod
    def _normalize_gender(cls, value: str | None) -> str:
        """
        Empty gender attributes are treated as mixed ("X") to keep parsing lenient.
        """
        if value is None:
            return "X"

        cleaned = value.strip().upper()
        return cleaned or "X"
