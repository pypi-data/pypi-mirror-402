from __future__ import annotations

import inspect


def _format_docstring(doc: str) -> str:
    """Formats docstring into Markdown."""
    formatted_doc: list[str] = []
    in_special_section = False
    for line in doc.splitlines():
        stripped_line = line.strip()
        if stripped_line in ("Args:", "Returns:", "Raises:"):
            if formatted_doc and formatted_doc[-1].strip():
                formatted_doc.append("")
            formatted_doc.append(f"**{stripped_line}**")
            in_special_section = True
        elif (
            in_special_section
            and ":" in stripped_line
            and not line.startswith(stripped_line)
            and not stripped_line.startswith("**")
        ):
            # This looks like a parameter/return/exception definition
            # (it's indented and contains a colon)
            param_name, param_desc = stripped_line.split(":", 1)
            formatted_doc.append(f"- **{param_name.strip()}**:{param_desc}")
        elif in_special_section and line.startswith("    ") and stripped_line:
            # Continuation of a multiline description
            # We preserve some indentation for Markdown if needed, or just append
            formatted_doc.append(f"  {stripped_line}")
        else:
            if not stripped_line:
                in_special_section = False
            formatted_doc.append(line)
    return "\n".join(formatted_doc)


def get_documentation() -> str:
    """Returns a Markdown string with the documentation for all MTX Client functions."""
    import mtx_api.client.mtx_client  # noqa: PLC0415

    mtx_client_class = mtx_api.client.mtx_client.MTXClient

    lines = [
        "# MTX Client Documentation",
        "",
    ]
    client = mtx_client_class(base_url="http://dummy", client_id="dummy")
    subclients: list[tuple[str, object]] = []
    for attr_name in dir(client):
        if attr_name.startswith("_"):
            continue

        attr = getattr(client, attr_name)
        if inspect.isroutine(attr):
            continue

        subclients.append((attr_name, attr))

    # Sort subclients by name
    subclients.sort(key=lambda x: x[0])

    for subclient_name, attr in subclients:
        subclient_fns: list[object] = []
        for sub_attr_name in dir(attr):
            if sub_attr_name.startswith("_"):
                continue

            sub_attr = getattr(attr, sub_attr_name)
            if inspect.isroutine(sub_attr):
                subclient_fns.append(sub_attr)

        if not subclient_fns:
            continue

        # Sort functions by name
        subclient_fns.sort(key=lambda x: x.__name__ if hasattr(x, "__name__") else str(x))

        lines.append(f"## {subclient_name}")
        lines.append("")
        for fn in subclient_fns:
            try:
                sig = inspect.signature(fn)  # type: ignore[arg-type]
                name = fn.__name__ if hasattr(fn, "__name__") else str(fn)
                lines.append(f"### {name}")
                lines.append("")
                lines.append("#### Signature")
                lines.append("```python")
                lines.append(f"{subclient_name}.{name}{sig}")
                lines.append("```")
                lines.append("")
                lines.append("#### Docstring")
                doc = inspect.getdoc(fn) or ""
                lines.append(_format_docstring(doc))
                lines.append("")
            except (ValueError, TypeError):
                continue

    return "\n".join(lines)
