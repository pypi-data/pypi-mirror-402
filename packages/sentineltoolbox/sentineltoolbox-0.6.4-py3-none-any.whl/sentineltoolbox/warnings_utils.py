import warnings
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

InstalledSnapshotType = Sequence[Any]


class WarningsSuppressor:
    """
    Suppress a configurable set of warnings.

    Usages:
    - As a context manager:
        with WarningsSuppressor():
            ...
    - As a decorator:
        @WarningsSuppressor()
        def f(...): ...
    - Globally:
        import warnings
        from typing import Any, Mapping, Iterable, Optional, Callable, Type

    """

    DEFAULT_FILTERS = (
        {"action": "ignore", "message": "All-NaN slice encountered"},
        {"action": "ignore", "message": "invalid value encountered in divide"},
        {"action": "ignore", "message": "Mean of empty slice"},
        {"action": "ignore", "message": "divide by zero encountered in divide"},
        {"action": "ignore", "message": "divide by zero encountered in scalar divide"},
    )

    def __init__(self, filters: Optional[Iterable[Mapping[str, Any]]] = None) -> None:
        self._filters = list(filters) if filters is not None else list(self.DEFAULT_FILTERS)
        self._installed_snapshot: InstalledSnapshotType | None = None

    # Context manager support
    def __enter__(self) -> None:
        # Use catch_warnings to be temporary and thread-local to the warnings module state
        self._cm = warnings.catch_warnings()
        self._cm.__enter__()
        # Apply each filter in the temporary context
        for f in self._filters:
            warnings.filterwarnings(**f)
        return None

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        # Exit the catch_warnings context -> restores previous filters in that context
        self._cm.__exit__(exc_type, exc, tb)

    # Decorator support
    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        # Return a wrapper that uses the context manager
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self:
                return func(*args, **kwargs)

        # Preserve metadata
        from functools import wraps

        return wraps(func)(wrapper)

    # Global install/uninstall (affects the global warnings.filters list)
    def activate(self) -> None:
        """Install these filters globally and keep a snapshot of previous filters for restore."""
        if self._installed_snapshot is not None:
            # Already installed
            return
        current = [tuple(f) for f in warnings.filters]
        self._installed_snapshot = current
        # Apply filters globally
        for f in self._filters:
            warnings.filterwarnings(**f)

    def deactivate(self) -> None:
        """Restore the snapshot made at install() time. If there was no snapshot, do nothing."""
        if self._installed_snapshot is None:
            return
        # Restore the snapshot (replace the warnings.filters list)
        warnings.filters = list(self._installed_snapshot)
        self._installed_snapshot = None
