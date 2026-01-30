import dataclasses

from david8.core.base_dml import BaseUpdate, FullTableName
from david8.protocols.dialect import DialectProtocol

from ..protocols.sql import UpdateProtocol


@dataclasses.dataclass(slots=True)
class Update(BaseUpdate, UpdateProtocol):
    returning_columns: tuple[str, ...] = dataclasses.field(default_factory=tuple)
    from_table_constr: FullTableName = dataclasses.field(default_factory=FullTableName)
    from_table_alias: str = ''

    def _from_table_to_sql(self, dialect: DialectProtocol) -> str:
        if not self.from_table_constr.table:
            return ''

        from_table = f' FROM {self.from_table_constr.get_sql(dialect)}'
        if self.from_table_alias:
            from_table = f'{from_table} AS {dialect.quote_ident(self.from_table_alias)}'

        return from_table

    def _get_sql(self, dialect: DialectProtocol) -> str:
        table = self._table_to_sql(dialect)
        set_columns = self._set_construction_to_sql(dialect)
        from_ = self._from_table_to_sql(dialect)
        where = self.where_construction.get_sql(dialect)
        if self.returning_columns:
            returning = f' RETURNING {", ".join(dialect.quote_ident(r) for r in self.returning_columns)}'
        else:
            returning = ''

        return f'UPDATE {table}{set_columns}{from_}{where}{returning}'

    def returning(self, *args: str) -> 'UpdateProtocol':
        self.returning_columns += args
        return self

    def from_table(self, table_name: str, alias: str = '', db_name: str = '') -> 'UpdateProtocol':
        self.from_table_constr.set_names(table_name, db_name)
        self.from_table_alias = alias
        return self
