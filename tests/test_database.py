"""Tests for services/database.py — all Supabase interactions."""

from unittest.mock import patch, MagicMock
import pytest
from services.database import (
    get_all_clients,
    add_client,
    delete_client,
    save_session,
    get_sessions_for_client,
    delete_session,
)


@pytest.fixture
def patched_supabase(mock_supabase):
    """Patch create_client to return our mock Supabase client."""
    with patch("services.database.create_client", return_value=mock_supabase):
        yield mock_supabase


class TestGetAllClients:
    def test_returns_list_of_clients(self, patched_supabase):
        patched_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[{"id": "1", "name": "Ana"}, {"id": "2", "name": "Luis"}]
        )
        result = get_all_clients()
        assert len(result) == 2
        assert result[0]["name"] == "Ana"
        patched_supabase.table.assert_called_with("clients")

    def test_returns_empty_list_on_error(self, patched_supabase):
        patched_supabase.table.side_effect = Exception("connection failed")
        result = get_all_clients()
        assert result == []

    def test_orders_by_name(self, patched_supabase):
        patched_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[]
        )
        get_all_clients()
        patched_supabase.table.return_value.select.return_value.order.assert_called_with("name")


class TestAddClient:
    def test_inserts_client_with_name_and_notes(self, patched_supabase):
        add_client("Maria", "Nota de prueba")
        patched_supabase.table.assert_called_with("clients")
        patched_supabase.table.return_value.insert.assert_called_once_with(
            {"name": "Maria", "notes": "Nota de prueba"}
        )

    def test_inserts_client_with_default_empty_notes(self, patched_supabase):
        add_client("Carlos")
        patched_supabase.table.return_value.insert.assert_called_once_with(
            {"name": "Carlos", "notes": ""}
        )

    def test_raises_on_error(self, patched_supabase):
        patched_supabase.table.side_effect = Exception("insert failed")
        with pytest.raises(Exception, match="insert failed"):
            add_client("Test")


class TestDeleteClient:
    def test_deletes_by_id(self, patched_supabase):
        delete_client("client-123")
        patched_supabase.table.assert_called_with("clients")
        patched_supabase.table.return_value.delete.return_value.eq.assert_called_once_with(
            "id", "client-123"
        )

    def test_raises_on_error(self, patched_supabase):
        patched_supabase.table.side_effect = Exception("delete failed")
        with pytest.raises(Exception, match="delete failed"):
            delete_client("client-123")


class TestSaveSession:
    def test_inserts_session_with_correct_fields(self, patched_supabase, sample_structured_summary):
        save_session("client-001", "transcripcion de prueba", sample_structured_summary)
        patched_supabase.table.assert_called_with("sessions")
        patched_supabase.table.return_value.insert.assert_called_once_with({
            "client_id": "client-001",
            "raw_transcript": "transcripcion de prueba",
            "structured_summary": sample_structured_summary,
        })

    def test_summary_is_dict_not_string(self, patched_supabase, sample_structured_summary):
        save_session("client-001", "test", sample_structured_summary)
        call_args = patched_supabase.table.return_value.insert.call_args[0][0]
        assert isinstance(call_args["structured_summary"], dict)

    def test_raises_on_error(self, patched_supabase):
        patched_supabase.table.side_effect = Exception("save failed")
        with pytest.raises(Exception, match="save failed"):
            save_session("client-001", "test", {})


class TestGetSessionsForClient:
    def test_returns_sessions_ordered_by_session_number(self, patched_supabase, sample_sessions):
        chain = patched_supabase.table.return_value.select.return_value.eq.return_value.order
        chain.return_value.execute.return_value = MagicMock(data=sample_sessions)

        result = get_sessions_for_client("client-001")
        assert len(result) == 2
        assert result[0]["session_number"] == 1
        patched_supabase.table.return_value.select.return_value.eq.assert_called_with(
            "client_id", "client-001"
        )

    def test_returns_empty_list_on_error(self, patched_supabase):
        patched_supabase.table.side_effect = Exception("query failed")
        result = get_sessions_for_client("client-001")
        assert result == []


class TestDeleteSession:
    def test_deletes_by_session_id(self, patched_supabase):
        delete_session("sess-001")
        patched_supabase.table.assert_called_with("sessions")
        patched_supabase.table.return_value.delete.return_value.eq.assert_called_once_with(
            "id", "sess-001"
        )

    def test_raises_on_error(self, patched_supabase):
        patched_supabase.table.side_effect = Exception("delete failed")
        with pytest.raises(Exception, match="delete failed"):
            delete_session("sess-001")
