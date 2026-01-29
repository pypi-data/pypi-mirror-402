#!/usr/bin/env python3
"""Warden GUI - Interactive console interface for managing Warden environments."""
import platform
import os
import sys

# Support both direct execution and module import
try:
    from .manager import WardenManager, CommandResult
except ImportError:
    from manager import WardenManager, CommandResult

# Config
DEFAULT_PROJECTS_ROOT = "~"


def clear_screen():
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def print_command_result(result: CommandResult, action: str, env_name: str = ""):
    """Print the result of a warden command in a nice format."""
    prefix = f"{env_name}-" if env_name else ""
    
    if result.network_created:
        print(f"  \033[92m✔\033[0m Network {env_name}_default Created")
    
    if result.created:
        for item in result.created:
            print(f"  \033[92m✔\033[0m Container {prefix}{item}-1 \033[92mCreated\033[0m")
    
    if result.started:
        for item in result.started:
            print(f"  \033[92m✔\033[0m Container {prefix}{item}-1 \033[92mStarted\033[0m")
    
    if result.stopped:
        for item in result.stopped:
            print(f"  \033[93m✔\033[0m Container {prefix}{item}-1 \033[93mStopped\033[0m")
    
    if result.removed:
        for item in result.removed:
            print(f"  \033[91m✔\033[0m Container {prefix}{item}-1 \033[91mRemoved\033[0m")
    
    for err in result.errors:
        print(f"  \033[91m✗ {err}\033[0m")


def stop_environment_ui(warden: WardenManager, env_name: str, project_path: str) -> bool:
    """Stop environment with UI feedback."""
    stop_cmd = "down" if warden.use_down else "stop"
    action = "STOPPING & REMOVING" if warden.use_down else "STOPPING"
    title = f"{action} {env_name.upper()}"
    
    print()
    print(f"╔{'═' * 58}╗")
    print(f"║  🛑 {title:<52} ║")
    print(f"╚{'═' * 58}╝")
    
    cmd = warden.get_stop_command(project_path)
    print(f"\033[90m  $ {cmd}\033[0m")
    print()
    
    result = warden.stop_environment(env_name, project_path)
    
    print_command_result(result, "stop", env_name)
    
    print()
    if result.success:
        print(f"  ✅ Environment {env_name} stopped successfully")
    else:
        print(f"  ❌ Failed to stop {env_name}")
        if result.error:
            for line in result.error.strip().split('\n')[:3]:
                print(f"  \033[91m{line}\033[0m")
    
    return result.success


def start_environment_ui(warden: WardenManager, env_name: str, project_path: str) -> bool:
    """Start environment with UI feedback."""
    title = f"STARTING {env_name.upper()}"
    print()
    print(f"╔{'═' * 58}╗")
    print(f"║  🚀 {title:<52} ║")
    print(f"╚{'═' * 58}╝")
    
    # Step 1: Start warden services
    print(f"\n\033[96m▶ Step 1/3: Starting Warden services...\033[0m")
    svc_cmd = warden.get_svc_command()
    print(f"\033[90m  $ {svc_cmd}\033[0m\n")
    
    svc_result = warden.start_services()
    
    if svc_result.started:
        print(f"  \033[92m▶ Running:\033[0m")
        for svc in svc_result.started:
            print(f"     ├─ {svc}")
    
    if svc_result.errors:
        for err in svc_result.errors:
            print(f"  \033[91m❌ {err}\033[0m")
    
    if svc_result.success:
        print(f"  ✅ Warden services ready")
    else:
        print(f"  ⚠️  Warden services (some may have failed)")
    
    # Step 2: Start environment
    print(f"\n\033[96m▶ Step 2/3: Starting {env_name} environment...\033[0m")
    env_cmd = warden.get_start_command(project_path)
    print(f"\033[90m  $ {env_cmd}\033[0m\n")
    
    result = warden.start_environment(env_name, project_path)
    
    print_command_result(result, "start", env_name)
    
    # Step 3: Restart services to pick up new env
    print(f"\n\033[96m▶ Step 3/3: Restarting Warden services...\033[0m")
    restart_cmd = f"{warden.WARDEN_PATH} svc restart"
    print(f"\033[90m  $ {restart_cmd}\033[0m\n")
    warden.restart_services()
    print(f"  ✅ Services restarted")
    
    print()
    print(f"{'─' * 60}")
    if result.success:
        print(f"  ✅ Environment {env_name} started successfully")
    else:
        print(f"  ❌ Failed to start {env_name}")
        if "Containers don't exist" in str(result.errors):
            print()
            print(f"  \033[93m💡 Hint: Run with --down flag to create containers:\033[0m")
            print(f"     \033[90mwardengui --down\033[0m")
    print(f"{'─' * 60}")
    
    return result.success


def display_menu(warden: WardenManager, projects, running_env, selected_idx, docker_stats=None):
    """Display the interactive menu."""
    clear_screen()
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║               🐳 WARDEN ENVIRONMENT MANAGER                  ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Commands: 0-9=select │ ssh │ start │ up/down │ quit │ help  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # Docker stats bar
    if docker_stats:
        img = docker_stats.get('Images', {})
        vol = docker_stats.get('Local Volumes', {})
        print(f"  📊 Environments: {len(projects)} │ 💾 Images: {img.get('size', 'N/A')} │ Volumes: {vol.get('size', 'N/A')}")
    print()
    
    for i, proj in enumerate(projects):
        env_name = proj.get('WARDEN_ENV_NAME', 'unknown')
        full_domain = warden.get_project_url(proj)
        is_running = env_name == running_env
        is_selected = i == selected_idx
        
        # Status indicator
        status = "● RUNNING" if is_running else "○ STOPPED"
        status_color = "\033[92m" if is_running else "\033[91m"
        reset = "\033[0m"
        
        # Selection indicator
        if is_selected:
            prefix = "▶ "
            line_start = "\033[7m"
            line_end = "\033[0m"
        else:
            prefix = "  "
            line_start = ""
            line_end = ""
        
        print(f"{line_start}{prefix}{i}. [{env_name}] {status_color}{status}{reset} - {full_domain}{line_end}")
    
    # Exit option
    exit_idx = len(projects)
    is_exit_selected = selected_idx == exit_idx
    prefix = "▶ " if is_exit_selected else "  "
    line_start = "\033[7m" if is_exit_selected else ""
    line_end = "\033[0m" if is_exit_selected else ""
    print(f"\n{line_start}{prefix}q. [Exit]{line_end}")
    
    # Show details of selected project
    if projects and selected_idx < len(projects):
        selected = projects[selected_idx]
        env_name = selected.get('WARDEN_ENV_NAME', '')
        full_url = warden.get_project_url(selected)
        volumes = warden.get_env_volumes(env_name)
        
        vol_sizes, total_size = warden.get_cached_volume_sizes(env_name)
        warden.load_volumes_async(env_name)
        
        print()
        print("─" * 66)
        print(f"  📋 {env_name.upper()} DETAILS")
        print("─" * 66)
        print(f"  📁 Path:        {selected.get('path', 'N/A')}")
        print(f"  🌐 URL:         https://{full_url}/")
        
        # Check hosts file on Windows
        hosts_ip = warden.check_hosts_file(full_url)
        if platform.system() == 'Windows':
            if hosts_ip:
                print(f"  🏠 Hosts:       ✅ {hosts_ip} → {full_url}")
            else:
                print(f"  🏠 Hosts:       ❌ Not in hosts file")
        
        print(f"  🔧 Environment: {env_name}")
        print(f"  📦 Type:        {selected.get('WARDEN_ENV_TYPE', 'N/A')}")
        print(f"  🐘 PHP:         {selected.get('PHP_VERSION', 'N/A')}")
        print(f"  🗄️  DB:          {selected.get('MARIADB_VERSION', selected.get('MYSQL_VERSION', 'N/A'))}")
        print(f"  🔍 ES:          {selected.get('ELASTICSEARCH_VERSION', selected.get('OPENSEARCH_VERSION', 'N/A'))}")
        
        # Get containers
        containers = warden.get_env_containers(env_name)
        running_containers = [c for c in containers if c['running']]
        
        # Two-column layout: Volumes | Containers
        print(f"  💿 Volumes: {len(volumes):<20} 🐳 Containers: {len(running_containers)}/{len(containers)} running")
        
        # Prepare volume lines
        vol_lines = []
        if vol_sizes is not None:
            sorted_vols = sorted(vol_sizes.items(), key=lambda x: x[1][1], reverse=True)[:6]
            for vol, (size_str, size_bytes) in sorted_vols:
                if size_bytes > 0:
                    vol_lines.append(f"  └─ {vol}: {size_str}")
        else:
            loading = "⏳" if warden.is_volume_loading(env_name) else ""
            vol_lines.append(f"  {loading} loading sizes...")
        
        # Prepare container lines
        cont_lines = []
        for c in containers[:6]:
            icon = "🟢" if c['running'] else "⚫"
            cont_lines.append(f"{icon} {c['name']}")
        
        # Print side by side
        max_lines = max(len(vol_lines), len(cont_lines))
        for i in range(max_lines):
            vol_col = vol_lines[i] if i < len(vol_lines) else ""
            cont_col = cont_lines[i] if i < len(cont_lines) else ""
            print(f"  {vol_col:<30} {cont_col}")
        
        print("─" * 66)


def get_key():
    """Get keypress or command. Arrow keys work, or type commands."""
    print("\n> ", end='', flush=True)
    
    try:
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
    except (termios.error, OSError, AttributeError):
        # Fallback for non-TTY
        cmd = input().strip()
        return parse_command(cmd)
    except (EOFError, KeyboardInterrupt):
        return 'quit'


def parse_command(cmd):
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


def wait_for_enter():
    """Wait for Enter key with EOFError handling."""
    try:
        input("\nPress Enter to continue...")
    except EOFError:
        pass


def main():
    import signal
    import argparse
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        clear_screen()
        print("Goodbye! 👋")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Warden Environment Manager GUI")
    parser.add_argument("-p", "--projects-root", default=DEFAULT_PROJECTS_ROOT,
                        help=f"Root directory to scan for projects (default: {DEFAULT_PROJECTS_ROOT})")
    parser.add_argument("-d", "--down", action="store_true",
                        help="Use 'env down/up' instead of 'env stop/start' (removes containers)")
    args = parser.parse_args()
    
    # Initialize Warden manager
    warden = WardenManager(args.projects_root, use_down=args.down)
    
    # Get projects
    projects = warden.get_projects()
    
    if not projects:
        print("No Warden projects found.")
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
            # SSH into running environment
            if running_env:
                for proj in projects:
                    if proj.get('WARDEN_ENV_NAME') == running_env:
                        clear_screen()
                        print(f"🔌 Connecting to {running_env}...")
                        print(f"\033[90m  $ {warden.get_shell_command(proj['path'])}\033[0m")
                        print("\nType 'exit' to return to the menu.\n")
                        warden.open_shell(proj['path'])
                        break
            else:
                print("\n⚠️  No environment is running. Start one first.")
                wait_for_enter()
        elif key == 'help':
            print("\n" + "─" * 50)
            print("  📖 AVAILABLE COMMANDS")
            print("─" * 50)
            print("  0-9      Select environment by number")
            print("  ssh      Connect to running environment")
            print("  start    Start selected environment")
            print("  up/u     Move selection up")
            print("  down/d   Move selection down")
            print("  quit/q   Exit the application")
            print("  help/?   Show this help")
            print("")
            print("  📋 WARDEN COMMANDS (run in running env)")
            print("  log / logs     Follow all logs")
            print("  log nginx      Follow nginx logs")
            print("  ls             List running containers")
            print("  run <cmd>      Run one-off command")
            print("  port <svc>     Show port bindings")
            print("─" * 50)
            wait_for_enter()
        elif isinstance(key, tuple) and key[0] == 'warden_cmd':
            # Run warden command in the running environment (interactive like ssh)
            if running_env:
                for proj in projects:
                    if proj.get('WARDEN_ENV_NAME') == running_env:
                        cmd = key[1]
                        # Normalize command
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
                        full_cmd = f"cd {proj['path']} && {cmd}"
                        clear_screen()
                        print(f"📋 Running command...")
                        print(f"\033[90m  $ {full_cmd}\033[0m")
                        print("\nPress Ctrl+C to stop.\n")
                        warden.run_cmd_live(full_cmd)
                        # If command finished (not interrupted), wait for enter
                        print("\n")
                        wait_for_enter()
                        break
            else:
                print("\n⚠️  No environment is running. Start one first.")
                wait_for_enter()
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
            if selected_idx == len(projects):
                clear_screen()
                print("Goodbye! 👋")
                break
            
            selected = projects[selected_idx]
            selected_name = selected.get('WARDEN_ENV_NAME')
            
            if selected_name == running_env:
                print("\n✓ This environment is already running!")
                wait_for_enter()
            else:
                # Stop current environment if running
                stop_success = True
                if running_env:
                    for proj in projects:
                        if proj.get('WARDEN_ENV_NAME') == running_env:
                            stop_success = stop_environment_ui(warden, running_env, proj['path'])
                            break
                
                if not stop_success:
                    print(f"\n❌ Failed to stop {running_env}")
                    wait_for_enter()
                    continue
                
                # Start selected environment
                start_success = start_environment_ui(warden, selected_name, selected['path'])
                
                if start_success:
                    running_env = selected_name
                    full_url = warden.get_project_url(selected)
                    print(f"\n✓ {selected_name} is now running!")
                    print(f"  → https://{full_url}/")
                else:
                    print(f"\n❌ Failed to start {selected_name}")
                    running_env = warden.get_running_environment()
                
                wait_for_enter()


if __name__ == "__main__":
    main()
