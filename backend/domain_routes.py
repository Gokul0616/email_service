"""
FastAPI routes for custom domain registration system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
from bson import ObjectId

from .domain_registration import DomainRegistrationSystem
from .domain_models import (
    DomainSearchRequest, DomainRegistrationRequest, DomainTransferRequest,
    DomainRenewalRequest, DNSRecordRequest, DNSRecordUpdate, DNSRecordDelete,
    PaymentRequest, DomainSearchResult, DomainRegistrationResult,
    PaymentResult, DomainInfo, WHOISInfo, DomainAnalytics, BulkDomainCheck,
    BulkDomainResult, DomainPricing, DomainFilter, DomainUpdateRequest
)

router = APIRouter(prefix="/api/domains", tags=["Domain Registration"])

# Initialize domain registration system
domain_system = DomainRegistrationSystem()

@router.get("/search", response_model=List[DomainSearchResult])
async def search_domains(query: str = Query(..., min_length=1, max_length=63)):
    """Search for available domains with different TLDs"""
    try:
        results = domain_system.search_domains(query)
        return [DomainSearchResult(**result) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-availability")
async def check_domain_availability(domain: str = Query(..., min_length=4, max_length=253)):
    """Check if a specific domain is available"""
    try:
        domain = domain.strip().lower()
        is_available, message = domain_system.is_domain_available(domain)
        pricing = domain_system.get_domain_pricing(domain)
        
        return {
            "domain": domain,
            "available": is_available,
            "message": message,
            "pricing": pricing
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-check", response_model=List[BulkDomainResult])
async def bulk_check_domains(request: BulkDomainCheck):
    """Check availability for multiple domains"""
    try:
        results = []
        for domain in request.domains:
            is_available, message = domain_system.is_domain_available(domain)
            price = None
            if is_available:
                pricing = domain_system.get_domain_pricing(domain)
                price = pricing['price'] if pricing else None
            
            results.append(BulkDomainResult(
                domain=domain,
                available=is_available,
                price=price,
                message=message
            ))
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register", response_model=DomainRegistrationResult)
async def register_domain(request: DomainRegistrationRequest):
    """Register a new domain"""
    try:
        result = domain_system.register_domain(
            domain=request.domain,
            registrant_info=request.registrant_info.dict(),
            years=request.years
        )
        
        return DomainRegistrationResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/payment/process", response_model=PaymentResult)
async def process_payment(request: PaymentRequest):
    """Process domain registration payment"""
    try:
        result = domain_system.process_payment(
            payment_id=request.payment_id,
            payment_method=request.payment_method
        )
        
        return PaymentResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-domains")
async def get_my_domains(user_email: str = Query(...)):
    """Get all domains registered by a user"""
    try:
        domains = domain_system.get_user_domains(user_email)
        return {"domains": domains}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/filter")
async def filter_domains(
    status: Optional[str] = Query(None),
    registrant_email: Optional[str] = Query(None),
    expiring_soon: Optional[bool] = Query(None),
    auto_renew: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Filter domains with various criteria"""
    try:
        # Build filter query
        filter_query = {}
        
        if status:
            filter_query['status'] = status
        if registrant_email:
            filter_query['registrant_info.email'] = registrant_email
        if auto_renew is not None:
            filter_query['auto_renew'] = auto_renew
        if expiring_soon:
            expiry_date = datetime.utcnow() + timedelta(days=30)
            filter_query['expiration_date'] = {'$lt': expiry_date}
        
        # Get filtered domains
        domains = list(domain_system.domains.find(
            filter_query,
            {'_id': 0}
        ).skip(offset).limit(limit).sort('registration_date', -1))
        
        total_count = domain_system.domains.count_documents(filter_query)
        
        return {
            "domains": domains,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{domain}/info")
async def get_domain_info(domain: str = Path(..., min_length=4, max_length=253)):
    """Get detailed information about a domain"""
    try:
        domain = domain.strip().lower()
        info = domain_system.get_domain_info(domain)
        
        if not info:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        return info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{domain}/renew")
async def renew_domain(
    domain: str = Path(..., min_length=4, max_length=253),
    request: DomainRenewalRequest = None
):
    """Renew domain registration"""
    try:
        domain = domain.strip().lower()
        years = request.years if request else 1
        
        result = domain_system.renew_domain(domain, years)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{domain}/transfer")
async def transfer_domain(
    domain: str = Path(..., min_length=4, max_length=253),
    request: DomainTransferRequest = None
):
    """Transfer domain to new owner"""
    try:
        domain = domain.strip().lower()
        
        result = domain_system.transfer_domain(
            domain=domain,
            new_registrant_info=request.new_registrant_info.dict(),
            auth_code=request.auth_code
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{domain}/update")
async def update_domain(
    domain: str = Path(..., min_length=4, max_length=253),
    request: DomainUpdateRequest = None
):
    """Update domain information"""
    try:
        domain = domain.strip().lower()
        
        update_data = {}
        if request.registrant_info:
            update_data['registrant_info'] = request.registrant_info.dict()
        if request.auto_renew is not None:
            update_data['auto_renew'] = request.auto_renew
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        update_data['updated_at'] = datetime.utcnow()
        
        result = domain_system.domains.update_one(
            {'domain': domain},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        return {"success": True, "domain": domain}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{domain}")
async def delete_domain(domain: str = Path(..., min_length=4, max_length=253)):
    """Delete/cancel domain registration"""
    try:
        domain = domain.strip().lower()
        
        # Update domain status to cancelled
        result = domain_system.domains.update_one(
            {'domain': domain},
            {
                '$set': {
                    'status': 'cancelled',
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        return {"success": True, "domain": domain, "status": "cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# DNS Management Routes
@router.get("/{domain}/dns")
async def get_dns_records(domain: str = Path(..., min_length=4, max_length=253)):
    """Get DNS records for a domain"""
    try:
        domain = domain.strip().lower()
        records = domain_system.get_domain_dns_records(domain)
        return {"domain": domain, "records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{domain}/dns")
async def add_dns_record(
    domain: str = Path(..., min_length=4, max_length=253),
    request: DNSRecordRequest = None
):
    """Add DNS record for a domain"""
    try:
        domain = domain.strip().lower()
        
        result = domain_system.add_dns_record(
            domain=domain,
            record_data=request.record.dict()
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{domain}/dns/{record_id}")
async def update_dns_record(
    domain: str = Path(..., min_length=4, max_length=253),
    record_id: str = Path(..., min_length=1),
    request: DNSRecordUpdate = None
):
    """Update DNS record"""
    try:
        domain = domain.strip().lower()
        
        result = domain_system.update_dns_record(
            domain=domain,
            record_id=record_id,
            record_data=request.record.dict()
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{domain}/dns/{record_id}")
async def delete_dns_record(
    domain: str = Path(..., min_length=4, max_length=253),
    record_id: str = Path(..., min_length=1)
):
    """Delete DNS record"""
    try:
        domain = domain.strip().lower()
        
        result = domain_system.delete_dns_record(
            domain=domain,
            record_id=record_id
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WHOIS Routes
@router.get("/{domain}/whois")
async def get_whois_info(domain: str = Path(..., min_length=4, max_length=253)):
    """Get WHOIS information for a domain"""
    try:
        domain = domain.strip().lower()
        whois_info = domain_system.get_whois_info(domain)
        
        if not whois_info:
            raise HTTPException(status_code=404, detail="WHOIS information not found")
        
        return whois_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Pricing Routes
@router.get("/pricing/tlds")
async def get_tld_pricing():
    """Get pricing for all supported TLDs"""
    try:
        pricing = list(domain_system.pricing.find({}, {'_id': 0}).sort('price', 1))
        return {"tlds": pricing}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pricing/{tld}")
async def get_tld_pricing_info(tld: str = Path(..., min_length=2, max_length=10)):
    """Get pricing information for a specific TLD"""
    try:
        if not tld.startswith('.'):
            tld = '.' + tld
        
        pricing = domain_system.pricing.find_one({'tld': tld.lower()}, {'_id': 0})
        
        if not pricing:
            raise HTTPException(status_code=404, detail=f"TLD {tld} not supported")
        
        return pricing
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Routes
@router.get("/analytics/overview")
async def get_domain_analytics():
    """Get domain registration analytics"""
    try:
        analytics = domain_system.get_analytics()
        return DomainAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/revenue")
async def get_revenue_analytics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get revenue analytics for a date range"""
    try:
        match_filter = {'status': 'completed'}
        
        if start_date:
            match_filter['created_at'] = {'$gte': datetime.fromisoformat(start_date)}
        if end_date:
            if 'created_at' not in match_filter:
                match_filter['created_at'] = {}
            match_filter['created_at']['$lt'] = datetime.fromisoformat(end_date)
        
        revenue_data = list(domain_system.payments.aggregate([
            {'$match': match_filter},
            {
                '$group': {
                    '_id': {
                        'year': {'$year': '$created_at'},
                        'month': {'$month': '$created_at'},
                        'day': {'$dayOfMonth': '$created_at'}
                    },
                    'total_revenue': {'$sum': '$amount'},
                    'transaction_count': {'$sum': 1}
                }
            },
            {'$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}}
        ]))
        
        return {"revenue_data": revenue_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/popular-domains")
async def get_popular_domains(limit: int = Query(20, ge=1, le=100)):
    """Get most popular domain names"""
    try:
        popular_domains = list(domain_system.domains.aggregate([
            {'$match': {'status': 'active'}},
            {
                '$group': {
                    '_id': {'$substr': ['$domain', 0, {'$indexOfBytes': ['$domain', '.']}]},
                    'count': {'$sum': 1},
                    'total_revenue': {'$sum': '$total_cost'}
                }
            },
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]))
        
        return {"popular_domains": popular_domains}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Utility Routes
@router.get("/auth-code/{domain}")
async def get_auth_code(domain: str = Path(..., min_length=4, max_length=253)):
    """Get authorization code for domain transfer"""
    try:
        domain = domain.strip().lower()
        domain_info = domain_system.get_domain_info(domain)
        
        if not domain_info:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        # Generate auth code (in real system, this would be more secure)
        import hashlib
        auth_code = hashlib.md5(f"{domain}_{domain_info['registration_id']}".encode()).hexdigest()[:8]
        
        return {"domain": domain, "auth_code": auth_code}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-auth-code")
async def validate_auth_code(domain: str, auth_code: str):
    """Validate authorization code for domain transfer"""
    try:
        domain = domain.strip().lower()
        domain_info = domain_system.get_domain_info(domain)
        
        if not domain_info:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        # Validate auth code
        import hashlib
        expected_auth_code = hashlib.md5(f"{domain}_{domain_info['registration_id']}".encode()).hexdigest()[:8]
        
        valid = auth_code == expected_auth_code
        
        return {"domain": domain, "valid": valid}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))