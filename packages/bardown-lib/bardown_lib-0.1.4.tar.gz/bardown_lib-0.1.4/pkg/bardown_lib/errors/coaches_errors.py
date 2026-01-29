from typing import List


class CoachValidationError(Exception):
    def __init__(self, message: str = None, invalid_fields: List[str] = None) -> None:
        self.__message = message
        self.invalid_fields = invalid_fields
        super().__init__(self.__message)


class CoachDoesNotExist(Exception):
    def __init__(self, message: str = None, invalid_coach_id: str = None) -> None:
        self.__message = message
        self.invalid_coach_id = invalid_coach_id
        super().__init__(self.__message)


class CoachAlreadyExists(Exception):
    def __init__(self, message: str = None, existing_coach_id: str = None) -> None:
        self.__message = message
        self.existing_coach_id = existing_coach_id
        super().__init__(self.__message)
