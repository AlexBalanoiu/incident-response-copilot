from investigator_agent import run_investigation, InvestigationResult
from retrieval_tool import search_knowledge_base
from critic_agent import run_critique

CONFIDENCE_THRESHOLD = 0.6


class ReflectionOutcome:
    def __init__(self, result: InvestigationResult, reflection_triggered: bool, critic_reasoning: str):
        self.result = result
        self.reflection_triggered = reflection_triggered
        self.critic_reasoning = critic_reasoning


def _evidence_text(symptom_description: str) -> str:
    raw = search_knowledge_base(symptom_description, n_results=5)
    return "\n---\n".join(r["content"] for r in raw["results"])


def investigate_with_reflection(symptom_description: str) -> ReflectionOutcome:
    result = run_investigation(symptom_description)
    if not result.candidates:
        return ReflectionOutcome(result, reflection_triggered=False, critic_reasoning="No candidates to critique.")

    top = result.candidates[0]
    evidence = _evidence_text(symptom_description)
    verdict = run_critique(symptom_description, evidence, top.scenario)

    below_threshold = top.confidence < CONFIDENCE_THRESHOLD
    needs_reflection = below_threshold or not verdict.supported

    if not needs_reflection:
        return ReflectionOutcome(result, reflection_triggered=False, critic_reasoning=verdict.reasoning)

    reason = verdict.reasoning if not verdict.supported else f"Confidence {top.confidence} below threshold {CONFIDENCE_THRESHOLD}"
    refinement = verdict.refinement_query or symptom_description
    refined_description = f"{symptom_description}\n\nAdditional angle to consider: {refinement}"
    second_result = run_investigation(refined_description)

    return ReflectionOutcome(second_result, reflection_triggered=True, critic_reasoning=reason)