"""Chat model wrappers for Crynux."""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI


class ChatCrynux(ChatOpenAI):
    """ChatOpenAI with a Crynux-specific VRAM requirement."""

    vram_limit: int

    def __init__(self, *args: Any, vram_limit: int = 24, **kwargs: Any) -> None:
        if vram_limit <= 0:
            raise ValueError("vram_limit must be a positive integer (GB).")

        kwargs.setdefault("base_url", "https://bridge.crynux-as.xyz/v1/llm")

        extra_body = kwargs.pop("extra_body", None)
        if extra_body is None:
            extra_body = {}
        if not isinstance(extra_body, dict):
            raise TypeError("extra_body must be a dict when provided.")

        extra_body = {**extra_body, "vram_limit": vram_limit}
        kwargs["extra_body"] = extra_body

        super().__init__(*args, **kwargs)
        self.vram_limit = vram_limit
