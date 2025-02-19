from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from collections.abc import Callable


class SortParamError(Exception):
    def __init__(self, prop: str, message: str, *args: object) -> None:
        super().__init__(*args)
        self.property = prop
        self.message = message


def _parse_sort_arguments(request: dict[str, Any], allowed_props: list[str]) -> dict[str, int]:
    """Parse sort arguments from DataTables

    Params:
      request: DataTables server-side processing request argument
      allowed_props: list of allowed properties.
        If the request tries to get a property not in this list, raise SortParamException

    Returns:
      dictionary of property to sort direction.
        The dictionary should have the property names as keys,
        and the values should either be "1" (sort ASC) or "-1" (sort DESC).

    Raises:
      SortParamException - if any params are not properly formatted. Should never be raised if
        DataTables queries this API, but may be raised if the API is used directly elsewhere.
    """
    sort_dict: dict[str, int] = {}
    columns: list[Any] = request.get('columns', None)  # noqa: SIM910
    if not isinstance(columns, list):
        prop = 'columns'
        raise SortParamError(prop, 'must be an array')
    for idx, sort_args in enumerate(request.get('order', [])):
        col_idx = 0
        err = False
        try:
            col_idx = sort_args['column']
            if col_idx >= len(allowed_props):
                err = True
        except KeyError:
            err = True
        if err:
            prop = f'order[{idx}]'
            raise SortParamError(prop, 'invalid column reference')
        try:
            column = columns[col_idx]
        except IndexError:
            prop = f'order[{idx}]["column"]'
            raise SortParamError(prop, 'invalid column reference') from None

        try:
            sort_dir = sort_args['dir']
            if sort_dir == 'asc':
                sort_code = 1
            elif sort_dir == 'desc':
                sort_code = -1
            else:
                prop = f'order[{idx}]["dir"]'
                raise SortParamError(prop, 'must be either "asc" or "desc"')
        except KeyError:
            prop = f'order[{idx}]["dir"]'
            raise SortParamError(prop, 'must be either "asc" or "desc"') from None

        if not isinstance(column, dict):
            prop = f'columns[{col_idx}]'
            raise SortParamError(prop, 'must be a valid DataTables column object')

        if column.get('orderable', False):
            err = False
            try:
                dataname = column['data']
                # if "columns" were defined client-side
                if isinstance(dataname, str):
                    if dataname in allowed_props:
                        sort_dict[dataname] = sort_code
                    else:
                        prop = f'columns[{col_idx}][data]'
                        raise SortParamError(prop, 'must be a valid property name')
                # if "columns" were not defined client-side
                elif isinstance(dataname, int):
                    try:
                        sort_dict[allowed_props[dataname]] = sort_code
                    except IndexError:
                        prop = f'columns[{col_idx}][data]'
                        raise SortParamError(
                            prop,
                            'must be a valid property index',
                        ) from None
                else:
                    prop = f'columns[{col_idx}][data]'
                    raise SortParamError(
                        prop,
                        'must be a valid property name or property index',
                    )
            except KeyError:
                prop = f'columns[{col_idx}]'
                raise SortParamError(prop, 'missing "data" property') from None

    if sort_dict:
        # enforce sort consistency in case all other properties are equal
        sort_dict['_id'] = 1

    return sort_dict


def _add_search_terms(search_terms: list[str], allowed_props: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Parse global search option from DataTables

    This simply adds an ignore-case regex search option for every column.

    Params:
      - search_terms: non-empty list of strings
      - allowed_props: specific columns we want to search by

    Returns:
      value to update the $match filter with
    """
    return {
        '$and': [
            {'$or': [{column: {'$regex': search_term, '$options': 'i'}} for column in allowed_props]}
            for search_term in search_terms
        ]
    }


# potentially useful reference: https://github.com/pjosols/mongo-datatables
# (NOTE: this library does NOT attempt to validate the input, so don't use it directly)
def get_datatables_results(
    request: dict[str, Any],
    allowed_props: list[str],
    data_query_fn: Callable[[dict[str, Any], int, int, dict[str, int]], list[Any]],
    count_query_fn: Callable[[dict[str, Any]], int],
    base_filter: dict[str, Any] | None = None,
) -> tuple[Literal[False], list[tuple[str, str]]] | tuple[Literal[True], dict[str, Any]]:
    """
    This function is intended to be a generic mechanism when interacting with a DataTables request.

    The DataTables API specification is available at: https://datatables.net/manual/server-side

    Params:
      request: the parameters that DataTables provides.
        Note that it is assumed that this has already been parsed into a dictionary,
        this makes no assumptions about what web framework you're using.
        HOWEVER - the function will perform validation on the request object from here.
        (TODO - maybe use Pydantic or Msgspec to validate the data structure?)
      allowed_props: list of permitted properties to query for. DataTables sends in arbitrary
        values for its columns, but we need to enforce this on the server-side and never assume
        that client-side data is valid.
      data_query_fn: Callback function which takes in a filter, skip amount, length amount,
        and sort orders, and returns the actual data from Mongo.
      count_query_fn: Callback function which takes in a filter,
        and returns the number of documents from the query
      base_filter: Optional parameter, this is a starting $match MongoDB query
        that can be appended to if the frontend sends search instructions.
        (note that the parameter will not be modified, we instead make a copy of it internally)

    Returns:
      always a two-tuple value:
      - OnError: False, followed by a list of tuples. The first entry is the property path string,
        the second entry is the error string.
      - OnSuccess: True, followed by the DataTables response (as a dictionary - not serialized yet)
    """
    if not isinstance(request, dict):
        return False, (('<BASE>', 'query parameter must be a DataTables JSON object string'))

    errors: list[tuple[str, str]] = []

    draw = request.get('draw', 0)
    if not isinstance(draw, int) or draw < 0:
        errors.append(('draw', 'must be a non-negative integer'))

    start = request.get('start', 0)
    if not isinstance(start, int) or start < 0:
        errors.append(('start', 'must be a non-negative integer'))

    length = request.get('length', 20)
    if not isinstance(length, int) or length < 1:
        errors.append(('length', 'must be a positive integer'))

    try:
        sort_args = _parse_sort_arguments(request, allowed_props)
    except SortParamError as e:
        sort_args = {}
        errors.append((e.property, e.message))

    if errors:
        return False, errors

    # TODO: currently only checking global search, but DataTables API allows for per-column search
    where_filter = deepcopy(base_filter) if base_filter else {}
    search = request.get('search')
    if isinstance(search, dict):
        search_value = search.get('value')
        if isinstance(search_value, str):
            # TODO should probably sanitize this search result
            search_values = search_value.split()
            if search_values:
                where_filter.update(_add_search_terms(search_values, allowed_props))

    return (
        True,
        {
            'draw': draw,
            'recordsTotal': count_query_fn(base_filter or {}),
            'recordsFiltered': count_query_fn(where_filter),
            'data': data_query_fn(where_filter, start, length, sort_args),
        },
    )
