# splash_screen.py
import sys
from PyQt5.QtWidgets import QSplashScreen, QApplication
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt, QTimer


class SplashScreen(QSplashScreen):
    def __init__(self, app):
        if sys.platform == "win32":
            splash_pix = QPixmap('C:/Users/Usr/Documents/Polarpor_DB_win/Polarpor_DB_win/media/splash_screen_1.png')
        else:
            splash_pix = QPixmap('/Users/sk/Documents/EDU_Python/PPT_do_quick/media/splash_screen_1.png')

        screen = app.primaryScreen().availableGeometry()
        splash_size = int(min(screen.width(), screen.height()) * 0.5)
        splash_pix = splash_pix.scaled(splash_size, splash_size, Qt.KeepAspectRatio)
        super().__init__(splash_pix, Qt.WindowStaysOnTopHint)

        self.setMask(splash_pix.mask())
        self.show()

        # Центрирование Splash Screen
        center_point = screen.center()
        self.move(center_point.x() - self.width() // 2, center_point.y() - self.height() // 2)

    def update_message(self, message, app):
        font = self.font()
        if sys.platform == "win32":
            font.setPointSize(self.width() // 40)
        else:
            font.setPointSize(self.width() // 30)
        self.setFont(font)
        self.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, QColor(Qt.white))
        app.processEvents()
