from pymongo import MongoClient
from pymongo.collection import Collection
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/cold_email_db')
            self.client = MongoClient(mongo_url)
            self.db = self.client.get_default_database()
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
            # Create indexes
            self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Contacts indexes
            self.db.contacts.create_index("email", unique=True)
            self.db.contacts.create_index("status")
            self.db.contacts.create_index("tags")
            self.db.contacts.create_index("created_at")
            
            # Campaigns indexes
            self.db.campaigns.create_index("status")
            self.db.campaigns.create_index("created_at")
            self.db.campaigns.create_index("scheduled_at")
            
            # Campaign emails indexes
            self.db.campaign_emails.create_index("campaign_id")
            self.db.campaign_emails.create_index("contact_id")
            self.db.campaign_emails.create_index("email")
            self.db.campaign_emails.create_index("status")
            self.db.campaign_emails.create_index("sent_at")
            
            # Analytics indexes
            self.db.email_analytics.create_index("campaign_id")
            self.db.email_analytics.create_index("email_id")
            self.db.email_analytics.create_index("event_type")
            self.db.email_analytics.create_index("event_timestamp")
            
            # Unsubscribes indexes
            self.db.unsubscribes.create_index("email", unique=True)
            self.db.unsubscribes.create_index("unsubscribed_at")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def get_collection(self, name: str) -> Collection:
        """Get a collection by name"""
        return self.db[name]
    
    # Contact operations
    def create_contact(self, contact_data: Dict[str, Any]) -> str:
        """Create a new contact"""
        try:
            # Check if contact already exists
            existing = self.db.contacts.find_one({"email": contact_data["email"]})
            if existing:
                if contact_data.get("skip_duplicates", True):
                    return existing["id"]
                else:
                    raise ValueError(f"Contact with email {contact_data['email']} already exists")
            
            result = self.db.contacts.insert_one(contact_data)
            return contact_data["id"]
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            raise
    
    def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get a contact by ID"""
        return self.db.contacts.find_one({"id": contact_id})
    
    def get_contacts(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get contacts with optional filters"""
        query = filters or {}
        return list(self.db.contacts.find(query).skip(offset).limit(limit))
    
    def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> bool:
        """Update a contact"""
        updates["updated_at"] = datetime.now()
        result = self.db.contacts.update_one({"id": contact_id}, {"$set": updates})
        return result.modified_count > 0
    
    def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact"""
        result = self.db.contacts.delete_one({"id": contact_id})
        return result.deleted_count > 0
    
    def bulk_create_contacts(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk create contacts"""
        try:
            created_count = 0
            skipped_count = 0
            errors = []
            
            for contact in contacts:
                try:
                    self.create_contact(contact)
                    created_count += 1
                except ValueError as e:
                    skipped_count += 1
                except Exception as e:
                    errors.append(f"Error creating contact {contact.get('email', 'unknown')}: {e}")
            
            return {
                "created": created_count,
                "skipped": skipped_count,
                "errors": errors
            }
        except Exception as e:
            logger.error(f"Error in bulk contact creation: {e}")
            raise
    
    # Campaign operations
    def create_campaign(self, campaign_data: Dict[str, Any]) -> str:
        """Create a new campaign"""
        try:
            result = self.db.campaigns.insert_one(campaign_data)
            return campaign_data["id"]
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            raise
    
    def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get a campaign by ID"""
        return self.db.campaigns.find_one({"id": campaign_id})
    
    def get_campaigns(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get campaigns with optional filters"""
        query = filters or {}
        return list(self.db.campaigns.find(query).sort("created_at", -1).skip(offset).limit(limit))
    
    def update_campaign(self, campaign_id: str, updates: Dict[str, Any]) -> bool:
        """Update a campaign"""
        updates["updated_at"] = datetime.now()
        result = self.db.campaigns.update_one({"id": campaign_id}, {"$set": updates})
        return result.modified_count > 0
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign"""
        # Also delete associated campaign emails
        self.db.campaign_emails.delete_many({"campaign_id": campaign_id})
        result = self.db.campaigns.delete_one({"id": campaign_id})
        return result.deleted_count > 0
    
    # Campaign email operations
    def create_campaign_email(self, email_data: Dict[str, Any]) -> str:
        """Create a campaign email"""
        try:
            result = self.db.campaign_emails.insert_one(email_data)
            return email_data["id"]
        except Exception as e:
            logger.error(f"Error creating campaign email: {e}")
            raise
    
    def get_campaign_emails(self, campaign_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get campaign emails"""
        query = {"campaign_id": campaign_id}
        if status:
            query["status"] = status
        return list(self.db.campaign_emails.find(query))
    
    def update_campaign_email(self, email_id: str, updates: Dict[str, Any]) -> bool:
        """Update a campaign email"""
        result = self.db.campaign_emails.update_one({"id": email_id}, {"$set": updates})
        return result.modified_count > 0
    
    # Template operations
    def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create an email template"""
        try:
            result = self.db.email_templates.insert_one(template_data)
            return template_data["id"]
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a template by ID"""
        return self.db.email_templates.find_one({"id": template_id})
    
    def get_templates(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get templates with optional filters"""
        query = filters or {}
        return list(self.db.email_templates.find(query).sort("created_at", -1))
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Update a template"""
        updates["updated_at"] = datetime.now()
        result = self.db.email_templates.update_one({"id": template_id}, {"$set": updates})
        return result.modified_count > 0
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        result = self.db.email_templates.delete_one({"id": template_id})
        return result.deleted_count > 0
    
    # Analytics operations
    def create_analytics_event(self, event_data: Dict[str, Any]) -> str:
        """Create an analytics event"""
        try:
            result = self.db.email_analytics.insert_one(event_data)
            return event_data["id"]
        except Exception as e:
            logger.error(f"Error creating analytics event: {e}")
            raise
    
    def get_campaign_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """Get analytics for a campaign"""
        pipeline = [
            {"$match": {"campaign_id": campaign_id}},
            {"$group": {
                "_id": "$event_type",
                "count": {"$sum": 1}
            }}
        ]
        
        result = list(self.db.email_analytics.aggregate(pipeline))
        
        analytics = {
            "opens": 0,
            "clicks": 0,
            "bounces": 0,
            "unsubscribes": 0
        }
        
        for item in result:
            if item["_id"] == "open":
                analytics["opens"] = item["count"]
            elif item["_id"] == "click":
                analytics["clicks"] = item["count"]
            elif item["_id"] == "bounce":
                analytics["bounces"] = item["count"]
            elif item["_id"] == "unsubscribe":
                analytics["unsubscribes"] = item["count"]
        
        return analytics
    
    # Unsubscribe operations
    def create_unsubscribe(self, unsubscribe_data: Dict[str, Any]) -> str:
        """Create an unsubscribe record"""
        try:
            # Check if already unsubscribed
            existing = self.db.unsubscribes.find_one({"email": unsubscribe_data["email"]})
            if existing:
                return existing["id"]
            
            result = self.db.unsubscribes.insert_one(unsubscribe_data)
            
            # Update contact status
            self.update_contact_by_email(unsubscribe_data["email"], {
                "status": "unsubscribed",
                "unsubscribed_at": unsubscribe_data["unsubscribed_at"]
            })
            
            return unsubscribe_data["id"]
        except Exception as e:
            logger.error(f"Error creating unsubscribe: {e}")
            raise
    
    def update_contact_by_email(self, email: str, updates: Dict[str, Any]) -> bool:
        """Update a contact by email"""
        updates["updated_at"] = datetime.now()
        result = self.db.contacts.update_one({"email": email}, {"$set": updates})
        return result.modified_count > 0
    
    def is_unsubscribed(self, email: str) -> bool:
        """Check if an email is unsubscribed"""
        return self.db.unsubscribes.find_one({"email": email}) is not None
    
    # Statistics operations
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            stats = {
                "total_contacts": self.db.contacts.count_documents({}),
                "active_contacts": self.db.contacts.count_documents({"status": "active"}),
                "total_campaigns": self.db.campaigns.count_documents({}),
                "active_campaigns": self.db.campaigns.count_documents({"status": {"$in": ["sending", "scheduled"]}}),
                "total_emails_sent": self.db.campaign_emails.count_documents({"status": {"$in": ["sent", "delivered", "opened", "clicked"]}}),
                "total_opens": self.db.email_analytics.count_documents({"event_type": "open"}),
                "total_clicks": self.db.email_analytics.count_documents({"event_type": "click"}),
                "total_unsubscribes": self.db.unsubscribes.count_documents({})
            }
            
            # Calculate rates
            if stats["total_emails_sent"] > 0:
                stats["overall_open_rate"] = (stats["total_opens"] / stats["total_emails_sent"]) * 100
                stats["overall_click_rate"] = (stats["total_clicks"] / stats["total_emails_sent"]) * 100
            else:
                stats["overall_open_rate"] = 0
                stats["overall_click_rate"] = 0
            
            return stats
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

# Global database instance
db_manager = DatabaseManager()