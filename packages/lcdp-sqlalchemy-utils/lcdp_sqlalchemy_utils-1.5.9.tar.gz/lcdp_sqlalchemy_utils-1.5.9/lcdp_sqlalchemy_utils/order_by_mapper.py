from sqlalchemy import desc, asc
from .exceptions.InvalidOrderByException import InvalidOrderByException


def build(order_by_dto, dao_mapper):
    if order_by_dto is None:
        return None

    to = []
    for order_by in order_by_dto:
        try:
            parts = order_by.split(':', 2)
            column = dao_mapper(parts[0])
            to.append(__add_sorting_order(parts[1], column))
        except IndexError as e:
            raise InvalidOrderByException("Order by dto is invalid cannot be convert to sqlalchemy order by", e)
    return to


def __add_sorting_order(sorting_order, column):
    if sorting_order.upper() == 'DESC':
        return desc(column)
    elif sorting_order.upper() == 'ASC':
        return asc(column)
    else:
        raise InvalidOrderByException(f"{sorting_order.upper()} is neither ASC or DESC")