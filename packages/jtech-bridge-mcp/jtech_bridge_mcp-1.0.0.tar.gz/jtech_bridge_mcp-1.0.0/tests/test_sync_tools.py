import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.sync_tools import GetBackendStatusTool, ReadLatestContractTool


@pytest.fixture
def mock_state_cache():
    with patch("app.tools.sync_tools.get_state_cache") as mock:
        cache = MagicMock()
        mock.return_value = cache
        yield cache


@pytest.fixture
def mock_project_repository():
    with patch("app.tools.sync_tools.get_project_repository") as mock:
        repo = MagicMock()
        repo.get_by_name = AsyncMock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def tool():
    return GetBackendStatusTool()


@pytest.fixture
def read_tool():
    return ReadLatestContractTool()


@pytest.fixture
def mock_validator():
    # Since get_path_validator is imported inside the method
    with patch("app.services.path_validator.get_path_validator") as mock:
        validator = MagicMock()
        validator.validate_path = AsyncMock()
        mock.return_value = validator
        yield validator


@pytest.mark.asyncio
async def test_execute_no_filters(tool, mock_state_cache):
    # Setup mock data
    tasks = [
        {"id": "1", "description": "Task 1", "path": "/path/to/project1/doc.md"},
        {"id": "2", "description": "Task 2", "path": "/path/to/project2/doc.md"},
    ]
    mock_state_cache.get_pending_tasks.return_value = tasks

    # Execute
    result = await tool.execute({})

    # Verify
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["status"] == "online"
    assert data["task_count"] == 2
    assert len(data["tasks"]) == 2
    assert data["filter"]["status"] == "pending"


@pytest.mark.asyncio
async def test_execute_filter_by_project_found(tool, mock_state_cache, mock_project_repository):
    # Setup data
    tasks = [
        {"id": "1", "description": "Task 1", "path": "/home/user/projects/proj1/doc.md"},
        {"id": "2", "description": "Task 2", "path": "/home/user/projects/proj2/doc.md"},
    ]
    mock_state_cache.get_pending_tasks.return_value = tasks

    # Setup project
    project = MagicMock()
    project.path = "/home/user/projects/proj1"
    mock_project_repository.get_by_name.return_value = project

    # Execute
    result = await tool.execute({"project_name": "proj1"})

    # Verify
    data = json.loads(result[0].text)
    assert data["task_count"] == 1
    assert data["tasks"][0]["id"] == "1"

    mock_project_repository.get_by_name.assert_called_with("proj1")


@pytest.mark.asyncio
async def test_execute_filter_by_project_not_found(tool, mock_state_cache, mock_project_repository):
    mock_state_cache.get_pending_tasks.return_value = []
    mock_project_repository.get_by_name.return_value = None

    result = await tool.execute({"project_name": "unknown"})

    data = json.loads(result[0].text)
    assert "error" in data
    assert "not found" in data["error"]


@pytest.mark.asyncio
async def test_execute_invalid_status(tool):
    result = await tool.execute({"status": "completed"})

    data = json.loads(result[0].text)
    assert "error" in data
    assert "not supported" in data["error"]


# ReadLatestContractTool Tests


@pytest.mark.asyncio
async def test_read_contract_success(read_tool, mock_validator):
    path_str = "/abs/path/to/file.md"
    mock_path = MagicMock(spec=Path)
    mock_path.read_text.return_value = "# Title\n\nContent"
    mock_path.suffix = ".md"
    mock_path.name = "file.md"
    mock_validator.validate_path.return_value = mock_path

    result = await read_tool.execute({"path": path_str})

    assert result[0].text == "# Title\n\nContent"
    mock_validator.validate_path.assert_called_with(path_str)


@pytest.mark.asyncio
async def test_read_contract_extract_section(read_tool, mock_validator):
    path_str = "/abs/path/to/file.md"
    content = """# Header 1
Some content

## Section A
Desired content
More content

## Section B
Other content
"""
    mock_path = MagicMock(spec=Path)
    mock_path.read_text.return_value = content
    mock_path.suffix = ".md"
    mock_validator.validate_path.return_value = mock_path

    result = await read_tool.execute({"path": path_str, "section": "Section A"})

    expected = "Desired content\nMore content"
    assert result[0].text.strip() == expected.strip()


@pytest.mark.asyncio
async def test_read_contract_section_not_found(read_tool, mock_validator):
    path_str = "/abs/path/to/file.md"
    content = "# Header 1\nContent"
    mock_path = MagicMock(spec=Path)
    mock_path.read_text.return_value = content
    mock_path.suffix = ".md"
    mock_path.name = "file.md"
    mock_validator.validate_path.return_value = mock_path

    result = await read_tool.execute({"path": path_str, "section": "Missing"})

    assert "not found" in result[0].text


@pytest.mark.asyncio
async def test_read_contract_missing_path(read_tool):
    result = await read_tool.execute({})
    assert "required" in result[0].text


@pytest.mark.asyncio
async def test_read_contract_validation_error(read_tool, mock_validator):
    mock_validator.validate_path.side_effect = PermissionError("Access denied")

    result = await read_tool.execute({"path": "/bad/path"})
    assert "Access denied" in result[0].text
