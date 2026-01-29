"""Duel Engine - The cognitive core of LearnLock.

Not a tutor. Not a quiz. Not a chatbot.
An engine that infers what you believe and uses it against you.
"""

from dataclasses import dataclass, field
from datetime import datetime
import os
import re
import json


@dataclass
class Claim:
    """A testable factual claim about a concept."""
    statement: str
    claim_type: str  # mechanism, requirement, boundary, definition
    index: int = 0


@dataclass
class BeliefError:
    """Typed error with severity. Must reference a claim."""
    type: str
    description: str
    severity: int
    violated_claim: str
    claim_index: int


@dataclass
class BeliefSnapshot:
    """A moment in belief evolution with causal trigger."""
    belief: str
    trigger: str
    errors_at_time: list[BeliefError] = field(default_factory=list)


@dataclass
class BeliefState:
    """The product. The conversation is just visualization."""
    belief: str = ""
    history: list[BeliefSnapshot] = field(default_factory=list)
    errors: list[BeliefError] = field(default_factory=list)
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    attack_history: list[str] = field(default_factory=list)
    ground_truth: str = ""
    claims: list[Claim] = field(default_factory=list)


def _llm(prompt: str) -> str:
    """Single LLM call."""
    from . import config
    
    if os.environ.get("GEMINI_API_KEY"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            return genai.GenerativeModel(config.GEMINI_MODEL).generate_content(prompt).text
        except:
            pass
    
    if os.environ.get("GROQ_API_KEY"):
        import litellm
        litellm.suppress_debug_info = True
        return litellm.completion(
            model=f"groq/{config.GROQ_MODEL}",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        ).choices[0].message.content
    
    raise ValueError("No API key")


def _parse_claims(ground_truth: str) -> list[Claim]:
    """Parse ground truth into 2-4 testable claims, then verify."""
    
    # Pass 1: Generate CONCEPTUAL claims (not transcript parroting)
    prompt = f"""Extract 2-4 conceptual claims about this topic.

SOURCE: {ground_truth}

RULES:
- Claims must be CONCEPTUAL TRUTHS, not runtime facts
- Claims must be FALSIFIABLE by a wrong explanation
- Claims must capture WHY or HOW, not just WHAT
- NO tautologies ("server serves", "runs when running")
- NO operational state ("is active", "must remain")

GOOD: "A backend server mediates between clients and data stores"
GOOD: "It enforces business logic like auth and validation"
BAD: "The server processes requests" (too obvious)
BAD: "It must be running to work" (tautology)

Types: definition, mechanism, requirement, boundary

Reply ONLY as:
TYPE|CLAIM"""

    try:
        resp = _llm(prompt).strip()
        claims = []
        seen = set()
        
        for line in resp.split("\n"):
            if "|" not in line:
                continue
            parts = line.split("|", 1)
            if len(parts) != 2:
                continue
            
            ctype = parts[0].strip().lower()
            stmt = parts[1].strip()[:150]
            
            if ctype not in ("definition", "mechanism", "requirement", "boundary"):
                continue
            if len(stmt) < 10:
                continue
            if stmt in seen:
                continue
            
            seen.add(stmt)
            claims.append(Claim(statement=stmt, claim_type=ctype, index=len(claims)))
        
        if len(claims) < 2:
            return [Claim(ground_truth[:150], "definition", 0)]
        
        claims = claims[:4]
        
        # Pass 2: Verify claims - prune garbage
        claims = _verify_claims(claims)
        
        if not claims:
            return [Claim(ground_truth[:150], "definition", 0)]
        
        # Pass 3: Sharpen claims - reject blurry truths
        claims = _sharpen_claims(claims)
        
        if not claims:
            return [Claim(ground_truth[:150], "definition", 0)]
        
        # Re-index after pruning
        for i, c in enumerate(claims):
            c.index = i
        
        return claims
    except:
        return [Claim(ground_truth[:150], "definition", 0)]


def _verify_claims(claims: list[Claim]) -> list[Claim]:
    """Prune claims that are stateful, vague, or not conceptual truths."""
    
    if not claims:
        return claims
    
    # Fast pattern rejection (no LLM needed)
    garbage_patterns = [
        # Stateful
        "currently", "is now", "has been", "is running", "is listening",
        "must remain", "must be active", "needs to be running",
        "running server",
        # Vague
        "is useful", "is important", "is helpful", "helps with",
        "is required", "is needed", "must be", "should be",
        "requires the", "needs the", "to function",
        # Tautological
        "processes requests", "serves requests", "handles requests",
        "processes and responds", "receives and processes",
        "responds to", "receives and", "sends and receives",
        "when running", "while running", "if running",
        "incoming requests", "client requests",
    ]
    
    def is_garbage(stmt: str) -> bool:
        lower = stmt.lower()
        return any(p in lower for p in garbage_patterns)
    
    # Pre-filter obvious garbage
    candidates = [c for c in claims if not is_garbage(c.statement)]
    
    # If we pruned everything, keep the first claim as fallback
    if not candidates:
        return claims[:1]
    
    # If only 1-2 left, skip LLM verification
    if len(candidates) <= 2:
        return candidates
    
    # Pass 2: LLM verification for remaining claims
    claims_str = "\n".join(f"{i+1}. [{c.claim_type}] {c.statement}" for i, c in enumerate(candidates))
    
    prompt = f"""Review these claims. Keep ONLY conceptual truths.

CLAIMS:
{claims_str}

REJECT claims that are:
- Tautological (obvious, unfalsifiable)
- Runtime state (not conceptual)
- Too vague to violate

Reply with ONLY the numbers to KEEP, comma-separated.
Example: 1,3

If all are bad, reply: NONE"""

    try:
        resp = _llm(prompt).strip().upper()
        
        if resp == "NONE" or not resp:
            return candidates[:1]
        
        kept = []
        for part in resp.replace(" ", "").split(","):
            try:
                idx = int(part) - 1
                if 0 <= idx < len(candidates):
                    kept.append(candidates[idx])
            except:
                continue
        
        return kept if kept else candidates[:2]
    except:
        return candidates


def _sharpen_claims(claims: list[Claim]) -> list[Claim]:
    """Reject blurry truths. Keep only claims sharp enough to violate."""
    
    if len(claims) <= 1:
        return claims
    
    # Blurry patterns - technically true but unfalsifiable
    blurry_patterns = [
        "handle ", "handles ", "manage ", "manages ",
        "deal with", "deals with", "work with", "works with",
        "is responsible", "takes care", "involved in",
        "related to", "associated with", "connected to",
        "plays a role", "is part of", "contributes to",
        "helps ensure", "helps provide", "helps manage",
        "various", "different types", "multiple", "many kinds",
        "and more", "and other", "etc", "such as",
        "in some way", "in general", "typically", "usually",
        "can be used", "may be used", "might be",
    ]
    
    def is_blurry(stmt: str) -> bool:
        lower = stmt.lower()
        return any(p in lower for p in blurry_patterns)
    
    sharp = [c for c in claims if not is_blurry(c.statement)]
    
    # Keep at least one claim
    return sharp if sharp else claims[:1]


def _is_non_answer(text: str) -> bool:
    """Detect dodging or ignorance."""
    text = text.lower().strip()
    dodges = [
        "i don't know", "i dont know", "idk", "no idea", "not sure",
        "i'm not sure", "im not sure", "no clue", "beats me",
        "i have no idea", "haven't learned", "havent learned",
        "don't understand", "dont understand", "confused",
        "i don't remember", "i dont remember", "forgot", "forget",
        "i forgot", "i forget", "forgotten", "pass", "can't answer",
        "cant answer", "don't know anything", "dont know anything",
        "no answer", "don't recall", "dont recall",
    ]
    for d in dodges:
        if d in text:
            return True
    return len(text.split()) < 3


def _run_belief_model(concept: str, user_msg: str, state: BeliefState) -> dict:
    """Extract what the student believes."""
    
    if _is_non_answer(user_msg):
        return {"belief": state.belief or "", "is_non_answer": True}
    
    conv = []
    for i, ev in enumerate(state.evidence):
        conv.append(f"Student: {ev}")
        if i < len(state.attack_history):
            conv.append(f"Challenge: {state.attack_history[i]}")
    conv.append(f"Student: {user_msg}")
    
    prompt = f"""Model what this student believes about {concept}.

PREVIOUS BELIEF: {state.belief or "None"}

CONVERSATION:
{chr(10).join(conv)}

Reply EXACTLY as:
BELIEF: [one sentence - their mental model]"""

    resp = _llm(prompt)
    belief = ""
    for line in resp.strip().split("\n"):
        if line.upper().startswith("BELIEF:"):
            belief = line[7:].strip()
            break
    
    if len(belief) < 10:
        belief = state.belief or ""
    
    return {"belief": belief, "is_non_answer": False}


def _run_contradiction_detector(belief: str, claims: list[Claim], turn: int) -> list[BeliefError]:
    """Check belief against claims. Errors MUST reference claims."""
    
    if not belief or not claims:
        return []
    
    harshness = {1: "Only CLEAR violations.", 2: "Violations and omissions.", 3: "All violations."}
    claims_str = "\n".join(f"{c.index+1}. [{c.claim_type}] {c.statement}" for c in claims)
    
    prompt = f"""Check belief against claims.

BELIEF: {belief}

CLAIMS:
{claims_str}

{harshness.get(turn, harshness[3])}

For EACH violation, output:
CLAIM_NUM|ERROR_TYPE|DESCRIPTION|SEVERITY

Types: wrong_mechanism, missing_mechanism, boundary_error, conflation, superficial
Severity: 1=minor, 2=significant, 3=critical

If no violations: NONE"""

    resp = _llm(prompt).strip()
    if resp.upper() in ("NONE", "N/A", ""):
        return []
    
    errors = []
    for line in resp.split("\n"):
        if "|" not in line:
            continue
        parts = line.split("|")
        if len(parts) < 4:
            continue
        try:
            idx = int(parts[0].strip()) - 1
            if idx < 0 or idx >= len(claims):
                continue  # Discard errors without valid claim
            errors.append(BeliefError(
                type=parts[1].strip().lower(),
                description=parts[2].strip(),
                severity=min(3, max(1, int(parts[3].strip()))),
                violated_claim=claims[idx].statement,
                claim_index=idx
            ))
        except:
            continue  # Discard malformed errors
    
    return errors


def _generate_non_answer_attack(concept: str, claims: list[Claim], history: list[str]) -> str:
    """Guide ignorant student toward a claim."""
    
    claim = claims[0] if claims else None
    history_str = "\n".join(f"- {q}" for q in history) if history else "None"
    
    prompt = f"""Student doesn't know about: {concept}

TARGET CLAIM: {claim.statement if claim else concept}

ALREADY ASKED:
{history_str}

Generate ONE question that helps them reason toward this claim.
Reply with ONLY the question."""

    q = _llm(prompt).strip().strip('"\'')
    q = re.sub(r'^(Q:|Question:)\s*', '', q, flags=re.I)
    return q or f"What do you think {concept} might involve?"


def _run_interrogator(belief: str, errors: list[BeliefError], claims: list[Claim], history: list[str]) -> str:
    """Attack highest severity error. Must reference violated claim."""
    
    if not errors:
        return None
    
    target = max(errors, key=lambda e: e.severity)
    history_str = "\n".join(f"- {q}" for q in history) if history else "None"
    
    prompt = f"""Corner this student.

THEY BELIEVE: {belief}

ERROR: {target.type} (severity {target.severity})
VIOLATES CLAIM: "{target.violated_claim}"
BECAUSE: {target.description}

ALREADY ASKED:
{history_str}

Generate ONE question that exposes why their belief violates this specific claim.
The question must force them to confront: "{target.violated_claim}"

Reply with ONLY the question."""

    q = _llm(prompt).strip().strip('"\'')
    q = re.sub(r'^(Q:|Question:)\s*', '', q, flags=re.I)
    return q or None


class DuelEngine:
    """Adversarial Socratic interrogation engine."""
    
    def __init__(self, concept: str, ground_truth: str, question: str = None):
        self.concept = concept
        self.state = BeliefState(ground_truth=ground_truth)
        self.state.claims = _parse_claims(ground_truth)
        self.turn = 0
        self.max_turns = 3
        self.finished = False
        self._initial_q = question or f"Explain {concept} in your own words."
    
    def get_challenge(self) -> str:
        if self.state.attack_history:
            return self.state.attack_history[-1]
        return self._initial_q
    
    def get_claims(self) -> list[Claim]:
        return self.state.claims
    
    def process(self, user_input: str) -> dict:
        self.turn += 1
        trigger = self.state.attack_history[-1] if self.state.attack_history else "initial"
        
        belief_result = _run_belief_model(self.concept, user_input, self.state)
        
        if belief_result["belief"] and belief_result["belief"] != self.state.belief:
            self.state.belief = belief_result["belief"]
        self.state.evidence.append(user_input)
        
        # Non-answer handling
        if belief_result.get("is_non_answer"):
            if self.turn >= self.max_turns:
                self.state.errors = [BeliefError(
                    "no_response", "Unable to explain", 3,
                    self.state.claims[0].statement if self.state.claims else "",
                    0
                )]
                self.finished = True
                return {"type": "reveal", "message": ""}
            
            attack = _generate_non_answer_attack(
                self.concept, self.state.claims, self.state.attack_history
            )
            self.state.attack_history.append(attack)
            return {"type": "attack", "message": attack}
        
        # Check against claims
        errors = _run_contradiction_detector(self.state.belief, self.state.claims, self.turn)
        self.state.errors = errors
        
        # Record snapshot (only if belief exists)
        if self.state.belief:
            self.state.history.append(BeliefSnapshot(
                belief=self.state.belief,
                trigger=trigger,
                errors_at_time=list(errors)
            ))
        
        if not errors:
            self.finished = True
            return {"type": "reveal", "message": ""}
        
        if self.turn >= self.max_turns:
            self.finished = True
            return {"type": "reveal", "message": ""}
        
        attack = _run_interrogator(
            self.state.belief, self.state.errors,
            self.state.claims, self.state.attack_history
        )
        if attack:
            self.state.attack_history.append(attack)
            return {"type": "attack", "message": attack}
        
        self.finished = True
        return {"type": "reveal", "message": ""}
    
    def get_reveal(self) -> dict:
        return {
            "belief": self.state.belief,
            "claims": self.state.claims,
            "history": self.state.history,
            "errors": self.state.errors,
            "ground_truth": self.state.ground_truth,
            "turns": self.turn,
            "evidence": self.state.evidence,
            "attacks": self.state.attack_history,
        }


def create_duel(concept: str, ground_truth: str, question: str = None) -> DuelEngine:
    return DuelEngine(concept, ground_truth, question)


def belief_to_score(state: BeliefState) -> int:
    if not state.errors:
        return 5
    max_sev = max(e.severity for e in state.errors)
    return {3: 1, 2: 2, 1: 4}.get(max_sev, 3)


def export_duel_data(state: BeliefState, concept: str) -> dict:
    """Export duel data for research/training."""
    return {
        "concept": concept,
        "timestamp": datetime.now().isoformat(),
        "ground_truth": state.ground_truth,
        "claims": [{"type": c.claim_type, "statement": c.statement, "index": c.index} for c in state.claims],
        "final_belief": state.belief,
        "trajectory": [
            {
                "belief": s.belief,
                "trigger": s.trigger,
                "errors": [{"type": e.type, "desc": e.description, "severity": e.severity,
                           "claim": e.violated_claim, "claim_idx": e.claim_index} for e in s.errors_at_time]
            } for s in state.history
        ],
        "final_errors": [{"type": e.type, "desc": e.description, "severity": e.severity,
                        "claim": e.violated_claim, "claim_idx": e.claim_index} for e in state.errors],
        "evidence": state.evidence,
        "attacks": state.attack_history,
    }


def save_duel_data(state: BeliefState, concept: str) -> str:
    """Save duel data to /data/duels/YYYY-MM-DD/"""
    from . import config
    
    data = export_duel_data(state, concept)
    date_str = datetime.now().strftime("%Y-%m-%d")
    duel_dir = config.DATA_DIR / "duels" / date_str
    duel_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{concept.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.json"
    filepath = duel_dir / filename
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    return str(filepath)
