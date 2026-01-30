from .types import _INTERVAL
from .types import _DATE
from .types import _NUMERIC
from .types import _BOOLEAN
from .types import _DATETIME

from sqlalchemy.sql import sqltypes


colspecs = {
    sqltypes.Interval: _INTERVAL,
    sqltypes.Date: _DATE,
    sqltypes.Numeric: _NUMERIC,
    sqltypes.Boolean: _BOOLEAN,
    sqltypes.DateTime: _DATETIME,
}