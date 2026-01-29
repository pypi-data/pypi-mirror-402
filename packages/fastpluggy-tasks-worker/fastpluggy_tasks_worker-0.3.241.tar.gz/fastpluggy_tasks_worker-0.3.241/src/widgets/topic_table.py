from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

from fastpluggy.core.widgets import AbstractWidget

from ..broker.factory import get_broker


class TopicTableView(AbstractWidget):
    """
    Custom widget to render broker topics in a Tabler-styled table with a per-row Info modal.
    Mirrors the style and approach of WorkerTableView.
    """

    widget_type = "topic_table_view"
    template_name: str = "tasks_worker/widgets/topic_table.html.j2"

    DEFAULT_FIELDS = [
        "topic",
        "queued",
        "running",
        "dead_letter",
        "subscribers",
        "total_count",
        "completed_count",
        "error_count",
        "skipped_count",
        "details",
    ]

    DEFAULT_HEADERS: Dict[str, str] = {
        "topic": "Topic",
        "queued": "Queued",
        "running": "Running",
        "dead_letter": "Dead Letter",
        "subscribers": "Subscribers",
        "total_count": "Total",
        "completed_count": "Completed",
        "error_count": "Errors",
        "skipped_count": "Skipped",
        "details": "Info",
    }

    def __init__(
        self,
        *,
        title: str = "Topics",
        data: Optional[List[Dict[str, Any]]] = None,
        fields: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
        broker: Optional[Any] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.title = title
        self._input_data = data
        self.fields = fields or self.DEFAULT_FIELDS
        self.headers = dict(self.DEFAULT_HEADERS)
        if headers:
            self.headers.update(headers)
        self.broker = broker
        self.data: List[Dict[str, Any]] = []

    def _make_dialog_id(self, row: Dict[str, Any]) -> Optional[str]:
        try:
            base_id = str(row.get("topic") or "topic")
            safe_id = "".join(ch if (ch.isalnum() or ch in ("-", "_")) else "-" for ch in base_id)
            return f"tpdlg-{safe_id}"
        except Exception:
            return None

    def _enrich_rows(self, rows: List[Dict[str, Any]], request: Optional[Any] = None) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for r in rows:
            r = dict(r)
            dlg = self._make_dialog_id(r)
            if dlg:
                r["dialog_id"] = dlg

            if request and r.get("topic"):
                r["url_purge"] = str(request.url_for("broker_debug_purge_topic")
                                     .include_query_params(topic=r["topic"]))
                r["url_purge_dead"] = str(request.url_for("broker_debug_purge_topic")
                                          .include_query_params(topic=r["topic"], include_dead="true"))
                r["url_remove_limit"] = str(request.url_for("broker_debug_set_topic_limit")
                                            .include_query_params(topic=r["topic"]))
                r["url_update_limit"] = str(request.url_for("broker_debug_set_topic_limit"))
                r["url_active_tasks"] = str(request.url_for("broker_debug_get_all_active_tasks")
                                            .include_query_params(topic=r["topic"]))

            out.append(r)
        return out

    def process(self, **kwargs):
        # load data if not provided
        data: Optional[List[Dict[str, Any]]] = self._input_data
        request = kwargs.get("request")
        if data is None:
            try:
                b = self.broker or get_broker()
                items = b.get_topics() or []
                data = [asdict(i) if is_dataclass(i) else i for i in items]
            except Exception:
                data = []
        data = list(data or [])
        self.data = self._enrich_rows(data, request=request)
        self.use_fields = self.fields
        self.use_headers = self.headers
        self.table_id = kwargs.get("table_id") or "topics-table"
        self.card_class = kwargs.get("card_class") or "card"
        self.table_class = kwargs.get("table_class") or "table table-vcenter"
