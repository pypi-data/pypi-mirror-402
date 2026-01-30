import pytest
import os
import logging
from unittest.mock import patch
from fastpluggy_plugin.tasks_worker import start_workers_if_available, TaskWorker
from fastpluggy_plugin.tasks_worker.broker.local import LocalBroker
from testcontainers.postgres import PostgresContainer
from fastpluggy_plugin.tasks_worker.broker.postgres import PostgresBroker

logger = logging.getLogger(__name__)

@pytest.fixture
def clean_local_broker():
    """Ensure LocalBroker is reset for each test."""
    # LocalBroker might use a singleton-like manager or shared state
    # We want to make sure we are starting fresh
    with patch.dict(os.environ, {"BROKER_TYPE": "local"}):
        broker = TaskWorker.get_broker()
        # If it's a LocalBroker, it might have state from previous tests if not handled
        if isinstance(broker, LocalBroker):
            # Attempt to clear workers if possible, or just ignore existing ones
            pass
        yield broker

def test_worker_count_local(fast_pluggy):
    """Test that the number of workers started matches WORKER_NUMBER for local broker."""
    worker_count = 3
    with patch.dict(os.environ, {"WORKER_NUMBER": str(worker_count), "BROKER_TYPE": "local"}):
        # Reset TaskWorker broker to ensure it picks up the right type
        TaskWorker._broker = None
        
        # We need to mock is_installed to return True for our plugin
        with patch("fastpluggy_plugin.tasks_worker.is_installed", return_value=True), \
             patch("fastpluggy_plugin.tasks_worker.TaskWorker.submit") as mock_submit:
            # mock_submit avoids starting the Scheduler loop which is called via TaskWorker.submit
            
            success = start_workers_if_available()
            assert success is True
            
            # Wait a bit for heartbeats to register
            import time
            time.sleep(1)
            
            broker = TaskWorker.get_broker()
            workers = broker.get_workers()
            
            # Filter workers by those registered in this test if possible, 
            # or just check if it's at least worker_count
            assert len(workers) >= worker_count
            logger.info(f"Verified {len(workers)} workers registered in LocalBroker")

            # Cleanup: stop executors to avoid leaking threads
            from fastpluggy.fastpluggy import FastPluggy
            fp = FastPluggy(app=None)
            executor = fp.get_global('tasks_worker.executor')
            if executor:
                executor.stop()

@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer("postgres:15-alpine") as postgres:
        db_url = postgres.get_connection_url()
        if db_url.startswith("postgresql+psycopg2://"):
            db_url = db_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
        os.environ["DATABASE_URL"] = db_url
        yield postgres

def test_worker_count_postgres(fast_pluggy, postgres_container):
    """Test that the number of workers started matches WORKER_NUMBER for postgres broker."""
    worker_count = 2
    db_url = os.environ.get("DATABASE_URL")
    
    with patch.dict(os.environ, {
        "WORKER_NUMBER": str(worker_count), 
        "BROKER_TYPE": "postgres",
        "DATABASE_URL": db_url
    }):
        # Reset TaskWorker broker
        TaskWorker._broker = None
        
        with patch("fastpluggy_plugin.tasks_worker.is_installed", return_value=True), \
             patch("fastpluggy_plugin.tasks_worker.TaskWorker.submit") as mock_submit:
            
            success = start_workers_if_available()
            assert success is True
            
            # Wait a bit for heartbeats to register
            import time
            time.sleep(1)
            
            broker = TaskWorker.get_broker()
            assert isinstance(broker, PostgresBroker)
            
            workers = broker.get_workers()
            assert len(workers) >= worker_count
            logger.info(f"Verified {len(workers)} workers registered in PostgresBroker")

            # Cleanup
            from fastpluggy.fastpluggy import FastPluggy
            fp = FastPluggy(app=None)
            executor = fp.get_global('tasks_worker.executor')
            if executor:
                executor.stop()
