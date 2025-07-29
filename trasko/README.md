# Trasko Screen Building Overview

This document summarizes how the AZ_trasko project builds screens using the
`hope.js` library.  Metadata is loaded from the server and transformed into
GraphQL schemas, filters and loaders that feed Vue components.

## Metadata Module

The metadata service loads the structure described in `server/docs` and then
processes references with the loader module.  After `processTypeReferences` the
metadata object contains fully linked types and methods ready for use.  The same
service exposes a GraphQL module used to generate query schemas.

## GraphQL Module

The GraphQL module generates query schemas and filter structures.  Methods such
as `getQuerySchemaForMethod`, `getFilterForMethod`, `setFilterValuesFromQuery`
and `getFilterFieldValues` operate on the metadata tree.

Filters can be customized by including or excluding fields and by removing words from captions. The returned object describes each filter field with the value stored in `data.value`.

## Loader Module

Loaders manage fetching data for forms via GraphQL and exposing the results to the Vue component. A loader is created per page using a standard template and can include pagination support.

The loader obtains GraphQL objects from metadata, fills filter values from URL
parameters, and executes the query. Pagination methods such as `prevPage`,
`nextPage` and `setRowsPerPage` manipulate the filter and refresh the query.
Each Vue page creates its own `loader.js` which extends a standard template from
`metadata/modules/loader`.

## Field Builder

Vue components build form fields based on metadata using the fieldBuilder utility. Each field definition from metadata is transformed into Vue components with labels, hints and validation. (See `client/src/lib/fieldBuilder` in the source repository.)

Hope's `link` function connects static metadata with runtime code, producing the model accessible in both the client and server. The client boot file `model.js` links the configuration with the generated code so components can access `this.$model`.

## Python Example

The file `metadata.py` contains a helper `generate_filter` that converts a method definition from `model.json` into a filter dictionary. A basic usage example:

```python
from trasko.metadata import generate_filter

method = {
    "arguments": {
        "list": [
            {"name": "id", "type": "string", "init": "abc", "extra": {"label": "ID"}},
            {"name": "active", "type": "boolean", "init": True, "extra": {"label": "Active"}},
        ]
    }
}

filters = generate_filter(method)
print(filters["id"])
```

The same module provides `generate_query_schema` which converts a method
definition into a plain GraphQL query string:

```python
from trasko.metadata import generate_query_schema

query = generate_query_schema({
    "name": "listRequests",
    "arguments": {"list": [{"name": "active", "type": "Boolean"}]},
    "result": {"list": [{"name": "count"}]}
})
print(query)
```

See `tests/test_trasko_metadata.py` for unit tests of these helpers.
