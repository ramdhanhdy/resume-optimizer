"""Evaluation runner for parallel candidate execution.

This module orchestrates running multiple model candidates in parallel
for a given pipeline stage, with proper randomization for blind evaluation.
"""

import asyncio
import random
import time
import uuid
import logging
from typing import Any, Callable, Dict, List, Optional, Protocol

from .schemas import (
    Scenario,
    StageEval,
    CandidateOutput,
    CandidateConfig,
)
from db.eval_db import EvalDatabase

logger = logging.getLogger(__name__)


class AgentProtocol(Protocol):
    """Protocol for agents that can be evaluated."""

    async def run_async(
        self,
        context: Dict[str, Any],
        model: str,
        **kwargs,
    ) -> str:
        """Run the agent asynchronously and return output text."""
        ...


class AgentFactory(Protocol):
    """Protocol for creating agents by stage ID."""

    def create(self, stage_id: str, model_id: str) -> AgentProtocol:
        """Create an agent for the given stage and model."""
        ...


class EvalRunner:
    """Orchestrates evaluation runs with multiple model candidates."""

    def __init__(
        self,
        db: EvalDatabase,
        agent_factory: Optional[AgentFactory] = None,
    ):
        """Initialize the evaluation runner.

        Args:
            db: Database for persisting evaluation data
            agent_factory: Factory for creating agents (optional, can use custom runner)
        """
        self.db = db
        self.agent_factory = agent_factory

    def generate_scenario_id(self) -> str:
        """Generate a unique scenario ID."""
        return f"scenario_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    def create_scenario(
        self,
        user_profile: str,
        job_posting: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Scenario:
        """Create and persist a new scenario.

        Args:
            user_profile: User's profile/resume text
            job_posting: Target job posting text
            metadata: Optional metadata (source, anonymized flag, etc.)

        Returns:
            Created Scenario object
        """
        scenario = Scenario(
            scenario_id=self.generate_scenario_id(),
            user_profile=user_profile,
            job_posting=job_posting,
            metadata=metadata or {},
        )
        scenario.id = self.db.create_scenario(scenario)
        logger.info(f"Created scenario: {scenario.scenario_id}")
        return scenario

    async def run_stage_eval(
        self,
        scenario_id: str,
        stage_id: str,
        context: Dict[str, Any],
        candidates: List[CandidateConfig],
        randomize: bool = True,
    ) -> StageEval:
        """Run evaluation for a stage with multiple candidates.

        Args:
            scenario_id: Parent scenario ID
            stage_id: Stage being evaluated
            context: Context passed to all candidates
            candidates: List of model configurations to evaluate
            randomize: Whether to randomize candidate order for blind eval

        Returns:
            StageEval with all candidate outputs
        """
        if not self.agent_factory:
            raise ValueError("AgentFactory required for run_stage_eval")

        # Create stage run record
        stage_run_id = self.db.create_stage_run(scenario_id, stage_id, context)
        logger.info(
            f"Created stage run {stage_run_id} for {stage_id} "
            f"with {len(candidates)} candidates"
        )

        # Run all candidates concurrently
        tasks = [
            self._run_candidate(stage_id, context, cfg)
            for cfg in candidates
        ]
        results: List[CandidateOutput] = await asyncio.gather(*tasks)

        # Shuffle for blind presentation
        if randomize:
            random.shuffle(results)

        # Assign blinded labels and persist
        labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, result in enumerate(results):
            result.candidate_label = labels[i]
            result.id = self.db.save_candidate(stage_run_id, result)
            result.stage_run_id = stage_run_id

        # Build and return StageEval
        stage_eval = StageEval(
            id=stage_run_id,
            scenario_id=scenario_id,
            stage_id=stage_id,
            context=context,
            candidates=results,
        )

        logger.info(
            f"Completed stage eval {stage_run_id}: "
            f"{[f'{c.candidate_label}={c.model_id}' for c in results]}"
        )
        return stage_eval

    async def _run_candidate(
        self,
        stage_id: str,
        context: Dict[str, Any],
        cfg: CandidateConfig,
    ) -> CandidateOutput:
        """Run a single candidate and capture output + metrics.

        Args:
            stage_id: Stage being evaluated
            context: Context for the agent
            cfg: Candidate configuration

        Returns:
            CandidateOutput with results
        """
        agent = self.agent_factory.create(stage_id, cfg.model_id)

        start_time = time.time()
        try:
            output = await agent.run_async(
                context=context,
                model=cfg.model_id,
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
            )
        except Exception as e:
            logger.error(f"Candidate {cfg.model_id} failed: {e}")
            output = f"[ERROR] {type(e).__name__}: {str(e)}"

        latency_ms = int((time.time() - start_time) * 1000)

        # Estimate token count (rough approximation)
        token_count = len(output.split())

        return CandidateOutput(
            model_id=cfg.model_id,
            output_text=output,
            latency_ms=latency_ms,
            token_count=token_count,
        )

    async def run_stage_eval_with_custom_runner(
        self,
        scenario_id: str,
        stage_id: str,
        context: Dict[str, Any],
        candidates: List[CandidateConfig],
        runner_fn: Callable[[CandidateConfig, Dict[str, Any]], str],
        randomize: bool = True,
    ) -> StageEval:
        """Run evaluation with a custom runner function.

        This allows using the eval framework without implementing AgentFactory.

        Args:
            scenario_id: Parent scenario ID
            stage_id: Stage being evaluated
            context: Context passed to all candidates
            candidates: List of model configurations
            runner_fn: Custom function that takes (config, context) and returns output
            randomize: Whether to randomize candidate order

        Returns:
            StageEval with all candidate outputs
        """
        stage_run_id = self.db.create_stage_run(scenario_id, stage_id, context)

        results = []
        for cfg in candidates:
            start_time = time.time()
            try:
                output = runner_fn(cfg, context)
            except Exception as e:
                logger.error(f"Candidate {cfg.model_id} failed: {e}")
                output = f"[ERROR] {type(e).__name__}: {str(e)}"

            latency_ms = int((time.time() - start_time) * 1000)

            results.append(CandidateOutput(
                model_id=cfg.model_id,
                output_text=output,
                latency_ms=latency_ms,
                token_count=len(output.split()),
            ))

        if randomize:
            random.shuffle(results)

        labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, result in enumerate(results):
            result.candidate_label = labels[i]
            result.id = self.db.save_candidate(stage_run_id, result)
            result.stage_run_id = stage_run_id

        return StageEval(
            id=stage_run_id,
            scenario_id=scenario_id,
            stage_id=stage_id,
            context=context,
            candidates=results,
        )

    def run_stage_eval_sync(
        self,
        scenario_id: str,
        stage_id: str,
        context: Dict[str, Any],
        candidates: List[CandidateConfig],
        runner_fn: Callable[[CandidateConfig, Dict[str, Any]], str],
        randomize: bool = True,
    ) -> StageEval:
        """Synchronous version of run_stage_eval_with_custom_runner.

        Useful for CLI scripts or non-async contexts.
        """
        import concurrent.futures

        def _run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.run_stage_eval_with_custom_runner(
                        scenario_id=scenario_id,
                        stage_id=stage_id,
                        context=context,
                        candidates=candidates,
                        runner_fn=runner_fn,
                        randomize=randomize,
                    )
                )
            finally:
                loop.close()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_run_in_thread)
            return future.result()

    def get_pending_evaluations(self, limit: int = 50) -> List[StageEval]:
        """Get stage evaluations that need human judgment.

        Args:
            limit: Maximum number to return

        Returns:
            List of StageEval objects without judgments
        """
        return self.db.get_pending_stage_runs(limit)
