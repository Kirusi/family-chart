"""Shared utilities."""

import json
import re


class Utils:
    """Shared utilities."""

    @staticmethod
    def extract_json(text):
        """Extract json embedded in the middle of a string."""
        # Find the index of the first opening curly brace
        if text:
            match = re.search(r"\{", text)
            if not match:
                return None

            start_index = match.start()

            # Use raw_decode starting from the brace
            decoder = json.JSONDecoder()
            try:
                data, end_index = decoder.raw_decode(text[start_index:])
                return data
            except json.JSONDecodeError:
                return None
        else:
            return None
