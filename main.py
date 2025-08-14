# /Users/sk/Documents/EDU_Python/Polarpor_DB_win/main.py
import sys
import logging
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QComboBox, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget
)

from config.logging_config import setup_logging
from src.firebase_manager import FirebaseManager

# Таб-классы
from src.tabs.case_numbers_tab import CaseNumbersTab
from src.tabs.proforma_tab import ProformaTab
from src.tabs.clients_tab import ClientsTab
from src.tabs.cargo_tab import CargoTab
from src.tabs.suppliers_tab import SuppliersTab
from src.tabs.settings_tab import SettingsTab

from src.dialogs.login_dialog import LoginDialog
from src.search_functions import (
    search_in_proforma_table, search_in_client_table, search_in_case_table
)
from splash_screen import SplashScreen


# ---------- Логирование ----------
setup_logging()


class MainWindow(QMainWindow):
    """
    Главное окно:
    - Загружает main.ui
    - Инициализирует вкладки
    - Делает вкладки «ленивыми» (activate/deactivate)
    - Реализует поиск и resize таблиц
    """

    def __init__(self):
        super().__init__()

        app_dir = Path(__file__).resolve().parent
        ui_main = app_dir / 'ui' / 'main.ui'
        if not ui_main.exists():
            logging.error(f"UI main.ui не найден: {ui_main}")
        uic.loadUi(str(ui_main), self)

        self.setWindowTitle("База")

        # --- Firebase ---
        self.firebase_manager = FirebaseManager()

        # --- Виджеты, к-рые используем напрямую во вкладках ---
        # Case
        self.caseNameInput: QComboBox = self.findChild(QComboBox, 'caseNameInput')
        self.clientInput: QComboBox = self.findChild(QComboBox, 'clientInput')
        self.addCaseButton: QPushButton = self.findChild(QPushButton, 'addCaseButton')
        self.deleteCaseButton: QPushButton = self.findChild(QPushButton, 'deleteCaseButton')
        self.caseTable: QTableWidget = self.findChild(QTableWidget, 'caseTable')

        # Proforma
        self.proformaClientInput: QComboBox = self.findChild(QComboBox, 'proformaClientInput')
        self.proformaNameInput: QComboBox = self.findChild(QComboBox, 'proformaNameInput')
        self.addProformaButton: QPushButton = self.findChild(QPushButton, 'addProformaButton')
        self.deleteProformaButton: QPushButton = self.findChild(QPushButton, 'deleteProformaButton')
        self.proformaCommentInput: QLineEdit = self.findChild(QLineEdit, 'proformaCommentInput')
        self.proformaTable: QTableWidget = self.findChild(QTableWidget, 'proformaTable')

        # Clients
        self.clientNameInput: QLineEdit = self.findChild(QLineEdit, 'clientNameInput')
        self.addClientButton: QPushButton = self.findChild(QPushButton, 'addClientButton')
        self.deleteClientButton: QPushButton = self.findChild(QPushButton, 'deleteClientButton')
        self.clientTable: QTableWidget = self.findChild(QTableWidget, 'clientTable')

        # Cargo
        self.cargoTable: QTableWidget = self.findChild(QTableWidget, 'cargoTable')

        # Suppliers
        self.supplierTable: QTableWidget = self.findChild(QTableWidget, 'supplierTable')
        self.addSupplierButton: QPushButton = self.findChild(QPushButton, 'addSupplierButton')
        self.deleteSupplierButton: QPushButton = self.findChild(QPushButton, 'deleteSupplierButton')
        self.supplierNameInput: QLineEdit = self.findChild(QLineEdit, 'supplierNameInput')  

        # Search
        self.searchButton: QPushButton = self.findChild(QPushButton, 'searchButton')
        self.searchInput: QLineEdit = self.findChild(QLineEdit, 'searchInput')
        self.searchComboBox: QComboBox = self.findChild(QComboBox, 'searchComboBox')
        if self.searchComboBox and self.searchComboBox.count() == 0:
            self.searchComboBox.addItems(["Case", "Proforma", "Client"])

        # Шрифты/размер окна
        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen_geo.width() * 0.6), int(screen_geo.height() * 0.6))
        f = self.font(); f.setPointSize(12); self.setFont(f)

        # Редактируемые выпадающие списки + фильтрация
        if self.caseNameInput:
            self.caseNameInput.setEditable(True)
            self.caseNameInput.lineEdit().textEdited.connect(self.filter_case_names)
        if self.clientInput:
            self.clientInput.setEditable(True)
            self.clientInput.lineEdit().textEdited.connect(self.filter_client_names)

        # Поиск
        if self.searchButton:
            self.searchButton.clicked.connect(self.search_items)
        if self.searchInput:
            self.searchInput.returnPressed.connect(self.search_items)

        # Resize-хуки
        self.installEventFilter(self)

        # --- Вкладки (классы) ---
        self.case_numbers_tab = CaseNumbersTab(self, self.firebase_manager)
        self.proforma_tab     = ProformaTab(self, self.firebase_manager)
        self.clients_tab      = ClientsTab(self, self.firebase_manager)
        self.cargo_tab        = CargoTab(self, self.firebase_manager)
        self.suppliers_tab    = SuppliersTab(self, self.firebase_manager)
        self.settings_tab     = SettingsTab(self, self.firebase_manager)

        # Если в main.ui есть общий QTabWidget с objectName "settingsTab" — используем его
        self.settingsTabWidget: QTabWidget = self.findChild(QTabWidget, "settingsTab")
        if not self.settingsTabWidget:
            logging.error("QTabWidget 'settingsTab' не найден. Проверь objectName в main.ui.")
        else:
            # Добавим вкладку «Настройки», если она отдельным виджетом
            try:
                self.settingsTabWidget.addTab(self.settings_tab, "Настройки")
            except Exception:
                pass

            # Подписка на смену вкладок -> activate/deactivate
            self.settingsTabWidget.currentChanged.connect(self._on_tabs_changed)

            # Активируем текущую вкладку при старте
            QTimer.singleShot(0, lambda: self._on_tabs_changed(self.settingsTabWidget.currentIndex()))

        # Первичное наполнение (лёгкое) некоторых таблиц
        try:
            self.suppliers_tab.load_supplier_table_data()
        except Exception as e:
            logging.warning(f"Первичная загрузка suppliers: {e}")

        # Первичное наполнение выпадающих списков (чтобы не были пустыми на старте)
        try:
            # Вкладка «Номера дел»
            self.case_numbers_tab.load_unique_names()
            self.case_numbers_tab.load_clients_into_combobox()
        except Exception as e:
            logging.warning(f"Первичная подгрузка комбобоксов Case: {e}")

        try:
            # Вкладка «Проформы»
            self.proforma_tab.load_case_numbers_for_proforma()
            self.proforma_tab.load_managers_into_combobox()
        except Exception as e:
            logging.warning(f"Первичная подгрузка комбобоксов Proforma: {e}")

    # ---------- Поиск ----------
    def search_items(self):
        text = (self.searchInput.text() if self.searchInput else "").strip().lower()
        tab = self.searchComboBox.currentText() if self.searchComboBox else "Case"

        if tab == "Case":
            search_in_case_table(self.case_numbers_tab.main_window.caseTable, self.firebase_manager, text, self)
        elif tab == "Proforma":
            search_in_proforma_table(self.proforma_tab.proformaTable, self.firebase_manager, text, self)
        elif tab == "Client":
            search_in_client_table(self.clients_tab.clientTable, self.firebase_manager, text, self)
        else:
            QMessageBox.warning(self, "Поиск", f"Неизвестная вкладка: {tab}")
            logging.error(f"Unknown search tab: {tab}")

    # ---------- Смена вкладок (ленивая активация) ----------
    def _on_tabs_changed(self, idx: int):
            if not self.settingsTabWidget:
                return

            w = self.settingsTabWidget.widget(idx)
            obj = w.objectName() if w else ""
            logging.debug(f"_on_tabs_changed: idx={idx}, objectName={obj}")

            # Снимаем активность со всех вкладок
            for tab in (self.proforma_tab, self.case_numbers_tab, self.clients_tab, self.cargo_tab, self.suppliers_tab):
                try:
                    tab.deactivate()
                except Exception:
                    pass

            # 1) Пытаемся по ожидаемым objectName
            try:
                if obj in ("tab", "TabCases", "casesTab"):
                    self.case_numbers_tab.activate(); return
                if obj in ("tab_2", "proformaTab"):
                    self.proforma_tab.activate(); return
                if obj in ("tab_3", "clientsTab"):
                    self.clients_tab.activate(); return
                if obj in ("cargoTab",):
                    self.cargo_tab.activate(); return
                if obj in ("suppliersTab",):
                    self.suppliers_tab.activate(); return
                if obj in ("settingsTabPage",):
                    return  # настройки
            except Exception as e:
                logging.error(f"_on_tabs_changed (by name) error: {e}")

            # 2) Фолбэк: распознаём вкладку по наличию виджетов внутри страницы
            try:
                if w:
                    if w.findChild(QTableWidget, "supplierTable"):
                        self.suppliers_tab.activate(); return
                    if w.findChild(QTableWidget, "cargoTable"):
                        self.cargo_tab.activate(); return
                    if w.findChild(QTableWidget, "clientTable"):
                        self.clients_tab.activate(); return
                    if w.findChild(QTableWidget, "proformaTable"):
                        self.proforma_tab.activate(); return
                    if w.findChild(QTableWidget, "caseTable"):
                        self.case_numbers_tab.activate(); return
            except Exception as e:
                logging.error(f"_on_tabs_changed (by content) error: {e}")

            # 3) Совсем на всякий случай — включим проформу
            try:
                self.proforma_tab.activate()
            except Exception:
                pass

    # ---------- Resize ----------
    def eventFilter(self, source, event):
        if event.type() == QEvent.Resize and source is self:
            self.resize_tables()
        return super().eventFilter(source, event)

    def resize_tables(self):
        try:
            if self.caseTable:
                self.caseTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            if self.proformaTable:
                self.proformaTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            if self.clientTable:
                self.clientTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            if self.cargoTable:
                self.cargoTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            if self.supplierTable:
                self.supplierTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            logging.debug(f"resize_tables: {e}")

    # ---------- Фильтры выпадающих списков ----------
    def filter_case_names(self, text: str):
        if not self.caseNameInput:
            return
        self.caseNameInput.clear()
        cases = self.firebase_manager.get_all_cases()
        if cases:
            uniq = set()
            for _, c in cases.items():
                name = (c.get("manager") or c.get("name") or "").strip() if isinstance(c, dict) else ""
                if text.lower() in name.lower():
                    uniq.add(name)
            self.caseNameInput.addItems(sorted(uniq))
            self.caseNameInput.setCurrentText(text)
        self.caseNameInput.repaint()

    def filter_client_names(self, text: str):
        if not self.clientInput:
            return
        self.clientInput.clear()
        clients = self.firebase_manager.get_all_clients()
        if clients:
            uniq = set()
            for _, c in clients.items():
                name = (c.get("name") or "").strip() if isinstance(c, dict) else str(c)
                if text.lower() in name.lower():
                    uniq.add(name)
            self.clientInput.addItems(sorted(uniq))
            self.clientInput.setCurrentText(text)
        self.clientInput.repaint()


def run_app():
    app_dir = Path(__file__).resolve().parent
    login_ui = app_dir / 'ui' / 'login.ui'
    if not login_ui.exists():
        logging.error(f"Файл UI не найден: {login_ui}")

    app = QApplication(sys.argv)

    # Логин
    login_dialog = LoginDialog(ui_file=str(login_ui))
    if login_dialog.exec_() != QDialog.Accepted:
        sys.exit(0)

    # Splash
    splash = SplashScreen(app)
    splash.show()
    splash.update_message("Инициализация...", app)
    QTimer.singleShot(600, lambda: splash.update_message("Загрузка данных...", app))
    QTimer.singleShot(1200, lambda: splash.update_message("Подготовка интерфейса...", app))

    # Главное окно
    mw = MainWindow()

    # Лёгкая первичная подгрузка (чтобы не было пусто на старте)
    try:
        splash.update_message("Загрузка клиентов...", app)
        mw.clients_tab.load_client_table_data()
        splash.update_message("Загрузка проформ...", app)
        mw.proforma_tab.load_proforma_table_data()
        splash.update_message("Загрузка дел...", app)
        mw.case_numbers_tab.load_case_table_data()
        splash.update_message("Загрузка поставщиков...", app)
        mw.suppliers_tab.load_supplier_table_data()
        splash.update_message("Подготовка списков дел...", app)
        mw.case_numbers_tab.load_unique_names()
        mw.case_numbers_tab.load_clients_into_combobox()

        splash.update_message("Подготовка списков проформ...", app)
        mw.proforma_tab.load_case_numbers_for_proforma()
        mw.proforma_tab.load_managers_into_combobox()

    except Exception as e:
        logging.warning(f"Первичная подгрузка: {e}")

    QTimer.singleShot(1800, splash.close)
    mw.show()
    splash.finish(mw)
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()