"""Tests for the middleware module."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from a2a_llm_tracker.middleware import (
    _is_uuid,
    _is_concept_id,
    set_request_id_async,
    generate_request_id_async,
    get_request_id,
    set_request_id,
    _request_id_var,
)


class TestIsUuid:
    """Tests for _is_uuid helper function."""

    def test_valid_uuid_lowercase(self):
        assert _is_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_valid_uuid_uppercase(self):
        assert _is_uuid("550E8400-E29B-41D4-A716-446655440000") is True

    def test_valid_uuid_mixed_case(self):
        assert _is_uuid("550e8400-E29B-41d4-A716-446655440000") is True

    def test_invalid_uuid_too_short(self):
        assert _is_uuid("550e8400-e29b-41d4-a716") is False

    def test_invalid_uuid_no_dashes(self):
        assert _is_uuid("550e8400e29b41d4a716446655440000") is False

    def test_invalid_uuid_random_string(self):
        assert _is_uuid("not-a-uuid") is False

    def test_invalid_uuid_integer_string(self):
        assert _is_uuid("12345") is False

    def test_empty_string(self):
        assert _is_uuid("") is False


class TestIsConceptId:
    """Tests for _is_concept_id helper function."""

    def test_valid_integer_string(self):
        assert _is_concept_id("12345") is True

    def test_valid_integer_string_zero(self):
        assert _is_concept_id("0") is True

    def test_valid_negative_integer(self):
        assert _is_concept_id("-123") is True

    def test_invalid_uuid_string(self):
        assert _is_concept_id("550e8400-e29b-41d4-a716-446655440000") is False

    def test_invalid_random_string(self):
        assert _is_concept_id("hello") is False

    def test_invalid_float_string(self):
        assert _is_concept_id("12.34") is False

    def test_empty_string(self):
        assert _is_concept_id("") is False


class TestSetRequestIdAsync:
    """Tests for set_request_id_async function."""

    @pytest.fixture(autouse=True)
    def reset_context(self):
        """Reset the context variable before each test."""
        _request_id_var.set("")
        yield
        _request_id_var.set("")

    @pytest.mark.asyncio
    async def test_uuid_creates_new_concept(self):
        """When given a UUID, should create a new concept and return its ID."""
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        mock_concept = MagicMock()
        mock_concept.id = 12345

        mock_tx = AsyncMock()
        mock_tx.initialize = AsyncMock()
        mock_tx.MakeTheInstanceConceptLocal = AsyncMock(return_value=mock_concept)
        mock_tx.commitTransaction = AsyncMock()

        with patch("a2a_llm_tracker.middleware.LocalTransaction", return_value=mock_tx):
            with patch("a2a_llm_tracker.middleware.GetTheConcept", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_concept
                result = await set_request_id_async(test_uuid, user_id=101)

        assert result == "12345"
        assert get_request_id() == "12345"
        mock_tx.MakeTheInstanceConceptLocal.assert_called_once_with(
            "the_llm_request",
            test_uuid,
            False,
            userId=101,
        )
        mock_tx.commitTransaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_concept_id_fetches_existing_concept(self):
        """When given a concept ID, should fetch the existing concept."""
        test_concept_id = "98765"
        mock_concept = MagicMock()
        mock_concept.id = 98765

        mock_tx = AsyncMock()
        mock_tx.initialize = AsyncMock()
        mock_tx.commitTransaction = AsyncMock()

        with patch("a2a_llm_tracker.middleware.LocalTransaction", return_value=mock_tx):
            with patch("a2a_llm_tracker.middleware.GetTheConcept", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_concept
                result = await set_request_id_async(test_concept_id, user_id=101)

        assert result == "98765"
        assert get_request_id() == "98765"
        # GetTheConcept should be called twice: once for fetching, once after commit
        assert mock_get.call_count == 2
        mock_get.assert_any_call(98765)
        mock_tx.MakeTheInstanceConceptLocal.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_format_creates_new_concept(self):
        """When given an unknown format, should create a new concept."""
        test_value = "custom-request-identifier"
        mock_concept = MagicMock()
        mock_concept.id = 11111

        mock_tx = AsyncMock()
        mock_tx.initialize = AsyncMock()
        mock_tx.MakeTheInstanceConceptLocal = AsyncMock(return_value=mock_concept)
        mock_tx.commitTransaction = AsyncMock()

        with patch("a2a_llm_tracker.middleware.LocalTransaction", return_value=mock_tx):
            with patch("a2a_llm_tracker.middleware.GetTheConcept", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_concept
                result = await set_request_id_async(test_value, user_id=101)

        assert result == "11111"
        assert get_request_id() == "11111"
        mock_tx.MakeTheInstanceConceptLocal.assert_called_once_with(
            "the_llm_request",
            test_value,
            False,
            userId=101,
        )

    @pytest.mark.asyncio
    async def test_custom_user_id(self):
        """Should use the provided user_id when creating concepts."""
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        mock_concept = MagicMock()
        mock_concept.id = 99999

        mock_tx = AsyncMock()
        mock_tx.initialize = AsyncMock()
        mock_tx.MakeTheInstanceConceptLocal = AsyncMock(return_value=mock_concept)
        mock_tx.commitTransaction = AsyncMock()

        with patch("a2a_llm_tracker.middleware.LocalTransaction", return_value=mock_tx):
            with patch("a2a_llm_tracker.middleware.GetTheConcept", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_concept
                result = await set_request_id_async(test_uuid, user_id=555)

        mock_tx.MakeTheInstanceConceptLocal.assert_called_once_with(
            "the_llm_request",
            test_uuid,
            False,
            userId=555,
        )

    @pytest.mark.asyncio
    async def test_rollback_on_exception(self):
        """Should rollback transaction and re-raise on exception."""
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"

        mock_tx = AsyncMock()
        mock_tx.initialize = AsyncMock()
        mock_tx.MakeTheInstanceConceptLocal = AsyncMock(side_effect=Exception("Test error"))
        mock_tx.rollbackTransaction = AsyncMock()

        with patch("a2a_llm_tracker.middleware.LocalTransaction", return_value=mock_tx):
            with pytest.raises(Exception, match="Test error"):
                await set_request_id_async(test_uuid)

        mock_tx.rollbackTransaction.assert_called_once()
        # On error, the original request_id should be set
        assert get_request_id() == test_uuid

    @pytest.mark.asyncio
    async def test_fallback_when_concept_has_no_id(self):
        """Should fallback to original request_id if concept has no id attribute."""
        test_value = "test-request"
        mock_concept = MagicMock(spec=[])  # No 'id' attribute

        mock_tx = AsyncMock()
        mock_tx.initialize = AsyncMock()
        mock_tx.MakeTheInstanceConceptLocal = AsyncMock(return_value=mock_concept)
        mock_tx.commitTransaction = AsyncMock()

        with patch("a2a_llm_tracker.middleware.LocalTransaction", return_value=mock_tx):
            with patch("a2a_llm_tracker.middleware.GetTheConcept", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_concept
                result = await set_request_id_async(test_value)

        assert result == test_value
        assert get_request_id() == test_value


class TestGenerateRequestIdAsync:
    """Tests for generate_request_id_async function."""

    @pytest.fixture(autouse=True)
    def reset_context(self):
        """Reset the context variable before each test."""
        _request_id_var.set("")
        yield
        _request_id_var.set("")

    @pytest.mark.asyncio
    async def test_creates_concept_and_returns_id(self):
        """Should create a concept and return its ID."""
        mock_concept = MagicMock()
        mock_concept.id = 12345

        mock_tx = AsyncMock()
        mock_tx.initialize = AsyncMock()
        mock_tx.MakeTheInstanceConceptLocal = AsyncMock(return_value=mock_concept)
        mock_tx.commitTransaction = AsyncMock()

        with patch("a2a_llm_tracker.middleware.LocalTransaction", return_value=mock_tx):
            with patch("a2a_llm_tracker.middleware.GetTheConcept", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_concept
                with patch("a2a_llm_tracker.middleware.uuid.uuid4") as mock_uuid:
                    mock_uuid.return_value = MagicMock(__str__=lambda _: "generated-uuid-value")
                    result = await generate_request_id_async(user_id=101)

        assert result == "12345"
        assert get_request_id() == "12345"
        mock_tx.MakeTheInstanceConceptLocal.assert_called_once_with(
            "the_llm_request",
            "generated-uuid-value",
            False,
            userId=101,
        )
        mock_tx.commitTransaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_sets_context_variable(self):
        """Should set the request ID in context variable."""
        mock_concept = MagicMock()
        mock_concept.id = 99999

        mock_tx = AsyncMock()
        mock_tx.initialize = AsyncMock()
        mock_tx.MakeTheInstanceConceptLocal = AsyncMock(return_value=mock_concept)
        mock_tx.commitTransaction = AsyncMock()

        with patch("a2a_llm_tracker.middleware.LocalTransaction", return_value=mock_tx):
            with patch("a2a_llm_tracker.middleware.GetTheConcept", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_concept
                await generate_request_id_async()

        assert get_request_id() == "99999"

    @pytest.mark.asyncio
    async def test_custom_user_id(self):
        """Should use the provided user_id when creating concepts."""
        mock_concept = MagicMock()
        mock_concept.id = 11111

        mock_tx = AsyncMock()
        mock_tx.initialize = AsyncMock()
        mock_tx.MakeTheInstanceConceptLocal = AsyncMock(return_value=mock_concept)
        mock_tx.commitTransaction = AsyncMock()

        with patch("a2a_llm_tracker.middleware.LocalTransaction", return_value=mock_tx):
            with patch("a2a_llm_tracker.middleware.GetTheConcept", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_concept
                await generate_request_id_async(user_id=777)

        # Check that the correct user_id was passed
        call_args = mock_tx.MakeTheInstanceConceptLocal.call_args
        assert call_args.kwargs["userId"] == 777

    @pytest.mark.asyncio
    async def test_rollback_on_exception(self):
        """Should rollback transaction and re-raise on exception."""
        mock_tx = AsyncMock()
        mock_tx.initialize = AsyncMock()
        mock_tx.MakeTheInstanceConceptLocal = AsyncMock(side_effect=Exception("Test error"))
        mock_tx.rollbackTransaction = AsyncMock()

        with patch("a2a_llm_tracker.middleware.LocalTransaction", return_value=mock_tx):
            with pytest.raises(Exception, match="Test error"):
                await generate_request_id_async()

        mock_tx.rollbackTransaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_when_concept_has_no_id(self):
        """Should fallback to UUID if concept has no id attribute."""
        mock_concept = MagicMock(spec=[])  # No 'id' attribute

        mock_tx = AsyncMock()
        mock_tx.initialize = AsyncMock()
        mock_tx.MakeTheInstanceConceptLocal = AsyncMock(return_value=mock_concept)
        mock_tx.commitTransaction = AsyncMock()

        with patch("a2a_llm_tracker.middleware.LocalTransaction", return_value=mock_tx):
            with patch("a2a_llm_tracker.middleware.GetTheConcept", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_concept
                with patch("a2a_llm_tracker.middleware.uuid.uuid4") as mock_uuid:
                    mock_uuid.return_value = MagicMock(__str__=lambda _: "fallback-uuid")
                    result = await generate_request_id_async()

        assert result == "fallback-uuid"
        assert get_request_id() == "fallback-uuid"


class TestSyncSetRequestId:
    """Tests for the sync set_request_id function."""

    @pytest.fixture(autouse=True)
    def reset_context(self):
        """Reset the context variable before each test."""
        _request_id_var.set("")
        yield
        _request_id_var.set("")

    def test_sets_request_id(self):
        """Should set the request ID in context."""
        set_request_id("test-123")
        assert get_request_id() == "test-123"

    def test_overwrites_previous_value(self):
        """Should overwrite the previous request ID."""
        set_request_id("first")
        set_request_id("second")
        assert get_request_id() == "second"


# ============================================================================
# Integration Tests (require real CCS connection)
# ============================================================================

@pytest.mark.integration
class TestSetRequestIdAsyncIntegration:
    """Integration tests for set_request_id_async with real CCS connection."""

    @pytest.fixture(autouse=True)
    def reset_context(self):
        """Reset the context variable before each test."""
        _request_id_var.set("")
        yield
        _request_id_var.set("")

    @pytest.mark.asyncio
    async def test_uuid_creates_real_concept(self, ccs_connection):
        """Test that a UUID creates a real concept in CCS."""
        import uuid
        test_uuid = str(uuid.uuid4())

        result = await set_request_id_async(test_uuid, user_id=101)

        # Result should be a numeric concept ID, not the UUID
        assert result != test_uuid
        assert result.isdigit(), f"Expected numeric concept ID, got: {result}"
        assert get_request_id() == result

        # Verify we can fetch the concept
        from ccs import GetTheConcept
        concept = await GetTheConcept(int(result))
        assert concept is not None
        assert concept.id == int(result)

    @pytest.mark.asyncio
    async def test_concept_id_fetches_existing(self, ccs_connection):
        """Test that an existing concept ID is fetched correctly."""
        import uuid

        # First create a concept
        test_uuid = str(uuid.uuid4())
        created_id = await set_request_id_async(test_uuid, user_id=101)

        # Reset context
        _request_id_var.set("")

        # Now use the concept ID
        result = await set_request_id_async(created_id, user_id=101)

        assert result == created_id
        assert get_request_id() == created_id

    @pytest.mark.asyncio
    async def test_custom_string_creates_concept(self, ccs_connection):
        """Test that a custom string creates a concept."""
        import uuid
        # Use a unique custom string to avoid collisions
        test_value = f"test-request-{uuid.uuid4().hex[:8]}"

        result = await set_request_id_async(test_value, user_id=101)

        # Result should be a numeric concept ID
        assert result.isdigit(), f"Expected numeric concept ID, got: {result}"
        assert get_request_id() == result

    @pytest.mark.asyncio
    async def test_different_user_ids(self, ccs_connection):
        """Test that different user IDs work correctly."""
        import uuid
        test_uuid = str(uuid.uuid4())

        result = await set_request_id_async(test_uuid, user_id=999)

        assert result.isdigit()
        assert get_request_id() == result


@pytest.mark.integration
class TestGenerateRequestIdAsyncIntegration:
    """Integration tests for generate_request_id_async with real CCS connection."""

    @pytest.fixture(autouse=True)
    def reset_context(self):
        """Reset the context variable before each test."""
        _request_id_var.set("")
        yield
        _request_id_var.set("")

    @pytest.mark.asyncio
    async def test_generates_concept_id(self, ccs_connection):
        """Test that generate_request_id_async creates a real concept."""
        result = await generate_request_id_async(user_id=101)

        # Result should be a numeric concept ID
        assert result.isdigit(), f"Expected numeric concept ID, got: {result}"
        assert get_request_id() == result

        # Verify we can fetch the concept
        from ccs import GetTheConcept
        concept = await GetTheConcept(int(result))
        assert concept is not None
        assert concept.id == int(result)

    @pytest.mark.asyncio
    async def test_generates_unique_ids(self, ccs_connection):
        """Test that each call generates a unique concept ID."""
        # Reset between calls
        _request_id_var.set("")
        result1 = await generate_request_id_async(user_id=101)

        _request_id_var.set("")
        result2 = await generate_request_id_async(user_id=101)

        assert result1 != result2
        assert result1.isdigit()
        assert result2.isdigit()

    @pytest.mark.asyncio
    async def test_with_custom_user_id(self, ccs_connection):
        """Test that custom user_id works correctly."""
        result = await generate_request_id_async(user_id=999)

        assert result.isdigit()
        assert get_request_id() == result
