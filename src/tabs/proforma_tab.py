import logging
import json
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QHeaderView, QTableWidget
from PyQt5.QtCore import QDateTime
from src.decorators import exception_handler

class ProformaTab:
    def __init__(self, main_window, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager
        
        # Добавляем атрибут proformaTable из главного окна.
        self.proformaTable = self.main_window.findChild(QTableWidget, "proformaTable")
        if self.proformaTable is None:
            logging.error("Не найден виджет QTableWidget с objectName 'proformaTable'")
            QMessageBox.critical(self.main_window, "Ошибка", "Не найден виджет таблицы проформ")
            return

        # Подключаем кнопки, если они есть (пример)
        self.main_window.addProformaButton.clicked.connect(self.add_new_proforma)
        self.main_window.deleteProformaButton.clicked.connect(self.confirm_delete_proforma)

        self.setup_proforma_table()
        self.load_proforma_table_data()
        self.load_proforma_case_numbers()
        self.load_managers_into_combobox()

    @exception_handler
    def setup_proforma_table(self):
        headers = ["Номер дела", "ID проформы", "Менеджер", "Клиент", "Комментарий", "Дата создания"]
        self.proformaTable.setColumnCount(len(headers))
        self.proformaTable.setHorizontalHeaderLabels(headers)
        self.proformaTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    @exception_handler
    def load_proforma_table_data(self):
        logging.info("Loading proforma table data")
        self.proformaTable.setRowCount(0)
        proformas = self.firebase_manager.get_all_proformas()
        logging.debug(f"Proformas loaded: {proformas}")
        if proformas:
            for proforma_id, proforma_data in proformas.items():
                row_position = self.proformaTable.rowCount()
                self.proformaTable.insertRow(row_position)
                self.proformaTable.setItem(row_position, 0, QTableWidgetItem(proforma_data.get('case_number', '')))
                self.proformaTable.setItem(row_position, 1, QTableWidgetItem(proforma_id))
                self.proformaTable.setItem(row_position, 2, QTableWidgetItem(proforma_data.get('name', '')))
                self.proformaTable.setItem(row_position, 3, QTableWidgetItem(proforma_data.get('client', '')))
                self.proformaTable.setItem(row_position, 4, QTableWidgetItem(proforma_data.get('comment', '')))
                self.proformaTable.setItem(row_position, 5, QTableWidgetItem(proforma_data.get('date_created', '')))
        logging.info("Proforma table data loaded")

    @exception_handler
    def load_proforma_case_numbers(self):
        logging.info("Loading case numbers for proforma tab")
        self.main_window.proformaClientInput.clear()
        cases = self.firebase_manager.get_all_cases()
        if cases:
            # Извлекаем номера дел только из записей-словарей
            case_numbers = [case_id for case_id, data in cases.items() if isinstance(data, dict)]
            self.main_window.proformaClientInput.addItems(case_numbers)
        logging.info("Case numbers for proforma tab loaded")

    @exception_handler
    def load_managers_into_combobox(self):
        """Загружает список менеджеров в выпадающий список для проформ.
        Список менеджеров загружается из локального файла managers.json.
        """
        logging.info("Loading managers into combobox for proforma tab")
        self.main_window.proformaNameInput.clear()
        try:
            with open("managers.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            managers = [manager["name"] for manager in data.get("managers", []) if "name" in manager]
            logging.debug(f"Managers loaded: {managers}")
            self.main_window.proformaNameInput.addItems(managers)
            logging.info("Managers loaded into combobox successfully")
        except Exception as e:
            logging.error(f"Error loading managers into combobox: {e}")
            QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка загрузки менеджеров: {e}")

    @exception_handler
    def add_new_proforma(self, event=None):
        name = self.main_window.proformaNameInput.currentText().strip()
        case_number = self.main_window.proformaClientInput.currentText().strip()
        comment = self.main_window.proformaCommentInput.text().strip()
        date_created = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

        if not name or not case_number:
            QMessageBox.warning(self.main_window, "Внимание",
                                "Имя проформы и номер дела не могут быть пустыми")
            return

        new_proforma = {
            'name': name,
            'case_number': case_number,
            'comment': comment,
            'date_created': date_created
        }
        try:
            proforma_id = self.firebase_manager.add_proforma(new_proforma)
            self.load_proforma_table_data()
            self.load_proforma_case_numbers()
            self.load_managers_into_combobox()  # Обновляем список менеджеров
            QMessageBox.information(self.main_window, "Успех",
                                    f"Проформа добавлена успешно с ID: {proforma_id}")
        except Exception as e:
            logging.error(f"Error adding new proforma: {e}")
            QMessageBox.critical(self.main_window, "Ошибка",
                                 f"Ошибка при добавлении проформы: {e}")

    @exception_handler
    def confirm_delete_proforma(self, event=None):
        selected_items = self.proformaTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main_window, "Внимание",
                                "Пожалуйста, выберите проформу для удаления")
            return

        row = selected_items[0].row()
        proforma_id_item = self.proformaTable.item(row, 1)
        if not proforma_id_item:
            QMessageBox.warning(self.main_window, "Ошибка",
                                "Не удалось определить ID проформы.")
            return

        proforma_id = proforma_id_item.text()
        response = QMessageBox.question(
            self.main_window,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить проформу с ID {proforma_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if response == QMessageBox.Yes:
            try:
                self.firebase_manager.delete_proforma(proforma_id)
                self.load_proforma_table_data()
                self.load_proforma_case_numbers()
                QMessageBox.information(self.main_window, "Успех",
                                        "Проформа удалена успешно")
            except Exception as e:
                logging.error(f"Error deleting proforma: {e}")
                QMessageBox.critical(self.main_window, "Ошибка",
                                     f"Ошибка при удалении проформы: {e}")