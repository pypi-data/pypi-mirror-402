from david8.protocols.sql import FunctionProtocol
from parameterized import parameterized

from david8_postgresql.functions_array import array_remove, array_replace, unnest
from david8_postgresql.functions_str import concat
from tests.base_test import BaseTest


class TestFunctionsArray(BaseTest):

    @parameterized.expand([
        (
            unnest('column1', 'column2', 'column3'),
            'SELECT unnest(column1, column2, column3)',
            'SELECT unnest("column1", "column2", "column3")',
        ),
        (
            unnest(concat('column1', 'column2')),
            'SELECT unnest(concat(column1 || column2))',
            'SELECT unnest(concat("column1" || "column2"))',
        ),
        (
            array_remove('column1', 1),
            "SELECT array_remove(column1, 1)",
            "SELECT array_remove(\"column1\", 1)",
        ),
        (
            array_remove('column1', 0.5),
            "SELECT array_remove(column1, 0.5)",
            "SELECT array_remove(\"column1\", 0.5)",
        ),
        (
            array_remove('column1', 'Legacy'),
            "SELECT array_remove(column1, 'Legacy')",
            "SELECT array_remove(\"column1\", 'Legacy')",
        ),
        (
            array_replace('column1', 'Legacy', 'Fixed'),
            "SELECT array_replace(column1, 'Legacy', 'Fixed')",
            'SELECT array_replace("column1", \'Legacy\', \'Fixed\')',
        ),
        (
            array_replace('column1', -1, 0),
            "SELECT array_replace(column1, -1, 0)",
            'SELECT array_replace("column1", -1, 0)',
        ),
    ])
    def test_array_fn(self, fn: FunctionProtocol, exp_sql: str, exp_w_sql: str):
        query = self.qb.select(fn)
        self.assertEqual(query.get_sql(), exp_sql)

        query = self.qb_w.select(fn)
        self.assertEqual(query.get_sql(), exp_w_sql)
