
import pytest
import uuid
from datetime import datetime, UTC
from fastpluggy_plugin.tasks_worker.core.context import TaskContext
from fastpluggy_plugin.tasks_worker.core.events import TaskLifecycleEvent
from fastpluggy_plugin.tasks_worker.core.status import TaskStatus
from fastpluggy_plugin.tasks_worker.subscribers.db_adapter import DBPersistence
from fastpluggy_plugin.tasks_worker.persistence.models.report import TaskReportDB
from fastpluggy_plugin.tasks_worker.persistence.models.context import TaskContextDB
from fastpluggy.core.database import session_scope

@pytest.fixture
def db_persistence():
    return DBPersistence()

def test_on_skipped_creates_report_if_missing(fast_pluggy, db_persistence):
    task_id = str(uuid.uuid4())
    ctx = TaskContext(
        task_id=task_id,
        task_name="test_task_skipped",
        func_name="test_func_skipped",
    )
    
    event = TaskLifecycleEvent(
        status=TaskStatus.SKIPPED,
        task_id=task_id,
        context=ctx,
        meta={"worker_id": "test_worker"}
    )
    
    # Ensure no report exists
    with session_scope() as db:
        db.query(TaskReportDB).filter_by(task_id=task_id).delete()
        db.query(TaskContextDB).filter_by(task_id=task_id).delete()
        db.commit()

    # Trigger on_skipped
    db_persistence.on_skipped(event)
    
    # Verify report was created
    with session_scope() as db:
        report = db.query(TaskReportDB).filter_by(task_id=task_id).first()
        assert report is not None, "Report should be created even if on_created was not called"
        assert report.status == TaskStatus.SKIPPED.value
        assert "concurrency lock" in report.logs

def test_on_created_creates_report(fast_pluggy, db_persistence):
    task_id = str(uuid.uuid4())
    ctx = TaskContext(
        task_id=task_id,
        task_name="test_task_created",
        func_name="test_func_created",
    )
    
    event = TaskLifecycleEvent(
        status=TaskStatus.CREATED,
        task_id=task_id,
        context=ctx,
        meta={"worker_id": "test_worker"}
    )
    
    # Ensure no report exists
    with session_scope() as db:
        db.query(TaskReportDB).filter_by(task_id=task_id).delete()
        db.commit()

    # Trigger on_created
    db_persistence.on_created(event)
    
    # Verify report was created
    with session_scope() as db:
        report = db.query(TaskReportDB).filter_by(task_id=task_id).first()
        assert report is not None
        assert report.status == TaskStatus.CREATED.value

def test_on_queued_updates_report(fast_pluggy, db_persistence):
    task_id = str(uuid.uuid4())
    ctx = TaskContext(
        task_id=task_id,
        task_name="test_task_queued",
        func_name="test_func_queued",
    )
    
    event = TaskLifecycleEvent(
        status=TaskStatus.QUEUED,
        task_id=task_id,
        context=ctx,
        meta={"worker_id": "test_worker"}
    )
    
    # Ensure no report exists
    with session_scope() as db:
        db.query(TaskReportDB).filter_by(task_id=task_id).delete()
        db.commit()

    # Trigger on_queued
    db_persistence.on_queued(event)
    
    # Verify report was updated to QUEUED
    with session_scope() as db:
        report = db.query(TaskReportDB).filter_by(task_id=task_id).first()
        assert report is not None
        assert report.status == TaskStatus.QUEUED.value
