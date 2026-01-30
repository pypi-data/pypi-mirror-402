# coding: utf-8
import re
from functools import reduce
from itertools import groupby
from sqlalchemy.engine import default
from sqlalchemy.engine import reflection
from sqlalchemy.sql import sqltypes
from sqlalchemy import util
from sqlalchemy import schema
from sqlalchemy import exc
from sqlalchemy.sql import compiler
from sqlalchemy.sql.elements import quoted_name
from sqlalchemy import select
from .base import colspecs


# coltype map
ischema_names = {               # GBASE 8s TYPE
    0: sqltypes.CHAR,           # CHAR
    1: sqltypes.SMALLINT,       # SMALLINT
    2: sqltypes.INTEGER,        # INT
    3: sqltypes.FLOAT,          # Float
    4: sqltypes.FLOAT,          # SmallFloat
    5: sqltypes.Numeric,        # DECIMAL
    6: sqltypes.Integer,        # Serial
    7: sqltypes.DATE,           # DATE
    8: sqltypes.Numeric,        # MONEY
    10: sqltypes.TIMESTAMP,     # DATETIME
    11: sqltypes.LargeBinary,   # BYTE
    12: sqltypes.TEXT,          # TEXT
    13: sqltypes.VARCHAR,       # VARCHAR
    14: sqltypes.Interval,      # INTERVAL DAY TO SECOND
    15: sqltypes.NCHAR,         # NCHAR
    16: sqltypes.NVARCHAR,      # NVARCHAR
    17: sqltypes.BIGINT,        # INT8
    18: sqltypes.BIGINT,        # Serial8
    43: sqltypes.String,        # LVARCHAR
    52: sqltypes.BIGINT,        # BIGINT
    65: sqltypes.TIMESTAMP,     # TIMESTAMP
}

class GBase8sDDLCompiler(compiler.DDLCompiler):
    
    def get_column_specification(self, column, **kwargs):
        colspec = self.preparer.format_column(column)
        impl_type = column.type.dialect_impl(self.dialect)
        if isinstance(impl_type, sqltypes.TypeDecorator):
            impl_type = impl_type.impl
        if (
            column.primary_key
            and column is column.table._autoincrement_column
            and (
                column.default is None
                or (
                    isinstance(column.default, schema.Sequence)
                    and column.default.optional
                )
            )
        ):
            if isinstance(impl_type, sqltypes.BigInteger):
                colspec += " BIGSERIAL"
            else:
                colspec += " SERIAL"
        else:
            colspec += " " + self.dialect.type_compiler.process(column.type, type_expression=column)
            default = self.get_column_default_string(column)
            if default is not None:
                    colspec += " DEFAULT " + default
        if column.computed is not None:
            colspec += " " + self.process(column.computed)
        if not column.nullable:
            colspec += " NOT NULL"
        return colspec
    
    def get_identity_options(self, identity_options):
        text = super().get_identity_options(identity_options)
        text = text.replace("NO MINVALUE", "NOMINVALUE")
        text = text.replace("NO MAXVALUE", "NOMAXVALUE")
        text = text.replace("NO CYCLE", "NOCYCLE")
        if identity_options.order is not None:
            text += " ORDER" if identity_options.order else " NOORDER"
        return text.strip()

    def visit_computed_column(self, generated, **kw):
        text = "GENERATED ALWAYS AS (%s)" % self.sql_compiler.process(
            generated.sqltext, include_table=False, literal_binds=True
        )
        if generated.persisted is True:
            raise exc.CompileError(
                "GBase 8s computed columns do not support 'stored' persistence; "
                "set the 'persisted' flag to None or False for support."
            )
        elif generated.persisted is False:
            text += " VIRTUAL"
        return text   
    
    def visit_drop_table_comment(self, drop, **kw):
        return "COMMENT ON TABLE %s IS NULL" % self.preparer.format_table(
            drop.element
        )

    def visit_create_index(
            self, create, include_schema=False, include_table_schema=True
    ):
        index = create.element
        self._verify_index_table(index)
        preparer = self.preparer
        text = "CREATE "
        if index.unique:
            text += "UNIQUE "

        text += "INDEX "

        # if create.if_not_exists:
        text += "IF NOT EXISTS "

        text += "%s ON %s (%s)" % (
            self._prepared_index_name(index, include_schema=True),
            preparer.format_table(index.table, use_schema=False),
            ", ".join(
                self.sql_compiler.process(
                    expr, include_table=False, literal_binds=True
                )
                for expr in index.expressions
            ),
        )

        return text
    

class GBase8sExecutionContext(default.DefaultExecutionContext):
    # _select_lastrowid = False
    # _lastrowid = None
    def pre_exec(self):
        super().pre_exec()
        if not getattr(self.compiled, "_sql_compiler", False):
            return
        self._set_cursor_outputtype_handler()
        
    def get_lastrowid(self):
        return self.cursor.lastrowid
        
            
    def _set_cursor_outputtype_handler(self):
        output_handlers = {}
        for keyname, name, objects, type_ in self.compiled._result_columns:
            handler = type_._cached_custom_processor(
                self.dialect,
                "_outputtypehandler",
                self._get_type_handler,
            )

            if handler:
                output_handlers[keyname] = handler

        if output_handlers:
            def output_type_handler(
                cursor, name, default_type, size, precision, scale
            ):
                if name in output_handlers:
                    return output_handlers[name](
                        cursor, name, default_type, size, precision, scale
                    )
                else:
                    return None

            self.cursor.outputtypehandler = output_type_handler
            
    def _get_type_handler(self, impl):
        if hasattr(impl, "_outputtypehandler"):
            return impl._outputtypehandler(self.dialect)
        else:
            return None

    def fire_sequence(self, seq, type_):
        return self._execute_scalar(
            "SELECT "
            + self.identifier_preparer.format_sequence(seq)
            + ".nextval FROM DUAL",
            type_,
        )
        

class GBase8sTypeCompiler(compiler.GenericTypeCompiler):

    def visit_TEXT(self, type_, **kw):
        return self.visit_CLOB(type_, **kw)
    
    def visit_DATETIME(self, type_, **kw):
        if type_.timezone:
            return "TIMESTAMP WITH TIME ZONE"
        return "TIMESTAMP"
    
    def visit_DATE(self, type_, **kw):
        return "TIMESTAMP"
    
    def visit_TIMESTAMP(self, type_, **kw):
        return self.visit_DATETIME(type_, **kw)
    
    def visit_INTERVAL(self, type_, **kw):
        return "INTERVAL DAY%s TO SECOND%s" % (
            type_.day_precision is not None
            and "(%d)" % type_.day_precision
            or "",
            type_.second_precision is not None
            and "(%d)" % type_.second_precision
            or "",
        )
        
    def visit_BOOLEAN(self, type_, **kw):
        return self.visit_SMALLINT(type_, **kw)
    
    def visit_DOUBLE(self, type_, **kw):
        return self.visit_DOUBLE_PRECISION(type_, **kw)
    
    def visit_VARCHAR(self, type_, **kw):
        return f'VARCHAR({type_.length})' if type_.length else 'VARCHAR(255)'
    
    def visit_NVARCHAR(self, type_, **kw):
        return f'NVARCHAR({type_.length})' if type_.length else 'NVARCHAR(255)'

    def visit_BINARY(self, type_, **kw):
        return 'BLOB'

    def visit_SMALLINT(self, type_, **kw):
        return 'INTEGER'


class GBase8sCompiler(compiler.SQLCompiler):
    _sql_compiler = True
    _p_exists = re.compile('(exists\s*\(.*\))(\s+as\s+.*)',  re.IGNORECASE|re.DOTALL)
    def default_from(self):
        return " FROM DUAL"
    
    def visit_now_func(self, fn, **kw):
        return "CURRENT_TIMESTAMP"
    
    def visit_sequence(self, seq, **kw):
        return self.preparer.format_sequence(seq) + ".nextval"
    
    def visit_is_distinct_from_binary(self, binary, operator, **kw):
        return "DECODE(%s, %s, 0, 1) = 1" % (
            self.process(binary.left),
            self.process(binary.right),
        )

    def visit_is_not_distinct_from_binary(self, binary, operator, **kw):
        return "DECODE(%s, %s, 0, 1) = 0" % (
            self.process(binary.left),
            self.process(binary.right),
        )
    
    def get_select_precolumns(self, select, **kw):
        result = super().get_select_precolumns(select, **kw)
        if select._offset_clause is not None:
            result += "SKIP " + self.process(select._offset_clause, **kw) + " "
        if select._limit_clause is not None:
            result += "LIMIT " + self.process(select._limit_clause, **kw) + " "
        return result
    
    def limit_clause(self, select, **kw):
        text = ""
        return text

    def visit_compound_select(self, cs, asfrom=False, compound_index=None, **kwargs):        
        selects = [select(s.subquery()) for s in cs.selects]
        cs.selects = selects
        toplevel = not self.stack

        compile_state = cs._compile_state_factory(cs, self, **kwargs)

        if toplevel and not self.compile_state:
            self.compile_state = compile_state

        compound_stmt = compile_state.statement

        entry = self._default_stack_entry if toplevel else self.stack[-1]
        need_result_map = toplevel or (
            not compound_index
            and entry.get("need_result_map_for_compound", False)
        )

        # indicates there is already a CompoundSelect in play
        if compound_index == 0:
            entry["select_0"] = cs

        self.stack.append(
            {
                "correlate_froms": entry["correlate_froms"],
                "asfrom_froms": entry["asfrom_froms"],
                "selectable": cs,
                "compile_state": compile_state,
                "need_result_map_for_compound": need_result_map,
            }
        )

        if compound_stmt._independent_ctes:
            for cte in compound_stmt._independent_ctes:
                cte._compiler_dispatch(self, **kwargs)

        keyword = self.compound_keywords.get(cs.keyword)

        text = "SELECT * FROM (\n" + (" " + keyword + " ").join(
            (
                c._compiler_dispatch(
                    self, asfrom=asfrom, compound_index=i, **kwargs
                )
                for i, c in enumerate(cs.selects)
            )
        ) + ") "

        kwargs["include_table"] = False
        text += self.group_by_clause(cs, **dict(asfrom=asfrom, **kwargs))
        text += self.order_by_clause(cs, **kwargs)
        if cs._has_row_limiting_clause:
            text += self._row_limit_clause(cs, **kwargs)

        if self.ctes:
            nesting_level = len(self.stack) if not toplevel else None
            text = (
                self._render_cte_clause(
                    nesting_level=nesting_level,
                    include_following_stack=True,
                    visiting_cte=kwargs.get("visiting_cte"),
                )
                + text
            )

        self.stack.pop(-1)
        return text

    def _convert_exists_to_case_when(self, v):        
        if isinstance(v, str) and v.startswith("EXISTS"):
            m = self._p_exists.match(v)
            exists_expr = m.group(1)
            as_alias = m.group(2)
            v = f"CASE WHEN {exists_expr} THEN 1 ELSE 0 END"
            if as_alias:
                v += as_alias
        return v

    def visit_select(
        self,
        select_stmt,
        asfrom=False,
        insert_into=False,
        fromhints=None,
        compound_index=None,
        select_wraps_for=None,
        lateral=False,
        from_linter=None,
        **kwargs
    ):
        assert select_wraps_for is None, (
            "SQLAlchemy 1.4 requires use of "
            "the translate_select_structure hook for structural "
            "translations of SELECT objects"
        )

        # initial setup of SELECT.  the compile_state_factory may now
        # be creating a totally different SELECT from the one that was
        # passed in.  for ORM use this will convert from an ORM-state
        # SELECT to a regular "Core" SELECT.  other composed operations
        # such as computation of joins will be performed.

        kwargs["within_columns_clause"] = False

        compile_state = select_stmt._compile_state_factory(
            select_stmt, self, **kwargs
        )
        select_stmt = compile_state.statement

        toplevel = not self.stack

        if toplevel and not self.compile_state:
            self.compile_state = compile_state

        is_embedded_select = compound_index is not None or insert_into

        # translate step for Oracle, SQL Server which often need to
        # restructure the SELECT to allow for LIMIT/OFFSET and possibly
        # other conditions
        if self.translate_select_structure:
            new_select_stmt = self.translate_select_structure(
                select_stmt, asfrom=asfrom, **kwargs
            )

            # if SELECT was restructured, maintain a link to the originals
            # and assemble a new compile state
            if new_select_stmt is not select_stmt:
                compile_state_wraps_for = compile_state
                select_wraps_for = select_stmt
                select_stmt = new_select_stmt

                compile_state = select_stmt._compile_state_factory(
                    select_stmt, self, **kwargs
                )
                select_stmt = compile_state.statement

        entry = self._default_stack_entry if toplevel else self.stack[-1]

        populate_result_map = need_column_expressions = (
            toplevel
            or entry.get("need_result_map_for_compound", False)
            or entry.get("need_result_map_for_nested", False)
        )

        # indicates there is a CompoundSelect in play and we are not the
        # first select
        if compound_index:
            populate_result_map = False

        # this was first proposed as part of #3372; however, it is not
        # reached in current tests and could possibly be an assertion
        # instead.
        if not populate_result_map and "add_to_result_map" in kwargs:
            del kwargs["add_to_result_map"]

        froms = self._setup_select_stack(
            select_stmt, compile_state, entry, asfrom, lateral, compound_index
        )

        column_clause_args = kwargs.copy()
        column_clause_args.update(
            {"within_label_clause": False, "within_columns_clause": False}
        )

        text = "SELECT "  # we're off to a good start !
        if select_stmt._hints:
            hint_text, byfrom = self._setup_select_hints(select_stmt)
            if hint_text:
                text += hint_text + " "
        else:
            byfrom = None

        if select_stmt._independent_ctes:
            for cte in select_stmt._independent_ctes:
                cte._compiler_dispatch(self, **kwargs)

        if select_stmt._prefixes:
            text += self._generate_prefixes(
                select_stmt, select_stmt._prefixes, **kwargs
            )

        text += self.get_select_precolumns(select_stmt, **kwargs)
        # the actual list of columns to print in the SELECT column list.
        inner_columns = [
            c
            for c in [
                self._label_select_column(
                    select_stmt,
                    column,
                    populate_result_map,
                    asfrom,
                    column_clause_args,
                    name=name,
                    proxy_name=proxy_name,
                    fallback_label_name=fallback_label_name,
                    column_is_repeated=repeated,
                    need_column_expressions=need_column_expressions,
                )
                for (
                    name,
                    proxy_name,
                    fallback_label_name,
                    column,
                    repeated,
                ) in compile_state.columns_plus_names
            ]
            if c is not None
        ]
        inner_columns = map(self._convert_exists_to_case_when, inner_columns)
        if populate_result_map and select_wraps_for is not None:
            # if this select was generated from translate_select,
            # rewrite the targeted columns in the result map

            translate = dict(
                zip(
                    [
                        name
                        for (
                            key,
                            proxy_name,
                            fallback_label_name,
                            name,
                            repeated,
                        ) in compile_state.columns_plus_names
                    ],
                    [
                        name
                        for (
                            key,
                            proxy_name,
                            fallback_label_name,
                            name,
                            repeated,
                        ) in compile_state_wraps_for.columns_plus_names
                    ],
                )
            )

            self._result_columns = [
                (key, name, tuple(translate.get(o, o) for o in obj), type_)
                for key, name, obj, type_ in self._result_columns
            ]
        

        text = self._compose_select_body(
            text,
            select_stmt,
            compile_state,
            inner_columns,
            froms,
            byfrom,
            toplevel,
            kwargs,
        )
        

        if select_stmt._statement_hints:
            per_dialect = [
                ht
                for (dialect_name, ht) in select_stmt._statement_hints
                if dialect_name in ("*", self.dialect.name)
            ]
            if per_dialect:
                text += " " + self.get_statement_hint_text(per_dialect)

        # In compound query, CTEs are shared at the compound level
        if self.ctes and (not is_embedded_select or toplevel):
            nesting_level = len(self.stack) if not toplevel else None
            text = (
                self._render_cte_clause(
                    nesting_level=nesting_level,
                    visiting_cte=kwargs.get("visiting_cte"),
                )
                + text
            )

        if select_stmt._suffixes:
            text += " " + self._generate_prefixes(
                select_stmt, select_stmt._suffixes, **kwargs
            )

        self.stack.pop(-1)

        return text


class GBase8sDialect(default.DefaultDialect):
    driver = 'gbase8sdb'
    supports_statement_cache = True
    div_is_floordiv = False
    postfetch_lastrowid = True
    supports_empty_insert = False
    supports_sequences = True
    supports_schemas = False
    supports_comments = True
    colspecs = colspecs
    
    statement_compiler = GBase8sCompiler
    type_compiler = GBase8sTypeCompiler
    execution_ctx_cls = GBase8sExecutionContext
    ddl_compiler = GBase8sDDLCompiler
    
    
    
    @classmethod
    def dbapi(self):
        import gbase8sdb
        gbase8sdb.defaults.fetch_lobs = False
        return gbase8sdb
    
    def create_connect_args(self, url):
        dsn_args = {}
        opts = url.translate_connect_args()
        dsn_args['host'] = opts.get('host', None)
        dsn_args['port'] = opts.get('port', 9088)
        dsn_args['db_name'] = opts.get('database', None)
        if dsn_args['db_name'] is None:         # 如果问号前只有dbname,会被识别为host
            dsn_args['db_name'] = opts.get('host', None)
            dsn_args['host'] = None
        query_args = {k.lower(): v for k, v in url.query.items()}
        if 'gbasedbtserver' in query_args:
            dsn_args['server_name'] = query_args.pop('gbasedbtserver')
        else:
            raise exc.ArgumentError(
                "gbase8sdb requires GBASEDBTSERVER=<server_name> in the query string"
            )
        dsn_args.update(query_args)
        dsn = self.dbapi.makedsn(**dsn_args)
        return (), {'dsn': dsn, 'user': opts['username'], 'password': opts['password']}
    
    def _has_table_object(self, connection, objname, schema=None, types_=('T', 'V')):
        result = connection.exec_driver_sql(
            f"""select count(*) from {schema+'.' if schema else ''}systables 
            where tabname=? and tabtype in (%s)
            """ % ','.join(['?'] * len(types_)),
            (objname, *types_)
        ).scalar()
        return result > 0
    
    
    @reflection.cache   # 缓存查询结果
    def has_table(self, connection, table_name, schema=None, **kwargs):
        return self._has_table_object(connection, table_name, schema)
    
    def _get_table_names(self, connection, schema, typ, **kw):
        s = f"SELECT tabname FROM {schema+'.' if schema else ''}systables WHERE tabtype=? and flags = 16384"
        return connection.exec_driver_sql(s, (typ, )).scalars().all()

    @reflection.cache
    def get_table_names(self, connection, schema=None, **kw):
        return self._get_table_names(connection, schema, 'T', **kw)

    @reflection.cache
    def get_schema_names(self, connection, **kw):
        s = "SELECT DBS_DBSNAME FROM SYSMASTER.SYSDBSLOCALE"
        rp = connection.exec_driver_sql(s)
        return [r[0].strip() for r in rp]

    @reflection.cache
    def get_view_names(self, connection, schema=None, **kw):
        return self._get_table_names(connection, schema, 'V', **kw)
    
    
    @reflection.cache
    def get_columns(self, connection, table_name, schema=None, **kw):
        c = connection.exec_driver_sql(
            f"""SELECT colname, coltype, colattr, collength, t3.default, t1.colno, extended_id 
                FROM {schema+'.' if schema else ''}syscolumns AS t1 , 
                {schema+'.' if schema else ''}systables AS t2 , 
                OUTER {schema+'.' if schema else ''}sysdefaultsexpr AS t3
                WHERE t1.tabid = t2.tabid AND t2.tabname=?
                AND t3.tabid = t2.tabid AND t3.colno = t1.colno
                AND t3.type = 'T'
                ORDER BY t1.colno""", (table_name,))
        pk_constraint = self.get_pk_constraint(connection, table_name, schema, **kw)
        primary_cols = pk_constraint['constrained_columns']

        columns = []
        rows = c.fetchall()
        c_comments = connection.exec_driver_sql(
            f"""select colname, comments from {schema+'.' if schema else ''}syscolcomments where tabname=?""", (table_name,))
        col_comments = {row[0]: row[1].rstrip() if row[1] is not None and row[1].rstrip() != '' else None
                                 for row in c_comments.fetchall()}
        for name, coltype, colattr, collength, default, colno, extended_id in rows:

            autoincrement = False
            primary_key = False

            if name in primary_cols:
                primary_key = True

            not_nullable, coltype = divmod(coltype, 256)

            if coltype == 6:  # Serial, mark as autoincrement
                autoincrement = True

            if coltype == 0 or coltype == 13:  # char, varchar
                coltype = ischema_names[coltype](collength)
                if default:
                    default = "'%s'" % default
            elif coltype == 5:  # decimal
                precision, scale = (collength & 0xFF00) >> 8, collength & 0xFF
                if scale == 255:
                    # scale = 0
                    coltype = sqltypes.INTEGER()
                else:
                    coltype = sqltypes.Numeric(precision, scale)
            elif coltype == 41:
                if extended_id == 10:
                    coltype = sqltypes.BLOB
                elif extended_id == 11:
                    coltype = sqltypes.CLOB
                elif extended_id == 5:
                    coltype = sqltypes.Boolean
                else:
                    util.warn("Did not recognize type '%s' of column '%s'" %
                              (coltype, name))
                    coltype = sqltypes.NULLTYPE
            else:
                try:
                    coltype = ischema_names[coltype]
                except KeyError:
                    util.warn("Did not recognize type '%s' of column '%s'" %
                              (coltype, name))
                    coltype = sqltypes.NULLTYPE
            if colattr == 768:  # 虚拟列标记
                computed = dict(sqltext=default)
                default = None
            else:
                computed = None
            cdict = dict(name=name, type=coltype, nullable=not not_nullable,
                               default=default, autoincrement=autoincrement,
                               primary_key=primary_key, comment=col_comments.get(name))
            if computed is not None:
                cdict["computed"] = computed
            columns.append(cdict)
        return columns

    
    @reflection.cache
    def _get_column_name_by_tabid_colno(self, connection, tabid, colno, schema=None):
        colname = connection.exec_driver_sql(
            f"""select colname from {schema+'.' if schema else ''}syscolumns where tabid=? and colno=?""", (tabid, colno)
        ).scalar()
        return colname
    
    @reflection.cache
    def get_pk_constraint(self, connection, table_name, schema=None, **kw):
        # Select the column positions from sysindexes for sysconstraints
        row = connection.exec_driver_sql(
            f"""SELECT t1.tabid, t2.*
            FROM {schema+'.' if schema else ''}systables AS t1, 
            {schema+'.' if schema else ''}sysindexes AS t2, 
            {schema+'.' if schema else ''}sysconstraints AS t3
            WHERE t1.tabid=t2.tabid AND t1.tabname=?
            AND t2.idxname=t3.idxname AND t3.constrtype='P'""",
            (table_name,)
        ).fetchone()
        if row:
            colpos = list(dict.fromkeys([getattr(row, 'part%d' % x) for x in range(1, 17) if getattr(row, 'part%d' % x) > 0]))
        else:
            colpos = []
        cols = []
        for pos in colpos:
            cols.append(self._get_column_name_by_tabid_colno(connection, row.tabid, pos, schema))         
        return {'constrained_columns': cols, 'name': None}   
    
    @reflection.cache
    def get_unique_constraints(self, connection, table_name, schema=None, **kw):
        indexes = self.get_indexes(connection, table_name, schema, constraint=True, **kw)
        constraints = []
        for index in indexes:
            if index['unique']:
                constraints.append({
                    'name': index['name'],
                    'column_names': index['column_names']
                })
        return constraints
    
    @reflection.cache
    def get_foreign_keys(self, connection, table_name, schema=None, **kw):
        # 查询全部外键
        rows = connection.exec_driver_sql(
            f"""
            SELECT t1.tabid, t1.tabname, t3.constrname, t3.constrid, t2.*
            FROM {schema+'.' if schema else ''}systables AS t1, 
            {schema+'.' if schema else ''}sysindexes AS t2, 
            {schema+'.' if schema else ''}sysconstraints AS t3
            WHERE t1.tabid=t2.tabid AND t1.tabname=?
            AND t2.idxname=t3.idxname AND t3.constrtype='R'
            """, 
            (table_name, )
            ).fetchall()
        foreigen_keys = []
        for row in rows:
            name = row.constrname
            constrid = row.constrid
            colpos = list(dict.fromkeys([getattr(row, 'part%d' % x) for x in range(1, 17) if getattr(row, 'part%d' % x) > 0]))
            constrained_columns = []
            for pos in colpos:
                constrained_columns.append(self._get_column_name_by_tabid_colno(connection, row.tabid, pos)) 
            refered_row = connection.exec_driver_sql(f"""
                            SELECT t4.tabname,t4.tabid, t2.*, t1.delrule
                            FROM {schema+'.' if schema else ''}sysreferences as t1,  
                            {schema+'.' if schema else ''}sysindexes AS t2, 
                            {schema+'.' if schema else ''}sysconstraints AS t3, 
                            {schema+'.' if schema else ''}systables AS t4
                            WHERE t1.constrid = ? AND t3.constrid = t1.primary
                            AND t2.idxname=t3.idxname AND t4.tabid = t1.ptabid
                            """, (constrid,)).fetchone()
            refered_colpos = list(dict.fromkeys([getattr(refered_row, 'part%d' % x) for x in range(1, 16) if getattr(refered_row, 'part%d' % x) > 0]))
            referred_columns = []
            for pos in refered_colpos:
                referred_columns.append(self._get_column_name_by_tabid_colno(connection, refered_row.tabid, pos)) 
               
            foreign_key = {
                 'name': name,
                 'constrained_columns': constrained_columns,
                 'referred_schema': None,
                 'referred_table': refered_row.tabname,
                 'referred_columns': referred_columns,
                 'options': {'ondelete': 'CASCADE'} if refered_row.delrule == 'C' else {}
             }
            foreigen_keys.append(foreign_key)
        return foreigen_keys
    
    
    @reflection.cache
    def get_indexes(self, connection, table_name, schema, **kw):
        c = connection.exec_driver_sql(
            f"""SELECT t1.*, t2.constrtype, t2.constrname
            FROM {schema+'.' if schema else ''}sysindexes AS t1 
            LEFT JOIN {schema+'.' if schema else ''}sysconstraints AS t2
            ON (t1.tabid = t2.tabid AND t1.idxname = t2.idxname)
            WHERE
            t1.tabid = (SELECT tabid FROM {schema+'.' if schema else ''}systables WHERE tabname=?)
            """,
            (table_name,))

        indexes = []
        for row in c.fetchall():
            if row.constrtype in ('P', 'R'):  # Cannot filter in the statement above due to informix bug?
                continue
            colnos = [getattr(row, 'part%d' % x) for x in range(1, 17)]
            colnos = [abs(x) for x in colnos if x]
            place_holder = ','.join('?' * len(colnos))
            c = connection.exec_driver_sql(
                f"""SELECT t1.colno, t1.colname
                FROM {schema+'.' if schema else ''}syscolumns AS t1, 
                {schema+'.' if schema else ''}systables AS t2
                WHERE t2.tabname=? AND t1.tabid = t2.tabid
                AND t1.colno IN (%s)""" % place_holder,
                (table_name,) + tuple(colnos)
            ).fetchall()
            mapping = dict(c)
            if kw.get('constraint', False):
                if row.constrname:
                    indexes.append({
                    'name': row.constrname,
                    'unique': row.idxtype.lower() == 'u',
                    'column_names': [mapping[no] for no in colnos],
                    'dialect_options': {}
                })
            else:
                if not row.constrname:
                    indexes.append({
                        'name': row.idxname,
                        'unique': row.idxtype.lower() == 'u',
                        'column_names': [mapping[no] for no in colnos],
                        'dialect_options': {}
                    })        
        return indexes
    
    def set_isolation_level(self, connection, level):
        if hasattr(connection, "dbapi_connection"):
            dbapi_connection = connection.dbapi_connection
        else:
            dbapi_connection = connection

        if level == "AUTOCOMMIT":
            dbapi_connection.autocommit = True
        else:
            dbapi_connection.autocommit = False
            dbapi_connection.rollback()
            with dbapi_connection.cursor() as cursor:
                cursor.execute(f"SET ISOLATION TO {level}")
                
    def get_isolation_level(self, dbapi_connection):
        with dbapi_connection.cursor() as cursor:
            cursor.execute("""
                select scs_isolationlevel from sysmaster.syssqlcurses
            """)
            row = cursor.fetchone()
            if row is None:
                raise exc.InvalidRequestError(
                    "could not retrieve isolation level"
                )
            result = row[0]
        return result
    
    def get_isolation_level_values(self, dbapi_connection):
        return [
            "DIRTY READ", 
            "COMMITTED READ LAST COMMITTED", 
            "COMMITTED READ", 
            "CURSOR STABILITY",
            "REPEATABLE READ",             
            "AUTOCOMMIT"
            ]

    def get_default_isolation_level(self, dbapi_conn):
        return self.get_isolation_level(dbapi_conn)
    
    @reflection.cache
    def get_check_constraints(self, connection, table_name, schema=None, **kw):
        c = connection.exec_driver_sql(f"""
            SELECT t1.*, t2.checktext 
            FROM {schema+'.' if schema else ''}sysconstraints AS t1, 
            {schema+'.' if schema else ''}syschecks AS t2
            WHERE t1.tabid = (SELECT tabid FROM {schema+'.' if schema else ''}systables WHERE tabname=?)
            AND t1.constrid = t2.constrid AND t2.type = 'T' AND t1.constrtype = 'C'
            ORDER BY t1.constrname, t2.seqno
        """, (table_name, ))

        constraints = []
        for k, g in groupby(c.fetchall(), lambda row: row.constrname):
            constraints.append({
                'name': k,
                'sqltext': ''.join(map(lambda row: row.checktext, g)).rstrip()
            })

        return constraints

    
    @reflection.cache
    def has_sequence(self, connection, sequence_name, schema=None, **kw):
        return self._has_table_object(connection, sequence_name, schema, ('Q', ))
    
    @reflection.cache
    def get_sequence_names(self, connection, schema=None, **kw):
        return self._get_table_names(connection, schema, 'Q', **kw)
    
    @reflection.cache
    def get_view_definition(self, connection, view_name, schema=None, **kw):
        view_def = connection.exec_driver_sql(
            f"""SELECT t1.viewtext
            FROM {schema+'.' if schema else ''}sysviews AS t1 , 
            {schema+'.' if schema else ''}systables AS t2
            WHERE t1.tabid=t2.tabid AND t2.tabname=?
            ORDER BY seqno""",
            (view_name,) ).scalar()

        if view_def:
            return view_def
        else:
            raise exc.NoSuchTableError(view_name)
        

    @reflection.cache
    def get_table_comment(self, connection, table_name, schema=None, **kw):
        comment = connection.exec_driver_sql(
            f"""select comments from {schema+'.' if schema else ''}syscomments where tabname=?
            """,
            (table_name,)).scalar()
        
        if comment is not None:
            comment = comment.rstrip()
            if comment == '':
                comment = None
        return {'text': comment}
