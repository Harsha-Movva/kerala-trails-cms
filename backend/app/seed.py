from sqlalchemy.orm import Session
from .models import User, Package, SeasonPrice, PackageVersion
from .security import hash_password

PACKAGES = [
 {"code":"PKG-KL-07","slug":"munnar-thekkady-alleppey-houseboat","title":"Munnar, Thekkady & Alleppey Houseboat","destination":"Kerala","duration_days":6,"summary":"A relaxed six-day journey through misty tea gardens, wildlife country and the quiet backwaters of Alleppey.","hero_image":"https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1800&q=85","hotel_category":"4 star","status":"published","itinerary":[{"day":1,"title":"Arrive in Kochi · Drive to Munnar","description":"Meet your driver and wind through the hills to Munnar."},{"day":2,"title":"Munnar tea country","description":"Visit tea gardens, viewpoints and the tea museum."},{"day":3,"title":"Munnar to Thekkady","description":"Travel through spice country and enjoy a guided plantation visit."},{"day":4,"title":"Thekkady to Alleppey","description":"Arrive at the backwaters and board your private houseboat."},{"day":5,"title":"Alleppey to Kochi","description":"Enjoy breakfast on the water before returning to Kochi."},{"day":6,"title":"Departure","description":"Breakfast and transfer to the airport or railway station."}],"inclusions":["5 nights accommodation","Daily breakfast","Private air-conditioned vehicle","One-night houseboat stay with meals","All sightseeing listed in itinerary"],"seasons":[{"season":"Peak · Oct–Mar","start_month":10,"end_month":3,"price_per_person":32500},{"season":"Monsoon · Jun–Sep","start_month":6,"end_month":9,"price_per_person":24900}]},
 {"code":"PKG-SI-12","slug":"madurai-rameswaram-kanyakumari","title":"Madurai, Rameswaram & Kanyakumari","destination":"Tamil Nadu","duration_days":5,"summary":"Temple heritage, coastal landscapes and memorable sunrises across South India's southern coast.","hero_image":"https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1800&q=85","hotel_category":"3 star","status":"draft","itinerary":[{"day":1,"title":"Arrive in Madurai","description":"Explore the historic city and its celebrated temple district."},{"day":2,"title":"Madurai to Rameswaram","description":"Drive across the Pamban bridge and explore the island."},{"day":3,"title":"Rameswaram","description":"A day to explore the island's coastal and cultural landmarks."},{"day":4,"title":"Kanyakumari","description":"Continue south for coastal views and sunset by the sea."},{"day":5,"title":"Departure","description":"Breakfast and onward transfer."}],"inclusions":["4 nights accommodation","Daily breakfast","Private transfers","Sightseeing as listed"],"seasons":[{"season":"All year","start_month":1,"end_month":12,"price_per_person":18750}]}
]

def seed(db: Session):
    if not db.query(User).filter_by(email="admin@keralatrails.demo").first():
        db.add(User(email="admin@keralatrails.demo", password_hash=hash_password("TrailDemo!2026"), role="admin"))
    db.flush()
    for item in PACKAGES:
        if db.query(Package).filter_by(code=item["code"]).first():
            continue
        seasons = item["seasons"]
        package_data = {k: v for k, v in item.items() if k != "seasons"}
        package = Package(**package_data)
        db.add(package); db.flush()
        for season in seasons:
            db.add(SeasonPrice(package_id=package.id, **season))
        snapshot = {k:v for k,v in package_data.items()}
        snapshot["seasons"] = seasons
        db.add(PackageVersion(package_id=package.id, version_number=1, snapshot=snapshot))
        if package.status == "published": package.published_version = 1
    db.commit()
