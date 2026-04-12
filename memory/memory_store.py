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
        self.working: dict = {}
        self.episodic = self.load("episodic.json")
        self.procedural = self.load("procedural.json")


    def set(self, key: str, value):
        self.working[key] = value

    def get(self, key: str, default=None):
        return self.working.get(key, default)



    def log_event(self, event: str, details: dict):
        self.episodic.append({
            "ts": time.time(),
            "event": event,
            "details": details,
        })
        if len(self.episodic) > self.MAX_EPISODIC:
            self.episodic = self.episodic[-self.MAX_EPISODIC:]
        self.save("episodic.json", self.episodic)

    def get_events(self, event_type: str = None, limit: int = 10) -> list:
        events = self.episodic
        if event_type:
            events = [event_item for event_item in events if event_item["event"] == event_type]
        return events[-limit:]


    def learn(self, problem_pattern: str, solution: str, context: str = ""):
        # evita duplicata exata
        for procedural_item in self.procedural:
            if procedural_item["pattern"] == problem_pattern:
                procedural_item["uses"] += 1
                procedural_item["ts"] = time.time()
                self.save("procedural.json", self.procedural)
                return

        self.procedural.append({
            "pattern":  problem_pattern,
            "solution": solution,
            "context":  context,
            "uses":     1,
            "ts":       time.time(),
        })
        self.save("procedural.json", self.procedural)

    def recall(self, problem: str) -> str | None:
        """Busca solução conhecida por substring matching."""
        for procedural_item in reversed(self.procedural):
            if procedural_item["pattern"].lower() in problem.lower():
                procedural_item["uses"] += 1
                self.save("procedural.json", self.procedural)
                return procedural_item["solution"]
        return None

    def get_lessons_for_prompt(self, limit: int = 3) -> str:
        if not self.procedural:
            return ""
        ranked = sorted(
            self.procedural,
            key=lambda procedural_item: (procedural_item["uses"], procedural_item["ts"]),
            reverse=True,
        )
        top = ranked[:limit]
        lines = ["Lições de execuções anteriores (aplique estas correções):"]
        for procedural_item in top:
            lines.append(f"- Problema: {procedural_item['pattern']}")
            lines.append(f"  Solução:  {procedural_item['solution']}")
        return "\n".join(lines)

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
