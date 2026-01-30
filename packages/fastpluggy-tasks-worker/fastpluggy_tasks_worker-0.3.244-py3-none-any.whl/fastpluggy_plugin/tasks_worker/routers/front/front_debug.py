import logging
from dataclasses import asdict, is_dataclass

from fastapi import APIRouter, Depends, Request

from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.widgets.categories.data.debug import DebugView
from ...widgets.topic_table import TopicTableView
from fastpluggy.core.widgets.categories.input.button import AutoLinkWidget
from fastpluggy.core.widgets.categories.input.button_list import ButtonListWidget
from ...widgets.worker_table import WorkerTableView
from ...broker.factory import get_broker

front_task_debug_router = APIRouter(tags=["task_debug"])


@front_task_debug_router.get("/debug", name="broker_debug_dashboard")
def broker_debug_dashboard(request: Request, view_builder=Depends(get_view_builder)):
    """
    Show broker-related runtime information on the Task Runner dashboard.
    Displays cluster stats, topics and workers as reported by the broker.
    """
    broker = None
    cluster_stats = {}
    topics = []
    workers = []
    errors = []

    try:
        broker = get_broker()
        # Overall cluster stats
        stats = broker.stats()
        logging.info(f"stats : {stats}")

        try:
            cs = broker.get_cluster_stats() or {}
            # convert structured dataclass to dict if needed
            cluster_stats = asdict(cs) if is_dataclass(cs) else cs
            logging.info(f"cluster_stats : {cluster_stats}")
        except Exception as e:
            errors.append(f"get_cluster_stats failed: {e}")

        # Per-topic summary
        try:
            tps = broker.get_topics() or []
            topics = [asdict(t) if is_dataclass(t) else t for t in tps]
            logging.info(f"topic : {topics}")
        except Exception as e:
            errors.append(f"get_topics failed: {e}")



    except Exception as e:
        errors.append(f"Unable to initialize broker: {e}")

    # Normalize columns for tables
    topic_columns = {
        "topic": "Topic",
        "queued": "Queued",
        "running": "Running",
        "dead_letter": "Dead Letter",
        "subscribers": "Subscribers",
        "total_count": "Total",
        "completed_count": "Completed",
        "error_count": "Errors",
        "skipped_count": "Skipped",
    }

    widgets = [
        ButtonListWidget(buttons=[
            AutoLinkWidget(label="Back to Task Dashboard", route_name="dashboard_tasks_worker"),
            AutoLinkWidget(label="Stats", route_name="broker_debug_stats"),
            AutoLinkWidget(label="Get All Active Tasks", route_name="broker_debug_get_all_active_tasks"),
            AutoLinkWidget(label="Get Workers", route_name="broker_debug_get_workers"),
            AutoLinkWidget(label="Get Topics", route_name="broker_debug_get_topics"),
            AutoLinkWidget(label="Get Cluster Stats", route_name="broker_debug_get_cluster_stats"),
            AutoLinkWidget(label="Get Locks", route_name="broker_debug_get_locks"),
        ]),
        TopicTableView(title="Topics", data=topics, request=request),
        WorkerTableView(title="Workers", broker=broker),
        DebugView(title="Cluster Stats", data=cluster_stats, collapsed=True),
    ]

    if errors:
        widgets.append(DebugView(title="Errors", data=errors, collapsed=True))

    return view_builder.generate(
        request,
        title="Broker Info",
        widgets=widgets,
    )


@front_task_debug_router.get("/debug/action/stats", name="broker_debug_stats")
def broker_debug_stats(request: Request, view_builder=Depends(get_view_builder)):
    broker = get_broker()
    data = broker.stats() or {}
    return view_builder.generate(
        request,
        title="Broker Stats",
        widgets=[
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Back", route_name="broker_debug_dashboard"),
            ]),
            DebugView(title="stats", data=data, collapsed=False),
        ],
    )


@front_task_debug_router.get("/debug/action/get_all_active_tasks", name="broker_debug_get_all_active_tasks")
def broker_debug_get_all_active_tasks(request: Request, view_builder=Depends(get_view_builder), topic: str | None = None):
    broker = get_broker()
    try:
        items = broker.get_all_active_tasks(topic)
    except TypeError:
        # some brokers may require a param-less call
        items = broker.get_all_active_tasks(None)
    # normalize dataclasses to dict
    data = [asdict(i) if is_dataclass(i) else i for i in items or []]
    return view_builder.generate(
        request,
        title="Broker Active Tasks",
        widgets=[
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Back", route_name="broker_debug_dashboard"),
            ]),
            DebugView(title=f"Active Tasks (topic={topic})", data=data, collapsed=False),
            DebugView(title="Tip", data={"usage": "Append ?topic=your_topic to filter"}, collapsed=True),
        ],
    )


@front_task_debug_router.get("/debug/action/get_workers", name="broker_debug_get_workers")
def broker_debug_get_workers(request: Request, view_builder=Depends(get_view_builder), include_tasks: bool = False):


    return view_builder.generate(
        request,
        title="Broker Workers",
        widgets=[
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Back", route_name="broker_debug_dashboard"),
                AutoLinkWidget(label="Show with tasks", route_name="broker_debug_get_workers", param_inputs={"include_tasks": True}),
            ]),
            WorkerTableView(title="Workers", include_tasks=include_tasks),
        ],
    )


@front_task_debug_router.get("/debug/action/get_topics", name="broker_debug_get_topics")
def broker_debug_get_topics(request: Request, view_builder=Depends(get_view_builder)):
    broker = get_broker()
    items = broker.get_topics() or []
    data = [asdict(i) if is_dataclass(i) else i for i in items]
    return view_builder.generate(
        request,
        title="Broker Topics",
        widgets=[
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Back", route_name="broker_debug_dashboard"),
            ]),
            TopicTableView(title="Topics", data=data, request=request),
        ],
    )


@front_task_debug_router.get("/debug/action/get_cluster_stats", name="broker_debug_get_cluster_stats")
def broker_debug_get_cluster_stats(request: Request, view_builder=Depends(get_view_builder)):
    broker = get_broker()
    cs = broker.get_cluster_stats() or {}
    data = asdict(cs) if is_dataclass(cs) else cs
    return view_builder.generate(
        request,
        title="Broker Cluster Stats",
        widgets=[
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Back", route_name="broker_debug_dashboard"),
            ]),
            DebugView(title="Cluster Stats", data=data, collapsed=False),
        ],
    )


@front_task_debug_router.get("/debug/action/set_topic_limit", name="broker_debug_set_topic_limit")
def broker_debug_set_topic_limit(request: Request, view_builder=Depends(get_view_builder), topic: str | None = None, limit: str | None = None):
    broker = get_broker()
    success = False
    error = None
    parsed_limit = None
    if not topic:
        error = "Missing topic. Provide ?topic=...&limit=... (empty or omitted limit to remove)"
    else:
        try:
            if limit is None or limit == "":
                parsed_limit = None
            else:
                li = int(limit)
                if li < 0:
                    raise ValueError("limit must be >= 0 or empty for unlimited")
                parsed_limit = li
            broker.set_topic_concurrency_limit(topic, parsed_limit)
            success = True
        except Exception as e:
            error = str(e)
    # reload topics to display updated state
    try:
        items = broker.get_topics() or []
        data = [asdict(i) if is_dataclass(i) else i for i in items]
    except Exception:
        data = []
    return view_builder.generate(
        request,
        title="Set Topic Concurrency Limit",
        widgets=[
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Back", route_name="broker_debug_dashboard"),
                AutoLinkWidget(label="Back to Topics", route_name="broker_debug_get_topics"),
            ]),
            DebugView(title="Result", data={"topic": topic, "limit": parsed_limit, "success": success, "error": error}, collapsed=False),
            TopicTableView(title="Topics", data=data, request=request),
        ],
    )


@front_task_debug_router.get("/debug/action/get_locks", name="broker_debug_get_locks")
def broker_debug_get_locks(request: Request, view_builder=Depends(get_view_builder)):
    broker = get_broker()
    locks = broker.get_locks() or []
    return view_builder.generate(
        request,
        title="Broker Locks",
        widgets=[
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Back", route_name="broker_debug_dashboard"),
            ]),
            DebugView(title="Locks", data=locks, collapsed=False),
            DebugView(title="Tip", data={"force_release_lock": "Use the button below and pass task_id as query param"}, collapsed=True),
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Force release lock (provide task_id)", route_name="broker_debug_force_release_lock"),
            ]),
        ],
    )


@front_task_debug_router.get("/debug/action/force_release_lock", name="broker_debug_force_release_lock")
def broker_debug_force_release_lock(request: Request, view_builder=Depends(get_view_builder), task_id: str | None = None):
    broker = get_broker()
    success = False
    error = None
    if not task_id:
        error = "Missing task_id. Provide ?task_id=..."
    else:
        try:
            success = bool(broker.force_release_lock(task_id))
        except Exception as e:
            error = str(e)
    return view_builder.generate(
        request,
        title="Force Release Lock",
        widgets=[
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Back", route_name="broker_debug_dashboard"),
                AutoLinkWidget(label="Back to Locks", route_name="broker_debug_get_locks"),
            ]),
            DebugView(title="Result", data={"task_id": task_id, "success": success, "error": error}, collapsed=False),
        ],
    )


@front_task_debug_router.get("/debug/action/purge_topic", name="broker_debug_purge_topic")
def broker_debug_purge_topic(request: Request, view_builder=Depends(get_view_builder), topic: str | None = None, include_dead: str | None = None):
    broker = get_broker()
    result = None
    error = None
    include_dead_bool = False
    if include_dead is not None:
        include_dead_bool = str(include_dead).lower() in ("1", "true", "yes", "y", "on")
    if not topic:
        error = "Missing topic. Provide ?topic=...&include_dead=true to also clear dead-letter"
    else:
        try:
            result = broker.purge_topic(topic, include_dead_bool)
        except Exception as e:
            error = str(e)
    # reload topics
    try:
        items = broker.get_topics() or []
        data = [asdict(i) if is_dataclass(i) else i for i in items]
    except Exception:
        data = []
    return view_builder.generate(
        request,
        title="Purge Topic",
        widgets=[
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Back", route_name="broker_debug_dashboard"),
                AutoLinkWidget(label="Back to Topics", route_name="broker_debug_get_topics"),
            ]),
            DebugView(title="Result", data={"topic": topic, "include_dead": include_dead_bool, "result": result, "error": error}, collapsed=False),
            TopicTableView(title="Topics", data=data, request=request),
        ],
    )
