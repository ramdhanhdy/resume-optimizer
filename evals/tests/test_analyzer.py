"""Tests for evaluation analyzer."""

import pytest
import tempfile
import os

from db.eval_db import EvalDatabase
from framework.analyzer import EvalAnalyzer
from framework.schemas import (
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


@pytest.fixture
def analyzer(db):
    """Create an EvalAnalyzer instance."""
    return EvalAnalyzer(db)


def setup_eval_data(db, num_runs=10, models=None, winner_pattern=None):
    """Helper to set up evaluation data.
    
    Args:
        db: Database instance
        num_runs: Number of stage runs to create
        models: List of model IDs (default: ["model/a", "model/b", "model/c"])
        winner_pattern: Function(run_idx) -> winner_idx, or None for alternating
    """
    if models is None:
        models = ["model/a", "model/b", "model/c"]
    
    if winner_pattern is None:
        winner_pattern = lambda idx: idx % len(models)
    
    scenario = Scenario(
        scenario_id="test_scenario",
        user_profile="Profile",
        job_posting="Job",
    )
    db.create_scenario(scenario)
    
    for run_idx in range(num_runs):
        stage_run_id = db.create_stage_run("test_scenario", "optimizer", {})
        
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
        
        winner_idx = winner_pattern(run_idx)
        judgment = Judgment(
            stage_run_id=stage_run_id,
            chosen_candidate_id=candidate_ids[winner_idx],
            evaluator_id="tester",
            scores={"relevance": 3 + (winner_idx % 3), "clarity": 4},
            tags=["good"] if winner_idx == 0 else ["ok"],
        )
        db.save_judgment(judgment)


class TestWinRates:
    """Tests for win rate computation."""

    def test_compute_win_rates_empty(self, analyzer):
        """Test win rates with no data."""
        results = analyzer.compute_win_rates("optimizer")
        
        assert results == []

    def test_compute_win_rates_equal(self, db, analyzer):
        """Test win rates with equal distribution."""
        # Each model wins once
        setup_eval_data(db, num_runs=3, models=["a", "b", "c"])
        
        results = analyzer.compute_win_rates("optimizer")
        
        assert len(results) == 3
        for r in results:
            assert r.appearances == 3
            assert r.wins == 1
            assert abs(r.win_rate - 1/3) < 0.01

    def test_compute_win_rates_dominant(self, db, analyzer):
        """Test win rates with one dominant model."""
        # Model A always wins
        setup_eval_data(
            db,
            num_runs=10,
            models=["model/a", "model/b"],
            winner_pattern=lambda _: 0,  # Always first model
        )
        
        results = analyzer.compute_win_rates("optimizer")
        
        assert len(results) == 2
        
        # Find model A
        model_a = next(r for r in results if r.model_id == "model/a")
        assert model_a.win_rate == 1.0
        assert model_a.wins == 10

    def test_win_rates_sorted(self, db, analyzer):
        """Test that win rates are sorted descending."""
        setup_eval_data(db, num_runs=6)
        
        results = analyzer.compute_win_rates("optimizer")
        
        rates = [r.win_rate for r in results]
        assert rates == sorted(rates, reverse=True)


class TestPairwisePreference:
    """Tests for pairwise preference computation."""

    def test_pairwise_no_data(self, analyzer):
        """Test pairwise with no data."""
        result = analyzer.pairwise_preference("optimizer", "a", "b")
        
        assert result.total == 0
        assert result.p_a_preferred == 0.5

    def test_pairwise_equal(self, db, analyzer):
        """Test pairwise with equal preferences."""
        setup_eval_data(
            db,
            num_runs=10,
            models=["a", "b"],
            winner_pattern=lambda idx: idx % 2,
        )
        
        result = analyzer.pairwise_preference("optimizer", "a", "b")
        
        assert result.total == 10
        assert result.a_wins == 5
        assert result.b_wins == 5
        assert abs(result.p_a_preferred - 0.5) < 0.01

    def test_pairwise_significant(self, db, analyzer):
        """Test pairwise with significant preference."""
        # A wins 9 out of 10
        setup_eval_data(
            db,
            num_runs=10,
            models=["a", "b"],
            winner_pattern=lambda idx: 0 if idx < 9 else 1,
        )
        
        result = analyzer.pairwise_preference("optimizer", "a", "b")
        
        assert result.a_wins == 9
        assert result.b_wins == 1
        assert result.p_a_preferred == 0.9
        # With 9/10 wins, should be significant
        assert result.significant is True

    def test_all_pairwise_comparisons(self, db, analyzer):
        """Test computing all pairwise comparisons."""
        setup_eval_data(db, num_runs=9, models=["a", "b", "c"])
        
        results = analyzer.all_pairwise_comparisons("optimizer")
        
        # 3 models = 3 pairs: (a,b), (a,c), (b,c)
        assert len(results) == 3


class TestBradleyTerry:
    """Tests for Bradley-Terry ranking."""

    def test_bradley_terry_empty(self, analyzer):
        """Test Bradley-Terry with no data."""
        results = analyzer.bradley_terry_ranking("optimizer")
        
        assert results == []

    def test_bradley_terry_ranking(self, db, analyzer):
        """Test Bradley-Terry produces valid ranking."""
        # A > B > C pattern
        def winner_pattern(idx):
            if idx < 5:
                return 0  # A wins
            elif idx < 8:
                return 1  # B wins
            else:
                return 2  # C wins
        
        setup_eval_data(
            db,
            num_runs=10,
            models=["a", "b", "c"],
            winner_pattern=winner_pattern,
        )
        
        results = analyzer.bradley_terry_ranking("optimizer")
        
        assert len(results) == 3
        
        # Check ranks are 1, 2, 3
        ranks = [r.rank for r in results]
        assert sorted(ranks) == [1, 2, 3]
        
        # Check strengths are positive
        for r in results:
            assert r.strength > 0

    def test_bradley_terry_convergence(self, db, analyzer):
        """Test Bradley-Terry converges with more data."""
        # Strong preference for model A
        setup_eval_data(
            db,
            num_runs=20,
            models=["a", "b"],
            winner_pattern=lambda idx: 0 if idx < 18 else 1,
        )
        
        results = analyzer.bradley_terry_ranking("optimizer")
        
        assert len(results) == 2
        
        # A should have higher strength
        model_a = next(r for r in results if r.model_id == "a")
        model_b = next(r for r in results if r.model_id == "b")
        
        assert model_a.strength > model_b.strength
        assert model_a.rank == 1
        assert model_b.rank == 2


class TestMeanScores:
    """Tests for mean score computation."""

    def test_mean_scores_empty(self, analyzer):
        """Test mean scores with no data."""
        results = analyzer.compute_mean_scores("optimizer")
        
        assert results == {}

    def test_mean_scores_computed(self, db, analyzer):
        """Test mean scores are computed correctly."""
        setup_eval_data(db, num_runs=6)
        
        results = analyzer.compute_mean_scores("optimizer")
        
        # Should have entries for winning models
        assert len(results) > 0
        
        for model, criteria in results.items():
            assert "relevance" in criteria or "clarity" in criteria
            for score in criteria.values():
                assert 1 <= score <= 5


class TestTagFrequencies:
    """Tests for tag frequency computation."""

    def test_tag_frequencies_empty(self, analyzer):
        """Test tag frequencies with no data."""
        results = analyzer.compute_tag_frequencies("optimizer")
        
        assert results == {}

    def test_tag_frequencies_computed(self, db, analyzer):
        """Test tag frequencies are computed correctly."""
        setup_eval_data(db, num_runs=6)
        
        results = analyzer.compute_tag_frequencies("optimizer")
        
        # Should have tag counts
        assert len(results) > 0
        
        for model, tags in results.items():
            for tag, count in tags.items():
                assert isinstance(count, int)
                assert count > 0


class TestReportGeneration:
    """Tests for report generation."""

    def test_generate_report(self, db, analyzer):
        """Test generating a complete report."""
        setup_eval_data(db, num_runs=10)
        
        report = analyzer.generate_report("optimizer")
        
        assert "stage_id" in report
        assert report["stage_id"] == "optimizer"
        assert "win_rates" in report
        assert "pairwise_comparisons" in report
        assert "bradley_terry" in report
        assert "mean_scores" in report
        assert "tag_frequencies" in report

    def test_report_serializable(self, db, analyzer):
        """Test that report is JSON serializable."""
        import json
        
        setup_eval_data(db, num_runs=5)
        
        report = analyzer.generate_report("optimizer")
        
        # Should not raise
        json_str = json.dumps(report)
        assert len(json_str) > 0
