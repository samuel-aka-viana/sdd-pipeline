import re
import unicodedata


class ArticleSanitizer:

    def __init__(self, spec: dict):
        self.spec = spec

    def normalize_text_for_match(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text or "")
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return normalized.lower()

    def sanitize_article(self, article: str) -> str:
        patterns = self.spec["article"]["quality_rules"]["no_placeholders"]["patterns"]

        lines = article.split("\n")
        cleaned = []

        for line in lines:
            lower = line.lower().strip()
            has_placeholder = any(pattern.lower() in lower for pattern in patterns)
            if has_placeholder:
                if lower.startswith("#") and len(lower) < 80:
                    continue
                for pattern in patterns:
                    line = re.sub(re.escape(pattern), "", line, flags=re.IGNORECASE)
                if not line.strip() or line.strip() in (".", "-", "*"):
                    continue
            cleaned.append(line)

        result = "\n".join(cleaned)

        result = re.sub(r'```bash\s*\n(\s*#[^\n]*\n)*\s*```', '', result)
        result = re.sub(r'```[a-zA-Z0-9_+-]*\s*\n\s*```', '', result)

        url_rules = self.spec["article"]["quality_rules"].get("url_validation", {})
        for block_pattern in url_rules.get("block_patterns", []):
            result = re.sub(rf'https?://[^\s]*{re.escape(block_pattern)}[^\s]*', '', result)

        result = self.sanitize_question_answer_evidence_urls(result)
        return self.handle_incomplete_commands(result)

    def sanitize_question_answer_evidence_urls(self, article: str) -> str:
        reference_urls = self.extract_reference_urls(article)
        if not reference_urls:
            return article

        sanitized_lines: list[str] = []
        for raw_line in article.splitlines():
            line = raw_line
            normalized_line = self.normalize_text_for_match(line)
            if "evidencia/url:" not in normalized_line:
                sanitized_lines.append(line)
                continue

            found_urls = re.findall(r'https?://[^\s)]+', line)
            if not found_urls:
                sanitized_lines.append(line)
                continue

            has_url_outside_references = any(found_url not in reference_urls for found_url in found_urls)
            if has_url_outside_references:
                sanitized_lines.append("Evidência/URL: N/D (fora das referências coletadas)")
                continue
            sanitized_lines.append(line)

        return "\n".join(sanitized_lines)

    def extract_reference_urls(self, article: str) -> set[str]:
        reference_urls: set[str] = set()
        in_references = False
        for line in article.splitlines():
            stripped_line = line.strip()
            normalized_line = self.normalize_text_for_match(stripped_line)
            if normalized_line.startswith("## referencias"):
                in_references = True
                continue
            if in_references and stripped_line.startswith("## "):
                break
            if not in_references:
                continue
            match = re.match(r'^-\s*(https?://\S+)\s*$', stripped_line)
            if match:
                reference_urls.add(match.group(1))
        return reference_urls

    def handle_incomplete_commands(self, article: str) -> str:
        updated_lines: list[str] = []
        has_endpoint_research_note = False
        has_curl_research_note = False
        has_queue_research_note = False

        for line in article.splitlines():
            updated_line = line
            stripped_line = updated_line.strip()

            if re.search(r'--endpoint-url=\s*(?:$|--)', stripped_line):
                updated_line = ""
                has_endpoint_research_note = True

            if re.fullmatch(r'curl(?:\s+[-\w]+(?:\s+\S+)*)?\s*', stripped_line) and not re.search(
                r'https?://', stripped_line
            ):
                updated_line = ""
                has_curl_research_note = True

            if 'QueueUrl": " }' in updated_line:
                updated_line = "Resultado esperado: retorno com campo `QueueUrl` válido."
                has_queue_research_note = True

            if updated_line:
                updated_lines.append(updated_line)

        if has_endpoint_research_note:
            updated_lines.append(
                "Nota: endpoint de serviço não confirmado nas fontes coletadas; "
                "validação manual é necessária com pesquisa adicional."
            )
        if has_curl_research_note:
            updated_lines.append(
                "Nota: comando curl removido por falta de URL confirmada nas fontes; "
                "validação manual é necessária com pesquisa adicional."
            )
        if has_queue_research_note:
            updated_lines.append(
                "Nota: exemplo de QueueUrl foi normalizado; valide o payload real manualmente."
            )

        return "\n".join(updated_lines)
