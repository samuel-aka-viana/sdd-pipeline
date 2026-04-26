import os
from dataclasses import dataclass


@dataclass
class LLMRuntimeConfig:
    provider_mode: str
    provider_engine: str
    provider_config: dict
    provider_configs: dict[str, dict]
    models: dict[str, str]
    model_providers: dict[str, str]


class ProviderConfigResolver:
    ROLES = ("researcher", "analyst", "writer", "critic")
    PROVIDER_ALIASES = {
        "ollama": "ollama_local",
        "local": "ollama_local",
        "ollama_local": "ollama_local",
        "openrouter": "openrouter_free",
        "openrouter_free": "openrouter_free",
    }

    def __init__(self, spec: dict):
        self.spec = spec

    def build_runtime(self) -> LLMRuntimeConfig:
        provider_mode = self.resolve_mode()
        provider_engine = "openrouter" if provider_mode == "openrouter_free" else "ollama"
        provider_config = self.resolve_config(provider_mode, provider_engine)
        models = self.resolve_models()
        model_providers = self.resolve_model_providers()
        provider_configs = {
            "openrouter": self.resolve_config("openrouter_free", "openrouter"),
            "ollama": self.resolve_config("ollama_local", "ollama"),
        }
        return LLMRuntimeConfig(
            provider_mode=provider_mode,
            provider_engine=provider_engine,
            provider_config=provider_config,
            provider_configs=provider_configs,
            models=models,
            model_providers=model_providers,
        )

    def resolve_mode(self) -> str:
        env_provider = os.getenv("LLM_PROVIDER")
        llm_conf = self.spec.get("llm", {})
        raw_provider = env_provider or llm_conf.get("provider") or "ollama_local"
        provider_mode = self.PROVIDER_ALIASES.get(raw_provider.strip().lower())
        if not provider_mode:
            supported = ", ".join(sorted(set(self.PROVIDER_ALIASES.values())))
            raise RuntimeError(
                f"LLM_PROVIDER inválido: {raw_provider}. Use um de: {supported}"
            )
        return provider_mode

    def resolve_models(self) -> dict[str, str]:
        spec_models = self.spec.get("models", {})
        models: dict[str, str] = {}
        for role in self.ROLES:
            env_key = f"LLM_MODEL_{role.upper()}"
            model = os.getenv(env_key) or spec_models.get(role)
            if isinstance(model, dict):
                model = model.get("model")
            if not model:
                raise RuntimeError(
                    f"Modelo ausente para role '{role}'. Defina {env_key} no .env."
                )
            models[role] = str(model).strip()
        return models

    def resolve_model_providers(self) -> dict[str, str]:
        providers = self.spec.get("model_providers")
        if isinstance(providers, dict) and providers:
            return {role: str(providers.get(role, "ollama")).strip().lower() for role in self.ROLES}

        spec_models = self.spec.get("models", {})
        resolved: dict[str, str] = {}
        for role in self.ROLES:
            model_config = spec_models.get(role)
            if isinstance(model_config, dict) and model_config.get("provider"):
                resolved[role] = str(model_config["provider"]).strip().lower()
            else:
                resolved[role] = "openrouter" if self.resolve_mode() == "openrouter_free" else "ollama"
        return resolved

    def resolve_config(self, provider_mode: str, provider_engine: str) -> dict:
        llm_conf = self.spec.get("llm", {})
        providers = llm_conf.get("providers", {})
        conf = dict(providers.get(provider_engine, {}))

        if provider_engine == "openrouter":
            conf["base_url"] = (
                os.getenv("OPENROUTER_BASE_URL")
                or conf.get("base_url")
                or "https://openrouter.ai/api/v1"
            ).rstrip("/")
            conf["api_key_env"] = os.getenv("OPENROUTER_API_KEY_ENV") or conf.get(
                "api_key_env", "OPENROUTER_API_KEY"
            )
            return conf

        conf["base_url"] = (
            os.getenv("OLLAMA_LOCAL_BASE_URL")
            or os.getenv("OLLAMA_BASE_URL")
            or conf.get("base_url")
            or "http://localhost:11434"
        ).rstrip("/")
        return conf

    def resolve_local_fallback_model(self, role: str, primary_model: str) -> str:
        role_env = os.getenv(f"LLM_MODEL_{role.upper()}_FALLBACK_LOCAL")
        global_env = os.getenv("LLM_MODEL_FALLBACK_LOCAL")
        if role_env:
            return role_env.strip()
        if global_env:
            return global_env.strip()
        if "/" not in primary_model:
            return primary_model
        return "qwen2.5:14b"
