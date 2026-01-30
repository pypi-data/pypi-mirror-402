import os
import psycopg2
from psycopg2.extensions import make_dsn
from quillsql.assets.pgtypes import PG_TYPES


def format_postgres(connection_string):
    def to_dsn(conn):
        return make_dsn(conn) if "://" in conn else conn

    return to_dsn(connection_string)


def connect_to_postgres(config, usingConnectionString):
    os.environ['PGGSSENCMODE'] = 'disable' # https://github.com/psycopg/psycopg2/issues/1084
    if usingConnectionString:
        return psycopg2.connect(config)
    else:
        return psycopg2.connect(
            database=config["dbname"],
            user=config["user"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
        )


def run_query_postgres(query, connection):
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    fields = [{"name": desc[0], "dataTypeID": desc[1]} for desc in cursor.description]
    cursor.close()
    rows_dict = [dict(zip([field["name"] for field in fields], row)) for row in result]
    return {"rows": rows_dict, "fields": fields}


def disconnect_from_postgres(connection):
    connection.close()
    return


# getTablesBySchemaPostgres


def get_tables_by_schema_postgres(connection, schema_names):
    all_tables = []
    for schema_name in schema_names:
        query = f"""
            SELECT table_name, table_schema
            FROM information_schema.tables
            WHERE table_schema = '{schema_name}'

            UNION

            SELECT c.relname as table_name, n.nspname as table_schema
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = '{schema_name}' 
            AND c.relkind = 'm';
            """
        results = run_query_postgres(query, connection)
        for row in results["rows"]:
            cur_table = {}
            cur_table["table_name"] = row["table_name"]
            cur_table["schema_name"] = row["table_schema"]
            all_tables.append(cur_table)
    return all_tables


# getSchemaColumnInfoPostgres


def get_schema_column_info_postgres(connection, schema_name, table_names):
    all_columns = []
    for table_name in table_names:
        query = f"""
            SELECT column_name as "column_name", udt_name as "field_type", ordinal_position as "sort_number"
            FROM information_schema.columns
            WHERE table_schema = '{table_name['schema_name']}' 
            AND table_name = '{table_name['table_name']}'
            
            UNION

            SELECT a.attname as "column_name", t.typname as "field_type", a.attnum as "sort_number"
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            JOIN pg_type t ON a.atttypid = t.oid
            WHERE n.nspname = '{table_name['schema_name']}'
                AND c.relname = '{table_name['table_name']}'
                AND c.relkind = 'm'
                AND a.attnum > 0
                AND NOT a.attisdropped
            ORDER BY "sort_number"
            """
        results = run_query_postgres(query, connection)
        columns = []
        for row in results["rows"]:
            pg_type = next(
                (
                    pg_type
                    for pg_type in PG_TYPES
                    if pg_type["typname"] == row["field_type"]
                ),
                None,
            )
            if pg_type is None:
                pg_type = 1043
            columns.append(
                {
                    "columnName": row["column_name"],
                    "displayName": row["column_name"],
                    "dataTypeID": pg_type["oid"],
                    "fieldType": row["field_type"],
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
