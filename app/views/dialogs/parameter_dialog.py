from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QDoubleSpinBox, QCheckBox, QMessageBox,
)
from sqlalchemy.orm import Session
from app.models.template import Template, TemplateParameter
from app.models.forecast_settings import ForecastSettings


class ParameterDialog(QDialog):
    """Dialog for adding or editing a TemplateParameter."""

    def __init__(
        self,
        session: Session,
        template: Template,
        parameter: TemplateParameter = None,
        parent=None,
    ):
        super().__init__(parent)
        self._session = session
        self._template = template
        self._parameter = parameter
        self._editing = parameter is not None

        self.setWindowTitle(
            "Изменить параметр" if self._editing else "Добавить параметр"
        )
        self.setMinimumWidth(380)

        layout = QFormLayout(self)

        self._name_edit = QLineEdit()
        layout.addRow("Название параметра *:", self._name_edit)

        self._unit_edit = QLineEdit()
        layout.addRow("Единица измерения:", self._unit_edit)

        self._critical_spin = QDoubleSpinBox()
        self._critical_spin.setMinimum(-999_999.0)
        self._critical_spin.setMaximum(999_999.0)
        self._critical_spin.setDecimals(4)
        self._critical_spin.setSingleStep(0.01)
        layout.addRow("Критическое значение *:", self._critical_spin)

        self._decreasing_cb = QCheckBox("Параметр уменьшается (стачивание)")
        self._decreasing_cb.setChecked(True)
        layout.addRow("Направление износа:", self._decreasing_cb)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if self._editing:
            self._name_edit.setText(parameter.name or "")
            self._unit_edit.setText(parameter.unit or "")
            self._critical_spin.setValue(parameter.critical_value)
            self._decreasing_cb.setChecked(bool(parameter.is_decreasing))

    def _on_accept(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(
                self, "Ошибка", "Поле 'Название параметра' обязательно для заполнения."
            )
            return

        critical_value = self._critical_spin.value()
        unit = self._unit_edit.text().strip() or None
        is_decreasing = self._decreasing_cb.isChecked()

        if self._editing:
            self._parameter.name = name
            self._parameter.unit = unit
            self._parameter.critical_value = critical_value
            self._parameter.is_decreasing = is_decreasing
        else:
            self._parameter = TemplateParameter(
                template_id=self._template.id,
                name=name,
                unit=unit,
                critical_value=critical_value,
                is_decreasing=is_decreasing,
            )
            self._session.add(self._parameter)
            self._session.flush()  # get parameter.id

            # Create default ForecastSettings
            settings = ForecastSettings(parameter_id=self._parameter.id)
            self._session.add(settings)

        self._session.commit()
        self.accept()

    @property
    def parameter(self) -> TemplateParameter:
        return self._parameter
