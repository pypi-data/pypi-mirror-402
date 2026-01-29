from pathlib import Path
from unittest import mock

from docker_detector.core import is_docker


def test_detects_docker_via_dockerenv():
    def path_constructor(*args, **kwargs):
        path_str = str(args[0]) if args else ""
        mock_path = mock.MagicMock(spec=Path)
        mock_path.__str__ = mock.Mock(return_value=path_str)
        mock_path.exists = mock.Mock(return_value=(path_str == "/.dockerenv"))
        mock_path.read_text = mock.Mock()
        return mock_path

    with mock.patch("sys.platform", "linux"), \
         mock.patch("docker_detector.core.Path", side_effect=path_constructor):
        assert is_docker(force_refresh=True) is True


def test_detects_docker_via_cgroup():
    def path_constructor(*args, **kwargs):
        path_str = str(args[0]) if args else ""
        mock_path = mock.MagicMock(spec=Path)
        mock_path.__str__ = mock.Mock(return_value=path_str)
        mock_path.exists = mock.Mock(return_value=False)
        
        def read_text():
            if path_str == "/proc/self/cgroup":
                return "xxx docker yyyy"
            raise FileNotFoundError()
        
        mock_path.read_text = mock.Mock(side_effect=read_text)
        return mock_path

    with mock.patch("sys.platform", "linux"), \
         mock.patch("docker_detector.core.Path", side_effect=path_constructor):
        assert is_docker(force_refresh=True) is True


def test_detects_docker_via_mountinfo():
    def path_constructor(*args, **kwargs):
        path_str = str(args[0]) if args else ""
        mock_path = mock.MagicMock(spec=Path)
        mock_path.__str__ = mock.Mock(return_value=path_str)
        mock_path.exists = mock.Mock(return_value=False)
        
        def read_text():
            if path_str == "/proc/self/cgroup":
                return "0::/"  # Cgroups v2 format
            if path_str == "/proc/self/mountinfo":
                return "1234 24 0:6 /docker/containers/abc123/hostname /etc/hostname rw,nosuid"
            raise FileNotFoundError()
        
        mock_path.read_text = mock.Mock(side_effect=read_text)
        return mock_path

    with mock.patch("sys.platform", "linux"), \
         mock.patch("docker_detector.core.Path", side_effect=path_constructor):
        assert is_docker(force_refresh=True) is True


def test_not_inside_docker_container():
    def path_constructor(*args, **kwargs):
        path_str = str(args[0]) if args else ""
        mock_path = mock.MagicMock(spec=Path)
        mock_path.__str__ = mock.Mock(return_value=path_str)
        mock_path.exists = mock.Mock(return_value=False)
        mock_path.read_text = mock.Mock(side_effect=FileNotFoundError())
        return mock_path

    with mock.patch("sys.platform", "linux"), \
         mock.patch("docker_detector.core.Path", side_effect=path_constructor):
        assert is_docker(force_refresh=True) is False


def test_caching_works_correctly():
    stat_call_count = 0
    read_call_count = 0

    def path_constructor(*args, **kwargs):
        path_str = str(args[0]) if args else ""
        mock_path = mock.MagicMock(spec=Path)
        mock_path.__str__ = mock.Mock(return_value=path_str)
        
        def exists():
            nonlocal stat_call_count
            stat_call_count += 1
            return False
        
        def read_text():
            nonlocal read_call_count
            read_call_count += 1
            if path_str == "/proc/self/cgroup":
                return "xxx docker yyyy"
            raise FileNotFoundError()
        
        mock_path.exists = mock.Mock(side_effect=exists)
        mock_path.read_text = mock.Mock(side_effect=read_text)
        return mock_path

    with mock.patch("sys.platform", "linux"), \
         mock.patch("docker_detector.core.Path", side_effect=path_constructor):
        # First call - force refresh to start fresh
        assert is_docker(force_refresh=True) is True
        assert stat_call_count == 1
        assert read_call_count == 1

        # Second call - should use cache
        assert is_docker() is True
        assert stat_call_count == 1  # Should not increase
        assert read_call_count == 1  # Should not increase


def test_force_refresh_clears_cache_and_rechecks():
    """Test that force_refresh=True actually clears cache and re-runs the check."""
    from docker_detector.core import _is_docker_cached
    
    check_count = 0

    def path_constructor(*args, **kwargs):
        path_str = str(args[0]) if args else ""
        mock_path = mock.MagicMock(spec=Path)
        mock_path.__str__ = mock.Mock(return_value=path_str)
        
        def exists():
            nonlocal check_count
            check_count += 1
            return (path_str == "/.dockerenv")
        
        mock_path.exists = mock.Mock(side_effect=exists)
        mock_path.read_text = mock.Mock(side_effect=FileNotFoundError())
        return mock_path

    with mock.patch("sys.platform", "linux"), \
         mock.patch("docker_detector.core.Path", side_effect=path_constructor):
        # Clear any existing cache first
        _is_docker_cached.cache_clear()
        
        # First call - should check
        assert is_docker() is True
        assert check_count == 1

        # Second call - should use cache
        assert is_docker() is True
        assert check_count == 1  # Should not increase

        # Third call with force_refresh - should clear cache and re-check
        assert is_docker(force_refresh=True) is True
        assert check_count == 2  # Should increase

        # Fourth call - should use cache again
        assert is_docker() is True
        assert check_count == 2  # Should not increase


def test_returns_false_on_non_linux_platforms():
    """Test that is_docker returns False on non-Linux platforms."""
    with mock.patch("sys.platform", "darwin"):  # macOS
        assert is_docker(force_refresh=True) is False
        assert is_docker() is False

    with mock.patch("sys.platform", "win32"):  # Windows
        assert is_docker(force_refresh=True) is False
        assert is_docker() is False
