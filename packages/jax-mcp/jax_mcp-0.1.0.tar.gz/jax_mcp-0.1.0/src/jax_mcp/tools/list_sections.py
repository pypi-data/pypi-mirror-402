"""List available JAX documentation sections."""

from jax_mcp.docs_source import DocsSource


async def list_sections(docs_source: DocsSource, category: str | None = None) -> str:
    """List available documentation sections.

    Args:
        docs_source: DocsSource instance
        category: Optional category filter ('concepts', 'gotchas', 'transforms',
                 'advanced', 'performance', 'api', 'examples')

    Returns:
        Formatted list with title, category, use_cases, and path for each section.
    """
    if category:
        sections = docs_source.get_sections_by_category(category)
        if not sections:
            return f"No sections found for category: {category}"
    else:
        sections = docs_source.list_sections()

    # Group by category for better readability
    categories = {}
    for section in sections:
        cat = section.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(section)

    lines = []
    category_order = ["concepts", "gotchas", "transforms", "advanced", "performance", "api", "examples"]

    for cat in category_order:
        if cat not in categories:
            continue

        lines.append(f"\n## {cat.upper()}")
        for section in categories[cat]:
            title = section.get("title", "Untitled")
            path = section.get("path", "")
            use_cases = section.get("use_cases", "general")
            lines.append(f"* {title} | use_cases: {use_cases} | path: {path}")

    return "\n".join(lines)
