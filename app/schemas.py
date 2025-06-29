from pydantic import BaseModel, ConfigDict
from typing import ClassVar

class RestaurantBase(BaseModel):
    name: str
    country_code: int
    city: str
    address: str
    locality: str
    latitude: float
    longitude: float
    cuisines: str
    average_cost_for_two: int
    currency: str
    has_online_delivery: bool
    has_table_booking: bool
    rating: float
    votes: int

class Restaurant(RestaurantBase):
    id: int

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
