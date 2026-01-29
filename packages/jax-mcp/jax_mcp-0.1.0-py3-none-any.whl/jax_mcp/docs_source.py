"""Documentation source handling - GitHub with caching and notebook parsing."""

import json
import os
import logging
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# GitHub raw content base URL
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/google/jax/main/docs"

# Default cache settings
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "jax-mcp"
DEFAULT_CACHE_TTL_HOURS = 24


# JAX documentation sections with use cases
# Organized by category for discoverability
JAX_SECTIONS = [
    # === CORE CONCEPTS (highest value) ===
    {
        "title": "Key Concepts",
        "path": "key-concepts",
        "category": "concepts",
        "use_cases": "always, overview, transformations, tracing, jaxprs, pytrees, api layers",
    },
    {
        "title": "Pytrees",
        "path": "pytrees",
        "category": "concepts",
        "use_cases": "always, nested data, model parameters, tree operations, jax.tree",
    },
    {
        "title": "Thinking in JAX",
        "path": "notebooks/thinking_in_jax",
        "category": "concepts",
        "use_cases": "always, mental model, functional programming, getting started",
    },
    {
        "title": "JIT Compilation",
        "path": "jit-compilation",
        "category": "concepts",
        "use_cases": "jit, compilation, tracing, static arguments, performance",
    },
    {
        "title": "Automatic Differentiation",
        "path": "automatic-differentiation",
        "category": "concepts",
        "use_cases": "grad, autodiff, gradients, jacobian, hessian, backpropagation",
    },
    {
        "title": "Random Numbers",
        "path": "random-numbers",
        "category": "concepts",
        "use_cases": "random, prng, keys, splitting, reproducibility",
    },
    # === GOTCHAS (critical for avoiding bugs) ===
    {
        "title": "Common Gotchas",
        "path": "notebooks/Common_Gotchas_in_JAX",
        "category": "gotchas",
        "use_cases": "always, debugging, mistakes, pure functions, in-place updates, immutability",
    },
    {
        "title": "FAQ",
        "path": "faq",
        "category": "gotchas",
        "use_cases": "troubleshooting, common questions, errors",
    },
    # === TRANSFORMS ===
    {
        "title": "Control Flow",
        "path": "control-flow",
        "category": "transforms",
        "use_cases": "cond, while_loop, fori_loop, scan, lax control flow",
    },
    {
        "title": "Autodiff Cookbook",
        "path": "notebooks/autodiff_cookbook",
        "category": "transforms",
        "use_cases": "grad patterns, jacobian, hessian, custom derivatives, stop_gradient",
    },
    {
        "title": "Custom Derivative Rules",
        "path": "notebooks/Custom_derivative_rules_for_Python_code",
        "category": "transforms",
        "use_cases": "custom_vjp, custom_jvp, custom gradients",
    },
    {
        "title": "Gradient Checkpointing",
        "path": "gradient-checkpointing",
        "category": "transforms",
        "use_cases": "remat, rematerialization, memory optimization, large models",
    },
    # === ADVANCED ===
    {
        "title": "Custom Pytrees",
        "path": "custom_pytrees",
        "category": "advanced",
        "use_cases": "register_pytree_node, custom containers, dataclasses",
    },
    {
        "title": "Distributed Arrays",
        "path": "notebooks/Distributed_arrays_and_automatic_parallelization",
        "category": "advanced",
        "use_cases": "sharding, parallelization, multi-device, distributed",
    },
    {
        "title": "Shard Map",
        "path": "notebooks/shard_map",
        "category": "advanced",
        "use_cases": "shard_map, manual sharding, SPMD",
    },
    {
        "title": "Multi-Process",
        "path": "multi_process",
        "category": "advanced",
        "use_cases": "multi-host, distributed training, jax.distributed",
    },
    # === PERFORMANCE ===
    {
        "title": "GPU Performance Tips",
        "path": "gpu_performance_tips",
        "category": "performance",
        "use_cases": "gpu, cuda, optimization, performance tuning",
    },
    {
        "title": "Profiling",
        "path": "profiling",
        "category": "performance",
        "use_cases": "profiling, tensorboard, performance analysis",
    },
    {
        "title": "Benchmarking",
        "path": "benchmarking",
        "category": "performance",
        "use_cases": "benchmarking, timing, block_until_ready",
    },
    # === API OVERVIEW (summaries, not full autodoc) ===
    {
        "title": "jax.numpy Overview",
        "path": "jax.numpy",
        "category": "api",
        "use_cases": "numpy, array operations, mathematical functions",
    },
    {
        "title": "jax.lax Overview",
        "path": "jax.lax",
        "category": "api",
        "use_cases": "lax, low-level operations, scan, conv, dot_general",
    },
    {
        "title": "jax.random Overview",
        "path": "jax.random",
        "category": "api",
        "use_cases": "random, distributions, sampling, prng",
    },
    {
        "title": "jax.nn Overview",
        "path": "jax.nn",
        "category": "api",
        "use_cases": "neural networks, activations, relu, softmax, initializers",
    },
    # === EXAMPLES ===
    {
        "title": "Neural Network Example",
        "path": "notebooks/Neural_Network_and_Data_Loading",
        "category": "examples",
        "use_cases": "neural network, training loop, mnist, data loading",
    },
    {
        "title": "Vectorized Log Probs",
        "path": "notebooks/vmapped_log_probs",
        "category": "examples",
        "use_cases": "vmap, probability, batching, vectorization",
    },
    {
        "title": "Convolutions Deep Dive",
        "path": "notebooks/convolutions",
        "category": "examples",
        "use_cases": "convolution, conv, lax.conv_general_dilated",
    },
]


class DocsSource:
    """Handles documentation fetching from GitHub with caching."""

    def __init__(self):
        self.local_path = os.environ.get("JAX_DOCS_PATH")
        self.cache_dir = Path(
            os.environ.get("JAX_MCP_CACHE_DIR", DEFAULT_CACHE_DIR)
        )
        self.cache_ttl = timedelta(
            hours=int(os.environ.get("JAX_MCP_CACHE_TTL", DEFAULT_CACHE_TTL_HOURS))
        )
        self.no_cache = os.environ.get("JAX_MCP_NO_CACHE", "0") == "1"

        if self.local_path:
            self.local_path = Path(self.local_path)
            if not self.local_path.exists():
                logger.warning(
                    f"JAX_DOCS_PATH={self.local_path} does not exist, falling back to GitHub"
                )
                self.local_path = None

        self.source_type = "local" if self.local_path else "github"
        logger.info(f"DocsSource initialized: {self.source_type}")

        # Ensure cache directory exists
        if not self.local_path:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def get_file(self, path: str) -> str:
        """Get a documentation file by path.

        Handles .md, .rst, and .ipynb files.

        Args:
            path: Relative path like 'pytrees' or 'notebooks/thinking_in_jax'

        Returns:
            File content as string (notebooks converted to markdown)
        """
        # Try different extensions
        for ext in [".md", ".rst", ".ipynb"]:
            full_path = f"{path}{ext}" if not path.endswith(ext) else path
            try:
                if self.local_path:
                    content = self._read_local(full_path)
                else:
                    content = await self._fetch_github(full_path)

                # Convert notebook to markdown if needed
                if full_path.endswith(".ipynb"):
                    content = self._notebook_to_markdown(content)

                return content
            except (FileNotFoundError, httpx.HTTPStatusError):
                continue

        raise FileNotFoundError(f"Doc not found: {path} (tried .md, .rst, .ipynb)")

    def _read_local(self, path: str) -> str:
        """Read from local filesystem."""
        file_path = self.local_path / path
        if not file_path.exists():
            raise FileNotFoundError(f"Doc not found: {file_path}")
        return file_path.read_text()

    async def _fetch_github(self, path: str) -> str:
        """Fetch from GitHub with caching."""
        # Check cache first
        cached = self._get_cached(path)
        if cached is not None:
            logger.debug(f"Cache hit: {path}")
            return cached

        # Fetch from GitHub
        url = f"{GITHUB_RAW_BASE}/{path}"
        logger.info(f"Fetching: {url}")

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            content = response.text

        # Cache the result
        self._set_cached(path, content)
        return content

    def _get_cached(self, path: str) -> Optional[str]:
        """Get cached content if valid."""
        if self.no_cache:
            return None

        cache_file = self.cache_dir / "docs" / path
        meta_file = self.cache_dir / "meta" / f"{path}.json"

        if not cache_file.exists() or not meta_file.exists():
            return None

        # Check TTL
        try:
            meta = json.loads(meta_file.read_text())
            cached_at = datetime.fromisoformat(meta.get("fetched_at", "2000-01-01"))
            if datetime.now() - cached_at > self.cache_ttl:
                logger.debug(f"Cache expired: {path}")
                return None
        except (json.JSONDecodeError, ValueError):
            return None

        return cache_file.read_text()

    def _set_cached(self, path: str, content: str):
        """Cache content to disk."""
        if self.no_cache:
            return

        cache_file = self.cache_dir / "docs" / path
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(content)

        # Update metadata
        meta_file = self.cache_dir / "meta" / f"{path}.json"
        meta_file.parent.mkdir(parents=True, exist_ok=True)
        meta = {"fetched_at": datetime.now().isoformat()}
        meta_file.write_text(json.dumps(meta, indent=2))

    def _notebook_to_markdown(self, notebook_json: str) -> str:
        """Convert Jupyter notebook JSON to markdown.

        Extracts markdown cells and code cells into readable format.
        """
        try:
            nb = json.loads(notebook_json)
        except json.JSONDecodeError:
            return notebook_json  # Return as-is if not valid JSON

        cells = nb.get("cells", [])
        output_parts = []

        for cell in cells:
            cell_type = cell.get("cell_type", "")
            source = "".join(cell.get("source", []))

            if cell_type == "markdown":
                output_parts.append(source)
            elif cell_type == "code":
                # Skip empty code cells
                if source.strip():
                    output_parts.append(f"```python\n{source}\n```")

                # Include text outputs (skip images/html)
                outputs = cell.get("outputs", [])
                for out in outputs:
                    if out.get("output_type") == "stream":
                        text = "".join(out.get("text", []))
                        if text.strip():
                            output_parts.append(f"```\n{text}\n```")
                    elif out.get("output_type") in ("execute_result", "display_data"):
                        data = out.get("data", {})
                        if "text/plain" in data:
                            text = "".join(data["text/plain"])
                            if text.strip() and len(text) < 500:  # Skip large outputs
                                output_parts.append(f"Output:\n```\n{text}\n```")

        return "\n\n".join(output_parts)

    def list_sections(self) -> list[dict]:
        """List all documentation sections.

        Returns:
            List of dicts with 'title', 'path', 'category', and 'use_cases' keys
        """
        return JAX_SECTIONS.copy()

    def get_sections_by_category(self, category: str) -> list[dict]:
        """Get sections filtered by category.

        Args:
            category: One of 'concepts', 'gotchas', 'transforms', 'advanced',
                     'performance', 'api', 'examples'
        """
        return [s for s in JAX_SECTIONS if s.get("category") == category]

    def find_section(self, query: str) -> Optional[dict]:
        """Find a section by title or path (fuzzy match).

        Args:
            query: Section title or path to search for

        Returns:
            Matching section dict or None
        """
        query_lower = query.lower().strip()

        # Exact path match
        for section in JAX_SECTIONS:
            if section["path"].lower() == query_lower:
                return section

        # Exact title match
        for section in JAX_SECTIONS:
            if section["title"].lower() == query_lower:
                return section

        # Partial match in title or path
        for section in JAX_SECTIONS:
            if query_lower in section["title"].lower():
                return section
            if query_lower in section["path"].lower():
                return section

        # Match in use_cases
        for section in JAX_SECTIONS:
            if query_lower in section.get("use_cases", "").lower():
                return section

        return None
