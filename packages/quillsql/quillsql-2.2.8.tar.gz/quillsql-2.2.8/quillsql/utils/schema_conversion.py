from quillsql.assets.pgtypes import PG_TYPES


def convert_type_to_postgres(data_type_id):
    # find the object in PG_TYPES that matches the type
    pg_type = next(
        (pg_type for pg_type in PG_TYPES if pg_type["oid"] == data_type_id), None
    )
    return pg_type["typname"] if pg_type else data_type_id
