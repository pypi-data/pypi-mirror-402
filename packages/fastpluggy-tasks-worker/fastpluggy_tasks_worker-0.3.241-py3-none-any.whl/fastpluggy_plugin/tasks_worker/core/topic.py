from typing import Any, Mapping, Optional, Callable


def resolve_topic(func: Any, topic: Optional[str] = None, *, settings=None) -> str:
    """Return an explicit topic if provided, else try func._task_metadata['topic'],
    else fall back to TasksRunnerSettings().default_topic.

    - Skips metadata lookup if func is a str.
    - Handles missing/invalid _task_metadata gracefully.
    - Allows injecting a settings instance to avoid repeated imports/instantiation.
    """
    # 1) If the caller already gave us a non-empty topic, keep it.
    if topic:
        return topic

    # 2) Try to get topic from the callable's metadata.
    meta_topic = None
    if not isinstance(func, str):
        meta = getattr(func, "_task_metadata", None)
        if isinstance(meta, Mapping):
            meta_topic = meta.get("topic")
        # Optional: also support a direct attribute as a soft fallback
        if not meta_topic:
            meta_topic = getattr(func, "topic", None)

    if meta_topic:
        return meta_topic

    # 3) Fall back to settings default (injectable to avoid per-call import).
    if settings is None:
        from ..config import TasksRunnerSettings
        settings = TasksRunnerSettings()

    return settings.default_topic


def load_lock_key_resolver(import_path: Optional[str]) -> Optional[Callable[..., Optional[str]]]:
    """Loader for a resolver that extracts a lock key from task submission.
    Should accept kwargs: func, args, kwargs, task_name, topic, settings.
    Returns a string key or None.
    """
    if not import_path:
        return None
    try:
        if ':' in import_path:
            module_name, attr_name = import_path.split(':', 1)
        else:
            parts = import_path.rsplit('.', 1)
            if len(parts) != 2:
                return None
            module_name, attr_name = parts
        import importlib
        mod = importlib.import_module(module_name)
        fn = getattr(mod, attr_name)
        return fn if callable(fn) else None
    except Exception:
        return None
