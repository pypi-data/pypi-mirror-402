# coding: utf-8

from sqlalchemy.testing.requirements import SuiteRequirements
from sqlalchemy.testing import exclusions
    

class Requirements(SuiteRequirements):
    
    @property
    def datetime_interval(self):
        """target dialect supports rendering of a datetime.timedelta as a
        literal string, e.g. via the TypeEngine.literal_processor() method.

        """
        return exclusions.open()
    
    @property
    def datetime_literals(self):
        """target dialect supports rendering of a date, time, or datetime as a
        literal string, e.g. via the TypeEngine.literal_processor() method.

        """

        return exclusions.open()
    
    @property
    def timestamp_microseconds(self):
        """target dialect supports representation of Python
        datetime.datetime() with microsecond objects but only
        if TIMESTAMP is used."""
        return exclusions.open()
    
    @property
    def time(self):
        """target dialect supports representation of Python
        datetime.time() objects."""

        return exclusions.closed()
    @property
    def time_microseconds(self):
        """target dialect supports representation of Python
        datetime.time() with microsecond objects."""

        return exclusions.closed()
    
    @property
    def ctes(self):
        """Target database supports CTEs"""

        return exclusions.open()
    
    @property
    def autocommit(self):
        return exclusions.open()
    
    @property
    def check_constraint_reflection(self):
        """target dialect supports reflection of check constraints"""
        return exclusions.open()
    
    @property
    def foreign_key_constraint_option_reflection_ondelete(self):
        return exclusions.open()
    
    @property
    def sequences(self):
        return exclusions.open()
    
    @property
    def identity_columns(self):
        return exclusions.closed()
    
    @property
    def isolation_level(self):
        return exclusions.open()
    
    @property
    def dbapi_lastrowid(self):
        """target platform includes a 'lastrowid' accessor on the DBAPI
        cursor object.

        """
        return exclusions.closed()
    
    @property
    def comment_reflection(self):
        """Indicates if the database support table comment reflection"""
        return exclusions.closed()
    
    @property
    def index_ddl_if_exists(self):
        """target platform supports IF NOT EXISTS / IF EXISTS for indexes."""

        return exclusions.open()
    
    @property
    def table_ddl_if_exists(self):
        """target platform supports IF NOT EXISTS / IF EXISTS for tables."""

        return exclusions.open()
    
    @property
    def unicode_ddl(self):
        return exclusions.open()
    
    @property
    def views(self):
        """Target database must support VIEWs."""

        return exclusions.open()

    @property
    def foreign_keys_reflect_as_index(self):
        """Target database creates an index that's reflected for
        foreign keys."""

        return exclusions.closed()    
    @property
    def unique_index_reflect_as_unique_constraints(self):
        """Target database reflects unique indexes as unique constrains."""

        return exclusions.closed()

    @property
    def unique_constraints_reflect_as_index(self):
        """Target database reflects unique constraints as indexes."""

        return exclusions.closed()
    
    @property
    def window_functions(self):
        return exclusions.open()
    
    @property
    def tuple_in(self):
        """Target platform supports the syntax
        "(x, y) IN ((x1, y1), (x2, y2), ...)"
        """

        return exclusions.open()
    
    @property
    def precision_numerics_many_significant_digits(self):
        """target backend supports values with many digits on both sides,
        such as 319438950232418390.273596, 87673.594069654243

        """
        return exclusions.open()


    @property
    def has_temp_table(self):
        """target dialect supports checking a single temp table name"""
        return exclusions.open()
    
    @property
    def datetime_timezone(self):
        """target dialect supports representation of Python
        datetime.datetime() with tzinfo with DateTime(timezone=True)."""

        return exclusions.closed()
    
    @property
    def computed_columns(self):
        "Supports computed columns"
        return exclusions.open()
    
    @property
    def comment_reflection(self):
        """Indicates if the database support table comment reflection"""
        return exclusions.open()

    def get_isolation_levels(self, config):
        return {
            "default": "COMMITTED READ",
            "supported":[
                "DIRTY READ", 
                "COMMITTED READ LAST COMMITTED", 
                "COMMITTED READ", 
                "CURSOR STABILITY",
                "REPEATABLE READ",             
                "AUTOCOMMIT"
            ]
        }

    


    
