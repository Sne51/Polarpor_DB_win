from PyQt5.QtWidgets import QStyledItemDelegate, QComboBox, QDateEdit
from PyQt5.QtCore import QDate


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent, items):
        super().__init__(parent)
        self.items = items

    def createEditor(self, parent, option, index):
        # Создаем выпадающий список
        combo = QComboBox(parent)
        combo.addItems(self.items)
        return combo

    def setEditorData(self, editor, index):
        # Устанавливаем текущее значение из таблицы
        text = index.data()
        if text in self.items:
            editor.setCurrentText(text)

    def setModelData(self, editor, model, index):
        # Сохраняем выбранное значение обратно в модель
        model.setData(index, editor.currentText())


class QDateEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        # Создаем редактор для выбора даты
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)  # Включаем всплывающее окно календаря
        editor.setDate(QDate.currentDate())  # Устанавливаем текущую дату по умолчанию
        return editor

    def setEditorData(self, editor, index):
        # Устанавливаем дату из таблицы
        text = index.data()
        if text:
            editor.setDate(QDate.fromString(text, "yyyy-MM-dd"))

    def setModelData(self, editor, model, index):
        # Сохраняем выбранную дату обратно в модель
        model.setData(index, editor.date().toString("yyyy-MM-dd"))
