import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Customer as CustomerSchema, Partner as PartnerSchema, Loan as LoanSchema

app = FastAPI(title="Loan Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility: convert Mongo documents to JSON-safe

def serialize_doc(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    # Convert datetime to isoformat
    for k, v in list(doc.items()):
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc


@app.get("/")
def read_root():
    return {"message": "Loan Tracker Backend Ready"}


# =============================
# Customers
# =============================

class CustomerCreate(CustomerSchema):
    pass

@app.post("/api/customers")
def create_customer(payload: CustomerCreate):
    customer_id = create_document("customer", payload)
    return {"id": customer_id}

@app.get("/api/customers")
def list_customers():
    docs = get_documents("customer")
    return [serialize_doc(d) for d in docs]


# =============================
# Partners
# =============================

class PartnerCreate(PartnerSchema):
    pass

@app.post("/api/partners")
def create_partner(payload: PartnerCreate):
    partner_id = create_document("partner", payload)
    return {"id": partner_id}

@app.get("/api/partners")
def list_partners():
    docs = get_documents("partner")
    return [serialize_doc(d) for d in docs]


# =============================
# Loans
# =============================

class LoanCreate(LoanSchema):
    pass

@app.post("/api/loans")
def create_loan(payload: LoanCreate):
    # Basic referential checks
    if payload.customer_id:
        try:
            customer = db.customer.find_one({"_id": ObjectId(payload.customer_id)})
            if not customer:
                raise HTTPException(status_code=400, detail="Invalid customer_id")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid customer_id format")
    if payload.partner_id:
        try:
            partner = db.partner.find_one({"_id": ObjectId(payload.partner_id)})
            if not partner:
                raise HTTPException(status_code=400, detail="Invalid partner_id")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid partner_id format")

    # Compute commission if funded and commission not set
    data = payload.model_dump()
    if data.get("status") == "funded":
        # fetch partner rate
        rate = 0.0
        if data.get("partner_id"):
            p = db.partner.find_one({"_id": ObjectId(data["partner_id"])})
            if p and "commission_rate" in p:
                rate = float(p["commission_rate"]) or 0.0
        commission = round((data["amount"] * rate) / 100.0, 2)
        data["commission_amount"] = commission
        if not data.get("funded_date"):
            data["funded_date"] = datetime.utcnow().date()

    loan_id = create_document("loan", data)
    return {"id": loan_id}

@app.get("/api/loans")
def list_loans(status: Optional[str] = None):
    filt = {"status": status} if status else None
    docs = get_documents("loan", filt)
    # Enrich with customer and partner names if available
    enriched = []
    for d in docs:
        cust = db.customer.find_one({"_id": d.get("customer_id")}) if isinstance(d.get("customer_id"), ObjectId) else None
        part = db.partner.find_one({"_id": d.get("partner_id")}) if isinstance(d.get("partner_id"), ObjectId) else None
        enriched.append(serialize_doc(d))
    return enriched


# =============================
# Utility endpoints
# =============================

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
