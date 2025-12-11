"""Tests for evaluation database layer."""

import pytest
import tempfile
import os
from datetime import datetime

from evals.db.eval_db import EvalDatabase
from evals.framework.schemas import (
    Scenario,
    CandidateOutput,
    Judgment,
)


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database = EvalDatabase(path)
    yield database
    database.close()
    os.unlink(path)


class TestScenarioOperations:
    """Tests for scenario CRUD operations."""

    def test_create_scenario(self, db):
        """Test creating a scenario."""
        scenario = Scenario(
            scenario_id="test_scenario_001",
            user_profile="Software engineer with 5 years experience",
            job_posting="Looking for senior developer",
            metadata={"source": "test"},
        )
        
        scenario_id = db.create_scenario(scenario)
        
        assert scenario_id is not None
        assert scenario_id > 0

    def test_get_scenario(self, db):
        """Test retrieving a scenario."""
        scenario = Scenario(
            scenario_id="test_scenario_002",
            user_profile="Data scientist profile",
            job_posting="ML engineer position",
        )
        db.create_scenario(scenario)
        
        retrieved = db.get_scenario("test_scenario_002")
        
        assert retrieved is not None
        assert retrieved.scenario_id == "test_scenario_002"
        assert retrieved.user_profile == "Data scientist profile"
        assert retrieved.job_posting == "ML engineer position"

    def test_get_nonexistent_scenario(self, db):
        """Test retrieving a non-existent scenario."""
        retrieved = db.get_scenario("nonexistent")
        
        assert retrieved is None

    def test_list_scenarios(self, db):
        """Test listing scenarios."""
        for i in range(5):
            scenario = Scenario(
                scenario_id=f"test_scenario_{i:03d}",
                user_profile=f"Profile {i}",
                job_posting=f"Job {i}",
            )
            db.create_scenario(scenario)
        
        scenarios = db.list_scenarios(limit=10)
        
        assert len(scenarios) == 5

    def test_scenario_metadata(self, db):
        """Test scenario metadata persistence."""
        metadata = {
            "source": "cli",
            "anonymized": True,
            "tags": ["test", "sample"],
        }
        scenario = Scenario(
            scenario_id="test_metadata",
            user_profile="Profile",
            job_posting="Job",
            metadata=metadata,
        )
        db.create_scenario(scenario)
        
        retrieved = db.get_scenario("test_metadata")
        
        assert retrieved.metadata == metadata


class TestStageRunOperations:
    """Tests for stage run operations."""

    def test_create_stage_run(self, db):
        """Test creating a stage run."""
        # Create parent scenario
        scenario = Scenario(
            scenario_id="stage_test_001",
            user_profile="Profile",
            job_posting="Job",
        )
        db.create_scenario(scenario)
        
        # Create stage run
        context = {"profile": "Profile", "job_posting": "Job"}
        stage_run_id = db.create_stage_run("stage_test_001", "optimizer", context)
        
        assert stage_run_id is not None
        assert stage_run_id > 0

    def test_get_stage_run(self, db):
        """Test retrieving a stage run."""
        scenario = Scenario(
            scenario_id="stage_test_002",
            user_profile="Profile",
            job_posting="Job",
        )
        db.create_scenario(scenario)
        
        context = {"key": "value"}
        stage_run_id = db.create_stage_run("stage_test_002", "qa", context)
        
        retrieved = db.get_stage_run(stage_run_id)
        
        assert retrieved is not None
        assert retrieved.scenario_id == "stage_test_002"
        assert retrieved.stage_id == "qa"
        assert retrieved.context == context

    def test_get_pending_stage_runs(self, db):
        """Test getting stage runs without judgments."""
        scenario = Scenario(
            scenario_id="pending_test",
            user_profile="Profile",
            job_posting="Job",
        )
        db.create_scenario(scenario)
        
        # Create stage runs
        for stage in ["optimizer", "qa"]:
            db.create_stage_run("pending_test", stage, {})
        
        pending = db.get_pending_stage_runs()
        
        assert len(pending) == 2


class TestCandidateOperations:
    """Tests for candidate output operations."""

    def test_save_candidate(self, db):
        """Test saving a candidate output."""
        scenario = Scenario(
            scenario_id="candidate_test",
            user_profile="Profile",
            job_posting="Job",
        )
        db.create_scenario(scenario)
        stage_run_id = db.create_stage_run("candidate_test", "optimizer", {})
        
        candidate = CandidateOutput(
            model_id="test/model-1",
            output_text="Generated resume content",
            latency_ms=1500,
            token_count=500,
            candidate_label="A",
        )
        
        candidate_id = db.save_candidate(stage_run_id, candidate)
        
        assert candidate_id is not None
        assert candidate_id > 0

    def test_get_candidates_for_stage_run(self, db):
        """Test retrieving candidates for a stage run."""
        scenario = Scenario(
            scenario_id="candidates_test",
            user_profile="Profile",
            job_posting="Job",
        )
        db.create_scenario(scenario)
        stage_run_id = db.create_stage_run("candidates_test", "optimizer", {})
        
        # Save multiple candidates
        for i, label in enumerate(["A", "B", "C"]):
            candidate = CandidateOutput(
                model_id=f"test/model-{i}",
                output_text=f"Output {i}",
                latency_ms=1000 + i * 100,
                token_count=400 + i * 50,
                candidate_label=label,
            )
            db.save_candidate(stage_run_id, candidate)
        
        candidates = db.get_candidates_for_stage_run(stage_run_id)
        
        assert len(candidates) == 3
        assert candidates[0].candidate_label == "A"
        assert candidates[1].candidate_label == "B"
        assert candidates[2].candidate_label == "C"


class TestJudgmentOperations:
    """Tests for judgment operations."""

    def test_save_judgment(self, db):
        """Test saving a judgment."""
        scenario = Scenario(
            scenario_id="judgment_test",
            user_profile="Profile",
            job_posting="Job",
        )
        db.create_scenario(scenario)
        stage_run_id = db.create_stage_run("judgment_test", "optimizer", {})
        
        candidate = CandidateOutput(
            model_id="test/model",
            output_text="Output",
            latency_ms=1000,
            token_count=400,
            candidate_label="A",
        )
        candidate_id = db.save_candidate(stage_run_id, candidate)
        
        judgment = Judgment(
            stage_run_id=stage_run_id,
            chosen_candidate_id=candidate_id,
            evaluator_id="tester",
            scores={"relevance": 4, "clarity": 5},
            tags=["excellent"],
            comments="Great output",
        )
        
        judgment_id = db.save_judgment(judgment)
        
        assert judgment_id is not None
        assert judgment_id > 0

    def test_get_judgment_for_stage_run(self, db):
        """Test retrieving judgment for a stage run."""
        scenario = Scenario(
            scenario_id="get_judgment_test",
            user_profile="Profile",
            job_posting="Job",
        )
        db.create_scenario(scenario)
        stage_run_id = db.create_stage_run("get_judgment_test", "optimizer", {})
        
        candidate = CandidateOutput(
            model_id="test/model",
            output_text="Output",
            latency_ms=1000,
            token_count=400,
            candidate_label="A",
        )
        candidate_id = db.save_candidate(stage_run_id, candidate)
        
        judgment = Judgment(
            stage_run_id=stage_run_id,
            chosen_candidate_id=candidate_id,
            evaluator_id="tester",
            scores={"relevance": 4},
        )
        db.save_judgment(judgment)
        
        retrieved = db.get_judgment_for_stage_run(stage_run_id)
        
        assert retrieved is not None
        assert retrieved.chosen_candidate_id == candidate_id
        assert retrieved.evaluator_id == "tester"
        assert retrieved.scores == {"relevance": 4}


class TestAnalysisQueries:
    """Tests for analysis query methods."""

    def _setup_eval_data(self, db):
        """Helper to set up evaluation data for analysis tests."""
        scenario = Scenario(
            scenario_id="analysis_test",
            user_profile="Profile",
            job_posting="Job",
        )
        db.create_scenario(scenario)
        
        # Create multiple stage runs with judgments
        models = ["model/a", "model/b", "model/c"]
        
        for run_idx in range(5):
            stage_run_id = db.create_stage_run("analysis_test", "optimizer", {})
            
            candidate_ids = []
            for i, model in enumerate(models):
                candidate = CandidateOutput(
                    model_id=model,
                    output_text=f"Output from {model}",
                    latency_ms=1000,
                    token_count=400,
                    candidate_label=chr(65 + i),
                )
                cid = db.save_candidate(stage_run_id, candidate)
                candidate_ids.append(cid)
            
            # Alternate winners
            winner_idx = run_idx % len(models)
            judgment = Judgment(
                stage_run_id=stage_run_id,
                chosen_candidate_id=candidate_ids[winner_idx],
                evaluator_id="tester",
            )
            db.save_judgment(judgment)

    def test_get_model_stats(self, db):
        """Test getting model statistics."""
        self._setup_eval_data(db)
        
        stats = db.get_model_stats("optimizer")
        
        assert len(stats) == 3
        for model in ["model/a", "model/b", "model/c"]:
            assert model in stats
            assert stats[model]["appearances"] == 5

    def test_get_judgments_for_stage(self, db):
        """Test getting judgments for a stage."""
        self._setup_eval_data(db)
        
        judgments = db.get_judgments_for_stage("optimizer")
        
        assert len(judgments) == 5
        for j in judgments:
            assert "winner_model_id" in j
            assert "all_model_ids" in j
            assert len(j["all_model_ids"]) == 3

    def test_get_head_to_head(self, db):
        """Test getting head-to-head comparisons."""
        self._setup_eval_data(db)
        
        h2h = db.get_head_to_head("optimizer", "model/a", "model/b")
        
        assert len(h2h) == 5
        for comparison in h2h:
            assert comparison["winner"] in ["model/a", "model/b", "model/c"]

    def test_get_all_pairwise(self, db):
        """Test getting all pairwise data."""
        self._setup_eval_data(db)
        
        pairwise = db.get_all_pairwise("optimizer")
        
        # Each judgment creates 2 pairwise comparisons (winner vs 2 losers)
        assert len(pairwise) == 10  # 5 judgments * 2 losers each
        for p in pairwise:
            assert "winner" in p
            assert "loser" in p
