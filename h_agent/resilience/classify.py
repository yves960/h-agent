#!/usr/bin/env python3

from enum import Enum

class FailoverReason(Enum):
    rate_limit = "rate_limit"
    auth = "auth"
    timeout = "timeout"
    billing = "billing"
    overflow = "overflow"
    unknown = "unknown"

COOLDOWN_SECONDS = {
    FailoverReason.rate_limit: 120,
    FailoverReason.auth: 300,
    FailoverReason.billing: 300,
    FailoverReason.timeout: 60,
    FailoverReason.overflow: 0,
    FailoverReason.unknown: 60,
}

def classify_failure(exc: Exception) -> FailoverReason:
    msg = str(exc).lower()
    
    if "rate" in msg or "429" in msg or "too many requests" in msg:
        return FailoverReason.rate_limit
    if "auth" in msg or "401" in msg or "key" in msg or "unauthorized" in msg:
        return FailoverReason.auth
    if "timeout" in msg or "timed out" in msg or "504" in msg:
        return FailoverReason.timeout
    if "billing" in msg or "quota" in msg or "402" in msg or "payment" in msg:
        return FailoverReason.billing
    if "context" in msg or "token" in msg or "overflow" in msg or "length" in msg:
        return FailoverReason.overflow
    return FailoverReason.unknown

def get_cooldown(reason: FailoverReason) -> float:
    return COOLDOWN_SECONDS.get(reason, 60.0)