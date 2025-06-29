from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from app import models, schemas, crud
from app.database import SessionLocal, engine

from fastapi import UploadFile, File
from app.utils.clip_utils import (
    encode_image,
    find_similar_cuisines,
    load_precomputed_cuisine_embeddings
)
import tempfile

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="app/templates")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(models.Restaurant)

    restaurants = query.offset(offset).limit(limit).all()

    return templates.TemplateResponse("home.html", {
        "request": request,
        "restaurants": restaurants,
        "offset": offset,
        "limit": limit
    })

 
        
@app.get("/restaurants/nearby", response_model=list[schemas.Restaurant])
def search_nearby(lat: float, lon: float, radius_km: float = 3.0, db: Session = Depends(get_db)):
    return crud.get_restaurants_nearby(db, lat=lat, lon=lon, radius_km=radius_km)

@app.get("/nearby", response_class=HTMLResponse)
def nearby_restaurants_page(
    request: Request,
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float = Query(3),
    offset: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    restaurants = crud.get_restaurants_nearby(db, lat, lon, radius_km, offset, limit)
    return templates.TemplateResponse("nearby.html", {
        "request": request,
        "restaurants": restaurants,
        "lat": lat,
        "lon": lon,
        "radius_km": radius_km,
        "offset": offset,
        "limit": limit
    })



@app.get("/restaurants/search", response_model=list[schemas.Restaurant])
async def search_restaurants(
    q: str = Query(..., min_length=2),
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    results = crud.search_restaurants(db, q, offset, limit)
    return [schemas.Restaurant.model_validate(r) for r in results]


@app.get("/search", response_class=HTMLResponse)
def search_html(
    request: Request,
    q: str,
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    results = crud.search_restaurants(db, query=q, offset=offset, limit=limit)
    return templates.TemplateResponse("search.html", {
        "request": request,
        "restaurants": results,
        "query": q,
        "offset": offset,
        "limit": limit
    })


@app.get("/restaurants/{restaurant_id}", response_model=schemas.Restaurant)
def read_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    db_restaurant = crud.get_restaurant_by_id(db, restaurant_id)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return db_restaurant


@app.get("/restaurant/{restaurant_id}", response_class=HTMLResponse)
def restaurant_detail(
    request: Request,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    restaurant = db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return templates.TemplateResponse("restaurant.html", {
        "request": request,
        "restaurant": restaurant
    })


@app.get("/restaurants", response_model=list[schemas.Restaurant])
def list_restaurants(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_restaurants(db, skip=skip, limit=limit)


@app.post("/upload-image", response_class=HTMLResponse)
async def upload_image(
    request: Request,
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

    return templates.TemplateResponse("upload.html", {
        "request": request,
        "matches": [{"cuisine": c, "score": round(s, 3)} for c, s in results],
        "restaurants": matching_restaurants,
        "offset": offset,
        "limit": limit
    })


@app.get("/upload-image", response_class=HTMLResponse)
def upload_image_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

