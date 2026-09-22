import unittest

from app.sql_validator import validate_read_only_sql


class SQLValidatorTests(unittest.TestCase):
    def test_read_only_select(self):
        valid, error = validate_read_only_sql("SELECT name FROM customers")
        self.assertTrue(valid, error)

    def test_read_only_cte(self):
        valid, error = validate_read_only_sql("WITH totals AS (SELECT COUNT(*) AS n FROM orders) SELECT n FROM totals")
        self.assertTrue(valid, error)

    def test_rejects_writes(self):
        for sql in ("DELETE FROM customers", "DROP TABLE orders", "UPDATE customers SET name='x'", "INSERT INTO customers VALUES (1)"):
            with self.subTest(sql=sql):
                self.assertFalse(validate_read_only_sql(sql)[0])

    def test_rejects_multiple_statements(self):
        self.assertFalse(validate_read_only_sql("SELECT 1; DELETE FROM customers")[0])

    def test_rejects_empty_query(self):
        self.assertFalse(validate_read_only_sql("  ")[0])

    def test_rejects_locking_query(self):
        self.assertFalse(validate_read_only_sql("SELECT * FROM customers FOR UPDATE")[0])


if __name__ == "__main__":
    unittest.main()
