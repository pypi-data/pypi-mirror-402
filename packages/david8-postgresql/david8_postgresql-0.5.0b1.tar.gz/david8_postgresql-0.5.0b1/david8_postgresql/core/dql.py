from david8.core.base_dql import BaseSelect
from david8.protocols.dialect import DialectProtocol

from ..protocols.sql import SelectProtocol


class Select(BaseSelect, SelectProtocol):
    row_lock_mode: str = ''

    def for_key_share(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR KEY SHARE'
        return self

    def for_key_share_nw(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR KEY SHARE NOWAIT'
        return self

    def for_key_share_sl(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR KEY SHARE SKIP LOCKED'
        return self

    def for_share(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR SHARE'
        return self

    def for_share_nw(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR SHARE NOWAIT'
        return self

    def for_share_sl(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR SHARE SKIP LOCKED'
        return self

    def for_update(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR UPDATE'
        return self

    def for_update_nw(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR UPDATE NOWAIT'
        return self

    def for_update_sl(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR UPDATE SKIP LOCKED'
        return self

    def for_nk_update(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR NO KEY UPDATE'
        return self

    def for_nk_update_nw(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR NO KEY UPDATE NOWAIT'
        return self

    def for_nk_update_sl(self) -> 'SelectProtocol':
        self.row_lock_mode = 'FOR NO KEY UPDATE SKIP LOCKED'
        return self

    def _get_sql(self, dialect: DialectProtocol):
        sql =  super()._get_sql(dialect)
        return f'{sql} {self.row_lock_mode}' if self.row_lock_mode else sql
