from typing import List


class PlayerRequestValidationError(Exception):
    def __init__(self, message=None, invalid_fields: List[str] = None):
        self.__message = message
        self.invalid_fields = invalid_fields
        super().__init__(self.__message)


class PlayerDoesNotExist(Exception):
    def __init__(self, message=None, invalid_player_id: str = None) -> None:
        self.__message = message
        self.invalid_player_id = invalid_player_id
        super().__init__(self.__message)


class PlayerAlreadyExists(Exception):
    def __init__(self, message=None, existing_player_id: str = None) -> None:
        self.__message = message
        self.existing_player_id = existing_player_id
        super().__init__(self.__message)
