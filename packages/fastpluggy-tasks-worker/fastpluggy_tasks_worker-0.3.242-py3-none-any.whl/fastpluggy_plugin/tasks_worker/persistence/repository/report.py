import datetime
from typing import Optional, List, Dict, Any

from fastpluggy.core.database import session_scope
from fastpluggy.core.tools.serialize_tools import serialize_value
from fastpluggy.core.tools.threads_tools import get_tid, get_py_ident
from ..models.report import TaskReportDB
from ..schema.report import TaskReport
from ...core.status import TaskStatus


def init_report_from_context(context: "TaskContext", status: TaskStatus = TaskStatus.RUNNING) -> TaskReport:
    """
    Create and persist an initial TaskReport based on the context.
    """
    report = TaskReport(
        task_id=context.task_id,
        function=context.func_name,
        args=[str(a) for a in context.args],
        kwargs={k: str(v) for k, v in context.kwargs.items()},
        start_time=datetime.datetime.now(datetime.UTC),
        status=status,
        thread_native_id=get_tid(),
        thread_ident=get_py_ident(),
    )
    return report


# def save_report(report: TaskReport) -> None:
#     """
#     Persist the initial TaskReport before execution.
#     """
#     with session_scope() as db:
#         data = TaskReportDB(**report.to_dict())
#         db.add(data)
#         db.commit()


def update_report(report: TaskReport) -> None:
    """
    Update fields on an existing TaskReportDB and in-memory TaskReport.
    If it doesn't exist, create it.
    - Preserves original start_time if already set in DB.
    - Computes duration when both start_time and end_time are available.
    """

    with session_scope() as db:
        exists = db.query(TaskReportDB).filter(TaskReportDB.task_id == report.task_id).first()

        data = report.to_dict()
        if 'result' in data:
            data['result'] = str(serialize_value(data['result']))

        if not exists:
            exists = TaskReportDB(**data)
            db.add(exists)
        else:
            # Preserve earliest start_time if already recorded
            if getattr(exists, 'start_time', None):
                data.pop('start_time', None)

            # Apply updates except duration (we'll compute it afterward)
            for key, value in data.items():
                if hasattr(exists, key):
                    setattr(exists, key, value)

        # Compute duration if possible
        start_time = exists.start_time or data.get('start_time')
        end_time = exists.end_time or data.get('end_time')
        try:
            if start_time and end_time:
                exists.duration = (end_time.timestamp() - start_time.timestamp())
        except Exception:
            # leave duration as-is on error
            pass

        db.add(exists)
        db.commit()
        db.refresh(exists)
        return exists


def get_report(task_id: str) -> Optional[TaskReportDB]:
    """
    Get a TaskReportDB by task_id.
    """
    with session_scope() as db:
        return db.query(TaskReportDB).filter(TaskReportDB.task_id == task_id).first()


def wait_for_task(
    task_id: str,
    timeout: Optional[float] = None,
    poll_interval: float = 0.5
) -> Optional[Dict[str, Any]]:
    """
    Wait for a task to finish execution by polling the database.

    Args:
        task_id (str): The unique identifier of the task to wait for.
        timeout (Optional[float]): Maximum time to wait in seconds. If None, wait indefinitely.
        poll_interval (float): Time in seconds between database checks. Defaults to 0.5s.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the final task report data 
        (task_id, status, finished, result, error) if the task finishes within the timeout,
        or None if the timeout is reached.
    """
    import time
    start_time = time.time()

    finished_statuses = {
        TaskStatus.SUCCESS.value,
        TaskStatus.FAILED.value,
        TaskStatus.CANCELLED.value,
        TaskStatus.MANUAL_CANCELLED.value,
        TaskStatus.CANCEL_PURGED.value,
        TaskStatus.ERROR.value,
        TaskStatus.TIMEOUT.value,
        TaskStatus.DEAD.value
    }

    while True:
        with session_scope() as db:
            report_db = db.query(TaskReportDB).filter(TaskReportDB.task_id == task_id).first()
            if report_db:
                # Check if finished
                is_finished = report_db.finished or report_db.status in finished_statuses
                if is_finished:
                    # Return data as dict to avoid detached instance issues
                    # We can't easily call to_dict() if it's not defined on the DB model, 
                    # but we can manually pick fields or use a helper if available.
                    # TaskReportDB seems to have many fields.
                    return {
                        "task_id": report_db.task_id,
                        "status": report_db.status,
                        "finished": report_db.finished,
                        "result": report_db.result,
                        "error": report_db.error,
                    }

        if timeout is not None and (time.time() - start_time) > timeout:
            return None

        time.sleep(poll_interval)
