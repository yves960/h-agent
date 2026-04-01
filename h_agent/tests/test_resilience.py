#!/usr/bin/env python3
"""
h_agent/tests/test_resilience.py - s09 Resilience TDD Tests

Tests for FailoverReason classification, ProfileManager, and ResilienceRunner.
"""

import time
import pytest
from unittest.mock import MagicMock, patch
from typing import Any

from h_agent.resilience.classify import (
    FailoverReason,
    classify_failure,
    get_cooldown,
    COOLDOWN_SECONDS,
)
from h_agent.resilience.profiles import ProfileManager, AuthProfile
from h_agent.resilience.runner import (
    ResilienceRunner,
    ResilienceResult,
    BASE_RETRY,
    PER_PROFILE,
    MAX_OVERFLOW_COMPACTION,
)


# ============================================================
# classify.py Tests
# ============================================================

class TestClassifyFailure:
    """Tests for classify_failure() - all 6 failure types."""

    def test_rate_limit_with_rate_in_message(self):
        """Rate limit detected by 'rate' keyword."""
        exc = Exception("rate limit exceeded")
        assert classify_failure(exc) == FailoverReason.rate_limit

    def test_rate_limit_with_429(self):
        """Rate limit detected by 429 status code."""
        exc = Exception("error 429 too many requests")
        assert classify_failure(exc) == FailoverReason.rate_limit

    def test_rate_limit_with_too_many_requests(self):
        """Rate limit detected by 'too many requests' phrase."""
        exc = Exception("too many requests in 1 minute")
        assert classify_failure(exc) == FailoverReason.rate_limit

    def test_auth_with_auth_keyword(self):
        """Auth error detected by 'auth' keyword."""
        exc = Exception("authentication failed")
        assert classify_failure(exc) == FailoverReason.auth

    def test_auth_with_401(self):
        """Auth error detected by 401 status code."""
        exc = Exception("HTTP 401 Unauthorized")
        assert classify_failure(exc) == FailoverReason.auth

    def test_auth_with_keyword(self):
        """Auth error detected by 'key' keyword."""
        exc = Exception("invalid api key")
        assert classify_failure(exc) == FailoverReason.auth

    def test_auth_with_unauthorized(self):
        """Auth error detected by 'unauthorized' keyword."""
        exc = Exception("unauthorized access")
        assert classify_failure(exc) == FailoverReason.auth

    def test_timeout_with_timeout_keyword(self):
        """Timeout detected by 'timeout' keyword."""
        exc = Exception("request timeout")
        assert classify_failure(exc) == FailoverReason.timeout

    def test_timeout_with_timed_out(self):
        """Timeout detected by 'timed out' phrase."""
        exc = Exception("connection timed out")
        assert classify_failure(exc) == FailoverReason.timeout

    def test_timeout_with_504(self):
        """Timeout detected by 504 status code."""
        exc = Exception("error 504 gateway timeout")
        assert classify_failure(exc) == FailoverReason.timeout

    def test_billing_with_billing_keyword(self):
        """Billing error detected by 'billing' keyword."""
        exc = Exception("billing problem")
        assert classify_failure(exc) == FailoverReason.billing

    def test_billing_with_quota(self):
        """Billing error detected by 'quota' keyword."""
        exc = Exception("quota exceeded")
        assert classify_failure(exc) == FailoverReason.billing

    def test_billing_with_402(self):
        """Billing error detected by 402 status code."""
        exc = Exception("error 402 payment required")
        assert classify_failure(exc) == FailoverReason.billing

    def test_billing_with_payment(self):
        """Billing error detected by 'payment' keyword."""
        exc = Exception("payment failed")
        assert classify_failure(exc) == FailoverReason.billing

    def test_overflow_with_context(self):
        """Overflow detected by 'context' keyword."""
        exc = Exception("context length exceeded")
        assert classify_failure(exc) == FailoverReason.overflow

    def test_overflow_with_token(self):
        """Overflow detected by 'token' keyword."""
        exc = Exception("token limit reached")
        assert classify_failure(exc) == FailoverReason.overflow

    def test_overflow_with_overflow(self):
        """Overflow detected by 'overflow' keyword."""
        exc = Exception("buffer overflow")
        assert classify_failure(exc) == FailoverReason.overflow

    def test_overflow_with_length(self):
        """Overflow detected by 'length' keyword."""
        exc = Exception("maximum length exceeded")
        assert classify_failure(exc) == FailoverReason.overflow

    def test_unknown_error(self):
        """Unknown errors default to unknown reason."""
        exc = Exception("something went wrong")
        assert classify_failure(exc) == FailoverReason.unknown

    def test_unknown_with_partial_match(self):
        """Messages without known patterns default to unknown."""
        exc = Exception("internal server error 500")
        assert classify_failure(exc) == FailoverReason.unknown

    def test_case_insensitive_matching(self):
        """Classification is case insensitive."""
        exc = Exception("RATE LIMIT ERROR")
        assert classify_failure(exc) == FailoverReason.rate_limit


class TestGetCooldown:
    """Tests for get_cooldown() - correct durations per type."""

    def test_rate_limit_cooldown(self):
        """Rate limit has 120 second cooldown."""
        assert get_cooldown(FailoverReason.rate_limit) == 120

    def test_auth_cooldown(self):
        """Auth has 300 second cooldown."""
        assert get_cooldown(FailoverReason.auth) == 300

    def test_billing_cooldown(self):
        """Billing has 300 second cooldown."""
        assert get_cooldown(FailoverReason.billing) == 300

    def test_timeout_cooldown(self):
        """Timeout has 60 second cooldown."""
        assert get_cooldown(FailoverReason.timeout) == 60

    def test_overflow_cooldown(self):
        """Overflow has 0 second cooldown (no delay)."""
        assert get_cooldown(FailoverReason.overflow) == 0

    def test_unknown_cooldown(self):
        """Unknown has 60 second cooldown."""
        assert get_cooldown(FailoverReason.unknown) == 60

    def test_unknown_reason_default(self):
        """Unknown reason uses 60 second default."""
        assert get_cooldown(FailoverReason.unknown) == 60.0


# ============================================================
# profiles.py Tests
# ============================================================

class TestAuthProfile:
    """Tests for AuthProfile dataclass."""

    def test_auth_profile_creation(self):
        """AuthProfile stores name and api_key."""
        profile = AuthProfile(name="test", api_key="sk-test")
        assert profile.name == "test"
        assert profile.api_key == "sk-test"
        assert profile.api_base == "https://api.openai.com/v1"
        assert profile.cooldown_until == 0.0
        assert profile.failure_reason is None
        assert profile.last_good_at == 0.0

    def test_auth_profile_custom_api_base(self):
        """AuthProfile accepts custom api_base."""
        profile = AuthProfile(
            name="custom",
            api_key="sk-test",
            api_base="https://custom.api.com/v1"
        )
        assert profile.api_base == "https://custom.api.com/v1"


class TestProfileManager:
    """Tests for ProfileManager.select_profile() and state management."""

    def test_select_profile_no_cooldown(self):
        """Select profile returns available profile."""
        profiles = [
            AuthProfile(name="p1", api_key="key1"),
            AuthProfile(name="p2", api_key="key2"),
        ]
        pm = ProfileManager(profiles)
        selected = pm.select_profile()
        assert selected is not None
        assert selected.name == "p1"

    def test_select_profile_skips_cooldown(self):
        """Select profile skips profiles on cooldown."""
        profiles = [
            AuthProfile(name="p1", api_key="key1", cooldown_until=time.time() + 1000),
            AuthProfile(name="p2", api_key="key2"),
        ]
        pm = ProfileManager(profiles)
        selected = pm.select_profile()
        assert selected is not None
        assert selected.name == "p2"

    def test_select_profile_all_cooldown(self):
        """Select profile returns None when all on cooldown."""
        profiles = [
            AuthProfile(name="p1", api_key="key1", cooldown_until=time.time() + 1000),
            AuthProfile(name="p2", api_key="key2", cooldown_until=time.time() + 1000),
        ]
        pm = ProfileManager(profiles)
        selected = pm.select_profile()
        assert selected is None

    def test_select_profile_empty(self):
        """Select profile returns None when no profiles."""
        pm = ProfileManager([])
        assert pm.select_profile() is None

    def test_mark_failure_sets_cooldown(self):
        """Mark failure sets cooldown_until."""
        profile = AuthProfile(name="p1", api_key="key1")
        pm = ProfileManager([profile])
        pm.mark_failure(profile, FailoverReason.rate_limit)
        assert profile.cooldown_until > time.time()
        assert profile.failure_reason == FailoverReason.rate_limit

    def test_mark_failure_custom_cooldown(self):
        """Mark failure accepts custom cooldown override."""
        profile = AuthProfile(name="p1", api_key="key1")
        pm = ProfileManager([profile])
        pm.mark_failure(profile, FailoverReason.rate_limit, cooldown_seconds=5)
        assert profile.cooldown_until == pytest.approx(time.time() + 5, abs=0.5)

    def test_mark_success_clears_failure(self):
        """Mark success clears failure reason."""
        profile = AuthProfile(name="p1", api_key="key1")
        profile.failure_reason = FailoverReason.rate_limit
        pm = ProfileManager([profile])
        pm.mark_success(profile)
        assert profile.failure_reason is None
        assert profile.last_good_at > 0

    def test_add_profile(self):
        """Add profile appends to list."""
        pm = ProfileManager()
        pm.add_profile(AuthProfile(name="p1", api_key="key1"))
        assert len(pm.profiles) == 1
        pm.add_profile(AuthProfile(name="p2", api_key="key2"))
        assert len(pm.profiles) == 2

    def test_remove_profile_existing(self):
        """Remove profile removes by name."""
        profiles = [
            AuthProfile(name="p1", api_key="key1"),
            AuthProfile(name="p2", api_key="key2"),
        ]
        pm = ProfileManager(profiles)
        result = pm.remove_profile("p1")
        assert result is True
        assert len(pm.profiles) == 1
        assert pm.profiles[0].name == "p2"

    def test_remove_profile_not_found(self):
        """Remove profile returns False if not found."""
        profiles = [AuthProfile(name="p1", api_key="key1")]
        pm = ProfileManager(profiles)
        result = pm.remove_profile("nonexistent")
        assert result is False

    def test_list_profiles_status(self):
        """List profiles shows available status."""
        profiles = [
            AuthProfile(name="p1", api_key="key1"),
            AuthProfile(name="p2", api_key="key2", cooldown_until=time.time() + 100),
        ]
        pm = ProfileManager(profiles)
        listing = pm.list_profiles()
        assert len(listing) == 2
        assert listing[0]["name"] == "p1"
        assert listing[0]["available"] is True
        assert listing[1]["name"] == "p2"
        assert listing[1]["available"] is False

    def test_list_profiles_shows_failure_reason(self):
        """List profiles includes failure reason when set."""
        profile = AuthProfile(name="p1", api_key="key1")
        profile.failure_reason = FailoverReason.rate_limit
        pm = ProfileManager([profile])
        listing = pm.list_profiles()
        assert listing[0]["failure_reason"] == "rate_limit"

    def test_get_cooldowns_only(self):
        """Get cooldowns returns only profiles on cooldown."""
        profiles = [
            AuthProfile(name="p1", api_key="key1", cooldown_until=time.time() + 100),
            AuthProfile(name="p2", api_key="key2"),
        ]
        pm = ProfileManager(profiles)
        cooldowns = pm.get_cooldowns()
        assert len(cooldowns) == 1
        assert cooldowns[0]["name"] == "p1"

    def test_get_cooldowns_none_on_cooldown(self):
        """Get cooldowns returns empty when no profiles on cooldown."""
        profiles = [AuthProfile(name="p1", api_key="key1")]
        pm = ProfileManager(profiles)
        cooldowns = pm.get_cooldowns()
        assert len(cooldowns) == 0


# ============================================================
# runner.py Tests
# ============================================================

class TestResilienceResult:
    """Tests for ResilienceResult dataclass."""

    def test_resilience_result_success(self):
        """ResilienceResult stores success state."""
        result = ResilienceResult(success=True, content="response")
        assert result.success is True
        assert result.content == "response"
        assert result.error is None
        assert result.retries == 0
        assert result.profile_used is None

    def test_resilience_result_failure(self):
        """ResilienceResult stores error information."""
        result = ResilienceResult(
            success=False,
            content=None,
            error="all profiles exhausted",
            retries=10,
            profile_used="p1"
        )
        assert result.success is False
        assert result.error == "all profiles exhausted"
        assert result.retries == 10
        assert result.profile_used == "p1"


class TestResilienceRunner:
    """Tests for ResilienceRunner 3-layer retry logic."""

    def _make_mock_api_client(self, responses: list, tool_calls: bool = False):
        """Create mock API client that returns sequential responses."""
        mock_client = MagicMock()
        response_iter = iter(responses)
        
        def create_side_effect(*args, **kwargs):
            resp = MagicMock()
            resp.choices = [MagicMock()]
            choice = resp.choices[0]
            choice.message = MagicMock()
            choice.message.content = next(response_iter, "final response")
            choice.message.tool_calls = None
            
            if tool_calls and choice.message.content != "final response":
                tc = MagicMock()
                tc.id = "call_123"
                tc.function.name = "test_tool"
                tc.function.arguments = '{"arg": "value"}'
                choice.message.tool_calls = [tc]
            
            return resp
        
        mock_client.chat.completions.create = create_side_effect
        return mock_client

    def test_run_success_first_attempt(self):
        """Run succeeds on first API call."""
        profiles = [AuthProfile(name="p1", api_key="key1")]
        pm = ProfileManager(profiles)
        runner = ResilienceRunner(pm, model="gpt-4o")
        
        mock_client = self._make_mock_api_client(["Hello!"])
        
        def api_client_fn(api_key, base_url):
            return mock_client
        
        result = runner.run("You are helpful.", [], [], api_client_fn)
        
        assert result.success is True
        assert result.content is not None
        assert result.profile_used == "p1"
        assert result.retries == 0

    def test_run_auth_failure_rotates_profile(self):
        """Auth failure causes profile rotation to next profile."""
        profiles = [
            AuthProfile(name="p1", api_key="key1"),
            AuthProfile(name="p2", api_key="key2"),
        ]
        pm = ProfileManager(profiles)
        runner = ResilienceRunner(pm, model="gpt-4o")
        
        auth_error = Exception("authentication failed")
        call_count = [0]
        
        def api_client_fn(api_key, base_url):
            mock = MagicMock()
            def create_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise auth_error
                resp = MagicMock()
                resp.choices = [MagicMock()]
                resp.choices[0].message = MagicMock()
                resp.choices[0].message.content = "Success on second profile"
                resp.choices[0].message.tool_calls = None
                return resp
            mock.chat.completions.create = create_side_effect
            return mock
        
        result = runner.run("You are helpful.", [], [], api_client_fn)
        
        assert result.success is True
        assert result.profile_used == "p2"

    def test_run_rate_limit_rotates_profile(self):
        """Rate limit causes profile rotation after cooldown."""
        profiles = [
            AuthProfile(name="p1", api_key="key1"),
            AuthProfile(name="p2", api_key="key2"),
        ]
        pm = ProfileManager(profiles)
        runner = ResilienceRunner(pm, model="gpt-4o")
        
        rate_limit_error = Exception("rate limit 429")
        call_count = [0]
        
        def api_client_fn(api_key, base_url):
            mock = MagicMock()
            def create_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise rate_limit_error
                resp = MagicMock()
                resp.choices = [MagicMock()]
                resp.choices[0].message = MagicMock()
                resp.choices[0].message.content = "Success on second profile"
                resp.choices[0].message.tool_calls = None
                return resp
            mock.chat.completions.create = create_side_effect
            return mock
        
        result = runner.run("You are helpful.", [], [], api_client_fn)
        
        assert result.success is True
        assert result.profile_used == "p2"

    def test_run_overflow_compacts_and_retries(self):
        """Overflow triggers compaction and retry."""
        profiles = [AuthProfile(name="p1", api_key="key1")]
        pm = ProfileManager(profiles)
        runner = ResilienceRunner(pm, model="gpt-4o")
        
        overflow_error = Exception("context length exceeded")
        call_count = [0]
        
        def api_client_fn(api_key, base_url):
            mock = MagicMock()
            def create_side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                resp.choices = [MagicMock()]
                resp.choices[0].message = MagicMock()
                
                if call_count[0] == 1:
                    raise overflow_error
                
                resp.choices[0].message.content = "Success after compaction"
                resp.choices[0].message.tool_calls = None
                return resp
            mock.chat.completions.create = create_side_effect
            return mock
        
        result = runner.run("You are helpful.", [], [], api_client_fn)
        
        assert result.success is True
        assert call_count[0] == 2  # Initial call + retry after compaction

    def test_run_all_profiles_exhausted_returns_failure(self):
        """All profiles exhausted returns failure result."""
        profiles = [
            AuthProfile(name="p1", api_key="key1"),
            AuthProfile(name="p2", api_key="key2"),
        ]
        pm = ProfileManager(profiles)
        runner = ResilienceRunner(pm, model="gpt-4o")
        
        def api_client_fn(api_key, base_url):
            mock = MagicMock()
            def create_side_effect(*args, **kwargs):
                raise Exception("persistent error")
            mock.chat.completions.create = create_side_effect
            return mock
        
        result = runner.run("You are helpful.", [], [], api_client_fn)
        
        assert result.success is False
        assert result.error is not None

    def test_run_fallback_models_after_exhaustion(self):
        """Fallback models are tried after profiles exhausted."""
        profiles = [AuthProfile(name="p1", api_key="key1")]
        pm = ProfileManager(profiles)
        runner = ResilienceRunner(pm, model="gpt-4o", fallback_models=["gpt-3.5-turbo"])
        
        call_count = [0]
        
        def api_client_fn(api_key, base_url):
            mock = MagicMock()
            def create_side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                resp.choices = [MagicMock()]
                resp.choices[0].message = MagicMock()
                resp.choices[0].message.content = f"Response {call_count[0]}"
                resp.choices[0].message.tool_calls = None
                return resp
            mock.chat.completions.create = create_side_effect
            return mock
        
        result = runner.run("You are helpful.", [], [], api_client_fn)
        
        assert result.success is True

    def test_run_timeout_causes_short_cooldown(self):
        """Timeout causes 60 second cooldown and profile rotation."""
        profiles = [
            AuthProfile(name="p1", api_key="key1"),
            AuthProfile(name="p2", api_key="key2"),
        ]
        pm = ProfileManager(profiles)
        runner = ResilienceRunner(pm, model="gpt-4o")
        
        timeout_error = Exception("request timeout")
        call_count = [0]
        
        def api_client_fn(api_key, base_url):
            mock = MagicMock()
            def create_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise timeout_error
                resp = MagicMock()
                resp.choices = [MagicMock()]
                resp.choices[0].message = MagicMock()
                resp.choices[0].message.content = "Success on second profile"
                resp.choices[0].message.tool_calls = None
                return resp
            mock.chat.completions.create = create_side_effect
            return mock
        
        result = runner.run("You are helpful.", [], [], api_client_fn)
        
        assert result.success is True
        assert result.profile_used == "p2"

    def test_run_truncate_tool_results(self):
        """Tool results exceeding max size are truncated."""
        runner = ResilienceRunner(ProfileManager(), model="gpt-4o")
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Let me help."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_call_id": "call_1",
                        "content": "x" * 20000,  # Exceeds max_result_size
                    }
                ],
            },
        ]
        
        truncated = runner._truncate_tool_results(messages)
        
        tool_result = truncated[2]["content"][0]
        assert len(tool_result["content"]) < 20000
        assert "[truncated]" in tool_result["content"]

    def test_run_compact_history_shortens_messages(self):
        """Compact history reduces message count."""
        profiles = [AuthProfile(name="p1", api_key="key1")]
        pm = ProfileManager(profiles)
        runner = ResilienceRunner(pm, model="gpt-4o")
        
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(20)
        ]
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summarized conversation."
        mock_client.chat.completions.create = lambda **kwargs: mock_response
        
        compacted = runner._compact_history(messages, mock_client)
        
        # Should be significantly shorter
        assert len(compacted) < len(messages)

    def test_run_compact_history_preserves_recent_messages(self):
        """Compact history keeps recent messages intact."""
        profiles = [AuthProfile(name="p1", api_key="key1")]
        pm = ProfileManager(profiles)
        runner = ResilienceRunner(pm, model="gpt-4o")
        
        recent_messages = [
            {"role": "user", "content": "Recent message 1"},
            {"role": "assistant", "content": "Recent response"},
        ]
        messages = [{"role": "user", "content": f"Old {i}"} for i in range(15)] + recent_messages
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summarized."
        mock_client.chat.completions.create = lambda **kwargs: mock_response
        
        compacted = runner._compact_history(messages, mock_client)
        
        # Recent messages should be in compacted result
        assert compacted[-2]["content"] == "Recent message 1"
        assert compacted[-1]["content"] == "Recent response"

    def test_run_max_overflow_compaction_limit(self):
        """Overflow retries respect MAX_OVERFLOW_COMPACTION limit."""
        profiles = [AuthProfile(name="p1", api_key="key1")]
        pm = ProfileManager(profiles)
        runner = ResilienceRunner(pm, model="gpt-4o")
        
        overflow_error = Exception("context length exceeded")
        call_count = [0]
        
        def api_client_fn(api_key, base_url):
            mock = MagicMock()
            def create_side_effect(*args, **kwargs):
                call_count[0] += 1
                raise overflow_error
            mock.chat.completions.create = create_side_effect
            return mock
        
        result = runner.run("You are helpful.", [], [], api_client_fn)
        
        # Should exhaust all overflow compaction attempts
        assert call_count[0] >= MAX_OVERFLOW_COMPACTION

    def test_execute_tool_returns_result(self):
        """Execute tool returns a result string."""
        profiles = [AuthProfile(name="p1", api_key="key1")]
        pm = ProfileManager(profiles)
        runner = ResilienceRunner(pm, model="gpt-4o")
        
        result = runner._execute_tool("test_tool", '{"arg": "value"}')
        
        assert "test_tool" in result
        assert "executed" in result


# ============================================================
# Module Constants Tests
# ============================================================

class TestModuleConstants:
    """Tests for module-level constants."""

    def test_base_retry_is_24(self):
        """BASE_RETRY should be 24."""
        assert BASE_RETRY == 24

    def test_per_profile_is_8(self):
        """PER_PROFILE should be 8."""
        assert PER_PROFILE == 8

    def test_max_overflow_compaction_is_2(self):
        """MAX_OVERFLOW_COMPACTION should be 2."""
        assert MAX_OVERFLOW_COMPACTION == 2

    def test_cooldown_seconds_mapping_complete(self):
        """All FailoverReason values have cooldowns defined."""
        for reason in FailoverReason:
            assert reason in COOLDOWN_SECONDS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])