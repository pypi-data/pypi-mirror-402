#!/usr/bin/env python3
"""Unit tests for WardenManager with mocked Docker commands."""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from io import StringIO
import subprocess

# Add src to path
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wardengui.warden import WardenManager, CommandResult


class TestWardenManagerDockerMocking(unittest.TestCase):
    """Test WardenManager with mocked Docker subprocess calls."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.warden = WardenManager(projects_root="~", use_down=False)
    
    @patch('wardengui.warden.subprocess.run')
    def test_get_running_environment_with_running_container(self, mock_run):
        """Test getting running environment when containers are running."""
        # Mock Docker ps output
        mock_result = Mock()
        mock_result.stdout = "pei-php-fpm-1\npei-nginx-1\nother-container"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.warden.get_running_environment()
        
        self.assertEqual(result, 'pei')
        mock_run.assert_called_once()
    
    @patch('wardengui.warden.subprocess.run')
    def test_get_running_environment_no_containers(self, mock_run):
        """Test getting running environment when no containers are running."""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.warden.get_running_environment()
        
        self.assertIsNone(result)
    
    @patch('wardengui.warden.subprocess.run')
    def test_get_env_volumes(self, mock_run):
        """Test getting volumes for an environment."""
        mock_result = Mock()
        mock_result.stdout = "pei_appcode\npei_dbdata\nother_env_volume"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        volumes = self.warden.get_env_volumes('pei')
        
        self.assertEqual(len(volumes), 2)
        self.assertIn('pei_appcode', volumes)
        self.assertIn('pei_dbdata', volumes)
        self.assertNotIn('other_env_volume', volumes)
    
    @patch('wardengui.warden.subprocess.run')
    def test_get_env_containers(self, mock_run):
        """Test getting containers for an environment."""
        mock_result = Mock()
        mock_result.stdout = (
            "pei-php-fpm-1\tUp 5 minutes\trunning\n"
            "pei-nginx-1\tUp 5 minutes\trunning\n"
            "other-container\tExited\tstopped"
        )
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        containers = self.warden.get_env_containers('pei')
        
        self.assertEqual(len(containers), 2)
        self.assertEqual(containers[0]['name'], 'php-fpm')
        self.assertEqual(containers[0]['running'], True)
        self.assertEqual(containers[1]['name'], 'nginx')
    
    @patch('wardengui.warden.subprocess.run')
    def test_stop_environment_success(self, mock_run):
        """Test stopping an environment successfully."""
        mock_result = Mock()
        mock_result.stdout = (
            "Container pei-php-fpm-1 stopped\n"
            "Container pei-nginx-1 stopped\n"
        )
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.warden.stop_environment('pei', '/path/to/project')
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.stopped), 2)
        self.assertIn('php-fpm', result.stopped)
        self.assertIn('nginx', result.stopped)
    
    @patch('wardengui.warden.subprocess.run')
    def test_stop_environment_failure(self, mock_run):
        """Test stopping an environment when it fails."""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = "Error: No such container"
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = self.warden.stop_environment('pei', '/path/to/project')
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
    
    @patch('wardengui.warden.subprocess.run')
    def test_start_environment_success(self, mock_run):
        """Test starting an environment successfully."""
        mock_result = Mock()
        mock_result.stdout = (
            "Network pei_default created\n"
            "Container pei-php-fpm-1 created\n"
            "Container pei-php-fpm-1 started\n"
            "Container pei-nginx-1 started\n"
        )
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.warden.start_environment('pei', '/path/to/project')
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.created), 1)
        self.assertIn('php-fpm', result.created)
        self.assertEqual(len(result.started), 2)
        self.assertTrue(result.network_created)
    
    @patch('wardengui.warden.subprocess.run')
    def test_start_environment_no_containers_error(self, mock_run):
        """Test starting an environment when containers don't exist."""
        mock_result = Mock()
        mock_result.stdout = "has no container to start"
        mock_result.stderr = ""
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = self.warden.start_environment('pei', '/path/to/project')
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
        self.assertIn("Containers don't exist", str(result.errors[0]))
    
    @patch('wardengui.warden.subprocess.run')
    def test_start_services_success(self, mock_run):
        """Test starting Warden services successfully."""
        mock_result = Mock()
        mock_result.stdout = (
            "Container traefik running\n"
            "Container portainer started\n"
        )
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.warden.start_services()
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.started), 0)
    
    @patch('wardengui.warden.subprocess.run')
    def test_restart_services(self, mock_run):
        """Test restarting Warden services."""
        mock_result = Mock()
        mock_result.stdout = "Services restarted"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.warden.restart_services()
        
        self.assertTrue(result.success)
        # Verify the command was called correctly
        call_args = mock_run.call_args[0][0]
        # call_args is a list like ['bash', '-c', 'warden svc restart 2>&1']
        cmd_str = ' '.join(call_args) if isinstance(call_args, list) else str(call_args)
        self.assertIn('svc', cmd_str)
        self.assertIn('restart', cmd_str)
    
    def test_get_stop_command(self):
        """Test getting stop command string."""
        cmd = self.warden.get_stop_command('/path/to/project')
        
        self.assertIn('cd', cmd)
        self.assertIn('/path/to/project', cmd)
        self.assertIn('env stop', cmd)
    
    def test_get_stop_command_with_down(self):
        """Test getting stop command with --down flag."""
        warden = WardenManager(projects_root="~", use_down=True)
        cmd = warden.get_stop_command('/path/to/project')
        
        self.assertIn('env down', cmd)
        self.assertNotIn('env stop', cmd)
    
    def test_get_start_command(self):
        """Test getting start command string."""
        cmd = self.warden.get_start_command('/path/to/project')
        
        self.assertIn('cd', cmd)
        self.assertIn('/path/to/project', cmd)
        self.assertIn('env up -d', cmd)
    
    def test_get_svc_command(self):
        """Test getting services command string."""
        cmd = self.warden.get_svc_command()
        
        self.assertEqual(cmd, "/opt/warden/bin/warden svc up -d")
    
    def test_get_project_url(self):
        """Test getting project URL."""
        project = {
            'TRAEFIK_SUBDOMAIN': 'app',
            'TRAEFIK_DOMAIN': 'test.local'
        }
        
        url = self.warden.get_project_url(project)
        
        self.assertEqual(url, 'app.test.local')
    
    def test_get_project_url_no_subdomain(self):
        """Test getting project URL without subdomain."""
        project = {
            'TRAEFIK_DOMAIN': 'test.local'
        }
        
        url = self.warden.get_project_url(project)
        
        self.assertEqual(url, 'test.local')
    
    def test_parse_docker_output_created(self):
        """Test parsing Docker output for created containers."""
        output = "Container pei-php-fpm-1 created\nContainer pei-nginx-1 created"
        result = self.warden._parse_docker_output(output, 'pei')
        
        self.assertEqual(len(result.created), 2)
        self.assertIn('php-fpm', result.created)
        self.assertIn('nginx', result.created)
    
    def test_parse_docker_output_started(self):
        """Test parsing Docker output for started containers."""
        output = "Container pei-php-fpm-1 started\nContainer pei-nginx-1 started"
        result = self.warden._parse_docker_output(output, 'pei')
        
        self.assertEqual(len(result.started), 2)
        self.assertIn('php-fpm', result.started)
        self.assertIn('nginx', result.started)
    
    def test_parse_docker_output_stopped(self):
        """Test parsing Docker output for stopped containers."""
        output = "Container pei-php-fpm-1 stopped\nContainer pei-nginx-1 stopped"
        result = self.warden._parse_docker_output(output, 'pei')
        
        self.assertEqual(len(result.stopped), 2)
        self.assertIn('php-fpm', result.stopped)
        self.assertIn('nginx', result.stopped)
    
    def test_parse_docker_output_network_created(self):
        """Test parsing Docker output for network creation."""
        output = "Network pei_default created"
        result = self.warden._parse_docker_output(output, 'pei')
        
        self.assertTrue(result.network_created)
    
    def test_parse_docker_output_errors(self):
        """Test parsing Docker output for errors."""
        output = "Error: Container not found\nError: Permission denied"
        result = self.warden._parse_docker_output(output, 'pei')
        
        self.assertGreater(len(result.errors), 0)


if __name__ == '__main__':
    unittest.main()
