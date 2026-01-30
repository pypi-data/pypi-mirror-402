import os
import codecs
from dotenv import load_dotenv

import requests
import redis
from .utils import Filter, convert_custom_filter
import json
from enum import Enum


from quillsql.db.cached_connection import CachedConnection
from quillsql.db.db_helper import (
    get_db_credentials,
    get_schema_column_info_by_db,
    get_schema_tables_by_db,
)
from quillsql.utils.schema_conversion import convert_type_to_postgres
from quillsql.utils.run_query_processes import (
    array_to_map,
    remove_fields,
)
from quillsql.utils.tenants import extract_tenant_ids
from quillsql.utils.pivot_template import (
    parse_distinct_values,
    hydrate_pivot_template,
)

load_dotenv()

ENV = os.getenv("PYTHON_ENV")
DEV_HOST = "http://localhost:8080"
PROD_HOST = "https://api.quill.co"
HOST = DEV_HOST if ENV == "development" else PROD_HOST

SINGLE_TENANT = "QUILL_SINGLE_TENANT"
ALL_TENANTS = "QUILL_ALL_TENANTS"
FLAG_TASKS = {'dashboard', 'report', 'item', 'report-info', 'filter-options'}

# Quill - Fullstack API Platform for Dashboards and Reporting.
class Quill:
    def __init__(
        self,
        private_key,
        database_type,
        database_connection_string=None,
        database_config=None,
        metadataServerURL=None,
        cache=None,
    ):
        if private_key is None:
            raise ValueError("Private key is required")
        if database_type is None:
            raise ValueError("Database type is required")
        if database_connection_string is None and database_config is None:
            raise ValueError("You must provide either DatabaseConnectionString or DatabaseConfig")

        # Handles both dsn-style connection strings (eg. "dbname=test password=secret" )
        # as well as url-style connection strings (eg. "postgres://foo@db.com")
        self.baseUrl = metadataServerURL if metadataServerURL is not None else HOST
        if database_connection_string is not None:
            self.target_connection = CachedConnection(
                database_type,
                get_db_credentials(database_type, database_connection_string),
                cache,
                True,
            )
        else:
            self.target_connection = CachedConnection(
                database_type, database_config, cache, False
            )
        self.private_key = private_key

    def get_cache(self, cache_config):
        cache_type = cache_config and cache_config.get("cache_type")
        if cache_type and cache_type == "redis" or cache_type == "rediss":
            return redis.Redis(
                host=cache_config.get("host", "localhost"),
                port=cache_config.get("port", 6379),
                username=cache_config.get("username", "default"),
                password=cache_config.get("password"),
            )
        return None

    def query(
        self,
        tenants,
        metadata,
        flags=None,
        filters: list[Filter] = None,
        admin_enabled: bool = None,
    ):
        if not tenants:
            raise ValueError("You may not pass an empty tenants array.")

        responseMetadata = {}
        if not metadata:
            return {"error": "Missing metadata.", "status": "error", "data": {}}

        task = metadata.get("task")
        if not task:
            return {"error": "Missing task.", "status": "error", "data": {}}

        try:
            # Set tenant IDs in the connection
            self.target_connection.tenant_ids = extract_tenant_ids(tenants)

            # Handle pivot-template task
            if task == "pivot-template":
                pivot_payload = {
                    **metadata,
                    "tenants": tenants,
                    "flags": flags,
                }
                if admin_enabled is not None:
                    pivot_payload["adminEnabled"] = admin_enabled
                if filters is not None:
                    pivot_payload["sdkFilters"] = [
                        convert_custom_filter(f) for f in filters
                    ]
                pivot_template_response = self.post_quill(
                    "pivot-template",
                    pivot_payload,
                )

                if pivot_template_response.get("error"):
                    return {
                        "status": "error",
                        "error": pivot_template_response.get("error"),
                        "data": pivot_template_response.get("metadata") or {},
                    }

                template = pivot_template_response.get("metadata", {}).get("template")
                config = pivot_template_response.get("metadata", {}).get("config")
                distinct_values_query = pivot_template_response.get("metadata", {}).get("distinctValuesQuery")
                row_count_query = pivot_template_response.get("metadata", {}).get("rowCountQuery")

                distinct_values = []
                if distinct_values_query:
                    distinct_value_results = self.run_queries(
                        [distinct_values_query],
                        self.target_connection.database_type,
                        metadata.get("databaseType"),
                        metadata,
                        None
                    )

                    distinct_value_query_results = (
                        distinct_value_results or {}
                    ).get("queryResults") or []
                    if distinct_value_query_results:
                        distinct_values = parse_distinct_values(
                            distinct_value_query_results[0],
                            config.get("databaseType")
                        )

                try:
                    final_query = hydrate_pivot_template(template, distinct_values, config)
                except Exception as err:
                    return {
                        "status": "error",
                        "error": f"Failed to hydrate pivot template: {str(err)}",
                        "data": {},
                    }

                queries_to_run = [final_query]
                if row_count_query:
                    hydrated_row_count_query = hydrate_pivot_template(
                        row_count_query,
                        distinct_values,
                        config
                    )
                    queries_to_run.append(hydrated_row_count_query)

                final_results = self.run_queries(
                    queries_to_run,
                    self.target_connection.database_type,
                    metadata.get("databaseType"),
                    metadata,
                    pivot_template_response.get("metadata", {}).get("runQueryConfig")
                )

                responseMetadata = pivot_template_response.get("metadata") or {}
                if final_results.get("queryResults") and len(final_results["queryResults"]) >= 1:
                    query_results = final_results["queryResults"][0]
                    if query_results.get("rows"):
                        responseMetadata["rows"] = query_results["rows"]
                    if query_results.get("fields"):
                        responseMetadata["fields"] = query_results["fields"]

                if "template" in responseMetadata:
                    del responseMetadata["template"]
                if "distinctValuesQuery" in responseMetadata:
                    del responseMetadata["distinctValuesQuery"]
                if "rowCountQuery" in responseMetadata:
                    del responseMetadata["rowCountQuery"]

                return {
                    "data": responseMetadata,
                    "queries": final_results,
                    "status": "success",
                }

            # Handle tenant flags synthesis
            tenant_flags = None
            if (task in FLAG_TASKS and 
                tenants[0] != ALL_TENANTS and 
                tenants[0] != SINGLE_TENANT
            ):
                
                tenant_flags_payload = {
                    'reportId': metadata.get('reportId') or metadata.get('dashboardItemId'),
                    'clientId': metadata.get('clientId'),
                    'dashboardName': metadata.get('name'),
                    'tenants': tenants,
                    'flags': flags,
                }
                if admin_enabled is not None:
                    tenant_flags_payload['adminEnabled'] = admin_enabled
                response = self.post_quill('tenant-mapped-flags', tenant_flags_payload)
                
                if response.get('error'):
                    return {
                        'status': 'error',
                        'error': response.get('error'),
                        'data': response.get('metadata') or {},
                    }
                
                flag_query_results = self.run_queries(
                    response.get('queries'),
                    self.target_connection.database_type,
                )
                
                tenant_flags = []
                query_order = (response.get('metadata') or {}).get('queryOrder') or []
                query_results = (flag_query_results or {}).get('queryResults') or []
                for index, tenant_field in enumerate(query_order):
                    query_result = (
                        query_results[index]
                        if index < len(query_results)
                        else {}
                    )
                    rows = (
                        query_result.get('rows')
                        if isinstance(query_result, dict)
                        else []
                    )
                    ordered_flags = []
                    seen = set()
                    for row in rows or []:
                        if not isinstance(row, dict):
                            continue
                        flag = row.get('quill_flag')
                        if flag is None or flag in seen:
                            continue
                        seen.add(flag)
                        ordered_flags.append(flag)
                    tenant_flags.append({
                        'tenantField': tenant_field,
                        'flags': ordered_flags,
                    })

            elif tenants[0] == SINGLE_TENANT and flags:
                if flags and isinstance(flags[0], dict):
                    tenant_flags = [{'tenantField': SINGLE_TENANT, 'flags': flags}]
                else:
                    tenant_flags = flags

            if metadata.get("preQueries"):
                pre_query_results = self.run_queries(
                    metadata.get("preQueries"),
                    self.target_connection.database_type,
                    metadata.get("databaseType"),
                    metadata,
                    metadata.get("runQueryConfig"),
                )
            else:
                pre_query_results = {}

            if metadata.get("runQueryConfig") and metadata.get("runQueryConfig").get(
                "overridePost"
            ):
                return {"data": pre_query_results, "status": "success"}
            view_query = None
            if metadata.get("preQueries"):
                view_query = metadata.get("preQueries")[0]
            pre_query_columns = (
                pre_query_results.get("columns")
                if metadata.get("runQueryConfig")
                and metadata.get("runQueryConfig").get("getColumns")
                else None
            )
            payload = {
                **metadata,
                "tenants": tenants,
                "flags": tenant_flags,
                "viewQuery": view_query,
            }
            if pre_query_columns is not None:
                payload["preQueryResultsColumns"] = pre_query_columns
            if admin_enabled is not None:
                payload["adminEnabled"] = admin_enabled
            if filters is not None:
                payload["sdkFilters"] = [convert_custom_filter(f) for f in filters]
            quill_results = self.post_quill(metadata.get("task"), payload)
            if quill_results.get("error"):
                responseMetadata = quill_results.get("metadata")
                response = {
                    "error": quill_results.get("error"),
                    "status": "error",
                    "data": {},
                }
                if responseMetadata:
                    response["data"] = responseMetadata
                return response

            # If there is no metadata in the quill results, create one
            if not quill_results.get("metadata"):
                quill_results["metadata"] = {}
            metadata = quill_results.get("metadata")
            responseMetadata = metadata
            results = self.run_queries(
                quill_results.get("queries"),
                self.target_connection.database_type,
                metadata.get("databaseType"),
                metadata,
                metadata.get("runQueryConfig"),
            )

            should_wrap_results = isinstance(results, list) or not results
            if should_wrap_results:
                normalized_results = {
                    "queryResults": results if isinstance(results, list) else []
                }
            else:
                normalized_results = results

            if (
                should_wrap_results
                and not normalized_results.get("queryResults")
                and quill_results.get("queries")
            ):
                normalized_results["queryResults"] = (
                    normalized_results.get("queryResults") or []
                )

            if (
                normalized_results.get("mapped_array")
                and metadata.get("runQueryConfig", {}).get("arrayToMap")
            ):
                array_to_map = metadata["runQueryConfig"]["arrayToMap"]
                target_collection = responseMetadata.get(array_to_map["arrayName"])
                if isinstance(target_collection, list):
                    for index, array in enumerate(normalized_results["mapped_array"]):
                        if index >= len(target_collection):
                            continue
                        target_entry = target_collection[index]
                        if not isinstance(target_entry, dict):
                            target_entry = {}
                            target_collection[index] = target_entry
                        target_entry[array_to_map["field"]] = array if array is not None else []
                del normalized_results["mapped_array"]

            query_results_list = normalized_results.get("queryResults") or []
            if len(query_results_list) == 1 and isinstance(query_results_list[0], dict):
                query_result = query_results_list[0]
                quill_results["metadata"]["rows"] = query_result.get("rows")
                quill_results["metadata"]["fields"] = query_result.get("fields")
            return {
                "data": quill_results.get("metadata"),
                "queries": normalized_results,
                "status": "success",
            }

        except Exception as err:
            if task == "update-view":
                broken_view_payload = {
                    "table": metadata.get("name"),
                    "clientId": metadata.get("clientId"),
                    "error": str(err),
                }
                if admin_enabled is not None:
                    broken_view_payload["adminEnabled"] = admin_enabled
                self.post_quill("set-broken-view", broken_view_payload)
            return {
                "error": str(err).splitlines()[0],
                "status": "error",
                "data": responseMetadata,
            }
        
    async def stream(
        self,
        tenants,
        metadata,
        flags=None,
    ):
        if not tenants:
            raise ValueError("You may not pass an empty tenants array.")

        if not metadata:
            yield {"type": "error", "errorText": "Missing metadata."}
            return

        task = metadata.get("task")
        if not task:
            yield {"type": "error", "errorText": "Missing task."}
            return

        try:
            # Set tenant IDs in the connection
            self.target_connection.tenant_ids = extract_tenant_ids(tenants)

            # Handle tenant flags synthesis
            tenant_flags = None
            if tenants[0] == SINGLE_TENANT and flags:
                if flags and isinstance(flags[0], dict):
                    tenant_flags = [{'tenantField': SINGLE_TENANT, 'flags': flags}]
                else:
                    tenant_flags = flags

            payload = { 
                **metadata,
                "tenants": tenants,
                "flags": tenant_flags,
            }
            # Custom JSON Encoder to handle Enums
            class EnumEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, Enum):
                        return obj.value  # Convert enum to its value (string in this case)
                    return super().default(obj)
            url = f"{self.baseUrl}/sdk/{task}"
            headers = {"Authorization": f"Bearer {self.private_key}", "Content-Type": "application/json","Accept": "text/event-stream"}
            encoded = json.dumps(payload, cls=EnumEncoder)

            resp = requests.post(url, data=encoded, headers=headers, stream=True)
            decoder = codecs.getincrementaldecoder('utf-8')()
            buf = ""
            for chunk in resp.iter_content(chunk_size=4096):
                buf += decoder.decode(chunk)
                while "\n\n" in buf:
                    raw_event, buf = buf.split("\n\n", 1)
                    data_lines = []
                    for line in raw_event.splitlines():
                        if line.startswith("data:"):
                            data_lines.append(line[len("data:"):].strip())
                    if not data_lines:
                        continue
                    payload = "\n".join(data_lines)
                    if payload == "[DONE]":
                        break
                    yield json.loads(payload)

            # flush any partial code points at the end
            buf += decoder.decode(b"", final=True)
            yield buf
            return
        except Exception as err:
            yield {
                "type": "error",
                "errorText": str(err).splitlines()[0],
            }
            return

    def apply_limit(self, query, limit):
        # Simple logic: if query already has a limit, don't add another
        if getattr(self.target_connection, 'database_type', '').lower() == 'mssql':
            import re
            if re.search(r'SELECT TOP \\d+', query, re.IGNORECASE):
                return query
            return re.sub(r'select', f'SELECT TOP {limit}', query, flags=re.IGNORECASE)
        else:
            if 'limit ' in query.lower():
                return query
            return f"{query.rstrip(';')} limit {limit}"

    def run_queries(
        self, queries, pkDatabaseType, databaseType=None, metadata=None, runQueryConfig=None
    ):
        results = {}
        if not queries:
            return {"queryResults": []}
        def _normalize_db_type(db_type):
            if not db_type:
                return None
            lowered = db_type.lower()
            if lowered in ("postgresql", "postgres"):
                return "postgres"
            return lowered

        normalized_metadata_db = _normalize_db_type(databaseType)
        normalized_backend_db = _normalize_db_type(pkDatabaseType)
        if (
            normalized_metadata_db
            and normalized_backend_db
            and normalized_metadata_db != normalized_backend_db
        ):
            return {"dbMismatched": True, "backendDatabaseType": pkDatabaseType}
        if runQueryConfig and runQueryConfig.get("arrayToMap"):
            mapped_array = array_to_map(
                queries,
                runQueryConfig.get("arrayToMap"),
                metadata,
                self.target_connection,
            )

            return {"queryResults": [], "mapped_array": mapped_array}
        elif runQueryConfig and runQueryConfig.get("getColumns"):
            query_results = self.target_connection.query(
                queries[0].strip().rstrip(";") + " limit 1000"
            )
            results["columns"] = [
                {
                    "fieldType": convert_type_to_postgres(result["dataTypeID"]),
                    "name": result["name"],
                    "displayName": result["name"],
                    "isVisible": True,
                    "field": result["name"],
                }
                for result in query_results["fields"]
            ]
        elif runQueryConfig and runQueryConfig.get("getColumnsForSchema"):
            query_results = []
            for table in queries:
                if not table.get("viewQuery") or (
                    not table.get("isSelectStar") and not table.get("customFieldInfo")
                ):
                    query_results.append(table)
                    continue

                limit = ""
                if runQueryConfig.get("limitBy"):
                    limit = f" limit {runQueryConfig.get('limitBy')}"

                try:
                    query_result = self.target_connection.query(
                        f"{table['viewQuery'].strip().rstrip(';')} {limit}"
                    )
                    columns = [
                        {
                            "fieldType": convert_type_to_postgres(field["dataTypeID"]),
                            "name": field["name"],
                            "displayName": field["name"],
                            "isVisible": True,
                            "field": field["name"],
                        }
                        for field in query_result["fields"]
                    ]
                    query_results.append(
                        {**table, "columns": columns, "rows": query_result["rows"]}
                    )
                except Exception as e:
                    query_results.append(
                        {**table, "error": f"Error fetching columns {e}"}
                    )

            results["queryResults"] = query_results
            if runQueryConfig.get("fieldsToRemove"):
                results["queryResults"] = [
                    {
                        **table,
                        "columns": [
                            column
                            for column in table.get("columns", [])
                            if column["name"] not in runQueryConfig["fieldsToRemove"]
                        ],
                    }
                    for table in query_results
                ]
            return results
        elif runQueryConfig and runQueryConfig.get("getTables"):
            tables = get_schema_tables_by_db(
                self.target_connection.database_type,
                self.target_connection.connection,
                runQueryConfig["schemaNames"],
            )
            schema = get_schema_column_info_by_db(
                self.target_connection.database_type,
                self.target_connection.connection,
                runQueryConfig["schemaNames"],
                tables,
            )
            results["queryResults"] = schema
        elif runQueryConfig and runQueryConfig.get("runIndividualQueries"):
            # so that one query doesn't fail the whole thing
            # the only reason this isn't the default behavior is for backwards compatibility
            query_results = []
            for query in queries:
                try:
                    run_query = query
                    if runQueryConfig.get("limitBy"):
                        run_query = self.apply_limit(query, runQueryConfig["limitBy"])
                    query_result = self.target_connection.query(run_query)
                    query_results.append(query_result)
                except Exception as e:
                    query_results.append({
                        "query": query,
                        "error": str(e),
                    })
            results["queryResults"] = query_results
        else:
            if runQueryConfig and runQueryConfig.get("limitThousand"):
                queries = [
                    query.strip().rstrip(";") + " limit 1000" for query in queries
                ]
            elif runQueryConfig and runQueryConfig.get("limitBy"):
                queries = [
                    query.strip().rstrip(";")
                    + f" limit {runQueryConfig.get('limitBy')}"
                    for query in queries
                ]
            query_results = [self.target_connection.query(query) for query in queries]
            results["queryResults"] = query_results
            if runQueryConfig and runQueryConfig.get("fieldsToRemove"):
                results["queryResults"] = [
                    remove_fields(query_result, runQueryConfig.get("fieldsToRemove"))
                    for query_result in results["queryResults"]
                ]
            if runQueryConfig and runQueryConfig.get("convertDatatypes"):
                for query_result in results["queryResults"]:
                    query_result["fields"] = [
                        {
                            "name": field["name"],
                            "displayName": field["name"],
                            "field": field["name"],
                            "isVisible": True,
                            "dataTypeID": field["dataTypeID"],
                            "fieldType": convert_type_to_postgres(field["dataTypeID"]),
                        }
                        for field in query_result["fields"]
                    ]

        return results
    
    def post_quill(self, path, payload):
        # Custom JSON Encoder to handle Enums
        class EnumEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Enum):
                    return obj.value  # Convert enum to its value (string in this case)
                return super().default(obj)
        
        url = f"{self.baseUrl}/sdk/{path}"
        # Set content type to application/json
        headers = {"Authorization": f"Bearer {self.private_key}", "Content-Type": "application/json"}
        encoded = json.dumps(payload, cls=EnumEncoder)
        response = requests.post(url, data=encoded, headers=headers)
        return response.json()
