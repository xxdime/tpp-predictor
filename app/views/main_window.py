from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox, QFileDialog,
)
from PySide6.QtCore import Qt

from app.database.engine import get_session
from app.models.part import Part
from app.views.dialogs.part_dialog import PartDialog
from app.services import export_service


class MainWindow(QMainWindow):
    """Main application window showing the list of parts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TPP Predictor — Прогнозирование износа деталей")
        self.setMinimumSize(700, 500)

        self._session = get_session()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # --- Part list ---
        self._list_widget = QListWidget()
        self._list_widget.itemDoubleClicked.connect(self._open_part_window)
        main_layout.addWidget(self._list_widget)

        # --- Buttons ---
        btn_layout = QHBoxLayout()

        self._btn_add = QPushButton("Добавить деталь")
        self._btn_add.clicked.connect(self._on_add_part)
        btn_layout.addWidget(self._btn_add)

        self._btn_edit = QPushButton("Изменить")
        self._btn_edit.clicked.connect(self._on_edit_part)
        btn_layout.addWidget(self._btn_edit)

        self._btn_delete = QPushButton("Удалить")
        self._btn_delete.clicked.connect(self._on_delete_part)
        btn_layout.addWidget(self._btn_delete)

        btn_layout.addStretch()

        self._btn_templates = QPushButton("Шаблоны")
        self._btn_templates.clicked.connect(self._open_templates_window)
        btn_layout.addWidget(self._btn_templates)

        self._btn_archive = QPushButton("Архивировать")
        self._btn_archive.clicked.connect(self._on_archive)
        btn_layout.addWidget(self._btn_archive)

        main_layout.addLayout(btn_layout)

        self._load_parts()

    # ------------------------------------------------------------------
    def _load_parts(self):
        self._list_widget.clear()
        self._session.expire_all()
        parts = self._session.query(Part).order_by(Part.name).all()
        for part in parts:
            label = part.name
            if part.serial_number:
                label += f"  [{part.serial_number}]"
            label += f"  — {part.template.name}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, part.id)
            self._list_widget.addItem(item)

    def _selected_part_id(self):
        item = self._list_widget.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    # ------------------------------------------------------------------
    def _on_add_part(self):
        dlg = PartDialog(self._session, parent=self)
        if dlg.exec():
            self._load_parts()

    def _on_edit_part(self):
        part_id = self._selected_part_id()
        if part_id is None:
            QMessageBox.information(self, "Информация", "Выберите деталь из списка.")
            return
        part = self._session.get(Part, part_id)
        if part is None:
            return
        dlg = PartDialog(self._session, part=part, parent=self)
        if dlg.exec():
            self._load_parts()

    def _on_delete_part(self):
        part_id = self._selected_part_id()
        if part_id is None:
            QMessageBox.information(self, "Информация", "Выберите деталь из списка.")
            return
        part = self._session.get(Part, part_id)
        if part is None:
            return
        answer = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить деталь '{part.name}'? Все измерения будут удалены.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._session.delete(part)
            self._session.commit()
            self._load_parts()

    def _open_part_window(self, item: QListWidgetItem):
        part_id = item.data(Qt.ItemDataRole.UserRole)
        from app.views.part_window import PartWindow
        win = PartWindow(part_id, parent=self)
        win.show()

    def _open_templates_window(self):
        from app.views.templates_window import TemplatesWindow
        win = TemplatesWindow(parent=self)
        win.show()

    def _on_archive(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить архив",
            "parts_export.zip",
            "ZIP Archive (*.zip)",
        )
        if not path:
            return
        try:
            export_service.export_parts_to_zip(self._session, path)
            QMessageBox.information(self, "Успех", f"Архив сохранён:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать архив:\n{exc}")

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self._session.close()
        super().closeEvent(event)
