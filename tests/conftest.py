import pytest
from sdd.config import load_runtime_config
from validators.spec_validator import SpecValidator


@pytest.fixture
def spec():
    """Load the merged runtime config from sdd/config/."""
    return load_runtime_config()


@pytest.fixture
def validator():
    """Create SpecValidator instance with the merged runtime config."""
    return SpecValidator()


@pytest.fixture
def valid_article():
    """A minimal valid article matching all spec requirements"""
    return """
# TLDR
Brief summary of the article about k3s and lightweight Kubernetes.

# O que é
k3s is a lightweight Kubernetes distribution designed for resource-constrained environments. It's perfect for edge computing, IoT, and development scenarios. k3s removes unnecessary components while maintaining full Kubernetes API compatibility.

# Requisitos
System requirements:
- CPU: 2 cores minimum
- RAM: 1 GB minimum (512MB per node)
- Storage: available space
- Docker or containerd runtime
- Linux kernel 3.10+

# Instalação
Installation is straightforward using the official installer:

```bash
curl -sfL https://get.k3s.io | sh -
```

Key installation steps:
1. Download the installer from https://get.k3s.io
2. Run the installation script
3. Verify with `kubectl get nodes` from https://kubernetes.io/docs/tasks/tools/
4. Configure kubeconfig from https://github.com/k3s-io/k3s

Official documentation: https://docs.k3s.io

# Configuração
After installation, configure k3s for your use case:

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl get nodes
```

Additional configuration options include database backend, network policies, and resource limits.

# Exemplo Prático
Deploy a simple nginx application:

```bash
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --type=ClusterIP
kubectl get pods
kubectl describe pod nginx
```

Verify the deployment is running and accessible through the service.

# Armadilhas
Common mistakes and their solutions:

1. **Port conflicts**: k3s uses ports 6443 (API) and 10250 (kubelet). Error: bind: address already in use
   Solução: Stop conflicting services with `sudo systemctl stop <service>` or use different port with `--https-listen-port`

2. **Insufficient resources**: k3s needs at least 1GB RAM to run properly. Error: OOMKilled or evicted pods
   Solução: Increase available memory or reduce workload complexity. Use `kubectl top nodes` to monitor.

# Otimizações
Performance optimization tips for k3s:

1. Use SQLite for etcd (default) instead of PostgreSQL unless you need HA for the control plane
2. Enable service account token automounting only for services that need it to reduce API server load
3. Use network policies to segment traffic and reduce iptables overhead on the host
4. Configure resource limits on deployments to prevent noisy neighbor problems in shared environments

# Conclusão
k3s is the ideal choice for running Kubernetes in resource-constrained environments. Its lightweight footprint combined with full Kubernetes compatibility makes it perfect for edge computing, development, and IoT applications. Start with a single-node cluster and scale horizontally as needed.

# Referências
- https://docs.k3s.io/quick-start
- https://github.com/k3s-io/k3s/releases
- https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/
"""


@pytest.fixture
def invalid_article_missing_tldr():
    """Article missing TLDR section"""
    return """
# O que é
Content here about the tool.

# Requisitos
System requirements listed.

# Instalação
Installation steps here.

# Configuração
Configuration details.

# Exemplo Prático
Usage example here.

# Armadilhas
Common error 1. Error 2.

# Otimizações
Tip 1. Tip 2. Tip 3.

# Conclusão
Summary here.

# Referências
- https://docs.example.com
- https://github.com/example/repo
- https://tutorial.example.com
"""


@pytest.fixture
def invalid_article_with_placeholder():
    """Article with [TODO placeholder"""
    return """
# TLDR
Brief summary.

# O que é
[TODO: Add explanation of the tool]

# Requisitos
System requirements listed.

# Instalação
Installation steps.

# Configuração
Configuration details.

# Exemplo Prático
Usage example.

# Armadilhas
Error 1. Error 2.

# Otimizações
Tip 1. Tip 2. Tip 3.

# Conclusão
Summary.

# Referências
- https://docs.example.com
- https://github.com/example/repo
- https://tutorial.example.com
"""


@pytest.fixture
def invalid_article_insufficient_refs():
    """Article with only 1 reference (needs 3)"""
    return """
# TLDR
Brief summary.

# O que é
Explanation of the tool and its purpose.

# Requisitos
System requirements listed.

# Instalação
Installation steps from https://docs.example.com here.

# Configuração
Configuration details.

# Exemplo Prático
Usage example with code.

# Armadilhas
Error 1. Error 2.

# Otimizações
Tip 1. Tip 2. Tip 3.

# Conclusão
Summary.

# Referências
- https://docs.example.com
"""


@pytest.fixture
def invalid_article_with_http_url():
    """Article with http:// instead of https://"""
    return """
# TLDR
Brief summary.

# O que é
Explanation of the tool.

# Requisitos
System requirements listed.

# Instalação
Installation steps from http://docs.example.com here.

# Configuração
Configuration details.

# Exemplo Prático
Usage example with code.

# Armadilhas
Error 1. Error 2.

# Otimizações
Tip 1. Tip 2. Tip 3.

# Conclusão
Summary.

# Referências
- http://docs.example.com
- http://github.com/example/repo
- http://tutorial.example.com
"""


@pytest.fixture
def invalid_article_localhost_url():
    """Article with localhost URL"""
    return """
# TLDR
Brief summary.

# O que é
Explanation of the tool.

# Requisitos
System requirements listed.

# Instalação
Installation steps from http://localhost:8000 here.

# Configuração
Configuration details.

# Exemplo Prático
Usage example with code.

# Armadilhas
Error 1. Error 2.

# Otimizações
Tip 1. Tip 2. Tip 3.

# Conclusão
Summary.

# Referências
- http://localhost:3000
- https://github.com/example/repo
- https://tutorial.com
"""
