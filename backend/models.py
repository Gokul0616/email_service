from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
import uuid
from enum import Enum

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class EmailStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"

class ContactStatus(str, Enum):
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    BLOCKED = "blocked"

class CampaignType(str, Enum):
    REGULAR = "regular"
    AB_TEST = "ab_test"
    DRIP = "drip"

# Contact Models
class Contact(BaseModel):
    id: str = None
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    status: ContactStatus = ContactStatus.ACTIVE
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}
    created_at: datetime = None
    updated_at: datetime = None
    unsubscribed_at: Optional[datetime] = None
    
    def __init__(self, **data):
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('created_at'):
            data['created_at'] = datetime.now()
        if not data.get('updated_at'):
            data['updated_at'] = datetime.now()
        super().__init__(**data)

class ContactList(BaseModel):
    id: str = None
    name: str
    description: Optional[str] = None
    contact_count: int = 0
    tags: List[str] = []
    created_at: datetime = None
    updated_at: datetime = None
    
    def __init__(self, **data):
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('created_at'):
            data['created_at'] = datetime.now()
        if not data.get('updated_at'):
            data['updated_at'] = datetime.now()
        super().__init__(**data)

class ContactImport(BaseModel):
    file_data: List[Dict[str, Any]]
    list_id: Optional[str] = None
    mapping: Dict[str, str]  # CSV column to contact field mapping

# Template Models
class EmailTemplate(BaseModel):
    id: str = None
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    variables: List[str] = []  # List of variable names used in template
    category: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    def __init__(self, **data):
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('created_at'):
            data['created_at'] = datetime.now()
        if not data.get('updated_at'):
            data['updated_at'] = datetime.now()
        super().__init__(**data)

# Campaign Models
class Campaign(BaseModel):
    id: str = None
    name: str
    subject: str
    template_id: Optional[str] = None
    html_content: str
    text_content: Optional[str] = None
    from_email: EmailStr
    from_name: str
    reply_to: Optional[EmailStr] = None
    
    # Campaign settings
    status: CampaignStatus = CampaignStatus.DRAFT
    campaign_type: CampaignType = CampaignType.REGULAR
    
    # Targeting
    contact_lists: List[str] = []  # List of contact list IDs
    tags: List[str] = []  # Target contacts with these tags
    
    # Scheduling
    scheduled_at: Optional[datetime] = None
    send_immediately: bool = False
    
    # A/B Testing
    ab_test_percentage: Optional[int] = None  # Percentage for A/B test
    ab_test_subject_b: Optional[str] = None
    ab_test_content_b: Optional[str] = None
    
    # Statistics
    total_recipients: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    bounced_count: int = 0
    unsubscribed_count: int = 0
    
    created_at: datetime = None
    updated_at: datetime = None
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __init__(self, **data):
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('created_at'):
            data['created_at'] = datetime.now()
        if not data.get('updated_at'):
            data['updated_at'] = datetime.now()
        super().__init__(**data)

class CampaignEmail(BaseModel):
    id: str = None
    campaign_id: str
    contact_id: str
    email: EmailStr
    
    # Content (personalized)
    subject: str
    html_content: str
    text_content: Optional[str] = None
    
    # Status and tracking
    status: EmailStatus = EmailStatus.PENDING
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    
    # Tracking data
    open_count: int = 0
    click_count: int = 0
    tracking_pixel_id: Optional[str] = None
    
    # A/B Testing
    ab_test_variant: Optional[str] = None  # 'A' or 'B'
    
    created_at: datetime = None
    
    def __init__(self, **data):
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('created_at'):
            data['created_at'] = datetime.now()
        if not data.get('tracking_pixel_id'):
            data['tracking_pixel_id'] = str(uuid.uuid4())
        super().__init__(**data)

# Drip Campaign Models
class DripSequence(BaseModel):
    id: str = None
    name: str
    description: Optional[str] = None
    is_active: bool = True
    
    # Trigger settings
    trigger_type: str = "manual"  # manual, signup, tag_added, etc.
    trigger_value: Optional[str] = None
    
    created_at: datetime = None
    updated_at: datetime = None
    
    def __init__(self, **data):
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('created_at'):
            data['created_at'] = datetime.now()
        if not data.get('updated_at'):
            data['updated_at'] = datetime.now()
        super().__init__(**data)

class DripEmail(BaseModel):
    id: str = None
    sequence_id: str
    order: int  # Order in sequence (1, 2, 3, ...)
    
    # Email content
    subject: str
    html_content: str
    text_content: Optional[str] = None
    
    # Timing
    delay_days: int = 0
    delay_hours: int = 0
    
    # Statistics
    sent_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    
    created_at: datetime = None
    updated_at: datetime = None
    
    def __init__(self, **data):
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('created_at'):
            data['created_at'] = datetime.now()
        if not data.get('updated_at'):
            data['updated_at'] = datetime.now()
        super().__init__(**data)

class DripSubscriber(BaseModel):
    id: str = None
    sequence_id: str
    contact_id: str
    email: EmailStr
    
    # Status
    status: str = "active"  # active, paused, completed, unsubscribed
    current_email: int = 1  # Which email in sequence is next
    
    # Timestamps
    subscribed_at: datetime = None
    next_email_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __init__(self, **data):
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('subscribed_at'):
            data['subscribed_at'] = datetime.now()
        super().__init__(**data)

# Analytics Models
class EmailAnalytics(BaseModel):
    id: str = None
    campaign_id: Optional[str] = None
    email_id: str
    
    # Event data
    event_type: str  # open, click, bounce, unsubscribe
    event_timestamp: datetime
    
    # Tracking data
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    click_url: Optional[str] = None
    
    created_at: datetime = None
    
    def __init__(self, **data):
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('created_at'):
            data['created_at'] = datetime.now()
        super().__init__(**data)

class UnsubscribeRequest(BaseModel):
    id: str = None
    email: EmailStr
    campaign_id: Optional[str] = None
    reason: Optional[str] = None
    unsubscribed_at: datetime = None
    
    def __init__(self, **data):
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('unsubscribed_at'):
            data['unsubscribed_at'] = datetime.now()
        super().__init__(**data)

# Request/Response Models
class CampaignCreate(BaseModel):
    name: str
    subject: str
    template_id: Optional[str] = None
    html_content: str
    text_content: Optional[str] = None
    from_email: EmailStr
    from_name: str
    reply_to: Optional[EmailStr] = None
    contact_lists: List[str] = []
    tags: List[str] = []
    scheduled_at: Optional[datetime] = None
    send_immediately: bool = False
    
    # A/B Testing
    ab_test_percentage: Optional[int] = None
    ab_test_subject_b: Optional[str] = None
    ab_test_content_b: Optional[str] = None

class CampaignResponse(BaseModel):
    success: bool
    message: str
    campaign_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class BulkContactImport(BaseModel):
    contacts: List[Dict[str, Any]]
    list_id: Optional[str] = None
    skip_duplicates: bool = True

class CampaignStats(BaseModel):
    campaign_id: str
    total_recipients: int
    sent_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    bounced_count: int
    unsubscribed_count: int
    open_rate: float
    click_rate: float
    bounce_rate: float
    unsubscribe_rate: float