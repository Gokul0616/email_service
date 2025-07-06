import re
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailPersonalizer:
    """Email personalization service for replacing variables in email content"""
    
    def __init__(self):
        self.variable_pattern = r'\{\{([^}]+)\}\}'
    
    def personalize(self, content: str, contact: Dict[str, Any]) -> str:
        """Replace variables in content with contact data"""
        if not content:
            return content
        
        try:
            # Find all variables in the content
            variables = re.findall(self.variable_pattern, content)
            
            # Replace each variable
            for variable in variables:
                value = self.get_variable_value(variable, contact)
                content = content.replace(f'{{{{{variable}}}}}', str(value))
            
            return content
        except Exception as e:
            logger.error(f"Error personalizing content: {e}")
            return content
    
    def get_variable_value(self, variable: str, contact: Dict[str, Any]) -> str:
        """Get the value for a variable from contact data"""
        variable = variable.strip().lower()
        
        # Standard contact fields
        if variable == 'first_name':
            return contact.get('first_name', '')
        elif variable == 'last_name':
            return contact.get('last_name', '')
        elif variable == 'full_name':
            first = contact.get('first_name', '')
            last = contact.get('last_name', '')
            return f"{first} {last}".strip() or contact.get('email', '').split('@')[0]
        elif variable == 'email':
            return contact.get('email', '')
        elif variable == 'company':
            return contact.get('company', '')
        elif variable == 'phone':
            return contact.get('phone', '')
        
        # Custom fields
        elif variable in contact.get('custom_fields', {}):
            return contact['custom_fields'][variable]
        
        # Date/time variables
        elif variable == 'current_date':
            return datetime.now().strftime('%Y-%m-%d')
        elif variable == 'current_time':
            return datetime.now().strftime('%H:%M')
        elif variable == 'current_datetime':
            return datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Fallback
        else:
            return f"[{variable}]"
    
    def extract_variables(self, content: str) -> List[str]:
        """Extract all variables from content"""
        try:
            variables = re.findall(self.variable_pattern, content)
            return [var.strip() for var in variables]
        except Exception as e:
            logger.error(f"Error extracting variables: {e}")
            return []
    
    def validate_content(self, content: str, required_fields: List[str] = None) -> Dict[str, Any]:
        """Validate content for personalization"""
        try:
            variables = self.extract_variables(content)
            
            # Check for required fields
            missing_fields = []
            if required_fields:
                for field in required_fields:
                    if field not in variables:
                        missing_fields.append(field)
            
            # Check for valid variables
            valid_variables = [
                'first_name', 'last_name', 'full_name', 'email', 'company', 'phone',
                'current_date', 'current_time', 'current_datetime'
            ]
            
            invalid_variables = []
            for var in variables:
                if var.lower() not in valid_variables:
                    # Check if it's a custom field pattern
                    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var):
                        invalid_variables.append(var)
            
            return {
                "valid": len(missing_fields) == 0 and len(invalid_variables) == 0,
                "variables": variables,
                "missing_fields": missing_fields,
                "invalid_variables": invalid_variables
            }
        except Exception as e:
            logger.error(f"Error validating content: {e}")
            return {"valid": False, "error": str(e)}
    
    def get_sample_personalization(self, content: str) -> str:
        """Get a sample of personalized content for preview"""
        sample_contact = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "company": "Example Corp",
            "phone": "+1 (555) 123-4567",
            "custom_fields": {
                "position": "Marketing Manager",
                "industry": "Technology"
            }
        }
        
        return self.personalize(content, sample_contact)
    
    def bulk_personalize(self, content: str, contacts: List[Dict[str, Any]]) -> List[str]:
        """Personalize content for multiple contacts"""
        personalized_content = []
        
        for contact in contacts:
            try:
                personalized = self.personalize(content, contact)
                personalized_content.append(personalized)
            except Exception as e:
                logger.error(f"Error personalizing for contact {contact.get('email', 'unknown')}: {e}")
                personalized_content.append(content)
        
        return personalized_content
    
    def get_personalization_stats(self, content: str) -> Dict[str, Any]:
        """Get statistics about personalization in content"""
        try:
            variables = self.extract_variables(content)
            
            stats = {
                "total_variables": len(variables),
                "unique_variables": len(set(variables)),
                "variable_list": list(set(variables)),
                "personalization_score": min(len(set(variables)) * 10, 100)  # Score out of 100
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting personalization stats: {e}")
            return {"total_variables": 0, "unique_variables": 0, "variable_list": [], "personalization_score": 0}