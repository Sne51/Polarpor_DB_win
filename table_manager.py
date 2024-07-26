from PyQt5.QtWidgets import QTableWidget, QHeaderView
from PyQt5.QtGui import QFont
import logging


class TableManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def adjust_font(self, table):
        font = table.font()
        base_font_size = max(12, int(self.main_window.width() // 100))
        font.setPointSize(base_font_size)
        table.setFont(font)
        logging.debug(f"Set table font size to {base_font_size}")

    def adjust_header_font(self, table):
        header_font = table.horizontalHeader().font()
        base_font_size = max(8, int(self.main_window.width() // 100))
        header_font.setPointSize(base_font_size)
        table.horizontalHeader().setFont(header_font)
        logging.debug(f"Set header font size to {base_font_size}")

    def apply_to_all_tables(self):
        tables = self.main_window.findChildren(QTableWidget)
        for table in tables:
            self.adjust_font(table)
            self.adjust_header_font(table)
            logging.debug(f"Adjusted fonts for table {table.objectName()}")

    def setup_table(self, table: QTableWidget, headers: list):
        """Настройка базовых параметров таблицы."""
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        self.adjust_font(table)
        self.adjust_header_font(table)