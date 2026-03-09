from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.engine import Base


class ForecastSettings(Base):
    __tablename__ = "forecast_settings"

    id = Column(Integer, primary_key=True)
    parameter_id = Column(
        Integer, ForeignKey("template_parameters.id"), unique=True, nullable=False
    )
    lsm_function_type = Column(String, default="linear")
    gpr_kernel_type = Column(String, default="rbf")
    gpr_length_scale = Column(Float, default=1000.0)
    gpr_noise_level = Column(Float, default=0.01)
    confidence_level = Column(Float, default=2.0)

    parameter = relationship("TemplateParameter", back_populates="forecast_settings")
