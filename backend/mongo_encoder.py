from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import Any

class MongoJSONEncoder(JSONResponse):
    """Custom JSON encoder for MongoDB ObjectId"""
    def render(self, content: Any) -> bytes:
        """Override render to handle ObjectId serialization"""
        return super().render(self.custom_encode(content))
    
    @staticmethod
    def custom_encode(content: Any) -> Any:
        """Custom encoder for MongoDB ObjectId"""
        if isinstance(content, dict):
            return {k: MongoJSONEncoder.custom_encode(v) for k, v in content.items()}
        elif isinstance(content, list):
            return [MongoJSONEncoder.custom_encode(item) for item in content]
        elif isinstance(content, ObjectId):
            return str(content)
        else:
            return content

def custom_jsonable_encoder(obj: Any) -> Any:
    """Custom jsonable_encoder for MongoDB ObjectId"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: custom_jsonable_encoder(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [custom_jsonable_encoder(item) for item in obj]
    else:
        return jsonable_encoder(obj)