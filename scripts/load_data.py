import pandas as pd
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Restaurant

df = pd.read_csv("data/zomato.csv", encoding="latin-1")

df = df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))

def to_bool(val):
    return str(val).strip().lower() == "yes"

def insert_data():
    session: Session = SessionLocal()
    for _, row in df.iterrows():
        try:
            rest = Restaurant(
                id=int(row["restaurant_id"]),
                name=row["restaurant_name"],
                country_code=int(row["country_code"]),
                city=row["city"],
                address=row["address"],
                locality=row["locality"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                cuisines=row["cuisines"],
                average_cost_for_two=int(row["average_cost_for_two"]),
                currency=row["currency"],
                has_online_delivery=to_bool(row["has_online_delivery"]),
                has_table_booking=to_bool(row["has_table_booking"]),
                rating=float(row["aggregate_rating"]),
                votes=int(row["votes"]),
            )
            session.add(rest)
        except Exception as e:
            print("Error processing row:", e)
    session.commit()
    session.close()

if __name__ == "__main__":
    insert_data()
