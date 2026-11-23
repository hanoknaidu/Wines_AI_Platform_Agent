"""Unit tests: money, masking/redaction, tokens, resilience primitives."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from app.core.clock import Clock
from app.core.errors import AuthenticationError
from app.core.masking import (
    contains_card_number,
    mask_email,
    mask_phone,
    mask_street,
    redact_mapping,
    redact_text,
)
from app.core.money import cents_to_str, pct_of, prorate, str_to_cents
from app.core.resilience import CircuitBreaker, CircuitOpenError, CircuitState, retry_async
from app.core.security import TokenService
from tests.conftest import make_settings


class TestMoney:
    @pytest.mark.parametrize("cents,text", [(0, "0.00"), (5, "0.05"), (2346, "23.46"), (-655, "-6.55"),
                                            (15000, "150.00")])
    def test_cents_to_str(self, cents, text):
        assert cents_to_str(cents) == text

    @pytest.mark.parametrize("text,cents", [("23.46", 2346), ("23.465", 2347), ("0.1", 10), ("150", 15000)])
    def test_str_to_cents_rounds_half_up(self, text, cents):
        assert str_to_cents(text) == cents

    def test_basis_points_and_prorate_are_integer_half_up(self):
        assert pct_of(10000, 1500) == 1500  # 15% restocking fee
        assert pct_of(333, 1500) == 50  # 49.95 -> 50
        assert prorate(1000, 1, 3) == 333
        assert prorate(1000, 2, 3) == 667
        assert prorate(100, 1, 0) == 0


class TestMasking:
    def test_contact_masks(self):
        assert mask_email("olivia.martinez@example.com") == "o***@example.com"
        assert mask_phone("+12015550111") == "***-***-0111"
        assert mask_street("25 Willowmere Street") == "** W*** Street"

    def test_redacts_luhn_valid_cards_only(self):
        assert contains_card_number("my card is 4111 1111 1111 1111")
        assert "[REDACTED_CARD]" in redact_text("card 4111-1111-1111-1111 please")
        assert not contains_card_number("order WA-100114 total 122.43")  # not a PAN

    def test_redacts_ssn_email_phone(self):
        out = redact_text("ssn 123-45-6789, mail jane.doe@example.org, call 201-555-0199")
        assert "123-45-6789" not in out and "[REDACTED_SSN]" in out
        assert "j***@example.org" in out
        assert "***-***-0199" in out

    def test_redact_mapping_handles_nested_and_sensitive_keys(self):
        out = redact_mapping({"token": "abc", 2: {"email": "a.b@example.com"}, "items": [{"password": "x"}]})
        assert out["token"] == "[REDACTED]"
        assert out["2"]["email"] == "a***@example.com"
        assert out["items"][0]["password"] == "[REDACTED]"


class TestTokens:
    def setup_method(self):
        self.clock = Clock(datetime(2026, 11, 19, 18, tzinfo=UTC))
        self.tokens = TokenService(make_settings(), self.clock)

    def test_customer_and_agent_tokens_round_trip(self):
        p = self.tokens.verify(self.tokens.issue_customer_token("C-100001"))
        assert (p.role, p.customer_number, p.actor_type) == ("customer", "C-100001", "customer")
        a = self.tokens.verify(self.tokens.issue_agent_token("C-100001", "S1", "run_x"))
        assert (a.role, a.customer_number, a.session_id, a.run_id) == ("agent", "C-100001", "S1", "run_x")
        assert a.actor_type == "ai_agent" and "refunds:write" in a.scopes

    def test_ownership(self):
        p = self.tokens.verify(self.tokens.issue_customer_token("C-100001"))
        assert p.can_access_customer("C-100001") and not p.can_access_customer("C-100002")
        staff = self.tokens.verify(self.tokens.issue_staff_token("S-1001"))
        assert staff.can_access_customer("C-100002")

    def test_rejects_tampered_and_expired(self):
        token = self.tokens.issue_customer_token("C-100001")
        with pytest.raises(AuthenticationError):
            self.tokens.verify(token[:-2] + "xx")
        later = TokenService(make_settings(), Clock(datetime(2026, 11, 19, 18, tzinfo=UTC) + timedelta(hours=3)))
        with pytest.raises(AuthenticationError):
            later.verify(token)
        other = TokenService(make_settings(jwt_secret="another-secret-0123456789abcdef0123"), self.clock)
        with pytest.raises(AuthenticationError):
            other.verify(token)


class TestResilience:
    async def test_circuit_opens_then_half_opens_then_closes(self):
        cb = CircuitBreaker("t", failure_threshold=2, reset_s=0.05)
        await cb.record_failure()
        await cb.before_call()  # still closed after one failure
        await cb.record_failure()
        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitOpenError):
            await cb.before_call()
        await asyncio.sleep(0.06)
        assert cb.state == CircuitState.HALF_OPEN
        await cb.before_call()
        await cb.record_success()
        assert cb.state == CircuitState.CLOSED

    async def test_retry_retries_only_when_allowed(self):
        calls = {"n": 0}

        async def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ConnectionError("boom")
            return "ok"

        result, attempts = await retry_async(flaky, attempts=3, should_retry=lambda o: isinstance(o, ConnectionError),
                                             base_delay_s=0.001)
        assert (result, attempts) == ("ok", 3)

        calls["n"] = 0
        with pytest.raises(ConnectionError):
            await retry_async(flaky, attempts=3, should_retry=lambda o: False, base_delay_s=0.001)
        assert calls["n"] == 1
