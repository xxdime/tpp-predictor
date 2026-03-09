from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.engine import Base


class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    name = Column(String, nullable=False)
    serial_number = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    template = relationship("Template", back_populates="parts")
    measurements = relationship(
        "Measurement",
        back_populates="part",
        cascade="all, delete-orphan",
    )
