"""Version checking and auto-update functionality for the installer."""

import sys
import subprocess
import logging
import os
from typing import Tuple, Optional
import requests
from packaging import version

logger = logging.getLogger(__name__)


def restart_installer():
    """Restart the installer to load the new version."""
    try:
        print("Restarting installer with new version...")
        logger.info("Restarting installer to load newly installed version")
        
        # Restart the script with the same arguments
        # This will load the newly installed version
        python = sys.executable
        os.execv(python, [python] + sys.argv)
        
    except Exception as e:
        print(f"Could not auto-restart: {e}")
        print(f"Please manually run: ns-installer {' '.join(sys.argv[1:])}")
        logger.error(f"Failed to auto-restart: {e}")
        sys.exit(1)


def get_current_version() -> str:
    """Get the current installed version of the package."""
    try:
        from installer import __version__
        return __version__
    except ImportError:
        return "0.0.0"


def get_latest_version_from_pypi(package_name: str = "netskope-log-stream-client-installer", include_prereleases: bool = False) -> Optional[str]:
    """
    Fetch the latest version from PyPI.
    
    Args:
        package_name: The name of the package on PyPI
        include_prereleases: If False, only returns stable releases (default: False)
        
    Returns:
        str: Latest stable version string, or None if unable to fetch
    """
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        
        # Configure proxy settings from environment variables
        proxies = None
        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        
        if http_proxy or https_proxy:
            proxies = {
                'http': http_proxy if http_proxy else https_proxy,
                'https': https_proxy if https_proxy else http_proxy
            }
            proxy_display = https_proxy if https_proxy else http_proxy
            print(f"Using proxy: {proxy_display}")
            logger.info(f"Using proxy configuration for PyPI access: {proxy_display}")
        else:
            logger.info("No proxy configured, using direct connection to PyPI")
        
        response = requests.get(url, timeout=10, proxies=proxies)
        response.raise_for_status()
        data = response.json()
        
        # Get all available versions
        all_versions = list(data["releases"].keys())
        
        if not include_prereleases:
            # Filter out pre-release versions (beta, alpha, rc, dev, etc.)
            stable_versions = []
            for v in all_versions:
                try:
                    parsed = version.parse(v)
                    # Pre-releases have .is_prerelease == True
                    if not parsed.is_prerelease:
                        stable_versions.append(v)
                except Exception:
                    # Skip invalid version strings
                    continue
            
            if not stable_versions:
                logger.warning("No stable versions found on PyPI")
                print("WARNING: No stable versions found on PyPI")
                return None
            
            # Find the highest stable version
            latest_version = max(stable_versions, key=version.parse)
            logger.info(f"Latest stable version on PyPI: {latest_version} (excluded {len(all_versions) - len(stable_versions)} pre-releases)")
        else:
            # Include pre-releases, find the highest version from all versions
            latest_version = max(all_versions, key=version.parse)
            logger.info(f"Latest version on PyPI (including pre-releases): {latest_version}")
        
        return latest_version
        
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch latest version from PyPI: {e}")
        print(f"WARNING: Could not check for updates from PyPI: {e}")
        return None
    except (KeyError, ValueError) as e:
        logger.warning(f"Failed to parse PyPI response: {e}")
        print(f"WARNING: Could not parse version information from PyPI: {e}")
        return None


def compare_versions(current: str, latest: str) -> Tuple[bool, str]:
    """
    Compare current version with latest version.
    
    Args:
        current: Current version string
        latest: Latest version string
        
    Returns:
        Tuple[bool, str]: (needs_update, comparison_message)
    """
    try:
        current_ver = version.parse(current)
        latest_ver = version.parse(latest)
        
        if latest_ver > current_ver:
            return True, f"New version available: {latest} (current: {current})"
        elif latest_ver == current_ver:
            return False, f"You are using the latest version: {current}"
        else:
            return False, f"You are using version {current} (latest: {latest})"
    except Exception as e:
        logger.warning(f"Failed to compare versions: {e}")
        return False, f"Could not compare versions: {e}"


def upgrade_package(package_name: str = "netskope-log-stream-client-installer") -> bool:
    """
    Upgrade the package to the latest version using pip.
    
    Args:
        package_name: The name of the package to upgrade
        
    Returns:
        bool: True if upgrade was successful, False otherwise
    """
    try:
        print(f"\n>>> Upgrading {package_name} to the latest version...")
        logger.info(f"Attempting to upgrade {package_name}")
        
        # Build pip command with proxy settings
        pip_cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package_name]
        
        # Add proxy if configured
        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        proxy_url = https_proxy if https_proxy else http_proxy
        
        if proxy_url:
            pip_cmd.extend(["--proxy", proxy_url])
            print(f"Using proxy for upgrade: {proxy_url}")
            logger.info(f"Using proxy for pip upgrade: {proxy_url}")
        else:
            logger.info("No proxy configured for pip, using direct connection")
        
        # Use pip to upgrade the package
        result = subprocess.run(
            pip_cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        print(f"SUCCESS: Package upgraded successfully!")
        logger.info(f"Package upgraded successfully: {result.stdout}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to upgrade package: {e}")
        print(f"Details: {e.stderr}")
        logger.error(f"Failed to upgrade package: {e.stderr}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error during upgrade: {e}")
        logger.error(f"Unexpected error during upgrade: {e}")
        return False


def check_for_updates(auto_upgrade: bool = False, package_name: str = "netskope-log-stream-client-installer") -> bool:
    """
    Check for updates and optionally auto-upgrade.
    
    Args:
        auto_upgrade: If True, automatically upgrade if a new version is available
        package_name: The name of the package on PyPI
        
    Returns:
        bool: True if an update was performed, False otherwise
    """
    try:
        current = get_current_version()
        print(f"\nCurrent version: {current}")
        logger.info(f"Current version: {current}")
        
        print("Checking for updates...")
        latest = get_latest_version_from_pypi(package_name)
        
        if latest is None:
            print("INFO: Unable to check for updates. Continuing with current version.")
            return False
        
        needs_update, message = compare_versions(current, latest)
        print(f"INFO: {message}")
        logger.info(message)
        
        if needs_update:
            if auto_upgrade:
                print("\nAuto-upgrade enabled. Upgrading now...")
                if upgrade_package(package_name):
                    restart_installer()  # Automatically restart with new version
                else:
                    print("WARNING: Auto-upgrade failed. Continuing with current version.")
                    return False
            else:
                print("\nA new version is available!")
                try:
                    response = input("Do you want to upgrade now? [y/n]: ").strip().lower()
                    if response in ("y", "yes"):
                        if upgrade_package(package_name):
                            restart_installer()  # Automatically restart with new version
                        else:
                            print("Continuing with current version.")
                            return False
                    else:
                        print("Continuing with current version.")
                        print(f"You can upgrade later by running: pip install --upgrade {package_name}")
                        return False
                except (EOFError, KeyboardInterrupt):
                    print("\nSkipping upgrade. Continuing with current version.")
                    return False
        
        return False
        
    except Exception as e:
        print(f"WARNING: Error checking for updates: {e}")
        logger.warning(f"Error checking for updates: {e}")
        print("Continuing with current version.")
        return False
