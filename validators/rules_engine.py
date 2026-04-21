class AdaptiveRulesEngine:
    """Override quality rule thresholds based on tool_type and foco."""

    PROFILES = {
        "containers": {
            "min_references": 5,
            "min_errors": 2,
            "min_tips": 3,
            "require_benchmark": False,
        },
        "orchestration": {
            "min_references": 4,
            "min_errors": 3,
            "min_tips": 3,
            "require_benchmark": False,
        },
        "databases_olap": {
            "min_references": 4,
            "min_errors": 2,
            "min_tips": 2,
            "require_benchmark": True,
        },
        "databases_oltp": {
            "min_references": 3,
            "min_errors": 2,
            "min_tips": 3,
            "require_benchmark": False,
        },
        "databases_nosql": {
            "min_references": 3,
            "min_errors": 2,
            "min_tips": 2,
            "require_benchmark": False,
        },
        "streaming": {
            "min_references": 4,
            "min_errors": 2,
            "min_tips": 3,
            "require_benchmark": True,
        },
        "languages": {
            "min_references": 3,
            "min_errors": 2,
            "min_tips": 2,
            "require_benchmark": False,
        },
        "monitoring": {
            "min_references": 4,
            "min_errors": 2,
            "min_tips": 3,
            "require_benchmark": False,
        },
        "storage": {
            "min_references": 4,
            "min_errors": 2,
            "min_tips": 2,
            "require_benchmark": True,
        },
        "llm_tools": {
            "min_references": 3,
            "min_errors": 2,
            "min_tips": 2,
            "require_benchmark": True,
        },
        "analytics": {
            "min_references": 4,
            "min_errors": 2,
            "min_tips": 2,
            "require_benchmark": True,
        },
        "default": {
            "min_references": 3,
            "min_errors": 2,
            "min_tips": 3,
            "require_benchmark": False,
        },
    }

    def __init__(self):
        pass

    def get_profile(self, tool_type: str, foco: str) -> dict:
        """Get rule profile with focus-based overrides."""
        profile = dict(self.PROFILES.get(tool_type, self.PROFILES["default"]))

        if foco == "performance / throughput":
            profile["require_benchmark"] = True

        if foco == "segurança":
            profile["min_errors"] = max(profile["min_errors"], 3)

        if foco == "custo":
            profile["min_tips"] = max(profile["min_tips"], 2)

        return profile
