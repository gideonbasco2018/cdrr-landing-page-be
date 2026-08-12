from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)

    reference_number = Column(String, nullable=True)
    activity = Column(String, nullable=True)
    applicant_company = Column(String, nullable=True)
    email_address = Column(String, nullable=True)
    contact_no = Column(String, nullable=True)
    address = Column(String, nullable=True)
    tin = Column(String, nullable=True)
    lto_no = Column(String, nullable=True)
    validity = Column(String, nullable=True)
    application_type = Column(String, nullable=True)

    brand_name = Column(String, nullable=True)
    generic_name = Column(String, nullable=True)
    dosage_strength = Column(String, nullable=True)
    dosage_form_route = Column(String, nullable=True)
    classification = Column(String, nullable=True)
    product_category = Column(String, nullable=True)
    essential_drug_list = Column(String, nullable=True)
    pharmacologic_category = Column(String, nullable=True)

    shelf_life = Column(String, nullable=True)
    storage_condition = Column(String, nullable=True)
    packaging = Column(String, nullable=True)
    suggested_retail_price = Column(String, nullable=True)
    registration_number = Column(String, nullable=True)
    mother_application_type = Column(String, nullable=True)
    old_rsn_other_dtn = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parties = relationship(
        "AppParty", back_populates="application", cascade="all, delete-orphan"
    )
    history = relationship(
        "AppHistory", back_populates="application", cascade="all, delete-orphan"
    )