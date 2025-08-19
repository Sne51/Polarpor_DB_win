# splash_screen.py
import sys
from pathlib import Path
from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtGui import QPixmap, QColor, QPainter
from PyQt5.QtCore import Qt

class SplashScreen(QSplashScreen):
    def __init__(self, app):
        # Путь к проекту (где лежит main.py)
        project_dir = Path(__file__).resolve().parent
        # ожидаем картинку тут: <project>/media/splash_screen_1.png
        img_path = project_dir / "media" / "splash_screen_1.png"

        pix = QPixmap()
        if img_path.exists():
            pix.load(str(img_path))

        # Фолбэк: если не нашли/не загрузили — рисуем простой прямоугольник
        if pix.isNull():
            screen_geo = app.primaryScreen().availableGeometry()
            size = int(min(screen_geo.width(), screen_geo.height()) * 0.4)
            if size < 200:
                size = 400
            pix = QPixmap(size, size)
            pix.fill(QColor("#0e1116"))
            p = QPainter(pix)
            p.setPen(Qt.white)
            p.drawText(pix.rect(), Qt.AlignCenter, "Загрузка…")
            p.end()

        # Масштабируем под экран
        screen_geo = app.primaryScreen().availableGeometry()
        splash_size = int(min(screen_geo.width(), screen_geo.height()) * 0.5)
        pix = pix.scaled(splash_size, splash_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        super().__init__(pix, Qt.WindowStaysOnTopHint)

        # Центрирование
        center = screen_geo.center()
        self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)
        self.show()              # показать сплэш
        app.processEvents()      # сразу отрисовать

    def update_message(self, message, app):
        f = self.font()
        f.setPointSize(max(10, self.width() // 30))
        self.setFont(f)
        self.showMessage(message, Qt.AlignBottom | Qt.AlignHCenter, QColor(Qt.white))
        app.processEvents()