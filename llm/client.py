import os
from dataclasses import dataclass

import requests
import yaml
from httpx import TimeoutException
from pathlib import Path


@dataclass
class LLMResponse:
    response: str


@dataclass
class LLMRuntimeConfig:
    provider_mode: str
    provider_engine: str
    provider_config: dict
    models: dict[str, str]


class LLMClient:
    ROLES = ("researcher", "analyst", "writer", "critic")
    PROVIDER_ALIASES = {
        "ollama": "ollama_local",
        "local": "ollama_local",
        "ollama_local": "ollama_local",
        "ollama_cloud": "ollama_cloud",
        "cloud": "ollama_cloud",
        "openrouter": "openrouter_free",
        "openrouter_free": "openrouter_free",
    }

    def __init__(self, spec_path: str = "spec/article_spec.yaml"):
        self.spec = yaml.safe_load(Path(spec_path).read_text())
        self.runtime = self.build_runtime()
        self.provider = self.runtime.provider_engine

    def generate(
        self,
        *,
        role: str,
        model: str,
        prompt: str,
        temperature: float,
        num_ctx: int | None = None,
        timeout: int | None = None,
    ) -> LLMResponse:
        errors_by_provider = []

        if self.runtime.provider_mode == "openrouter_free":
            try:
                return self.generate_openrouter(
                    role=role,
                    model=model,
                    prompt=prompt,
                    temperature=temperature,
                    timeout=timeout,
                )
            except (RuntimeError, TimeoutException) as openrouter_error:
                errors_by_provider.append(f"openrouter: {openrouter_error}")

            fallback_from_cloud = self.try_ollama_cloud_fallback(
                role=role,
                prompt=prompt,
                temperature=temperature,
                num_ctx=num_ctx,
                timeout=timeout,
                errors_by_provider=errors_by_provider,
            )
            if fallback_from_cloud:
                return fallback_from_cloud

            fallback_from_local = self.try_ollama_local_fallback(
                role=role,
                primary_model=model,
                prompt=prompt,
                temperature=temperature,
                num_ctx=num_ctx,
                timeout=timeout,
                errors_by_provider=errors_by_provider,
            )
            if fallback_from_local:
                return fallback_from_local

        elif self.runtime.provider_mode == "ollama_cloud":
            cloud_result = self.try_ollama_cloud_fallback(
                role=role,
                prompt=prompt,
                temperature=temperature,
                num_ctx=num_ctx,
                timeout=timeout,
                errors_by_provider=errors_by_provider,
                primary_model=model,
            )
            if cloud_result:
                return cloud_result

            local_result = self.try_ollama_local_fallback(
                role=role,
                primary_model=model,
                prompt=prompt,
                temperature=temperature,
                num_ctx=num_ctx,
                timeout=timeout,
                errors_by_provider=errors_by_provider,
            )
            if local_result:
                return local_result

        else:
            local_result = self.try_ollama_local_fallback(
                role=role,
                primary_model=model,
                prompt=prompt,
                temperature=temperature,
                num_ctx=num_ctx,
                timeout=timeout,
                errors_by_provider=errors_by_provider,
            )
            if local_result:
                return local_result

        error_details = " | ".join(errors_by_provider) if errors_by_provider else "falha desconhecida"
        raise RuntimeError(f"Todos os provedores de LLM falharam: {error_details}")

    def model_for_role(self, role: str) -> str:
        model = self.runtime.models.get(role)
        if not model:
            raise RuntimeError(f"Modelo não configurado para role: {role}")
        return model

    def build_runtime(self) -> LLMRuntimeConfig:
        provider_mode = self.resolve_provider_mode()
        provider_engine = "openrouter" if provider_mode == "openrouter_free" else "ollama"
        provider_config = self.resolve_provider_config(provider_mode, provider_engine)
        models = self.resolve_models()
        return LLMRuntimeConfig(
            provider_mode=provider_mode,
            provider_engine=provider_engine,
            provider_config=provider_config,
            models=models,
        )

    def resolve_provider_mode(self) -> str:
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
            if not model:
                raise RuntimeError(
                    f"Modelo ausente para role '{role}'. Defina {env_key} no .env."
                )
            models[role] = str(model).strip()

        return models

    def resolve_provider_config(self, provider_mode: str, provider_engine: str) -> dict:
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
                "api_key_env",
                "OPENROUTER_API_KEY",
            )
            return conf

        if provider_mode == "ollama_cloud":
            conf["base_url"] = (
                os.getenv("OLLAMA_CLOUD_BASE_URL")
                or os.getenv("OLLAMA_BASE_URL")
                or conf.get("cloud_base_url")
                or "https://ollama.com"
            ).rstrip("/")
            cloud_api_key = (
                os.getenv("OLLAMA_CLOUD_API_KEY")
                or os.getenv("OLLAMA_API_KEY")
                or ""
            ).strip()
            if cloud_api_key:
                conf["api_key"] = cloud_api_key
            return conf

        conf["base_url"] = (
            os.getenv("OLLAMA_LOCAL_BASE_URL")
            or os.getenv("OLLAMA_BASE_URL")
            or conf.get("base_url")
            or "http://localhost:11434"
        ).rstrip("/")
        return conf

    def generate_ollama(
        self,
        *,
        model: str,
        prompt: str,
        temperature: float,
        num_ctx: int | None,
        timeout: int | None,
        provider_config: dict | None = None,
    ) -> LLMResponse:
        conf = provider_config or self.runtime.provider_config
        base_url = conf.get("base_url", "http://localhost:11434").rstrip("/")
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if num_ctx:
            payload["options"]["num_ctx"] = num_ctx
        headers = {}
        if conf.get("api_key"):
            headers["Authorization"] = f"Bearer {conf['api_key']}"

        try:
            resp = requests.post(
                f"{base_url}/api/generate",
                json=payload,
                headers=headers or None,
                timeout=timeout,
            )
            resp.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise TimeoutException("Ollama request timed out") from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"Erro ao chamar Ollama: {exc}") from exc

        data = resp.json()
        return LLMResponse(response=data.get("response", "").strip())

    def generate_openrouter(
        self,
        *,
        role: str,
        model: str,
        prompt: str,
        temperature: float,
        timeout: int | None,
    ) -> LLMResponse:
        conf = self.runtime.provider_config
        base_url = conf.get("base_url", "https://openrouter.ai/api/v1").rstrip("/")
        api_key_env = conf.get("api_key_env", "OPENROUTER_API_KEY")
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Variável de ambiente ausente: {api_key_env}"
            )

        extra_body = {**conf.get("extra_body", {})}
        extra_body.update(conf.get("extra_body_by_role", {}).get(role, {}))

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        if conf.get("site_url"):
            headers["HTTP-Referer"] = conf["site_url"]
        if conf.get("app_name"):
            headers["X-Title"] = conf["app_name"]

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if extra_body:
            payload.update(extra_body)

        try:
            resp = requests.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            resp.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise TimeoutException("OpenRouter request timed out") from exc
        except requests.exceptions.RequestException as exc:
            detail = ""
            if exc.response is not None:
                detail = f" | resposta: {exc.response.text[:300]}"
            raise RuntimeError(f"Erro ao chamar OpenRouter: {exc}{detail}") from exc

        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            content = "\n".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            )
        return LLMResponse(response=str(content).strip())

    def try_ollama_cloud_fallback(
        self,
        *,
        role: str,
        prompt: str,
        temperature: float,
        num_ctx: int | None,
        timeout: int | None,
        errors_by_provider: list[str],
        primary_model: str | None = None,
    ) -> LLMResponse | None:
        cloud_model = self.resolve_cloud_fallback_model(role, primary_model)
        cloud_config = self.resolve_provider_config("ollama_cloud", "ollama")
        try:
            return self.generate_ollama(
                model=cloud_model,
                prompt=prompt,
                temperature=temperature,
                num_ctx=num_ctx,
                timeout=timeout,
                provider_config=cloud_config,
            )
        except (RuntimeError, TimeoutException) as cloud_error:
            errors_by_provider.append(f"ollama_cloud({cloud_model}): {cloud_error}")
            return None

    def try_ollama_local_fallback(
        self,
        *,
        role: str,
        primary_model: str,
        prompt: str,
        temperature: float,
        num_ctx: int | None,
        timeout: int | None,
        errors_by_provider: list[str],
    ) -> LLMResponse | None:
        local_model = self.resolve_local_fallback_model(role, primary_model)
        local_config = self.resolve_provider_config("ollama_local", "ollama")
        try:
            return self.generate_ollama(
                model=local_model,
                prompt=prompt,
                temperature=temperature,
                num_ctx=num_ctx,
                timeout=timeout,
                provider_config=local_config,
            )
        except (RuntimeError, TimeoutException) as local_error:
            errors_by_provider.append(f"ollama_local({local_model}): {local_error}")
            return None

    def resolve_cloud_fallback_model(self, role: str, primary_model: str | None) -> str:
        role_env = os.getenv(f"LLM_MODEL_{role.upper()}_FALLBACK_CLOUD")
        global_env = os.getenv("LLM_MODEL_FALLBACK_CLOUD")
        if role_env:
            return role_env.strip()
        if global_env:
            return global_env.strip()
        if primary_model and ":cloud" in primary_model:
            return primary_model
        return "glm5.1:cloud"

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
