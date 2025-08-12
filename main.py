import sys
import json
import logging
import requests

from PyQt5.QtWidgets import (QApplication, QMainWindow, QDialog, QTableWidgetItem,
                             QMessageBox, QSplashScreen, QComboBox, QHeaderView, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QEvent
from PyQt5.QtGui import QPixmap, QScreen, QColor
from PyQt5 import uic
from config.logging_config import setup_logging
from src.firebase_manager import FirebaseManager
# from qt_material import apply_stylesheet  # Если требуется тема Material
from src.tabs.case_numbers_tab import CaseNumbersTab
from src.tabs.proforma_tab import ProformaTab
from src.tabs.clients_tab import ClientsTab
from src.tabs.cargo_tab import CargoTab    # Подключаем вкладку "Грузы"
from src.dialogs.login_dialog import LoginDialog
from src.search_functions import search_in_proforma_table, search_in_client_table, search_in_case_table
from splash_screen import SplashScreen      # Подключаем SplashScreen
from src.tabs.suppliers_tab import SuppliersTab
from src.tabs.settings_tab import SettingsTab
from pathlib import Path

# Настройка логирования
setup_logging()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Загружаем главный UI из файла main.ui (убедитесь, что путь корректный)
        APP_DIR = Path(__file__).resolve().parent
        LOGIN_UI_PATH = APP_DIR / 'ui' / 'login.ui'
        uic.loadUi(str(APP_DIR / 'ui' / 'main.ui'), self)   
        self.firebase_manager = FirebaseManager()

        self.setWindowTitle("База")

        # Инициализация виджетов, находящихся в главном окне
        self.caseNameInput = self.findChild(QComboBox, 'caseNameInput')
        self.clientInput = self.findChild(QComboBox, 'clientInput')
        self.addCaseButton = self.findChild(QPushButton, 'addCaseButton')
        self.deleteCaseButton = self.findChild(QPushButton, 'deleteCaseButton')
        self.proformaClientInput = self.findChild(QComboBox, 'proformaClientInput')
        self.proformaNameInput = self.findChild(QComboBox, 'proformaNameInput')
        self.addProformaButton = self.findChild(QPushButton, 'addProformaButton')
        self.deleteProformaButton = self.findChild(QPushButton, 'deleteProformaButton')
        self.clientNameInput = self.findChild(QLineEdit, 'clientNameInput')
        self.addClientButton = self.findChild(QPushButton, 'addClientButton')
        self.deleteClientButton = self.findChild(QPushButton, 'deleteClientButton')
        self.searchButton = self.findChild(QPushButton, 'searchButton')
        self.searchInput = self.findChild(QLineEdit, 'searchInput')
        self.searchComboBox = self.findChild(QComboBox, 'searchComboBox')
        
        # Если требуется, можно сделать выпадающие списки редактируемыми
        self.caseNameInput.setEditable(True)
        self.clientInput.setEditable(True)
        self.caseNameInput.lineEdit().textEdited.connect(self.filter_case_names)
        self.clientInput.lineEdit().textEdited.connect(self.filter_client_names)

        self.searchButton.clicked.connect(self.search_items)
        self.searchInput.returnPressed.connect(self.search_items)
        self.searchComboBox.addItems(["Case", "Proforma", "Client"])

        # Масштабирование окна (например, 60% от доступного экрана)
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.6), int(screen.height() * 0.6))

        # Увеличение шрифта для всех виджетов
        font = self.font()
        font.setPointSize(12)
        self.setFont(font)

        # Установка фильтра событий (например, для обработки изменения размера окна)
        self.installEventFilter(self)

        # Инициализация всех вкладок.
        # При инициализации классов вкладок мы передаём ссылку на главное окно,
        # поэтому в каждой вкладке можно обратиться к нужным виджетам через main_window.
        self.case_numbers_tab = CaseNumbersTab(self, self.firebase_manager)
        self.proforma_tab = ProformaTab(self, self.firebase_manager)
        self.clients_tab = ClientsTab(self, self.firebase_manager)
        self.cargo_tab = CargoTab(self, self.firebase_manager)
        self.suppliers_tab = SuppliersTab(self, self.firebase_manager)
        self.settings_tab = SettingsTab(self, self.firebase_manager)

        # Автообновление комбобоксов "Проформ" при переключении вкладок
        for tw in self.findChildren(QTabWidget):
            if self.proforma_tab.proformaTable and tw.isAncestorOf(self.proforma_tab.proformaTable):
                tw.currentChanged.connect(self.on_tab_changed)
                break

        # Если в вашем main.ui уже есть QTabWidget для настроек (objectName "settingsTab"), добавляем вкладку настроек
        self.settingsTabWidget = self.findChild(QTabWidget, "settingsTab")
        if self.settingsTabWidget:
            self.settingsTabWidget.addTab(self.settings_tab, "Настройки")
        else:
            logging.error("QTabWidget с objectName 'settingsTab' не найден в main.ui.")

        # Пример: можно вызвать метод загрузки данных для вкладки "Грузы"
        self.cargo_tab.load_cargo_table()

    def search_items(self):
        search_text = self.searchInput.text().strip().lower()
        search_type = self.searchComboBox.currentText()
        if search_type == "Case":
            search_in_case_table(self.case_numbers_tab.main_window.caseTable, self.firebase_manager, search_text, self)
        elif search_type == "Proforma":
            search_in_proforma_table(self.proforma_tab.proformaTable, self.firebase_manager, search_text, self)
        elif search_type == "Client":
            search_in_client_table(self.clients_tab.clientTable, self.firebase_manager, search_text, self)
        else:
            QMessageBox.warning(self, "Поиск", f"Неизвестная вкладка: {search_type}")
            logging.error(f"User selected unknown search tab: {search_type}")

    def eventFilter(self, source, event):
        if event.type() == QEvent.Resize and source is self:
            self.resize_tables()
        return super(MainWindow, self).eventFilter(source, event)

    def resize_tables(self):
        # Обратите внимание: теперь используем виджеты, найденные через findChild через main_window,
        # поскольку в некоторых вкладках (например, CaseNumbersTab) таблица хранится в главном окне.
        self.findChild(QTableWidget, "caseTable").horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.proforma_tab.proformaTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clients_tab.clientTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cargo_tab.cargoTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.suppliers_tab.supplierTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def on_tab_changed(self, _idx):
        # Когда вкладка с таблицей проформ стала видимой — обновляем выпадающие списки
        try:
            if self.proforma_tab.proformaTable and self.proforma_tab.proformaTable.isVisible():
                self.proforma_tab.load_case_numbers_for_proforma()
                self.proforma_tab.load_managers_into_combobox()
        except Exception as e:
            logging.error(f"on_tab_changed error: {e}")

    def filter_case_names(self, text):
        self.caseNameInput.clear()
        cases = self.firebase_manager.get_all_cases()
        if cases:
            unique_names = set()
            for case_id, case_data in cases.items():
                name = case_data.get('name', '')
                if isinstance(name, str) and text.lower() in name.lower():
                    unique_names.add(name)
            self.caseNameInput.addItems(sorted(unique_names))
            self.caseNameInput.setCurrentText(text)
        self.caseNameInput.repaint()

    def filter_client_names(self, text):
        self.clientInput.clear()
        clients = self.firebase_manager.get_all_clients()
        if clients:
            unique_names = set()
            for client_id, client_data in clients.items():
                name = client_data.get('name', '')
                if isinstance(name, str) and text.lower() in name.lower():
                    unique_names.add(name)
            self.clientInput.addItems(sorted(unique_names))
            self.clientInput.setCurrentText(text)
        self.clientInput.repaint()


if __name__ == "__main__":
    APP_DIR = Path(__file__).resolve().parent
    LOGIN_UI_PATH = APP_DIR / 'ui' / 'login.ui'
    if not LOGIN_UI_PATH.exists():
        logging.error(f"Файл UI не найден: {LOGIN_UI_PATH}")

    app = QApplication(sys.argv)
    # Применить тему Material при необходимости:
    # from qt_material import apply_stylesheet
    # apply_stylesheet(app, theme='dark_teal.xml')

    login_dialog = LoginDialog(ui_file=str(LOGIN_UI_PATH))
    if login_dialog.exec_() == QDialog.Accepted:
        splash = SplashScreen(app)
        splash.show()
        splash.update_message("Инициализация...", app)
        QTimer.singleShot(1000, lambda: splash.update_message("Загрузка данных...", app))
        QTimer.singleShot(2000, lambda: splash.update_message("Подготовка интерфейса...", app))

        main_window = MainWindow()

        splash.update_message("Загрузка данных о клиентах...", app)
        main_window.clients_tab.load_client_table_data()
        splash.update_message("Загрузка данных о проформах...", app)
        main_window.proforma_tab.load_proforma_table_data()
        splash.update_message("Загрузка уникальных имен...", app)
        main_window.case_numbers_tab.load_unique_names()
        splash.update_message("Загрузка данных о делах...", app)
        main_window.case_numbers_tab.load_case_table_data()

        QTimer.singleShot(3000, splash.close)
        main_window.show()
        splash.finish(main_window)
        sys.exit(app.exec_())