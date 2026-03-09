from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox, QLabel,
    QSplitter,
)
from PySide6.QtCore import Qt

from app.database.engine import get_session
from app.models.template import Template, TemplateParameter
from app.views.dialogs.template_dialog import TemplateDialog
from app.views.dialogs.parameter_dialog import ParameterDialog
from app.views.dialogs.settings_dialog import SettingsDialog


class TemplatesWindow(QMainWindow):
    """Window for managing part templates and their parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Шаблоны деталей")
        self.setMinimumSize(750, 500)

        self._session = get_session()

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)

        # --- Left: template list ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Шаблоны:"))

        self._template_list = QListWidget()
        self._template_list.setMaximumWidth(260)
        self._template_list.currentItemChanged.connect(self._on_template_selected)
        left_layout.addWidget(self._template_list)

        tpl_btn_layout = QHBoxLayout()
        self._btn_add_tpl = QPushButton("Добавить")
        self._btn_add_tpl.clicked.connect(self._on_add_template)
        tpl_btn_layout.addWidget(self._btn_add_tpl)

        self._btn_edit_tpl = QPushButton("Изменить")
        self._btn_edit_tpl.clicked.connect(self._on_edit_template)
        tpl_btn_layout.addWidget(self._btn_edit_tpl)

        self._btn_delete_tpl = QPushButton("Удалить")
        self._btn_delete_tpl.clicked.connect(self._on_delete_template)
        tpl_btn_layout.addWidget(self._btn_delete_tpl)

        left_layout.addLayout(tpl_btn_layout)
        root_layout.addWidget(left_widget)

        # --- Right: parameter list ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Параметры выбранного шаблона:"))

        self._param_list = QListWidget()
        right_layout.addWidget(self._param_list)

        param_btn_layout = QHBoxLayout()
        self._btn_add_param = QPushButton("Добавить параметр")
        self._btn_add_param.clicked.connect(self._on_add_parameter)
        param_btn_layout.addWidget(self._btn_add_param)

        self._btn_edit_param = QPushButton("Изменить параметр")
        self._btn_edit_param.clicked.connect(self._on_edit_parameter)
        param_btn_layout.addWidget(self._btn_edit_param)

        self._btn_delete_param = QPushButton("Удалить параметр")
        self._btn_delete_param.clicked.connect(self._on_delete_parameter)
        param_btn_layout.addWidget(self._btn_delete_param)

        self._btn_settings = QPushButton("Настройки прогноза")
        self._btn_settings.clicked.connect(self._on_settings)
        param_btn_layout.addWidget(self._btn_settings)

        right_layout.addLayout(param_btn_layout)
        root_layout.addWidget(right_widget)

        self._load_templates()

    # ------------------------------------------------------------------
    def _load_templates(self):
        self._template_list.clear()
        templates = (
            self._session.query(Template).order_by(Template.name).all()
        )
        for t in templates:
            item = QListWidgetItem(t.name)
            item.setData(Qt.ItemDataRole.UserRole, t.id)
            self._template_list.addItem(item)

    def _selected_template(self) -> Template:
        item = self._template_list.currentItem()
        if item is None:
            return None
        return self._session.get(Template, item.data(Qt.ItemDataRole.UserRole))

    def _selected_parameter(self) -> TemplateParameter:
        item = self._param_list.currentItem()
        if item is None:
            return None
        return self._session.get(
            TemplateParameter, item.data(Qt.ItemDataRole.UserRole)
        )

    def _on_template_selected(self):
        template = self._selected_template()
        self._load_parameters(template)

    def _load_parameters(self, template: Template):
        self._param_list.clear()
        if template is None:
            return
        self._session.refresh(template)
        for param in template.parameters:
            unit_str = f" [{param.unit}]" if param.unit else ""
            label = (
                f"{param.name}{unit_str}, крит.: {param.critical_value}"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, param.id)
            self._param_list.addItem(item)

    # ------------------------------------------------------------------
    def _on_add_template(self):
        dlg = TemplateDialog(self._session, parent=self)
        if dlg.exec():
            self._load_templates()

    def _on_edit_template(self):
        template = self._selected_template()
        if template is None:
            QMessageBox.information(self, "Информация", "Выберите шаблон.")
            return
        dlg = TemplateDialog(self._session, template=template, parent=self)
        if dlg.exec():
            self._load_templates()

    def _on_delete_template(self):
        template = self._selected_template()
        if template is None:
            QMessageBox.information(self, "Информация", "Выберите шаблон.")
            return
        if template.parts:
            QMessageBox.warning(
                self,
                "Нельзя удалить",
                f"Шаблон '{template.name}' нельзя удалить, "
                "так как к нему привязаны детали.",
            )
            return
        answer = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить шаблон '{template.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._session.delete(template)
            self._session.commit()
            self._load_templates()
            self._param_list.clear()

    # ------------------------------------------------------------------
    def _on_add_parameter(self):
        template = self._selected_template()
        if template is None:
            QMessageBox.information(self, "Информация", "Выберите шаблон.")
            return
        dlg = ParameterDialog(self._session, template, parent=self)
        if dlg.exec():
            self._load_parameters(template)

    def _on_edit_parameter(self):
        template = self._selected_template()
        param = self._selected_parameter()
        if param is None:
            QMessageBox.information(self, "Информация", "Выберите параметр.")
            return
        dlg = ParameterDialog(
            self._session, template, parameter=param, parent=self
        )
        if dlg.exec():
            self._load_parameters(template)

    def _on_delete_parameter(self):
        param = self._selected_parameter()
        if param is None:
            QMessageBox.information(self, "Информация", "Выберите параметр.")
            return
        if param.measurements:
            QMessageBox.warning(
                self,
                "Нельзя удалить",
                f"Параметр '{param.name}' нельзя удалить, "
                "так как к нему привязаны измерения.",
            )
            return
        answer = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить параметр '{param.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            template = self._selected_template()
            self._session.delete(param)
            self._session.commit()
            self._load_parameters(template)

    def _on_settings(self):
        param = self._selected_parameter()
        if param is None:
            QMessageBox.information(self, "Информация", "Выберите параметр.")
            return
        dlg = SettingsDialog(self._session, param, parent=self)
        dlg.exec()

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self._session.close()
        super().closeEvent(event)
