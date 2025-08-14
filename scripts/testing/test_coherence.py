# tests/test_coherence.py
import pytest
from app.models.schemas import TaskResponse, ProgressInfo, AnalysisType
from app.models.database import ScrapingTask, init_db
from app.config.settings import settings

def test_progress_format_consistency():
    """Test que le format progress est cohérent partout"""
    # Test ProgressInfo
    progress = ProgressInfo()
    progress.update_from_values(3, 10)
    
    assert progress.current == 3
    assert progress.total == 10
    assert progress.percentage == 30.0
    assert progress.display == "3/10"

def test_task_response_creation():
    """Test création TaskResponse cohérente"""
    response = TaskResponse(
        task_id="test-123",
        status="pending",
        analysis_type=AnalysisType.STANDARD,
        progress=ProgressInfo(),
        created_at=datetime.utcnow(),
        urls=["https://test.com"],
        parameters={}
    )
    
    assert response.task_id == "test-123"
    assert response.has_error == False
    assert response.urls_count == 1

def test_database_task_conversion():
    """Test conversion ScrapingTask -> TaskResponse"""
    from app.models.database import create_sample_task
    
    db_task = create_sample_task("test-conversion")
    response = db_task.to_task_response()
    
    assert isinstance(response, TaskResponse)
    assert response.task_id == "test-conversion"
    assert response.progress.total == 2