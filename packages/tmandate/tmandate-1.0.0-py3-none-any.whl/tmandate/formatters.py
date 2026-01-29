"""
Mode-specific output formatters.

All formatters read the SAME API response.
Different emphasis and phrasing only.
No new signals - only format existing outputs.
"""

from typing import Dict, Any
from .types import CheckResponse


def format_check_mode(response: CheckResponse) -> str:
    """
    Format check mode output - authoritative, compliance-focused.
    
    Dense verdict format. No internals shown.
    """
    decision = response.get("decision", {})
    advisory = decision.get("advisory", {})
    guidance = response.get("execution_advisory", {}).get("execution_guidance", {})
    latency = response.get("processing_time_ms", 0)
    target = decision.get("target", "unknown")
    
    # Extract values
    risk_level = advisory.get("risk_level", "UNKNOWN").upper()
    confidence = decision.get("confidence_band", "unknown").upper()
    valid_until = decision.get("valid_until", "unknown")
    
    # Interpret reasons (from existing signals only)
    reasons = []
    if guidance.get("volatile_window", False):
        reasons.append("Execution instability detected in recent history")
    retry_risk = guidance.get("retry_risk", "low")
    if retry_risk in ("high", "medium"):
        reasons.append("Similar targets showed elevated failure rates")
    failure_mode = guidance.get("dominant_failure_mode", "unknown")
    if failure_mode != "unknown":
        reasons.append("Current execution window is classified as sensitive")
    
    # Default reason if none found
    if not reasons:
        reasons.append("Standard execution conditions detected")
    
    # Interpret explanation
    if retry_risk == "high" or guidance.get("volatile_window", False):
        explanation = "Proceeding without safeguards increases the likelihood of retries, UI instability, or partial failure."
    else:
        explanation = "Standard execution safeguards are recommended for optimal reliability."
    
    # Format output
    output = f"""[TMANDATE]  target={target}   latency={latency}ms

EXECUTION VERDICT
  Risk Level     : {risk_level}
  Confidence     : {confidence}

WHY THIS MATTERS
"""
    for reason in reasons:
        output += f"  • {reason}\n"
    
    output += f"""
WHAT THIS MEANS
  {explanation}

DECISION VALIDITY
  Valid until: {valid_until}
"""
    return output


def format_advisory_mode(response: CheckResponse) -> str:
    """
    Format advisory mode output - urgent, "oh shit" mode.
    
    Interpreted risk intelligence. Creates urgency.
    """
    decision = response.get("decision", {})
    target = decision.get("target", "unknown")
    advisory = response.get("execution_advisory", {})
    guidance = advisory.get("execution_guidance", {})
    stability = advisory.get("stability_drift_signal", {})
    patterns = advisory.get("execution_change_patterns", {})
    path_adv = advisory.get("execution_path_advisory", {})
    persistence = advisory.get("persistence_cost_estimation", {})
    health = advisory.get("operational_health", {})
    
    # Opening statement
    volatile = guidance.get("volatile_window", False)
    retry_risk = guidance.get("retry_risk", "low")
    if volatile and retry_risk == "high":
        opening = "This execution target has historically caused agent instability."
    elif volatile or retry_risk == "high":
        opening = "This execution target shows elevated risk indicators."
    else:
        opening = "This execution target requires attention."
    
    # Why this is risky
    risk_reasons = []
    if retry_risk == "high":
        risk_reasons.append("Agents frequently enter retry loops in this state")
    pattern_summary = patterns.get("summary", {})
    overall_trend = pattern_summary.get("overall_trend", "stable")
    if overall_trend == "increasing":
        risk_reasons.append("Execution volatility is increasing")
    stability_score = stability.get("stability_score", 1.0)
    if stability_score < 0.5:
        risk_reasons.append("Recovery paths are unstable")
    growth_rate = persistence.get("growth_rate_bytes_per_day", 0.0)
    if growth_rate > 1000000:  # >1MB/day
        risk_reasons.append("Token burn accelerates without governance")
    
    if not risk_reasons:
        risk_reasons.append("Standard risk factors present")
    
    # Observed behavior
    drift_direction = stability.get("drift_direction", "stable")
    if drift_direction == "increasing":
        trend_str = "declining"
    elif drift_direction == "decreasing":
        trend_str = "improving"
    else:
        trend_str = "stable"
    
    retry_amp = guidance.get("retry_risk", "low").upper()
    
    # Where agents fail
    failure_points = []
    path_novelty = path_adv.get("path_novelty", {})
    novelty_rate = path_novelty.get("novelty_rate", 0.0)
    if novelty_rate > 0.5:
        failure_points.append("High path novelty (agents re-explore repeatedly)")
    path_likelihood = path_adv.get("path_likelihood_trends", {})
    mean_likelihood = path_likelihood.get("mean_likelihood", 0.0)
    if mean_likelihood > 0.5:
        failure_points.append("Mean execution likelihood remains high despite failures")
    path_comp = path_adv.get("path_composition", {})
    trust_anchor_usage = path_comp.get("trust_anchor_usage", 100.0)
    if trust_anchor_usage < 50.0:
        failure_points.append("Trust anchor usage is inconsistent")
    
    if not failure_points:
        failure_points.append("Standard execution patterns observed")
    
    # System pressure
    projected_bytes = persistence.get("projected_monthly_bytes", 0)
    projected_gb = projected_bytes / (1024 ** 3)  # Convert to GB
    projected_str = f"~{projected_gb:.1f}GB" if projected_gb >= 0.1 else f"~{projected_bytes / (1024 ** 2):.1f}MB"
    
    health_class = health.get("health_classification", "healthy")
    health_indicators = health.get("indicators", {})
    failure_rate = health_indicators.get("scan_failure_rate", 0.0)
    failure_pct = int(failure_rate * 100)
    
    # Impact if ungoverned
    impacts = []
    execution_risk = guidance.get("execution_risk", "low")
    if execution_risk == "high":
        impacts.append("Higher probability of stalled execution")
    if growth_rate > 1000000:
        impacts.append("Increased token burn")
    health_class = health.get("health_classification", "healthy")
    if health_class in ("degraded", "critical"):
        impacts.append("Reduced completion reliability")
    
    if not impacts:
        impacts.append("Standard execution risks")
    
    # Recommendation
    recommended_strategy = guidance.get("recommended_strategy", "continuous_execution")
    if recommended_strategy == "checkpointed_execution":
        recommendation = "Use execution governance for this run."
    else:
        recommendation = "Monitor execution closely."
    
    # Format output
    output = f"""[TMANDATE]  target={target}

⚠️ EXECUTION RISK WARNING

{opening}

WHY THIS IS RISKY
"""
    for reason in risk_reasons:
        output += f"  • {reason}\n"
    
    output += f"""
OBSERVED BEHAVIOR
  Stability Score        : {stability_score:.2f} ({trend_str})
  Change Pattern Trend   : {overall_trend.capitalize()}
  Retry Amplification    : {retry_amp}

WHERE AGENTS FAIL
"""
    for point in failure_points:
        output += f"  • {point}\n"
    
    output += f"""
SYSTEM PRESSURE
  Projected State Growth : {projected_str} / month
  Operational State      : {health_class.capitalize()}
  Scan Failure Rate      : {failure_pct}%

IMPACT IF UNGOVERNED
"""
    for impact in impacts:
        output += f"  • {impact}\n"
    
    output += f"""
RECOMMENDATION
  {recommendation}
"""
    return output


def format_authority_mode(response: CheckResponse) -> Dict[str, Any]:
    """
    Format authority mode output - machine-readable JSON.
    
    Execution control for agents/production systems.
    """
    guidance = response.get("execution_advisory", {}).get("execution_guidance", {})
    
    # Extract all fields
    execution_risk = guidance.get("execution_risk", "low")
    authority_level = guidance.get("authority_level", "normal")
    retry_risk = guidance.get("retry_risk", "low")
    volatile_window = guidance.get("volatile_window", False)
    dominant_failure_mode = guidance.get("dominant_failure_mode", "unknown")
    confidence_horizon = guidance.get("confidence_horizon", "short")
    max_continuous_steps = guidance.get("max_continuous_steps", 20)
    semantics = guidance.get("_semantics", "advisory_not_mandatory")
    
    # Derive execution_verdict (FIX 3: explicit logic)
    if execution_risk == "high" and authority_level == "strict":
        verdict = "RESTRICT"
    elif execution_risk in ("medium", "high") or volatile_window:
        verdict = "ALLOW_WITH_CAUTION"
    else:
        verdict = "ALLOW"
    
    return {
        "execution_verdict": verdict,
        "execution_risk": execution_risk,
        "authority_level": authority_level,
        "retry_risk": retry_risk,
        "volatile_window": volatile_window,
        "dominant_failure_mode": dominant_failure_mode,
        "confidence_horizon": confidence_horizon,
        "max_continuous_steps": max_continuous_steps,
        "semantics": semantics
    }
