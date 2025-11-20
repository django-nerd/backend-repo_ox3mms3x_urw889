"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

# Loan app schemas

class Customer(BaseModel):
    """
    Customers collection schema
    Collection name: "customer"
    """
    first_name: str = Field(..., description="Customer first name")
    last_name: str = Field(..., description="Customer last name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")
    notes: Optional[str] = Field(None, description="Additional notes about the customer")

class Partner(BaseModel):
    """
    Referral partners collection schema
    Collection name: "partner"
    """
    name: str = Field(..., description="Partner business or agent name")
    contact_name: Optional[str] = Field(None, description="Primary contact person")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    commission_rate: float = Field(5.0, ge=0, le=100, description="Commission percentage on funded loan amount")
    notes: Optional[str] = Field(None, description="Additional notes")

class Loan(BaseModel):
    """
    Loans collection schema
    Collection name: "loan"
    """
    customer_id: str = Field(..., description="Reference to customer _id as string")
    partner_id: Optional[str] = Field(None, description="Reference to referral partner _id as string")
    amount: float = Field(..., gt=0, description="Loan principal amount")
    status: Literal["applied", "approved", "funded", "rejected", "closed"] = Field("applied", description="Current loan status")
    application_date: Optional[date] = Field(None, description="Date the application was submitted")
    funded_date: Optional[date] = Field(None, description="Date the loan was funded, if funded")
    commission_amount: Optional[float] = Field(None, ge=0, description="Computed commission amount at time of funding")

# Example schemas kept for reference (not used by the app but safe to keep if needed):
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
