from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from contextlib import contextmanager
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Определение базовой модели
Base = declarative_base()


class DatabaseManager:
    def __init__(self):
        cred = credentials.Certificate("path/to/your/polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json")
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def add_client(self, client_data):
        clients_ref = self.db.collection('clients')
        existing_client = clients_ref.where('client_id', '==', client_data['client_id']).get()

        if existing_client:
            print("Client already exists!")
            return False
        else:
            clients_ref.add(client_data)
            print("Client added successfully!")
            return True

    def get_clients(self, limit=10):
        clients_ref = self.db.collection('clients').limit(limit)
        return [client.to_dict() for client in clients_ref.stream()]

    def get_all_clients(self):
        clients_ref = self.db.collection('clients')
        return [client.to_dict() for client in clients_ref.stream()]


# Модель для хранения информации о заказчиках
class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


# Модель для хранения имен
class Name(Base):
    __tablename__ = 'names'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


# Модель для хранения дел
class Case(Base):
    __tablename__ = 'cases'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name_id = Column(Integer, ForeignKey('names.id'))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    comment = Column(String)
    creation_date = Column(DateTime, default=datetime.datetime.utcnow)
    deleted = Column(Boolean, default=False)  # добавляем атрибут deleted

    name = relationship("Name")
    customer = relationship("Customer")


class Proforma(Base):
    __tablename__ = 'proformas'
    id = Column(Integer, primary_key=True)
    case_number = Column(String)
    number = Column(String)
    name = Column(String)
    comment = Column(String)


# Создание подключения к базе данных и сессии
engine = create_engine('sqlite:///mydatabase.db')
Session = scoped_session(sessionmaker(bind=engine))
Base.metadata.create_all(engine)


# Контекстный менеджер для управления сессиями
@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


# Функции для добавления и получения заказчиков
def add_customer(name):
    with session_scope() as session:
        customer = Customer(name=name)
        session.add(customer)


def get_all_customers():
    with session_scope() as session:
        customers = session.query(Customer.name).all()
        return [customer[0] for customer in customers]


# Функции для добавления и получения имен
def add_name(name):
    with session_scope() as session:
        name = Name(name=name)
        session.add(name)


def get_all_names():
    with session_scope() as session:
        names = session.query(Name.name).all()
        return [name[0] for name in names]


# Функции для работы с делами
def add_case(name_id, customer_id, comment):
    with session_scope() as session:
        new_case = Case(name_id=name_id, customer_id=customer_id if customer_id else None, comment=comment if comment else "")
        session.add(new_case)


def get_all_cases():
    with session_scope() as session:
        cases = session.query(Case).filter_by(deleted=False).all()
        cases_list = [{
            'id': case.id,
            'name_sur': case.name.name if case.name else "No Name",
            'customer': case.customer.name if case.customer else "No Customer",
            'comment': case.comment if case.comment else "",
            'creation_date': case.creation_date.strftime('%Y-%m-%d %H:%M:%S') if case.creation_date else "No Date"
        } for case in cases]
        return cases_list


def delete_case(case_id):
    with session_scope() as session:
        case = session.query(Case).filter(Case.id == case_id).one_or_none()
        if case:
            case.deleted = True  # помечаем дело как удаленное
            print(f"Удалено дело с ID: {case_id}")
        else:
            print(f"Дело с ID {case_id} не найдено")


def get_name_id(name):
    with session_scope() as session:
        name_instance = session.query(Name).filter_by(name=name).first()
        if not name_instance:
            name_instance = Name(name=name)
            session.add(name_instance)
            session.commit()
        return name_instance.id


def get_customer_id(customer_name):
    if not customer_name:
        return None
    with session_scope() as session:
        customer_instance = session.query(Customer).filter_by(name=customer_name).first()
        if not customer_instance:
            customer_instance = Customer(name=customer_name)
            session.add(customer_instance)
            session.commit()
        return customer_instance.id


def get_last_proforma_number():
    with session_scope() as session:
        last_proforma = session.query(Proforma).order_by(Proforma.number.desc()).first()
        if last_proforma:
            return last_proforma.number
        return None


def add_proforma_to_database(case_number, proforma_number, name, comment):
    with session_scope() as session:
        new_proforma = Proforma(case_number=case_number, number=proforma_number, name=name, comment=comment)
        session.add(new_proforma)


if __name__ == "__main__":
    Base.metadata.create_all(engine)