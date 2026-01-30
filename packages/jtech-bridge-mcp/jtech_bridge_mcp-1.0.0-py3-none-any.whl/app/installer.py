import os
import sys
import shutil
import subprocess
import platform
import distro
from pathlib import Path

BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
RED = '\033[0;31m'
NC = '\033[0m'

def is_ubuntu() -> bool:
    """Check if the current OS is Ubuntu."""
    try:
        if platform.system() != "Linux":
            return False
        return distro.id() == "ubuntu"
    except Exception:
        return False

def install_service() -> None:
    """
    Install the systemd service for the application.
    Must be run with sudo/root privileges.
    """
    # 1. Check Root
    if os.geteuid() != 0:
        print(f"{RED}Error: This command must be run as root (sudo).{NC}")
        print(f"Try: sudo {sys.argv[0]} --install-service")
        sys.exit(1)

    # 2. Check OS
    if not is_ubuntu():
        print(f"{RED}Error: Automatic service installation is only supported on Ubuntu.{NC}")
        print("For other distributions, please configure systemd manually.")
        sys.exit(1)

    print(f"{BLUE}🚀 Starting Jtech Bridge Service Installation...{NC}")

    # 3. Determine Paths
    # We want to use the current python executable or the 'jtech-bridge' command location
    # If installed via pip globally, sys.executable might be /usr/bin/python3
    # We want to find where 'jtech-bridge' is.
    
    # Check if we are running from the installed command
    cmd_path = shutil.which("jtech-bridge")
    if not cmd_path:
        # Fallback if running via python -m app
        cmd_path = sys.executable + " -m app.server"
        print(f"{BLUE}ℹ️  Command 'jtech-bridge' not found in PATH, using: {cmd_path}{NC}")
    
    # We need to know which user to run as. 
    # Since we are running as root (sudo), we shouldn't run the service as root.
    # We will use the SUDO_USER environment variable if available (user who invoked sudo)
    real_user = os.environ.get('SUDO_USER') or os.environ.get('USER')
    
    if not real_user or real_user == 'root':
        print(f"{RED}⚠️  Warning: Service will run as root. Ideally it should run as a standard user.{NC}")
        # Try to find a better user? No, stick to what we have or ask.
        # For automation, we will proceed but warn.
    
    # Resolve %h (Home) for the user
    import pwd
    try:
        pw_record = pwd.getpwnam(real_user)
        user_home = pw_record.pw_dir
        uid = pw_record.pw_uid
        gid = pw_record.pw_gid
    except Exception:
         user_home = "/root"

    print(f"{BLUE}ℹ️  Installing service for user: {real_user} (Home: {user_home}){NC}")

    # 4. Generate Service File
    # We need to preserve environment variables, specifically for Mongo connection if it's not default
    # But for a basic install, we assume defaults or a config file in /etc/jtech-bridge or ~/.jtech-bridge
    
    # Constructing the service file content
    service_content = f"""[Unit]
Description=Jtech Bridge MCP Server
Documentation=https://github.com/angelovicentefilho/mcp-ide-bridge
After=network.target mongodb.service

[Service]
Type=simple
User={real_user}
Group={real_user}
WorkingDirectory={user_home}
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart={cmd_path}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

    service_path = "/etc/systemd/system/jtech-bridge-mcp.service"
    
    try:
        with open(service_path, "w") as f:
            f.write(service_content)
        print(f"{GREEN}✅ Service file created at {service_path}{NC}")
    except Exception as e:
        print(f"{RED}❌ Failed to write service file: {e}{NC}")
        sys.exit(1)

    # 5. Install MongoDB (Docker)
    install_mongodb(real_user)

    # 6. Enable and Start
    print(f"{BLUE}⚙️  Reloading systemd...{NC}")
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    
    print(f"{BLUE}⚙️  Enabling service...{NC}")
    subprocess.run(["systemctl", "enable", "jtech-bridge-mcp"], check=True)
    
    print(f"{BLUE}🚀 Starting service...{NC}")
    try:
        subprocess.run(["systemctl", "start", "jtech-bridge-mcp"], check=True)
        print(f"{GREEN}✅ Service started successfully!{NC}")
    except subprocess.CalledProcessError:
        print(f"{RED}⚠️  Failed to start service immediately. Check logs with: journalctl -u jtech-bridge-mcp{NC}")

    print(f"\n{GREEN}Installation Complete!{NC}")
    print(f"Check status: {BLUE}systemctl status jtech-bridge-mcp{NC}")


def install_mongodb(user: str) -> None:
    """
    Check if Docker is installed and run a MongoDB container.
    """
    print(f"{BLUE}🐳 Checking for MongoDB Docker...{NC}")

    # Check for Docker
    if int(subprocess.call(["sudo", "-u", user, "docker", "--version"])) != 0:
        print(f"{RED}⚠️  Docker not found or user '{user}' not in docker group.{NC}")
        print("Skipping MongoDB installation. Please install Docker or MongoDB manually.")
        return

    # Check if container exists
    check_container = subprocess.run(
        ["sudo", "-u", user, "docker", "ps", "-a", "--filter", "name=mcp-mongo", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )

    if "mcp-mongo" in check_container.stdout:
        print(f"{GREEN}✅ MongoDB container 'mcp-mongo' already exists.{NC}")
        # Ensure it's running
        subprocess.run(["sudo", "-u", user, "docker", "start", "mcp-mongo"], check=False)
    else:
        print(f"{BLUE}🚀 Starting new MongoDB container...{NC}")
        try:
            # Pull and Run
            subprocess.run(
                ["sudo", "-u", user, "docker", "run", "-d", 
                 "--name", "mcp-mongo", 
                 "-p", "27017:27017", 
                 "--restart", "unless-stopped", 
                 "mongo:latest"],
                check=True
            )
            print(f"{GREEN}✅ MongoDB container started!{NC}")
        except subprocess.CalledProcessError:
            print(f"{RED}❌ Failed to start MongoDB container.{NC}")


