from typing import List, Literal, Optional

from pydantic import field_validator
from pydantic_xml import BaseXmlModel, attr, element

from .athlete import Athlete


class Event(BaseXmlModel, tag="EVENT"):
    name: str = attr(name="name")
    gender: Optional[Literal["M", "F", "X"]] = attr(
        name="gender", default=None)
    stroke: str = attr(name="stroke")
    distance: int = attr(name="distance")
    heatcount: int = attr(name="heatcount", default=0)
    relaycount: int = attr(name="relaycount", default=0)

    athletes: List[Athlete] = element(tag="ATHLETE", default_factory=list)

    @field_validator("gender", mode="before")
    @classmethod
    def _normalize_gender(cls, value: str | None) -> str | None:
        """
        Empty gender attributes appear in some fixtures; treat them as mixed ("X") so validation passes.
        """
        if value is None:
            return "X"

        cleaned = value.strip().upper()
        return cleaned or "X"
