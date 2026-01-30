from __future__ import annotations

from mcp.server import Server


async def send_progress(app: Server, message: str, progress: float, total: float = 3.0) -> None:
    """Send a progress notification if a progress token is available."""
    try:
        ctx = app.request_context
        if ctx.meta and ctx.meta.progressToken:
            await ctx.session.send_progress_notification(
                ctx.meta.progressToken,
                progress,
                total=total,
                message=message,
            )
    except (LookupError, AttributeError):
        # No request context or progress token available
        pass
