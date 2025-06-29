from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    country_code = Column(Integer)
    city = Column(String)
    address = Column(String)
    locality = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    cuisines = Column(String)
    average_cost_for_two = Column(Integer)
    currency = Column(String)
    has_online_delivery = Column(Boolean)
    has_table_booking = Column(Boolean)
    rating = Column(Float)
    votes = Column(Integer)
