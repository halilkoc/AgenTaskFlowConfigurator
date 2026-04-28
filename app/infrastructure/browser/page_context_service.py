from __future__ import annotations
from typing import List, Tuple
from playwright.async_api import Frame, Page
class PageContextService:
    async def get_all_contexts(self, page: Page) -> List[Tuple[str, Frame | Page]]:
        contexts: List[Tuple[str, Frame | Page]] = [("main", page)]
        for index, frame in enumerate(page.frames):
            if frame == page.main_frame:
                continue
            contexts.append((f"frame_{index}", frame))
        return contexts