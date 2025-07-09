"""
Custom Domain Registration System
Provides complete domain management functionality without external APIs
"""

import re
import uuid
import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, EmailStr, validator
from pymongo import MongoClient
import os
from email_validator import validate_email, EmailNotValidError

class DomainRegistrationSystem:
    """Custom domain registration system with built-in TLD support"""
    
    def __init__(self):
        self.mongo_client = MongoClient(os.getenv('MONGO_URL'))
        self.db = self.mongo_client.get_database("cold_email_db")
        
        # Collections
        self.domains = self.db.registered_domains
        self.dns_records = self.db.dns_records
        self.whois_info = self.db.whois_info
        self.payments = self.db.domain_payments
        self.pricing = self.db.domain_pricing
        
        # Initialize TLD pricing and availability
        self.init_tld_pricing()
        
        # Reserved domains that cannot be registered
        self.reserved_domains = {
            'google.com', 'facebook.com', 'twitter.com', 'amazon.com',
            'microsoft.com', 'apple.com', 'youtube.com', 'instagram.com',
            'linkedin.com', 'github.com', 'stackoverflow.com', 'reddit.com',
            'netflix.com', 'spotify.com', 'dropbox.com', 'zoom.us',
            'localhost', 'example.com', 'example.org', 'example.net'
        }
    
    def init_tld_pricing(self):
        """Initialize TLD pricing structure"""
        default_pricing = [
            {'tld': '.com', 'price': 12.99, 'renewal_price': 14.99, 'popular': True},
            {'tld': '.net', 'price': 14.99, 'renewal_price': 16.99, 'popular': True},
            {'tld': '.org', 'price': 13.99, 'renewal_price': 15.99, 'popular': True},
            {'tld': '.info', 'price': 2.99, 'renewal_price': 19.99, 'popular': False},
            {'tld': '.biz', 'price': 15.99, 'renewal_price': 17.99, 'popular': False},
            {'tld': '.me', 'price': 19.99, 'renewal_price': 21.99, 'popular': False},
            {'tld': '.co', 'price': 29.99, 'renewal_price': 31.99, 'popular': True},
            {'tld': '.io', 'price': 39.99, 'renewal_price': 41.99, 'popular': True},
            {'tld': '.app', 'price': 16.99, 'renewal_price': 18.99, 'popular': False},
            {'tld': '.dev', 'price': 14.99, 'renewal_price': 16.99, 'popular': False},
            {'tld': '.online', 'price': 0.99, 'renewal_price': 34.99, 'popular': False},
            {'tld': '.store', 'price': 2.99, 'renewal_price': 59.99, 'popular': False},
            {'tld': '.tech', 'price': 4.99, 'renewal_price': 54.99, 'popular': False},
            {'tld': '.ai', 'price': 99.99, 'renewal_price': 199.99, 'popular': False},
            {'tld': '.xyz', 'price': 1.99, 'renewal_price': 13.99, 'popular': False},
        ]
        
        # Check if pricing exists, if not initialize
        if self.pricing.count_documents({}) == 0:
            self.pricing.insert_many(default_pricing)
    
    def is_valid_domain(self, domain: str) -> bool:
        """Validate domain format"""
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.([a-zA-Z]{2,}|[a-zA-Z]{2,}\.[a-zA-Z]{2,})$'
        return re.match(domain_pattern, domain.lower()) is not None
    
    def get_tld_from_domain(self, domain: str) -> str:
        """Extract TLD from domain"""
        parts = domain.lower().split('.')
        if len(parts) >= 2:
            return '.' + parts[-1]
        return ''
    
    def is_domain_available(self, domain: str) -> Tuple[bool, str]:
        """Check if domain is available for registration"""
        domain = domain.lower().strip()
        
        # Validate domain format
        if not self.is_valid_domain(domain):
            return False, "Invalid domain format"
        
        # Check if domain is reserved
        if domain in self.reserved_domains:
            return False, "Domain is reserved and cannot be registered"
        
        # Check if domain is already registered
        existing = self.domains.find_one({"domain": domain, "status": {"$in": ["active", "pending"]}})
        if existing:
            return False, "Domain is already registered"
        
        # Check if TLD is supported
        tld = self.get_tld_from_domain(domain)
        pricing_info = self.pricing.find_one({"tld": tld})
        if not pricing_info:
            return False, f"TLD {tld} is not supported"
        
        return True, "Domain is available"
    
    def get_domain_pricing(self, domain: str) -> Optional[Dict]:
        """Get pricing information for a domain"""
        tld = self.get_tld_from_domain(domain)
        return self.pricing.find_one({"tld": tld})
    
    def search_domains(self, query: str) -> List[Dict]:
        """Search for available domains with different TLDs"""
        base_name = query.lower().strip()
        
        # Remove existing TLD if present
        if '.' in base_name:
            base_name = base_name.split('.')[0]
        
        # Get all available TLDs
        tlds = list(self.pricing.find({}).sort("price", 1))
        
        results = []
        for tld_info in tlds:
            domain = f"{base_name}{tld_info['tld']}"
            is_available, message = self.is_domain_available(domain)
            
            results.append({
                'domain': domain,
                'tld': tld_info['tld'],
                'available': is_available,
                'price': tld_info['price'],
                'renewal_price': tld_info['renewal_price'],
                'popular': tld_info.get('popular', False),
                'message': message
            })
        
        return results
    
    def generate_payment_id(self) -> str:
        """Generate unique payment ID"""
        return f"PAY_{uuid.uuid4().hex[:12].upper()}"
    
    def register_domain(self, domain: str, registrant_info: Dict, years: int = 1) -> Dict:
        """Register a new domain"""
        domain = domain.lower().strip()
        
        # Check availability
        is_available, message = self.is_domain_available(domain)
        if not is_available:
            raise ValueError(f"Cannot register domain: {message}")
        
        # Get pricing
        pricing_info = self.get_domain_pricing(domain)
        if not pricing_info:
            raise ValueError("Pricing information not found")
        
        # Calculate total cost
        total_cost = pricing_info['price'] * years
        
        # Generate registration ID
        registration_id = str(uuid.uuid4())
        payment_id = self.generate_payment_id()
        
        # Create domain record
        domain_record = {
            'registration_id': registration_id,
            'domain': domain,
            'registrant_info': registrant_info,
            'status': 'pending',
            'registration_date': datetime.utcnow(),
            'expiration_date': datetime.utcnow() + timedelta(days=365 * years),
            'years': years,
            'total_cost': total_cost,
            'payment_id': payment_id,
            'payment_status': 'pending',
            'auto_renew': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Insert domain record
        result = self.domains.insert_one(domain_record)
        
        # Create payment record
        payment_record = {
            'payment_id': payment_id,
            'registration_id': registration_id,
            'domain': domain,
            'amount': total_cost,
            'currency': 'USD',
            'status': 'pending',
            'payment_method': 'credit_card',
            'created_at': datetime.utcnow()
        }
        
        self.payments.insert_one(payment_record)
        
        # Initialize default DNS records
        self.create_default_dns_records(domain, registration_id)
        
        # Create WHOIS record
        self.create_whois_record(domain, registrant_info, registration_id)
        
        return {
            'registration_id': registration_id,
            'domain': domain,
            'status': 'pending',
            'payment_id': payment_id,
            'total_cost': total_cost,
            'expiration_date': domain_record['expiration_date'].isoformat()
        }
    
    def create_default_dns_records(self, domain: str, registration_id: str):
        """Create default DNS records for a domain"""
        default_records = [
            {
                'domain': domain,
                'registration_id': registration_id,
                'name': '@',
                'type': 'A',
                'value': '192.168.1.1',  # Default parking IP
                'ttl': 3600,
                'created_at': datetime.utcnow()
            },
            {
                'domain': domain,
                'registration_id': registration_id,
                'name': 'www',
                'type': 'CNAME',
                'value': domain,
                'ttl': 3600,
                'created_at': datetime.utcnow()
            },
            {
                'domain': domain,
                'registration_id': registration_id,
                'name': '@',
                'type': 'MX',
                'value': f'10 mail.{domain}',
                'ttl': 3600,
                'created_at': datetime.utcnow()
            }
        ]
        
        self.dns_records.insert_many(default_records)
    
    def create_whois_record(self, domain: str, registrant_info: Dict, registration_id: str):
        """Create WHOIS record for domain"""
        whois_record = {
            'domain': domain,
            'registration_id': registration_id,
            'registrant': registrant_info,
            'admin_contact': registrant_info,
            'tech_contact': registrant_info,
            'billing_contact': registrant_info,
            'registrar': 'Custom Domain Registry',
            'creation_date': datetime.utcnow(),
            'expiration_date': datetime.utcnow() + timedelta(days=365),
            'updated_date': datetime.utcnow(),
            'status': ['clientTransferProhibited'],
            'name_servers': [f'ns1.{domain}', f'ns2.{domain}'],
            'privacy_protection': registrant_info.get('privacy_protection', False)
        }
        
        self.whois_info.insert_one(whois_record)
    
    def process_payment(self, payment_id: str, payment_method: str = 'credit_card') -> Dict:
        """Process domain registration payment"""
        payment = self.payments.find_one({'payment_id': payment_id})
        if not payment:
            raise ValueError("Payment not found")
        
        if payment['status'] != 'pending':
            raise ValueError("Payment already processed")
        
        # Simulate payment processing
        # In a real system, this would integrate with payment processors
        success = True  # For simulation, always successful
        
        if success:
            # Update payment status
            self.payments.update_one(
                {'payment_id': payment_id},
                {
                    '$set': {
                        'status': 'completed',
                        'processed_at': datetime.utcnow(),
                        'payment_method': payment_method
                    }
                }
            )
            
            # Activate domain
            self.domains.update_one(
                {'registration_id': payment['registration_id']},
                {
                    '$set': {
                        'status': 'active',
                        'payment_status': 'completed',
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            return {
                'success': True,
                'payment_id': payment_id,
                'status': 'completed',
                'domain': payment['domain']
            }
        else:
            # Update payment status as failed
            self.payments.update_one(
                {'payment_id': payment_id},
                {
                    '$set': {
                        'status': 'failed',
                        'processed_at': datetime.utcnow()
                    }
                }
            )
            
            return {
                'success': False,
                'payment_id': payment_id,
                'status': 'failed',
                'error': 'Payment processing failed'
            }
    
    def get_user_domains(self, user_email: str) -> List[Dict]:
        """Get all domains registered by a user"""
        domains = list(self.domains.find(
            {'registrant_info.email': user_email},
            {'_id': 0}
        ).sort('registration_date', -1))
        
        return domains
    
    def get_domain_info(self, domain: str) -> Optional[Dict]:
        """Get detailed information about a domain"""
        return self.domains.find_one({'domain': domain.lower()}, {'_id': 0})
    
    def renew_domain(self, domain: str, years: int = 1) -> Dict:
        """Renew domain registration"""
        domain_info = self.get_domain_info(domain)
        if not domain_info:
            raise ValueError("Domain not found")
        
        if domain_info['status'] != 'active':
            raise ValueError("Domain is not active")
        
        # Get pricing
        pricing_info = self.get_domain_pricing(domain)
        if not pricing_info:
            raise ValueError("Pricing information not found")
        
        # Calculate renewal cost
        renewal_cost = pricing_info['renewal_price'] * years
        payment_id = self.generate_payment_id()
        
        # Update expiration date
        current_expiration = domain_info['expiration_date']
        if isinstance(current_expiration, str):
            current_expiration = datetime.fromisoformat(current_expiration)
        
        new_expiration = current_expiration + timedelta(days=365 * years)
        
        # Update domain record
        self.domains.update_one(
            {'domain': domain},
            {
                '$set': {
                    'expiration_date': new_expiration,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # Create renewal payment record
        payment_record = {
            'payment_id': payment_id,
            'registration_id': domain_info['registration_id'],
            'domain': domain,
            'amount': renewal_cost,
            'currency': 'USD',
            'status': 'pending',
            'payment_method': 'credit_card',
            'type': 'renewal',
            'created_at': datetime.utcnow()
        }
        
        self.payments.insert_one(payment_record)
        
        return {
            'domain': domain,
            'payment_id': payment_id,
            'renewal_cost': renewal_cost,
            'new_expiration': new_expiration.isoformat(),
            'years': years
        }
    
    def transfer_domain(self, domain: str, new_registrant_info: Dict, auth_code: str) -> Dict:
        """Transfer domain to new owner"""
        domain_info = self.get_domain_info(domain)
        if not domain_info:
            raise ValueError("Domain not found")
        
        # Validate auth code (in real system, this would be more complex)
        expected_auth_code = hashlib.md5(f"{domain}_{domain_info['registration_id']}".encode()).hexdigest()[:8]
        if auth_code != expected_auth_code:
            raise ValueError("Invalid authorization code")
        
        # Update domain ownership
        self.domains.update_one(
            {'domain': domain},
            {
                '$set': {
                    'registrant_info': new_registrant_info,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # Update WHOIS record
        self.whois_info.update_one(
            {'domain': domain},
            {
                '$set': {
                    'registrant': new_registrant_info,
                    'updated_date': datetime.utcnow()
                }
            }
        )
        
        return {
            'domain': domain,
            'status': 'transferred',
            'new_owner': new_registrant_info['email']
        }
    
    def get_domain_dns_records(self, domain: str) -> List[Dict]:
        """Get DNS records for a domain"""
        return list(self.dns_records.find(
            {'domain': domain.lower()},
            {'_id': 0}
        ).sort('name', 1))
    
    def update_dns_record(self, domain: str, record_id: str, record_data: Dict) -> Dict:
        """Update DNS record"""
        result = self.dns_records.update_one(
            {'domain': domain.lower(), 'record_id': record_id},
            {
                '$set': {
                    **record_data,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise ValueError("DNS record not found")
        
        return {'success': True, 'record_id': record_id}
    
    def add_dns_record(self, domain: str, record_data: Dict) -> Dict:
        """Add new DNS record"""
        record_id = str(uuid.uuid4())
        
        record = {
            'record_id': record_id,
            'domain': domain.lower(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            **record_data
        }
        
        self.dns_records.insert_one(record)
        
        return {'success': True, 'record_id': record_id}
    
    def delete_dns_record(self, domain: str, record_id: str) -> Dict:
        """Delete DNS record"""
        result = self.dns_records.delete_one({
            'domain': domain.lower(),
            'record_id': record_id
        })
        
        if result.deleted_count == 0:
            raise ValueError("DNS record not found")
        
        return {'success': True, 'record_id': record_id}
    
    def get_whois_info(self, domain: str) -> Optional[Dict]:
        """Get WHOIS information for domain"""
        return self.whois_info.find_one({'domain': domain.lower()}, {'_id': 0})
    
    def get_analytics(self) -> Dict:
        """Get domain registration analytics"""
        total_domains = self.domains.count_documents({})
        active_domains = self.domains.count_documents({'status': 'active'})
        pending_domains = self.domains.count_documents({'status': 'pending'})
        
        # Revenue analytics
        total_revenue = list(self.payments.aggregate([
            {'$match': {'status': 'completed'}},
            {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
        ]))
        
        total_revenue = total_revenue[0]['total'] if total_revenue else 0
        
        # Popular TLDs
        popular_tlds = list(self.domains.aggregate([
            {'$group': {'_id': '$domain', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]))
        
        return {
            'total_domains': total_domains,
            'active_domains': active_domains,
            'pending_domains': pending_domains,
            'total_revenue': total_revenue,
            'popular_tlds': popular_tlds
        }