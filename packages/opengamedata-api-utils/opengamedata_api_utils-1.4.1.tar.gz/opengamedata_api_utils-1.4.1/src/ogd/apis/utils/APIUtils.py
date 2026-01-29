"""
APIUtils

Contains general utility functions for common  tasks when setting up our flask/flask-restful API functions.
In particular, has functions to assist in parsing certain kinds of data, and for generating OGD-core objects.
"""

# import standard libraries
import json
import os
from json.decoder import JSONDecodeError
from logging import Logger
from typing import Any, List, Optional
from urllib import parse

# import OGD libraries
from ogd.common.storage.interfaces.Interface import Interface
from ogd.common.storage.interfaces.MySQLInterface import MySQLInterface
from ogd.common.storage.interfaces.BigQueryInterface import BigQueryInterface
from ogd.common.configs.DataTableConfig import DataTableConfig
# from ogd.core.schemas.configs.ConfigSchema import ConfigSchema

# import local files

def parse_list(list_str:str, logger:Optional[Logger]=None) -> Optional[List[Any]]:
    """Simple utility to parse a string containing a bracketed list into a Python list.
    Returns None if the list was empty

    :param list_str: _description_
    :type list_str: str
    :return: A list parsed from the input string, or None if the string list was invalid or empty.
    :rtype: Union[List[Any], None]
    """
    ret_val : Optional[List[Any]] = None
    try:
        ret_val = json.loads(list_str)
    except JSONDecodeError as e:
        if logger:
            logger.warning(f"Could not parse '{list_str}' as a list, format was not valid!\nGot Error {e}")
    else:
        if ret_val is not None and len(ret_val) == 0:
            # If we had empty list, just treat as null.
            ret_val = None
    return ret_val

def urljoin(base:str, url:str, ignore_base_file:bool=False, allow_fragments:bool=True):
    """Custom variation of the `urllib.parse.urljoin` function provided by Python.

    By default, this version allows filenames in the base path to remain in the joined path.

    This is useful for working with Flask apps, particularly on Apache.
    Specifically, unless you alias things in Apache, you'll have `app.py` or `app.wsgi` in the URL.
    For a Flask API, then, you'll likely be joining a base URL like `"https://host.of.app/path/to/app.wsgi"` with an endpoint, call it `"endpoint"`.
    Under `urllib.parse.urljoin`, you'll get `"https://host.of.app/path/to/endpoint"`.
    With _this_ function, setting `ignore_base_file=False`, you'll get `"http://host.of.app/path/to/app.wsgi/endpoint"` as desired.

    When `ignore_base_file=True`, this function directly falls back to use `urllib.parse.urljoin`.

    :param base: The base URL, onto which the `url` parameter is joined.
    :type base: str
    :param url: The URL to be joined onto the given base URL.
    :type url: str
    :param ignore_base_file: Whether to ignore filenames in the base URL.  
        When True, such filenames are removed from the joined URL.
        For example, joining `https://host.of.app/path/to/app.wsgi` with `endpoint` would yield `https://host.of.app/path/to/endpoint`.  
        When False, such filenames are included in the joined URL.
    :type ignore_base_file: bool
    :param allow_fragments: Whether to allow fragment parts in the URLs.  
        This is only used when `ignore_base_file=True`, in which case this function falls back on `urllib.parse.urljoin` and `allow_fragments` is passed to that function call.
    :type ignore_base_file: bool
    """
    if ignore_base_file:
        return parse.urljoin(base=base, url=url, allow_fragments=allow_fragments)
    else:
        # Make sure we have a scheme
        if not (base.startswith("http://") or base.startswith("https://")):
            base = f"https://{base}"
        # If base ends with a /, remove it so we don't double-up when joining
        if base.endswith("/"):
            base = base[:-1]
        # If url starts with a /, remove it so we don't double-up when joining
        if url.startswith("/"):
            url = url[1:]
        return f"{base}/{url}"

# def gen_interface(game_id, core_config:ConfigSchema, logger:Optional[Logger]=None) -> Optional[Interface]:
#     """Utility to set up an Interface object for use by the API, given a game_id.

#     :param game_id: _description_
#     :type game_id: _type_
#     :return: _description_
#     :rtype: _type_
#     """
#     ret_val = None
    
#     _game_source : DataTableConfig = core_config.GameSourceMap.get(game_id, DataTableConfig.Default())

#     if _game_source.Source is not None:
#         # set up interface and request
#         match _game_source.Source.Type.upper():
#             case "MYSQL":
#                 ret_val = MySQLInterface(game_id, config=_game_source, fail_fast=False)
#                 if logger:
#                     logger.info(f"Using MySQLInterface for {game_id}")
#             case "BIGQUERY":
#                 if logger:
#                     logger.info(f"Generating BigQueryInterface for {game_id}, from directory {os.getcwd()}...")
#                 ret_val = BigQueryInterface(game_id=game_id, config=_game_source, fail_fast=False)
#                 if logger:
#                     logger.info("Done")
#             case _:
#                 ret_val = MySQLInterface(game_id, config=_game_source, fail_fast=False)
#                 if logger:
#                     logger.warning(f"Could not find a valid interface for {game_id}, defaulting to MySQL!")
#     return ret_val

# def gen_coding_interface(game_id) -> Optional[CodingInterface]:
#     """Utility to set up an Interface object for use by the API, given a game_id.

#     :param game_id: _description_
#     :type game_id: _type_
#     :return: _description_
#     :rtype: _type_
#     """
#     ret_val = None

#     _core_config = ConfigSchema(name="Core Config", all_elements=core_settings)
#     _game_source : GameSourceSchema = _core_config.GameSourceMap.get(game_id, GameSourceSchema.EmptySchema())

#     if _game_source.Source is not None:
#         # set up interface and request
#         if _game_source.Source.Type == "BigQuery":
#             ret_val = BigQueryCodingInterface(game_id=game_id, config=_core_config)
#             current_app.logger.info(f"Using BigQueryCodingInterface for {game_id}")
#         else:
#             ret_val = BigQueryCodingInterface(game_id=game_id, config=_core_config)
#             current_app.logger.warning(f"Could not find a valid interface for {game_id}, defaulting to BigQuery!")
#     return ret_val
