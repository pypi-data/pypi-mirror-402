from typing import Iterable, Self


class PlayerDataServiceResponse:
    _status: int
    _data: Iterable

    def __init__(self, status: int, data: dict) -> Self:
        self._status = status
        self._data = data

    @property
    def status(self) -> int:
        return self._status

    @status.setter
    def status(self, new_status: int) -> None:
        self._status = new_status

    @property
    def data(self) -> Iterable:
        return self._data

    @data.setter
    def data(self, new_data: Iterable) -> None:
        self._data = new_data

    @data.setter
    def data(self, new_data: str) -> None:
        self._data = self.data_from_string(new_data)
