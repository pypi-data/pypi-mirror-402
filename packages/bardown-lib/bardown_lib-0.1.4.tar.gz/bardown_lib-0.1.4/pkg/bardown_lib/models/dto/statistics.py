from typing import Optional

from pydantic import BaseModel


class Statistics(BaseModel):
    """
    Create statistics DTO object. The statistics for each player
    is represented in the db as a string in this format:

    0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0
    """

    hsh: Optional[int] = 0
    msh: Optional[int] = 0
    lsh: Optional[int] = 0
    hg: Optional[int] = 0
    mg: Optional[int] = 0
    lg: Optional[int] = 0
    a: Optional[int] = 0
    gb: Optional[int] = 0
    t: Optional[int] = 0
    ct: Optional[int] = 0
    p: Optional[int] = 0
    k: Optional[int] = 0
    ms: Optional[int] = 0
    hga: Optional[int] = 0
    mga: Optional[int] = 0
    lga: Optional[int] = 0
    hgs: Optional[int] = 0
    mgs: Optional[int] = 0
    lgs: Optional[int] = 0
    fow: Optional[int] = 0
    fol: Optional[int] = 0

    @classmethod
    def from_string(cls, statistics_string: str):
        stats = dict(zip(cls.model_fields.keys(), map(int, statistics_string.split("|"))))
        return Statistics(**stats)

    def __str__(self) -> str:
        return (
            f"{self.hsh}|{self.msh}|{self.lsh}|{self.hg}|{self.mg}|{self.lg}|{self.a}|{self.gb}"
            + f"|{self.t}|{self.ct}|{self.p}|{self.k}|{self.ms}|{self.hga}|{self.mga}"
            + f"|{self.lga}|{self.hgs}|{self.mgs}|{self.lgs}|{self.fow}|{self.fol}"
        )
