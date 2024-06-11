from PyQt5.QtWidgets import QSplashScreen, QGraphicsDropShadowEffect, QApplication
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt


class SplashScreen(QSplashScreen):
    def __init__(self):
        app = QApplication.instance()
        screen_geometry = app.primaryScreen().geometry()
        width, height = screen_geometry.width(), screen_geometry.height()

        # Размер SplashScreen будет 1/10 размера экрана
        splash_width = width // 3
        splash_height = height // 3

        pixmap = QPixmap("/Users/sk/Documents/EDU_Python/PPT_BD/Polarpor_DB_win_clean/media/splash_screen_1.png")
        pixmap = pixmap.scaled(splash_width, splash_height, Qt.KeepAspectRatio)

        super().__init__(pixmap)

        # Центрируем SplashScreen на экране
        self.setGeometry((width - splash_width) // 2, (height - splash_height) // 2, splash_width, splash_height)

        # Добавление теней для улучшения внешнего вида
        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(20)
        effect.setXOffset(0)
        effect.setYOffset(0)
        effect.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(effect)

        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
