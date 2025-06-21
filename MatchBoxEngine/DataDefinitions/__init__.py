"""
MatchBoxAIEngine.DataDefinitions - Data classes used internally

Developed and maintained by Aditya Gaur / @xdityagr at Github / adityagaur.home@gmail.com
© 2025 MatchBox AI. All rights reserved.
"""


from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Union, Dict

@dataclass
class Deliverable:
    type: str  # e.g. 'YT shorts', 'Insta story', 'Reel'
    count: Optional[int] = None
    exclusive: Optional[bool] = None

@dataclass
class CreatorRequirement:
    gender: Optional[str] = None
    age_range: Optional[str] = None
    niche: Optional[str] = None
    follower_range: Optional[str] = None
    engagement_min: Optional[float] = None

@dataclass
class CampaignInfo:
    category: str
    products_services: List[str]
    creator_requirements: List[CreatorRequirement] = field(default_factory=list)
    budget_per_creator: Optional[str] = None
    budget_total: Optional[str] = None
    deliverables: List[Deliverable] = field(default_factory=list)
    genre: Optional[str] = None
    followers_open: bool = True
    location: Optional[str] = None
    tat: Optional[datetime] = None
    notes: Optional[str] = None
    num_creators_target: Optional[Dict[str,int]] = field(default_factory=dict)
    platforms: List[str] = field(default_factory=lambda: ['YouTube','Instagram'])

    def is_urgent(self) -> bool:
        if not self.tat:
            return False
        return self.tat <= datetime.now()

    def summary(self):
        return {
            "category": self.category,
            "budget": self.budget_total or self.budget_per_creator,
            "deliverables": [f"{d.count} x {d.type}" for d in self.deliverables],
            "TAT": self.tat.isoformat() if self.tat else None,
        }
