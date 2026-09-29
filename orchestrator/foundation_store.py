"""Small, durable SQLite store for Phase 1 orchestration foundations."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import closing
from pathlib import Path
from typing import Iterable

from .domain import (
    Agent, AgentMessage, ApprovalRequest, ApprovalStatus, Artifact, BlackboardEntry, Event,
    ExecutionAttempt, Objective, ObjectiveCreate, ObjectiveStatus, Plan, Task, Team,
    UsageRecord, utc_now,
)
from .redact_engine import redact_text


DEFAULT_DB_PATH = Path(os.getenv("AUNITEDAI_DB_PATH", "data/aunitedai.db"))


class FoundationStore:
    def __init__(self, path: str | Path = DEFAULT_DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS objectives (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, objective TEXT NOT NULL,
                    status TEXT NOT NULL, mode TEXT NOT NULL, data TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_objectives_project ON objectives(project_id, created_at);
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL, project_id TEXT NOT NULL, objective_id TEXT,
                    task_id TEXT, agent_id TEXT, payload TEXT NOT NULL, timestamp TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_scope ON events(project_id, objective_id, sequence);
                CREATE TABLE IF NOT EXISTS blackboard_entries (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL, project_id TEXT NOT NULL, objective_id TEXT,
                    task_id TEXT, author_agent_id TEXT, content TEXT NOT NULL,
                    domains TEXT NOT NULL, evidence TEXT NOT NULL, confidence REAL,
                    relevance REAL NOT NULL, metadata TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_blackboard_scope
                    ON blackboard_entries(project_id, objective_id, type, sequence);
                CREATE TABLE IF NOT EXISTS entities (
                    kind TEXT NOT NULL, id TEXT NOT NULL, objective_id TEXT,
                    status TEXT, data TEXT NOT NULL, created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, PRIMARY KEY(kind, id)
                );
                CREATE INDEX IF NOT EXISTS idx_entities_scope
                    ON entities(kind, objective_id, created_at);
            """)

    def create_objective(self, request: ObjectiveCreate) -> Objective:
        objective = Objective(**request.model_dump())
        objective = objective.model_copy(update={
            "objective": redact_text(objective.objective),
            "constraints": [redact_text(item) for item in objective.constraints],
            "success_criteria": [redact_text(item) for item in objective.success_criteria],
        })
        data = objective.model_dump_json()
        with self._lock, closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO objectives VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (objective.id, objective.project_id, objective.objective,
                 objective.status.value, objective.mode.value, data,
                 objective.created_at.isoformat(), objective.updated_at.isoformat()),
            )
        return objective

    def get_objective(self, objective_id: str) -> Objective | None:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT data FROM objectives WHERE id = ?", (objective_id,)).fetchone()
        return Objective.model_validate_json(row["data"]) if row else None

    def update_objective_status(self, objective_id: str, status: ObjectiveStatus) -> Objective | None:
        objective = self.get_objective(objective_id)
        if objective is None:
            return None
        updated = objective.model_copy(update={"status": status, "updated_at": utc_now()})
        with self._lock, closing(self._connect()) as connection, connection:
            connection.execute(
                "UPDATE objectives SET status = ?, data = ?, updated_at = ? WHERE id = ?",
                (status.value, updated.model_dump_json(), updated.updated_at.isoformat(), objective_id),
            )
        return updated

    def list_objectives(self, project_id: str | None = None, limit: int = 100) -> list[Objective]:
        query, params = "SELECT data FROM objectives", []
        if project_id:
            query += " WHERE project_id = ?"
            params.append(project_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))
        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()
        return [Objective.model_validate_json(row["data"]) for row in rows]

    def append_event(self, event: Event) -> Event:
        payload = redact_text(json.dumps(event.payload, ensure_ascii=False))
        with self._lock, closing(self._connect()) as connection, connection:
            connection.execute(
                """INSERT INTO events
                   (id, type, project_id, objective_id, task_id, agent_id, payload, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (event.id, event.type.value, event.project_id, event.objective_id,
                 event.task_id, event.agent_id, payload, event.timestamp.isoformat()),
            )
        return event

    def list_events(self, project_id: str, objective_id: str | None = None,
                    after_sequence: int = 0, limit: int = 200) -> list[dict]:
        clauses, params = ["project_id = ?", "sequence > ?"], [project_id, after_sequence]
        if objective_id:
            clauses.append("objective_id = ?")
            params.append(objective_id)
        params.append(max(1, min(limit, 1000)))
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT * FROM events WHERE {' AND '.join(clauses)} ORDER BY sequence LIMIT ?", params
            ).fetchall()
        return [{**dict(row), "payload": json.loads(row["payload"])} for row in rows]

    def add_blackboard_entry(self, entry: BlackboardEntry) -> BlackboardEntry:
        clean_content = redact_text(entry.content)
        clean_evidence = [redact_text(item) for item in entry.evidence]
        stored = entry.model_copy(update={"content": clean_content, "evidence": clean_evidence})
        with self._lock, closing(self._connect()) as connection, connection:
            connection.execute(
                """INSERT INTO blackboard_entries
                   (id, type, project_id, objective_id, task_id, author_agent_id, content,
                    domains, evidence, confidence, relevance, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (stored.id, stored.type.value, stored.project_id, stored.objective_id,
                 stored.task_id, stored.author_agent_id, stored.content,
                 json.dumps(stored.domains), json.dumps(stored.evidence), stored.confidence,
                 stored.relevance, json.dumps(stored.metadata), stored.created_at.isoformat()),
            )
        return stored

    def save_entity(self, kind: str, entity) -> object:
        data = entity.model_dump_json()
        objective_id = getattr(entity, "objective_id", None)
        status = getattr(entity, "status", None)
        status_value = status.value if hasattr(status, "value") else status
        created = getattr(entity, "created_at", utc_now()).isoformat()
        updated = getattr(entity, "updated_at", utc_now()).isoformat()
        with self._lock, closing(self._connect()) as connection, connection:
            connection.execute(
                """INSERT INTO entities(kind, id, objective_id, status, data, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(kind, id) DO UPDATE SET status=excluded.status,
                   data=excluded.data, updated_at=excluded.updated_at""",
                (kind, entity.id, objective_id, status_value, data, created, updated),
            )
        return entity

    def list_entities(self, kind: str, model, objective_id: str | None = None) -> list:
        query, params = "SELECT data FROM entities WHERE kind = ?", [kind]
        if objective_id:
            query += " AND objective_id = ?"
            params.append(objective_id)
        query += " ORDER BY created_at"
        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()
        return [model.model_validate_json(row["data"]) for row in rows]

    def get_entity(self, kind: str, entity_id: str, model):
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT data FROM entities WHERE kind = ? AND id = ?", (kind, entity_id)
            ).fetchone()
        return model.model_validate_json(row["data"]) if row else None

    def save_plan(self, plan: Plan) -> Plan:
        self.save_entity("plan", plan)
        for task in plan.tasks:
            self.save_entity("task", task)
        return plan

    def get_plan(self, objective_id: str) -> Plan | None:
        plans = self.list_entities("plan", Plan, objective_id)
        return plans[-1] if plans else None

    def list_tasks(self, objective_id: str) -> list[Task]:
        return self.list_entities("task", Task, objective_id)

    def list_agents(self, objective_id: str) -> list[Agent]:
        return self.list_entities("agent", Agent, objective_id)

    def list_teams(self, objective_id: str) -> list[Team]:
        return self.list_entities("team", Team, objective_id)

    def list_messages(self, objective_id: str) -> list[AgentMessage]:
        return self.list_entities("message", AgentMessage, objective_id)

    def list_approvals(self, objective_id: str) -> list[ApprovalRequest]:
        return self.list_entities("approval", ApprovalRequest, objective_id)

    def list_usage(self, objective_id: str) -> list[UsageRecord]:
        return self.list_entities("usage", UsageRecord, objective_id)

    def list_attempts(self, objective_id: str) -> list[ExecutionAttempt]:
        return self.list_entities("attempt", ExecutionAttempt, objective_id)

    def list_artifacts(self, objective_id: str) -> list[Artifact]:
        return self.list_entities("artifact", Artifact, objective_id)

    def resolve_approval(self, approval_id: str, status: ApprovalStatus,
                         edited_action: str | None = None) -> ApprovalRequest | None:
        approval = self.get_entity("approval", approval_id, ApprovalRequest)
        if approval is None:
            return None
        changes = {"status": status, "resolved_at": utc_now()}
        if edited_action:
            changes["action"] = edited_action
        return self.save_entity("approval", approval.model_copy(update=changes))

    def query_blackboard(self, project_id: str, objective_id: str | None = None,
                         entry_type: str | None = None, task_id: str | None = None,
                         agent_id: str | None = None, domain: str | None = None,
                         min_confidence: float | None = None, limit: int = 100) -> list[BlackboardEntry]:
        clauses, params = ["project_id = ?"], [project_id]
        filters = (("objective_id", objective_id), ("type", entry_type),
                   ("task_id", task_id), ("author_agent_id", agent_id))
        for column, value in filters:
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        if min_confidence is not None:
            clauses.append("confidence >= ?")
            params.append(min_confidence)
        params.append(max(1, min(limit, 500)))
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT * FROM blackboard_entries WHERE {' AND '.join(clauses)} "
                "ORDER BY relevance DESC, sequence DESC LIMIT ?", params
            ).fetchall()
        entries = [self._blackboard_from_row(row) for row in rows]
        if domain:
            entries = [entry for entry in entries if domain in entry.domains]
        return entries

    @staticmethod
    def _blackboard_from_row(row: sqlite3.Row) -> BlackboardEntry:
        return BlackboardEntry.model_validate({
            "id": row["id"], "type": row["type"], "project_id": row["project_id"],
            "objective_id": row["objective_id"], "task_id": row["task_id"],
            "author_agent_id": row["author_agent_id"], "content": row["content"],
            "domains": json.loads(row["domains"]), "evidence": json.loads(row["evidence"]),
            "confidence": row["confidence"], "relevance": row["relevance"],
            "metadata": json.loads(row["metadata"]), "created_at": row["created_at"],
        })


default_foundation_store = FoundationStore()
