from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WebSnippet:
    url: str
    title: str
    snippet: str