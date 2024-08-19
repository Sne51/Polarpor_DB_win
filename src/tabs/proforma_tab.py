from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QHeaderView
from PyQt5.QtCore import QDateTime
import logging
from src.decorators import exception_handler  # Обновляем путь для импорта

class ProformaTab:
    def __init__(self, main_window: QMainWindow, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager
        self.main_window.addProformaButton.clicked.connect(self.add_new_proforma)
        self.main_window.deleteProformaButton.clicked.connect(self.confirm_delete_proforma)
        self.setup_proforma_table()
        self.load_proforma_table_data()
        self.load_proforma_case_numbers()

    @exception_handler
    def setup_proforma_table(self):
        headers = ["Номер дела", "Проформа", "Имя", "Клиент", "Комментарий", "Дата создания"]
        self.main_window.proformaTable.setColumnCount(len(headers))
        self.main_window.proformaTable.setHorizontalHeaderLabels(headers)
        self.main_window.proformaTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    @exception_handler
    def load_proforma_table_data(self):
        logging.info("Loading proforma table data")
        self.main_window.proformaTable.setRowCount(0)
        proformas = self.firebase_manager.get_all_proformas()
        logging.debug(f"Proformas loaded: {proformas}")
        if proformas:
            for proforma_id, proforma_data in proformas.items():
                row_position = self.main_window.proformaTable.rowCount()
                self.main_window.proformaTable.insertRow(row_position)
                self.main_window.proformaTable.setItem(row_position, 0, QTableWidgetItem(proforma_data.get('case_number', '')))
                self.main_window.proformaTable.setItem(row_position, 1, QTableWidgetItem(proforma_id))
                self.main_window.proformaTable.setItem(row_position, 2, QTableWidgetItem(proforma_data.get('name', '')))
                self.main_window.proformaTable.setItem(row_position, 3, QTableWidgetItem(proforma_data.get('client', '')))
                self.main_window.proformaTable.setItem(row_position, 4, QTableWidgetItem(proforma_data.get('comment', '')))
                self.main_window.proformaTable.setItem(row_position, 5, QTableWidgetItem(proforma_data.get('date_created', '')))

        # Load data into combo boxes
        self.main_window.proformaNameInput.clear()

        unique_proforma_names = set()

        for proforma_id, proforma_data in proformas.items():
            unique_proforma_names.add(proforma_data.get('name', ''))

        self.main_window.proformaNameInput.addItems(sorted(unique_proforma_names))
        logging.info("Proforma table data loaded")

    @exception_handler
    def load_proforma_case_numbers(self):
        logging.info("Loading case numbers for proforma tab")
        self.main_window.proformaClientInput.clear()
        cases = self.firebase_manager.get_all_cases()
        if cases:
            case_numbers = [case_id for case_id in cases]
            self.main_window.proformaClientInput.addItems(case_numbers)
        logging.info("Case numbers for proforma tab loaded")

    @exception_handler
    def add_new_proforma(self, event=None):
        name = self.main_window.proformaNameInput.currentText().strip()
        case_number = self.main_window.proformaClientInput.currentText().strip()
        comment = self.main_window.proformaCommentInput.text().strip()
        date_created = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

        if not name or not case_number:
            QMessageBox.warning(self.main_window, "Внимание", "Имя проформы и номер дела не могут быть пустыми")
            return

        try:
            new_proforma = {
                'name': name,
                'case_number': case_number,
                'comment': comment,
                'date_created': date_created
            }
            proforma_id = self.firebase_manager.add_proforma(new_proforma)
            self.load_proforma_table_data()
            self.load_proforma_case_numbers()  # Reload case numbers to include any new entries
            QMessageBox.information(self.main_window, "Успех", f"Проформа добавлена успешно с ID: {proforma_id}")
        except Exception as e:
            logging.error(f"Error adding new proforma: {e}")
            QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при добавлении проформы: {e}")

    @exception_handler
    def confirm_delete_proforma(self, event=None):
        selected_items = self.main_window.proformaTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main_window, "Внимание", "Пожалуйста, выберите проформу для удаления")
            return

        row = selected_items[0].row()
        proforma_id = self.main_window.proformaTable.item(row, 1).text()
        response = QMessageBox.question(self.main_window, "Подтверждение", f"Вы уверены, что хотите удалить проформу с ID {proforma_id}?",
                                        QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                self.firebase_manager.delete_proforma(proforma_id)
                self.load_proforma_table_data()
                self.load_proforma_case_numbers()  # Reload case numbers to ensure consistency
                QMessageBox.information(self.main_window, "Успех", "Проформа удалена успешно")
            except Exception as e:
                logging.error(f"Error deleting proforma: {e}")
                QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при удалении проформы: {e}")
