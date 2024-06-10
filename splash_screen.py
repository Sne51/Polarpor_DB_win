from PyQt5.QtWidgets import QSplashScreen, QDesktopWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt


class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap("/Users/sk/Documents/EDU_Python/PPT_BD/Polarpor_DB_win_clean/media/splash_screen_1.png")
        super().__init__(pixmap)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setFixedSize(pixmap.size())
        self.center()

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
