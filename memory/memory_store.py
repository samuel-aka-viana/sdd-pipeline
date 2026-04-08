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

    def __init__(self, path: str = ".memory"):
        self.base = Path(path)
        self.base.mkdir(exist_ok=True)
        self._working: dict = {}
        self._episodic   = self._load("episodic.json")
        self._procedural = self._load("procedural.json")


    def set(self, key: str, value):
        self._working[key] = value

    def get(self, key: str, default=None):
        return self._working.get(key, default)



    def log_event(self, event: str, details: dict):
        self._episodic.append({
            "ts": time.time(),
            "event": event,
            "details": details,
        })
        if len(self._episodic) > self.MAX_EPISODIC:
            self._episodic = self._episodic[-self.MAX_EPISODIC:]
        self._save("episodic.json", self._episodic)

    def get_events(self, event_type: str = None, limit: int = 10) -> list:
        events = self._episodic
        if event_type:
            events = [e for e in events if e["event"] == event_type]
        return events[-limit:]


    def learn(self, problem_pattern: str, solution: str, context: str = ""):
        # evita duplicata exata
        for p in self._procedural:
            if p["pattern"] == problem_pattern:
                p["uses"] += 1
                p["ts"] = time.time()
                self._save("procedural.json", self._procedural)
                return

        self._procedural.append({
            "pattern":  problem_pattern,
            "solution": solution,
            "context":  context,
            "uses":     1,
            "ts":       time.time(),
        })
        self._save("procedural.json", self._procedural)

    def recall(self, problem: str) -> str | None:
        """Busca solução conhecida por substring matching."""
        for proc in reversed(self._procedural):
            if proc["pattern"].lower() in problem.lower():
                proc["uses"] += 1
                self._save("procedural.json", self._procedural)
                return proc["solution"]
        return None

    def get_lessons_for_prompt(self, limit: int = 3) -> str:
        if not self._procedural:
            return ""
        ranked = sorted(
            self._procedural,
            key=lambda p: (p["uses"], p["ts"]),
            reverse=True,
        )
        top = ranked[:limit]
        lines = ["Lições de execuções anteriores (aplique estas correções):"]
        for p in top:
            lines.append(f"- Problema: {p['pattern']}")
            lines.append(f"  Solução:  {p['solution']}")
        return "\n".join(lines)

    def _load(self, filename: str) -> list:
        p = self.base / filename
        if not p.exists():
            return []
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return []

    def _save(self, filename: str, data):
        (self.base / filename).write_text(
            json.dumps(data, indent=2, ensure_ascii=False)
        )