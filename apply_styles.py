def apply_app_style(app):
    # Настройки стиля для QComboBox
    app.setStyleSheet("""
        QComboBox {
            color: white; /* Цвет текста */
            background-color: #333333; /* Цвет фона */
        }
        QComboBox QAbstractItemView {
            color: white; /* Цвет текста элементов */
            background-color: #333333; /* Цвет фона элементов */
            selection-background-color: #555555; /* Цвет фона выбранного элемента */
        }
        QComboBox::drop-down {
            background-color: #333333; /* Цвет фона кнопки выпадающего списка */
        }
        QComboBox::down-arrow {
            image: url(down_arrow.png); /* Пользовательское изображение стрелки вниз, если нужно */
        }
    """)