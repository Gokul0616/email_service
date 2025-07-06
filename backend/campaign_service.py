import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from models import (
    Campaign, CampaignEmail, Contact, EmailAnalytics, 
    CampaignStatus, EmailStatus, ContactStatus
)
from database import db_manager
from email_personalization import EmailPersonalizer
from email_validator import validate_email, EmailNotValidError
import re
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CampaignService:
    def __init__(self):
        self.personalizer = EmailPersonalizer()
        self.is_sending = False
        self.current_campaign = None
    
    def create_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new campaign"""
        try:
            # Create campaign object
            campaign = Campaign(**campaign_data)
            
            # Calculate total recipients
            total_recipients = self.calculate_recipients(campaign.contact_lists, campaign.tags)
            campaign.total_recipients = total_recipients
            
            # Save to database
            campaign_id = db_manager.create_campaign(campaign.dict())
            
            logger.info(f"Created campaign {campaign_id} with {total_recipients} recipients")
            
            return {
                "success": True,
                "message": "Campaign created successfully",
                "campaign_id": campaign_id,
                "total_recipients": total_recipients
            }
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return {
                "success": False,
                "message": f"Error creating campaign: {str(e)}"
            }
    
    def calculate_recipients(self, contact_lists: List[str], tags: List[str]) -> int:
        """Calculate total recipients for a campaign"""
        try:
            # Build query
            query = {"status": "active"}
            
            # Add filters
            if contact_lists:
                query["$or"] = [
                    {"list_id": {"$in": contact_lists}},
                    {"tags": {"$in": tags}} if tags else {"list_id": {"$in": contact_lists}}
                ]
            elif tags:
                query["tags"] = {"$in": tags}
            
            # Count recipients
            count = db_manager.db.contacts.count_documents(query)
            return count
        except Exception as e:
            logger.error(f"Error calculating recipients: {e}")
            return 0
    
    def get_campaign_recipients(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get all recipients for a campaign"""
        try:
            campaign = db_manager.get_campaign(campaign_id)
            if not campaign:
                return []
            
            # Build query
            query = {"status": "active"}
            
            # Add filters
            if campaign["contact_lists"]:
                query["$or"] = [
                    {"list_id": {"$in": campaign["contact_lists"]}},
                    {"tags": {"$in": campaign["tags"]}} if campaign["tags"] else {"list_id": {"$in": campaign["contact_lists"]}}
                ]
            elif campaign["tags"]:
                query["tags"] = {"$in": campaign["tags"]}
            
            # Get recipients
            recipients = db_manager.get_contacts(query, limit=10000)
            return recipients
        except Exception as e:
            logger.error(f"Error getting campaign recipients: {e}")
            return []
    
    def prepare_campaign_emails(self, campaign_id: str) -> Dict[str, Any]:
        """Prepare individual emails for a campaign"""
        try:
            campaign = db_manager.get_campaign(campaign_id)
            if not campaign:
                return {"success": False, "message": "Campaign not found"}
            
            # Get recipients
            recipients = self.get_campaign_recipients(campaign_id)
            
            if not recipients:
                return {"success": False, "message": "No recipients found for campaign"}
            
            # A/B Testing setup
            ab_test_percentage = campaign.get("ab_test_percentage", 0)
            ab_test_count = 0
            if ab_test_percentage > 0:
                ab_test_count = int(len(recipients) * ab_test_percentage / 100)
            
            # Prepare emails
            emails_created = 0
            for i, recipient in enumerate(recipients):
                try:
                    # Validate email
                    validate_email(recipient["email"])
                    
                    # Check if already unsubscribed
                    if db_manager.is_unsubscribed(recipient["email"]):
                        continue
                    
                    # Determine A/B test variant
                    ab_variant = None
                    if ab_test_percentage > 0 and i < ab_test_count:
                        ab_variant = "B"
                    elif ab_test_percentage > 0:
                        ab_variant = "A"
                    
                    # Personalize content
                    subject = campaign["subject"]
                    html_content = campaign["html_content"]
                    
                    if ab_variant == "B":
                        subject = campaign.get("ab_test_subject_b", subject)
                        html_content = campaign.get("ab_test_content_b", html_content)
                    
                    # Apply personalization
                    personalized_subject = self.personalizer.personalize(subject, recipient)
                    personalized_html = self.personalizer.personalize(html_content, recipient)
                    personalized_text = self.personalizer.personalize(campaign.get("text_content", ""), recipient)
                    
                    # Create campaign email
                    email_data = {
                        "campaign_id": campaign_id,
                        "contact_id": recipient["id"],
                        "email": recipient["email"],
                        "subject": personalized_subject,
                        "html_content": personalized_html,
                        "text_content": personalized_text,
                        "ab_test_variant": ab_variant,
                        "status": "pending"
                    }
                    
                    campaign_email = CampaignEmail(**email_data)
                    db_manager.create_campaign_email(campaign_email.dict())
                    emails_created += 1
                    
                except EmailNotValidError:
                    logger.warning(f"Invalid email address: {recipient['email']}")
                    continue
                except Exception as e:
                    logger.error(f"Error preparing email for {recipient['email']}: {e}")
                    continue
            
            # Update campaign status
            db_manager.update_campaign(campaign_id, {
                "status": "prepared",
                "total_recipients": emails_created
            })
            
            return {
                "success": True,
                "message": f"Prepared {emails_created} emails for campaign",
                "emails_created": emails_created
            }
        except Exception as e:
            logger.error(f"Error preparing campaign emails: {e}")
            return {"success": False, "message": f"Error preparing emails: {str(e)}"}
    
    async def send_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Send a campaign"""
        try:
            campaign = db_manager.get_campaign(campaign_id)
            if not campaign:
                return {"success": False, "message": "Campaign not found"}
            
            if campaign["status"] == "sending":
                return {"success": False, "message": "Campaign is already sending"}
            
            # Update campaign status
            db_manager.update_campaign(campaign_id, {
                "status": "sending",
                "sent_at": datetime.now()
            })
            
            # Get pending emails
            pending_emails = db_manager.get_campaign_emails(campaign_id, "pending")
            
            if not pending_emails:
                return {"success": False, "message": "No pending emails found"}
            
            # Send emails in batches
            batch_size = 10
            sent_count = 0
            failed_count = 0
            
            for i in range(0, len(pending_emails), batch_size):
                batch = pending_emails[i:i + batch_size]
                
                # Send batch
                batch_results = await self.send_email_batch(batch)
                sent_count += batch_results["sent"]
                failed_count += batch_results["failed"]
                
                # Update campaign statistics
                db_manager.update_campaign(campaign_id, {
                    "sent_count": sent_count,
                    "updated_at": datetime.now()
                })
                
                # Small delay between batches to avoid overwhelming
                await asyncio.sleep(1)
            
            # Update final campaign status
            final_status = "completed" if failed_count == 0 else "completed_with_errors"
            db_manager.update_campaign(campaign_id, {
                "status": final_status,
                "completed_at": datetime.now(),
                "sent_count": sent_count
            })
            
            return {
                "success": True,
                "message": f"Campaign completed. Sent: {sent_count}, Failed: {failed_count}",
                "sent_count": sent_count,
                "failed_count": failed_count
            }
        except Exception as e:
            logger.error(f"Error sending campaign: {e}")
            return {"success": False, "message": f"Error sending campaign: {str(e)}"}
    
    async def send_email_batch(self, emails: List[Dict[str, Any]]) -> Dict[str, int]:
        """Send a batch of emails"""
        sent = 0
        failed = 0
        
        for email in emails:
            try:
                # Import here to avoid circular imports
                from server import smtp_client
                
                # Create email message
                from models import EmailMessage
                message = EmailMessage(
                    to_email=email["email"],
                    from_email=email.get("from_email", "noreply@pixelrisewebco.com"),
                    from_name=email.get("from_name", "PixelRise WebCo"),
                    subject=email["subject"],
                    body=email["html_content"],
                    is_html=True
                )
                
                # Send email
                result = smtp_client.send_email(message)
                
                if result.success:
                    # Update email status
                    db_manager.update_campaign_email(email["id"], {
                        "status": "sent",
                        "sent_at": datetime.now()
                    })
                    sent += 1
                else:
                    # Update email status
                    db_manager.update_campaign_email(email["id"], {
                        "status": "failed"
                    })
                    failed += 1
                    logger.error(f"Failed to send email to {email['email']}: {result.message}")
                
            except Exception as e:
                logger.error(f"Error sending email to {email['email']}: {e}")
                db_manager.update_campaign_email(email["id"], {
                    "status": "failed"
                })
                failed += 1
        
        return {"sent": sent, "failed": failed}
    
    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign statistics"""
        try:
            campaign = db_manager.get_campaign(campaign_id)
            if not campaign:
                return {"success": False, "message": "Campaign not found"}
            
            # Get email statistics
            email_stats = self.get_email_stats(campaign_id)
            
            # Get analytics
            analytics = db_manager.get_campaign_analytics(campaign_id)
            
            # Calculate rates
            total_sent = email_stats["sent"] + email_stats["delivered"] + email_stats["opened"] + email_stats["clicked"]
            
            stats = {
                "campaign_id": campaign_id,
                "campaign_name": campaign["name"],
                "status": campaign["status"],
                "total_recipients": campaign["total_recipients"],
                "sent_count": total_sent,
                "delivered_count": email_stats["delivered"],
                "opened_count": analytics["opens"],
                "clicked_count": analytics["clicks"],
                "bounced_count": analytics["bounces"],
                "unsubscribed_count": analytics["unsubscribes"],
                "failed_count": email_stats["failed"],
                "open_rate": (analytics["opens"] / total_sent * 100) if total_sent > 0 else 0,
                "click_rate": (analytics["clicks"] / total_sent * 100) if total_sent > 0 else 0,
                "bounce_rate": (analytics["bounces"] / total_sent * 100) if total_sent > 0 else 0,
                "unsubscribe_rate": (analytics["unsubscribes"] / total_sent * 100) if total_sent > 0 else 0,
                "created_at": campaign["created_at"],
                "sent_at": campaign.get("sent_at"),
                "completed_at": campaign.get("completed_at")
            }
            
            return {"success": True, "data": stats}
        except Exception as e:
            logger.error(f"Error getting campaign stats: {e}")
            return {"success": False, "message": f"Error getting stats: {str(e)}"}
    
    def get_email_stats(self, campaign_id: str) -> Dict[str, int]:
        """Get email status statistics"""
        try:
            pipeline = [
                {"$match": {"campaign_id": campaign_id}},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            
            result = list(db_manager.db.campaign_emails.aggregate(pipeline))
            
            stats = {
                "pending": 0,
                "sent": 0,
                "delivered": 0,
                "opened": 0,
                "clicked": 0,
                "bounced": 0,
                "failed": 0
            }
            
            for item in result:
                if item["_id"] in stats:
                    stats[item["_id"]] = item["count"]
            
            return stats
        except Exception as e:
            logger.error(f"Error getting email stats: {e}")
            return {}
    
    def schedule_campaign(self, campaign_id: str, scheduled_time: datetime) -> Dict[str, Any]:
        """Schedule a campaign for future sending"""
        try:
            campaign = db_manager.get_campaign(campaign_id)
            if not campaign:
                return {"success": False, "message": "Campaign not found"}
            
            # Update campaign
            db_manager.update_campaign(campaign_id, {
                "status": "scheduled",
                "scheduled_at": scheduled_time
            })
            
            return {
                "success": True,
                "message": f"Campaign scheduled for {scheduled_time}",
                "scheduled_at": scheduled_time
            }
        except Exception as e:
            logger.error(f"Error scheduling campaign: {e}")
            return {"success": False, "message": f"Error scheduling campaign: {str(e)}"}
    
    def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Pause a campaign"""
        try:
            campaign = db_manager.get_campaign(campaign_id)
            if not campaign:
                return {"success": False, "message": "Campaign not found"}
            
            if campaign["status"] not in ["sending", "scheduled"]:
                return {"success": False, "message": "Campaign cannot be paused"}
            
            # Update campaign status
            db_manager.update_campaign(campaign_id, {
                "status": "paused"
            })
            
            return {
                "success": True,
                "message": "Campaign paused successfully"
            }
        except Exception as e:
            logger.error(f"Error pausing campaign: {e}")
            return {"success": False, "message": f"Error pausing campaign: {str(e)}"}
    
    def resume_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Resume a paused campaign"""
        try:
            campaign = db_manager.get_campaign(campaign_id)
            if not campaign:
                return {"success": False, "message": "Campaign not found"}
            
            if campaign["status"] != "paused":
                return {"success": False, "message": "Campaign is not paused"}
            
            # Update campaign status
            db_manager.update_campaign(campaign_id, {
                "status": "sending"
            })
            
            return {
                "success": True,
                "message": "Campaign resumed successfully"
            }
        except Exception as e:
            logger.error(f"Error resuming campaign: {e}")
            return {"success": False, "message": f"Error resuming campaign: {str(e)}"}

# Global campaign service instance
campaign_service = CampaignService()