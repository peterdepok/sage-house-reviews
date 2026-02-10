# Phase 2: Placement Integrations

This directory contains stubs for Phase 2 placement tracking integrations.

## Overview

Phase 2 will add placement/inquiry tracking functionality to complement the review monitoring system. This will enable:

1. **Lead Tracking**: Track inquiries from various sources
2. **Conversion Funnel**: Monitor inquiry → tour → placement pipeline
3. **Referral Management**: Track referral sources and fees
4. **ROI Analysis**: Correlate review performance with placement rates

## Planned Integrations

### A Place for Mom (APFM)

APFM provides placement referrals for senior living communities.

**Planned Features:**
- Fetch new inquiries from APFM partner portal
- Track inquiry status (new, contacted, tour scheduled, placed, lost)
- Sync status updates back to APFM
- Track referral fees and reconciliation

**Requirements:**
- APFM Partner Portal credentials
- API access (may require partnership agreement)

### Caring.com

Caring.com also provides placement referrals.

**Planned Features:**
- Similar to APFM integration
- Inquiry tracking
- Conversion tracking

**Requirements:**
- Caring.com Partner credentials
- API access

### Direct Web Inquiries

Track inquiries from the facility website.

**Planned Features:**
- Form submission tracking
- Lead scoring
- Follow-up automation

### Phone Call Tracking

Integration with call tracking systems (CallRail, etc.)

**Planned Features:**
- Incoming call tracking
- Call recording links
- Conversion attribution

## Data Model

See `models.py` for the `Placement` table stub:

```python
class Placement(Base):
    id: int
    platform_id: int  # Links to platforms table
    external_id: str  # Platform-specific ID
    status: str  # inquiry, tour_scheduled, placed, lost
    source: str
    notes: str
    created_at: datetime
    updated_at: datetime
```

## Implementation Notes

### Base Class

All placement integrations should inherit from `PlacementPlatform`:

```python
from integrations.base import PlacementPlatform, PlacementData

class MyPlatformIntegration(PlacementPlatform):
    @property
    def platform_name(self) -> str:
        return "my_platform"
    
    def fetch_inquiries(self) -> List[PlacementData]:
        # Implementation here
        pass
    
    def update_status(self, external_id: str, status: str, notes: str = None) -> bool:
        # Implementation here
        pass
```

### Configuration

Add platform-specific credentials to `.env`:

```env
# A Place for Mom
APFM_PARTNER_ID=your_partner_id
APFM_API_KEY=your_api_key

# Caring.com
CARING_PARTNER_ID=your_partner_id
CARING_API_KEY=your_api_key
```

## Timeline

Phase 2 is planned after Phase 1 (review tracking) is stable and in production:

1. **Phase 1**: Review aggregation and monitoring (current)
2. **Phase 2**: Placement tracking integrations (future)
3. **Phase 3**: Advanced analytics and reporting

## Contributing

When implementing a new integration:

1. Create a new file in this directory (e.g., `apfm.py`)
2. Inherit from `PlacementPlatform` base class
3. Implement all required abstract methods
4. Add configuration to `.env.example`
5. Update `__init__.py` to export the new class
6. Write tests in `tests/test_integrations.py`
