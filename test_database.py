import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import add_case, get_all_cases, Base, Case


class TestDatabaseFunctions(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.session.close()

    def test_add_and_retrieve_cases(self):
        add_case('Test Name 1', 'Test Comment 1', self.session)
        add_case('Test Name 2', 'Test Comment 2', self.session)
        cases = get_all_cases(self.session)
        self.assertEqual(len(cases), 2)
        self.assertEqual(cases[0].name_sur, 'Test Name 1')
        self.assertEqual(cases[1].name_sur, 'Test Name 2')

    def test_delete_case(self):
        # Измените этот тест, чтобы использовать self.session для операций с базой данных
        pass


if __name__ == '__main__':
    unittest.main()
