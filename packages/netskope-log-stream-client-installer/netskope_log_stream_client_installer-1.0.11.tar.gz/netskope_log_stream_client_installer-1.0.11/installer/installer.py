import platform
import shutil
import subprocess
import logging
import os
import sys
import re
from pathlib import Path
import time
import urllib.parse
import base64
import json

try:
    from installer.version_checker import check_for_updates
except ImportError:
    # Fallback if version_checker is not available
    def check_for_updates(auto_upgrade=False, package_name=None):
        return False

try:
    from installer import __version__
except ImportError:
    __version__ = "unknown"

# Constants
VERSION = "I.2025.11.1"
SUPPORTED_OS = ["debian", "ubuntu", "raspbian", "rhel", "centos", "rocky", "almalinux", "sles"]
SUPPORTED_ARCHITECTURE = ["x86_64", "arm64", "AMD64", "64bit"]
DOCKER_IMAGE = "netskope/nsstreamingclient:stable"
CONTAINER_NAME = "nsstreamingclient"
WATCHER_IMAGE = "netskope/nswatcher:stable"
WATCHER_CONTAINER = "ns-watcher"
LOG_DRIVER_OPTIONS = [
    "--log-driver=json-file",
    "--log-opt", "max-size=10m",
    "--log-opt", "max-file=10",
    "--log-opt", "compress=true",
    "--network", "host"
]
CONTAINER_COMMAND = "sh -c 'exec > /var/log/container.log 2>&1 && tail -f /dev/null'"
CLIENT_KEY = ""

# Proxy Configuration Flags
# Container proxy configuration - HTTPS recommended for security
CONTAINER_PROXY_HTTPS = True

# Configure logging
logging.basicConfig(level=logging.INFO, filename="container_init.log", filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Checking Supported OS.
def check_os() -> bool:
    """Check if the operating system is supported."""
    try:
        print("\n>>> Checking if operating system is supported...")
        with open('/etc/os-release') as f:
            for line in f:
                if line.startswith('ID='):
                    os_name = line.split('=')[1].strip('"\n')
                    break

        if os_name not in SUPPORTED_OS:
            print(f"ERROR: Operating system ({os_name}) is not supported.")
            print(f"Supported operating systems: {', '.join(SUPPORTED_OS)}")
            logger.error(f"Unsupported OS. Supported OS: {', '.join(SUPPORTED_OS)}")
            return False
        print(f"SUCCESS: Check for operating system passed.")
        logger.info(f"Check for operating system passed..")
        return True
    except Exception as e:
        print(f"ERROR: Couldn't check Operating system: {e}")
        logger.error(f"Couldn't check Operating system: {e}")
        return False

# Checking Supported Architecture.
def check_architecture() -> bool:
    """Check if the architecture is supported."""
    try:
        print("\n>>> Checking if hardware architecture is supported...")
        arch = platform.machine()
        if arch == "AMD64":
            arch = "x86_64"
        elif platform.architecture()[0] == "64bit":
            arch = "64bit"

        if arch not in SUPPORTED_ARCHITECTURE:
            print(f"ERROR: Architecture ({arch}) is not supported.")
            print(f"Supported architectures: {', '.join(SUPPORTED_ARCHITECTURE)}")
            logger.error(f"Unsupported architecture. Supported architectures: {', '.join(SUPPORTED_ARCHITECTURE)}")
            return False
        print(f"SUCCESS: Check for Architecture passed.")
        logger.info(f"Check for Architecture passed.")
        return True
    except Exception as e:
        print(f"ERROR: Couldn't check hardware architecture: {e}")
        logger.error(f"Couldn't check hardware architecture: {e}")
        return False

# Checking Docker is running.
def is_docker_running() -> bool:
    """Check if the Docker daemon is running."""
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("SUCCESS: Docker daemon is running.")
        logger.info("Docker daemon is running.")
        return True
    except subprocess.CalledProcessError:
        print("ERROR: Docker daemon is not running.")
        print("Please start Docker and try again.")
        logger.error("Docker daemon is not running.")
        return False
    except FileNotFoundError:
        print("ERROR: Docker is not installed.")
        logger.error("Docker is not installed.")
        return False

# Checking Docker is installed.
def check_docker() -> bool:
    """Check if Docker is installed and running."""
    try:
        print("\n>>> Checking if Docker is installed and running...")
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("SUCCESS: Docker is installed.")
        logger.info("Docker is installed.")
        return is_docker_running()
    except FileNotFoundError:
        print("ERROR: Docker is not installed.")
        print("Please install Docker before continuing.")
        logger.info("Docker is not installed.")
        return False

# Pull Docker Image
def pull_image() -> bool:
    """Pull the Docker image if it doesn't exist locally."""
    try:
        print(f"\n>>> Pulling Docker image: {DOCKER_IMAGE}")
        print("The process might take a moment...")
        

        # Use default environment - proxy should be configured at Docker daemon level
        subprocess.run(["docker", "pull", DOCKER_IMAGE], check=True)
        print("SUCCESS: Docker image pulled successfully!")
        logger.info("Image pulled successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to pull Docker image. Details: {e}")
        logger.error(f"Error pulling Docker image: {e}")
        return False

# Initialize log file with proper ownership
def initialize_log_file(directory: str, operation_type: str) -> bool:
    """
    Create or recreate the installer log file with proper ownership.
    Args:
        directory: The base directory for the installation
        operation_type: The type of operation (install, reinstall, silent)
    Returns:
        bool: True if log file was successfully initialized, False otherwise
    """
    try:
        # Determine the correct logs directory path based on operation type
        if operation_type == "silent":
            logs_directory = os.path.join(os.path.expanduser(directory), "container_files", "logs")
        else:
            homedirectory = os.path.expanduser(os.path.join(directory, "container_files"))
            logs_directory = os.path.join(homedirectory, "logs")

        # Create logs directory if it doesn't exist
        os.makedirs(logs_directory, exist_ok=True)
        log_file_path = os.path.join(logs_directory, "installerInformation.log")

        # Delete existing log file if it exists, then create a new empty one
        if os.path.exists(log_file_path):
            try:
                os.remove(log_file_path)
                print(f"INFO: Removed existing installer information log file.")
                logger.info(f"Removed existing installer information log file: {log_file_path}")
            except OSError as e:
                print(f"WARNING: Could not remove existing installer information log file: {e}")
                logger.warning(f"Could not remove existing installer information log file {log_file_path}: {e}")

        # Create empty log file to ensure we own it
        with open(log_file_path, 'w') as f:
            f.write("")  # Create empty file

        print(f"INFO: Initialized installer information log file.")
        logger.info(f"Created/reset log file: {log_file_path}")
        return True

    except Exception as e:
        print(f"WARNING: Could not initialize installer information log file: {e}")
        logger.warning(f"Could not initialize installer information log file during {operation_type}: {e}")
        return False

# Proxy Configuration Functions
def check_proxy_setup():
    """Check if user needs proxy setup and get container proxy configuration.
    Returns: (container_proxy, user_wants_proxy)
    """
    try:
        print("\n>>> Configuring proxy settings...")
        logger.info("Starting proxy configuration")

        # Ask if proxy is already setup (default to 'no')
        try:
            proxy_setup_response = input("\nDo you need proxy setup for Streaming Client? [y/n] (default: n): ").strip().lower()
            # If empty input, default to 'no'
            if not proxy_setup_response:
                proxy_setup_response = 'n'
        except (EOFError, KeyboardInterrupt):
            print("\nOperation canceled by user.")
            sys.exit(1)

        if proxy_setup_response in ("n", "no"):
            print("INFO: No proxy configuration - proceeding without proxy")
            logger.info("User chose no proxy configuration.")
            return None, False
        elif proxy_setup_response in ("y", "yes"):
            print("INFO: Configuring proxy for containers")
            logger.info("User needs proxy configuration")

            # Get container proxy configuration
            container_status, container_proxy = get_container_proxy()

            # Check if container proxy configuration failed
            if container_status is False:
                print("ERROR: Container proxy configuration failed. Please check the URL format and try again.")
                logger.error("Container proxy configuration failed due to invalid URL")
                return False, False  # Return False to indicate error

            return container_proxy, True
        else:
            print("ERROR: Invalid input. Please enter 'y' or 'n'.")
            logger.error("Invalid proxy setup response.")
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: Failed to configure proxy: {e}")
        logger.error(f"Failed to configure proxy: {e}")
        return False, False  # Return False to indicate error

def get_container_proxy():
    """Get proxy configuration for containers."""
    try:
        print("\n--- Streaming Client Container Proxy Configuration ---")
        print("This proxy will be used by the running containers for their operations.")

        # Determine proxy type based on configuration flag
        proxy_type = "HTTPS" if CONTAINER_PROXY_HTTPS else "HTTP"
        http_example_url = "http://proxy.company.com:8080"
        https_example_url = "https://proxy.company.com:8080"
        try:
            proxy_url = input(f"{proxy_type} Proxy URL (e.g., {http_example_url} or {https_example_url}): ").strip()

            # Clean up input - remove variable name prefixes if user entered them
            if proxy_url.startswith('HTTP_PROXY=') or proxy_url.startswith('http_proxy=') or proxy_url.startswith('HTTPS_PROXY=') or proxy_url.startswith('https_proxy='):
                proxy_url = proxy_url.split('=', 1)[1]

        except (EOFError, KeyboardInterrupt):
            print("\nOperation canceled by user.")
            sys.exit(1)

        # Check if proxy URL is empty
        if not proxy_url:
            print("ERROR: Proxy URL is required.")
            logger.error("Proxy URL is required.")
            sys.exit(1)

        # Validate URL format
        if not validate_proxy_url(proxy_url):
            print("ERROR: Invalid proxy URL format")
            print(f"Expected format: {http_example_url} or {https_example_url}")
            logger.error("Invalid container proxy URL provided")
            return False, {}  # Return False on error

        if proxy_url:
            if CONTAINER_PROXY_HTTPS:
                result = {'HTTPS_PROXY': proxy_url}
                print(f"INFO: Container HTTPS proxy configured: {proxy_url}")
                logger.info(f"Container HTTPS proxy configured: {proxy_url}")
            else:
                result = {'HTTP_PROXY': proxy_url}
                print(f"INFO: Container HTTP proxy configured: {proxy_url}")
                logger.info(f"Container HTTP proxy configured: {proxy_url}")
            return True, result
        else:
            print("INFO: No container proxy configured")
            logger.info("No container proxy configured")
            return None, {}

    except Exception as e:
        print(f"ERROR: Failed to get container proxy: {e}")
        logger.error(f"Failed to get container proxy: {e}")
        return False, {}

def validate_proxy_url(proxy_url):
    """Validate proxy URL format and basic structure."""
    try:
        if not proxy_url:
            return False

        parsed = urllib.parse.urlparse(proxy_url)

        # Check if scheme is valid
        if parsed.scheme not in ['http', 'https']:
            return False

        # Check if netloc (hostname:port) exists
        if not parsed.netloc:
            return False

        # Additional validation: check if hostname exists
        if ':' in parsed.netloc:
            hostname, port = parsed.netloc.split(':', 1)
            try:
                port_int = int(port)
                if port_int < 1 or port_int > 65535:
                    return False
            except ValueError:
                return False
        else:
            hostname = parsed.netloc

        # Basic hostname validation (not empty)
        if not hostname:
            return False

        return True

    except Exception:
        return False

def create_proxy_env_file(envdirectory: str, container_proxy: dict) -> bool:
    """Create proxy.env file with proxy configurations."""
    try:
        proxy_file_path = os.path.join(envdirectory, "proxy.env")
        
         # Always clear existing proxy.env file first to ensure clean state
        if os.path.exists(proxy_file_path):
            try:
                os.remove(proxy_file_path)
                logger.info("Cleared existing proxy.env file before writing new configuration")
            except Exception as e:
                logger.warning(f"Could not remove existing proxy.env file: {e}")
        
        # Only create the file if there are proxy configurations
        if container_proxy:
            print("INFO: Creating proxy configuration file...")
            with open(proxy_file_path, "w") as f:
                f.write("# Proxy Configuration File\n")
                f.write("# This file contains proxy settings for the application\n\n")
                
                # Write container proxy configuration
                f.write("# Container Proxy Settings\n")
                if container_proxy.get('HTTP_PROXY'):
                    f.write(f"CONTAINER_HTTP_PROXY={container_proxy['HTTP_PROXY']}\n")
                    logger.info(f"Saved container HTTP proxy to proxy.env: {container_proxy['HTTP_PROXY']}")
                if container_proxy.get('HTTPS_PROXY'):
                    f.write(f"CONTAINER_HTTPS_PROXY={container_proxy['HTTPS_PROXY']}\n")
                    logger.info(f"Saved container HTTPS proxy to proxy.env: {container_proxy['HTTPS_PROXY']}")
                        
            print(f"SUCCESS: Proxy configuration saved to proxy.env")
            logger.info(f"proxy.env created in {envdirectory}")
            return True
        else:
            print("INFO: No proxy configuration - proxy.env file not created")
            logger.info("No proxy configuration provided - skipping proxy.env creation")
            return True
            
    except Exception as e:
        print(f"ERROR: Failed to create proxy.env file: {e}")
        logger.error(f"Failed to create proxy.env file: {e}")
        return False

def validate_client_key(client_key: str) -> tuple[bool, str]:
    """
    Validate that client key contains CONNECTION_KEY and CONTAINER_KEY.
    Args:
        client_key: The base64 encoded client key string
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    try:
        if not client_key or not client_key.strip():
            return False, "Invalid client key"

        # Decode from base64
        decoded_bytes = base64.b64decode(client_key.strip())
        decoded_str = decoded_bytes.decode('utf-8')

        # Parse as JSON
        client_data = json.loads(decoded_str)

        if not isinstance(client_data, dict):
            return False, "Invalid client key"

        # Check for required fields
        if 'CONNECTION_KEY' not in client_data:
            return False, "Invalid client key"

        if 'CONTAINER_KEY' not in client_data:
            return False, "Invalid client key"

        if not client_data['CONNECTION_KEY']:
            return False, "Invalid client key"

        if not client_data['CONTAINER_KEY']:
            return False, "Invalid client key"

        return True, ""

    except Exception as e:
        return False, "Invalid client key"

# Run docker Container
def run_container(client_key: str, directory: str, option: str, container_proxy=None, user_wants_proxy=False) -> bool:
    """Run the Docker container."""
    try:
        print("\n>>> Setting up and starting the container...")
        directory = os.path.expanduser(directory)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"INFO: Created installation directory: {directory}")
            logger.info(f"Installation directory created: {directory}")
        else:
            print(f"INFO: Using existing installation directory: {directory}")
            logger.info(f"Installation directory already exists: {directory}")

        result = subprocess.run(["docker", "ps", "-a", "-q", "-f", f"name={CONTAINER_NAME}"], capture_output=True, text=True)
        container_exists = bool(result.stdout.strip())

        if option == "reinstall":
            if container_exists:
                print("INFO: Removing existing container...")
                subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stderr=subprocess.DEVNULL)

            # Initialize log file with proper ownership for reinstall
            initialize_log_file(directory, "reinstall")

        if not pull_image():
            return False

        homedirectory = os.path.expanduser(os.path.join(directory, "container_files"))
        envdirectory = os.path.expanduser(os.path.join(homedirectory, "cfg"))

        if option == "install":
            print("INFO: Configuring container volumes and environment variables...")
            os.makedirs(homedirectory, exist_ok=True)
            os.makedirs(envdirectory, exist_ok=True)

            # Initialize log file with proper ownership for install
            initialize_log_file(directory, "install")
            
            # Create main container configuration file (without proxy settings)
            env_file_path = os.path.join(envdirectory, "container_config.env")
            with open(env_file_path, "w") as f:
                f.write(f"CLIENT_KEY={client_key}\n")
                f.write(f"DIRECTORY={directory}\n")
            print(f"INFO: Container configuration file created successfully")
            logger.info(f"container_config.env created in {envdirectory}")
            
            # Create separate proxy configuration file only if user chose proxy setup
            if user_wants_proxy:
                print("INFO: Creating proxy configuration file...")
                create_proxy_env_file(envdirectory, container_proxy)
            else:
                # During install, remove existing proxy.env file if user chose no proxy
                proxy_file_path = os.path.join(envdirectory, "proxy.env")
                if os.path.exists(proxy_file_path):
                    try:
                        os.remove(proxy_file_path)
                        print("INFO: Removed existing proxy configuration file (no proxy selected)")
                        logger.info("Removed existing proxy.env file - user chose no proxy")
                    except Exception as e:
                        print(f"WARNING: Could not remove existing proxy configuration file: {e}")
                        logger.warning(f"Could not remove existing proxy.env file: {e}")
                else:
                    logger.info("User declined proxy setup - no proxy.env file to remove")

        print("INFO: Starting container...")
        # Prepare docker run command
        docker_cmd = [
            "docker", "run", "-d", "--name", CONTAINER_NAME, "--restart=always",
            "-v", f"{homedirectory}:/opt/ns",
            "-e", f"DIRECTORY={directory}"
        ]

        # Add proxy environment variables if configured
        if container_proxy:
            http_proxy = container_proxy.get('HTTP_PROXY')
            https_proxy = container_proxy.get('HTTPS_PROXY')
        
            if http_proxy:
                docker_cmd.extend(["-e", f"HTTP_PROXY={http_proxy}"])
            if https_proxy:
                docker_cmd.extend(["-e", f"HTTPS_PROXY={https_proxy}"])
        
            # Print consolidated proxy message
            if http_proxy and https_proxy and http_proxy == https_proxy:
                print(f"INFO: Adding proxy to container for both HTTP and HTTPS: {http_proxy}")
            else:
                if http_proxy:
                    print(f"INFO: Adding HTTP proxy to container: {http_proxy}")
                if https_proxy:
                    print(f"INFO: Adding HTTPS proxy to container: {https_proxy}")

        # Add log driver options and image
        docker_cmd.extend(LOG_DRIVER_OPTIONS)
        docker_cmd.append(DOCKER_IMAGE)
        docker_cmd.extend(CONTAINER_COMMAND)

        subprocess.run(docker_cmd, check=True)

        print(f"SUCCESS: Container '{CONTAINER_NAME}' started successfully!")
        print(f"Container files and Log files will be stored in: {directory}")
        logger.info("Docker container started successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to start container. Details: {e}")
        logger.error(f"Error while running the container: {e}")
        return False
# Run watcher container
def run_watcher_container(directory: str, day_of_week: str, time_of_day: str, container_proxy=None):
    """
    Start the ns-watcher container to monitor the main container.

    Args:
        directory: Installation directory path
        day_of_week: Day for scheduled updates
        time_of_day: Time for scheduled updates
        container_proxy: Container proxy config (passed to container)
    """
    try:
        logger.info("Setting up watcher container...")
        print("\n>>> Setting up watcher container to monitor the main container...")

        directory = os.path.expanduser(directory)
        existing = subprocess.getoutput(f"docker ps -a --filter 'name={WATCHER_CONTAINER}' --format '{{{{.Names}}}}'")
        if WATCHER_CONTAINER in existing:
            logger.info("Watcher container already exists. Restarting it...")
            print("INFO: Watcher container already exists. Restarting it...")
            subprocess.call(["docker", "rm", "-f", WATCHER_CONTAINER])

        print("INFO: Pulling watcher image...")
        
        # Use Docker daemon proxy configuration
        subprocess.call(["docker", "pull", WATCHER_IMAGE])

        print("INFO: Starting watcher container...")
        # Prepare watcher container command
        watcher_cmd = [
            "docker", "run", "-d", "--restart", "always", "--name", WATCHER_CONTAINER,
            "-e", f"UPDATE_DAY={day_of_week}",
            "-e", f"UPDATE_TIME={time_of_day}",
            "-e", f"DIRECTORY={directory}",
            "--network", "host",
            "-v", f"{directory}:/mnt",
            "-v", "/var/run/docker.sock:/var/run/docker.sock"
        ]

        # Add container proxy environment variables to watcher container if configured
        if container_proxy:
            container_http_proxy = container_proxy.get('HTTP_PROXY')
            container_https_proxy = container_proxy.get('HTTPS_PROXY')

            if container_http_proxy:
                watcher_cmd.extend(["-e", f"CONTAINER_HTTP_PROXY={container_http_proxy}"])
                print(f"INFO: Adding container HTTP proxy to watcher container: {container_http_proxy}")
                logger.info(f"Adding container HTTP proxy to watcher container: {container_http_proxy}")
            if container_https_proxy:
                watcher_cmd.extend(["-e", f"CONTAINER_HTTPS_PROXY={container_https_proxy}"])
                print(f"INFO: Adding container HTTPS proxy to watcher container: {container_https_proxy}")
                logger.info(f"Adding container HTTPS proxy to watcher container: {container_https_proxy}")
        else:
            logger.info("No proxy configuration for watcher container")

        watcher_cmd.append(WATCHER_IMAGE)
        subprocess.call(watcher_cmd)

        print("SUCCESS: Watcher container started successfully!")
        logger.info("Watcher container started.")
    except subprocess.SubprocessError as e:
        print(f"ERROR: Failed to start watcher container: {e}")
        logger.error(f"Error while starting watcher container: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error in watcher container setup: {e}")
        logger.error(f"Unexpected error in watcher container setup: {e}")

def get_client_key_from_args_for_silent_mode():
    """Extract client key from command line arguments for silent mode."""

    try:
        silent_index = sys.argv.index("--silent")
        # Look for -k flag after --silent
        for i in range(silent_index + 1, len(sys.argv)):
            if sys.argv[i] == "-k" and i + 1 < len(sys.argv):
                key = sys.argv[i + 1]
                if not key.startswith("-"):
                    return key
                break
    except ValueError:
        pass

    return None



def get_client_key_from_args():
    """Extract client key from command line arguments for install mode."""

    # Look for -k flag in the arguments
    for i, arg in enumerate(sys.argv):
        if arg == "-k" and i + 1 < len(sys.argv):
            key = sys.argv[i + 1]
            if not key.startswith("-"):
                return key

    return None

def validate_client_key(client_key: str) -> tuple[bool, str]:
    """
    Validate that client key contains CONNECTION_KEY and CONTAINER_KEY.
    Args:
        client_key: The base64 encoded client key string
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    try:
        if not client_key or not client_key.strip():
            return False, "Invalid client key"

        # Decode from base64
        decoded_bytes = base64.b64decode(client_key.strip())
        decoded_str = decoded_bytes.decode('utf-8')

        # Parse as JSON
        client_data = json.loads(decoded_str)

        if not isinstance(client_data, dict):
            return False, "Invalid client key"

        # Check for required fields
        if 'CONNECTION_KEY' not in client_data:
            return False, "Invalid client key"

        if 'CONTAINER_KEY' not in client_data:
            return False, "Invalid client key"

        if not client_data['CONNECTION_KEY']:
            return False, "Invalid client key"

        if not client_data['CONTAINER_KEY']:
            return False, "Invalid client key"

        return True, ""

    except Exception as e:
        return False, "Invalid client key"

def wait_for_config_download(log_file_path: str, timeout: int = 60, poll_interval: int = 3) -> tuple[bool, bool]:
    """
    Wait up to `timeout` seconds for all specified success messages to appear in the log file.
    The order in which success messages appear does not matter for completion.
    Prints real-time progress to the CLI as each unique success message is found.
    Returns True if all success messages are found, False if timeout occurs or a failure is detected.
    """
    success_messages = [
        "PROGRESS: Connected with syslog.",
        "PROGRESS: Syslog details verified.",
        "PROGRESS: Configuration verified.",
        "Successfully downloaded stream configuration",
        "GRPC connection established successfully"
    ]

    alternative_status_messages = [
        "Client is not enabled",
        "No destinations found or destination is disabled",
        "No active targets found"
    ]

    config_download_message = "Successfully downloaded stream configuration"

    failure_messages = [
        "Failed to connect to configuration server",
        "Failed to connect to syslog server",
        "Failed to test syslog connection",
        "Failed to test syslog details",
        "Failed to verify configuration",
        "Failed to download configuration",
        "Destination is disabled or no targets to connect",
        "Failed to fetch stream configuration, retrying ...",
        "Failed to connect to Netskope:",
        "Failed to fetch stream configuration, status code:",
        "Failed to read client key",
        "CLIENT_KEY not found in either env file",
        "Failed to load static configuration or token.",
        "Error establishing gRPC connection"
    ]

    logger.info(f"Starting configuration wait for {log_file_path} with timeout {timeout}s")
    print(f">>> Waiting for configuration to complete (max {timeout} seconds)...")

    if not os.path.isabs(log_file_path) or ".." in log_file_path:
        logger.error(f"Invalid log file path: {log_file_path}")
        print(f"ERROR: Invalid log file path: {log_file_path}")
        return False, False

    start_time = time.time()
    saw_failure_during_attempt = False
    found_alternative_status = False
    found_config_download = False
    found_success_messages = set()
    shown_error_messages = set()  # Track which error messages we've already shown
    initial_success_time = None
    grace_period = 15
    while time.time() - start_time < timeout:
        if os.path.isfile(log_file_path):
            try:
                with open(log_file_path, "r", encoding="utf-8", errors='ignore') as f:
                    # Read entire file since we create a fresh log file for each operation
                    content = f.read()

                    lines = content.splitlines()
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue

                        # Process all log lines since we create a fresh log file for each operation

                        # Check for failure messages and only print each unique one once per phase
                        for failure_msg in failure_messages:
                            if failure_msg in line and failure_msg not in shown_error_messages:
                                shown_error_messages.add(failure_msg)
                                saw_failure_during_attempt = True
                                logger.info(f"Error detected: {failure_msg}")
                                print(f"STATUS: {line}")
                                if initial_success_time is not None:
                                    logger.warning("Failure detected after initial success - resetting success state")
                                    print("WARNING: Configuration issue detected - monitoring continues...")
                                    initial_success_time = None
                                    found_alternative_status = False
                                    found_config_download = False
                                    found_success_messages.clear()
                                    shown_error_messages.clear()  # Reset shown errors when resetting state
                                break  # Only process first matching error per line

                        for alt_msg in alternative_status_messages:
                            if alt_msg in line and not found_alternative_status:
                                found_alternative_status = True
                                logger.info(f"Found alternative status message: {alt_msg}")
                                print(f"PROGRESS: {alt_msg}")

                        if config_download_message in line and not found_config_download:
                            found_config_download = True
                            logger.info(f"Found configuration download message: {config_download_message}")
                            print(f"Successfully downloaded stream configuration")

                        success_condition_met = False
                        if found_alternative_status and found_config_download:
                            success_condition_met = True
                        elif len(found_success_messages) == len(success_messages):
                            success_condition_met = True
                        elif found_alternative_status:
                            success_condition_met = True

                        if success_condition_met and initial_success_time is None:
                            initial_success_time = time.time()
                            shown_error_messages.clear()
                            logger.info("Initial success conditions met - starting grace period monitoring")
                            if found_alternative_status and found_config_download:
                                print(f"INFO: Installation successful - Client configured with valid status")
                            elif found_alternative_status:
                                print(f"INFO: Installation successful. Waiting for configuration download...")
                            else:
                                print(f"INFO: Installation successful - All connectivity tests passed")
                            print(f"INFO: Monitoring for {grace_period}s ...")

                        for main_msg in success_messages:
                            if main_msg in line and main_msg not in found_success_messages:
                                found_success_messages.add(main_msg)
                                logger.info(f"Installation progress: {main_msg}")
                                if main_msg != config_download_message:
                                    if main_msg.startswith("PROGRESS:"):
                                        print(main_msg)
                                    else:
                                        print(f"{main_msg}")

                    # Check if we have all success messages - start grace period
                    if len(found_success_messages) == len(success_messages) and initial_success_time is None:
                        initial_success_time = time.time()
                        logger.info("All success messages found - starting 15s connectivity check")
                        print("INFO: Installation successful - All connectivity tests passed")
                        print(f"INFO: Monitoring for {grace_period}s ...")

                    if initial_success_time is not None and time.time() - initial_success_time >= grace_period:
                        final_success = False
                        if found_alternative_status and found_config_download:
                            final_success = True
                            logger.info("Installation completed successfully - Client or Destination is disabled.")
                        elif len(found_success_messages) == len(success_messages):
                            final_success = True
                            logger.info("Installation completed successfully - all success messages found")
                        elif found_alternative_status:
                            final_success = True
                            logger.info("Installation completed successfully - status indicates valid configuration but Client or Destination may be disabled")

                        if final_success:
                            return True, False
                        else:
                            logger.warning("Success conditions no longer met after grace period")
                            initial_success_time = None

            except PermissionError:
                logger.error(f"Permission denied accessing log file: {log_file_path}")
                print(f"ERROR: Permission denied accessing log file: {log_file_path}")
                return False, False
            except UnicodeDecodeError:
                logger.error(f"Failed to decode log file: {log_file_path}. Try changing encoding or using errors='ignore'.")
                print(f"ERROR: Failed to decode log file: {log_file_path}")
                return False, False
            except IOError as e:
                logger.error(f"Failed to read log file: {e}")
                print(f"ERROR: Failed to read log file: {e}")
                return False, False
        else:
            logger.debug(f"Log file not found yet: {log_file_path}")
            time.sleep(1)

        time.sleep(poll_interval)

    if saw_failure_during_attempt:
        found_failures = [msg for msg in failure_messages if msg in content]
        has_grpc_error = "Error establishing gRPC connection" in content

        if has_grpc_error:
            logger.error(f"GRPC error detected in log content")

            other_failures = [msg for msg in found_failures if "Error establishing gRPC connection" not in msg]
            if other_failures:
                  print(f"ERROR: Error establishing gRPC connection")
                  print(f"ERROR: Configuration failed. Additional errors: {other_failures}")
                  return False, True
            else:
                print(f"INFO: Configuration succeeded but Error establishing gRPC connection.")
                return True, True
        else:
            logger.error(f"Configuration failed after timeout. Failures detected: {found_failures}")
            print(f"ERROR: Configuration failed. Failures detected: {found_failures}")
            return False, False
    elif initial_success_time is not None:
        logger.error("Configuration failed - success conditions were met but failures occurred during grace period")
        print("ERROR: Configuration failed - initial success was detected but subsequent failures occurred")
        return False, False
    else:
        # Check if we found any GRPC-related messages (success or error)
        grpc_success_found = "GRPC connection established successfully" in content
        grpc_error_found = "Error establishing gRPC connection" in content

        if not grpc_success_found and not grpc_error_found:
            logger.warning(f"Timeout reached. No GRPC logs found in the log file.")
            print(f"ERROR: Not able to find GRPC logs. Please check the log file manually.")
            return False, False
        else:
            logger.warning(f"Timeout reached. No success messages were found in the log file.")
            print(f"ERROR: Timeout reached. No success messages were found in the log file.")
            return False, False

# Run script in Silent mode
def run_silent_install():
    try:
        print("INSTALLATION (SILENT MODE)")
        print("Running in silent mode with default settings...")
        logger.info("Running in silent mode...")

        if not (check_os() and check_architecture() and check_docker()):
            print("\nERROR: System checks failed. Exiting silent mode.")
            logger.error("One or more system checks failed in silent mode.")
            return

        print("\nSUCCESS: All system checks passed!")
        logger.info("All checks passed.")

        if CLIENT_KEY!="":
            client_key=CLIENT_KEY
            # Validate the client key
            is_valid, error_msg = validate_client_key(client_key)
            if not is_valid:
                print(f"ERROR: Invalid client key - {error_msg}. Please retry with valid client key")
                logger.error(f"Client key validation failed: {error_msg}")
                return
        else:
            client_key=get_client_key_from_args_for_silent_mode()
            if client_key:
                print(f"INFO: Using client key from arguments.")
                logger.info(f"Using client key from arguments.")
            else:
                print("ERROR: No valid client key found.")
                logger.error("No valid client key found.")
                return

        # Validate the client key
        is_valid, error_msg = validate_client_key(client_key)
        if not is_valid:
            print(f"ERROR: Invalid client key - {error_msg}. Please retry with valid client key")
            logger.error(f"Client key validation failed: {error_msg}")
            return

        default_directory="~/ns"
        default_day = "Thursday"
        default_time = "23:00"
        print(f"\nINFO: Watcher container will check for updates every {default_day} at {default_time}")
        logger.info(f"Default watcher schedule: {default_day} at {default_time}")

        # In silent mode, no proxy configuration is used
        print("INFO: Silent mode - no proxy configuration will be used")
        logger.info("Silent mode - no proxy configuration")
        # Initialize log file with proper ownership for silent install
        initialize_log_file(default_directory, "silent")

        try:
            if run_container(client_key, default_directory, "install", container_proxy=None, user_wants_proxy=False):
                run_watcher_container(default_directory, default_day, default_time, container_proxy=None)
                log_path = os.path.join(os.path.expanduser(default_directory), "container_files", "logs", "installerInformation.log")
                success, is_grpc_error = wait_for_config_download(log_path)
                if success:
                    logger.info("Configuration successfully completed.")
                    print("Container started successfully.")
                    print("INSTALLATION COMPLETE")
                else:
                    if not is_grpc_error:
                        print("Configuration failed")
                    logger.error("Configuration failed in silent mode.")
                    print("Container started successfully.")
                    print("INSTALLATION COMPLETE (WITH ERROR)")
                print(f"Container files and Log files will be stored in: {default_directory}")
                logger.info("Container started successfully.")
            else:
                print("\nERROR: Failed to start container.")
                logger.error("Failed to start container.")
        except Exception as e:
            print(f"ERROR: Unexpected error during container startup: {e}")
            logger.error(f"Error while starting container in silent mode: {e}")

    except Exception as e:
        print(f"ERROR: Unhandled exception in silent install: {e}")
        logger.error(f"Unhandled error in silent install: {e}")
        print("ERROR: Silent installation failed due to an unexpected error.")

# function for Load container_config.env file
def load_env_file(env_file="container_config.env") -> dict:
    """Load environment variables from a text file and return them as a dictionary."""
    try:
        print(f"\n>>> Looking for environment file ({env_file})...")
        env_file_path = None
        directory_value = None

        try:
            container_info = subprocess.run(
                ["docker", "inspect", "--format", "{{range .Config.Env}}{{println .}}{{end}}", CONTAINER_NAME],
                capture_output=True, text=True, check=False
            )
            if container_info.returncode == 0:
                for line in container_info.stdout.strip().splitlines():
                    if line.startswith("DIRECTORY="):
                        directory_value = line.split("=", 1)[1]
                        break

                if directory_value:
                    env_file_path = os.path.join(os.path.expanduser(directory_value), "container_files", "cfg", env_file)
                    if not os.path.isfile(env_file_path):
                        env_file_path = None

        except Exception as e:
            logger.warning(f"Could not retrieve directory from running container: {e}")

        if not env_file_path:
            search_paths = [
                os.path.join(os.getcwd(), env_file),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), env_file),
                os.path.expanduser(f"~/ns/container_files/{env_file}"),
                os.path.join("/opt/ns", env_file)
            ]
            for path in search_paths:
                if os.path.isfile(path):
                    env_file_path = path
                    break

        if not env_file_path:
            print(f"ERROR: Environment file '{env_file}' not found in any known location.")
            logger.error(f"{env_file} not found in installation directory or common locations.")
            return {}

        env_vars = {}
        with open(env_file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
                    else:
                        print(f"WARNING: Ignoring invalid entry in environment file: {line}")

        print(f"SUCCESS: Loaded environment variables from: {env_file_path}")
        logger.info(f"Loaded environment variables from: {env_file_path}")
        return env_vars

    except Exception as e:
        print(f"ERROR: Failed to load environment file: {e}")
        logger.error(f"Error loading env file: {e}")
        return {}

# Removing the container and container image
def remove_container_and_image(image: str, container: str):
    try:
        print(f"\n>>> Removing container '{container}' and image '{image}'...")
        print(f"INFO: Removing container '{container}'...")
        subprocess.run(["docker", "rm", "-f", container], stderr=subprocess.DEVNULL, check=True)
        print(f"SUCCESS: Container '{container}' removed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Could not remove container '{container}'. It may not exist. Details: {e}")
        logger.warning(f"Failed to remove container '{container}': {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error while removing container: {e}")
        logger.error(f"Unexpected error while removing container: {e}")

    try:
        print(f"INFO: Removing Docker image '{image}'...")
        subprocess.run(["docker", "rmi", image], stderr=subprocess.DEVNULL, check=True)
        print(f"SUCCESS: Docker image '{image}' removed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Could not remove Docker image '{image}'. It may not exist or be in use. Details: {e}")
        logger.warning(f"Failed to remove image '{image}': {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error while removing image: {e}")
        logger.error(f"Unexpected error while removing image: {e}")

def load_proxy_env_file() -> dict:
    """Load proxy configuration from proxy.env file."""
    try:
        # Try to find proxy.env file in the same locations as container_config.env
        proxy_file_path = None
        directory_value = None
        
        # First try to get directory from running container
        try:
            container_info = subprocess.run(
                ["docker", "inspect", "--format", "{{range .Config.Env}}{{println .}}{{end}}", CONTAINER_NAME],
                capture_output=True, text=True, check=False
            )
            if container_info.returncode == 0:
                for line in container_info.stdout.strip().splitlines():
                    if line.startswith("DIRECTORY="):
                        directory_value = line.split("=", 1)[1]
                        break
                        
                if directory_value:
                    proxy_file_path = os.path.join(os.path.expanduser(directory_value), "container_files", "cfg", "proxy.env")
                    if not os.path.isfile(proxy_file_path):
                        proxy_file_path = None
        except Exception:
            pass
        
        # If not found, try common locations
        if not proxy_file_path:
            search_paths = [
                os.path.join(os.getcwd(), "proxy.env"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy.env"),
                os.path.expanduser("~/ns/container_files/cfg/proxy.env"),
                os.path.join("/opt/ns", "cfg", "proxy.env")
            ]
            for path in search_paths:
                if os.path.isfile(path):
                    proxy_file_path = path
                    break
        
        if not proxy_file_path:
            logger.info("proxy.env file not found")
            return {}
        
        # Load proxy configuration from file
        proxy_vars = {}
        with open(proxy_file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    proxy_vars[key.strip()] = value.strip()
        
        logger.info(f"Loaded proxy configuration from: {proxy_file_path}")
        return proxy_vars
        
    except Exception as e:
        logger.warning(f"Failed to load proxy.env file: {e}")
        return {}

def check_existing_proxy_config(env_data: dict) -> dict:
    """Check if proxy configuration exists in the proxy.env file or watcher container."""
    container_proxy = None
    
    # First, check for proxy configuration in dedicated proxy.env file
    proxy_config = load_proxy_env_file()
    
    if proxy_config:
        # Check for container proxy in proxy file
        container_http = proxy_config.get('CONTAINER_HTTP_PROXY')
        container_https = proxy_config.get('CONTAINER_HTTPS_PROXY')
        
        if container_http or container_https:
            container_proxy = {}
            if container_http:
                container_proxy['HTTP_PROXY'] = container_http
            if container_https:
                container_proxy['HTTPS_PROXY'] = container_https
    
    # If no proxy found in config file, check watcher container environment variables
    if not container_proxy:
        try:
            logger.info("Checking watcher container for proxy environment variables")
            
            # Get environment variables from running watcher container
            watcher_env = subprocess.run(
                ["docker", "inspect", "--format", "{{range .Config.Env}}{{println .}}{{end}}", WATCHER_CONTAINER],
                capture_output=True, text=True, check=False
            )
            
            if watcher_env.returncode == 0:
                watcher_vars = {}
                for line in watcher_env.stdout.strip().splitlines():
                    if "=" in line:
                        key, value = line.split("=", 1)
                        watcher_vars[key] = value
                
                # Check for container proxy variables in watcher container
                watcher_container_http = watcher_vars.get('CONTAINER_HTTP_PROXY')
                watcher_container_https = watcher_vars.get('CONTAINER_HTTPS_PROXY')
                
                if watcher_container_http or watcher_container_https:
                    container_proxy = {}
                    if watcher_container_http:
                        container_proxy['HTTP_PROXY'] = watcher_container_http
                        print(f"INFO: Found container HTTP proxy in watcher container: {watcher_container_http}")
                    if watcher_container_https:
                        container_proxy['HTTPS_PROXY'] = watcher_container_https
                        print(f"INFO: Found container HTTPS proxy in watcher container: {watcher_container_https}")
                
                if container_proxy:
                    logger.info("Retrieved proxy configuration from watcher container environment")
                else:
                    logger.info("No proxy configuration found in watcher container")
            else:
                logger.warning("Could not inspect watcher container for proxy configuration")
                
        except Exception as e:
            logger.warning(f"Error checking watcher container environment: {e}")
    
    return container_proxy

# Reinstall
def reinstall(option: str):
    """Reinstall with stored client_key and directory"""
    try:
        print("REINSTALLING CONTAINER")

        env_data = load_env_file()
        CLIENT_KEY = ""
        directory_value = env_data.get("DIRECTORY")
        
        # Check for existing proxy configuration
        container_proxy = check_existing_proxy_config(env_data)
        
        # Display proxy setup
        if container_proxy:
            print("INFO: Using proxy setup...")
            logger.info("Reinstall will use existing proxy configuration")
            
            proxy_types = []
            if container_proxy.get('HTTP_PROXY'):
                proxy_types.append(f"Container Proxy HTTP: {container_proxy['HTTP_PROXY']}")
            if container_proxy.get('HTTPS_PROXY'):
                proxy_types.append(f"Container Proxy HTTPS: {container_proxy['HTTPS_PROXY']}")
            print(f"  - {', '.join(proxy_types)}")
        else:
            print("INFO: No proxy configuration found - proceeding without proxy")
            logger.info("No proxy configuration found for reinstall")
        
        log_path = os.path.join(os.path.expanduser(directory_value), "container_files", "logs", "installerInformation.log")
        if not directory_value:
            print("ERROR: Cannot reinstall - missing configuration information.")
            logger.error("CLIENT_KEY or DIRECTORY missing from env.")

            container_exists = subprocess.run(
                ["docker", "inspect", CONTAINER_NAME],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            ).returncode == 0

            image_exists = subprocess.run(
                ["docker", "images", "-q", DOCKER_IMAGE],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            ).stdout.strip() != b''

            if container_exists or image_exists:
                print("Detected existing container/image but missing environment configuration.")
                print("Please remove container manually.")
                logger.warning("Partial install detected. Suggesting manual uninstall.")
            else:
                print("No running container or image found.")
                print("Please run the 'Install' option to continue.")
                logger.warning("No container/image found but config missing.")
            return
        try:
            print("INFO: Removing existing container and image...")
            remove_container_and_image(DOCKER_IMAGE, CONTAINER_NAME)

            print("INFO: Starting the container...")
            # Check if user has existing proxy configuration
            user_has_existing_proxy = bool(container_proxy)
            if run_container(CLIENT_KEY, directory_value, option, container_proxy, user_has_existing_proxy):
                success, is_grpc_error = wait_for_config_download(log_path)
                if success:
                    logger.info("Configuration successfully completed.")
                    print("REINSTALLATION COMPLETE")
                else:
                    if not is_grpc_error:
                        print("Reinstalled but configuration failed")
                    logger.error("Configuration failed during reinstall.")
                    print("REINSTALLATION COMPLETE (WITH ERROR)")
                logger.info("Successfully reinstalled the container.")
            else:
                print("ERROR: Failed to start the container during reinstall.")
        except Exception as e:
            print(f"ERROR: Failed to run the container: {e}")
            logger.error(f"Error while running container: {e}")
    except Exception as e:
        print(f"ERROR: Reinstallation failed: {e}")
        logger.error(f"An error occurred during the reinstall process: {e}")


# Uninstalling the container
def uninstall():
    """Removes the container and Docker image and scheduler"""
    try:
        print("UNINSTALLING CONTAINER")

        env_data = load_env_file()
        directory = env_data.get("DIRECTORY")
        if not directory:
            print("ERROR: Installation directory not found. Aborting uninstall.")
            logger.error("Uninstall failed: DIRECTORY not found.")
            return False
        print("INFO: Removing container and related resources...")
        remove_container_and_image(DOCKER_IMAGE, CONTAINER_NAME)
        remove_container_and_image(WATCHER_IMAGE, WATCHER_CONTAINER)

        # Delete proxy.env file specifically if it exists
        proxy_env_path = os.path.join(directory, "container_files", "cfg", "proxy.env")
        if os.path.exists(proxy_env_path):
            try:
                os.remove(proxy_env_path)
                print(f"INFO: Deleted proxy configuration file: {proxy_env_path}")
                logger.info(f"Deleted proxy.env file: {proxy_env_path}")
            except Exception as e:
                print(f"WARNING: Could not delete proxy.env file: {e}")
                logger.warning(f"Failed to delete proxy.env file: {e}")

        container_files = os.path.join(directory, "container_files")

        if os.path.exists(container_files):
            shutil.rmtree(container_files)
            print(f"INFO: Deleted Directory: {container_files}")
            logger.info(f"Deleted Directory: {container_files}")
        else:
            print("WARNING: Deleted Installation Directory. Skipping file deletion.")
            logger.warning("Deleted Installation Directory during uninstall.")

        print("UNINSTALLATION COMPLETE")
        logger.info("Uninstallation completed successfully.")
    except Exception as e:
        print(f"ERROR: Uninstallation failed: {e}")
        logger.error(f"An unexpected error occurred during uninstallation: {e}")

# Validate User input
def validate_inputs(directory: str, CLIENT_KEY: str) -> bool:
    """Validate user inputs."""
    if not directory:
        print("ERROR: Directory path are required.")
        logger.error("Directory path are required.")
        return False
    if not CLIENT_KEY:
        print("ERROR: Client key is required.")
        logger.error("Client key is required.")
        return False
    return True

# Display Help
def display_help():
    """Display the help message."""
    print("""
    ========================================================
    NETSKOPE LOG STREAM CLIENT INSTALLER
    ========================================================

    What is this script?

    This script manages streaming client Docker container.
    This script simplifies installation, scheduling updates, monitoring, and cleanup.

    Supported Features:
    - Verifies system compatibility and Docker installation.
    - Runs container interactively or in silent mode.
    - Schedules automatic updates using systemd timers.
    - Reinstalls or removes the container and its configuration.
    - Automatic version checking and updates from PyPI.

    Usage:
        es-installer [OPTION]

    Available Options:
    - `--help`              Show this help message and exit.
    - `Install`             Install and configure the container.
    - `--silent`            Run in silent mode with default values.
    - `Reinstall`           Stop the current container and start a fresh one.
    - `Uninstall`           Remove the container, image, and optional settings.
    - `--auto-upgrade`      Automatically upgrade to latest version if available.
    - `--no-version-check`  Skip version checking at startup.

    You can also run the script without any option:
        es-installer
    This will prompt you to choose an operation (Install, Reinstall, Uninstall, etc).

    Examples:
    - Display help:
        es-installer --help
    - Install with user prompts:
        es-installer Install
    - Reinstall with saved configuration:
        es-installer Reinstall
    - Silent install with default values:
        python3 installer.py --silent
    - Silent install with client key:
        python3 installer.py --silent -k YOUR_CLIENT_KEY
    - Silent install with auto-upgrade:
        es-installer --silent --auto-upgrade
    - Install without version check:
        es-installer Install --no-version-check
    - Uninstall everything:
        es-installer Uninstall

    What Each Option Does:

    - **Install**
        - Checks for latest version and prompts for upgrade.
        - Checks system OS and architecture.
        - Ensures Docker is running.
        - Asks directory path for storing logs.
        - Sets up weekly systemd timer (e.g., every Monday at 2 AM).

    - **--silent**
        - Skips prompts and uses default client key and script directory.
        - Automatically upgrades to latest version if available.
        - Useful for automation or simple one-click setup.

    - **Reinstall**
        - Stops and removes the running container.
        - Starts a fresh one using saved client key and directory.

    - **Uninstall**
        - Removes the container and Docker image.
        - Asks if scheduler should be deleted.

    - **--auto-upgrade**
        - Automatically upgrade the installer to the latest version from PyPI.
        - No user prompt required.

    - **--no-version-check**
        - Skip the version check at startup.
        - Useful when running offline or in restricted environments.

    Notes:
    - Logs are saved to `container_init.log` in the script directory.
    - The installer checks PyPI for updates on each run (unless --no-version-check is used).
    - To manually upgrade: pip install --upgrade netskope-log-stream-client
    """)

def main():
    """Main function to run the installer checks and start the container."""
    try:
        print(f"NETSKOPE LOG STREAM CLIENT INSTALLER {VERSION}")
        print(f"Version: {__version__}")
        
        # Check for version updates (unless --no-version-check is passed)
        if "--no-version-check" not in sys.argv and "--help" not in sys.argv:
            # Auto-upgrade in silent mode, prompt in interactive mode
            auto_upgrade = "--silent" in sys.argv or "--auto-upgrade" in sys.argv
            check_for_updates(auto_upgrade=auto_upgrade)
        
        # Check for --help argument
        if "--help" in sys.argv:
            logger.info("User requested help.")
            display_help()
            sys.exit()

        # Check for --silent argument
        if "--silent" in sys.argv:
            logger.info("User run script in silent mode")
            run_silent_install()
            sys.exit()

        # Determine the option
        option = ""
        if "install" in sys.argv:
            option = "install"
        elif "reinstall" in sys.argv:
            option = "reinstall"
        elif "uninstall" in sys.argv:
            option = "uninstall"
        else:
            print("\nPlease specify an option:")
            print("1. install   - Set up and configure the container")
            print("2. reinstall - Remove and recreate the container")
            print("3. uninstall - Remove the container and cleanup")
            logger.info("Prompting user for option.")
            try:
                option_input = input("\nEnter option (install/reinstall/uninstall): ").strip()
                if option_input.lower() in ["1", "install"]:
                    option = "install"
                elif option_input.lower() in ["2", "reinstall"]:
                    option = "reinstall"
                elif option_input.lower() in ["3", "uninstall"]:
                    option = "uninstall"
                else:
                    print("ERROR: Invalid option. Please choose 'install', 'reinstall', or 'uninstall'.")
                    sys.exit(1)
            except (EOFError, KeyboardInterrupt):
                print("\nOperation canceled by user.")
                sys.exit(1)

        # Installation
        if option == "install":
            print("INSTALLATION")
            if check_os() and check_architecture() and check_docker():
                print("\nSUCCESS: All the systems checks passed.")

                print("\nConfiguring container ...")
                logger.info("All the systems checks passed...")
                logger.info("Configure Container....")
                result = subprocess.run(["docker", "ps", "-a", "-q", "-f", f"name={CONTAINER_NAME}"], capture_output=True, text=True)
                container_exists = bool(result.stdout.strip())
                if container_exists:
                    print(f"ERROR: A container with the name '{CONTAINER_NAME}' already exists.")
                    print("INFO: Please run the uninstall option then install.")
                    sys.exit(1)

                try:
                    default_dir = os.path.expanduser("~/ns")
                    directory = input(f"\nEnter the directory path to store the installation files and logs [default: {default_dir}]: ").strip()
                    if not directory:
                        directory = default_dir
                except (EOFError, KeyboardInterrupt):
                    print("\nOperation canceled by user.")
                    sys.exit(1)

                if CLIENT_KEY!="":
                            client_key = CLIENT_KEY
                            # Validate the client key
                            is_valid, error_msg = validate_client_key(client_key)
                            if not is_valid:
                                print(f"ERROR: Invalid client key - {error_msg}. Please retry with valid client key")
                                logger.error(f"Client key validation failed: {error_msg}")
                                sys.exit(1)
                else:
                    client_key=get_client_key_from_args()
                    if client_key:
                        print(f"INFO: Using client key from arguments.")
                        print(f"Client key: {client_key}")
                        logger.info(f"Using client key from arguments.")

                        # Validate the client key from arguments
                        is_valid, error_msg = validate_client_key(client_key)
                        if not is_valid:
                            print(f"ERROR: Invalid client key - {error_msg}. Please retry with valid client key")
                            logger.error(f"Client key validation failed: {error_msg}")
                            sys.exit(1)
                    else:
                        try:
                            client_key = input("Enter the client key : ").strip()
                            print(f"Client key: {client_key}")
                        except Exception as error:
                            print('ERROR:', error)
                            logger.error(f"Error while reading client key: {error}")
                            sys.exit(1)

                # Validate the client key
                is_valid, error_msg = validate_client_key(client_key)
                if not is_valid:
                    print(f"ERROR: Invalid client key - {error_msg}. Please retry with valid client key")
                    logger.error(f"Client key validation failed: {error_msg}")
                    sys.exit(1)

                print("\nPlease set up a weekly schedule for automatic Docker image updates.")
                default_day = "Thursday"
                default_time = "23:00"
                use_default = False
                try:
                    response = input(f"\nDo you want to use the default schedule ({default_day} at {default_time})? [y/n]: ").strip().lower()
                    if response in ("y", "yes"):
                        use_default = True
                except (EOFError, KeyboardInterrupt):
                    print("\nOperation canceled by user.")
                    sys.exit(1)

                days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                if not use_default:
                    print("\nEnter the day of the week and time of day when updates should be checked.")
                    while True:
                        try:
                            day_of_week = input("\nDay of week (e.g., Monday): ").strip()
                            if day_of_week in days:
                                default_day = day_of_week
                                break
                            print("ERROR: Invalid day. Please enter a valid day name (e.g., Monday).")
                        except (EOFError, KeyboardInterrupt):
                            print("\nOperation canceled by user.")
                            sys.exit(1)
                    while True:
                        try:
                            time_of_day = input("Day of Time (24-hour format, HH:MM): ").strip()
                            match = re.match(r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", time_of_day)
                            if match:
                                hour, minute = map(int, time_of_day.split(':'))
                                default_time = time_of_day
                                break
                            else:
                                print("ERROR: Invalid time format. Please use HH:MM format (e.g., 14:15).")
                                logger.info("Invalid time format entered.")
                        except (EOFError, KeyboardInterrupt):
                            print("\nOperation canceled by user.")
                            sys.exit(1)

                # Get proxy configuration
                container_proxy, user_wants_proxy = check_proxy_setup()

                # Check if proxy configuration failed (False means error, None means no proxy)
                if container_proxy is False:
                    print("ERROR: Installation aborted due to proxy configuration failure.")
                    logger.error("Installation aborted due to proxy configuration failure.")
                    sys.exit(1)

                if validate_inputs(directory, client_key):
                    logger.info(f"Directory: {directory}")
                    try:
                        if run_container(client_key, directory, option, container_proxy, user_wants_proxy):
                            run_watcher_container(directory, default_day, default_time, container_proxy)
                            success, is_grpc_error = wait_for_config_download(os.path.join(directory, "container_files", "logs", "installerInformation.log"))
                            if success:
                                logger.info("Configuration successfully completed.")
                                print("INSTALLATION COMPLETE")
                            else:
                                if not is_grpc_error:
                                    print("configuration failed")
                                logger.error("Configuration failed.")
                                print("INSTALLATION COMPLETE (WITH ERROR)")
                        else:
                            print("\nERROR: Failed to start the container.")
                    except Exception as e:
                        print(f"ERROR: Configuration failed: {e}")
                        logger.error(f"Configuration failed: {e}")
                        print("Installation could not be completed.")
                else:
                    print("ERROR: Installation aborted due to invalid inputs.")
                    logger.error("Invalid inputs provided.")
            else:
                print("\nERROR: Installation failed due to unmet system requirements.")
                logger.error("Setup failed due to unmet requirements.")

        # Reinstall
        elif option == "reinstall":
            logger.info("Reinstalling container with stored credential.")
            try:
                reinstall(option)
            except Exception as e:
                print(f"ERROR: Reinstallation failed: {e}")
                logger.error(f"Reinstall failed: {e}")

        # Uninstall
        elif option == "uninstall":
            logger.info("Removing the container and Image")
            try:
                uninstall()
            except Exception as e:
                print(f"ERROR: Uninstallation failed: {e}")
                logger.error(f"Uninstall failed: {e}")

    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {e}")
        print("Please check the installer.log file for more details.")
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()