import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from orchestrator.domain import (
    BlackboardEntry, BlackboardEntryType, Event, EventType, ObjectiveCreate,
    Task, TaskGraph, TaskStatus,
)
from orchestrator.foundation_store import FoundationStore


class TaskGraphTests(unittest.TestCase):
    def test_ready_tasks_respect_dependencies(self):
        first = Task(id="first", objective_id="o1", title="First", status=TaskStatus.DONE)
        second = Task(id="second", objective_id="o1", title="Second", dependencies=["first"])
        third = Task(id="third", objective_id="o1", title="Third", dependencies=["second"])
        self.assertEqual(["second"], [task.id for task in TaskGraph(tasks=[first, second, third]).ready_tasks()])

    def test_cycle_is_rejected(self):
        with self.assertRaises(ValidationError):
            TaskGraph(tasks=[
                Task(id="a", objective_id="o1", title="A", dependencies=["b"]),
                Task(id="b", objective_id="o1", title="B", dependencies=["a"]),
            ])


class FoundationStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = FoundationStore(Path(self.temp.name) / "foundation.db")

    def tearDown(self):
        self.temp.cleanup()

    def test_objective_event_and_blackboard_round_trip(self):
        objective = self.store.create_objective(ObjectiveCreate(objective="Build a reliable system"))
        self.assertEqual(objective.id, self.store.get_objective(objective.id).id)

        event = Event(type=EventType.OBJECTIVE_CREATED, project_id="default", objective_id=objective.id)
        self.store.append_event(event)
        self.assertEqual(event.id, self.store.list_events("default")[0]["id"])

        entry = BlackboardEntry(
            type=BlackboardEntryType.EVIDENCE, project_id="default", objective_id=objective.id,
            content="Tests passed", domains=["testing"], confidence=0.95,
        )
        self.store.add_blackboard_entry(entry)
        found = self.store.query_blackboard("default", domain="testing", min_confidence=0.9)
        self.assertEqual([entry.id], [item.id for item in found])

    def test_large_final_delivery_is_supported(self):
        entry = BlackboardEntry(
            type=BlackboardEntryType.TASK_RESULT,
            project_id="default",
            content="x" * 100_000,
            metadata={"kind": "delivery"},
        )
        self.store.add_blackboard_entry(entry)
        found = self.store.query_blackboard("default", entry_type="task_result")
        self.assertEqual(100_000, len(found[0].content))


if __name__ == "__main__":
    unittest.main()
