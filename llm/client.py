import logging
import os
from pathlib import Path

import requests
import yaml
from httpx import TimeoutException
from pydantic import BaseModel
from typing import TypeVar

from llm.circuit_breaker import (
    CircuitBreakerRegistry,
    CircuitOpenError,
    classify_http_failure,
)
from llm.fallback import try_provider
from llm.provider_config import LLMRuntimeConfig, ProviderConfigResolver
from llm.structured import (
    StructuredOutputError,
    build_repair_prompt,
    build_schema_hint,
    parse_response,
)
from llm.token_counter import count_tokens

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class LLMResponse:
    def __init__(self, response: str):
        self.response = response


class LLMClient:
    def __init__(self, spec_path: str = "spec/article_spec.yaml"):
        self.spec = yaml.safe_load(Path(spec_path).read_text())
        self._resolver = ProviderConfigResolver(self.spec)
        self.runtime: LLMRuntimeConfig = self._resolver.build_runtime()
        self.provider = self.runtime.provider_engine
        self.circuit_breaker = CircuitBreakerRegistry()

    def generate_cached(
        self,
        *,
        role: str,
        model: str,
        stable_prefix: str,
        volatile_suffix: str,
        temperature: float,
        num_ctx: int | None = None,
        timeout: int | None = None,
    ) -> LLMResponse:
        """Variante de generate com cache breakpoint entre prefix e suffix.

        OpenRouter: usa cache_control=ephemeral no primeiro segmento.
        Ollama: concatena (KV cache automático em prefix byte-idêntico).
        """
        if not volatile_suffix:
            return self.generate(
                role=role, model=model, prompt=stable_prefix,
                temperature=temperature, num_ctx=num_ctx, timeout=timeout,
            )
        if self.runtime.provider_mode == "openrouter_free" and "/" in model:
            result = try_provider(
                lambda: self.generate_openrouter(
                    role=role, model=model, prompt=stable_prefix,
                    temperature=temperature, timeout=timeout,
                    volatile_suffix=volatile_suffix,
                ),
                provider_id="openrouter", role=role,
            )
            if result:
                return result
        return self.generate(
            role=role, model=model, prompt=stable_prefix + volatile_suffix,
            temperature=temperature, num_ctx=num_ctx, timeout=timeout,
        )

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
        errors_by_provider: list[str] = []

        if self.runtime.provider_mode == "openrouter_free" and "/" in model:
            result = try_provider(
                lambda: self.generate_openrouter(
                    role=role, model=model, prompt=prompt,
                    temperature=temperature, timeout=timeout,
                ),
                provider_id="openrouter", role=role, errors=errors_by_provider,
            )
            if result:
                return result

        local_result = self._try_ollama_local(
            role=role, primary_model=model, prompt=prompt,
            temperature=temperature, num_ctx=num_ctx, timeout=timeout,
            errors=errors_by_provider,
        )
        if local_result:
            return local_result

        error_details = " | ".join(errors_by_provider) if errors_by_provider else "falha desconhecida"
        raise RuntimeError(f"Todos os provedores de LLM falharam: {error_details}")

    def generate_structured(
        self,
        *,
        role: str,
        model: str,
        prompt: str,
        schema: type[T],
        temperature: float,
        num_ctx: int | None = None,
        timeout: int | None = None,
        max_repairs: int = 1,
    ) -> T:
        schema_hint = build_schema_hint(schema)
        full_prompt = (
            f"{prompt}\n\n"
            "Responda APENAS com um objeto JSON válido conforme o schema abaixo. "
            "Sem texto adicional, sem markdown, sem ```json fences.\n\n"
            f"Schema JSON:\n{schema_hint}"
        )

        attempt_prompt = full_prompt
        last_raw = ""
        last_error: Exception | None = None

        for attempt in range(max_repairs + 1):
            response = self.generate(
                role=role, model=model, prompt=attempt_prompt,
                temperature=temperature, num_ctx=num_ctx, timeout=timeout,
            )
            last_raw = response.response
            try:
                return parse_response(last_raw, schema)
            except StructuredOutputError as exc:
                last_error = exc
                logger.warning(
                    "[generate_structured] role=%s schema=%s tentativa=%d falhou: %s",
                    role, schema.__name__, attempt + 1, exc,
                )
                if attempt == max_repairs:
                    break
                attempt_prompt = build_repair_prompt(full_prompt, last_raw, str(exc))

        raise StructuredOutputError(
            f"generate_structured falhou após {max_repairs + 1} tentativas para {schema.__name__}: {last_error}"
        )

    def _log_token_usage(
        self,
        provider_id: str,
        model: str,
        prompt: str,
        response: str,
        response_data: dict | None = None,
    ) -> None:
        usage = (response_data or {}).get("usage") if response_data else None
        if usage:
            input_tokens = int(usage.get("prompt_tokens", 0) or 0)
            output_tokens = int(usage.get("completion_tokens", 0) or 0)
            source = "provider"
        else:
            input_tokens = count_tokens(prompt, model)
            output_tokens = count_tokens(response, model)
            source = "tiktoken_estimate"
        logger.info(
            "[tokens] provider=%s model=%s in=%d out=%d total=%d source=%s",
            provider_id, model, input_tokens, output_tokens,
            input_tokens + output_tokens, source,
        )

    def model_for_role(self, role: str) -> str:
        model = self.runtime.models.get(role)
        if not model:
            raise RuntimeError(f"Modelo não configurado para role: {role}")
        return model

    def resolve_fast_model(self, role: str) -> str:
        """Modelo menor opcional para sub-tasks da role (classificação/filtragem).

        Lookup: env LLM_MODEL_<ROLE>_FAST > spec.models.<role>_fast > role default.
        """
        env_value = os.getenv(f"LLM_MODEL_{role.upper()}_FAST")
        if env_value:
            return env_value.strip()
        spec_models = self.spec.get("models", {})
        spec_value = spec_models.get(f"{role}_fast")
        if spec_value:
            return str(spec_value).strip()
        return self.model_for_role(role)

    def generate_ollama(
        self,
        *,
        model: str,
        prompt: str,
        temperature: float,
        num_ctx: int | None,
        timeout: int | None,
        provider_config: dict | None = None,
        provider_id: str = "ollama",
    ) -> LLMResponse:
        conf = provider_config or self.runtime.provider_config
        base_url = conf.get("base_url", "http://localhost:11434").rstrip("/")
        self.circuit_breaker.check(provider_id)
        payload: dict = {
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
            self.circuit_breaker.record_failure(provider_id, "timeout")
            raise TimeoutException("Ollama request timed out") from exc
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            kind = classify_http_failure(status, type(exc).__name__)
            self.circuit_breaker.record_failure(provider_id, kind)
            raise RuntimeError(f"Erro HTTP {status} ao chamar Ollama: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            self.circuit_breaker.record_failure(provider_id, "error")
            raise RuntimeError(f"Erro ao chamar Ollama: {exc}") from exc

        self.circuit_breaker.record_success(provider_id)
        data = resp.json()
        response_text = data.get("response", "").strip()
        self._log_token_usage(provider_id, model, prompt, response_text)
        return LLMResponse(response=response_text)

    def generate_openrouter(
        self,
        *,
        role: str,
        model: str,
        prompt: str,
        temperature: float,
        timeout: int | None,
        volatile_suffix: str = "",
    ) -> LLMResponse:
        conf = self.runtime.provider_config
        base_url = conf.get("base_url", "https://openrouter.ai/api/v1").rstrip("/")
        api_key_env = conf.get("api_key_env", "OPENROUTER_API_KEY")
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(f"Variável de ambiente ausente: {api_key_env}")

        provider_id = "openrouter"
        self.circuit_breaker.check(provider_id)

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

        if volatile_suffix:
            content: object = [
                {"type": "text", "text": prompt, "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": volatile_suffix},
            ]
        else:
            content = prompt

        payload: dict = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
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
            self.circuit_breaker.record_failure(provider_id, "timeout")
            raise TimeoutException("OpenRouter request timed out") from exc
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            kind = classify_http_failure(status, type(exc).__name__)
            self.circuit_breaker.record_failure(provider_id, kind)
            detail = f" | resposta: {exc.response.text[:300]}" if exc.response is not None else ""
            raise RuntimeError(f"Erro HTTP {status} ao chamar OpenRouter: {exc}{detail}") from exc
        except requests.exceptions.RequestException as exc:
            self.circuit_breaker.record_failure(provider_id, "error")
            detail = f" | resposta: {exc.response.text[:300]}" if exc.response is not None else ""
            raise RuntimeError(f"Erro ao chamar OpenRouter: {exc}{detail}") from exc

        self.circuit_breaker.record_success(provider_id)
        data = resp.json()
        raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if isinstance(raw_content, list):
            raw_content = "\n".join(
                part.get("text", "")
                for part in raw_content
                if isinstance(part, dict)
            )
        response_text = str(raw_content).strip()
        full_prompt = prompt + (volatile_suffix or "")
        self._log_token_usage(provider_id, model, full_prompt, response_text, response_data=data)
        return LLMResponse(response=response_text)

    def _try_ollama_local(
        self,
        *,
        role: str,
        primary_model: str,
        prompt: str,
        temperature: float,
        num_ctx: int | None,
        timeout: int | None,
        errors: list[str],
    ) -> LLMResponse | None:
        local_model = self._resolver.resolve_local_fallback_model(role, primary_model)
        local_config = self._resolver.resolve_config("ollama_local", "ollama")
        logger.info("[LLM fallback] Tentando Ollama Local role=%s model=%s", role, local_model)
        result = try_provider(
            lambda: self.generate_ollama(
                model=local_model, prompt=prompt, temperature=temperature,
                num_ctx=num_ctx, timeout=timeout,
                provider_config=local_config, provider_id="ollama_local",
            ),
            provider_id="ollama_local", role=role, errors=errors,
        )
        if result:
            logger.info("[LLM fallback] Ollama Local OK role=%s model=%s", role, local_model)
        return result
