from typing import Dict, Any


def generate_filter(method: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a filter structure from a method definition.

    Parameters
    ----------
    method: dict
        A method definition similar to those in AZ_trasko `model.json`.

    Returns
    -------
    dict
        Mapping of field names to filter descriptors with default values.
    """
    result: Dict[str, Any] = {}
    arguments = method.get("arguments", {}).get("list", [])
    for field in arguments:
        name = field["name"]
        extra = field.get("extra", {})
        descriptor = {
            "name": extra.get("label", name),
            "description": extra.get("description", ""),
            "type": field.get("type"),
            "isArray": bool(field.get("array")),
            "default": field.get("init"),
            "data": {"value": field.get("init")},
        }
        result[name] = descriptor
    return result


def generate_query_schema(method: Dict[str, Any]) -> str:
    """Generate a GraphQL query string from a method definition.

    Parameters
    ----------
    method: dict
        Structure describing a method, similar to AZ_trasko ``model.json``.

    Returns
    -------
    str
        GraphQL query string for executing the method.
    """
    name = method.get("name", "Query")

    args = []
    call_args = []
    for field in method.get("arguments", {}).get("list", []):
        arg_name = field["name"]
        arg_type = field.get("type", "String")
        if field.get("array"):
            arg_type = f"[{arg_type}]"
        if field.get("required"):
            arg_type += "!"
        args.append(f"${arg_name}: {arg_type}")
        call_args.append(f"{arg_name}: ${arg_name}")

    args.append("$context: String")
    call_args.append("context: $context")

    lines = [f"query {name}({', '.join(args)}) {{", f"  {name}({', '.join(call_args)}) {{"]

    def render_fields(fields, indent=4):
        for f in fields:
            fname = f["name"]
            sub = f.get("fields")
            if sub:
                lines.append(" " * indent + f"{fname} {{")
                render_fields(sub, indent + 2)
                lines.append(" " * indent + "}")
            else:
                lines.append(" " * indent + fname)

    result_fields = method.get("result", {}).get("list")
    if result_fields is None and isinstance(method.get("result"), dict):
        result_fields = [{"name": k, **v} for k, v in method["result"].items()]
    render_fields(result_fields or [])

    lines.append("  }")
    lines.append("}")
    return "\n".join(lines)
