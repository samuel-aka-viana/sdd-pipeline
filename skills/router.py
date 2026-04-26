import re
import logging

logger = logging.getLogger(__name__)


class ToolTypeRouter:
    """Classify tool pair → type → optimal pipeline config."""

    TOOL_MAP = {
        "containers": {
            "docker", "podman", "containerd", "cri-o", "nerdctl", "lxc", "lxd"
        },
        "orchestration": {
            "kubernetes", "k3s", "microk8s", "k0s", "kind", "minikube", "k8s"
        },
        "databases_oltp": {
            "postgresql", "postgres", "mysql", "sqlite", "mariadb", "oracle",
            "sql server", "cockroachdb", "tidb"
        },
        "databases_olap": {
            "duckdb", "clickhouse", "trino", "bigquery", "snowflake", "vertica",
            "redshift", "athena", "presto"
        },
        "databases_nosql": {
            "mongodb", "redis", "cassandra", "elasticsearch", "dynamodb", "couchdb",
            "arangodb", "neo4j"
        },
        "streaming": {
            "kafka", "flink", "nats", "rabbitmq", "pulsar", "kinesis", "kafka streams",
            "apache flink"
        },
        "languages": {
            "python", "go", "rust", "typescript", "java", "c#", "csharp", "kotlin",
            "scala", "javascript", "node", "nodejs"
        },
        "monitoring": {
            "prometheus", "grafana", "victoriametrics", "loki", "datadog", "new relic",
            "dynatrace", "splunk", "elastic"
        },
        "storage": {
            "minio", "ceph", "seaweedfs", "s3", "gcs", "azure storage", "gluster",
            "nfs", "lustre"
        },
        "llm_tools": {
            "ollama", "lm studio", "llama.cpp", "vllm", "text-generation-webui",
            "lm-studio"
        },
        "analytics": {
            "polars", "pandas", "spark", "dbt", "sqlmesh", "dbt cloud", "apache spark",
            "pyspark", "dataframe"
        },
    }

    def classify(self, ferramentas: str, foco: str) -> dict:
        """Return routing config for this tool + focus combination."""
        tools = self._parse_tools(ferramentas)
        tool_type = self._identify_type(tools)

        return {
            "tool_type": tool_type,
            "tools": tools,
            "research_boost_queries": self._boost_queries(tool_type, foco),
            "skip_sections": self._sections_to_skip(tool_type, foco),
            "rule_profile": tool_type,
            "can_parallelize_analysis": len(tools) >= 2,
            "analysis_aspects": self._aspects_for(tool_type, foco),
        }

    def _parse_tools(self, ferramentas: str) -> list[str]:
        """Extract tool names from input string."""
        tools = re.split(r'[,\s&]+', ferramentas.lower())
        return [t.strip() for t in tools if t.strip()]

    def _identify_type(self, tools: list[str]) -> str:
        """Identify primary tool type from list of tools."""
        tool_lower = [t.lower() for t in tools]

        for tool_type, tool_names in self.TOOL_MAP.items():
            if any(tool in tool_names for tool in tool_lower):
                return tool_type

        return "default"

    def _boost_queries(self, tool_type: str, foco: str) -> list[str]:
        """Return additional search queries based on tool type."""
        base_boost = {
            "containers": ["rootless", "buildkit", "oci", "runtime"],
            "orchestration": ["helm", "crd", "operator", "admission"],
            "databases_olap": ["benchmark", "tpc-h", "analytics"],
            "llm_tools": ["quantization", "inference", "tokens/s"],
            "monitoring": ["alerting", "slo", "scrape"],
            "streaming": ["throughput", "latency", "at-least-once"],
        }

        queries = base_boost.get(tool_type, [])

        if foco == "performance / throughput":
            queries.extend(["benchmark", "latency", "throughput", "load test"])
        elif foco == "segurança":
            queries.extend(["security", "rbac", "tls", "encryption"])
        elif foco == "integração":
            queries.extend(["integration", "api", "compatibility", "sdk"])

        return list(set(queries))

    def _sections_to_skip(self, tool_type: str, foco: str) -> list[str]:
        """Sections that may be optional for this tool type."""
        skip_map = {
            "languages": ["instalação"],
            "llm_tools": [],
            "monitoring": ["requisitos"],
        }
        return skip_map.get(tool_type, [])

    def _aspects_for(self, tool_type: str, foco: str) -> list[str]:
        """Analysis aspects for parallel processing."""
        aspects = ["core"]

        if foco == "performance / throughput":
            aspects.append("performance")
        elif foco == "segurança":
            aspects.append("security")
        elif foco == "custo":
            aspects.append("cost")

        if foco == "integração":
            aspects.append("integration")

        if tool_type in ("databases_olap", "databases_oltp", "streaming"):
            aspects.append("scalability")

        return aspects
