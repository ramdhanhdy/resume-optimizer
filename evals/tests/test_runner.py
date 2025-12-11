"""Tests for evaluation runner."""

import pytest
import tempfile
import os
import asyncio

from evals.db.eval_db import EvalDatabase
from evals.framework.runner import EvalRunner
from evals.framework.schemas import CandidateConfig


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database = EvalDatabase(path)
    yield database
    database.close()
    os.unlink(path)


@pytest.fixture
def runner(db):
    """Create an EvalRunner instance."""
    return EvalRunner(db)


class TestEvalRunner:
    """Tests for EvalRunner class."""

    def test_generate_scenario_id(self, runner):
        """Test scenario ID generation."""
        id1 = runner.generate_scenario_id()
        id2 = runner.generate_scenario_id()
        
        assert id1.startswith("scenario_")
        assert id2.startswith("scenario_")
        assert id1 != id2

    def test_create_scenario(self, runner):
        """Test scenario creation."""
        scenario = runner.create_scenario(
            user_profile="Test profile",
            job_posting="Test job posting",
            metadata={"source": "test"},
        )
        
        assert scenario.scenario_id is not None
        assert scenario.user_profile == "Test profile"
        assert scenario.job_posting == "Test job posting"
        assert scenario.metadata == {"source": "test"}
        assert scenario.id is not None

    def test_run_stage_eval_sync(self, runner):
        """Test synchronous stage evaluation with custom runner."""
        scenario = runner.create_scenario(
            user_profile="Profile",
            job_posting="Job",
        )
        
        candidates = [
            CandidateConfig(model_id="model/a"),
            CandidateConfig(model_id="model/b"),
        ]
        
        def mock_runner(cfg, context):
            return f"Output from {cfg.model_id}"
        
        stage_eval = runner.run_stage_eval_sync(
            scenario_id=scenario.scenario_id,
            stage_id="optimizer",
            context={"profile": "Profile", "job_posting": "Job"},
            candidates=candidates,
            runner_fn=mock_runner,
            randomize=False,
        )
        
        assert stage_eval.id is not None
        assert stage_eval.stage_id == "optimizer"
        assert len(stage_eval.candidates) == 2

    def test_candidate_labels_assigned(self, runner):
        """Test that candidate labels are assigned correctly."""
        scenario = runner.create_scenario(
            user_profile="Profile",
            job_posting="Job",
        )
        
        candidates = [
            CandidateConfig(model_id=f"model/{i}")
            for i in range(5)
        ]
        
        def mock_runner(cfg, context):
            return f"Output from {cfg.model_id}"
        
        stage_eval = runner.run_stage_eval_sync(
            scenario_id=scenario.scenario_id,
            stage_id="optimizer",
            context={},
            candidates=candidates,
            runner_fn=mock_runner,
            randomize=False,
        )
        
        labels = [c.candidate_label for c in stage_eval.candidates]
        assert labels == ["A", "B", "C", "D", "E"]

    def test_randomization(self, runner):
        """Test that candidates are randomized when requested."""
        scenario = runner.create_scenario(
            user_profile="Profile",
            job_posting="Job",
        )
        
        candidates = [
            CandidateConfig(model_id=f"model/{i}")
            for i in range(10)
        ]
        
        def mock_runner(cfg, context):
            return f"Output from {cfg.model_id}"
        
        # Run multiple times and check if order varies
        orders = []
        for _ in range(5):
            stage_eval = runner.run_stage_eval_sync(
                scenario_id=scenario.scenario_id,
                stage_id="optimizer",
                context={},
                candidates=candidates,
                runner_fn=mock_runner,
                randomize=True,
            )
            order = [c.model_id for c in stage_eval.candidates]
            orders.append(tuple(order))
        
        # With 10 candidates, it's extremely unlikely all 5 runs have same order
        unique_orders = set(orders)
        assert len(unique_orders) > 1, "Randomization should produce different orders"

    def test_error_handling_in_runner(self, runner):
        """Test that errors in runner function are captured."""
        scenario = runner.create_scenario(
            user_profile="Profile",
            job_posting="Job",
        )
        
        candidates = [
            CandidateConfig(model_id="model/good"),
            CandidateConfig(model_id="model/bad"),
        ]
        
        def mock_runner(cfg, context):
            if "bad" in cfg.model_id:
                raise ValueError("Simulated error")
            return "Good output"
        
        stage_eval = runner.run_stage_eval_sync(
            scenario_id=scenario.scenario_id,
            stage_id="optimizer",
            context={},
            candidates=candidates,
            runner_fn=mock_runner,
            randomize=False,
        )
        
        # Both candidates should be present
        assert len(stage_eval.candidates) == 2
        
        # Find the bad candidate
        bad_candidate = next(
            c for c in stage_eval.candidates if "bad" in c.model_id
        )
        assert "[ERROR]" in bad_candidate.output_text

    def test_get_pending_evaluations(self, runner, db):
        """Test getting pending evaluations."""
        # Create scenarios with stage runs
        for i in range(3):
            scenario = runner.create_scenario(
                user_profile=f"Profile {i}",
                job_posting=f"Job {i}",
            )
            db.create_stage_run(scenario.scenario_id, "optimizer", {})
        
        pending = runner.get_pending_evaluations()
        
        assert len(pending) == 3

    def test_latency_captured(self, runner):
        """Test that latency is captured correctly."""
        import time
        
        scenario = runner.create_scenario(
            user_profile="Profile",
            job_posting="Job",
        )
        
        candidates = [CandidateConfig(model_id="model/slow")]
        
        def slow_runner(cfg, context):
            time.sleep(0.1)  # 100ms delay
            return "Output"
        
        stage_eval = runner.run_stage_eval_sync(
            scenario_id=scenario.scenario_id,
            stage_id="optimizer",
            context={},
            candidates=candidates,
            runner_fn=slow_runner,
            randomize=False,
        )
        
        assert stage_eval.candidates[0].latency_ms >= 100


class TestCandidateConfig:
    """Tests for CandidateConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CandidateConfig(model_id="test/model")
        
        assert config.model_id == "test/model"
        assert config.prompt_version == "default"
        assert config.temperature == 0.65
        assert config.max_tokens == 32000

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CandidateConfig(
            model_id="test/model",
            prompt_version="v2",
            temperature=0.3,
            max_tokens=16000,
        )
        
        assert config.prompt_version == "v2"
        assert config.temperature == 0.3
        assert config.max_tokens == 16000

    def test_to_dict(self):
        """Test serialization to dict."""
        config = CandidateConfig(model_id="test/model")
        
        d = config.to_dict()
        
        assert d["model_id"] == "test/model"
        assert "temperature" in d
        assert "max_tokens" in d
