"""
GenericLib: A collection of reusable utilities for text processing, data
structures, constants, platform helpers, and formatted output.

This package consolidates commonly used components into a single namespace,
making it easier to import and work with them across applications. It exposes
a curated set of classes, functions, and constants through `__all__` for
convenient access.
"""

from genericlib.collection import DictObject
from genericlib.collection import DotObject
from genericlib.collection import substitute_variable

from genericlib.text import Text
from genericlib.file import File

from genericlib.search import Wildcard

from genericlib.constant import ICSValue
from genericlib.constant import ICSStripValue
from genericlib.constant import ECODE
from genericlib.constant import STRING
from genericlib.constant import STR
from genericlib.constant import TEXT
from genericlib.constnum import NUMBER
from genericlib.constnum import INDEX
from genericlib.constsymbol import SYMBOL
from genericlib.constpattern import PATTERN
from genericlib.conststruct import STRUCT
from genericlib.conststruct import SLICE

from genericlib.utils import Printer
from genericlib.utils import Tabular
from genericlib.utils import get_data_as_tabular
from genericlib.utils import print_data_as_tabular

from genericlib.config import version

from genericlib.robotframeworklib import RFFile

__all__ = [
    'DictObject',
    'DotObject',

    'ECODE',
    'ICSValue',
    'ICSStripValue',
    'STRING',
    'STR',

    'INDEX',
    'NUMBER',
    'SYMBOL',
    'PATTERN',

    'STRUCT',
    'SLICE',
    'TEXT',

    'File',
    'RFFile',

    'Wildcard',

    'Printer',

    'Text',

    'Tabular',
    'get_data_as_tabular',
    'print_data_as_tabular',

    'substitute_variable',

    'version',
]
