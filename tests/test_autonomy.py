import tempfile
import unittest
from pathlib import Path

from orchestrator.autonomy import (
    AntiChaosGuard, BudgetExceededError, IntentEngine, ModelRouter,
    PermissionEngine, RecoveryEngine, WorkstationService,
)
from orchestrator.domain import (
    AgentMessage, Artifact, ApprovalStatus, AttemptStatus, ExecutionAttempt, ExecutionMode,
    MessageType, Objective, ObjectiveCreate, Permission, RiskClass, TaskStatus,
    UsageRecord,
)
from orchestrator.foundation_store import FoundationStore


class AutonomousServicesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = FoundationStore(Path(self.temp.name) / "workstation.db")
        self.service = WorkstationService(self.store)

    def tearDown(self):
        self.temp.cleanup()

    def test_intent_planning_and_dynamic_organization(self):
        objective = self.store.create_objective(ObjectiveCreate(
            objective="Research and build a tested Windows C++ desktop application"
        ))
        workspace = self.service.bootstrap(objective)
        self.assertTrue(workspace["intent"].requires_code)
        self.assertTrue(workspace["intent"].requires_research)
        self.assertIn("c++", workspace["intent"].domains)
        self.assertGreaterEqual(len(workspace["agents"]), 4)
        self.assertTrue(all(task.owner_agent_id for task in workspace["plan"].tasks))
        self.assertEqual(TaskStatus.READY, workspace["plan"].tasks[0].status)

    def test_workspace_survives_store_recreation(self):
        objective = self.store.create_objective(ObjectiveCreate(objective="Build a Python API"))
        self.service.bootstrap(objective)
        reopened = WorkstationService(FoundationStore(self.store.path)).snapshot(objective.id)
        self.assertEqual(objective.id, reopened["objective"].id)
        self.assertGreater(len(reopened["tasks"]), 0)
        self.assertGreater(len(reopened["events"]), 0)

    def test_hard_budget_is_enforced(self):
        objective = self.store.create_objective(ObjectiveCreate(objective="Analyze data", budget_usd=1.0))
        self.service.record_usage(UsageRecord(
            objective_id=objective.id, provider="local", model="test", estimated_cost=.75
        ))
        with self.assertRaises(BudgetExceededError):
            self.service.record_usage(UsageRecord(
                objective_id=objective.id, provider="cloud", model="test", estimated_cost=.30
            ))

    def test_failure_recovery_has_a_retry_limit(self):
        attempt = ExecutionAttempt(
            objective_id="o", task_id="t", status=AttemptStatus.FAILED,
            number=1, error_message="build failed",
        )
        retry = RecoveryEngine().decide(attempt, max_attempts=2)
        self.assertEqual(AttemptStatus.RETRYING, retry.status)
        exhausted = RecoveryEngine().decide(attempt.model_copy(update={"number": 2}), max_attempts=2)
        self.assertEqual(AttemptStatus.EXHAUSTED, exhausted.status)

    def test_permission_modes_and_sensitive_actions(self):
        engine = PermissionEngine()
        self.assertEqual((RiskClass.SAFE, True), engine.evaluate(Permission.READ_FILE, ExecutionMode.SUPERVISED))
        self.assertEqual((RiskClass.SENSITIVE, False), engine.evaluate(Permission.DEPLOY, ExecutionMode.AUTONOMOUS_SANDBOX))
        self.assertEqual((RiskClass.PROHIBITED, False), engine.evaluate(Permission.PURCHASE, ExecutionMode.SUPERVISED))

    def test_duplicate_message_loop_is_stopped(self):
        guard = AntiChaosGuard(duplicate_limit=1)
        first = AgentMessage(objective_id="o", type=MessageType.PROPOSAL, sender_agent_id="a", content="Use SQLite")
        duplicate = AgentMessage(objective_id="o", type=MessageType.PROPOSAL, sender_agent_id="b", content=" use   sqlite ")
        self.assertEqual("duplicate message loop detected", guard.check_message(duplicate, [first]))

    def test_model_router_honors_local_privacy(self):
        selected = ModelRouter().route(["coding"], privacy_local=True)
        self.assertTrue(selected.local)

    def test_only_real_artifacts_are_persisted(self):
        objective = self.store.create_objective(ObjectiveCreate(objective="Build a file"))
        artifact = Artifact(
            objective_id=objective.id, path="outputs/example/app.py", name="app.py",
            size_bytes=42, sha256="abc", verified=True,
        )
        self.store.save_entity("artifact", artifact)
        found = self.store.list_artifacts(objective.id)
        self.assertEqual(["outputs/example/app.py"], [item.path for item in found])
        self.assertTrue(found[0].verified)


if __name__ == "__main__":
    unittest.main()
