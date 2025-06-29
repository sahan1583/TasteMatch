from sqlalchemy.orm import Session
from app import models
from typing import List
from math import radians, cos, sin, sqrt, atan2
from sqlalchemy import or_

def get_restaurant_by_id(db: Session, restaurant_id: int):
    return db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()

def get_restaurants(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Restaurant).offset(skip).limit(limit).all()

def get_restaurants_nearby(db: Session, lat: float, lon: float, radius_km: float) -> List[models.Restaurant]:
    all_restaurants = db.query(models.Restaurant).all()
    result = []

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        phi1, phi2 = radians(lat1), radians(lat2)
        d_phi = radians(lat2 - lat1)
        d_lambda = radians(lon2 - lon1)
        a = sin(d_phi/2)**2 + cos(phi1)*cos(phi2)*sin(d_lambda/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    for r in all_restaurants:
        if r.latitude is None or r.longitude is None:
            continue
        dist = haversine(lat, lon, r.latitude, r.longitude)
        if dist <= radius_km:
            result.append(r)

    return result

def get_restaurants_by_cuisines_filtered(
    db: Session,
    cuisines: list[str],
    cuisine_scores: dict[str, float],  
    country_code: int = None,
    avgcost_for2: int = None,
    offset: int = 0,
    limit: int = 10
):

    filters = [models.Restaurant.cuisines.ilike(f"%{c}%") for c in cuisines]

    query = db.query(models.Restaurant).filter(or_(*filters))

    # Optional filters
    if country_code is not None:
        query = query.filter(models.Restaurant.country_code == country_code)
    if avgcost_for2 is not None:
        query = query.filter(models.Restaurant.average_cost_for_two <= avgcost_for2)

    all_matches = query.offset(offset).limit(limit * 5).all()  

    print("DB returned:", len(all_matches), "restaurants")

    # Sort by best cuisine match score
    def score_r(r):
        for c in cuisines:
            if c.lower() in r.cuisines.lower():
                return cuisine_scores.get(c, 0)
        return 0

    sorted_matches = sorted(all_matches, key=score_r, reverse=True)

    return sorted_matches[:limit]


def search_restaurants(
    db: Session,
    query: str,
    offset: int = 0,
    limit: int = 10
):
    like_pattern = f"%{query}%"

    return db.query(models.Restaurant).filter(
        or_(
            models.Restaurant.name.ilike(like_pattern),
            models.Restaurant.cuisines.ilike(like_pattern),
            models.Restaurant.locality.ilike(like_pattern),
            models.Restaurant.address.ilike(like_pattern)
        )
    ).offset(offset).limit(limit).all()
