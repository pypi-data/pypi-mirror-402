from typing import List


class StatisticsValidationError(Exception):
    def __init__(self, message=None, invalid_fields: List = None):
        self.__message = message
        self.invalid_fields = invalid_fields
        super().__init__(self.__message)


class StatisticsDoNoExist(Exception):
    def __init__(self, message=None):
        self.__message = message
        super().__init__(self.__message)


class StatisticsAlreadyExist(Exception):
    def __init__(self, message=None) -> None:
        self.__message = message
        super().__init__(self.__message)


class GameStatisticsValidationError(Exception):
    def __init__(self, message=None, invalid_fields: List = None):
        self.__message = message
        self.invalid_fields = invalid_fields
        super().__init__(self.__message)


class GameStatisticsDoNoExist(Exception):
    def __init__(self, message=None):
        self.__message = message
        super().__init__(self.__message)


class GameStatisticsAlreadyExist(Exception):
    def __init__(self, message=None) -> None:
        self.__message = message
        super().__init__(self.__message)
