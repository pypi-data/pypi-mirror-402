"""Retrieve JAX documentation content."""

from jax_mcp.docs_source import DocsSource


async def get_documentation(
    docs_source: DocsSource,
    section: str | list[str],
) -> str:
    """Retrieve full documentation for requested sections.

    Args:
        docs_source: DocsSource instance
        section: Section name(s) or path(s). Can be:
            - Single string: "pytrees", "key-concepts"
            - List: ["pytrees", "jit-compilation"]
            - Path: "notebooks/thinking_in_jax"

    Returns:
        Documentation content as markdown string.
    """
    # Normalize to list
    if isinstance(section, str):
        sections = [section]
    else:
        sections = list(section)

    results = []

    for sec in sections:
        # Try to find matching section in our catalog
        section_info = docs_source.find_section(sec)

        if section_info:
            path = section_info["path"]
            title = section_info["title"]
        else:
            # Use as-is (might be a direct path)
            path = sec
            title = sec

        try:
            content = await docs_source.get_file(path)
            results.append(f"# {title}\n\n{content}")
        except FileNotFoundError as e:
            results.append(f"# {title}\n\nError: {e}")

    return "\n\n---\n\n".join(results)
