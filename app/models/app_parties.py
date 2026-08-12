from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class AppParty(Base):
    __tablename__ = "app_parties"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)

    party_type = Column(String, nullable=False)
    name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    tin = Column(String, nullable=True)
    lto_no = Column(String, nullable=True)
    country = Column(String, nullable=True)

    application = relationship("Application", back_populates="parties")