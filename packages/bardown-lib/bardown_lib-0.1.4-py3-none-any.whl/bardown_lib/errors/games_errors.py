from typing import List


class GameValidationError(Exception):
    def __init__(self, message=None, invalid_fields: List = None):
        self.__message = message
        self.invalid_fields = invalid_fields
        super().__init__(self.__message)


class GameDoesNotExist(Exception):
    def __init__(self, message=None):
        self.__message = message
        super().__init__(self.__message)


class GameAlreadyExists(Exception):
    def __init__(self, message=None, existing_game_id: str = None) -> None:
        self.__message = message
        self.existing_game_id = existing_game_id
        super().__init__(self.__message)
