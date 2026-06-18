"""Pure presentation formatters (human-readable size / duration).

Kept out of widgets so they are unit-testable and reusable by the completion
panel and the (future) library screen.
"""

from __future__ import annotations


def human_size(num_bytes: int) -> str:
    """Format a byte count like ``4.2 MB``."""
    size = float(max(0, num_bytes))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"  # pragma: no cover - unreachable


def human_duration(seconds: float) -> str:
    """Format seconds like ``1:03:05`` or ``2:07`` (h:mm:ss / m:ss)."""
    total = int(round(max(0.0, seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
