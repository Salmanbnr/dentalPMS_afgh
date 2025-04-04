from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Service:
    """Model class for dental services"""
    service_id: Optional[int] = None
    name: str = ""
    description: str = ""
    default_price: float = 0.0
    is_active: bool = True
    last_updated: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create a Service instance from a dictionary (database row)"""
        if not data:
            return None
        
        return cls(
            service_id=data.get('service_id'),
            name=data.get('name', ''),
            description=data.get('description', ''),
            default_price=float(data.get('default_price', 0.0)),
            is_active=bool(data.get('is_active', 1)),
            last_updated=data.get('last_updated')
        )
    
    def to_dict(self) -> dict:
        """Convert the Service instance to a dictionary"""
        return {
            'service_id': self.service_id,
            'name': self.name,
            'description': self.description,
            'default_price': self.default_price,
            'is_active': 1 if self.is_active else 0
        }
    
    def __str__(self) -> str:
        """String representation of the Service"""
        return f"{self.name} (${self.default_price:.2f})"