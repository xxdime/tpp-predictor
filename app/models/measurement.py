from datetime import datetime
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.engine import Base


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    parameter_id = Column(Integer, ForeignKey("template_parameters.id"), nullable=False)
    hours = Column(Float, nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    part = relationship("Part", back_populates="measurements")
    parameter = relationship("TemplateParameter", back_populates="measurements")
