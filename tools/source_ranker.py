import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SourceRank:
    """Ranking de fonte com score e tier."""
    score: int
    tier: str
    reason: str


class SourceRanker:
    """Rank search results by source quality: 60% official docs + 40% practical articles."""

    # TIER 1: Official Documentation (60%)
    TIER_1_OFFICIAL = {
        "name": "official_docs",
        "score": 100,
        "patterns": [
            r"^https://docs\.",
            r"^https://[a-z-]+\.io/docs",
            r"^https://[a-z-]+\.org/doc",
            r"/official.*docum",
            r"github\.com/([a-z-]+)/\1(/|$)",  # github.com/docker/docker
        ],
        "domains": {
            # Containers
            "docs.docker.com": 100,
            "podman.io/docs": 100,
            "github.com/containers": 95,
            "docs.podman.io": 100,
            # Kubernetes
            "kubernetes.io": 100,
            "k3s.io": 100,
            "github.com/kubernetes": 95,
            # Databases
            "postgresql.org/docs": 100,
            "mysql.com/doc": 100,
            "duckdb.org/docs": 100,
            "sqlite.org": 100,
            "clickhouse.com/docs": 100,
            "mongodb.com/docs": 100,
            "redis.io/documentation": 100,
            # Streaming
            "kafka.apache.org/docs": 100,
            "flink.apache.org/docs": 100,
            # Monitoring
            "prometheus.io/docs": 100,
            "grafana.com/docs": 100,
            # Storage
            "minio.io/docs": 100,
            "ceph.io/docs": 100,
            # IA/LLM
            "ollama.com": 95,
            "lm-studio.org": 95,
        }
    }

    # TIER 2: Technical Articles (35%) - uso prático
    TIER_2_TECHNICAL = {
        "name": "technical_articles",
        "score": 75,
        "patterns": [
            r"github\.com",  # All GitHub (not official repo handled in TIER_1)
            r"dev\.to/",
            r"medium\.com/",
            r"hashicorp\.com/",
            r"atlassian\.com/.*blog",
            r"cloud\.google\.com/docs",
            r"docs\.aws\.amazon\.com",
            r"docs\.microsoft\.com",
            r"digitalocean\.com/community",
            r"linode\.com/docs",
        ],
        "domains": {
            "github.com": 80,
            "dev.to": 75,
            "medium.com": 70,
            "digitalocean.com": 78,
            "linode.com": 75,
            "aws.amazon.com": 85,
            "cloud.google.com": 85,
            "docs.microsoft.com": 85,
            "hashicorp.com": 80,
        }
    }

    # TIER 3: Community (5%) - último recurso
    TIER_3_COMMUNITY = {
        "name": "community",
        "score": 40,
        "patterns": [
            r"stackoverflow\.com",
            r"reddit\.com/r/",
            r"discourse\..*\.org",
        ],
        "domains": {
            "stackoverflow.com": 45,
            "reddit.com": 35,
        }
    }

    # REJECT: Blogs genéricos, spam, outdated
    REJECT_PATTERNS = [
        r"pinterest\.com",
        r"facebook\.com",
        r"twitter\.com",
        r"instagram\.com",
        r"youtube\.com(?!/c/[A-Z])",  # allow channels, reject videos
        r"linkedin\.com/pulse",
        r"medium\.com/tag/",  # tag pages, not articles
        r"quora\.com",
        r"example\.com",
        r"localhost",
        r"127\.0\.0\.1",
        r"testdomain",
        r"\d{4}-\d{2}-\d{2}.*\(old\)",  # explicitly old posts
    ]

    def __init__(self):
        pass

    def rank_results(self, results: list[dict]) -> list[dict]:
        """Reorder search results by source quality (60% official + 40% practical)."""
        scored_results = []

        for idx, result in enumerate(results):
            url = result.get("url", "")
            rank = self._calculate_rank(url)

            scored_results.append({
                **result,
                "_source_score": rank.score,
                "_source_tier": rank.tier,
                "_source_reason": rank.reason,
                "_original_position": idx,
            })

        # Sort by score DESC, preserve original order as tiebreaker
        sorted_results = sorted(
            scored_results,
            key=lambda x: (-x["_source_score"], x["_original_position"])
        )

        return sorted_results

    def _calculate_rank(self, url: str) -> SourceRank:
        """Calculate rank for a single URL."""
        url_lower = url.lower()

        # Check reject patterns first
        for pattern in self.REJECT_PATTERNS:
            if re.search(pattern, url_lower, re.IGNORECASE):
                return SourceRank(
                    score=0,
                    tier="rejected",
                    reason=f"Matched reject pattern: {pattern}"
                )

        # Extract domain
        domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url_lower)
        if not domain_match:
            return SourceRank(score=10, tier="unknown", reason="Could not extract domain")

        domain = domain_match.group(1)

        # Check TIER 1: Official Docs
        tier_1_score = self._check_tier(url_lower, domain, self.TIER_1_OFFICIAL)
        if tier_1_score and tier_1_score > 0:
            return SourceRank(
                score=tier_1_score,
                tier="tier_1_official",
                reason=f"Official documentation (domain: {domain})"
            )

        # Check TIER 2: Technical Articles
        tier_2_score = self._check_tier(url_lower, domain, self.TIER_2_TECHNICAL)
        if tier_2_score and tier_2_score > 0:
            return SourceRank(
                score=tier_2_score,
                tier="tier_2_technical",
                reason=f"Technical article (domain: {domain})"
            )

        # Check TIER 3: Community
        tier_3_score = self._check_tier(url_lower, domain, self.TIER_3_COMMUNITY)
        if tier_3_score and tier_3_score > 0:
            return SourceRank(
                score=tier_3_score,
                tier="tier_3_community",
                reason=f"Community (domain: {domain})"
            )

        # Default: reject generic blogs
        return SourceRank(
            score=5,
            tier="generic_blog",
            reason=f"Generic blog (domain: {domain})"
        )

    def _check_tier(self, url: str, domain: str, tier_config: dict) -> Optional[int]:
        """Check if URL matches a tier configuration."""
        # Check domain map first (fastest)
        for tier_domain, score in tier_config["domains"].items():
            if domain == tier_domain or domain.endswith("." + tier_domain):
                return score

        # Check patterns
        for pattern in tier_config["patterns"]:
            if re.search(pattern, url, re.IGNORECASE):
                return tier_config["score"]

        return None

    def get_tier_distribution(self, ranked_results: list[dict]) -> dict:
        """Get distribution of sources by tier."""
        distribution = {}
        for result in ranked_results:
            tier = result.get("_source_tier", "unknown")
            distribution[tier] = distribution.get(tier, 0) + 1

        return distribution

    def filter_by_tier(self, results: list[dict], allowed_tiers: list[str]) -> list[dict]:
        """Filter results to only include specific tiers."""
        return [r for r in results if r.get("_source_tier") in allowed_tiers]

    def get_top_by_tier_ratio(self, results: list[dict], ratio: dict) -> list[dict]:
        """
        Get results maintaining tier ratio.
        Example: ratio = {"tier_1_official": 0.6, "tier_2_technical": 0.4}
        """
        tier_buckets = {}
        for result in results:
            tier = result.get("_source_tier", "unknown")
            if tier not in tier_buckets:
                tier_buckets[tier] = []
            tier_buckets[tier].append(result)

        selected = []
        for tier, target_ratio in ratio.items():
            if tier in tier_buckets:
                count = max(1, int(len(results) * target_ratio))
                selected.extend(tier_buckets[tier][:count])

        # Fill remaining slots with next best tier
        remaining_count = len(results) - len(selected)
        if remaining_count > 0:
            for tier in ["tier_2_technical", "tier_3_community", "generic_blog"]:
                if tier in tier_buckets:
                    selected.extend(
                        tier_buckets[tier][:(remaining_count)]
                    )
                    remaining_count -= len(tier_buckets[tier])
                    if remaining_count <= 0:
                        break

        return selected[:len(results)]
