import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app.main import app


class ApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        with cls.engine.begin() as connection:
            connection.execute(text('CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT)'))
            connection.execute(text("INSERT INTO customers (id, name) VALUES (1, 'Priya')"))
            connection.execute(text('CREATE TABLE events (id INTEGER PRIMARY KEY)'))
            connection.execute(text('INSERT INTO events (id) VALUES (:id)'), [{'id': i} for i in range(250)])
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.engine.dispose()

    def test_schema_returns_structured_tables(self):
        with patch('app.main.get_engine', return_value=self.engine), patch('app.main.get_connection_info', return_value={'connection_id': 'test', 'label': 'Test', 'dialect': 'sqlite'}):
            response = self.client.get('/schema?connection_id=test')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('tables', data)
        self.assertIn('customers', [table['name'] for table in data['tables']])
        self.assertTrue(next(table for table in data['tables'] if table['name'] == 'customers')['columns'])

    def test_query_limits_results_and_reports_truncation(self):
        from types import SimpleNamespace
        plan = SimpleNamespace(status='success', sql='SELECT id FROM events ORDER BY id', interpreted_question='List events', explanation='Events')
        with patch('app.main.get_engine', return_value=self.engine), patch('app.main.get_connection_info', return_value={'connection_id': 'test', 'label': 'Test', 'dialect': 'sqlite'}), patch('app.main.build_query_plan', return_value=plan):
            response = self.client.post('/query', json={'question': 'List events', 'connection_id': 'test'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['row_count'], 200)
        self.assertTrue(data['truncated'])
        self.assertEqual(len(data['result']), 200)

    def test_execution_error_does_not_expose_database_details(self):
        from types import SimpleNamespace
        plan = SimpleNamespace(status='success', sql='SELECT secret_column FROM customers', interpreted_question='Secret', explanation='')
        with patch('app.main.get_engine', return_value=self.engine), patch('app.main.get_connection_info', return_value={'connection_id': 'test', 'label': 'Test', 'dialect': 'sqlite'}), patch('app.main.build_query_plan', return_value=plan):
            data = self.client.post('/query', json={'question': 'Secret', 'connection_id': 'test'}).json()
        self.assertEqual(data['status'], 'execution_error')
        self.assertNotIn('no such column', data['message'].lower())


if __name__ == '__main__':
    unittest.main()
