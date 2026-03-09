from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.engine import Base


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)

    parameters = relationship(
        "TemplateParameter",
        back_populates="template",
        cascade="all, delete-orphan",
    )
    parts = relationship("Part", back_populates="template")


class TemplateParameter(Base):
    __tablename__ = "template_parameters"

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=True)
    critical_value = Column(Float, nullable=False)
    is_decreasing = Column(Boolean, default=True)

    template = relationship("Template", back_populates="parameters")
    forecast_settings = relationship(
        "ForecastSettings",
        back_populates="parameter",
        uselist=False,
        cascade="all, delete-orphan",
    )
    measurements = relationship(
        "Measurement",
        back_populates="parameter",
        cascade="all, delete-orphan",
    )
