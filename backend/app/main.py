from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_
from .config import settings
from .db import Base, engine, get_db, SessionLocal
from .models import User, Package, SeasonPrice, PackageVersion, Enquiry, ActivityLog
from .schemas import LoginIn, TokenOut, PackageIn, EnquiryIn, EnquiryStatusIn
from .security import verify_password, create_token, current_user, require_admin
from .seed import seed
from .ai import extract_enquiry

if settings.app_env.lower() == "production" and settings.jwt_secret == "local-development-secret-change-me":
    raise RuntimeError("JWT_SECRET must be replaced before production startup")

Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed(db)

app = FastAPI(title="Kerala Trails API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    from sqlalchemy import text
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": engine.dialect.name, "database_connected": True}

@app.post("/api/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    return {"access_token":create_token(user), "role":user.role}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"id":user.id,"email":user.email,"role":user.role}

def package_out(p: Package):
    return {"id":p.id,"code":p.code,"slug":p.slug,"title":p.title,"destination":p.destination,"duration_days":p.duration_days,"summary":p.summary,"hero_image":p.hero_image,"itinerary":p.itinerary,"inclusions":p.inclusions,"hotel_category":p.hotel_category,"status":p.status,"published_version":p.published_version,"seasons":[{"id":s.id,"season":s.season,"start_month":s.start_month,"end_month":s.end_month,"price_per_person":float(s.price_per_person),"basis":s.basis,"gst_note":s.gst_note} for s in p.seasons]}

@app.get("/api/packages")
def list_packages(q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Package).options(joinedload(Package.seasons)).filter(Package.status == "published")
    if q and q.strip():
        term = f"%{q.strip()[:100]}%"
        query = query.filter(or_(Package.title.ilike(term), Package.destination.ilike(term), Package.summary.ilike(term)))
    return [package_out(p) for p in query.order_by(Package.id).all()]

@app.get("/api/packages/{slug}")
def get_package(slug: str, db: Session = Depends(get_db)):
    p = db.query(Package).options(joinedload(Package.seasons)).filter_by(slug=slug, status="published").first()
    if not p: raise HTTPException(404, "Package not found")
    return package_out(p)

@app.get("/api/admin/packages")
def admin_packages(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return [package_out(p) for p in db.query(Package).options(joinedload(Package.seasons)).order_by(Package.updated_at.desc()).all()]

@app.post("/api/admin/packages")
def create_package(payload: PackageIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if db.query(Package).filter((Package.code == payload.code) | (Package.slug == payload.slug)).first():
        raise HTTPException(409, "Package code or URL slug already exists")
    data = payload.model_dump(exclude={"seasons"})
    p = Package(**data); db.add(p); db.flush()
    for s in payload.seasons: db.add(SeasonPrice(package_id=p.id, **s.model_dump()))
    snapshot = payload.model_dump(mode="json")
    db.add(PackageVersion(package_id=p.id, version_number=1, snapshot=snapshot, changed_by=user.id))
    db.add(ActivityLog(actor_id=user.id, action="package.created", entity_type="package", entity_id=p.id, details={"status": p.status, "version": 1}))
    if p.status == "published": p.published_version = 1
    db.commit(); db.refresh(p)
    return package_out(p)

@app.put("/api/admin/packages/{package_id}")
def update_package(package_id: int, payload: PackageIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    p = db.query(Package).options(joinedload(Package.seasons)).filter_by(id=package_id).first()
    if not p: raise HTTPException(404, "Package not found")
    duplicate = db.query(Package).filter(Package.id != package_id, ((Package.code == payload.code) | (Package.slug == payload.slug))).first()
    if duplicate: raise HTTPException(409, "Package code or URL slug already exists")
    for key, value in payload.model_dump(exclude={"seasons"}).items(): setattr(p, key, value)
    for s in list(p.seasons): db.delete(s)
    db.flush()
    for s in payload.seasons: db.add(SeasonPrice(package_id=p.id, **s.model_dump()))
    latest = db.query(PackageVersion).filter_by(package_id=p.id).order_by(desc(PackageVersion.version_number)).first()
    version = (latest.version_number if latest else 0) + 1
    db.add(PackageVersion(package_id=p.id, version_number=version, snapshot=payload.model_dump(mode="json"), changed_by=user.id))
    db.add(ActivityLog(actor_id=user.id, action="package.updated", entity_type="package", entity_id=p.id, details={"status": p.status, "version": version}))
    if p.status == "published": p.published_version = version
    db.commit(); db.refresh(p)
    return package_out(p)

@app.get("/api/admin/packages/{package_id}/preview")
def preview_package(package_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Authenticated preview endpoint: drafts are never exposed by the public package route."""
    package = db.query(Package).options(joinedload(Package.seasons)).filter_by(id=package_id).first()
    if not package:
        raise HTTPException(404, "Package not found")
    return {**package_out(package), "preview": True, "published_version": package.published_version}

@app.get("/api/admin/packages/{package_id}/versions")
def package_versions(package_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if not db.get(Package, package_id):
        raise HTTPException(404, "Package not found")
    versions = db.query(PackageVersion).filter_by(package_id=package_id).order_by(desc(PackageVersion.version_number)).all()
    return [{"version_number":v.version_number,"snapshot":v.snapshot,"created_at":v.created_at.isoformat()} for v in versions]

@app.post("/api/admin/packages/{package_id}/versions/{version_number}/restore")
def restore_package_version(package_id: int, version_number: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    package = db.query(Package).options(joinedload(Package.seasons)).filter_by(id=package_id).first()
    if not package:
        raise HTTPException(404, "Package not found")
    selected = db.query(PackageVersion).filter_by(package_id=package_id, version_number=version_number).first()
    if not selected:
        raise HTTPException(404, "Version not found")
    snapshot = dict(selected.snapshot)
    seasons = snapshot.pop("seasons", [])
    duplicate = db.query(Package).filter(Package.id != package_id, ((Package.code == snapshot.get("code")) | (Package.slug == snapshot.get("slug")))).first()
    if duplicate:
        raise HTTPException(409, "Cannot restore: the historical package code or slug is now used by another package")
    for key, value in snapshot.items():
        if hasattr(package, key) and key not in {"id", "created_at", "updated_at", "published_version"}:
            setattr(package, key, value)
    for season in list(package.seasons):
        db.delete(season)
    db.flush()
    for season in seasons:
        db.add(SeasonPrice(package_id=package.id, **{k:v for k,v in season.items() if k not in {"id", "package_id"}}))
    latest = db.query(PackageVersion).filter_by(package_id=package_id).order_by(desc(PackageVersion.version_number)).first()
    new_version = (latest.version_number if latest else 0) + 1
    restored_snapshot = {**snapshot, "seasons": seasons}
    db.add(PackageVersion(package_id=package.id, version_number=new_version, snapshot=restored_snapshot, changed_by=user.id))
    db.add(ActivityLog(actor_id=user.id, action="package.version_restored", entity_type="package", entity_id=package.id, details={"restored_from": version_number, "created_version": new_version}))
    if package.status == "published":
        package.published_version = new_version
    db.commit()
    db.refresh(package)
    return {"restored_from": version_number, "created_version": new_version, "package": package_out(package)}

@app.post("/api/enquiries")
def create_enquiry(payload: EnquiryIn, background: BackgroundTasks, db: Session = Depends(get_db)):
    if payload.package_id:
        selected_package = db.get(Package, payload.package_id)
        if not selected_package or selected_package.status != "published": raise HTTPException(404, "Package not found")
    e = Enquiry(**payload.model_dump(), source="website", status="new")
    db.add(e); db.commit(); db.refresh(e)
    background.add_task(process_enquiry, e.id, payload.message)
    return {"id":e.id,"status":"received","acknowledgement":"Thank you. Your enquiry has been received; our travel team will contact you shortly."}

def process_enquiry(enquiry_id: int, message: str):
    from .db import SessionLocal
    db = SessionLocal()
    try:
        e = db.get(Enquiry, enquiry_id)
        if not e: return
        try:
            extracted = extract_enquiry(message)
            packages = db.query(Package).filter_by(status="published").all()
            destination = (extracted.get("destination") or "").lower()
            must = " ".join(extracted.get("must_haves") or []).lower()
            travellers = int(extracted.get("adults") or 0) + int(extracted.get("children") or 0)
            budget = extracted.get("total_budget_inr")
            ranked = []
            for package in packages:
                score = 0
                reasons = []
                package_text = (package.destination + " " + package.title).lower()
                if destination and (destination in package_text or package_text in destination):
                    score += 3; reasons.append("Destination match")
                if "houseboat" in must and "houseboat" in package_text:
                    score += 3; reasons.append("Houseboat preference")
                if extracted.get("nights") and abs((package.duration_days - 1) - int(extracted["nights"])) <= 1:
                    score += 1; reasons.append("Trip length match")
                if budget and travellers and package.seasons:
                    estimated_total = min(float(season.price_per_person) for season in package.seasons) * travellers
                    if estimated_total <= float(budget):
                        score += 1; reasons.append("Within indicative group budget")
                if score:
                    ranked.append({"package_id": package.id, "title": package.title, "slug": package.slug, "match_score": score, "reasons": reasons})
            ranked.sort(key=lambda item: item["match_score"], reverse=True)
            e.extracted = extracted
            e.ai_suggestions = ranked[:3]
            e.ai_draft = extracted.get("draft_reply", "")
        except Exception:
            e.extracted = {"error":"AI processing failed; manual review required"}
            e.ai_suggestions = []; e.ai_draft = ""
        db.commit()
    finally: db.close()

@app.get("/api/admin/activity")
def admin_activity(limit: int = 50, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.query(ActivityLog).order_by(desc(ActivityLog.created_at)).limit(max(1, min(limit, 100))).all()
    return [{"id": row.id, "actor_id": row.actor_id, "action": row.action, "entity_type": row.entity_type, "entity_id": row.entity_id, "details": row.details, "created_at": row.created_at.isoformat()} for row in rows]

@app.get("/api/admin/enquiries")
def admin_enquiries(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.query(Enquiry).order_by(desc(Enquiry.created_at)).all()
    return [{"id":e.id,"name":e.name,"email":e.email,"phone":e.phone,"message":e.message,"status":e.status,"package_id":e.package_id,"extracted":e.extracted,"ai_suggestions":e.ai_suggestions,"ai_draft":e.ai_draft,"whatsapp_consent":e.whatsapp_consent,"created_at":e.created_at.isoformat()} for e in rows]

@app.patch("/api/admin/enquiries/{enquiry_id}")
def update_enquiry(enquiry_id: int, payload: EnquiryStatusIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    e = db.get(Enquiry, enquiry_id)
    if not e: raise HTTPException(404, "Enquiry not found")
    e.status = payload.status; e.assigned_to = payload.assigned_to
    if payload.extracted is not None:
        e.extracted = {**payload.extracted, "needs_manual_review": False, "reviewed_by_staff": True}
    action = "enquiry.reviewed" if payload.extracted is not None else "enquiry.status_updated"
    db.add(ActivityLog(actor_id=user.id, action=action, entity_type="enquiry", entity_id=e.id, details={"status": payload.status}))
    db.commit()
    return {"id":e.id,"status":e.status,"assigned_to":e.assigned_to}
