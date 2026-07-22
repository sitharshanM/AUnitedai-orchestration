import os
import json
import uuid
import datetime
from typing import List, Dict, Any, Optional
from .redact_engine import redact_text

KNOWLEDGE_DIR = "knowledge_base"
DECISIONS_FILE = os.path.join(KNOWLEDGE_DIR, "gstack_decisions.jsonl")
LEARNINGS_FILE = os.path.join(KNOWLEDGE_DIR, "gstack_learnings.jsonl")

os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

class DecisionMemoryStore:
    """Event-sourced Decision & Project Memory store ported from gstack."""

    def __init__(self, decisions_path: str = DECISIONS_FILE, learnings_path: str = LEARNINGS_FILE):
        self.decisions_path = decisions_path
        self.learnings_path = learnings_path

    def record_decision(
        self,
        decision: str,
        rationale: str = "",
        alternatives: str = "",
        scope: str = "repo",
        source: str = "agent",
        confidence: float = 0.9,
        workflow_role: str = "general"
    ) -> Dict[str, Any]:
        """Appends a new technical or strategic decision event to the decision log."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Sanitize text fields via redact engine to prevent secret leakages
        clean_decision = redact_text(decision)
        clean_rationale = redact_text(rationale)
        clean_alternatives = redact_text(alternatives)

        event = {
            "id": event_id,
            "kind": "decide",
            "decision": clean_decision,
            "rationale": clean_rationale,
            "alternatives_considered": clean_alternatives,
            "scope": scope,
            "source": source,
            "confidence": confidence,
            "workflow_role": workflow_role,
            "timestamp": timestamp
        }

        with open(self.decisions_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        return event

    def record_learning(self, category: str, pattern: str, pitfall_or_guideline: str) -> Dict[str, Any]:
        """Records a project pattern or pitfall to build compounding intelligence."""
        learning_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        learning = {
            "id": learning_id,
            "category": redact_text(category),
            "pattern": redact_text(pattern),
            "guideline": redact_text(pitfall_or_guideline),
            "timestamp": timestamp
        }

        with open(self.learnings_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(learning) + "\n")

        return learning

    def get_active_decisions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves past recorded active decisions."""
        if not os.path.exists(self.decisions_path):
            return []

        events = []
        try:
            with open(self.decisions_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line.strip()))
        except Exception:
            return []

        # Return latest N decisions
        return events[-limit:]

    def get_learnings(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves accumulated project learnings."""
        if not os.path.exists(self.learnings_path):
            return []

        learnings = []
        try:
            with open(self.learnings_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        learnings.append(json.loads(line.strip()))
        except Exception:
            return []

        return learnings[-limit:]

# Global singleton memory store
default_memory_store = DecisionMemoryStore()
