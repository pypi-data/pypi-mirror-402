def remove_fields(query_result, fields_to_remove):
    if not isinstance(query_result, dict):
        return query_result
    fields = [
        {"name": field["name"], "dataTypeID": field["dataTypeID"]}
        for field in (query_result.get("fields") or [])
        if field.get("name") not in fields_to_remove
    ]
    rows = []
    for row in query_result.get("rows") or []:
        if not isinstance(row, dict):
            rows.append(row)
            continue
        filtered = dict(row)
        for field in fields_to_remove:
            if field in filtered:
                del filtered[field]
        rows.append(filtered)
    return {"fields": fields, "rows": rows}


def array_to_map(queries, array_to_map, metadata, target_pool):
    mapped_array = []
    for i in range(len(queries)):
        query_result = target_pool.query(queries[i])
        if isinstance(query_result, dict):
            mapped_array.append(query_result.get("rows"))
        else:
            mapped_array.append([])
    return mapped_array
