from datetime import datetime
from typing import Dict, Self, Tuple


class Game:
    def __init__(
        self,
        game_id: str = None,
        title: str = None,
        date: datetime = None,
        score: str = None,
        location: str = None,
        created: datetime = None,
        modified: datetime = None,
    ) -> Self:
        self.game_id = game_id
        self.title = title
        self.date = date
        self.score = score
        self.location = location
        self.created = created
        self.modified = modified

    @classmethod
    def from_tuple(cls, game_tuple: Tuple) -> None:
        """Create game from a tuple

        Args:
            player_tuple (Tuple): Tuple containing ordered game data
        """
        return cls(**{k: v for k, v in zip(cls().to_dict().keys(), game_tuple)})

    def __str__(self) -> str:
        return f"{self.date} | {self.title}: {self.score}"

    def to_dict(self) -> Dict:
        return {
            "game_id": f"{self.game_id}",
            "title": f"{self.title}",
            "date": f"{self.date}",
            "score": f"{self.score}",
            "location": f"{self.location}",
            "created": f"{self.created}",
            "modified": f"{self.modified}",
        }
