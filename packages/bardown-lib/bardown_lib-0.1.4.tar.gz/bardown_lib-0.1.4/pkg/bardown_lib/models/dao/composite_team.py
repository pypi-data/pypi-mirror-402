from typing import Dict, List, Tuple


class CompositeTeamPlayer:
    team_id: str
    team_name: str
    team_location: str
    year: int
    team_img_url: str
    player_id: str
    first_name: str
    last_name: str
    number: int
    position: str
    grade: str
    school: str
    img_url: str

    def __init__(
        self,
        team_id: str = None,
        team_name: str = None,
        team_img_url: str = None,
        team_location: str = None,
        year: int = None,
        player_id: str = None,
        first_name: str = None,
        last_name: str = None,
        number: int = None,
        position: str = None,
        grade: str = None,
        school: str = None,
        img_url: str = None,
    ):
        self.team_id = team_id
        self.team_name = team_name
        self.team_location = team_location
        self.team_img_url = team_img_url
        self.year = year
        self.player_id = player_id
        self.first_name = first_name
        self.last_name = last_name
        self.number = number
        self.position = position
        self.grade = grade
        self.school = school
        self.img_url = img_url

    @classmethod
    def from_tuple(cls, composite_team_player_tuple: Tuple) -> None:
        return cls(**{k: v for k, v in zip(cls().to_dict().keys(), composite_team_player_tuple)})

    def to_dict(self) -> Dict:
        return {
            "team_id": f"{self.team_id}",
            "team_name": f"{self.team_location}",
            "team_location": f"{self.team_location}",
            "team_img_url": f"{self.team_img_url}",
            "year": self.year,
            "player_id": f"{self.player_id}",
            "first_name": f"{self.first_name}",
            "last_name": f"{self.last_name}",
            "number": f"{self.number}",
            "position": f"{self.position}",
            "grade": f"{self.grade}",
            "school": f"{self.school}",
            "img_url": f"{self.img_url}",
        }


class CompositeTeamCoach:
    team_id: str
    team_name: str
    team_location: str
    team_img_url: str
    year: int
    coach_id: str
    first_name: str
    last_name: str
    role: str
    since: int
    email: str
    phone_number: str
    img_url: str

    def __init__(
        self,
        team_id: str = None,
        team_name: str = None,
        team_location: str = None,
        team_img_url: str = None,
        year: int = None,
        coach_id: str = None,
        first_name: str = None,
        last_name: str = None,
        role: str = None,
        since: int = None,
        email: str = None,
        phone_number: str = None,
        img_url: str = None,
    ):
        self.team_id = team_id
        self.team_name = team_name
        self.team_location = team_location
        self.team_img_url = team_img_url
        self.year = year
        self.coach_id = coach_id
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.since = since
        self.email = email
        self.phone_number = phone_number
        self.img_url = img_url

    @classmethod
    def from_tuple(cls, composite_team_coach_tuple: Tuple) -> None:
        return cls(**{k: v for k, v in zip(cls().to_dict().keys(), composite_team_coach_tuple)})

    def to_dict(self) -> Dict:
        return {
            "team_id": f"{self.team_id}",
            "team_name": f"{self.team_name}",
            "team_location": f"{self.team_location}",
            "team_img_url": f"{self.team_img_url}",
            "year": self.year,
            "coach_id": f"{self.coach_id}",
            "first_name": f"{self.first_name}",
            "last_name": f"{self.last_name}",
            "role": f"{self.role}",
            "since": f"{self.since}",
            "email": f"{self.email}",
            "phone_number": f"{self.phone_number}",
            "img_url": f"{self.img_url}",
        }


class CompositeTeam:
    players: List[CompositeTeamPlayer]
    coaches: List[CompositeTeamCoach]

    def __init__(
        self,
        players: List[CompositeTeamPlayer],
        coaches: List[CompositeTeamCoach],
    ):
        self.players = players
        self.coaches = coaches

    def to_dict(self) -> Dict:
        return {
            "players": [player.to_dict() for player in self.players],
            "coaches": [coach.to_dict() for coach in self.coaches],
        }
