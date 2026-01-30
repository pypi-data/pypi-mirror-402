"""Convert Yjs binary to markdown using pycrdt."""

import base64
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class YjsConverter:
    """
    Convert Yjs binary to markdown.

    Uses pycrdt (actively maintained, replaces abandoned y-py).
    Based on TypeScript implementation in copyTicketAsMarkdown.ts
    """

    def convert(
        self,
        yjs_binary_base64: Optional[str],
        plain_text_fallback: Optional[str] = None,
        attachments: Optional[List[dict]] = None,
    ) -> str:
        """
        Convert Yjs binary to markdown.

        Args:
            yjs_binary_base64: Base64-encoded Yjs binary
            plain_text_fallback: Plain text description to use as fallback
            attachments: List of attachment dicts with ai_description for inline image handling

        Returns:
            Markdown string
        """
        self._attachments = attachments or []

        # If we have Yjs binary, try to convert it
        if yjs_binary_base64:
            try:
                markdown = self._convert_with_pycrdt(yjs_binary_base64)
                if markdown and markdown.strip():
                    return markdown
            except Exception as e:
                logger.warning(f"Yjs conversion failed, falling back to plain text: {e}")

        # Fall back to plain text if Yjs conversion failed or returned empty
        if plain_text_fallback and plain_text_fallback.strip():
            return plain_text_fallback.strip()

        return "*No description provided*"

    def _convert_with_pycrdt(self, base64_str: str) -> str:
        """
        Use pycrdt library to parse Yjs binary and extract text.

        Args:
            base64_str: Base64-encoded Yjs binary

        Returns:
            Markdown string

        Raises:
            Exception: If conversion fails
        """
        try:
            from pycrdt import Doc, XmlElement, XmlText, XmlFragment
        except ImportError:
            raise Exception("pycrdt library not installed. Run: pip install pycrdt")

        # Decode base64
        binary_data = self._base64_to_bytes(base64_str)
        if not binary_data:
            raise Exception("Failed to decode base64")

        # Create Doc and apply update
        doc = Doc()
        doc.apply_update(binary_data)

        # Get the BlockNote editor fragment
        try:
            # pycrdt uses get() with type= parameter
            fragment = doc.get("blocknote-editor", type=XmlFragment)
        except Exception as e:
            raise Exception(f"Failed to get blocknote-editor fragment: {e}")

        if fragment is None:
            raise Exception("blocknote-editor fragment is None")

        # Extract text from fragment
        return self._extract_text_from_fragment(fragment)

    def _base64_to_bytes(self, base64_str: str) -> Optional[bytes]:
        """Convert base64 string to bytes."""
        try:
            if not base64_str or not isinstance(base64_str, str):
                return None

            cleaned = base64_str.strip()

            # Validate base64 format
            import re
            if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', cleaned):
                logger.warning("Invalid base64 format detected")
                return None

            return base64.b64decode(cleaned)
        except Exception as e:
            logger.warning(f"Failed to decode base64: {e}")
            return None

    def _extract_text_from_fragment(self, fragment) -> str:
        """
        Extract markdown text from XmlFragment.

        This mimics the TypeScript extractTextFromYDoc function.

        Args:
            fragment: XmlFragment containing BlockNote content

        Returns:
            Markdown string
        """
        from pycrdt import XmlElement, XmlText

        lines: List[str] = []

        def process_node(node, indent: int = 0, add_blank_line: bool = True):
            """Process a single XML node recursively."""
            try:
                if isinstance(node, XmlText):
                    # Handle text nodes - these are inline, no blank line
                    text = str(node).strip()
                    if text:
                        lines.append("  " * indent + text)

                elif isinstance(node, XmlElement):
                    # Handle element nodes
                    node_name = node.tag
                    children = list(node.children) if hasattr(node, "children") else []

                    # Collect text content from XmlText children
                    text_content = "".join(
                        str(child) for child in children if isinstance(child, XmlText)
                    ).strip()

                    # Node processing (debug removed)

                    # Process based on node type (matching BlockNote structure)

                    # BlockNote wrapper elements - just recurse into children
                    if node_name in ("blockGroup", "blockContainer"):
                        for child in children:
                            process_node(child, indent, add_blank_line)

                    # Actual content blocks
                    elif node_name == "heading" and text_content:
                        level = int(node.attributes.get("level", 1))
                        lines.append("#" * level + " " + text_content)
                        lines.append("")  # Blank line after heading

                    elif node_name == "paragraph" and text_content:
                        lines.append(text_content)
                        lines.append("")  # Blank line after paragraph

                    elif node_name == "quote" and text_content:
                        # BlockNote quote becomes markdown blockquote
                        lines.append("> " + text_content)
                        lines.append("")  # Blank line after quote

                    elif node_name == "bulletListItem" and text_content:
                        lines.append("  " * indent + "- " + text_content)
                        # Process nested lists
                        for child in children:
                            if isinstance(child, XmlElement):
                                process_node(child, indent + 1, add_blank_line=False)

                    elif node_name == "numberedListItem" and text_content:
                        lines.append("  " * indent + "1. " + text_content)
                        # Process nested lists
                        for child in children:
                            if isinstance(child, XmlElement):
                                process_node(child, indent + 1, add_blank_line=False)

                    elif node_name == "checkListItem":
                        checked = node.attributes.get("checked", "false") == "true"
                        checkbox = "[x]" if checked else "[ ]"
                        if text_content:
                            lines.append("  " * indent + f"- {checkbox} " + text_content)

                    elif node_name == "codeBlock":
                        language = node.attributes.get("language", "")
                        lines.append(f"```{language}")
                        if text_content:
                            lines.append(text_content)
                        lines.append("```")
                        lines.append("")

                    elif node_name == "image":
                        # Handle image nodes - show placeholder with AI description if available
                        url = node.attributes.get("url", "") or node.attributes.get("src", "")
                        name = node.attributes.get("name", "")
                        caption = node.attributes.get("caption", "")

                        # Try to find matching attachment by URL
                        ai_description = None
                        filename = name or "image"

                        for attachment in self._attachments:
                            att_url = attachment.get("url", "") or attachment.get("file_url", "")
                            att_filename = attachment.get("original_filename", "")
                            # Match by URL or filename
                            if (url and att_url and url in att_url) or \
                               (name and att_filename and name in att_filename) or \
                               (att_url and att_url in url):
                                ai_description = attachment.get("ai_description")
                                filename = att_filename or filename
                                break

                        lines.append(f"[Image: {filename}]")
                        if ai_description:
                            lines.append(f"*{ai_description}*")
                        elif caption:
                            lines.append(f"*{caption}*")
                        lines.append("")

                    elif node_name == "hardBreak":
                        # Hard breaks are inline - ignore them as we add blank lines between blocks
                        pass

                    elif node_name == "table":
                        # Handle table - recurse into rows
                        for child in children:
                            process_node(child, indent, add_blank_line=False)
                        lines.append("")

                    elif node_name == "tableRow":
                        # Collect cell contents for this row
                        row_cells = []
                        for child in children:
                            if isinstance(child, XmlElement) and child.tag in ("tableCell", "tableHeader"):
                                cell_text = "".join(
                                    str(c) for c in child.children if isinstance(c, XmlText)
                                ).strip()
                                row_cells.append(cell_text or " ")
                        if row_cells:
                            lines.append("| " + " | ".join(row_cells) + " |")

                    elif node_name in ("tableCell", "tableHeader"):
                        # Handled by tableRow
                        pass

                    elif node_name == "file":
                        # File attachment block
                        filename = node.attributes.get("name", "file")
                        lines.append(f"[File: {filename}]")
                        lines.append("")

                    elif node_name == "video":
                        # Video block
                        url = node.attributes.get("url", "")
                        name = node.attributes.get("name", "video")
                        lines.append(f"[Video: {name}]")
                        lines.append("")

                    elif node_name == "audio":
                        # Audio block
                        url = node.attributes.get("url", "")
                        name = node.attributes.get("name", "audio")
                        lines.append(f"[Audio: {name}]")
                        lines.append("")

                    elif node_name in ("divider", "horizontalRule"):
                        lines.append("---")
                        lines.append("")

                    elif node_name == "alert":
                        # Alert/callout block
                        alert_type = node.attributes.get("type", "info")
                        if text_content:
                            lines.append(f"> **{alert_type.upper()}:** {text_content}")
                            lines.append("")

                    # Handle empty paragraphs or unknown blocks
                    elif text_content:
                        lines.append(text_content)
                        lines.append("")

                    # Always process children for unknown types
                    elif node_name not in ("hardBreak", "tableCell", "tableHeader"):
                        for child in children:
                            process_node(child, indent, add_blank_line=True)

            except Exception as e:
                logger.debug(f"Error processing node: {e}")

        # Process all top-level children
        try:
            if hasattr(fragment, "children"):
                children_list = list(fragment.children)
                for child in children_list:
                    process_node(child)
            else:
                # Try iterating directly
                for child in fragment:
                    process_node(child)
        except Exception as e:
            logger.warning(f"Failed to iterate fragment: {e}")
            raise Exception(f"Could not iterate fragment children")

        result = "\n".join(lines).strip()
        return result if result else ""
