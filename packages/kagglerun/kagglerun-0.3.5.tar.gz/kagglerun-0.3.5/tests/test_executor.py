"""
Unit tests for KaggleRun executor.

These tests use mocking to avoid requiring actual Kaggle API access.
Run with: pytest tests/ -v
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kagglerun.executor import KaggleExecutor, connect


class TestKaggleExecutor:
    """Tests for KaggleExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create executor with mock URL."""
        return KaggleExecutor("https://fake-kaggle-url.com/proxy", verbose=False)

    def test_init(self, executor):
        """Test executor initialization."""
        assert executor.base_url == "https://fake-kaggle-url.com/proxy"
        assert executor.kernel_id is None
        assert executor.verbose is False
        assert executor.default_timeout == 120

    def test_init_with_options(self):
        """Test executor initialization with custom options."""
        callback = Mock()
        executor = KaggleExecutor(
            "https://test.com/proxy",
            verbose=True,
            timeout=60,
            on_output=callback
        )
        assert executor.verbose is True
        assert executor.default_timeout == 60
        assert executor.on_output == callback

    @patch('kagglerun.executor.requests.Session')
    def test_test_connection_success(self, mock_session_class, executor):
        """Test successful connection test."""
        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        executor._session = mock_session

        assert executor.test_connection() is True
        mock_session.get.assert_called_once()

    @patch('kagglerun.executor.requests.Session')
    def test_test_connection_failure(self, mock_session_class, executor):
        """Test failed connection test."""
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Connection refused")
        executor._session = mock_session

        assert executor.test_connection() is False

    @patch('kagglerun.executor.requests.Session')
    def test_get_kernel_state_idle(self, mock_session_class, executor):
        """Test getting kernel state when idle."""
        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"execution_state": "idle"}
        mock_session.get.return_value = mock_response
        executor._session = mock_session
        executor.kernel_id = "test-kernel-id"

        state = executor.get_kernel_state()
        assert state == "idle"

    @patch('kagglerun.executor.requests.Session')
    def test_get_kernel_state_busy(self, mock_session_class, executor):
        """Test getting kernel state when busy."""
        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"execution_state": "busy"}
        mock_session.get.return_value = mock_response
        executor._session = mock_session
        executor.kernel_id = "test-kernel-id"

        state = executor.get_kernel_state()
        assert state == "busy"

    def test_get_kernel_state_no_kernel(self, executor):
        """Test getting kernel state with no kernel."""
        assert executor.get_kernel_state() == "unknown"

    @patch('kagglerun.executor.requests.Session')
    def test_get_or_create_kernel_existing(self, mock_session_class, executor):
        """Test using existing kernel."""
        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "existing-kernel-123"}]
        mock_session.get.return_value = mock_response
        executor._session = mock_session

        kernel_id = executor.get_or_create_kernel()
        assert kernel_id == "existing-kernel-123"
        assert executor.kernel_id == "existing-kernel-123"

    @patch('kagglerun.executor.requests.Session')
    def test_get_or_create_kernel_new(self, mock_session_class, executor):
        """Test creating new kernel."""
        mock_session = MagicMock()

        # First call returns empty list (no existing kernels)
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []

        # Second call creates new kernel
        mock_post_response = Mock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = {"id": "new-kernel-456"}

        mock_session.get.return_value = mock_get_response
        mock_session.post.return_value = mock_post_response
        executor._session = mock_session

        kernel_id = executor.get_or_create_kernel()
        assert kernel_id == "new-kernel-456"

    @patch('kagglerun.executor.requests.Session')
    def test_interrupt_kernel(self, mock_session_class, executor):
        """Test kernel interrupt."""
        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 204
        mock_session.post.return_value = mock_response
        executor._session = mock_session
        executor.kernel_id = "test-kernel"

        assert executor.interrupt_kernel() is True

    def test_interrupt_kernel_no_kernel(self, executor):
        """Test interrupt with no kernel."""
        assert executor.interrupt_kernel() is False

    @patch('kagglerun.executor.websocket.create_connection')
    @patch('kagglerun.executor.requests.Session')
    def test_execute_success(self, mock_session_class, mock_ws_create):
        """Test successful code execution."""
        executor = KaggleExecutor("https://test.com/proxy", verbose=False)

        # Mock session for kernel operations
        mock_session = MagicMock()

        # Mock kernel list
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = [{"id": "kernel-123"}]
        mock_session.get.return_value = mock_get_response

        executor._session = mock_session
        executor.kernel_id = "kernel-123"

        # Mock WebSocket
        mock_ws = MagicMock()
        mock_ws_create.return_value = mock_ws

        # Simulate WebSocket messages
        messages = [
            {"msg_type": "status", "parent_header": {"msg_id": "test"}, "content": {"execution_state": "busy"}},
            {"msg_type": "stream", "parent_header": {"msg_id": "test"}, "content": {"text": "Hello World\n"}},
            {"msg_type": "status", "parent_header": {"msg_id": "test"}, "content": {"execution_state": "idle"}},
        ]
        mock_ws.recv.side_effect = [json.dumps(m) for m in messages]

        # Skip the actual message ID matching by patching uuid
        with patch('kagglerun.executor.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value="test")

            result = executor.execute("print('Hello World')", wait_idle=False)

        assert result["success"] is True
        assert "Hello World" in result["output_text"]

    def test_run_file_not_found(self, executor):
        """Test running non-existent file."""
        result = executor.run_file("/nonexistent/file.py")
        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_run_file_success(self, executor, tmp_path):
        """Test running a local file."""
        # Create temp file
        test_file = tmp_path / "test_script.py"
        test_file.write_text("print('test')")

        # Mock execute
        with patch.object(executor, 'execute') as mock_execute:
            mock_execute.return_value = {"success": True, "outputs": ["test"], "output_text": "test", "errors": []}
            result = executor.run_file(str(test_file))

        assert mock_execute.called
        mock_execute.assert_called_once()

    def test_save_text(self, executor):
        """Test saving text to remote."""
        with patch.object(executor, 'execute') as mock_execute:
            mock_execute.return_value = {"success": True, "outputs": ["Saved"], "output_text": "Saved", "errors": []}
            result = executor.save_text("test.txt", "Hello World")

        assert mock_execute.called
        # Check that the code contains base64 encoding
        call_args = mock_execute.call_args[0][0]
        assert "base64" in call_args
        assert "/kaggle/working/test.txt" in call_args

    def test_read_file_relative_path(self, executor):
        """Test reading file with relative path."""
        with patch.object(executor, 'execute') as mock_execute:
            mock_execute.return_value = {"success": True, "outputs": ["content"], "output_text": "content", "errors": []}
            result = executor.read_file("myfile.txt")

        call_args = mock_execute.call_args[0][0]
        assert "/kaggle/working/myfile.txt" in call_args

    def test_read_file_absolute_path(self, executor):
        """Test reading file with absolute path."""
        with patch.object(executor, 'execute') as mock_execute:
            mock_execute.return_value = {"success": True, "outputs": ["content"], "output_text": "content", "errors": []}
            result = executor.read_file("/custom/path/file.txt")

        call_args = mock_execute.call_args[0][0]
        assert "/custom/path/file.txt" in call_args

    def test_list_files(self, executor):
        """Test listing files."""
        with patch.object(executor, 'execute') as mock_execute:
            mock_execute.return_value = {"success": True, "outputs": ["files"], "output_text": "files", "errors": []}
            result = executor.list_files()

        assert mock_execute.called
        call_args = mock_execute.call_args[0][0]
        assert "/kaggle/working/" in call_args

    def test_get_gpu_info(self, executor):
        """Test getting GPU info."""
        with patch.object(executor, 'execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "outputs": ["GPU: NVIDIA Tesla T4, 16GB"],
                "output_text": "GPU: NVIDIA Tesla T4, 16GB",
                "errors": []
            }
            result = executor.get_gpu_info()

        assert mock_execute.called
        call_args = mock_execute.call_args[0][0]
        assert "nvidia-smi" in call_args

    def test_download_file_success(self, executor):
        """Test downloading file."""
        import base64
        test_content = b"test binary content"
        b64_content = base64.b64encode(test_content).decode()

        with patch.object(executor, 'execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "outputs": [b64_content],
                "output_text": b64_content,
                "errors": []
            }
            result = executor.download_file("test.bin")

        assert result == test_content

    def test_download_file_failure(self, executor):
        """Test downloading file failure."""
        with patch.object(executor, 'execute') as mock_execute:
            mock_execute.return_value = {
                "success": False,
                "outputs": [],
                "output_text": "",
                "errors": ["File not found"]
            }
            result = executor.download_file("nonexistent.bin")

        assert result is None


class TestConnect:
    """Tests for connect() convenience function."""

    @patch('kagglerun.executor.KaggleExecutor')
    def test_connect_success(self, mock_executor_class):
        """Test successful connection."""
        mock_executor = Mock()
        mock_executor.test_connection.return_value = True
        mock_executor_class.return_value = mock_executor

        result = connect("https://test.com/proxy")

        assert result == mock_executor
        mock_executor.test_connection.assert_called_once()

    @patch('kagglerun.executor.KaggleExecutor')
    def test_connect_failure(self, mock_executor_class):
        """Test connection failure raises error."""
        mock_executor = Mock()
        mock_executor.test_connection.return_value = False
        mock_executor_class.return_value = mock_executor

        with pytest.raises(ConnectionError):
            connect("https://test.com/proxy")


class TestCLI:
    """Tests for CLI module."""

    def test_cli_import(self):
        """Test CLI module can be imported."""
        from kagglerun.cli import main
        assert callable(main)

    def test_cli_no_url(self):
        """Test CLI with no URL returns error."""
        from kagglerun.cli import main

        # Clear env var if set
        old_env = os.environ.pop('KAGGLE_JUPYTER_URL', None)
        try:
            result = main(['print("test")'])
            assert result == 1
        finally:
            if old_env:
                os.environ['KAGGLE_JUPYTER_URL'] = old_env

    def test_cli_help(self, capsys):
        """Test CLI help output."""
        from kagglerun.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main(['--help'])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert 'kagglerun' in captured.out
        assert 'GPU' in captured.out or 'kagglerun' in captured.out


class TestMCPServer:
    """Tests for MCP server module."""

    def test_mcp_import(self):
        """Test MCP server module can be imported."""
        from kagglerun.mcp_server import TOOLS, handle_tool_call
        assert len(TOOLS) > 0
        assert callable(handle_tool_call)

    def test_mcp_tools_defined(self):
        """Test all expected tools are defined."""
        from kagglerun.mcp_server import TOOLS

        tool_names = [t["name"] for t in TOOLS]
        assert "execute_python" in tool_names
        assert "get_gpu_info" in tool_names
        assert "list_files" in tool_names
        assert "read_file" in tool_names
        assert "save_file" in tool_names

    def test_mcp_tool_schemas(self):
        """Test tool schemas are valid."""
        from kagglerun.mcp_server import TOOLS

        for tool in TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
