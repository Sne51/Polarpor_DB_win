import sys
import json
import logging
from PyQt5.QtWidgets import QApplication, QDialog, QSplashScreen, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QDateTime, QEvent
from PyQt5.QtGui import QPixmap, QColor
from qt_material import apply_stylesheet
from login import LoginDialog
from main_window import MainWindow  # Импортируем MainWindow
from apply_styles import apply_app_style  # Импортируем apply_app_style

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Применение темы Material
    apply_stylesheet(app, theme='dark_lightgreen.xml')

    apply_app_style(app)

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
            app.processEvents()  # Обеспечивает немедленное отображение сообщения

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
        main_window.load_client_table_data()
        update_splash_message("Загрузка данных о проформах...")
        main_window.load_proforma_table_data()
        update_splash_message("Загрузка уникальных имен...")
        main_window.load_unique_names()
        update_splash_message("Загрузка данных о делах...")
        main_window.load_case_table_data()

        QTimer.singleShot(3000, splash.close)

        main_window.show()
        splash.finish(main_window)
        sys.exit(app.exec_())