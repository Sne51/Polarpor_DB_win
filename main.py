import sys
import json
import logging
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QTableWidgetItem, QMessageBox, QSplashScreen, QComboBox, QHeaderView, QLabel, QLineEdit, QPushButton, QTableWidget
from PyQt5.QtCore import Qt, QTimer, QDateTime, QEvent
from PyQt5.QtGui import QPixmap, QScreen, QColor
from PyQt5 import uic
from config.logging_config import setup_logging
from src.firebase_manager import FirebaseManager
from qt_material import apply_stylesheet
from src.tabs.case_numbers_tab import CaseNumbersTab
from src.tabs.proforma_tab import ProformaTab
from src.tabs.clients_tab import ClientsTab
from src.dialogs.login_dialog import LoginDialog
from src.search_functions import search_in_proforma_table, search_in_client_table

# Настройка логирования
setup_logging()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/main.ui', self)
        self.firebase_manager = FirebaseManager()

        self.setWindowTitle("База")

        # Делает выпадающие списки редактируемыми, что позволяет вводить новые значения
        self.caseNameInput.setEditable(True)
        self.clientInput.setEditable(True)

        self.caseNameInput.lineEdit().textEdited.connect(self.filter_case_names)
        self.clientInput.lineEdit().textEdited.connect(self.filter_client_names)

        # Инициализация виджетов
        self.caseNameInput = self.findChild(QComboBox, 'caseNameInput')
        self.clientInput = self.findChild(QComboBox, 'clientInput')
        self.addCaseButton = self.findChild(QPushButton, 'addCaseButton')
        self.deleteCaseButton = self.findChild(QPushButton, 'deleteCaseButton')
        self.proformaClientInput = self.findChild(QComboBox, 'proformaClientInput')
        self.proformaNameInput = self.findChild(QComboBox, 'proformaNameInput')
        self.addProformaButton = self.findChild(QPushButton, 'addProformaButton')
        self.deleteProformaButton = self.findChild(QPushButton, 'deleteProformaButton')
        self.clientTable = self.findChild(QTableWidget, 'clientTable')
        self.clientNameInput = self.findChild(QLineEdit, 'clientNameInput')
        self.addClientButton = self.findChild(QPushButton, 'addClientButton')
        self.deleteClientButton = self.findChild(QPushButton, 'deleteClientButton')

        # Подключение кнопки поиска к методу search_items
        self.searchButton.clicked.connect(self.search_items)

        # Заполнение выпадающего списка
        self.searchComboBox.addItems(["Case", "Proforma", "Client"])

        # Масштабирование окна в зависимости от разрешения экрана
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.6), int(screen.height() * 0.6))

        # Увеличение шрифта всех виджетов
        font = self.font()
        font.setPointSize(12)  # Здесь можно настроить нужный размер шрифта
        self.setFont(font)

        # Установка фильтра событий для отслеживания изменения размера окна
        self.installEventFilter(self)

        # Инициализация вкладки номеров дел
        self.case_numbers_tab = CaseNumbersTab(self, self.firebase_manager)
        # Инициализация вкладки номеров проформ
        self.proforma_tab = ProformaTab(self, self.firebase_manager)
        # Инициализация вкладки клиентов
        self.clients_tab = ClientsTab(self, self.firebase_manager)

    def search_items(self):
        search_text = self.searchInput.text().strip().lower()
        search_type = self.searchComboBox.currentText()
        if search_type == "Case":
            search_in_case_table(self.caseTable, self.firebase_manager, search_text)
        elif search_type == "Proforma":
            search_in_proforma_table(self.proformaTable, self.firebase_manager, search_text)
        elif search_type == "Client":
            search_in_client_table(self.clientTable, self.firebase_manager, search_text)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Resize and source is self:
            self.resize_tables()
        return super(MainWindow, self).eventFilter(source, event)

    def resize_tables(self):
        self.caseTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.proformaTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clientTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def filter_case_names(self, text):
        self.case_numbers_tab.filter_case_names(text)

    def filter_client_names(self, text):
        self.clientInput.clear()
        clients = self.firebase_manager.get_all_clients()
        logging.debug(f"Clients from Firebase: {clients}")
        if clients:
            unique_names = set()
            if isinstance(clients, dict):
                for client_id, client_data in clients.items():
                    name = client_data.get('name', '') if isinstance(client_data, dict) else client_data
                    logging.debug(f"Client ID: {client_id}, Name: {name}")
                    if text.lower() in name.lower():
                        unique_names.add(name)
            elif isinstance(clients, list):
                for client_data in clients:
                    if client_data:
                        name = client_data.get('name', '')
                        logging.debug(f"Client Name: {name}")
                        if text.lower() in name.lower():
                            unique_names.add(name)
            
            # Ограничиваем отображение первых 5 уникальных имен
            limited_names = sorted(unique_names)[:5]
            logging.debug(f"Limited client names: {limited_names}")
            self.clientInput.addItems(limited_names)

        # Восстанавливаем введенный текст в поле ввода
        self.clientInput.setCurrentText(text)
        logging.debug(f"Current text in client input: {text}")

        # Принудительное обновление интерфейса
        self.clientInput.repaint()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Применение темы Material
    apply_stylesheet(app, theme='dark_teal.xml')

    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        # Определяем путь к splash screen в зависимости от операционной системы
        if sys.platform == "win32":
            splash_pix = QPixmap('C:/Users/Usr/Documents/Polarpor_DB_win/Polarpor_DB_win/media/splash_screen_1.png')
        else:
            splash_pix = QPixmap('/Users/sk/Documents/EDU_Python/PPT_do_quick/media/splash_screen_1.png')

        screen = app.primaryScreen().availableGeometry()
        splash_size = int(min(screen.width(), screen.height()) * 0.5)
        splash_pix = splash_pix.scaled(splash_size, splash_size, Qt.KeepAspectRatio)  # Адаптируем размер Splash Screen
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        splash.show()

        # Центрирование Splash Screen
        center_point = screen.center()
        splash.move(center_point.x() - splash.width() // 2, center_point.y() - splash.height() // 2)

        def update_splash_message(message):
            font = splash.font()
            if sys.platform == "win32":
                font.setPointSize(splash_size // 40)  # Уменьшено значение для Windows
            else:
                font.setPointSize(splash_size // 30)  # Оригинальное значение для macOS
            splash.setFont(font)
            splash.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, QColor(Qt.white))
            app.processEvents()  # Ensure the message is shown immediately

        # Примеры обновления сообщений на splash screen
        update_splash_message("Инициализация...")
        logging.info("Инициализация...")
        QTimer.singleShot(1000, lambda: update_splash_message("Загрузка данных..."))
        logging.info("Загрузка данных...")
        QTimer.singleShot(2000, lambda: update_splash_message("Подготовка интерфейса..."))
        logging.info("Подготовка интерфейса...")

        main_window = MainWindow()

        # Примеры обновления сообщений во время загрузки данных
        update_splash_message("Загрузка данных о клиентах...")
        main_window.clients_tab.load_client_table_data()
        update_splash_message("Загрузка данных о проформах...")
        main_window.proforma_tab.load_proforma_table_data()
        update_splash_message("Загрузка уникальных имен...")
        main_window.case_numbers_tab.load_unique_names()
        update_splash_message("Загрузка данных о делах...")
        main_window.case_numbers_tab.load_case_table_data()

        QTimer.singleShot(3000, splash.close)

        main_window.show()
        splash.finish(main_window)
        sys.exit(app.exec_())
