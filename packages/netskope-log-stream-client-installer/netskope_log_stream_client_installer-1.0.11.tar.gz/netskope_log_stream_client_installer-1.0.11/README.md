# Netskope Log Stream Client Installer

    This script manages streaming client Docker container.
    This script simplifies installation, scheduling updates, monitoring, and cleanup.

## Overview

The installer automates the deployment of a containerized log streaming client that:
- Streams logs from Netskope services
- Provides automated monitoring and health checks
- Schedules regular updates via a watcher container
- Manages container lifecycle operations

## Prerequisites

### System Requirements
- **Operating Systems**: Debian, Ubuntu, Raspbian, RHEL, CentOS, Rocky Linux, AlmaLinux, SLES
- **Architecture**: x86_64, ARM64, AMD64, 64-bit
- **Docker**: Must be installed and running
- **Python**: Python 3.x with standard libraries

### Docker Images
- Main application: `nsstreamingclient/ns-streaming-client-container`
- Watcher service: `nsstreamingclient/ns-watcher`

## Usage

### Command Line Options

```bash
python3 installer.py [OPTION]
```

#### Available Options

| Option | Description |
|--------|-------------|
| `--help` | Display help message and exit |
| `install` | Interactive installation with user prompts |
| `--silent` | Silent installation with default settings |
| `reinstall` | Remove and recreate existing container |
| `uninstall` | Complete removal of containers and files |

### Interactive Mode

Run without arguments to get an interactive menu:
```bash
python3 installer.py
```

You'll be prompted to choose:
1. **install** - Set up and configure the container
2. **reinstall** - Remove and recreate the container
3. **uninstall** - Remove the container and cleanup

### Installation Examples

#### Interactive Installation
```bash
python3 installer.py install
```
- Prompts for installation directory
- Configures update schedule
- Sets up monitoring

#### Silent Installation
```bash
python3 installer.py --silent
```
- Uses default directory: `~/ns`
- Default update schedule: Thursday at 11.00 pm
- No user interaction required

#### Reinstallation
```bash
python3 installer.py reinstall
```
- Uses stored configuration
- Preserves existing settings
- Updates container to latest version

#### Uninstallation
```bash
python3 installer.py uninstall
```
- Removes all containers and images
- Cleans up installation directories
- Removes configuration files

## Configuration

### Installation Directory Structure
```
~/ns/                          # Default installation directory
├── container_files/
│   └── container_env.env      # Environment configuration
└── container_logs/            # Container log files
```

### Environment Configuration
The installer creates a `container_env.env` file containing:
- Container key
- Installation directory path
- Connection key

### Update Schedule
The watcher container monitors and updates the main container based on your configured schedule:
- **Default**: Every Thursday at 11:00 pm
- **Customizable**: Any day of the week, any time (24-hour format)

## Features

### System Validation
- Operating system compatibility check
- Hardware architecture verification
- Docker installation and daemon status
- Comprehensive pre-flight validation

### Container Management
- Automatic image pulling and updating
- Container lifecycle management
- Restart policies and health monitoring
- Log rotation and management

### Monitoring & Updates
- Automated ns-watcher container for monitoring
- Container health checks and restart capabilities
- Comprehensive logging and error handling

### Security
- Container key authentication
- Secure environment variable handling
- Container isolation and resource limits

## Logging

The installer creates detailed logs in `installer.log` with:
- Installation progress and status
- Error messages and troubleshooting information
- Container lifecycle events
- System validation results

### Log Levels
- **INFO**: Normal operation messages
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures requiring attention

## Troubleshooting

### Common Issues

#### Docker Not Running
```
ERROR: Docker daemon is not running.
```
**Solution**: Start Docker service
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

#### Unsupported Operating System
```
ERROR: Operating system is not supported.
```
**Solution**: Verify you're running on a supported OS or contact support

#### Container Already Exists
```
ERROR: A container with the name 'ns-streaming-client-container' already exists.
```
**Solution**: Run uninstall first, then install
```bash
python3 installer.py uninstall
python3 installer.py install
```

#### Permission Issues
```
ERROR: Permission denied
```
**Solution**: Ensure user has Docker permissions
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Log Analysis
Check `installer.log` for detailed error information:
```bash
tail -f installer.log
```

## Container Details

### Main Container (`ns-streaming-client-container`)
- **Image**: `nsstreamingclient/ns-streaming-client-container`
- **Purpose**: Log streaming and processing
- **Restart Policy**: Always restart
- **Volumes**:
  - Configuration: `/opt/ns`
  - Logs: `/var/log`

### Watcher Container (`ns-watcher`)
- **Image**: `nsstreamingclient/watcher`
- **Purpose**: Monitoring and automated updates
- **Network**: Host network access
- **Volumes**:
  - Installation directory: `/mnt`
  - Docker socket: `/var/run/docker.sock`

### Log Management
- **Driver**: JSON file logging
- **Rotation**: 10MB max size, 10 files max
- **Compression**: Enabled for space efficiency

## Security Considerations

- The installer uses a container key for authentication
- Containers run with minimal required privileges
- Log files are rotated and compressed to prevent disk space issues
- Docker socket access is required for the ns-watcher container

## Support

### Getting Help
```bash
python3 installer.py --help
```

### Log Files
- Installation logs: `installer.log`
- Container logs: `~/ns/container_logs/`

### Environment Information
Check your environment configuration:
```bash
cat ~/ns/container_files/container_env.env
```

## Development

### Code Structure
- System validation functions
- Docker management utilities
- Container lifecycle management
- Environment configuration handling
- Logging and error handling

### Dependencies
- Python 3.x standard library modules
- Docker CLI tools
- System utilities (platform detection)

## License

This installer is provided as-is for managing Netskope Log Stream Client deployments.

---

**Note**: This installer requires Docker to be installed and running on your system. Ensure you have appropriate permissions to manage Docker containers before running the installation.