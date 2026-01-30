#!/usr/bin/env python3
"""System testing utilities for WardenGUI."""
import os
import platform
import subprocess
import time
import shutil
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class TestResult:
    """Result of a system test."""
    name: str
    passed: bool
    message: str
    value: Optional[Any] = None
    unit: Optional[str] = None


class SystemTester:
    """System testing utilities."""
    
    def __init__(self, projects_root: str = "~"):
        """Initialize system tester."""
        # Expand ~ to full path immediately
        self.projects_root = os.path.expanduser(projects_root)
        self.is_wsl = self._detect_wsl()
        self.is_windows = platform.system() == 'Windows'
    
    @staticmethod
    def _detect_wsl() -> bool:
        """Detect if running in WSL."""
        return ('microsoft' in platform.uname().release.lower() or 
                os.path.exists('/proc/sys/fs/binfmt_misc/WSLInterop'))
    
    def _run_in_wsl(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run command in WSL if on Windows, otherwise run directly."""
        if not self.is_wsl and self.is_windows:
            # On Windows, run through WSL
            return subprocess.run(['wsl'] + cmd, capture_output=True, text=True, timeout=10)
        else:
            # In WSL/Linux, run directly
            return subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    
    def _expand_path_in_wsl(self, path: str) -> str:
        """Expand path in WSL context."""
        if not self.is_wsl and self.is_windows:
            # Running from Windows - expand path in WSL
            result = subprocess.run(
                ['wsl', 'bash', '-c', f'echo $(cd {path} && pwd) 2>/dev/null || echo {path}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                expanded = result.stdout.strip()
                if expanded and expanded != path:
                    return expanded
        # Already in WSL or path expansion failed, use os.path.expanduser
        return os.path.expanduser(path)
    
    def test_filesystem_speed(self, path: Optional[str] = None) -> TestResult:
        """Test filesystem write/read speed (runs in WSL)."""
        test_path = self._expand_path_in_wsl(path if path else self.projects_root)
        
        # Check if path exists (in WSL context)
        if not self.is_wsl and self.is_windows:
            # Check in WSL
            check_result = subprocess.run(
                ['wsl', 'test', '-d', test_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            if check_result.returncode != 0:
                return TestResult(
                    name="Filesystem Speed",
                    passed=False,
                    message=f"Path does not exist in WSL: {test_path}"
                )
        else:
            # Check in current WSL environment
            if not os.path.exists(test_path):
                return TestResult(
                    name="Filesystem Speed",
                    passed=False,
                    message=f"Path does not exist: {test_path}"
                )
            
            if not os.path.isdir(test_path):
                return TestResult(
                    name="Filesystem Speed",
                    passed=False,
                    message=f"Path is not a directory: {test_path}"
                )
        
        # Check if Windows mounted volume
        if self.is_wsl:
            try:
                result = subprocess.run(
                    ['findmnt', '-n', '-o', 'FSTYPE', test_path],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    fstype = result.stdout.strip()
                    if fstype in ['9p', 'drvfs']:
                        return TestResult(
                            name="Filesystem Speed",
                            passed=False,
                            message=f"Path is on Windows mounted volume ({fstype}). Performance will be slow.",
                            value=fstype
                        )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # Check if /mnt/c path (Windows mount)
        if self.is_wsl and test_path.startswith('/mnt/'):
            return TestResult(
                name="Filesystem Speed",
                passed=False,
                message="Path is on Windows mounted volume (/mnt/). Use Linux filesystem for better performance.",
                value="Windows mount"
            )
        
        # Test write speed (run in WSL)
        test_file = os.path.join(test_path, '.wardengui_speed_test')
        test_size_mb = 10
        
        try:
            if not self.is_wsl and self.is_windows:
                # Run speed test in WSL
                import shlex
                safe_path = shlex.quote(test_path)
                safe_file = shlex.quote(test_file)
                
                # Create test script that runs in WSL
                test_script = f"""
                cd {safe_path} || exit 1
                test_file={safe_file}
                test_size={test_size_mb}
                chunk_size=1048576
                
                # Write test
                start=$(date +%s.%N)
                dd if=/dev/zero of="$test_file" bs=$chunk_size count=$test_size 2>/dev/null || exit 1
                write_time=$(echo "$(date +%s.%N) - $start" | bc)
                
                # Read test
                start=$(date +%s.%N)
                dd if="$test_file" of=/dev/null bs=$chunk_size 2>/dev/null || exit 1
                read_time=$(echo "$(date +%s.%N) - $start" | bc)
                
                # Cleanup
                rm -f "$test_file"
                
                echo "$write_time $read_time"
                """
                
                result = subprocess.run(
                    ['wsl', 'bash', '-c', test_script],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    return TestResult(
                        name="Filesystem Speed",
                        passed=False,
                        message=f"Test failed in WSL: {result.stderr.strip() or 'Unknown error'}"
                    )
                
                # Parse results
                times = result.stdout.strip().split()
                if len(times) >= 2:
                    write_time = float(times[0])
                    read_time = float(times[1])
                else:
                    return TestResult(
                        name="Filesystem Speed",
                        passed=False,
                        message="Could not parse test results from WSL"
                    )
            else:
                # Run directly in WSL
                test_data = b'0' * (1024 * 1024)  # 1MB chunk
                
                # Write test
                start_time = time.time()
                with open(test_file, 'wb') as f:
                    for _ in range(test_size_mb):
                        f.write(test_data)
                write_time = time.time() - start_time
                
                # Read test
                start_time = time.time()
                with open(test_file, 'rb') as f:
                    while f.read(1024 * 1024):
                        pass
                read_time = time.time() - start_time
                
                # Cleanup
                os.remove(test_file)
            
            write_speed = test_size_mb / write_time if write_time > 0 else 0
            read_speed = test_size_mb / read_time if read_time > 0 else 0
            avg_speed = (write_speed + read_speed) / 2
            
            # Determine if speed is acceptable (>50 MB/s is good)
            passed = avg_speed > 50
            
            return TestResult(
                name="Filesystem Speed",
                passed=passed,
                message=f"Write: {write_speed:.1f} MB/s, Read: {read_speed:.1f} MB/s, Avg: {avg_speed:.1f} MB/s",
                value=avg_speed,
                unit="MB/s"
            )
        except Exception as e:
            return TestResult(
                name="Filesystem Speed",
                passed=False,
                message=f"Test failed: {str(e)}"
            )
    
    def test_cpu(self) -> TestResult:
        """Test CPU performance."""
        try:
            # Simple CPU benchmark (calculate primes)
            start_time = time.time()
            count = 0
            for i in range(2, 10000):
                is_prime = True
                for j in range(2, int(i ** 0.5) + 1):
                    if i % j == 0:
                        is_prime = False
                        break
                if is_prime:
                    count += 1
            elapsed = time.time() - start_time
            
            # Good if completes in < 0.5 seconds
            passed = elapsed < 0.5
            
            return TestResult(
                name="CPU Performance",
                passed=passed,
                message=f"Calculated {count} primes in {elapsed:.3f}s",
                value=elapsed,
                unit="seconds"
            )
        except Exception as e:
            return TestResult(
                name="CPU Performance",
                passed=False,
                message=f"Test failed: {str(e)}"
            )
    
    def test_memory(self) -> TestResult:
        """Test memory availability."""
        try:
            if self.is_windows:
                # Windows memory check
                result = subprocess.run(
                    ['wmic', 'OS', 'get', 'TotalVisibleMemorySize,FreePhysicalMemory', '/value'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    total = 0
                    free = 0
                    for line in lines:
                        if 'TotalVisibleMemorySize' in line:
                            total = int(line.split('=')[1])
                        elif 'FreePhysicalMemory' in line:
                            free = int(line.split('=')[1])
                    
                    if total > 0:
                        total_gb = total / (1024 * 1024)
                        free_gb = free / (1024 * 1024)
                        used_percent = ((total - free) / total) * 100
                        
                        passed = free_gb > 1.0  # At least 1GB free
                        
                        return TestResult(
                            name="Memory",
                            passed=passed,
                            message=f"Total: {total_gb:.1f} GB, Free: {free_gb:.1f} GB ({used_percent:.1f}% used)",
                            value=free_gb,
                            unit="GB"
                        )
            else:
                # Linux/WSL memory check
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                
                total_kb = 0
                free_kb = 0
                available_kb = 0
                
                for line in meminfo.split('\n'):
                    if line.startswith('MemTotal:'):
                        total_kb = int(line.split()[1])
                    elif line.startswith('MemFree:'):
                        free_kb = int(line.split()[1])
                    elif line.startswith('MemAvailable:'):
                        available_kb = int(line.split()[1])
                
                if total_kb > 0:
                    total_gb = total_kb / (1024 * 1024)
                    available_gb = (available_kb or free_kb) / (1024 * 1024)
                    used_percent = ((total_kb - (available_kb or free_kb)) / total_kb) * 100
                    
                    passed = available_gb > 1.0  # At least 1GB available
                    
                    return TestResult(
                        name="Memory",
                        passed=passed,
                        message=f"Total: {total_gb:.1f} GB, Available: {available_gb:.1f} GB ({used_percent:.1f}% used)",
                        value=available_gb,
                        unit="GB"
                    )
            
            return TestResult(
                name="Memory",
                passed=False,
                message="Could not determine memory information"
            )
        except Exception as e:
            return TestResult(
                name="Memory",
                passed=False,
                message=f"Test failed: {str(e)}"
            )
    
    def test_disk_space(self, path: Optional[str] = None) -> TestResult:
        """Test disk space availability (runs in WSL)."""
        test_path = self._expand_path_in_wsl(path if path else self.projects_root)
        
        try:
            if not self.is_wsl and self.is_windows:
                # Get disk usage from WSL
                import shlex
                safe_path = shlex.quote(test_path)
                result = subprocess.run(
                    ['wsl', 'df', '-B1', safe_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        parts = lines[1].split()
                        if len(parts) >= 4:
                            total_bytes = int(parts[1])
                            used_bytes = int(parts[2])
                            free_bytes = int(parts[3])
                            
                            total_gb = total_bytes / (1024 ** 3)
                            free_gb = free_bytes / (1024 ** 3)
                            used_gb = used_bytes / (1024 ** 3)
                            used_percent = (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0
                            
                            passed = free_gb > 5.0
                            
                            return TestResult(
                                name="Disk Space",
                                passed=passed,
                                message=f"Total: {total_gb:.1f} GB, Free: {free_gb:.1f} GB, Used: {used_percent:.1f}%",
                                value=free_gb,
                                unit="GB"
                            )
                return TestResult(
                    name="Disk Space",
                    passed=False,
                    message=f"Could not get disk usage for {test_path}"
                )
            else:
                # Run directly in WSL
                stat = shutil.disk_usage(test_path)
            
            total_gb = stat.total / (1024 ** 3)
            free_gb = stat.free / (1024 ** 3)
            used_gb = stat.used / (1024 ** 3)
            used_percent = (stat.used / stat.total) * 100
            
            # Pass if at least 5GB free
            passed = free_gb > 5.0
            
            return TestResult(
                name="Disk Space",
                passed=passed,
                message=f"Total: {total_gb:.1f} GB, Free: {free_gb:.1f} GB, Used: {used_percent:.1f}%",
                value=free_gb,
                unit="GB"
            )
        except Exception as e:
            return TestResult(
                name="Disk Space",
                passed=False,
                message=f"Test failed: {str(e)}"
            )
    
    def test_docker(self) -> TestResult:
        """Test Docker availability (runs in WSL)."""
        try:
            # Run Docker commands in WSL context
            if not self.is_wsl and self.is_windows:
                # Run from Windows - execute in WSL
                version_result = self._run_in_wsl(['docker', '--version'])
                if version_result.returncode == 0:
                    version = version_result.stdout.strip()
                    # Check if Docker daemon is running
                    ps_result = self._run_in_wsl(['docker', 'ps'])
                    daemon_running = ps_result.returncode == 0
                    
                    return TestResult(
                        name="Docker",
                        passed=daemon_running,
                        message=f"{version} (WSL). Daemon: {'Running' if daemon_running else 'Not running'}",
                        value=version
                    )
                else:
                    return TestResult(
                        name="Docker",
                        passed=False,
                        message="Docker not found in WSL or not accessible"
                    )
            else:
                # Already in WSL - run directly
                result = subprocess.run(
                    ['docker', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    version = result.stdout.strip()
                    
                    # Check if Docker daemon is running
                    ps_result = subprocess.run(
                        ['docker', 'ps'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    daemon_running = ps_result.returncode == 0
                    
                    return TestResult(
                        name="Docker",
                        passed=daemon_running,
                        message=f"{version}. Daemon: {'Running' if daemon_running else 'Not running'}",
                        value=version
                    )
                else:
                    return TestResult(
                        name="Docker",
                        passed=False,
                        message="Docker not found or not accessible"
                    )
        except FileNotFoundError:
            return TestResult(
                name="Docker",
                passed=False,
                message="Docker command not found"
            )
        except Exception as e:
            return TestResult(
                name="Docker",
                passed=False,
                message=f"Test failed: {str(e)}"
            )
    
    def test_warden(self) -> TestResult:
        """Test Warden availability (runs in WSL)."""
        warden_path = "/opt/warden/bin/warden"
        
        try:
            # Check Warden in WSL context
            if not self.is_wsl and self.is_windows:
                # Run from Windows - check in WSL
                check_result = self._run_in_wsl(['test', '-f', warden_path])
                if check_result.returncode != 0:
                    return TestResult(
                        name="Warden",
                        passed=False,
                        message=f"Warden not found in WSL at {warden_path}"
                    )
                
                # Warden doesn't support --version, just check if it's executable
                check_exec_result = self._run_in_wsl(['test', '-x', warden_path])
                if check_exec_result.returncode == 0:
                    return TestResult(
                        name="Warden",
                        passed=True,
                        message=f"Warden found in WSL at {warden_path}",
                        value="installed"
                    )
                else:
                    return TestResult(
                        name="Warden",
                        passed=False,
                        message=f"Warden found in WSL at {warden_path} but is not executable"
                    )
            else:
                # Already in WSL - check directly
                if not os.path.exists(warden_path):
                    return TestResult(
                        name="Warden",
                        passed=False,
                        message=f"Warden not found at {warden_path}"
                    )
                
                # Warden doesn't support --version, just check if it's executable
                if os.access(warden_path, os.X_OK):
                    return TestResult(
                        name="Warden",
                        passed=True,
                        message=f"Warden found at {warden_path}",
                        value="installed"
                    )
                else:
                    return TestResult(
                        name="Warden",
                        passed=False,
                        message=f"Warden found at {warden_path} but is not executable"
                    )
        except Exception as e:
            return TestResult(
                name="Warden",
                passed=False,
                message=f"Test failed: {str(e)}"
            )
    
    def run_all_tests(self, path: Optional[str] = None) -> List[TestResult]:
        """Run all system tests."""
        results = []
        
        # Expand path if provided
        expanded_path = os.path.expanduser(path) if path else None
        
        results.append(self.test_filesystem_speed(expanded_path))
        results.append(self.test_cpu())
        results.append(self.test_memory())
        results.append(self.test_disk_space(expanded_path))
        results.append(self.test_docker())
        results.append(self.test_warden())
        
        return results
