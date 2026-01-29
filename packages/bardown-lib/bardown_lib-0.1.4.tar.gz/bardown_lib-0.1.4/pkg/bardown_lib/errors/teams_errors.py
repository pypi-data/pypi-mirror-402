from typing import List


class TeamValidationError(Exception):
    def __init__(self, message=None, invalid_fields: List = None):
        self.__message = message
        self.invalid_fields = invalid_fields
        super().__init__(self.__message)


class TeamDoesNotExist(Exception):
    def __init__(self, message=None, invalid_team_id: str = None):
        self.__message = message
        self.invalid_team_id = invalid_team_id
        super().__init__(self.__message)


class TeamAlreadyExists(Exception):
    def __init__(self, message=None, existing_team_id: str = None) -> None:
        self.__message = message
        self.existing_team_id = existing_team_id
        super().__init__(self.__message)
