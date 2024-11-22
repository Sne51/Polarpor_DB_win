from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QHeaderView
import logging


class SuppliersTab:
    def __init__(self, main_window: QMainWindow, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager
        self.main_window.addSupplierButton.clicked.connect(self.add_supplier)
        self.main_window.deleteSupplierButton.clicked.connect(self.confirm_delete_supplier)
        self.setup_supplier_table()

    def setup_supplier_table(self):
        headers = ["ID", "Имя поставщика"]
        self.main_window.supplierTable.setColumnCount(len(headers))
        self.main_window.supplierTable.setHorizontalHeaderLabels(headers)
        self.main_window.supplierTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_supplier_table_data()

    def load_supplier_table_data(self):
        logging.info("Loading supplier table data")
        self.main_window.supplierTable.setRowCount(0)
        suppliers = self.firebase_manager.get_all_suppliers()
        logging.debug(f"Suppliers loaded: {suppliers}")
        
        if suppliers:
            # Проверка типа структуры данных, возвращаемой Firebase
            if isinstance(suppliers, dict):
                # Если suppliers - это словарь
                for supplier_id, supplier_data in suppliers.items():
                    if supplier_data:
                        row_position = self.main_window.supplierTable.rowCount()
                        self.main_window.supplierTable.insertRow(row_position)
                        
                        supplier_name = supplier_data.get('name', '') if isinstance(supplier_data.get('name'), str) else supplier_data.get('name', {}).get('name', '')
                        
                        self.main_window.supplierTable.setItem(row_position, 0, QTableWidgetItem(supplier_id))  # Используем ID из Firebase
                        self.main_window.supplierTable.setItem(row_position, 1, QTableWidgetItem(supplier_name))  # Имя поставщика
            elif isinstance(suppliers, list):
                # Если suppliers - это список
                for index, supplier_data in enumerate(suppliers):
                    if supplier_data:
                        row_position = self.main_window.supplierTable.rowCount()
                        self.main_window.supplierTable.insertRow(row_position)
                        
                        supplier_name = supplier_data.get('name', '') if isinstance(supplier_data.get('name'), str) else supplier_data.get('name', {}).get('name', '')
                        
                        self.main_window.supplierTable.setItem(row_position, 0, QTableWidgetItem(str(index + 1)))  # Присваиваем индекс как ID
                        self.main_window.supplierTable.setItem(row_position, 1, QTableWidgetItem(supplier_name))  # Имя поставщика
        logging.info("Supplier table data loaded")


    def add_supplier(self):
        supplier_name = self.main_window.supplierNameInput.text().strip()

        if not supplier_name:
            QMessageBox.warning(self.main_window, "Внимание", "Имя поставщика не может быть пустым")
            return

        try:
            # Проверка на дубликат по имени
            existing_suppliers = []
            for row in range(self.main_window.supplierTable.rowCount()):
                item = self.main_window.supplierTable.item(row, 1)
                if item and isinstance(item.text(), str):  # Проверка, что текст является строкой
                    existing_suppliers.append(item.text().lower())

            if supplier_name.lower() in existing_suppliers:
                QMessageBox.warning(self.main_window, "Ошибка", "Такой поставщик уже существует")
                return

            new_supplier = {'name': supplier_name}
            # Добавление поставщика в Firebase
            self.firebase_manager.add_supplier(new_supplier)
            self.load_supplier_table_data()
            QMessageBox.information(self.main_window, "Успех", f"Поставщик {supplier_name} добавлен успешно")
        except Exception as e:
            logging.error(f"Error adding supplier: {e}")
            QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при добавлении поставщика: {e}")

    def confirm_delete_supplier(self):
        selected_items = self.main_window.supplierTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main_window, "Внимание", "Пожалуйста, выберите поставщика для удаления")
            return

        row = selected_items[0].row()
        supplier_id = self.main_window.supplierTable.item(row, 0).text()  # Используем ID из Firebase
        supplier_name = self.main_window.supplierTable.item(row, 1).text()

        if not supplier_id or not supplier_name:
            QMessageBox.warning(self.main_window, "Ошибка", "Невозможно удалить поставщика. Некорректные данные.")
            return

        response = QMessageBox.question(self.main_window, "Подтверждение", f"Вы уверены, что хотите удалить поставщика {supplier_name} с ID {supplier_id}?",
                                        QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                self.firebase_manager.delete_supplier(supplier_id)
                self.load_supplier_table_data()
                QMessageBox.information(self.main_window, "Успех", "Поставщик удален успешно")
            except Exception as e:
                logging.error(f"Error deleting supplier: {e}")
                QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при удалении поставщика: {e}")
