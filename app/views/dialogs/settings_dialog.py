from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QComboBox,
    QDoubleSpinBox, QLabel,
)
from sqlalchemy.orm import Session
from app.models.template import TemplateParameter
from app.models.forecast_settings import ForecastSettings


_LSM_OPTIONS = [
    ("Линейная", "linear"),
    ("Квадратичная", "quadratic"),
    ("Кубическая", "cubic"),
    ("Экспоненциальная", "exponential"),
    ("Степенная", "power"),
    ("Логарифмическая", "logarithmic"),
]

_GPR_KERNEL_OPTIONS = [
    ("RBF", "rbf"),
    ("Matérn", "matern"),
    ("RBF + White Noise", "rbf+white"),
    ("Matérn + White Noise", "matern+white"),
]


class SettingsDialog(QDialog):
    """Dialog for editing ForecastSettings of a TemplateParameter."""

    def __init__(
        self,
        session: Session,
        parameter: TemplateParameter,
        parent=None,
    ):
        super().__init__(parent)
        self._session = session
        self._parameter = parameter

        self.setWindowTitle(f"Настройки прогноза — {parameter.name}")
        self.setMinimumWidth(420)

        layout = QFormLayout(self)

        layout.addRow("Параметр:", QLabel(f"<b>{parameter.name}</b>"))

        self._lsm_combo = QComboBox()
        for label, value in _LSM_OPTIONS:
            self._lsm_combo.addItem(label, value)
        layout.addRow("Тип функции МНК:", self._lsm_combo)

        self._kernel_combo = QComboBox()
        for label, value in _GPR_KERNEL_OPTIONS:
            self._kernel_combo.addItem(label, value)
        layout.addRow("Тип ядра GPR:", self._kernel_combo)

        self._length_scale_spin = QDoubleSpinBox()
        self._length_scale_spin.setMinimum(1.0)
        self._length_scale_spin.setMaximum(1_000_000.0)
        self._length_scale_spin.setDecimals(1)
        self._length_scale_spin.setSingleStep(100.0)
        layout.addRow("Масштаб длины GPR:", self._length_scale_spin)

        self._noise_spin = QDoubleSpinBox()
        self._noise_spin.setMinimum(0.0001)
        self._noise_spin.setMaximum(100.0)
        self._noise_spin.setDecimals(4)
        self._noise_spin.setSingleStep(0.001)
        layout.addRow("Уровень шума GPR:", self._noise_spin)

        self._confidence_spin = QDoubleSpinBox()
        self._confidence_spin.setMinimum(0.5)
        self._confidence_spin.setMaximum(3.0)
        self._confidence_spin.setSingleStep(0.5)
        self._confidence_spin.setDecimals(1)
        self._confidence_spin.setToolTip("1.0 = 68%, 2.0 = 95%, 3.0 = 99.7%")
        layout.addRow("Множитель доверит. интервала:", self._confidence_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self._load_settings()

    def _get_or_create_settings(self) -> ForecastSettings:
        s = self._parameter.forecast_settings
        if s is None:
            s = ForecastSettings(parameter_id=self._parameter.id)
            self._session.add(s)
            self._session.flush()
        return s

    def _load_settings(self):
        s = self._get_or_create_settings()

        for i in range(self._lsm_combo.count()):
            if self._lsm_combo.itemData(i) == s.lsm_function_type:
                self._lsm_combo.setCurrentIndex(i)
                break

        for i in range(self._kernel_combo.count()):
            if self._kernel_combo.itemData(i) == s.gpr_kernel_type:
                self._kernel_combo.setCurrentIndex(i)
                break

        self._length_scale_spin.setValue(s.gpr_length_scale or 1000.0)
        self._noise_spin.setValue(s.gpr_noise_level or 0.01)
        self._confidence_spin.setValue(s.confidence_level or 2.0)

    def _on_accept(self):
        s = self._get_or_create_settings()
        s.lsm_function_type = self._lsm_combo.currentData()
        s.gpr_kernel_type = self._kernel_combo.currentData()
        s.gpr_length_scale = self._length_scale_spin.value()
        s.gpr_noise_level = self._noise_spin.value()
        s.confidence_level = self._confidence_spin.value()
        self._session.commit()
        self.accept()
