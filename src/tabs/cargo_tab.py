from PyQt5.QtWidgets import QTableWidgetItem, QComboBox, QDateEdit
from PyQt5.QtCore import QDate
from src.local_data_manager import LocalDataManager
from src.delegates import ComboBoxDelegate, QDateEditDelegate


class CargoTab:
    def __init__(self, parent, firebase_manager):
        self.parent = parent
        self.firebase_manager = firebase_manager
        self.data_manager = LocalDataManager()  # Загрузка данных из JSON
        self.cargo_table = self.parent.cargoTable

        # Загрузка данных из базы
        self.cases = self.firebase_manager.get_all_cases() or {}
        self.clients = self.firebase_manager.get_all_clients() or {}
        self.managers = self.firebase_manager.get_all_managers() or []
        self.suppliers = self.firebase_manager.get_all_suppliers() or {}

        # Настройка вкладки
        self.setup_cargo_tab()

    def setup_cargo_tab(self):
        """Настройка вкладки 'Грузы'."""
        self.setup_cargo_table()
        self.setup_dropdowns()

    def setup_dropdowns(self):
        """Загрузка данных в выпадающие списки."""
        # Заполнение выпадающего списка "Номер дела"
        self.parent.cargoCaseNumberInput.clear()
        self.parent.cargoCaseNumberInput.addItems(self.cases.keys())

        # Заполнение выпадающего списка "Менеджер"
        self.parent.cargoManagerInput.clear()
        self.parent.cargoManagerInput.addItems(self.managers)

        # Заполнение выпадающего списка "Поставщик"
        self.parent.cargoSupplierInput.clear()
        self.parent.cargoSupplierInput.addItems(supplier['name'] for supplier in self.suppliers.values())

        # Заполнение выпадающего списка "Клиент"
        self.parent.cargoCustomerInput.clear()
        self.parent.cargoCustomerInput.addItems(client['name'] for client in self.clients.values())

    def load_cargo_table(self):
        """Метод для загрузки данных в таблицу."""
        self.cargo_table.setRowCount(0)  # Очистить таблицу перед загрузкой
        cargo_data = self.firebase_manager.get_all_cargo()  # Получаем данные из Firebase
        for cargo in cargo_data:
            row_position = self.cargo_table.rowCount()
            self.cargo_table.insertRow(row_position)
            for col_index, value in enumerate(cargo.values()):
                self.cargo_table.setItem(row_position, col_index, QTableWidgetItem(str(value)))

    def setup_cargo_table(self):
        """Настройка колонок и делегатов таблицы."""
        self.cargo_table.setColumnCount(10)
        self.cargo_table.setHorizontalHeaderLabels([
            "Case Number", "Manager", "Client", "Supplier", "Deadline",
            "ETD", "ETA", "TK", "Destination", "Tracking"
        ])

        # Установим редакторы для столбцов с выпадающими списками и календарем
        self.cargo_table.setItemDelegateForColumn(4, QDateEditDelegate(self.cargo_table))  # Deadline
        self.cargo_table.setItemDelegateForColumn(5, QDateEditDelegate(self.cargo_table))  # ETD
        self.cargo_table.setItemDelegateForColumn(6, QDateEditDelegate(self.cargo_table))  # ETA
        self.cargo_table.setItemDelegateForColumn(7, ComboBoxDelegate(self.cargo_table, self.data_manager.load_transport_companies()))  # TK
        self.cargo_table.setItemDelegateForColumn(8, ComboBoxDelegate(self.cargo_table, self.data_manager.load_destinations()))  # Destination

    def add_cargo_row(self, row_position):
        """Добавляет строку в таблицу 'Грузы'."""
        self.cargo_table.insertRow(row_position)

        # Номер заказа
        case_selector = QComboBox()
        case_selector.setEditable(True)
        case_selector.addItems(self.cases.keys())
        case_selector.currentTextChanged.connect(
            lambda text: self.fill_cargo_row(text, row_position)
        )
        self.cargo_table.setCellWidget(row_position, 0, case_selector)

        # Deadline, ETD, ETA
        for col in range(4, 7):  # Колонки для календарей
            date_selector = QDateEdit()
            date_selector.setCalendarPopup(True)
            date_selector.setDate(QDate.currentDate())  # Устанавливаем текущую дату
            self.cargo_table.setCellWidget(row_position, col, date_selector)

        # TK (Транспортная компания)
        tk_selector = QComboBox()
        tk_selector.addItems(self.data_manager.load_transport_companies())
        self.cargo_table.setCellWidget(row_position, 7, tk_selector)

        # Пункт назначения
        destination_selector = QComboBox()
        destination_selector.addItems(self.data_manager.load_destinations())
        self.cargo_table.setCellWidget(row_position, 8, destination_selector)

        # Tracking
        self.cargo_table.setItem(row_position, 9, QTableWidgetItem(""))

    def fill_cargo_row(self, case_id, row_position):
        """Автозаполнение строки таблицы 'Грузы'."""
        case_data = self.cases.get(case_id, {})

        if case_data:
            # Менеджер
            manager = case_data.get('manager', '')
            self.cargo_table.setItem(row_position, 1, QTableWidgetItem(manager))

            # Клиент
            client_name = case_data.get('client_name', '')
            self.cargo_table.setItem(row_position, 2, QTableWidgetItem(client_name))

            # Поставщик
            supplier = case_data.get('supplier', '')
            self.cargo_table.setItem(row_position, 3, QTableWidgetItem(supplier))