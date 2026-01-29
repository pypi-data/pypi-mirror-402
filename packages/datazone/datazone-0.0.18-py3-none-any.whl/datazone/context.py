from typing import Optional

from contextvars import ContextVar

profile_context: ContextVar[Optional[str]] = ContextVar("profile_context", default=None)
