import logging
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QComboBox, QPushButton, QTableWidget, QHeaderView
from PyQt5.QtCore import QDate
from src.delegates import QDateEditDelegate

class CargoTab:
    def __init__(self, parent, firebase_manager):
        self.parent = parent
        self.firebase_manager = firebase_manager

        # Поиск виджетов по objectName из main.ui
        self.caseNumberInput = self.parent.findChild(QComboBox, 'cargoCaseNumberInput')
        self.supplierInput = self.parent.findChild(QComboBox, 'cargoSupplierInput')
        self.addCargoButton = self.parent.findChild(QPushButton, 'addCargoButton')
        self.deleteCargoButton = self.parent.findChild(QPushButton, 'deleteCargoButton')
        self.cargoTable = self.parent.findChild(QTableWidget, 'cargoTable')

        missing_widgets = []
        if self.caseNumberInput is None:
            missing_widgets.append('cargoCaseNumberInput')
        if self.supplierInput is None:
            missing_widgets.append('cargoSupplierInput')
        if self.addCargoButton is None:
            missing_widgets.append('addCargoButton')
        if self.deleteCargoButton is None:
            missing_widgets.append('deleteCargoButton')
        if self.cargoTable is None:
            missing_widgets.append('cargoTable')
        if missing_widgets:
            msg = f"Отсутствуют следующие виджеты: {', '.join(missing_widgets)}"
            logging.error(msg)
            QMessageBox.critical(self.parent, "Ошибка", msg)
            return

        # Загружаем данные для выпадающих списков
        self.load_combobox_data()
        # Настраиваем таблицу "Грузы"
        self.setup_cargo_table()
        # Загружаем данные в таблицу
        self.load_cargo_table()

        # Подключаем кнопки
        self.addCargoButton.clicked.connect(self.add_cargo)
        self.deleteCargoButton.clicked.connect(self.delete_cargo)

    def load_combobox_data(self):
        try:
            cases = self.firebase_manager.get_all_cases() or {}
            case_numbers = [key for key, value in cases.items() if isinstance(value, dict)]
            suppliers = self.firebase_manager.get_all_suppliers() or {}
            supplier_names = []
            if isinstance(suppliers, dict):
                supplier_names = [data.get('name', '') for data in suppliers.values() if isinstance(data, dict)]
            elif isinstance(suppliers, list):
                supplier_names = [item.get('name', '') for item in suppliers if isinstance(item, dict)]
            self.caseNumberInput.clear()
            self.supplierInput.clear()
            self.caseNumberInput.addItems(case_numbers)
            self.supplierInput.addItems(supplier_names)
            logging.info("Данные для выпадающих списков на вкладке 'Грузы' загружены успешно.")
        except Exception as e:
            logging.error(f"Ошибка загрузки данных в выпадающие списки на вкладке 'Грузы': {e}")
            QMessageBox.critical(self.parent, "Ошибка", f"Ошибка загрузки данных: {e}")

    def setup_cargo_table(self):
        headers = ["ID", "Case Number", "Manager", "Client", "Supplier", "Deadline", "ETD", "ETA", "TK", "Destination", "Tracking"]
        self.cargoTable.setColumnCount(len(headers))
        self.cargoTable.setHorizontalHeaderLabels(headers)
        self.cargoTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cargoTable.setItemDelegateForColumn(5, QDateEditDelegate(self.cargoTable))

    def load_cargo_table(self):
        try:
            self.cargoTable.setRowCount(0)
            cargo_data = self.firebase_manager.get_all_cargo() or {}
            if isinstance(cargo_data, dict):
                for cargo_id, cargo in cargo_data.items():
                    if not isinstance(cargo, dict):
                        logging.warning(f"Пропуск записи 'Грузы', так как она не является словарём: {cargo_id}")
                        continue
                    self.insert_cargo_row(cargo_id, cargo)
            elif isinstance(cargo_data, list):
                for idx, cargo in enumerate(cargo_data):
                    if cargo is None or not isinstance(cargo, dict):
                        logging.warning(f"Пропуск записи 'Грузы', так как она не является словарём: индекс {idx}")
                        continue
                    cargo_id = str(idx)
                    self.insert_cargo_row(cargo_id, cargo)
            else:
                logging.error("Cargo data is not a dictionary or list.")
            logging.info("Таблица 'Грузы' загружена.")
        except Exception as e:
            logging.error(f"Ошибка загрузки таблицы 'Грузы': {e}")
            QMessageBox.critical(self.parent, "Ошибка", f"Ошибка загрузки таблицы 'Грузы': {e}")

    def insert_cargo_row(self, cargo_id, cargo):
        row = self.cargoTable.rowCount()
        self.cargoTable.insertRow(row)
        self.cargoTable.setItem(row, 0, QTableWidgetItem(str(cargo_id)))
        self.cargoTable.setItem(row, 1, QTableWidgetItem(str(cargo.get("case_number", ""))))
        self.cargoTable.setItem(row, 2, QTableWidgetItem(str(cargo.get("manager", ""))))
        self.cargoTable.setItem(row, 3, QTableWidgetItem(str(cargo.get("client", ""))))
        self.cargoTable.setItem(row, 4, QTableWidgetItem(str(cargo.get("supplier", ""))))
        self.cargoTable.setItem(row, 5, QTableWidgetItem(str(cargo.get("deadline", ""))))
        self.cargoTable.setItem(row, 6, QTableWidgetItem(str(cargo.get("etd", ""))))
        self.cargoTable.setItem(row, 7, QTableWidgetItem(str(cargo.get("eta", ""))))
        self.cargoTable.setItem(row, 8, QTableWidgetItem(str(cargo.get("tk", ""))))
        self.cargoTable.setItem(row, 9, QTableWidgetItem(str(cargo.get("destination", ""))))
        self.cargoTable.setItem(row, 10, QTableWidgetItem(str(cargo.get("tracking", ""))))

    def add_cargo(self):
        try:
            case_number = self.caseNumberInput.currentText()
            supplier = self.supplierInput.currentText()
            # Проверка: если груз с таким номером уже существует, не даём добавить
            existing_cargo = self.firebase_manager.get_all_cargo() or {}
            for cargo_id, cargo in existing_cargo.items():
                if isinstance(cargo, dict) and cargo.get("case_number", "") == case_number:
                    QMessageBox.warning(self.parent, "Добавление груза",
                        f"Груз с номером дела {case_number} уже существует. Повторное добавление невозможно.")
                    return

            # Оставляем поля Manager и Client пустыми, их можно задавать вручную позже
            manager = ""
            client = ""
            deadline = ""  # Здесь оставляем пустым. Пользователь должен вручную выбрать дату в таблице.
            new_cargo = {
                "case_number": case_number,
                "manager": manager,
                "client": client,
                "supplier": supplier,
                "deadline": deadline,
                "etd": "",
                "eta": "",
                "tk": "",
                "destination": "",
                "tracking": ""
            }
            self.firebase_manager.add_cargo(new_cargo)
            self.load_cargo_table()
            QMessageBox.information(self.parent, "Успех", "Груз успешно добавлен.")
            logging.info("Груз успешно добавлен.")
        except Exception as e:
            logging.error(f"Ошибка при добавлении груза: {e}")
            QMessageBox.critical(self.parent, "Ошибка", f"Не удалось добавить груз: {e}")

    def delete_cargo(self):
        try:
            selected_items = self.cargoTable.selectedItems()
            if not selected_items:
                QMessageBox.warning(self.parent, "Внимание", "Пожалуйста, выберите запись для удаления.")
                return
            row = selected_items[0].row()
            cargo_id_item = self.cargoTable.item(row, 0)
            if cargo_id_item is None:
                QMessageBox.warning(self.parent, "Ошибка", "Не удалось определить ID записи.")
                return
            cargo_id = cargo_id_item.text()
            reply = QMessageBox.question(
                self.parent,
                "Подтверждение удаления",
                f"Удалить груз с ID {cargo_id}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.firebase_manager.delete_cargo(cargo_id)
                self.load_cargo_table()
                QMessageBox.information(self.parent, "Успех", "Груз успешно удален.")
                logging.info("Груз успешно удален.")
        except Exception as e:
            logging.error(f"Ошибка при удалении груза: {e}")
            QMessageBox.critical(self.parent, "Ошибка", f"Не удалось удалить груз: {e}")