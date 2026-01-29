"""
Context resolvers for automatic frontmatter context injection.

This module provides resolvers for different context types that can be
automatically detected and injected from file frontmatter without explicit
configuration.

Supported context types:
- file: Include content from another file (relative/absolute paths)
- dir: Recursively scan directory and include file contents
- url: Fetch content from HTTP endpoint
- rellink: Resolve Hugo content paths (path.md or path/_index.md)
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


class BaseContextResolver:
    """Abstract base class for context resolvers."""

    def __init__(self, base_path: str, project_path: str, logger):
        """
        Initialize the resolver.

        Args:
            base_path: Base path for relative path resolution
            project_path: Root path of the project
            logger: Logger instance for logging messages
        """
        self.base_path = base_path
        self.project_path = project_path
        self.logger = logger

    def resolve(self, value: str) -> Optional[str]:
        """
        Resolve the context item and return formatted content.

        Args:
            value: The context value to resolve

        Returns:
            Formatted context message or None if resolution fails
        """
        raise NotImplementedError("Subclasses must implement resolve()")


class FileResolver(BaseContextResolver):
    """Resolves file: context items."""

    def resolve(self, value: str) -> Optional[str]:
        """
        Resolve file path and read content.

        Supports both relative and absolute paths, including home directory expansion.

        Args:
            value: File path (relative, absolute, or with ~/ for home directory)

        Returns:
            File content with metadata or None if file not found
        """
        # Expand home directory if path starts with ~/
        if value.startswith("~/"):
            value = os.path.expanduser(value)

        # Handle absolute paths
        if os.path.isabs(value):
            file_path = value
        else:
            # Try relative to base_path first
            file_path = os.path.join(self.base_path, value)
            if not os.path.isfile(file_path):
                # Try relative to project_path
                file_path = os.path.join(self.project_path, value)

        if not os.path.isfile(file_path):
            self.logger.warning(f"File not found for context injection: {value}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return format_context_message(content, "file", value)
        except Exception as exception_error:
            self.logger.error(f"Failed to read file {file_path}: {exception_error}")
            return None


class DirResolver(BaseContextResolver):
    """Resolves dir: context items."""

    def resolve(self, value: str) -> Optional[str]:
        """
        Resolve directory path and recursively scan for files.

        Args:
            value: Directory path (relative or absolute)

        Returns:
            Combined content of all files with metadata or None if directory not found
        """
        # Handle absolute paths
        if os.path.isabs(value):
            dir_path = value
        else:
            # Try relative to base_path first
            dir_path = os.path.join(self.base_path, value)
            if not os.path.isdir(dir_path):
                # Try relative to project_path
                dir_path = os.path.join(self.project_path, value)

        if not os.path.isdir(dir_path):
            self.logger.warning(f"Directory not found for context injection: {value}")
            return None

        files_content = []
        try:
            for root, _dirs, filenames in os.walk(dir_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        rel_path = os.path.relpath(file_path, self.project_path)
                        files_content.append(format_context_message(content, "file", rel_path))
                    except Exception as exception_error:
                        self.logger.warning(f"Failed to read file {file_path}: {exception_error}")
                        continue

            if not files_content:
                self.logger.warning(f"No readable files found in directory: {value}")
                return None

            return "\n\n".join(files_content)
        except Exception as exception_error:
            self.logger.error(f"Failed to scan directory {dir_path}: {exception_error}")
            return None


class URLResolver(BaseContextResolver):
    """Resolves url: context items."""

    def resolve(self, value: str) -> Optional[str]:
        """
        Fetch content from HTTP endpoint.

        Args:
            value: URL to fetch

        Returns:
            URL content with metadata or None if fetch fails
        """
        try:
            # Set timeout to 10 seconds
            with urlopen(value, timeout=10) as response:
                content = response.read().decode("utf-8")
            return format_context_message(content, "url", value)
        except HTTPError as exception_error:
            self.logger.error(f"HTTP error fetching URL {value}: {exception_error.code} {exception_error.reason}")
            return None
        except URLError as exception_error:
            self.logger.error(f"URL error fetching {value}: {exception_error.reason}")
            return None
        except Exception as exception_error:
            self.logger.error(f"Failed to fetch URL {value}: {exception_error}")
            return None


class RelinkResolver(BaseContextResolver):
    """Resolves rellink: context items for Hugo content patterns."""

    def resolve(self, value: str) -> Optional[str]:
        """
        Resolve Hugo content paths.

        Tries multiple patterns:
        - path.md
        - path/_index.md
        - Multilingual: path.LANG.md, path/_index.LANG.md

        Args:
            value: Hugo content path (e.g., /docs/concepts/dev)

        Returns:
            File content with metadata or None if not found
        """
        # Remove leading slash if present
        clean_path = value.lstrip("/")

        # Look for content directory
        content_dir = os.path.join(self.project_path, "content")
        if not os.path.isdir(content_dir):
            self.logger.warning(f"No content directory found for rellink: {value}")
            return None

        # Try different patterns
        patterns = [
            f"{clean_path}.md",
            f"{clean_path}/_index.md",
            f"{clean_path}/index.md",
        ]

        # Add multilingual patterns (common Hugo languages)
        for lang in ["en", "es", "fr", "de", "nl", "pt", "ja", "zh"]:
            patterns.extend(
                [
                    f"{clean_path}.{lang}.md",
                    f"{clean_path}/_index.{lang}.md",
                    f"{clean_path}/index.{lang}.md",
                ]
            )

        for pattern in patterns:
            file_path = os.path.join(content_dir, pattern)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    return format_context_message(content, "rellink", value)
                except Exception as exception_error:
                    self.logger.error(f"Failed to read rellink file {file_path}: {exception_error}")
                    return None

        self.logger.warning(
            f"Hugo rellink not found: {value} (tried patterns: {', '.join(patterns[:3])} and multilingual variants)"
        )
        return None


def format_context_message(content: str, source_type: str, source_path: str) -> str:
    """
    Format context content with metadata and source attribution.

    Args:
        content: The content to format
        source_type: Type of source (file, url, rellink)
        source_path: Path or URL of the source

    Returns:
        Formatted message with metadata
    """
    lines = content.split("\n")
    line_count = len(lines)
    char_count = len(content)

    header = f"--- Context from {source_type}: {source_path} ---"
    footer = f"--- End of {source_type} context ({line_count} lines, {char_count} characters) ---"

    return f"{header}\n{content}\n{footer}"


def resolve_context_item(item: Dict[str, Any], base_path: str, project_path: str, logger) -> Optional[str]:
    """
    Resolve a single context item based on its type.

    Args:
        item: Context item dictionary with keys like 'file', 'url', 'dir', 'rellink'
        base_path: Base path for relative path resolution
        project_path: Root path of the project
        logger: Logger instance for logging messages

    Returns:
        Resolved context message or None if resolution fails
    """
    if not isinstance(item, dict):
        logger.warning(f"Invalid context item (expected dict): {item}")
        return None

    # Determine which resolver to use based on the key
    if "file" in item:
        resolver = FileResolver(base_path, project_path, logger)
        return resolver.resolve(item["file"])
    elif "dir" in item:
        resolver = DirResolver(base_path, project_path, logger)
        return resolver.resolve(item["dir"])
    elif "url" in item:
        resolver = URLResolver(base_path, project_path, logger)
        return resolver.resolve(item["url"])
    elif "rellink" in item:
        resolver = RelinkResolver(base_path, project_path, logger)
        return resolver.resolve(item["rellink"])
    else:
        logger.warning(f"Unknown context type in item: {item}")
        return None
