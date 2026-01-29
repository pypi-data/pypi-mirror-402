from datetime import datetime
from typing import Dict, Tuple

from bardown_lib.enums import position


class GameResult:
    def __init__(
        self,
        game_id: str = None,
        home_team_id: str = None,
        away_team_id: str = None,
        title: str = None,
        date: datetime = None,
        score: str = None,
        location: str = None,
        team_id: str = None,
        team_name: str = None,
        team_image_url: str = None,
        player_id: str = None,
        first_name: str = None,
        last_name: str = None,
        position: position.Position = None,
        number: int = None,
        player_image_url: str = None,
        statistics: str = None,
    ):
        self.game_id = game_id
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id
        self.title = title
        self.date = date
        self.score = score
        self.location = location
        self.team_id = team_id
        self.team_name = team_name
        self.team_image_url = team_image_url
        self.player_id = player_id
        self.first_name = first_name
        self.last_name = last_name
        self.position = position
        self.number = number
        self.player_image_url = player_image_url
        self.statistics = statistics

    @classmethod
    def from_tuple(cls, game_result_tuple: Tuple) -> None:
        return cls(**{k: v for k, v in zip(cls().to_dict().keys(), game_result_tuple)})

    def to_dict(self) -> Dict:
        return {
            "game_id": f"{self.game_id}",
            "home_team_id": f"{self.home_team_id}",
            "away_team_id": f"{self.away_team_id}",
            "title": f"{self.title}",
            "date": f"{self.date}",
            "score": f"{self.score}",
            "location": f"{self.location}",
            "team_id": f"{self.team_id}",
            "team_name": f"{self.team_name}",
            "team_image_url": f"{self.team_image_url}",
            "player_id": f"{self.player_id}",
            "first_name": f"{self.first_name}",
            "last_name": f"{self.last_name}",
            "position": self.position,
            "number": f"{self.number}",
            "player_image_url": f"{self.player_image_url}",
            "statistics": f"{self.statistics}",
        }
