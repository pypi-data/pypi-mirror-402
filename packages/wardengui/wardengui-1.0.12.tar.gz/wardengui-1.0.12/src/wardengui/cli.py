#!/usr/bin/env python3
"""Warden GUI - Interactive console interface for managing Warden environments."""
import platform
import os
import sys
from typing import List, Dict, Any, Optional, Union, Tuple

# Support both direct execution and module import
try:
    from .warden import WardenManager, CommandResult
    from .colors import Colors
except ImportError:
    from warden import WardenManager, CommandResult
    from colors import Colors

# Config
DEFAULT_PROJECTS_ROOT = "~"


def clear_screen() -> None:
    """Clear the terminal screen."""
    import subprocess
    try:
        if platform.system() == 'Windows':
            subprocess.run(['cls'], shell=True, check=True)
        else:
            subprocess.run(['clear'], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: print newlines if clear command fails
        print('\n' * 50)


def print_command_result(result: CommandResult, action: str, env_name: str = "") -> None:
    """Print the result of a warden command in a nice format."""
    prefix = f"{env_name}-" if env_name else ""
    
    if result.network_created:
        print(f"  {Colors.GREEN}✓{Colors.RESET} Network {env_name}_default {Colors.GREEN}Created{Colors.RESET}")
    
    if result.created:
        for item in result.created:
            print(f"  {Colors.GREEN}✓{Colors.RESET} Container {prefix}{item}-1 {Colors.GREEN}Created{Colors.RESET}")
    
    if result.started:
        for item in result.started:
            print(f"  {Colors.GREEN}✓{Colors.RESET} Container {prefix}{item}-1 {Colors.GREEN}Started{Colors.RESET}")
    
    if result.stopped:
        for item in result.stopped:
            print(f"  {Colors.YELLOW}✓{Colors.RESET} Container {prefix}{item}-1 {Colors.YELLOW}Stopped{Colors.RESET}")
    
    if result.removed:
        for item in result.removed:
            print(f"  {Colors.RED}✓{Colors.RESET} Container {prefix}{item}-1 {Colors.RED}Removed{Colors.RESET}")
    
    for err in result.errors:
        print(f"  {Colors.RED}✗{Colors.RESET} {err}")


def stop_environment_ui(warden: WardenManager, env_name: str, project_path: str) -> bool:
    """Stop environment with UI feedback."""
    stop_cmd = "down" if warden.use_down else "stop"
    action = "STOPPING & REMOVING" if warden.use_down else "STOPPING"
    title = f"{action} {env_name.upper()}"
    
    print()
    print(f"{Colors.BOLD}{title}{Colors.RESET}")
    print()
    
    cmd = warden.get_stop_command(project_path)
    print(f"  {Colors.GRAY}$ {cmd}{Colors.RESET}\n")
    
    result = warden.stop_environment(env_name, project_path)
    
    print_command_result(result, "stop", env_name)
    
    print()
    if result.success:
        print(f"  {Colors.GREEN}✓{Colors.RESET} Environment {env_name} stopped successfully")
    else:
        print(f"  {Colors.RED}✗{Colors.RESET} Failed to stop {env_name}")
        if result.error:
            for line in result.error.strip().split('\n')[:3]:
                print(f"    {line}")
    
    return result.success


def start_environment_ui(warden: WardenManager, env_name: str, project_path: str) -> bool:
    """Start environment with UI feedback."""
    title = f"STARTING {env_name.upper()}"
    print()
    print(f"{Colors.BOLD}{title}{Colors.RESET}")
    print()
    
    # Step 1: Start warden services
    print(f"  {Colors.BLUE}Step 1/3:{Colors.RESET} Starting Warden services...")
    svc_cmd = warden.get_svc_command()
    print(f"  {Colors.GRAY}$ {svc_cmd}{Colors.RESET}\n")
    
    svc_result = warden.start_services()
    
    if svc_result.started:
        print(f"  Running:")
        for svc in svc_result.started:
            print(f"    {Colors.GREEN}●{Colors.RESET} {svc}")
    
    if svc_result.errors:
        for err in svc_result.errors:
            print(f"  {Colors.RED}✗{Colors.RESET} {err}")
    
    if svc_result.success:
        print(f"  {Colors.GREEN}✓{Colors.RESET} Warden services ready")
    else:
        print(f"  {Colors.YELLOW}⚠{Colors.RESET} Warden services (some may have failed)")
    
    # Step 2: Start environment
    print(f"\n  {Colors.BLUE}Step 2/3:{Colors.RESET} Starting {env_name} environment...")
    env_cmd = warden.get_start_command(project_path)
    print(f"  {Colors.GRAY}$ {env_cmd}{Colors.RESET}\n")
    
    result = warden.start_environment(env_name, project_path)
    
    print_command_result(result, "start", env_name)
    
    # Step 3: Restart services to pick up new env
    print(f"\n  {Colors.BLUE}Step 3/3:{Colors.RESET} Restarting Warden services...")
    restart_cmd = f"{warden.WARDEN_PATH} svc restart"
    print(f"  {Colors.GRAY}$ {restart_cmd}{Colors.RESET}\n")
    warden.restart_services()
    print(f"  {Colors.GREEN}✓{Colors.RESET} Services restarted")
    
    print()
    if result.success:
        print(f"  {Colors.GREEN}✓{Colors.RESET} Environment {env_name} started successfully")
    else:
        print(f"  {Colors.RED}✗{Colors.RESET} Failed to start {env_name}")
        if "Containers don't exist" in str(result.errors):
            print()
            print(f"  Hint: Run with --down flag to create containers:")
            print(f"    wardengui --down")
    
    return result.success


def _print_menu_header(docker_stats: Optional[Dict[str, Dict[str, str]]], num_projects: int) -> None:
    """Print the menu header with Docker stats."""
    print(f"{Colors.BOLD}  🐳 WARDEN ENVIRONMENT MANAGER:{Colors.RESET}")
    print(f"  Commands: 0-9=select │ ssh │ start │ ↑/↓ │ q=quit │ ?=help")
    
    if docker_stats:
        img = docker_stats.get('Images', {})
        vol = docker_stats.get('Local Volumes', {})
        print(f"  📊 Environments: {num_projects}  │  💾 Images: {img.get('size', 'N/A')}  │  💾 Volumes: {vol.get('size', 'N/A')}")
    print()


def _print_project_list(
    warden: WardenManager,
    projects: List[Dict[str, Any]],
    running_env: Optional[str],
    selected_idx: int
) -> None:
    """Print the list of projects with selection indicators."""
    print(f"  {Colors.BOLD}📦 ENVIRONMENTS:{Colors.RESET}")
    
    for i, proj in enumerate(projects):
        env_name = proj.get('WARDEN_ENV_NAME', 'unknown')
        full_domain = warden.get_project_url(proj)
        is_running = env_name == running_env
        is_selected = i == selected_idx
        
        # Status indicators
        if is_running:
            status_icon = f"{Colors.GREEN}●{Colors.RESET}"
            status_text = f"{Colors.GREEN}RUNNING{Colors.RESET}"
        else:
            status_icon = f"{Colors.GRAY}○{Colors.RESET}"
            status_text = f"{Colors.GRAY}STOPPED{Colors.RESET}"
        
        # Selection highlighting
        if is_selected:
            prefix = "> "
            env_bg = Colors.BG_BLUE
            env_text_color = Colors.WHITE + Colors.BOLD
        else:
            prefix = "  "
            env_bg = ""
            env_text_color = ""
        
        # Format: > 0. [env-name] ● RUNNING -> https://domain.test
        # Apply background color only to the environment name
        # Make URL clickable
        url = f"https://{full_domain}/"
        url_text = f"https://{full_domain}"
        clickable_url = Colors.hyperlink(url, url_text)
        print(f"{prefix}{i}. {env_bg}{env_text_color}[{env_name}]{Colors.RESET}  {status_icon} {status_text}  ->  {clickable_url}")
    
    # Exit option
    exit_idx = len(projects)
    is_exit_selected = selected_idx == exit_idx
    prefix = "> " if is_exit_selected else "  "
    
    print(f"{prefix}q. [Exit]")
    print()


def _print_project_details(
    warden: WardenManager,
    project: Dict[str, Any]
) -> None:
    """Print detailed information about the selected project."""
    env_name = project.get('WARDEN_ENV_NAME', '')
    full_url = warden.get_project_url(project)
    volumes = warden.get_env_volumes(env_name)
    
    vol_sizes, total_size = warden.get_cached_volume_sizes(env_name)
    warden.load_volumes_async(env_name)
    
    # Header
    print(f"{Colors.BOLD}📋 {env_name.upper()} DETAILS:{Colors.RESET}")
    # Basic info section
    path_val = project.get('path', 'N/A')
    print(f"  📁 Path:        {path_val}")
    print(f"  🌐 URL:         https://{full_url}/")
    
    git_url = warden.get_git_remote_url(project.get('path', ''))
    if git_url:
        print(f"  📦 Repo:        {git_url}")
    
    hosts_ip = warden.check_hosts_file(full_url)
    if platform.system() == 'Windows':
        if hosts_ip:
            print(f"  🏠 Hosts:       {Colors.GREEN}✓{Colors.RESET} {hosts_ip} -> {full_url}")
        else:
            print(f"  🏠 Hosts:       {Colors.RED}✗{Colors.RESET} Not in hosts file")
    
    # Configuration section
    print(f"  🔧 Environment: {env_name}")
    env_type = project.get('WARDEN_ENV_TYPE', 'N/A')
    print(f"  📦 Type:        {env_type}")
    php_version = project.get('PHP_VERSION', 'N/A')
    print(f"  🐘 PHP:         {php_version}")
    db_version = project.get('MARIADB_VERSION', project.get('MYSQL_VERSION', 'N/A'))
    print(f"  🗄️  DB:          {db_version}")
    es_version = project.get('ELASTICSEARCH_VERSION', project.get('OPENSEARCH_VERSION', 'N/A'))
    print(f"  🔍 ES:          {es_version}")
    
    # Resources section
    containers = warden.get_env_containers(env_name)
    running_containers = [c for c in containers if c['running']]
    
    # Prepare volume lines
    vol_lines = []
    if vol_sizes is not None:
        sorted_vols = sorted(vol_sizes.items(), key=lambda x: x[1][1], reverse=True)[:6]
        for vol, (size_str, size_bytes) in sorted_vols:
            if size_bytes > 0:
                vol_lines.append(f"  └─ {vol}: {size_str}")
    else:
        loading = "..." if warden.is_volume_loading(env_name) else ""
        vol_lines.append(f"  {loading} loading sizes...")
    
    # Prepare container lines
    cont_lines = []
    sorted_containers = sorted(containers, key=lambda x: x['name'])
    for c in sorted_containers[:6]:
        status = f"{Colors.GREEN}●{Colors.RESET}" if c['running'] else f"{Colors.GRAY}○{Colors.RESET}"
        cont_lines.append(f"{status} {c['name']}")
    
    # Calculate padding for alignment (same as used below)
    sample_vol = vol_lines[0] if vol_lines else "  └─ sample: 1GB"
    sample_cont = cont_lines[0] if cont_lines else "○ sample"
    vol_clean = sample_vol.replace('\033[', '').split('m')[-1] if '\033[' in sample_vol else sample_vol
    cont_clean = sample_cont.replace('\033[', '').split('m')[-1] if '\033[' in sample_cont else sample_cont
    padding_len = max(0, 35 - len(vol_clean))
    container_start_pos = len(vol_clean) + padding_len
    
    # Print header with proper alignment
    volumes_header = f"  💾 Volumes: {len(volumes)}"
    containers_header = f"🐳 Containers: {Colors.GREEN}{len(running_containers)}{Colors.RESET}/{len(containers)} running"
    # Calculate padding to align containers header with container names
    header_padding = container_start_pos - len(volumes_header)
    if header_padding < 0:
        header_padding = 0
    # Remove one space for better alignment
    header_padding = max(0, header_padding - 2)
    print(f"{volumes_header}" + " " * header_padding + f"{containers_header}")
    
    # Print side by side
    max_lines = max(len(vol_lines), len(cont_lines))
    for i in range(max_lines):
        vol_col = vol_lines[i] if i < len(vol_lines) else ""
        cont_col = cont_lines[i] if i < len(cont_lines) else ""
        # Remove ANSI codes for length calculation
        vol_clean = vol_col.replace('\033[', '').split('m')[-1] if '\033[' in vol_col else vol_col
        cont_clean = cont_col.replace('\033[', '').split('m')[-1] if '\033[' in cont_col else cont_col
        padding_len = max(0, 35 - len(vol_clean))
        print(f"{vol_col}" + " " * padding_len + f"{cont_col}")


def display_menu(
    warden: WardenManager,
    projects: List[Dict[str, Any]],
    running_env: Optional[str],
    selected_idx: int,
    docker_stats: Optional[Dict[str, Dict[str, str]]] = None
) -> None:
    """Display the interactive menu."""
    clear_screen()
    _print_menu_header(docker_stats, len(projects))
    _print_project_list(warden, projects, running_env, selected_idx)
    
    if projects and selected_idx < len(projects):
        _print_project_details(warden, projects[selected_idx])


def _read_raw_input() -> Union[str, Tuple[str, Union[int, str]], None]:
    """Read raw input from terminal with arrow key support."""
    import tty
    import termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    buffer = []
    
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            
            # Arrow keys
            if ch == '\x1b':
                ch2 = sys.stdin.read(2)
                if ch2 == '[A':
                    print()
                    return 'up'
                elif ch2 == '[B':
                    print()
                    return 'down'
                continue
            
            # Ctrl+C
            if ch == '\x03':
                print()
                return 'quit'
            
            # Enter - submit command
            if ch == '\r' or ch == '\n':
                print()
                cmd = ''.join(buffer).strip()
                if not cmd:
                    return 'enter'
                return parse_command(cmd)
            
            # Backspace
            if ch == '\x7f' or ch == '\x08':
                if buffer:
                    buffer.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
                continue
            
            # Regular character - echo and add to buffer
            if ch.isprintable():
                buffer.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def get_key() -> Union[str, Tuple[str, Union[int, str]], None]:
    """Get keypress or command. Arrow keys work, or type commands."""
    print("\n> ", end='', flush=True)
    
    try:
        return _read_raw_input()
    except (OSError, AttributeError):
        # Fallback for non-TTY (termios not available on Windows)
        cmd = input().strip()
        return parse_command(cmd)
    except (EOFError, KeyboardInterrupt):
        return 'quit'


def parse_command(cmd: str) -> Union[str, Tuple[str, Union[int, str]], None]:
    """Parse a typed command string."""
    if not cmd:
        return None
    cmd_lower = cmd.lower()
    if cmd_lower in ('u', 'up'):
        return 'up'
    elif cmd_lower in ('d', 'down'):
        return 'down'
    elif cmd_lower in ('q', 'quit', 'exit', 'e'):
        return 'quit'
    elif cmd_lower in ('s', 'ssh', 'shell'):
        return 'ssh'
    elif cmd_lower in ('start',):
        return 'enter'
    elif cmd_lower.isdigit():
        return ('select', int(cmd_lower))
    elif cmd_lower == 'help' or cmd_lower == '?':
        return 'help'
    elif (cmd_lower.startswith('warden ') or cmd_lower.startswith('env ') or 
          cmd_lower.startswith('logs ') or cmd_lower.startswith('log ') or 
          cmd_lower.startswith('run ') or cmd_lower.startswith('port ') or
          cmd_lower in ('log', 'logs', 'ls')):
        return ('warden_cmd', cmd)
    return None


def wait_for_enter() -> None:
    """Wait for Enter key with EOFError handling."""
    try:
        input("\nPress Enter to continue...")
    except EOFError:
        pass


def _handle_ssh_command(
    warden: WardenManager,
    projects: List[Dict[str, Any]],
    running_env: Optional[str]
) -> None:
    """Handle SSH command to connect to running environment."""
    if running_env:
        for proj in projects:
            if proj.get('WARDEN_ENV_NAME') == running_env:
                clear_screen()
                print(f"🔌 Connecting to {running_env}...")
                print(f"{Colors.GRAY}  $ {warden.get_shell_command(proj['path'])}{Colors.RESET}")
                print("\nType 'exit' to return to the menu.\n")
                warden.open_shell(proj['path'])
                break
    else:
        print()
        print(f"{Colors.YELLOW}⚠  No Environment Running{Colors.RESET}")
        print(f"  Select an environment and press Enter to start it.")
        wait_for_enter()


def _handle_warden_command(
    warden: WardenManager,
    projects: List[Dict[str, Any]],
    running_env: Optional[str],
    cmd: str
) -> None:
    """Handle warden command execution in running environment."""
    if running_env:
        for proj in projects:
            if proj.get('WARDEN_ENV_NAME') == running_env:
                warden_bin = warden.WARDEN_PATH
                cmd_l = cmd.lower()
                if cmd_l == 'log' or cmd_l == 'logs':
                    cmd = f'{warden_bin} env logs --tail 100 -f'
                elif cmd_l == 'ls':
                    cmd = f'{warden_bin} env ps'
                elif cmd_l.startswith('log '):
                    cmd = f'{warden_bin} env logs ' + cmd[4:]
                elif cmd_l.startswith('logs '):
                    cmd = f'{warden_bin} env ' + cmd
                elif cmd_l.startswith('run '):
                    cmd = f'{warden_bin} env ' + cmd
                elif cmd_l.startswith('port '):
                    cmd = f'{warden_bin} env ' + cmd
                elif cmd_l.startswith('env '):
                    cmd = f'{warden_bin} ' + cmd
                elif cmd_l.startswith('warden '):
                    cmd = cmd.replace('warden', warden_bin, 1)
                
                import shlex
                safe_path = shlex.quote(proj['path'])
                full_cmd = f"cd {safe_path} && {cmd}"
                clear_screen()
                print(f"Running command...")
                print(f"{Colors.GRAY}  $ {full_cmd}{Colors.RESET}")
                print("\nPress Ctrl+C to stop.\n")
                warden.run_cmd_live(full_cmd)
                print("\n")
                wait_for_enter()
                break
            else:
                print()
                print(f"{Colors.YELLOW}⚠  No Environment Running{Colors.RESET}")
                print(f"  Select an environment and press Enter to start it first.")
                wait_for_enter()


def _handle_environment_start(
    warden: WardenManager,
    projects: List[Dict[str, Any]],
    selected_idx: int,
    running_env: Optional[str]
) -> Optional[str]:
    """Handle starting a selected environment (GUI mode). Returns new running_env."""
    if selected_idx == len(projects):
        clear_screen()
        print("Goodbye! 👋")
        return None
    
    selected = projects[selected_idx]
    selected_name = selected.get('WARDEN_ENV_NAME')
    
    # Check if already running (GUI-specific message)
    if selected_name == running_env:
        print()
        print(f"{Colors.GREEN}✓ Environment Already Running{Colors.RESET}")
        print(f"  {selected_name} is already running.")
        wait_for_enter()
        return running_env
    
    # Use core start logic
    success, new_running_env = _start_environment_core(warden, selected_name, selected, projects, running_env, headless=False)
    
    if not success:
        # GUI-specific error handling
        if new_running_env != selected_name:
            print(f"\n❌ Failed to stop environment '{running_env}'.")
            print(f"   Check Docker is running and try again.")
            if running_env:
                for proj in projects:
                    if proj.get('WARDEN_ENV_NAME') == running_env:
                        print(f"   You can also manually stop it with: cd {proj['path']} && warden env stop")
                        break
        else:
            print(f"\n❌ Failed to start environment '{selected_name}'.")
            print(f"   Check the error messages above for details.")
            print(f"   Ensure Docker is running and the project path is valid.")
        wait_for_enter()
    
    return new_running_env


def _find_project_by_name(env_name: str, projects: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find a project by environment name."""
    for proj in projects:
        if proj.get('WARDEN_ENV_NAME') == env_name:
            return proj
    return None


def _start_environment_core(
    warden: WardenManager,
    env_name: str,
    project: Dict[str, Any],
    projects: List[Dict[str, Any]],
    running_env: Optional[str],
    headless: bool = False
) -> Tuple[bool, Optional[str]]:
    """Core logic for starting an environment. Returns (success, new_running_env)."""
    # If already running
    if env_name == running_env:
        if headless:
            print(f"{Colors.GREEN}✓ Environment '{env_name}' is already running.{Colors.RESET}")
        return (True, running_env)
    
    # Stop current environment if running
    if running_env:
        for proj in projects:
            if proj.get('WARDEN_ENV_NAME') == running_env:
                if headless:
                    print(f"Stopping current environment '{running_env}'...\n")
                stop_success = stop_environment_ui(warden, running_env, proj['path'])
                if not stop_success:
                    if headless:
                        print(f"\n{Colors.RED}✗ Failed to stop '{running_env}'. Aborting.{Colors.RESET}")
                        sys.exit(1)
                    return (False, running_env)
                if headless:
                    print()
                break
    
    # Start the requested environment
    if headless:
        print(f"Starting environment '{env_name}'...\n")
    start_success = start_environment_ui(warden, env_name, project['path'])
    
    if start_success:
        if headless:
            full_url = warden.get_project_url(project)
            print(f"\n{Colors.GREEN}✓ {env_name} is now running!{Colors.RESET}")
            print(f"  -> https://{full_url}/")
        return (True, env_name)
    else:
        if headless:
            print(f"\n{Colors.RED}✗ Failed to start '{env_name}'.{Colors.RESET}")
            sys.exit(1)
        return (False, warden.get_running_environment())


def _show_environment_info(warden: WardenManager, env_name: str, projects: List[Dict[str, Any]]) -> None:
    """Show detailed information about a specific environment (headless mode)."""
    project = _find_project_by_name(env_name, projects)
    
    if not project:
        print(f"{Colors.RED}✗ Environment '{env_name}' not found.{Colors.RESET}")
        print(f"   Available environments:")
        for proj in projects:
            print(f"     - {proj.get('WARDEN_ENV_NAME')}")
        return
    
    # Show info
    _print_project_details(warden, project)
    
    # Show running status
    running_env = warden.get_running_environment()
    is_running = env_name == running_env
    
    print()
    if is_running:
        print(f"  {Colors.GREEN}● Status: RUNNING{Colors.RESET}")
    else:
        print(f"  {Colors.GRAY}○ Status: STOPPED{Colors.RESET}")


def _headless_start(warden: WardenManager, env_name: str, projects: List[Dict[str, Any]]) -> None:
    """Start environment in headless mode (stop current, start new)."""
    project = _find_project_by_name(env_name, projects)
    
    if not project:
        print(f"{Colors.RED}✗ Environment '{env_name}' not found.{Colors.RESET}")
        print(f"   Available environments:")
        for proj in projects:
            print(f"     - {proj.get('WARDEN_ENV_NAME')}")
        sys.exit(1)
        return  # Never reached, but helps with type checking
    
    running_env = warden.get_running_environment()
    success, new_running_env = _start_environment_core(warden, env_name, project, projects, running_env, headless=True)
    
    if success and new_running_env == env_name:
        _show_environment_info(warden, env_name, projects)


def _headless_ssh(warden: WardenManager, env_name: str, projects: List[Dict[str, Any]]) -> None:
    """Open SSH shell to environment in headless mode."""
    project = _find_project_by_name(env_name, projects)
    
    if not project:
        print(f"{Colors.RED}✗ Environment '{env_name}' not found.{Colors.RESET}")
        print(f"   Available environments:")
        for proj in projects:
            print(f"     - {proj.get('WARDEN_ENV_NAME')}")
        sys.exit(1)
        return  # Never reached, but helps with type checking
    
    running_env = warden.get_running_environment()
    if env_name != running_env:
        print(f"{Colors.YELLOW}⚠ Environment '{env_name}' is not running.{Colors.RESET}")
        print(f"   Currently running: {running_env if running_env else 'none'}")
        print(f"   Start it first with: wardengui {env_name} start")
        sys.exit(1)
        return  # Never reached, but helps with type checking
    
    print(f"🔌 Connecting to {env_name}...")
    print(f"{Colors.GRAY}  $ {warden.get_shell_command(project['path'])}{Colors.RESET}")
    print("\nType 'exit' to return.\n")
    warden.open_shell(project['path'])


def _headless_log(warden: WardenManager, env_name: str, projects: List[Dict[str, Any]], tail: int = 100, follow: bool = False) -> None:
    """Show logs for environment in headless mode."""
    project = _find_project_by_name(env_name, projects)
    
    if not project:
        print(f"{Colors.RED}✗ Environment '{env_name}' not found.{Colors.RESET}")
        print(f"   Available environments:")
        for proj in projects:
            print(f"     - {proj.get('WARDEN_ENV_NAME')}")
        sys.exit(1)
        return  # Never reached, but helps with type checking
    
    running_env = warden.get_running_environment()
    if env_name != running_env:
        print(f"{Colors.YELLOW}⚠ Environment '{env_name}' is not running.{Colors.RESET}")
        print(f"   Currently running: {running_env if running_env else 'none'}")
        print(f"   Start it first with: wardengui {env_name} start")
        sys.exit(1)
        return  # Never reached, but helps with type checking
    
    # Build log command
    log_cmd = f"{warden.WARDEN_PATH} env logs"
    if tail:
        log_cmd += f" --tail {tail}"
    if follow:
        log_cmd += " -f"
    
    import shlex
    safe_path = shlex.quote(project['path'])
    full_cmd = f"cd {safe_path} && {log_cmd}"
    
    print(f"📋 Showing logs for {env_name}...")
    print(f"{Colors.GRAY}  $ {full_cmd}{Colors.RESET}")
    if follow:
        print("\nPress Ctrl+C to stop following logs.\n")
    else:
        print()
    
    warden.run_cmd_live(full_cmd)


def main() -> None:
    import signal
    import argparse
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        clear_screen()
        print("Goodbye! 👋")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Warden Environment Manager GUI",
        epilog="Examples:\n  wardengui                    # Interactive GUI\n  wardengui pei start          # Start 'pei' environment\n  wardengui pei info           # Show 'pei' info\n  wardengui pei ssh            # SSH into 'pei' environment\n  wardengui pei log            # Show 'pei' logs\n  wardengui pei log --tail 50  # Show last 50 lines\n  wardengui pei log -f         # Follow logs (tail -f)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-p", "--projects-root", default=DEFAULT_PROJECTS_ROOT,
                        help=f"Root directory to scan for projects (default: {DEFAULT_PROJECTS_ROOT})")
    parser.add_argument("-d", "--down", action="store_true",
                        help="Use 'env down/up' instead of 'env stop/start' (removes containers)")
    parser.add_argument("env_name", nargs="?", help="Environment name for headless mode (e.g., 'pei')")
    parser.add_argument("action", nargs="?", choices=["start", "info", "ssh", "log"], 
                        help="Action: 'start' to start environment, 'info' to show info, 'ssh' to open shell, 'log' to show logs")
    parser.add_argument("--tail", type=int, default=100, metavar="N",
                        help="Number of log lines to show (default: 100)")
    parser.add_argument("-f", "--follow", action="store_true",
                        help="Follow log output (like tail -f)")
    
    args = parser.parse_args()
    
    # Initialize Warden manager
    warden = WardenManager(args.projects_root, use_down=args.down)
    
    # Get projects
    projects = warden.get_projects()
    
    if not projects:
        print()
        print(f"{Colors.RED}✗ No Warden Projects Found{Colors.RESET}")
        print(f"  Searched in: {args.projects_root}")
        print()
        print(f"  Tip: Make sure you have Warden projects with '.warden' directories.")
        print(f"  You can specify a different directory with:")
        print(f"    wardengui -p /path/to/projects")
        print()
        return
    
    # Headless mode: if env_name is provided
    if args.env_name:
        if args.action == "start":
            _headless_start(warden, args.env_name, projects)
            return
        elif args.action == "info":
            _show_environment_info(warden, args.env_name, projects)
            return
        elif args.action == "ssh":
            _headless_ssh(warden, args.env_name, projects)
            return
        elif args.action == "log":
            _headless_log(warden, args.env_name, projects, tail=args.tail, follow=args.follow)
            return
        else:
            # If env_name provided but no action, default to info
            _show_environment_info(warden, args.env_name, projects)
            return
    
    selected_idx = 0
    running_env = warden.get_running_environment()
    docker_stats = warden.get_docker_stats()
    
    # Preload volume data
    for proj in projects:
        env_name = proj.get('WARDEN_ENV_NAME', '')
        if env_name:
            warden.load_volumes_async(env_name)
    
    # Find and select currently running env
    for i, proj in enumerate(projects):
        if proj.get('WARDEN_ENV_NAME') == running_env:
            selected_idx = i
            break
    
    while True:
        display_menu(warden, projects, running_env, selected_idx, docker_stats)
        
        key = get_key()
        
        if key is None:
            continue
        
        total_items = len(projects) + 1
        
        if key == 'quit':
            clear_screen()
            print("Goodbye! 👋")
            break
        elif key == 'ssh':
            _handle_ssh_command(warden, projects, running_env)
        elif key == 'help':
            print()
            print(f"{Colors.BOLD}📖 AVAILABLE COMMANDS:{Colors.RESET}")
            print()
            print(f"  {Colors.BOLD}Navigation:{Colors.RESET}")
            print(f"    0-9      Select environment by number")
            print(f"    ↑/↓ or u/d     Move selection up/down")
            print(f"    Enter    Start selected environment")
            print()
            print(f"  {Colors.BOLD}Actions:{Colors.RESET}")
            print(f"    ssh       Connect to running environment")
            print(f"    start     Start selected environment")
            print(f"    quit/q    Exit the application")
            print(f"    help/?    Show this help")
            print()
            print(f"  {Colors.BOLD}📋 WARDEN COMMANDS:{Colors.RESET} (run in running env)")
            print(f"    log / logs     Follow all logs")
            print(f"    log nginx     Follow nginx logs")
            print(f"    ls             List running containers")
            print(f"    run <cmd>      Run one-off command")
            print(f"    port <svc>     Show port bindings")
            wait_for_enter()
        elif isinstance(key, tuple) and key[0] == 'warden_cmd':
            _handle_warden_command(warden, projects, running_env, key[1])
        elif key == 'up':
            selected_idx = (selected_idx - 1) % total_items
        elif key == 'down':
            selected_idx = (selected_idx + 1) % total_items
        elif isinstance(key, tuple) and key[0] == 'select':
            idx = key[1]
            if 0 <= idx < len(projects):
                selected_idx = idx
                key = 'enter'
            else:
                continue
        
        if key == 'enter':
            new_running_env = _handle_environment_start(warden, projects, selected_idx, running_env)
            if new_running_env is None:
                break
            running_env = new_running_env
            wait_for_enter()


if __name__ == "__main__":
    main()
