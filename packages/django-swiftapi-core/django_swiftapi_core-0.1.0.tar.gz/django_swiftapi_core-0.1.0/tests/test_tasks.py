"""
Tests for SwiftAPI Tasks (Background Processing).
"""
import pytest
from swiftapi.tasks import (
    TaskResult,
    AsyncTaskBackend,
    background_task,
    get_task_backend,
)


class TestTaskResult:
    """Test TaskResult class."""
    
    def test_task_result_creation(self):
        """Test creating a task result."""
        result = TaskResult(task_id="123", status="pending")
        assert result.task_id == "123"
        assert result.status == "pending"
        assert result.result is None
        assert result.error is None
    
    def test_task_result_completed(self):
        """Test completed task result."""
        result = TaskResult(task_id="456", status="completed", result={"data": "value"})
        assert result.status == "completed"
        assert result.result == {"data": "value"}
    
    def test_task_result_failed(self):
        """Test failed task result."""
        result = TaskResult(task_id="789", status="failed", error="Something went wrong")
        assert result.status == "failed"
        assert result.error == "Something went wrong"
    
    def test_task_result_to_dict(self):
        """Test task result to_dict method."""
        result = TaskResult(task_id="abc", status="running")
        data = result.to_dict()
        
        assert data["task_id"] == "abc"
        assert data["status"] == "running"


class TestAsyncTaskBackend:
    """Test AsyncTaskBackend."""
    
    def test_backend_initialization(self):
        """Test backend initialization."""
        backend = AsyncTaskBackend()
        assert backend._tasks == {}


class TestBackgroundTaskDecorator:
    """Test @background_task decorator."""
    
    def test_decorator_preserves_function(self):
        """Test decorator preserves function attributes."""
        @background_task
        def my_task():
            return "result"
        
        assert callable(my_task)
        assert hasattr(my_task, "delay")
    
    def test_decorator_delay_method(self):
        """Test decorator adds delay method."""
        @background_task
        def another_task(x, y):
            return x + y
        
        assert hasattr(another_task, "delay")
        assert callable(another_task.delay)


class TestGetTaskBackend:
    """Test get_task_backend function."""
    
    def test_get_default_backend(self):
        """Test getting default task backend."""
        backend = get_task_backend()
        assert isinstance(backend, AsyncTaskBackend)
