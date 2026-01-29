#!/usr/bin/env python3
"""Unit tests for headless mode features."""
import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
from io import StringIO
from typing import Dict, Any, List

# Add src to path
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wardengui.cli import (
    _find_project_by_name,
    _start_environment_core,
    _show_environment_info,
    _headless_start,
    _headless_ssh,
    _headless_log,
    main
)
from wardengui.warden import WardenManager, CommandResult


class TestHeadlessFeatures(unittest.TestCase):
    """Test headless mode functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_warden = Mock(spec=WardenManager)
        self.mock_warden.WARDEN_PATH = "/opt/warden/bin/warden"
        self.mock_warden.use_down = False
        
        # Sample projects data
        self.sample_projects = [
            {
                'WARDEN_ENV_NAME': 'api',
                'path': '/home/user/api-project',
                'TRAEFIK_SUBDOMAIN': 'app',
                'TRAEFIK_DOMAIN': 'apitire.test',
                'WARDEN_ENV_TYPE': 'symfony',
                'PHP_VERSION': '8.4',
                'MARIADB_VERSION': '10.11'
            },
            {
                'WARDEN_ENV_NAME': 'pei',
                'path': '/home/user/pei-project',
                'TRAEFIK_SUBDOMAIN': 'app',
                'TRAEFIK_DOMAIN': 'peigenesis.test',
                'WARDEN_ENV_TYPE': 'symfony',
                'PHP_VERSION': '8.4',
                'MARIADB_VERSION': '10.11'
            }
        ]
    
    def test_find_project_by_name_found(self):
        """Test finding a project by name when it exists."""
        result = _find_project_by_name('api', self.sample_projects)
        self.assertIsNotNone(result)
        self.assertEqual(result['WARDEN_ENV_NAME'], 'api')
        self.assertEqual(result['path'], '/home/user/api-project')
    
    def test_find_project_by_name_not_found(self):
        """Test finding a project by name when it doesn't exist."""
        result = _find_project_by_name('nonexistent', self.sample_projects)
        self.assertIsNone(result)
    
    @patch('wardengui.cli.stop_environment_ui')
    @patch('wardengui.cli.start_environment_ui')
    def test_start_environment_core_already_running(self, mock_start, mock_stop):
        """Test starting an environment that's already running."""
        self.mock_warden.get_running_environment.return_value = 'api'
        
        project = self.sample_projects[0]
        success, running_env = _start_environment_core(
            self.mock_warden,
            'api',
            project,
            self.sample_projects,
            'api',
            headless=True
        )
        
        self.assertTrue(success)
        self.assertEqual(running_env, 'api')
        mock_start.assert_not_called()
        mock_stop.assert_not_called()
    
    @patch('wardengui.cli.stop_environment_ui')
    @patch('wardengui.cli.start_environment_ui')
    def test_start_environment_core_stop_current_then_start(self, mock_start, mock_stop):
        """Test stopping current environment and starting new one."""
        self.mock_warden.get_running_environment.return_value = 'pei'
        mock_stop.return_value = True
        mock_start.return_value = True
        self.mock_warden.get_project_url.return_value = 'app.apitire.test'
        
        project = self.sample_projects[0]  # api project
        success, running_env = _start_environment_core(
            self.mock_warden,
            'api',
            project,
            self.sample_projects,
            'pei',  # Currently running
            headless=True
        )
        
        self.assertTrue(success)
        self.assertEqual(running_env, 'api')
        mock_stop.assert_called_once_with(self.mock_warden, 'pei', '/home/user/pei-project')
        mock_start.assert_called_once_with(self.mock_warden, 'api', '/home/user/api-project')
    
    @patch('wardengui.cli.stop_environment_ui')
    @patch('wardengui.cli.start_environment_ui')
    def test_start_environment_core_stop_fails(self, mock_start, mock_stop):
        """Test when stopping current environment fails."""
        self.mock_warden.get_running_environment.return_value = 'pei'
        mock_stop.return_value = False
        
        project = self.sample_projects[0]
        
        with patch('sys.exit') as mock_exit:
            success, running_env = _start_environment_core(
                self.mock_warden,
                'api',
                project,
                self.sample_projects,
                'pei',
                headless=True
            )
            
            self.assertFalse(success)
            self.assertEqual(running_env, 'pei')
            mock_exit.assert_called_once_with(1)
            mock_start.assert_not_called()
    
    @patch('wardengui.cli.stop_environment_ui')
    @patch('wardengui.cli.start_environment_ui')
    def test_start_environment_core_start_fails(self, mock_start, mock_stop):
        """Test when starting new environment fails."""
        self.mock_warden.get_running_environment.return_value = None
        mock_start.return_value = False
        self.mock_warden.get_running_environment.side_effect = [None, None]
        
        project = self.sample_projects[0]
        
        with patch('sys.exit') as mock_exit:
            success, running_env = _start_environment_core(
                self.mock_warden,
                'api',
                project,
                self.sample_projects,
                None,
                headless=True
            )
            
            self.assertFalse(success)
            mock_exit.assert_called_once_with(1)
            mock_start.assert_called_once()
    
    @patch('wardengui.cli._print_project_details')
    def test_show_environment_info_found(self, mock_print_details):
        """Test showing info for an existing environment."""
        self.mock_warden.get_running_environment.return_value = 'api'
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            _show_environment_info(self.mock_warden, 'api', self.sample_projects)
        
        mock_print_details.assert_called_once()
        self.mock_warden.get_running_environment.assert_called()
    
    @patch('wardengui.cli._print_project_details')
    def test_show_environment_info_not_found(self, mock_print_details):
        """Test showing info for a non-existent environment."""
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            _show_environment_info(self.mock_warden, 'nonexistent', self.sample_projects)
        
        mock_print_details.assert_not_called()
        output = mock_stdout.getvalue()
        self.assertIn("✗ Environment 'nonexistent' not found", output)
        self.assertIn("Available environments", output)
    
    @patch('wardengui.cli._start_environment_core')
    @patch('wardengui.cli._show_environment_info')
    def test_headless_start_success(self, mock_show_info, mock_start_core):
        """Test successful headless start."""
        self.mock_warden.get_running_environment.return_value = None
        mock_start_core.return_value = (True, 'api')
        
        _headless_start(self.mock_warden, 'api', self.sample_projects)
        
        mock_start_core.assert_called_once()
        mock_show_info.assert_called_once_with(self.mock_warden, 'api', self.sample_projects)
    
    @patch('wardengui.cli._start_environment_core')
    def test_headless_start_env_not_found(self, mock_start_core):
        """Test headless start when environment not found."""
        with patch('sys.exit') as mock_exit:
            _headless_start(self.mock_warden, 'nonexistent', self.sample_projects)
        
        mock_exit.assert_called_once_with(1)
        mock_start_core.assert_not_called()
    
    @patch('wardengui.cli._start_environment_core')
    @patch('wardengui.cli._show_environment_info')
    def test_headless_start_already_running(self, mock_show_info, mock_start_core):
        """Test headless start when environment is already running."""
        self.mock_warden.get_running_environment.return_value = 'api'
        mock_start_core.return_value = (True, 'api')
        
        _headless_start(self.mock_warden, 'api', self.sample_projects)
        
        mock_start_core.assert_called_once()
        mock_show_info.assert_called_once()


class TestHeadlessIntegration(unittest.TestCase):
    """Integration tests for headless mode with mocked WardenManager."""
    
    def setUp(self):
        """Set up test fixtures with mocked WardenManager."""
        self.mock_warden = Mock(spec=WardenManager)
        self.mock_warden.WARDEN_PATH = "/opt/warden/bin/warden"
        self.mock_warden.use_down = False
        self.mock_warden.projects_root = "/home/user"
        
        # Mock methods
        self.mock_warden.get_projects.return_value = [
            {
                'WARDEN_ENV_NAME': 'test-env',
                'path': '/home/user/test-project',
                'TRAEFIK_SUBDOMAIN': 'app',
                'TRAEFIK_DOMAIN': 'test.local',
            }
        ]
        self.mock_warden.get_running_environment.return_value = None
        self.mock_warden.get_project_url.return_value = 'app.test.local'
        self.mock_warden.get_env_volumes.return_value = ['test-env_appcode', 'test-env_dbdata']
        self.mock_warden.get_env_containers.return_value = [
            {'name': 'php-fpm', 'running': True, 'status': 'Up 5 minutes', 'state': 'running'},
            {'name': 'nginx', 'running': True, 'status': 'Up 5 minutes', 'state': 'running'},
        ]
        self.mock_warden.get_cached_volume_sizes.return_value = (
            {'appcode': ('1.5GB', 1610612736), 'dbdata': ('500MB', 524288000)},
            '2.0GB'
        )
        self.mock_warden.is_volume_loading.return_value = False
        self.mock_warden.load_volumes_async = Mock()
        self.mock_warden.get_git_remote_url.return_value = 'https://github.com/user/test-project'
        self.mock_warden.check_hosts_file.return_value = None
    
    @patch('wardengui.cli.stop_environment_ui')
    @patch('wardengui.cli.start_environment_ui')
    @patch('wardengui.cli._print_project_details')
    def test_headless_start_full_flow(self, mock_print_details, mock_start, mock_stop):
        """Test complete headless start flow."""
        mock_start.return_value = True
        
        projects = self.mock_warden.get_projects()
        _headless_start(self.mock_warden, 'test-env', projects)
        
        mock_start.assert_called_once()
        mock_print_details.assert_called_once()
    
    @patch('wardengui.cli._print_project_details')
    def test_headless_info_full_flow(self, mock_print_details):
        """Test complete headless info flow."""
        projects = self.mock_warden.get_projects()
        _show_environment_info(self.mock_warden, 'test-env', projects)
        
        mock_print_details.assert_called_once()
        self.mock_warden.get_running_environment.assert_called()
    
    @patch('wardengui.cli.stop_environment_ui')
    @patch('wardengui.cli.start_environment_ui')
    def test_start_environment_core_with_mocked_services(self, mock_start, mock_stop):
        """Test start environment core with mocked service calls."""
        # Mock successful start
        mock_start.return_value = True
        self.mock_warden.get_project_url.return_value = 'app.test.local'
        
        project = self.mock_warden.get_projects()[0]
        success, running_env = _start_environment_core(
            self.mock_warden,
            'test-env',
            project,
            self.mock_warden.get_projects(),
            None,
            headless=True
        )
        
        self.assertTrue(success)
        self.assertEqual(running_env, 'test-env')
        mock_start.assert_called_once()
    
    def test_start_environment_core_no_current_running(self):
        """Test starting when no environment is currently running."""
        self.mock_warden.get_running_environment.return_value = None
        
        project = self.mock_warden.get_projects()[0]
        
        with patch('wardengui.cli.start_environment_ui') as mock_start:
            mock_start.return_value = True
            self.mock_warden.get_project_url.return_value = 'app.test.local'
            
            success, running_env = _start_environment_core(
                self.mock_warden,
                'test-env',
                project,
                self.mock_warden.get_projects(),
                None,
                headless=True
            )
            
            self.assertTrue(success)
            mock_start.assert_called_once()


class TestHeadlessErrorCases(unittest.TestCase):
    """Test error handling in headless mode."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_warden = Mock(spec=WardenManager)
        self.projects = [
            {'WARDEN_ENV_NAME': 'env1', 'path': '/path1'},
            {'WARDEN_ENV_NAME': 'env2', 'path': '/path2'},
        ]
    
    def test_headless_start_env_not_found_exits(self):
        """Test that headless start exits when environment not found."""
        with patch('sys.exit') as mock_exit:
            _headless_start(self.mock_warden, 'nonexistent', self.projects)
        
        mock_exit.assert_called_once_with(1)
    
    @patch('wardengui.cli.stop_environment_ui')
    def test_start_environment_core_stop_failure_exits(self, mock_stop):
        """Test that headless mode exits when stop fails."""
        mock_stop.return_value = False
        
        project = self.projects[0]
        
        with patch('sys.exit') as mock_exit:
            _start_environment_core(
                self.mock_warden,
                'env1',
                project,
                self.projects,
                'env2',
                headless=True
            )
        
        mock_exit.assert_called_once_with(1)
    
    @patch('wardengui.cli.start_environment_ui')
    def test_start_environment_core_start_failure_exits(self, mock_start):
        """Test that headless mode exits when start fails."""
        mock_start.return_value = False
        self.mock_warden.get_running_environment.return_value = None
        
        project = self.projects[0]
        
        with patch('sys.exit') as mock_exit:
            _start_environment_core(
                self.mock_warden,
                'env1',
                project,
                self.projects,
                None,
                headless=True
            )
        
        mock_exit.assert_called_once_with(1)


class TestMainHeadlessMode(unittest.TestCase):
    """Test main() function headless mode handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_warden = Mock(spec=WardenManager)
        self.mock_warden.WARDEN_PATH = "/opt/warden/bin/warden"
        self.projects = [
            {
                'WARDEN_ENV_NAME': 'test-env',
                'path': '/home/user/test-project',
                'TRAEFIK_SUBDOMAIN': 'app',
                'TRAEFIK_DOMAIN': 'test.local',
            }
        ]
    
    @patch('wardengui.cli._headless_start')
    @patch('wardengui.cli.WardenManager')
    @patch('sys.argv', ['wardengui', 'test-env', 'start'])
    def test_main_headless_start(self, mock_warden_class, mock_headless_start):
        """Test main() with headless start command."""
        mock_warden_instance = Mock()
        mock_warden_class.return_value = mock_warden_instance
        mock_warden_instance.get_projects.return_value = self.projects
        
        main()
        
        mock_headless_start.assert_called_once_with(
            mock_warden_instance,
            'test-env',
            self.projects
        )
    
    @patch('wardengui.cli._headless_ssh')
    @patch('wardengui.cli.WardenManager')
    @patch('sys.argv', ['wardengui', 'test-env', 'ssh'])
    def test_main_headless_ssh(self, mock_warden_class, mock_headless_ssh):
        """Test main() with headless ssh command."""
        mock_warden_instance = Mock()
        mock_warden_class.return_value = mock_warden_instance
        mock_warden_instance.get_projects.return_value = self.projects
        
        main()
        
        mock_headless_ssh.assert_called_once_with(
            mock_warden_instance,
            'test-env',
            self.projects
        )
    
    @patch('wardengui.cli._headless_log')
    @patch('wardengui.cli.WardenManager')
    @patch('sys.argv', ['wardengui', 'test-env', 'log'])
    def test_main_headless_log(self, mock_warden_class, mock_headless_log):
        """Test main() with headless log command."""
        mock_warden_instance = Mock()
        mock_warden_class.return_value = mock_warden_instance
        mock_warden_instance.get_projects.return_value = self.projects
        
        main()
        
        mock_headless_log.assert_called_once()
        # Check that it was called with default tail=100 and follow=False
        call_kwargs = mock_headless_log.call_args[1]
        self.assertEqual(call_kwargs.get('tail'), 100)
        self.assertEqual(call_kwargs.get('follow'), False)
    
    @patch('wardengui.cli._headless_log')
    @patch('wardengui.cli.WardenManager')
    @patch('sys.argv', ['wardengui', 'test-env', 'log', '--tail', '50', '-f'])
    def test_main_headless_log_with_options(self, mock_warden_class, mock_headless_log):
        """Test main() with headless log command and options."""
        mock_warden_instance = Mock()
        mock_warden_class.return_value = mock_warden_instance
        mock_warden_instance.get_projects.return_value = self.projects
        
        main()
        
        call_kwargs = mock_headless_log.call_args[1]
        self.assertEqual(call_kwargs.get('tail'), 50)
        self.assertEqual(call_kwargs.get('follow'), True)
    
    @patch('wardengui.cli._show_environment_info')
    @patch('wardengui.cli.WardenManager')
    @patch('sys.argv', ['wardengui', 'test-env', 'info'])
    def test_main_headless_info(self, mock_warden_class, mock_show_info):
        """Test main() with headless info command."""
        mock_warden_instance = Mock()
        mock_warden_class.return_value = mock_warden_instance
        mock_warden_instance.get_projects.return_value = self.projects
        
        main()
        
        mock_show_info.assert_called_once_with(
            mock_warden_instance,
            'test-env',
            self.projects
        )
    
    @patch('wardengui.cli._show_environment_info')
    @patch('wardengui.cli.WardenManager')
    @patch('sys.argv', ['wardengui', 'test-env'])
    def test_main_headless_default_info(self, mock_warden_class, mock_show_info):
        """Test main() with env name but no action (defaults to info)."""
        mock_warden_instance = Mock()
        mock_warden_class.return_value = mock_warden_instance
        mock_warden_instance.get_projects.return_value = self.projects
        
        main()
        
        mock_show_info.assert_called_once_with(
            mock_warden_instance,
            'test-env',
            self.projects
        )
    
    @patch('wardengui.cli.WardenManager')
    @patch('sys.argv', ['wardengui'])
    def test_main_no_projects(self, mock_warden_class):
        """Test main() when no projects found."""
        mock_warden_instance = Mock()
        mock_warden_class.return_value = mock_warden_instance
        mock_warden_instance.get_projects.return_value = []
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            main()
        
        output = mock_stdout.getvalue()
        self.assertIn("No Warden Projects Found", output)


class TestHeadlessSSHAndLog(unittest.TestCase):
    """Test headless SSH and log features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_warden = Mock(spec=WardenManager)
        self.mock_warden.WARDEN_PATH = "/opt/warden/bin/warden"
        self.projects = [
            {
                'WARDEN_ENV_NAME': 'test-env',
                'path': '/home/user/test-project',
            }
        ]
    
    def test_headless_ssh_env_not_found(self):
        """Test SSH when environment not found."""
        with patch('sys.exit') as mock_exit:
            _headless_ssh(self.mock_warden, 'nonexistent', self.projects)
        
        mock_exit.assert_called_once_with(1)
    
    def test_headless_ssh_env_not_running(self):
        """Test SSH when environment is not running."""
        self.mock_warden.get_running_environment.return_value = 'other-env'
        
        with patch('sys.exit') as mock_exit:
            _headless_ssh(self.mock_warden, 'test-env', self.projects)
        
        mock_exit.assert_called_once_with(1)
    
    def test_headless_ssh_success(self):
        """Test successful SSH connection."""
        self.mock_warden.get_running_environment.return_value = 'test-env'
        self.mock_warden.get_shell_command.return_value = "cd /path && warden shell"
        self.mock_warden.open_shell = Mock()
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            _headless_ssh(self.mock_warden, 'test-env', self.projects)
        
        self.mock_warden.open_shell.assert_called_once_with('/home/user/test-project')
        self.mock_warden.get_shell_command.assert_called_once()
    
    def test_headless_log_env_not_found(self):
        """Test log when environment not found."""
        with patch('sys.exit') as mock_exit:
            _headless_log(self.mock_warden, 'nonexistent', self.projects)
        
        mock_exit.assert_called_once_with(1)
    
    def test_headless_log_env_not_running(self):
        """Test log when environment is not running."""
        self.mock_warden.get_running_environment.return_value = None
        
        with patch('sys.exit') as mock_exit:
            _headless_log(self.mock_warden, 'test-env', self.projects)
        
        mock_exit.assert_called_once_with(1)
    
    def test_headless_log_success_default(self):
        """Test successful log viewing with default options."""
        self.mock_warden.get_running_environment.return_value = 'test-env'
        self.mock_warden.run_cmd_live = Mock()
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            _headless_log(self.mock_warden, 'test-env', self.projects)
        
        self.mock_warden.run_cmd_live.assert_called_once()
        call_args = self.mock_warden.run_cmd_live.call_args[0][0]
        self.assertIn('env logs', call_args)
        self.assertIn('--tail 100', call_args)
        self.assertNotIn('-f', call_args)
    
    def test_headless_log_with_tail(self):
        """Test log viewing with custom tail value."""
        self.mock_warden.get_running_environment.return_value = 'test-env'
        self.mock_warden.run_cmd_live = Mock()
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            _headless_log(self.mock_warden, 'test-env', self.projects, tail=50)
        
        call_args = self.mock_warden.run_cmd_live.call_args[0][0]
        self.assertIn('--tail 50', call_args)
    
    def test_headless_log_with_follow(self):
        """Test log viewing with follow option."""
        self.mock_warden.get_running_environment.return_value = 'test-env'
        self.mock_warden.run_cmd_live = Mock()
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            _headless_log(self.mock_warden, 'test-env', self.projects, follow=True)
        
        call_args = self.mock_warden.run_cmd_live.call_args[0][0]
        self.assertIn('-f', call_args)
    
    def test_headless_log_with_tail_and_follow(self):
        """Test log viewing with both tail and follow options."""
        self.mock_warden.get_running_environment.return_value = 'test-env'
        self.mock_warden.run_cmd_live = Mock()
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            _headless_log(self.mock_warden, 'test-env', self.projects, tail=200, follow=True)
        
        call_args = self.mock_warden.run_cmd_live.call_args[0][0]
        self.assertIn('--tail 200', call_args)
        self.assertIn('-f', call_args)


class TestWardenManagerMocking(unittest.TestCase):
    """Test headless features with mocked WardenManager methods."""
    
    def setUp(self):
        """Set up test fixtures with comprehensive WardenManager mocking."""
        self.mock_warden = Mock(spec=WardenManager)
        self.mock_warden.WARDEN_PATH = "/opt/warden/bin/warden"
        self.mock_warden.use_down = False
        
        # Mock Docker commands
        self.mock_warden.get_running_environment.return_value = None
        self.mock_warden.get_env_volumes.return_value = ['test-env_appcode', 'test-env_dbdata']
        self.mock_warden.get_env_containers.return_value = [
            {'name': 'php-fpm', 'running': True, 'status': 'Up 5 minutes', 'state': 'running'},
            {'name': 'nginx', 'running': True, 'status': 'Up 5 minutes', 'state': 'running'},
        ]
        self.mock_warden.get_cached_volume_sizes.return_value = (
            {'appcode': ('1.5GB', 1610612736), 'dbdata': ('500MB', 524288000)},
            '2.0GB'
        )
        self.mock_warden.is_volume_loading.return_value = False
        self.mock_warden.load_volumes_async = Mock()
        self.mock_warden.get_git_remote_url.return_value = 'https://github.com/user/test-project'
        self.mock_warden.check_hosts_file.return_value = None
        self.mock_warden.get_project_url.return_value = 'app.test.local'
        
        # Mock command methods
        self.mock_warden.get_stop_command.return_value = "cd /path && /opt/warden/bin/warden env stop"
        self.mock_warden.get_start_command.return_value = "cd /path && /opt/warden/bin/warden env up -d"
        self.mock_warden.get_svc_command.return_value = "/opt/warden/bin/warden svc up -d"
        
        # Mock command execution results
        self.mock_warden.stop_environment.return_value = CommandResult(
            success=True,
            stopped=['php-fpm', 'nginx']
        )
        self.mock_warden.start_environment.return_value = CommandResult(
            success=True,
            created=['php-fpm'],
            started=['php-fpm', 'nginx'],
            network_created=True
        )
        self.mock_warden.start_services.return_value = CommandResult(
            success=True,
            started=['traefik', 'portainer']
        )
        self.mock_warden.restart_services.return_value = CommandResult(success=True)
    
    @patch('wardengui.cli.stop_environment_ui')
    @patch('wardengui.cli.start_environment_ui')
    def test_start_environment_core_with_mocked_warden(self, mock_start, mock_stop):
        """Test start environment core with fully mocked WardenManager."""
        mock_start.return_value = True
        
        project = {
            'WARDEN_ENV_NAME': 'test-env',
            'path': '/home/user/test-project',
        }
        projects = [project]
        
        success, running_env = _start_environment_core(
            self.mock_warden,
            'test-env',
            project,
            projects,
            None,
            headless=True
        )
        
        self.assertTrue(success)
        self.assertEqual(running_env, 'test-env')
        mock_start.assert_called_once_with(
            self.mock_warden,
            'test-env',
            '/home/user/test-project'
        )
    
    @patch('wardengui.cli._print_project_details')
    def test_show_environment_info_with_mocked_warden(self, mock_print_details):
        """Test show environment info with fully mocked WardenManager."""
        self.mock_warden.get_running_environment.return_value = 'test-env'
        
        project = {
            'WARDEN_ENV_NAME': 'test-env',
            'path': '/home/user/test-project',
            'TRAEFIK_SUBDOMAIN': 'app',
            'TRAEFIK_DOMAIN': 'test.local',
        }
        projects = [project]
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            _show_environment_info(self.mock_warden, 'test-env', projects)
        
        mock_print_details.assert_called_once()
        self.mock_warden.get_running_environment.assert_called()
        
        # Verify status output
        output = mock_stdout.getvalue()
        self.assertIn("RUNNING", output)
    
    @patch('wardengui.cli.stop_environment_ui')
    @patch('wardengui.cli.start_environment_ui')
    @patch('wardengui.cli._print_project_details')
    def test_headless_start_full_flow_with_mocks(self, mock_print_details, mock_start, mock_stop):
        """Test complete headless start flow with all mocks."""
        self.mock_warden.get_running_environment.return_value = None
        mock_start.return_value = True
        
        project = {
            'WARDEN_ENV_NAME': 'test-env',
            'path': '/home/user/test-project',
        }
        projects = [project]
        
        _headless_start(self.mock_warden, 'test-env', projects)
        
        mock_start.assert_called_once()
        mock_print_details.assert_called_once()
        self.mock_warden.get_project_url.assert_called()


if __name__ == '__main__':
    unittest.main()
