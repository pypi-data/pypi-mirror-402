import re

from pyligent.core.action import Action, BacktrackAction, DoneAction, NodeAction


class ActionParser:
    # -------------------------------------------------------------------------
    # Regex Constants - Extract content from tags, ignoring surrounding text
    # -------------------------------------------------------------------------

    # Extract content between <node>...</node> tags with explicit ID
    # Pattern: <node> ID Content (non-greedy until closing tag or end)
    # Captures: Group 1 (ID), Group 2 (Content)
    _RE_NODE_ID = re.compile(
        r"[<(\[]node[>)\]]\s*(\d+)\s+(.*?)(?:[<(\[]/node[>)\]]|\s*$)",
        re.S | re.IGNORECASE | re.DOTALL,
    )

    # Extract content between <node>...</node> tags without ID
    # Pattern: <node> Content (non-greedy until closing tag or end)
    # Captures: Group 1 (Content)
    _RE_NODE_NO_ID = re.compile(
        r"[<(\[]node[>)\]]\s*(.*?)(?:[<(\[]/node[>)\]]|\s*$)",
        re.S | re.IGNORECASE | re.DOTALL,
    )

    # Extract ID from <backtrack> tag
    # Pattern: <backtrack> ID
    # Captures: Group 1 (ID)
    _RE_BACK = re.compile(r"[<(\[]backtrack[>)\]]\s*(\d+)", re.IGNORECASE)

    # Extract content between <done>...</done> tags
    # Pattern: <done> Content (non-greedy until closing tag or end)
    # Captures: Group 1 (Content)
    _RE_DONE = re.compile(
        r"[<(\[]done[>)\]]\s*(.*?)(?:[<(\[]/done[>)\]]|\s*$)",
        re.S | re.IGNORECASE | re.DOTALL,
    )

    # Matches: "answer is ..." or "answer: ..."
    # Captures: Group 1 (Content after answer)
    _RE_ANSWER = re.compile(
        r"answer\s*(?:is|:)\s*(.*?)(?:[.!]+\s*)?$", re.S | re.IGNORECASE
    )

    # Malformed tag detection
    _RE_MALFORMED_TAG = re.compile(r"[<(\[](backtrack|done)", re.IGNORECASE)

    # Pattern to detect and remove malformed closing tags from content
    # Matches: </something, </som>, </, etc. at the end of content
    _RE_MALFORMED_CLOSING = re.compile(r"[<(\[]/[a-z]*[>)\]]?$", re.IGNORECASE)

    @staticmethod
    def _clean_content(content: str) -> str:
        """
        Clean extracted content by removing extraneous whitespace and artifacts.

        This includes:
        - Trimming whitespace
        - Removing malformed closing tags (e.g., </nod, </node, </)
        - Removing nested malformed tags within content

        Args:
            content: Raw content string to clean

        Returns:
            Cleaned content string
        """
        content = content.strip()

        # Remove malformed closing tags at the end
        # Examples: "</node", "</nod", "</", etc.
        content = ActionParser._RE_MALFORMED_CLOSING.sub("", content).strip()

        return content

    @staticmethod
    def _strip_trailing_punctuation(content: str) -> str:
        """
        Remove trailing punctuation marks from content.

        Args:
            content: Content string to process

        Returns:
            Content with trailing punctuation removed
        """
        return content.rstrip(".!?").strip()

    @staticmethod
    def parse(text: str, node_id: int) -> Action:
        """
        Parse action from text, extracting content only from within tags.

        This function handles cases where LLM output contains extra text
        outside tags or malformed closing tags. For example:
            "Some comment <node>Needed stuff</nod" -> NodeAction with "Needed stuff"
            "Extra text <done>Final answer</done>" -> DoneAction with "Final answer"
            "<node>6 (stack red yellow)</node>" -> NodeAction with "(stack red yellow)"

        Parsing priority (evaluated in order):
        1. Backtrack actions: <backtrack> ID
        2. Done actions: <done> content
        3. Answer patterns: "answer is/: content"
        4. Malformed tag detection
        5. Node with explicit ID: <node> ID content
        6. Node without ID: <node> content
        7. Fallback: Wrap raw text in NodeAction

        Args:
            text: Raw text to parse (may contain extra text outside tags)
            node_id: Current node ID for fallback NodeAction

        Returns:
            Parsed action (NodeAction, BacktrackAction, or DoneAction)
        """
        text = text.strip()

        # Tier 1: Backtrack action
        if m := ActionParser._RE_BACK.search(text):
            try:
                target_id = int(m.group(1))
                return BacktrackAction(
                    target_id, reason=f"Model backtrack to {target_id}"
                )
            except ValueError:
                pass

        # Tier 2: Done action - extract content from within tags
        if m := ActionParser._RE_DONE.search(text):
            content = ActionParser._clean_content(m.group(1))
            if content:  # Only return if there's actual content
                return DoneAction(content)

        # Tier 3: Detect "answer is/:" patterns
        if m := ActionParser._RE_ANSWER.search(text):
            content = ActionParser._clean_content(m.group(1))
            content = ActionParser._strip_trailing_punctuation(content)
            if content:
                return DoneAction(content)

        # Tier 4: Detect malformed specific actions
        if ActionParser._RE_MALFORMED_TAG.search(text):
            return NodeAction(node_id, f'Malformed action attempt: "{text}"')

        # Tier 5: Node with explicit ID - extract content from within tags
        if m := ActionParser._RE_NODE_ID.search(text):
            try:
                extracted_id = int(m.group(1))
                content = ActionParser._clean_content(m.group(2))
                return NodeAction(extracted_id, content)
            except ValueError:
                pass

        # Tier 6: Node without ID - extract content from within tags
        if m := ActionParser._RE_NODE_NO_ID.search(text):
            content = ActionParser._clean_content(m.group(1))
            return NodeAction(node_id, content)

        # Tier 7: Fallback for raw text without tags
        return NodeAction(node_id, text)
