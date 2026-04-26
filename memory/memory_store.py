import json
import time
from pathlib import Path


class MemoryStore:
    """
    Memória simples em 3 camadas — JSON puro.
    working    → estado da sessão atual (RAM, some ao terminar)
    episodic   → log do que aconteceu (persistente, com rotação)
    procedural → receitas de correção que funcionaram (persistente)
    """

    MAX_EPISODIC = 500
    EPISODIC_TTL_SECONDS = 7 * 24 * 3600

    def __init__(self, path: str = ".memory"):
        self.base = Path(path)
        self.base.mkdir(exist_ok=True)
        self.working: dict = {}
        self._episodic = self.load("episodic.json")
        self._procedural = self.load("procedural.json")
        self._procedural_lower: list[tuple[str, int]] = []
        self._rebuild_procedural_index()


    def set(self, key: str, value):
        self.working[key] = value

    def get(self, key: str, default=None):
        return self.working.get(key, default)



    def log_event(self, event: str, details: dict):
        self._episodic.append({
            "ts": time.time(),
            "event": event,
            "details": details,
        })
        # TTL eviction before length cap
        now = time.time()
        self._episodic = [e for e in self._episodic if now - float(e.get("ts", 0)) <= self.EPISODIC_TTL_SECONDS]
        if len(self._episodic) > self.MAX_EPISODIC:
            self._episodic = self._episodic[-self.MAX_EPISODIC:]
        self.save("episodic.json", self._episodic)

    def get_events(self, event_type: str = None, limit: int = 10) -> list:
        events = self._episodic
        if event_type:
            events = [event_item for event_item in events if event_item["event"] == event_type]
        return events[-limit:]


    def learn(self, problem_pattern: str, solution: str, context: str = ""):
        # evita duplicata exata
        for procedural_item in self._procedural:
            if procedural_item["pattern"] == problem_pattern:
                procedural_item["uses"] += 1
                procedural_item["ts"] = time.time()
                self.save("procedural.json", self._procedural)
                self._rebuild_procedural_index()
                return

        self._procedural.append({
            "pattern":  problem_pattern,
            "solution": solution,
            "context":  context,
            "uses":     1,
            "ts":       time.time(),
        })
        self.save("procedural.json", self._procedural)
        self._rebuild_procedural_index()

    def recall(self, problem: str) -> str | None:
        """Busca solução conhecida por substring matching."""
        problem_lower = problem.lower()
        for pattern_lower, idx in self._procedural_lower:
            if pattern_lower in problem_lower:
                procedural_item = self._procedural[idx]
                procedural_item["uses"] += 1
                self.save("procedural.json", self._procedural)
                return procedural_item["solution"]
        return None

    def get_lessons_for_prompt(self, limit: int = 3) -> str:
        if not self._procedural:
            return ""
        now = time.time()
        ranked = sorted(
            self._procedural,
            key=lambda procedural_item: (
                procedural_item["uses"],
                1.0 / (1 + (now - procedural_item["ts"]) / 86400)
            ),
            reverse=True,
        )
        top = ranked[:limit]
        lines = ["Lições de execuções anteriores (aplique estas correções):"]
        for procedural_item in top:
            lines.append(f"- Problema: {procedural_item['pattern']}")
            lines.append(f"  Solução:  {procedural_item['solution']}")
        return "\n".join(lines)

    def _rebuild_procedural_index(self):
        """Build precomputed lowercase index for O(n) recall."""
        self._procedural_lower = [
            (item["pattern"].lower(), idx)
            for idx, item in enumerate(self._procedural)
        ]
        # Reverse to newest-first
        self._procedural_lower.reverse()

    def load(self, filename: str) -> list:
        p = self.base / filename
        if not p.exists():
            return []
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return []

    def save(self, filename: str, data):
        (self.base / filename).write_text(
            json.dumps(data, indent=2, ensure_ascii=False)
        )
