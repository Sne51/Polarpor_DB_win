# src/tabs/cargo_tab.py
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QHeaderView
from PyQt5.QtCore import QDateTime
import logging
from src.decorators import exception_handler  # Импортируем декоратор
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QEvent


class CargoTab:
    def __init__(self, main_window, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager
        self.setup_cargo_table()

    def setup_cargo_table(self):
        # Имена столбцов
        headers = ["Заказ", "Менеджер", "Поставщик", "Покупатель", "Deadline",
                   "Пункт назн.", "ETD", "ТК", "Tracking", "ETA"]

        # Устанавливаем количество столбцов и их заголовки
        self.main_window.cargoTable.setColumnCount(len(headers))
        self.main_window.cargoTable.setHorizontalHeaderLabels(headers)

        # Настройка шрифта для заголовков
        header_font = QFont()
        header_font.setPointSize(8)  # Установите желаемый размер шрифта
        self.main_window.cargoTable.horizontalHeader().setFont(header_font)

        # Растягивание столбцов по ширине окна
        self.main_window.cargoTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Устанавливаем режим растягивания столбцов на всю ширину таблицы
        self.main_window.cargoTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def resizeEvent(self, event):
        new_size = self.cargoTable.width() // len(self.cargoTable.horizontalHeader())
        header_font = self.cargoTable.horizontalHeader().font()
        header_font.setPointSize(max(8, new_size // 15))  # Устанавливаем минимальный размер шрифта 8
        self.cargoTable.horizontalHeader().setFont(header_font)

    def load_cargo_table_data(self):
        cargos = self.firebase_manager.get_all_cargos()  # Предположим, что этот метод существует и возвращает данные по грузам
        self.main_window.cargoTable.setRowCount(0)  # Очищаем таблицу перед загрузкой новых данных

        if cargos:
            for cargo_id, cargo_data in cargos.items():
                row_position = self.main_window.cargoTable.rowCount()
                self.main_window.cargoTable.insertRow(row_position)
                self.main_window.cargoTable.setItem(row_position, 0, QTableWidgetItem(cargo_id))
     
                # Пример: Заполнение остальных колонок данными из `cargo_data`
                self.main_window.cargoTable.setItem(row_position, 1, QTableWidgetItem(cargo_data.get('manager', '')))
                self.main_window.cargoTable.setItem(row_position, 2, QTableWidgetItem(cargo_data.get('supplier', '')))
                self.main_window.cargoTable.setItem(row_position, 3, QTableWidgetItem(cargo_data.get('customer', '')))
                self.main_window.cargoTable.setItem(row_position, 4, QTableWidgetItem(cargo_data.get('deadline', '')))
                self.main_window.cargoTable.setItem(row_position, 5, QTableWidgetItem(cargo_data.get('destination', '')))
                self.main_window.cargoTable.setItem(row_position, 6, QTableWidgetItem(cargo_data.get('etd', '')))
                self.main_window.cargoTable.setItem(row_position, 7, QTableWidgetItem(cargo_data.get('tk', '')))
                self.main_window.cargoTable.setItem(row_position, 8, QTableWidgetItem(cargo_data.get('tracking', '')))
                self.main_window.cargoTable.setItem(row_position, 9, QTableWidgetItem(cargo_data.get('eta', '')))
