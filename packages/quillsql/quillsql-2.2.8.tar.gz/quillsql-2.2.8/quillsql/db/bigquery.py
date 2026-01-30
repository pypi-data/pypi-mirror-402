from google.cloud import bigquery
from google.oauth2 import service_account
import json
import re


def format_bigquery_config(connection_string):
    # find the start of the json {
    json_start = connection_string.find("{")
    if json_start == -1:
        raise Exception("Invalid input string. No JSON data found.")

    dataset_name = connection_string[0:json_start].strip()
    json_string = connection_string[json_start:]
    try:
        service_account = json.loads(json_string)
        if not service_account.get("project_id") or not service_account.get(
            "private_key"
        ):
            raise Exception(
                "Invalid service account JSON. Required fields are missing."
            )

        return {
            "dataset_id": dataset_name,
            "project": service_account.get("project_id"),
            "credentials": service_account,
        }
    except (ValueError, TypeError) as e:
        print("Invalid service account JSON.", e)
    return connection_string


def connect_to_bigquery(config, using_connection_string):
    if using_connection_string:
        credentials = service_account.Credentials.from_service_account_info(
            config["credentials"]
        )
    else:
        credentials = service_account.Credentials.from_service_account_file(
            config["service_account_file_path"]
        )
    return bigquery.Client(project=config["project"], credentials=credentials)


def run_query_big_query(query, connection):
    query_job = connection.query(query)
    result = query_job.result()
    rows = [dict(row) for row in result]
    fields = [
        {
            "name": field.name,
            "dataTypeID": convert_bigquery_to_postgres(field.field_type),
        }
        for field in result.schema
    ]
    # TODO CONVERT to postgres types

    return {"rows": rows, "fields": fields}


def get_tables_by_schema_big_query(connection, schema_names):
    all_table = []
    for schema_name in schema_names:
        dataset_ref = connection.dataset(schema_name)
        tables = connection.list_tables(dataset_ref)
        for table in tables:
            cur_table = {}
            cur_table["table_name"] = table.table_id
            cur_table["schema_name"] = schema_name
            all_table.append(cur_table)
    return all_table


def get_schema_column_info_big_query(connection, schema_name, table_names):
    all_columns = []
    for table_name in table_names:
        table_ref = connection.dataset(table_name["schema_name"]).table(
            table_name["table_name"]
        )
        table = connection.get_table(table_ref)
        columns = []
        for field in table.schema:
            columns.append(
                {
                    "columnName": field.name,
                    "displayName": field.name,
                    "dataTypeId": convert_bigquery_to_postgres(field.field_type),
                    "fieldType": field.field_type,
                }
            )
        all_columns.append(
            {
                "tableName": table_name["schema_name"] + "." + table_name["table_name"],
                "displayName": table_name["schema_name"]
                + "."
                + table_name["table_name"],
                "columns": columns,
            }
        )
    return all_columns


def infer_schema_big_query(elem):
    # compare elem with regex
    if isinstance(elem, list):
        return 23
    if isinstance(elem, object):
        if re.match(r"/^\d{4}-\d{2}-\d{2}$/", elem.get("value")):
            return 1082
        elif re.match(r"/^\d{2}\/\d{2}\/\d{2,4}$/", elem.get("value")):
            return 1082
        elif re.match(
            r"/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/", elem.get("value")
        ):
            return 1184
        elif re.match(
            r"/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/", elem.get("value")
        ):
            return 1114
        elif re.match(r"/^\d{2}:\d{2}:\d{2}$/", elem.get("value")):
            return 1083
    if isinstance(elem, str):
        if re.match(r"/^\d{4}-\d{2}-\d{2}$/", elem):
            return 1082
        elif re.match(r"/^\d{2}\/\d{2}\/\d{2,4}$/", elem):
            return 1082
        elif re.match(r"/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/", elem):
            return 1184
        elif re.match(r"/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/", elem):
            return 1114
        elif re.match(r"/^\d{2}:\d{2}:\d{2}$/", elem):
            return 1083
        else:
            return 1043
    return 1043


def convert_bigquery_to_postgres(value):
    type_to_oid = {
        "VARCHAR": 1043,
        "INTEGER": 23,
        "FLOAT": 700,
        "TIMESTAMP": 1114,
        "DATE": 1082,
        "BOOL": 16,
    }
    return type_to_oid.get(value.upper()) or 1043
