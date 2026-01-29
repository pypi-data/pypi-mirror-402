from typing import Optional, List

from fastpluggy.core.config import BaseDatabaseSettings


class TasksRunnerSettings(BaseDatabaseSettings):
    """
    Settings for the tasks_worker plugin (cleaned, current behavior).

    Topic routing
    - By default, tasks publish to settings.worker_id if set, else to settings.default_topic.
    - If settings.force_task_topic is truthy, the hostname is used for both topic and worker_id
      to route all submissions to the local worker (useful for debugging).
    - Removed: topic_resolver, concurrency_policy_resolver, virtual_topic_base (0.3.231).

    Per-entity concurrency (keyed locks)
    - lock_key_resolver (str | None): dotted path to a callable that extracts a lock key from
      the task invocation (receives func, args, kwargs, task_name, topic, settings). If it
      returns a non-empty string, the worker acquires a broker lock named
      f"{lock_namespace}{key}" to serialize tasks sharing that key.
    - lock_namespace (str): prefix for lock names. Default "v:lock:".

    Notes on legacy/unused settings
    - external_notification_loaders: kept for legacy compatibility; not used by current notifier flow.
    - watchdog_enabled / watchdog_timeout_minutes: watchdog task is not scheduled by default.

    This docstring intentionally focuses on effective, supported options for clarity.
    """

    BROKER_TYPE : str = 'local'  # Used by broker.factory.get_broker()
    BROKER_DSN: Optional[str] = None  # Optional DSN: for rabbitmq (amqp URL) or postgres (database URL) when BROKER_TYPE matches

    # Broker specific options
    # Worker heartbeat TTL for Postgres broker (in seconds). Determines when a worker is considered stale.
    postgres_worker_ttl_seconds: int = 24 * 3600

    # Topics
    worker_id: Optional[str] = None  # If set, TaskWorker.submit will default topic to this value
    default_topic: str = "default"  # Fallback topic for submissions and runner wiring
    force_task_topic: Optional[str] = None  # If set, overrides topic on submission (uses hostname)

    # Per-entity locking
    lock_key_resolver: Optional[str] = None  # Dotted path to a callable used to extract lock key from args/kwargs
    lock_namespace: str = "v:lock:"  # Prefix added to the lock key to form the broker lock name

    # Executor settings
    #thread_pool_max_workers: Optional[int] = None  # None means use default (CPU count * 5). Not wired currently.

    # Scheduler
    scheduler_enabled: bool = True  # Controls enabling of scheduler routes and background loop
    scheduler_frequency: float = 5  # Used by tasks/scheduler main loop sleep
    allow_create_schedule_task: bool = True  # Controls UI ability to create scheduled tasks
    allow_delete_schedule_task: bool = True  # Controls UI/route ability to delete scheduled tasks

    # notifier
    external_notification_loaders: Optional[List[str]] = []  # UNUSED in current implementation (legacy placeholder)

    # Registry/Discover of tasks
    enable_auto_task_discovery: bool = True  # Enables scanning for task functions in loaded modules

    # Celery
    discover_celery_tasks: bool = False  # Enables Celery task discovery integration
    celery_app_path: Optional[str] = None   # Path to the Celery app object for discovery for example "myproject.worker:celery_app"
    discover_celery_schedule_enabled_status: bool = False # Default enabled status when importing Celery beat schedule


    store_task_db: bool = True  # Controls DB persistence of task contexts/reports
    #store_task_notif_db: bool = False  # Not used currently

    # Purge in case the task is stored in DB
    purge_enabled :bool = True  # Enables purge job creation (if/when scheduled)
    purge_after_days: int = 30  # Retention period for purge job

    # Metrics
    metrics_enabled: bool = True

    watchdog_enabled: bool = True  # UNUSED: watchdog task scheduling is commented out
    #watchdog_frequency: float = 5  # Not wired currently
    watchdog_timeout_minutes: int = 120  # UNUSED at runtime unless watchdog task is scheduled


# maybe add a module prefix
#    class Config:
#        env_prefix = "tasks_worker_"