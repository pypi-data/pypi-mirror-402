from typing import Dict, Self


class OrderingRules:
    def __init__(self, order: str = None, order_by: str = None) -> Self:
        self.order = order
        self.order_by = order_by

    def to_dict(self) -> Dict:
        data = {}

        if self.order is not None:
            data["order"] = self.order
        if self.order_by is not None:
            data["orderBy"] = self.order_by

        return data
