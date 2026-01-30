import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from quillsql.core import Quill


@patch("quillsql.core.CachedConnection")
def test_query_handles_none_tenant_flag_responses(mock_cached_connection):
    mock_connection = MagicMock()
    mock_connection.database_type = "PostgreSQL"
    mock_cached_connection.return_value = mock_connection

    quill = Quill(
        private_key=os.getenv("PRIVATE_KEY"),
        database_type=os.getenv("DB_TYPE"),
        database_connection_string=os.getenv("DB_URL")
    )

    quill.run_queries = MagicMock(
        side_effect=[
            {"queryResults": [None]},
            {"queryResults": []},
        ]
    )

    def post_quill_side_effect(path, payload):
        if path == "tenant-mapped-flags":
            return {
                "queries": [
                    'SELECT * FROM (SELECT "id" AS "customer_id", "name" AS "quill_label", "id" AS "quill_flag" FROM "public"."customers") AS "subq_owner_query" WHERE "customer_id" IN (2)'
                ],
                "metadata": {"queryOrder": ["customer_id"]},
            }
        return {"queries": [], "metadata": {}}

    quill.post_quill = MagicMock(side_effect=post_quill_side_effect)

    result = quill.query(
        tenants=["tenant-1"],
        metadata={
            "task": "report",
            "clientId": "client-123",
            "reportId": "report-456",
            "databaseType": "PostgreSQL",
        },
    )

    assert result["status"] == "success"
    assert result["data"] == {}


@patch("quillsql.core.CachedConnection")
def test_query_handles_tenant_flag_metadata_none(mock_cached_connection):
    mock_connection = MagicMock()
    mock_connection.database_type = "PostgreSQL"
    mock_cached_connection.return_value = mock_connection

    quill = Quill(
       private_key=os.getenv("PRIVATE_KEY"),
        database_type=os.getenv("DB_TYPE"),
        database_connection_string=os.getenv("DB_URL")
    )

    quill.run_queries = MagicMock(
        side_effect=[
            {"queryResults": [{"rows": [{"quill_flag": "alpha"}]}]},
            {"queryResults": []},
        ]
    )

    def post_quill_side_effect(path, payload):
        if path == "tenant-mapped-flags":
            return {
                "queries": [
                    'SELECT * FROM (SELECT "id" AS "customer_id", "name" AS "quill_label", "id" AS "quill_flag" FROM "public"."customers") AS "subq_owner_query" WHERE "customer_id" IN (2)'
                ],
                "metadata": None,
            }
        return {"queries": [], "metadata": {}}

    quill.post_quill = MagicMock(side_effect=post_quill_side_effect)

    result = quill.query(
        tenants=[{"tenantField": "customer_id", "tenantIds": [2]}],
        metadata={
            "task": "report",
            "clientId": "client-123",
            "reportId": "report-456",
            "databaseType": "PostgreSQL",
        },
    )

    assert result["status"] == "success"
    assert result["data"] == {}


@patch("quillsql.core.CachedConnection")
def test_query_handles_array_to_map_with_null_mapped_rows(mock_cached_connection):
    mock_connection = MagicMock()
    mock_connection.database_type = "PostgreSQL"
    mock_cached_connection.return_value = mock_connection

    quill = Quill(
        private_key=os.getenv("PRIVATE_KEY"),
        database_type=os.getenv("DB_TYPE"),
        database_connection_string=os.getenv("DB_URL")
    )

    quill.run_queries = MagicMock(
        side_effect=[
            {"queryResults": []},  # tenant-mapped-flags
            {"queryResults": [], "mapped_array": [None]},  # main query
        ]
    )

    def post_quill_side_effect(path, payload):
        if path == "tenant-mapped-flags":
            return {"queries": [], "metadata": {"queryOrder": []}}
        if path == "filter-options":
            return {
                "queries": ["SELECT 1"],
                "metadata": {
                    "filters": [{"label": "Driver"}],
                    "runQueryConfig": {
                        "arrayToMap": {"arrayName": "filters", "field": "options"}
                    },
                },
            }
        return {"queries": [], "metadata": {}}

    quill.post_quill = MagicMock(side_effect=post_quill_side_effect)

    result = quill.query(
        tenants=[{"tenantField": "customer_id", "tenantIds": [2]}],
        metadata={
            "task": "filter-options",
            "clientId": "client-123",
            "filter": {"field": "user_name"},
        },
        flags=[],
    )

    assert result["status"] == "success"
    assert result["data"]["filters"][0]["options"] == []


@patch("quillsql.core.CachedConnection")
def test_query_handles_fields_to_remove_with_null_results(mock_cached_connection):
    mock_connection = MagicMock()
    mock_connection.database_type = "PostgreSQL"
    mock_cached_connection.return_value = mock_connection

    quill = Quill(
        private_key=os.getenv("PRIVATE_KEY"),
        database_type=os.getenv("DB_TYPE"),
        database_connection_string=os.getenv("DB_URL")
    )

    quill.run_queries = MagicMock(
        side_effect=[
            {"queryResults": []},  # tenant-mapped-flags
            {"queryResults": [None]},  # main run_queries
        ]
    )

    def post_quill_side_effect(path, payload):
        if path == "tenant-mapped-flags":
            return {"queries": [], "metadata": {"queryOrder": []}}
        if path == "report":
            return {
                "queries": ["SELECT 1"],
                "metadata": {
                    "runQueryConfig": {"fieldsToRemove": ["customer_id"]},
                },
            }
        return {"queries": [], "metadata": {}}

    quill.post_quill = MagicMock(side_effect=post_quill_side_effect)

    result = quill.query(
        tenants=[{"tenantField": "customer_id", "tenantIds": [2]}],
        metadata={
            "task": "report",
            "clientId": "client-123",
            "reportId": "report-456",
            "databaseType": "PostgreSQL",
        },
        flags=[],
    )

    assert result["status"] == "success"
    assert result["queries"]["queryResults"][0] is None

