from typing import Dict, Optional, Self
from urllib.parse import urlencode

from client.client_url import ClientUrl

from .ordering import OrderingRules
from .pagination import Pagination


class PlayerDataServiceRequest:
    _url: ClientUrl
    _path_parameters: Optional[Dict]
    _query_parameters: Optional[Dict]
    _request_body: Optional[Dict]
    _pagination: Optional[Pagination]
    _ordering: Optional[OrderingRules]

    def __init__(
        self,
        url: ClientUrl,
        path_parameters: str = None,
        query_parameters: Dict = None,
        request_body: Dict = None,
        pagination: Pagination = None,
        ordering: OrderingRules = None,
    ) -> Self:
        self._url = url
        self._path_parameters = path_parameters
        self._query_parameters = query_parameters if query_parameters is not None else dict()
        self._request_body = request_body if request_body is not None else dict()
        self._pagination = pagination if pagination is not None else Pagination()
        self._ordering = ordering if ordering is not None else OrderingRules()

    def construct_query_parameters(self) -> Dict:
        return self.query_parameters | self.pagination.to_dict() | self.ordering.to_dict()

    def query_string(self) -> str:
        return "?" + urlencode(self.construct_query_parameters())

    @property
    def uri(self) -> str:
        uri = self._url.url

        if self.path_parameters is not None and len(self.path_parameters) > 0:
            uri += f"/{self.path_parameters}"

        if self.query_parameters is not None and len(self.query_parameters) > 0:
            uri += self.query_string()

        return uri

    @property
    def path_parameters(self) -> Dict:
        return self._path_parameters

    @path_parameters.setter
    def path_parameters(self, new_path_parameters: Dict) -> Dict:
        self.path_parameters = new_path_parameters

    @property
    def query_parameters(self) -> Dict:
        return self._query_parameters

    @query_parameters.setter
    def query_parameters(self, new_query_params: Dict) -> Dict:
        self._query_parameters = new_query_params

    @property
    def request_body(self) -> Dict:
        return self._request_body

    @request_body.setter
    def request_body(self, new_request_body: Dict) -> None:
        self._request_body = new_request_body

    @property
    def limit(self) -> int:
        return self._pagination.limit

    @limit.setter
    def limit(self, new_limit: int) -> None:
        self._pagination.limit = new_limit

    @property
    def offset(self) -> int:
        return self._pagination.offset

    @offset.setter
    def offset(self, new_offset: int) -> None:
        self._pagination.offset = new_offset

    @property
    def order(self) -> str:
        return self._ordering.order

    @order.setter
    def order(self, new_order: str) -> None:
        self._ordering.order = new_order

    @property
    def order_by(self) -> str:
        return self._ordering.order_by

    @order_by.setter
    def order_by(self, new_order_by: str) -> None:
        self._ordering.order_by = new_order_by

    @property
    def pagination(self) -> Pagination:
        return self._pagination

    @property
    def ordering(self) -> OrderingRules:
        return self._ordering

    @property
    def url(self) -> ClientUrl:
        return self._url

    @url.setter
    def url(self, new_url: ClientUrl) -> None:
        self._url = new_url

    @property
    def method(self) -> str:
        return self._url.method

    @method.setter
    def method(self, new_method: str) -> None:
        self._url.method = new_method
