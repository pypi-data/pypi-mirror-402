from __future__ import annotations

import decimal
import datetime as dt
from typing import Type
from typing import Optional
from typing import TYPE_CHECKING

from sqlalchemy.sql import sqltypes
from sqlalchemy import processors

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect
    from sqlalchemy.sql.type_api import _LiteralProcessorType

class _INTERVAL(sqltypes.NativeForEmulated, sqltypes._AbstractInterval):
    __visit_name__ = "INTERVAL"

    def __init__(self, day_precision=None, second_precision=None):
        self.day_precision = day_precision
        self.second_precision = second_precision if second_precision is None or second_precision <=5 else 5

    @classmethod
    def _adapt_from_generic_interval(cls, interval):
        return _INTERVAL(
            day_precision=interval.day_precision,
            second_precision=interval.second_precision,
        )

    @classmethod
    def adapt_emulated_to_native(
        cls, interval: sqltypes.Interval, **kw  # type: ignore[override]
    ):
        return _INTERVAL(
            day_precision=interval.day_precision,
            second_precision=interval.second_precision,
        )

    @property
    def _type_affinity(self):
        return sqltypes.Interval

    def as_generic(self, allow_nulltype=False):
        return sqltypes.Interval(
            native=True,
            second_precision=self.second_precision,
            day_precision=self.day_precision,
        )

    @property
    def python_type(self) -> Type[dt.timedelta]:
        return dt.timedelta

    def literal_processor(
        self, dialect: Dialect
    ) -> Optional[_LiteralProcessorType[dt.timedelta]]:
        def process(value: dt.timedelta) -> str:
            return f"NUMTODSINTERVAL({value.total_seconds()}, 'SECOND')"

        return process
    
    
class _DATE(sqltypes.Date):
    
    def bind_processor(self, dialect):
        return None

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is not None:
                return value.date()
            else:
                return value

        return process

    def literal_processor(self, dialect):
        def process(value):
            fmt = "YYYY-MM-DD"
            value = '{:4}-{:02}-{:02}'.format(value.year, value.month, value.day)
            func_name = 'TO_TIMESTAMP'
            value = (
                f"""{func_name}"""
                f"""('{value}', """
                f"""'{fmt}')"""
            )
            return value

        return process
    
    
class _NUMERIC(sqltypes.Numeric):
    is_number = False

    def bind_processor(self, dialect):
        if self.scale == 0:
            return None
        elif self.asdecimal:
            processor = processors.to_decimal_processor_factory(
                decimal.Decimal, self._effective_decimal_return_scale
            )

            def process(value):
                if isinstance(value, (int, float)):
                    return processor(value)
                elif value is not None and value.is_infinite():
                    return float(value)
                else:
                    return value

            return process
        else:
            return processors.to_float

    def result_processor(self, dialect, coltype):
        return None
    
    def _outputtypehandler(self, dialect):
        gdbase8sdb = dialect.dbapi

        def handler(cursor, name, default_type, size, precision, scale):
            outconverter = None

            if precision:
                if self.asdecimal:
                    if default_type == gdbase8sdb.DB_TYPE_BINARY_DOUBLE:
                        # receiving float and doing Decimal after the fact
                        # allows for float("inf") to be handled
                        type_ = default_type
                        outconverter = decimal.Decimal
                    else:
                        type_ = decimal.Decimal
                else:
                    if self.is_number and scale == 0:
                        # integer. cx_Oracle is observed to handle the widest
                        # variety of ints when no directives are passed,
                        # from 5.2 to 7.0.  See [ticket:4457]
                        return None
                    else:
                        type_ = gdbase8sdb.DB_TYPE_BINARY_DOUBLE

            else:
                if self.asdecimal:
                    if default_type == gdbase8sdb.DB_TYPE_BINARY_DOUBLE:
                        type_ = default_type
                        outconverter = decimal.Decimal
                    else:
                        type_ = decimal.Decimal
                else:
                    if self.is_number and scale == 0:
                        # integer. cx_Oracle is observed to handle the widest
                        # variety of ints when no directives are passed,
                        # from 5.2 to 7.0.  See [ticket:4457]
                        return None
                    else:
                        type_ = gdbase8sdb.DB_TYPE_BINARY_DOUBLE

            return cursor.var(
                type_,
                255,
                arraysize=cursor.arraysize,
                outconverter=outconverter,
            )

        return handler
    
    
class _BOOLEAN(sqltypes.Boolean):
    def get_dbapi_type(self, dbapi):
        return dbapi.DB_TYPE_NUMBER

    
class _DATETIME(sqltypes.DateTime):    
    def literal_processor(self, dialect):
        def process(value):
            if getattr(value, "microsecond", None):
                fmt = 'YYYY-MM-DD HH24:MI:SS.FF6'
            else:
                fmt = 'YYYY-MM-DD HH24:MI:SS'
            if getattr(value, "tzinfo", None):
                func_name = 'TO_TIMESTAMP_TZ'
                fmt += ' TZH:TZM'
            else:
                func_name = 'TO_TIMESTAMP'
            value = (
                f"""{func_name}"""
                f"""('{value.isoformat().replace("T", " ")}', """
                f"""'{fmt}')"""
            )
            return value

        return process
    
