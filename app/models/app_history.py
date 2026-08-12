from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class AppHistory(Base):
    __tablename__ = "app_history"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)

    reference_number = Column(String, nullable=True)
    application_step = Column(String, nullable=True)
    current_status = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    step_duedate = Column(String, nullable=True)

    application = relationship("Application", back_populates="history")