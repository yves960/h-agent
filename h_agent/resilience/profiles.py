#!/usr/bin/env python3

import time
from dataclasses import dataclass
from typing import Optional, List
from h_agent.resilience.classify import FailoverReason, get_cooldown

@dataclass
class AuthProfile:
    name: str
    api_key: str
    api_base: str = "https://api.openai.com/v1"
    cooldown_until: float = 0.0
    failure_reason: Optional[FailoverReason] = None
    last_good_at: float = 0.0

class ProfileManager:
    def __init__(self, profiles: Optional[List[AuthProfile]] = None):
        self.profiles: List[AuthProfile] = profiles or []
    
    def select_profile(self) -> Optional[AuthProfile]:
        now = time.time()
        for profile in self.profiles:
            if now >= profile.cooldown_until:
                return profile
        return None
    
    def mark_failure(self, profile: AuthProfile, reason: FailoverReason, cooldown_seconds: Optional[float] = None) -> None:
        if cooldown_seconds is None:
            cooldown_seconds = get_cooldown(reason)
        profile.cooldown_until = time.time() + cooldown_seconds
        profile.failure_reason = reason
    
    def mark_success(self, profile: AuthProfile) -> None:
        profile.failure_reason = None
        profile.last_good_at = time.time()
    
    def add_profile(self, profile: AuthProfile) -> None:
        self.profiles.append(profile)
    
    def remove_profile(self, name: str) -> bool:
        for i, p in enumerate(self.profiles):
            if p.name == name:
                self.profiles.pop(i)
                return True
        return False
    
    def list_profiles(self) -> List[dict]:
        now = time.time()
        return [
            {
                "name": p.name,
                "available": now >= p.cooldown_until,
                "cooldown_remaining": max(0, p.cooldown_until - now),
                "failure_reason": p.failure_reason.value if p.failure_reason else None,
                "last_good_at": p.last_good_at,
            }
            for p in self.profiles
        ]
    
    def get_cooldowns(self) -> List[dict]:
        now = time.time()
        return [
            {
                "name": p.name,
                "cooldown_remaining": max(0, p.cooldown_until - now),
                "failure_reason": p.failure_reason.value if p.failure_reason else None,
            }
            for p in self.profiles
            if now < p.cooldown_until
        ]