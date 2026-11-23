from unittest.mock import patch, MagicMock
import eval.decoys.decoy_subprocess_constant as dsc

def test_disk_usage_report():
    with patch("subprocess.run") as mock_run:
        mock_res = MagicMock()
        mock_res.stdout = "dummy disk usage"
        mock_run.return_value = mock_res
        
        res = dsc.disk_usage_report()
        assert res == "dummy disk usage"
        mock_run.assert_called_once_with(
            ["df", "-h", "/"],
            capture_output=True,
            text=True,
            shell=False,
            check=True,
        )

def test_kernel_version():
    with patch("subprocess.check_output") as mock_check_output:
        mock_check_output.return_value = "dummy kernel"
        
        res = dsc.kernel_version()
        assert res == "dummy kernel"
        mock_check_output.assert_called_once_with(["uname", "-r"], text=True)

def test_list_app_processes():
    with patch("subprocess.run") as mock_run:
        mock_res = MagicMock()
        mock_res.stdout = "dummy processes"
        mock_run.return_value = mock_res
        
        res = dsc.list_app_processes()
        assert res == "dummy processes"
        mock_run.assert_called_once_with(
            ["ps", "-eo", "pid,comm"],
            capture_output=True,
            text=True,
            check=True,
        )
