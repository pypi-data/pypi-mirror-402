import os
import unittest
from unittest.mock import patch, MagicMock
from fastpluggy_plugin.tasks_worker import start_workers_if_available

class TestWorkerStartup(unittest.TestCase):
    @patch('fastpluggy_plugin.tasks_worker.is_installed')
    @patch('fastpluggy_plugin.tasks_worker.TaskWorker.setup_broker')
    @patch('fastpluggy_plugin.tasks_worker.TaskWorker.init_worker')
    def test_start_workers_if_available(self, mock_init, mock_setup, mock_is_installed):
        # Setup mocks
        mock_is_installed.return_value = True
        
        # Test with default 1 worker
        with patch.dict(os.environ, {"WORKER_NUMBER": "1"}):
            result = start_workers_if_available()
            self.assertTrue(result)
            mock_setup.assert_called_once()
            self.assertEqual(mock_init.call_count, 1)
        
        mock_init.reset_mock()
        mock_setup.reset_mock()
        
        # Test with 3 workers
        with patch.dict(os.environ, {"WORKER_NUMBER": "3"}):
            result = start_workers_if_available()
            self.assertTrue(result)
            mock_setup.assert_called_once()
            self.assertEqual(mock_init.call_count, 3)

    @patch('fastpluggy_plugin.tasks_worker.is_installed')
    def test_start_workers_not_installed(self, mock_is_installed):
        mock_is_installed.return_value = False
        result = start_workers_if_available()
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
