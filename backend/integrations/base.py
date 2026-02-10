"""
PHASE 2 STUB: Base classes for placement platform integrations.

This module defines the abstract interface for placement tracking
integrations to be implemented in Phase 2.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class PlacementData:
    """
    Standardized placement data structure.
    To be expanded in Phase 2.
    """
    external_id: str
    source_platform: str
    status: str  # inquiry, tour_scheduled, placed, lost
    
    # Contact info
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    # Placement details
    resident_name: Optional[str] = None
    care_level: Optional[str] = None  # independent, assisted, memory_care
    move_in_date: Optional[datetime] = None
    
    # Tracking
    inquiry_date: Optional[datetime] = None
    tour_date: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    
    # Financial
    monthly_rate: Optional[float] = None
    referral_fee: Optional[float] = None
    
    # Raw data
    raw_json: Optional[Dict[str, Any]] = None


class PlacementPlatform(ABC):
    """
    Abstract base class for placement platform integrations.
    
    PHASE 2: This will be implemented for platforms like:
    - A Place for Mom (placement referrals)
    - Caring.com (placement referrals)
    - Direct web inquiries
    - Phone call tracking systems
    
    Each implementation should handle:
    - Fetching placement/inquiry data from the platform
    - Standardizing data into PlacementData format
    - Tracking conversion funnel stages
    - Syncing status back to source platform (where supported)
    """
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name."""
        pass
    
    @abstractmethod
    def fetch_inquiries(self) -> List[PlacementData]:
        """
        Fetch new inquiries from the platform.
        
        Returns:
            List of standardized placement data
        """
        pass
    
    @abstractmethod
    def update_status(
        self, 
        external_id: str, 
        status: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update the status of a placement on the source platform.
        
        Args:
            external_id: Platform-specific identifier
            status: New status
            notes: Optional status notes
            
        Returns:
            True if update successful
        """
        pass
    
    def sync(self) -> Dict[str, Any]:
        """
        Perform full sync with the platform.
        
        Returns:
            Sync result summary
        """
        # Default implementation - to be overridden
        inquiries = self.fetch_inquiries()
        return {
            "platform": self.platform_name,
            "inquiries_fetched": len(inquiries),
            "sync_time": datetime.utcnow().isoformat(),
        }


class APlaceForMomPlacementStub(PlacementPlatform):
    """
    STUB: A Place for Mom placement integration.
    
    Phase 2 will implement:
    - API integration with APFM partner portal
    - Inquiry tracking
    - Conversion tracking
    - Referral fee reconciliation
    """
    
    @property
    def platform_name(self) -> str:
        return "aplaceformom_placements"
    
    def fetch_inquiries(self) -> List[PlacementData]:
        # STUB
        return []
    
    def update_status(
        self, 
        external_id: str, 
        status: str,
        notes: Optional[str] = None
    ) -> bool:
        # STUB
        return False


class CaringComPlacementStub(PlacementPlatform):
    """
    STUB: Caring.com placement integration.
    
    Phase 2 will implement:
    - API integration with Caring.com partner portal
    - Lead tracking
    - Conversion tracking
    """
    
    @property
    def platform_name(self) -> str:
        return "caring_placements"
    
    def fetch_inquiries(self) -> List[PlacementData]:
        # STUB
        return []
    
    def update_status(
        self, 
        external_id: str, 
        status: str,
        notes: Optional[str] = None
    ) -> bool:
        # STUB
        return False
