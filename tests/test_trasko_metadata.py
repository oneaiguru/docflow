from trasko.metadata import generate_filter, generate_query_schema


def test_generate_filter_basic():
    method = {
        "arguments": {
            "list": [
                {
                    "name": "id",
                    "type": "string",
                    "init": "abc",
                    "extra": {"label": "ID", "description": "Identifier"},
                },
                {
                    "name": "active",
                    "type": "boolean",
                    "init": True,
                    "extra": {"label": "Active"},
                },
            ]
        }
    }
    res = generate_filter(method)
    assert res["id"]["name"] == "ID"
    assert res["id"]["type"] == "string"
    assert res["id"]["data"]["value"] == "abc"
    assert res["active"]["default"] is True


def test_generate_query_schema_basic():
    method = {
        "name": "listRequests",
        "arguments": {"list": [
            {"name": "active", "type": "Boolean", "required": True}
        ]},
        "result": {"list": [
            {"name": "count", "type": "Int"},
            {"name": "items", "fields": [
                {"name": "id", "type": "ID"}
            ]}
        ]}
    }
    query = generate_query_schema(method)
    assert "query listRequests(" in query
    assert "$active: Boolean!" in query
    assert "listRequests(active: $active, context: $context)" in query
    assert "count" in query and "items" in query and "id" in query
