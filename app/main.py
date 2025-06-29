from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas, crud
from app.database import SessionLocal, engine

from fastapi import UploadFile, File
from app.utils.clip_utils import (
    encode_image,
    find_similar_cuisines,
    load_precomputed_cuisine_embeddings
)
import tempfile


models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

      
        
@app.get("/restaurants/nearby", response_model=list[schemas.Restaurant])
def search_nearby(lat: float, lon: float, radius_km: float = 3.0, db: Session = Depends(get_db)):
    return crud.get_restaurants_nearby(db, lat=lat, lon=lon, radius_km=radius_km)

@app.get("/restaurants/search", response_model=list[schemas.Restaurant])
async def search_restaurants(
    q: str = Query(..., min_length=2),
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    results = crud.search_restaurants(db, q, offset, limit)
    return [schemas.Restaurant.model_validate(r) for r in results]


@app.get("/restaurants/{restaurant_id}", response_model=schemas.Restaurant)
def read_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    db_restaurant = crud.get_restaurant_by_id(db, restaurant_id)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return db_restaurant


@app.get("/restaurants", response_model=list[schemas.Restaurant])
def list_restaurants(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_restaurants(db, skip=skip, limit=limit)


@app.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    country_code: int = Query(None),
    avgcost_for2: int = Query(None),
    offset: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    # Save uploaded image to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Load all cuisine embeddings
    cuisine_names, cuisine_embeddings = load_precomputed_cuisine_embeddings()

    # Encode image using CLIP
    image_embedding = encode_image(tmp_path)

    results = find_similar_cuisines(
        image_embedding,
        cuisine_embeddings,
        cuisine_names,
        top_k=5,
        similarity_threshold=0.2
    )

    matched_cuisine_names = [c for c, _ in results]
    cuisine_scores = {c: s for c, s in results}

    matching_restaurants = crud.get_restaurants_by_cuisines_filtered(
        db=db,
        cuisines=matched_cuisine_names,
        cuisine_scores=cuisine_scores,
        country_code=country_code,
        avgcost_for2=avgcost_for2,
        offset=offset,
        limit=limit
    )

    # print("Matched cuisines:", matched_cuisine_names)
    # print("Fetched restaurants:", [r.name for r in matching_restaurants])

    return {
        "matches": [{"cuisine": c, "score": round(s, 3)} for c, s in results],
        "restaurants": [schemas.Restaurant.model_validate(r) for r in matching_restaurants]
    }


