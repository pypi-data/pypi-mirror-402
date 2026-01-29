"""
Type definitions for TMANDATE SDK.

All types match the API response structure exactly.
No modifications, no interpretations.
"""

from typing import TypedDict, List, Optional, Dict, Any


class Advisory(TypedDict, total=False):
    """Decision advisory section (Mode 0)."""
    summary: str
    risk_level: str


class UncertaintyNotes(TypedDict, total=False):
    """Uncertainty notes section."""
    why_certainty_is_limited: str


class Decision(TypedDict, total=False):
    """Decision section from API response."""
    decision_id: str
    target: str
    advisory: Advisory
    advisory_notice: str
    confidence_band: str
    uncertainty_notes: UncertaintyNotes
    evidence_available: bool
    evidence_summary: str
    issued_at: str
    valid_until: str


class PathStability(TypedDict, total=False):
    """Path stability metrics."""
    stability_score: float
    reappearing_paths_count: int
    unique_paths_count: int
    stability_trend: str


class PathNovelty(TypedDict, total=False):
    """Path novelty metrics."""
    novelty_rate: float
    total_new_paths: int
    path_cap_activated_percentage: float
    paths_capped_in_scans: int


class PathLikelihoodTrends(TypedDict, total=False):
    """Path likelihood trends."""
    mean_likelihood_trend: str
    likelihood_variance: float
    high_likelihood_paths_count: int
    mean_likelihood: float


class PathComposition(TypedDict, total=False):
    """Path composition metrics."""
    common_nodes: List[str]
    node_diversity: float
    trust_anchor_usage: float


class ExecutionPathAdvisory(TypedDict, total=False):
    """Execution path advisory section."""
    status: str
    target: str
    required_scans: int
    current_scans: int
    reason: str
    path_stability: PathStability
    path_novelty: PathNovelty
    path_likelihood_trends: PathLikelihoodTrends
    path_composition: PathComposition


class Pattern(TypedDict, total=False):
    """Execution change pattern."""
    pattern_type: str
    correlation_strength: float
    lag_days: float
    occurrences: int
    description: str
    acceleration_trend: str
    spike_count: int


class ChangePatternsSummary(TypedDict, total=False):
    """Execution change patterns summary."""
    strongest_pattern: str
    most_frequent_pattern: str
    overall_trend: str
    total_patterns_detected: int


class ExecutionChangePatterns(TypedDict, total=False):
    """Execution change patterns section."""
    status: str
    target: str
    required_scans: int
    current_scans: int
    reason: str
    patterns: List[Pattern]
    summary: ChangePatternsSummary


class StabilityComponents(TypedDict, total=False):
    """Stability drift signal components."""
    trust_drift_stability: float
    exposure_momentum_stability: float
    risk_direction_stability: float
    feature_delta_stability: float


class StabilityDriftSignal(TypedDict, total=False):
    """Stability drift signal section."""
    status: str
    stability_score: float
    drift_direction: str
    signal_strength: str
    components: StabilityComponents
    reason: str


class PersistenceComponents(TypedDict, total=False):
    """Persistence cost estimation components."""
    graph_storage: int
    paths_storage: int
    features_storage: int
    evidence_storage: int
    ledger_storage: int


class PersistenceCostEstimation(TypedDict, total=False):
    """Persistence cost estimation section."""
    status: str
    target: str
    bytes_per_scan: int
    scans_count: int
    total_bytes_estimated: int
    growth_rate_bytes_per_day: float
    projected_monthly_bytes: int
    components: PersistenceComponents
    reason: str


class HealthComponents(TypedDict, total=False):
    """Operational health components."""
    risk_accumulation: float
    trust_degradation: float
    resource_pressure: float


class HealthIndicators(TypedDict, total=False):
    """Operational health indicators."""
    sustained_high_risk: bool
    trust_drift_worsening: bool
    storage_growth_anomaly: bool
    scan_failure_rate: float


class OperationalHealth(TypedDict, total=False):
    """Operational health section."""
    status: str
    target: str
    health_score: float
    health_classification: str
    components: HealthComponents
    indicators: HealthIndicators
    advisory_message: str
    required_scans: int
    current_scans: int
    reason: str


class ExecutionGuidance(TypedDict, total=False):
    """Execution guidance section."""
    recommended_strategy: str
    checkpoint_scope: List[str]
    volatile_window: bool
    retry_risk: str
    max_continuous_steps: int
    confidence_horizon: str
    dominant_failure_mode: str
    authority_level: str
    execution_risk: str
    _semantics: str


class ExecutionAdvisory(TypedDict, total=False):
    """Execution advisory section."""
    status: str
    reason: str
    execution_path_advisory: ExecutionPathAdvisory
    execution_change_patterns: ExecutionChangePatterns
    stability_drift_signal: StabilityDriftSignal
    persistence_cost_estimation: PersistenceCostEstimation
    operational_health: OperationalHealth
    execution_guidance: ExecutionGuidance


class CheckResponse(TypedDict, total=False):
    """Complete API response structure."""
    decision: Decision
    processing_time_ms: int
    receipt_id: str
    execution_advisory: ExecutionAdvisory


class AuthorityView(TypedDict, total=False):
    """Authority mode output (machine-readable)."""
    execution_verdict: str
    execution_risk: str
    authority_level: str
    retry_risk: str
    volatile_window: bool
    dominant_failure_mode: str
    confidence_horizon: str
    max_continuous_steps: int
    semantics: str
