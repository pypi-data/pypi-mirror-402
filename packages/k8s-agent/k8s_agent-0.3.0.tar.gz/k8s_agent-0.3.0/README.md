# k8s-agent

CLI tool for K8sVMGr - Kubernetes VM Manager

## Installation

```bash
pip install k8s-agent
```

## Quick Start

### Authentication

```bash
# Login to your K8sVMGr account
k8s-agent login

# Check who you're logged in as
k8s-agent whoami

# Logout
k8s-agent logout
```

### VM Management

```bash
# List all VMs
k8s-agent list

# Create a CPU VM
k8s-agent create --cpu 16

# Create a GPU VM
k8s-agent create --gpu 2 --gpu-model A800-80G-R

# Check availability before creating
k8s-agent create --gpu 4 --gpu-model A800-80G-R --check

# Delete a VM
k8s-agent delete <vm-id>

# Force delete (skip backup)
k8s-agent delete <vm-id> --force
```

### VM Inspection

```bash
# View VM events
k8s-agent events <vm-id>

# View VM logs
k8s-agent logs <vm-id>
k8s-agent logs <vm-id> --tail 100

# View VM dashboard with visual metrics
k8s-agent dashboard <vm-id>
```

### VM Operations

```bash
# Interconnect all running VMs for SSH access
k8s-agent interconnect
```

## Features

- 🔐 **OAuth 2.0 Device Flow Authentication** - Secure login via web browser
- 📊 **Visual Dashboard** - Beautiful ASCII charts showing GPU/CPU metrics
- 🚀 **VM Lifecycle Management** - Create, delete, and monitor VMs
- 📈 **Resource Monitoring** - Real-time metrics with gauges and sparklines
- 🔗 **VM Interconnection** - Setup SSH between VMs for distributed computing
- 🎯 **Tab Completion** - Fast command completion (future feature)

## Configuration

k8s-agent stores authentication tokens in `~/.k8s-agent/config.json`.

You can override the API URL with the `--api-url` flag or set the `K8S_AGENT_API_URL` environment variable.

## Requirements

- Python 3.8+
- Access to a K8sVMGr backend instance

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/k8s-agent.git
cd k8s-agent

# Install in development mode
pip install -e .

# Run tests
pytest
```

## License

MIT License

## Support

For issues and feature requests, please visit:
https://github.com/yourusername/k8s-agent/issues
