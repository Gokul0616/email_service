"""
Pydantic models for domain registration system
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DomainStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    TRANSFERRED = "transferred"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class DNSRecordType(str, Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"
    NS = "NS"
    PTR = "PTR"
    SRV = "SRV"

class RegistrantInfo(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    address: str = Field(..., min_length=5, max_length=200)
    city: str = Field(..., min_length=2, max_length=50)
    state: str = Field(..., min_length=2, max_length=50)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field(..., min_length=2, max_length=50)
    organization: Optional[str] = Field(None, max_length=100)
    privacy_protection: bool = Field(default=True)

    @validator('phone')
    def validate_phone(cls, v):
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, v))
        if len(digits) < 10:
            raise ValueError('Phone number must contain at least 10 digits')
        return v

    @validator('country')
    def validate_country(cls, v):
        # Simple country validation - in real system, use ISO country codes
        if len(v) < 2:
            raise ValueError('Country must be at least 2 characters')
        return v.upper()

class DomainSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=63)
    
    @validator('query')
    def validate_query(cls, v):
        # Remove spaces and convert to lowercase
        v = v.strip().lower()
        # Check for invalid characters
        if not v.replace('-', '').replace('.', '').isalnum():
            raise ValueError('Domain name can only contain letters, numbers, and hyphens')
        return v

class DomainRegistrationRequest(BaseModel):
    domain: str = Field(..., min_length=4, max_length=253)
    years: int = Field(1, ge=1, le=10)
    registrant_info: RegistrantInfo
    auto_renew: bool = Field(default=True)
    
    @validator('domain')
    def validate_domain(cls, v):
        v = v.strip().lower()
        if not v.count('.') >= 1:
            raise ValueError('Domain must contain at least one dot')
        return v

class DomainTransferRequest(BaseModel):
    domain: str = Field(..., min_length=4, max_length=253)
    auth_code: str = Field(..., min_length=8, max_length=32)
    new_registrant_info: RegistrantInfo
    
    @validator('domain')
    def validate_domain(cls, v):
        return v.strip().lower()

class DomainRenewalRequest(BaseModel):
    domain: str = Field(..., min_length=4, max_length=253)
    years: int = Field(1, ge=1, le=10)
    
    @validator('domain')
    def validate_domain(cls, v):
        return v.strip().lower()

class DNSRecord(BaseModel):
    name: str = Field(..., max_length=253)
    type: DNSRecordType
    value: str = Field(..., min_length=1, max_length=4096)
    ttl: int = Field(3600, ge=300, le=86400)  # 5 minutes to 24 hours
    priority: Optional[int] = Field(None, ge=0, le=65535)  # For MX records
    
    @validator('name')
    def validate_name(cls, v):
        if v == '':
            return '@'
        return v.strip()
    
    @validator('value')
    def validate_value(cls, v, values):
        record_type = values.get('type')
        v = v.strip()
        
        if record_type == DNSRecordType.A:
            # Basic IPv4 validation
            parts = v.split('.')
            if len(parts) != 4:
                raise ValueError('Invalid IPv4 address')
            for part in parts:
                if not part.isdigit() or not 0 <= int(part) <= 255:
                    raise ValueError('Invalid IPv4 address')
        
        elif record_type == DNSRecordType.MX:
            # MX record format: "priority hostname"
            parts = v.split(' ', 1)
            if len(parts) != 2:
                raise ValueError('MX record must be in format "priority hostname"')
            try:
                priority = int(parts[0])
                if not 0 <= priority <= 65535:
                    raise ValueError('MX priority must be between 0 and 65535')
            except ValueError:
                raise ValueError('Invalid MX priority')
        
        return v

class DNSRecordRequest(BaseModel):
    domain: str = Field(..., min_length=4, max_length=253)
    record: DNSRecord
    
    @validator('domain')
    def validate_domain(cls, v):
        return v.strip().lower()

class DNSRecordUpdate(BaseModel):
    domain: str = Field(..., min_length=4, max_length=253)
    record_id: str = Field(..., min_length=1)
    record: DNSRecord
    
    @validator('domain')
    def validate_domain(cls, v):
        return v.strip().lower()

class DNSRecordDelete(BaseModel):
    domain: str = Field(..., min_length=4, max_length=253)
    record_id: str = Field(..., min_length=1)
    
    @validator('domain')
    def validate_domain(cls, v):
        return v.strip().lower()

class PaymentRequest(BaseModel):
    payment_id: str = Field(..., min_length=1)
    payment_method: str = Field('credit_card', regex='^(credit_card|paypal|bank_transfer)$')
    card_number: Optional[str] = Field(None, min_length=13, max_length=19)
    card_expiry: Optional[str] = Field(None, regex=r'^\d{2}/\d{2}$')
    card_cvv: Optional[str] = Field(None, min_length=3, max_length=4)
    card_name: Optional[str] = Field(None, min_length=1, max_length=100)
    
    @validator('card_number')
    def validate_card_number(cls, v, values):
        if values.get('payment_method') == 'credit_card' and not v:
            raise ValueError('Card number is required for credit card payments')
        if v:
            # Remove spaces and hyphens
            v = v.replace(' ', '').replace('-', '')
            if not v.isdigit():
                raise ValueError('Card number must contain only digits')
        return v

class DomainSearchResult(BaseModel):
    domain: str
    tld: str
    available: bool
    price: float
    renewal_price: float
    popular: bool
    message: str

class DomainRegistrationResult(BaseModel):
    registration_id: str
    domain: str
    status: DomainStatus
    payment_id: str
    total_cost: float
    expiration_date: str

class PaymentResult(BaseModel):
    success: bool
    payment_id: str
    status: PaymentStatus
    domain: str
    error: Optional[str] = None

class DomainInfo(BaseModel):
    registration_id: str
    domain: str
    status: DomainStatus
    registration_date: datetime
    expiration_date: datetime
    registrant_info: RegistrantInfo
    auto_renew: bool
    total_cost: float
    years: int

class WHOISInfo(BaseModel):
    domain: str
    registrant: RegistrantInfo
    admin_contact: RegistrantInfo
    tech_contact: RegistrantInfo
    billing_contact: RegistrantInfo
    registrar: str
    creation_date: datetime
    expiration_date: datetime
    updated_date: datetime
    status: List[str]
    name_servers: List[str]
    privacy_protection: bool

class DomainAnalytics(BaseModel):
    total_domains: int
    active_domains: int
    pending_domains: int
    total_revenue: float
    popular_tlds: List[Dict[str, Any]]

class BulkDomainCheck(BaseModel):
    domains: List[str] = Field(..., min_items=1, max_items=100)
    
    @validator('domains')
    def validate_domains(cls, v):
        validated_domains = []
        for domain in v:
            domain = domain.strip().lower()
            if len(domain) < 4:
                raise ValueError(f'Domain {domain} is too short')
            validated_domains.append(domain)
        return validated_domains

class BulkDomainResult(BaseModel):
    domain: str
    available: bool
    price: Optional[float] = None
    message: str

class DomainPricing(BaseModel):
    tld: str
    price: float
    renewal_price: float
    popular: bool
    currency: str = "USD"

class DomainFilter(BaseModel):
    status: Optional[DomainStatus] = None
    registrant_email: Optional[EmailStr] = None
    expiring_soon: Optional[bool] = None  # Domains expiring in next 30 days
    auto_renew: Optional[bool] = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class DomainUpdateRequest(BaseModel):
    domain: str = Field(..., min_length=4, max_length=253)
    registrant_info: Optional[RegistrantInfo] = None
    auto_renew: Optional[bool] = None
    
    @validator('domain')
    def validate_domain(cls, v):
        return v.strip().lower()