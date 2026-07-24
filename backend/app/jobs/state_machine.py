"""
app/jobs/state_machine.py — PipelineStateMachine

Manages legal stage transitions, execution ordering, and resume logic.
The JobExecutor delegates all transition decisions to this class; it
never performs state manipulation directly.

Design invariants:
  - Stages execute in the declared order.
  - No stage may be skipped unless it was already completed (resume mode).
  - The machine is deterministic: given the same inputs it always produces
    the same stage sequence.
  - The executor asks the machine which stage to run next; the machine
    never calls back into the executor.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict

from app.jobs.stage import PipelineStage


@dataclass
class TransitionResult:
    """Result of asking the state machine for the next stage."""
    next_stage: Optional[PipelineStage]
    is_terminal: bool        # True when the pipeline is finished
    resume_from_checkpoint: bool  # True when the stage has prior checkpoint data


class StageTransitionError(Exception):
    """Raised when an illegal transition is attempted."""


class PipelineStateMachine:
    """
    Ordered, resumable pipeline state machine.

    Usage:
        machine = PipelineStateMachine(stages, last_successful_stage="convert")
        result = machine.next()
        while not result.is_terminal:
            run(result.next_stage, resume=result.resume_from_checkpoint)
            machine.advance(success=True)
            result = machine.next()
    """

    def __init__(
        self,
        stages: List[PipelineStage],
        last_successful_stage: Optional[str] = None,
        checkpoints: Optional[Dict[str, dict]] = None,
    ) -> None:
        if not stages:
            raise StageTransitionError("Pipeline must have at least one stage.")
        self._stages = stages
        self._stage_index: Dict[str, int] = {
            s.stage_name(): i for i, s in enumerate(stages)
        }
        self._checkpoints: Dict[str, dict] = checkpoints or {}
        self._current_pos: int = self._find_resume_position(last_successful_stage)
        self._completed: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def next(self) -> TransitionResult:
        """Return the next stage to execute, or a terminal result."""
        if self._completed or self._current_pos >= len(self._stages):
            return TransitionResult(next_stage=None, is_terminal=True, resume_from_checkpoint=False)

        stage = self._stages[self._current_pos]
        has_checkpoint = stage.stage_name() in self._checkpoints and stage.can_resume()
        return TransitionResult(
            next_stage=stage,
            is_terminal=False,
            resume_from_checkpoint=has_checkpoint,
        )

    def advance(self, success: bool) -> None:
        """
        Record the outcome of the current stage and advance the pointer.

        :param success: True if the stage completed successfully.
        :raises StageTransitionError: If called when pipeline is already terminal.
        """
        if self._completed:
            raise StageTransitionError("Pipeline is already terminal; cannot advance.")
        if self._current_pos >= len(self._stages):
            self._completed = True
            return

        if success:
            self._current_pos += 1
            if self._current_pos >= len(self._stages):
                self._completed = True
        # On failure: position does NOT advance; the executor decides whether
        # to retry (same position) or abort (advance to terminal).

    def mark_terminal(self) -> None:
        """Forcefully move the machine to terminal state (on abort)."""
        self._completed = True
        self._current_pos = len(self._stages)

    @property
    def current_stage_name(self) -> Optional[str]:
        if self._current_pos < len(self._stages):
            return self._stages[self._current_pos].stage_name()
        return None

    @property
    def is_terminal(self) -> bool:
        return self._completed or self._current_pos >= len(self._stages)

    def stage_count(self) -> int:
        return len(self._stages)

    def all_stage_names(self) -> List[str]:
        return [s.stage_name() for s in self._stages]

    def save_checkpoint(self, stage_name: str, data: dict) -> None:
        """Persist stage-level checkpoint data for potential resume."""
        self._checkpoints[stage_name] = data

    def get_checkpoint(self, stage_name: str) -> Optional[dict]:
        return self._checkpoints.get(stage_name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_resume_position(self, last_successful_stage: Optional[str]) -> int:
        """
        Determine where to resume.

        If last_successful_stage is None → start from the beginning.
        If it is the final stage → pipeline is already complete (return len).
        Otherwise → start from the stage AFTER the last successful one.
        """
        if last_successful_stage is None:
            return 0
        idx = self._stage_index.get(last_successful_stage)
        if idx is None:
            # Unknown stage name — restart from scratch to be safe.
            return 0
        # Resume from the stage immediately following the last success.
        return idx + 1
