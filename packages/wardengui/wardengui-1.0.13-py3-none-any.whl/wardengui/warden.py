#!/usr/bin/env python3
"""Warden environment manager class - pure logic, no GUI."""
import subprocess
import json
import platform
import os
import sys
import shlex
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Union


@dataclass
class CommandResult:
    """Result of a warden command execution."""
    success: bool
    output: str = ""
    error: str = ""
    created: List[str] = field(default_factory=list)
    started: List[str] = field(default_factory=list)
    stopped: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    network_created: bool = False
    errors: List[str] = field(default_factory=list)


class WardenManager:
    """Manages Warden Docker environments - pure logic, no GUI output."""
    
    WARDEN_PATH = "/opt/warden/bin/warden"
    
    def __init__(self, projects_root="~", use_down=False):
        # Expand ~ to home directory
        self.projects_root = os.path.expanduser(projects_root)
        self.is_wsl = self._detect_wsl()
        self.use_down = use_down
        
        # Volume cache for async loading
        self._volume_cache = {}
        self._volume_cache_lock = threading.Lock()
        self._volume_loading = set()
    
    @staticmethod
    def _detect_wsl():
        """Detect if running in WSL."""
        return ('microsoft' in platform.uname().release.lower() or 
                os.path.exists('/proc/sys/fs/binfmt_misc/WSLInterop'))
    
    def _run_cmd(self, cmd: Union[str, List[str]], shell: bool = False) -> subprocess.CompletedProcess:
        """Run command, wrapping with wsl if on Windows."""
        if not self.is_wsl and platform.system() == 'Windows':
            if isinstance(cmd, list):
                cmd = ['wsl'] + cmd
        return subprocess.run(cmd, capture_output=True, text=True, shell=shell)
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Scan directory for Warden projects."""
        # Use shlex.quote to safely escape paths
        safe_root = shlex.quote(self.projects_root)
        result = self._run_cmd([
            "bash", "-c", 
            f"find {safe_root} -maxdepth 2 -name '.warden' -type d 2>/dev/null"
        ])
        
        projects = []
        home_result = self._run_cmd(["bash", "-c", "echo $HOME"])
        home_dir = home_result.stdout.strip()
        
        for warden_dir in result.stdout.strip().split('\n'):
            if not warden_dir:
                continue
            if warden_dir == f"{home_dir}/.warden":
                continue
            
            project_dir = warden_dir.replace('/.warden', '')
            env_file = f"{project_dir}/.env"
            
            # Use shlex.quote to safely escape file path
            safe_env_file = shlex.quote(env_file)
            env_result = self._run_cmd(["bash", "-c", f"cat {safe_env_file}"])
            
            config = {'path': project_dir}
            for line in env_result.stdout.split('\n'):
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
            
            if 'WARDEN_ENV_NAME' in config:
                projects.append(config)
        
        return projects
    
    def get_docker_stats(self) -> Dict[str, Dict[str, str]]:
        """Get Docker disk usage statistics."""
        result = self._run_cmd(["docker", "system", "df", "--format", "{{json .}}"])
        stats = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    stats[data.get('Type', '')] = {
                        'size': data.get('Size', '0'),
                        'reclaimable': data.get('Reclaimable', '0')
                    }
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # Skip malformed JSON lines - Docker output may contain non-JSON lines
                    continue
        return stats
    
    def get_running_environment(self) -> Optional[str]:
        """Get currently running Warden environment name."""
        result = self._run_cmd(["docker", "ps", "--format", "{{.Names}}"])
        
        for name in result.stdout.strip().split('\n'):
            if name and '-php-fpm-' in name:
                return name.split('-')[0]
        return None
    
    def get_env_volumes(self, env_name: str) -> List[str]:
        """Get volumes for a specific environment."""
        result = self._run_cmd(["docker", "volume", "ls", "--format", "{{.Name}}"])
        volumes = []
        for vol in result.stdout.strip().split('\n'):
            if vol and vol.startswith(f"{env_name}_"):
                volumes.append(vol)
        return volumes
    
    def get_env_containers(self, env_name: str) -> List[Dict[str, Union[str, bool]]]:
        """Get containers for a specific environment with status."""
        result = self._run_cmd(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.State}}"])
        containers = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                name, status, state = parts[0], parts[1], parts[2]
                if name.startswith(f"{env_name}_") or name.startswith(f"{env_name}-"):
                    short_name = name.replace(f"{env_name}_", "").replace(f"{env_name}-", "")
                    # Remove trailing _1 or -1
                    if short_name.endswith('_1'):
                        short_name = short_name[:-2]
                    elif short_name.endswith('-1'):
                        short_name = short_name[:-2]
                    containers.append({
                        'name': short_name,
                        'status': status,
                        'state': state,
                        'running': state == 'running'
                    })
        return containers
    
    @staticmethod
    def _parse_size_to_bytes(size_str: str) -> float:
        """Parse size string to bytes."""
        try:
            if 'GB' in size_str:
                return float(size_str.replace('GB', '')) * 1024 * 1024 * 1024
            elif 'MB' in size_str:
                return float(size_str.replace('MB', '')) * 1024 * 1024
            elif 'kB' in size_str:
                return float(size_str.replace('kB', '')) * 1024
            elif 'B' in size_str:
                return float(size_str.replace('B', ''))
        except (ValueError, AttributeError) as e:
            # Invalid size format - return 0 instead of failing silently
            return 0
        return 0
    
    def _load_volume_sizes(self, env_name: str) -> Tuple[Dict[str, Tuple[str, float]], str]:
        """Load volume sizes for an environment."""
        result = self._run_cmd(["bash", "-c", "docker system df -v 2>/dev/null"])
        
        volumes = {}
        total_bytes = 0
        in_volumes = False
        
        for line in result.stdout.split('\n'):
            if 'Local Volumes space usage' in line:
                in_volumes = True
                continue
            if in_volumes and line.startswith(f'{env_name}_'):
                parts = line.split()
                if len(parts) >= 3:
                    vol_name = parts[0].replace(f'{env_name}_', '')
                    size_str = parts[2]
                    size_bytes = self._parse_size_to_bytes(size_str)
                    volumes[vol_name] = (size_str, size_bytes)
                    total_bytes += size_bytes
        
        if total_bytes >= 1024 * 1024 * 1024:
            total_str = f"{total_bytes / (1024*1024*1024):.2f} GB"
        elif total_bytes >= 1024 * 1024:
            total_str = f"{total_bytes / (1024*1024):.1f} MB"
        else:
            total_str = f"{total_bytes / 1024:.1f} kB"
        
        return volumes, total_str
    
    def load_volumes_async(self, env_name: str):
        """Load volume sizes in background thread."""
        if env_name in self._volume_loading:
            return
        
        with self._volume_cache_lock:
            if env_name in self._volume_cache:
                return
        
        self._volume_loading.add(env_name)
        
        def loader():
            volumes, total_str = self._load_volume_sizes(env_name)
            with self._volume_cache_lock:
                self._volume_cache[env_name] = (volumes, total_str)
            self._volume_loading.discard(env_name)
        
        thread = threading.Thread(target=loader, daemon=True)
        thread.start()
    
    def get_cached_volume_sizes(self, env_name: str) -> Tuple[Optional[Dict[str, Tuple[str, float]]], Optional[str]]:
        """Get volume sizes from cache only (non-blocking)."""
        with self._volume_cache_lock:
            return self._volume_cache.get(env_name, (None, None))
    
    def is_volume_loading(self, env_name: str) -> bool:
        """Check if volume data is currently loading."""
        return env_name in self._volume_loading
    
    def _parse_docker_output(self, output: str, env_name: str) -> CommandResult:
        """Parse Docker output and return structured result."""
        result = CommandResult(success=True)
        result.output = output
        
        lines = output.strip().split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Skip non-essential lines
            if 'level=warning' in line_lower or 'level=info' in line_lower:
                continue
            if 'regenerating' in line_lower or 'regenerated' in line_lower:
                continue
            if 'connecting' in line_lower:
                continue
            
            # Parse container actions
            if 'created' in line_lower and 'container' in line_lower:
                name = self._extract_container_name(line, env_name)
                if name and name not in result.created:
                    result.created.append(name)
            elif 'started' in line_lower and 'container' in line_lower:
                name = self._extract_container_name(line, env_name)
                if name and name not in result.started:
                    result.started.append(name)
            elif 'stopped' in line_lower and 'container' in line_lower:
                name = self._extract_container_name(line, env_name)
                if name and name not in result.stopped:
                    result.stopped.append(name)
            elif 'removed' in line_lower and 'container' in line_lower:
                name = self._extract_container_name(line, env_name)
                if name and name not in result.removed:
                    result.removed.append(name)
            elif 'network' in line_lower and 'created' in line_lower:
                result.network_created = True
            elif 'error' in line_lower:
                result.errors.append(line.strip())
        
        return result
    
    def _extract_container_name(self, line: str, env_name: str) -> Optional[str]:
        """Extract container service name from Docker output line."""
        parts = line.split()
        for i, part in enumerate(parts):
            if part.lower() == 'container' and i + 1 < len(parts):
                container = parts[i + 1]
                name = container.replace(f'{env_name}-', '').rstrip('-1234567890')
                return name
        return None
    
    def get_stop_command(self, project_path: str) -> str:
        """Get the stop command string."""
        stop_cmd = "down" if self.use_down else "stop"
        # Use shlex.quote to safely escape paths
        safe_path = shlex.quote(project_path)
        return f"cd {safe_path} && {self.WARDEN_PATH} env {stop_cmd}"
    
    def get_start_command(self, project_path: str) -> str:
        """Get the start command string."""
        # Use shlex.quote to safely escape paths
        safe_path = shlex.quote(project_path)
        return f"cd {safe_path} && {self.WARDEN_PATH} env up -d"
    
    def get_svc_command(self) -> str:
        """Get the warden services command string."""
        return f"{self.WARDEN_PATH} svc up -d"
    
    def stop_environment(self, env_name: str, project_path: str) -> CommandResult:
        """Stop a Warden environment."""
        cmd = f"{self.get_stop_command(project_path)} 2>&1"
        proc_result = self._run_cmd(["bash", "-c", cmd])
        
        result = self._parse_docker_output(proc_result.stdout, env_name)
        result.success = proc_result.returncode == 0
        result.error = proc_result.stderr
        
        if not result.success and proc_result.stderr:
            # Add context to error message
            result.errors.append(f"Failed to stop environment '{env_name}': {proc_result.stderr.strip()}")
        
        return result
    
    def start_services(self) -> CommandResult:
        """Start Warden global services."""
        cmd = f"{self.get_svc_command()} 2>&1"
        proc_result = self._run_cmd(["bash", "-c", cmd])
        
        result = CommandResult(
            success=proc_result.returncode == 0,
            output=proc_result.stdout,
            error=proc_result.stderr
        )
        
        # Parse output for service status
        for line in proc_result.stdout.split('\n'):
            line_lower = line.lower()
            if 'running' in line_lower and 'container' in line_lower:
                name = self._extract_service_name(line)
                if name and name not in result.started:
                    result.started.append(name)
            elif 'started' in line_lower and 'container' in line_lower:
                name = self._extract_service_name(line)
                if name and name not in result.started:
                    result.started.append(name)
            elif 'error' in line_lower:
                result.errors.append(line.strip())
        
        return result
    
    def restart_services(self) -> CommandResult:
        """Restart Warden global services."""
        cmd = f"{self.WARDEN_PATH} svc restart 2>&1"
        proc_result = self._run_cmd(["bash", "-c", cmd])
        return CommandResult(
            success=proc_result.returncode == 0,
            output=proc_result.stdout,
            error=proc_result.stderr
        )
    
    def _extract_service_name(self, line: str) -> Optional[str]:
        """Extract service name from Docker output line."""
        parts = line.split()
        for i, part in enumerate(parts):
            if part.lower() == 'container' and i + 1 < len(parts):
                return parts[i + 1]
        return None
    
    def start_environment(self, env_name: str, project_path: str) -> CommandResult:
        """Start a Warden environment."""
        cmd = f"{self.get_start_command(project_path)} 2>&1"
        proc_result = self._run_cmd(["bash", "-c", cmd])
        
        result = self._parse_docker_output(proc_result.stdout, env_name)
        result.success = proc_result.returncode == 0
        result.error = proc_result.stderr
        
        # Check for container-not-exist errors
        if "has no container to start" in proc_result.stdout:
            result.errors.append(
                f"Containers don't exist for environment '{env_name}'. "
                f"Run with --down flag to create containers: wardengui --down"
            )
        
        if not result.success and proc_result.stderr:
            # Add context to error message
            result.errors.append(
                f"Failed to start environment '{env_name}': {proc_result.stderr.strip()}. "
                f"Check that Docker is running and the project path '{project_path}' is valid."
            )
        
        return result
    
    def get_project_url(self, project: Dict[str, Any]) -> str:
        """Get full URL for a project."""
        subdomain = project.get('TRAEFIK_SUBDOMAIN', '')
        domain = project.get('TRAEFIK_DOMAIN', 'localhost')
        return f"{subdomain}.{domain}" if subdomain else domain
    
    def check_hosts_file(self, domain: str) -> Optional[str]:
        """Check if domain is in Windows hosts file. Returns IP if found, None otherwise."""
        if platform.system() != 'Windows':
            return None
        
        hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
        try:
            with open(hosts_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        ip = parts[0]
                        hostnames = parts[1:]
                        if domain in hostnames:
                            return ip
        except IOError as e:
            # File not found or cannot be read
            return None
        except PermissionError as e:
            # Permission denied - user may need to run as administrator
            return None
        return None
    
    def get_shell_command(self, project_path: str) -> str:
        """Get the shell command string."""
        # Use shlex.quote to safely escape paths
        safe_path = shlex.quote(project_path)
        return f"cd {safe_path} && {self.WARDEN_PATH} shell"
    
    def open_shell(self, project_path: str):
        """Open interactive shell in the environment (blocking)."""
        # Use shlex.quote to safely escape paths
        safe_path = shlex.quote(project_path)
        cmd_str = f"cd {safe_path} && {self.WARDEN_PATH} shell"
        # Run interactively - this will block until user exits
        if not self.is_wsl and platform.system() == 'Windows':
            # On Windows, run through wsl with proper terminal
            subprocess.call(["wsl", "bash", "-c", cmd_str])
        else:
            # In WSL/Linux, run directly using subprocess for better error handling
            subprocess.call(
                ["bash", "-c", cmd_str],
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
    
    def run_cmd_live(self, cmd: str):
        """Run command with live output (for logs, etc.)."""
        if not self.is_wsl and platform.system() == 'Windows':
            # Use subprocess for better control and error handling
            subprocess.call(
                ["wsl", "bash", "-c", cmd],
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
        else:
            # Use subprocess instead of os.system for better error handling
            subprocess.call(
                ["bash", "-c", cmd],
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
    
    def get_git_remote_url(self, project_path: str) -> Optional[str]:
        """Get GitHub/Git remote URL for a project."""
        # Use shlex.quote to safely escape paths
        safe_path = shlex.quote(project_path)
        result = self._run_cmd(["bash", "-c", f"cd {safe_path} && git remote get-url origin 2>/dev/null"])
        url = result.stdout.strip()
        if url:
            # Convert SSH to HTTPS format for display
            if url.startswith('git@github.com:'):
                url = url.replace('git@github.com:', 'https://github.com/').replace('.git', '')
            elif url.endswith('.git'):
                url = url[:-4]
            return url
        return None
