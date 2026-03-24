"""Correlation engine — the core fraud-detection logic.

Cross-checks image metadata against police report data using four rules
and produces a 0-100 risk score.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.schemas import AnalysisFlag, AnalysisResponse
from app.utils.haversine import safe_distance

# ── Thresholds ──────────────────────────────────────────────────────────
TIME_THRESHOLD_HOURS = 24
DISTANCE_THRESHOLD_KM = 5.0
CONSISTENCY_THRESHOLD = 0.5
FLAGGED_THRESHOLD = 50

# ── Score weights ───────────────────────────────────────────────────────
WEIGHT_TIME = 30
WEIGHT_LOCATION = 30
WEIGHT_INTEGRITY = 20
WEIGHT_CONSISTENCY = 20


def _parse_report_datetime(report: Dict[str, Any]) -> Optional[datetime]:
    """Parse incident date + time from the report into a datetime."""
    date_str = report.get("incident_date", "")
    time_str = report.get("incident_time", "")
    if not date_str:
        return None
    try:
        combined = f"{date_str} {time_str}" if time_str else date_str
        fmt = "%Y-%m-%d %H:%M" if time_str else "%Y-%m-%d"
        return datetime.strptime(combined, fmt)
    except (ValueError, TypeError):
        return None


# ── Rule 1: Time Consistency ───────────────────────────────────────────

def _check_time_consistency(
    image_results: List[Dict[str, Any]],
    report: Dict[str, Any],
) -> AnalysisFlag:
    """Flag if any photo timestamp is >24 h after or before the incident."""
    incident_dt = _parse_report_datetime(report)

    if incident_dt is None:
        return AnalysisFlag(
            rule="TIME_CONSISTENCY",
            triggered=False,
            score_contribution=0,
            detail="Incident datetime not available in report — rule skipped.",
        )

    max_delta: Optional[timedelta] = None
    worst_file: Optional[str] = None

    for img in image_results:
        photo_dt = img["exif"].get("datetime_original")
        if photo_dt is None:
            continue
        delta = abs(photo_dt - incident_dt)
        if max_delta is None or delta > max_delta:
            max_delta = delta
            worst_file = img["filename"]

        # Also flag if photo was taken BEFORE the incident
        if photo_dt < incident_dt:
            return AnalysisFlag(
                rule="TIME_CONSISTENCY",
                triggered=True,
                score_contribution=WEIGHT_TIME,
                detail=(
                    f"Photo '{worst_file}' was taken BEFORE the reported "
                    f"incident ({photo_dt} < {incident_dt})."
                ),
            )

    if max_delta is None:
        return AnalysisFlag(
            rule="TIME_CONSISTENCY",
            triggered=False,
            score_contribution=0,
            detail="No photo timestamps available — rule inconclusive.",
        )

    threshold = timedelta(hours=TIME_THRESHOLD_HOURS)
    triggered = max_delta > threshold
    hours = max_delta.total_seconds() / 3600.0

    return AnalysisFlag(
        rule="TIME_CONSISTENCY",
        triggered=triggered,
        score_contribution=WEIGHT_TIME if triggered else 0,
        detail=(
            f"Time mismatch: {hours:.1f}h (threshold {TIME_THRESHOLD_HOURS}h). "
            f"Worst file: '{worst_file}'."
        )
        if triggered
        else f"Time delta {hours:.1f}h is within {TIME_THRESHOLD_HOURS}h threshold.",
    )


# ── Rule 2: Location Consistency ──────────────────────────────────────

def _check_location_consistency(
    image_results: List[Dict[str, Any]],
    report: Dict[str, Any],
) -> AnalysisFlag:
    """Flag if photo GPS is >5 km from the reported incident location."""
    report_coords: Optional[Tuple[float, float]] = None
    if report.get("gps_lat") is not None and report.get("gps_lon") is not None:
        report_coords = (report["gps_lat"], report["gps_lon"])

    if report_coords is None:
        return AnalysisFlag(
            rule="LOCATION_CONSISTENCY",
            triggered=False,
            score_contribution=0,
            detail="Report location GPS not available — rule skipped.",
        )

    worst_dist: Optional[float] = None
    worst_file: Optional[str] = None

    for img in image_results:
        exif = img["exif"]
        if exif.get("gps_lat") is None or exif.get("gps_lon") is None:
            continue
        photo_coords = (exif["gps_lat"], exif["gps_lon"])
        dist = safe_distance(photo_coords, report_coords)
        if dist is not None and (worst_dist is None or dist > worst_dist):
            worst_dist = dist
            worst_file = img["filename"]

    if worst_dist is None:
        return AnalysisFlag(
            rule="LOCATION_CONSISTENCY",
            triggered=False,
            score_contribution=0,
            detail="No photo GPS data available — rule inconclusive.",
        )

    triggered = worst_dist > DISTANCE_THRESHOLD_KM
    return AnalysisFlag(
        rule="LOCATION_CONSISTENCY",
        triggered=triggered,
        score_contribution=WEIGHT_LOCATION if triggered else 0,
        detail=(
            f"GPS mismatch: {worst_dist:.1f}km (threshold {DISTANCE_THRESHOLD_KM}km). "
            f"Worst file: '{worst_file}'."
        )
        if triggered
        else f"GPS distance {worst_dist:.1f}km is within {DISTANCE_THRESHOLD_KM}km threshold.",
    )


# ── Rule 3: Integrity Check ──────────────────────────────────────────

def _check_integrity(
    image_results: List[Dict[str, Any]],
) -> AnalysisFlag:
    """Flag if any image was edited (Photoshop, Canva, etc.)."""
    edited_files: List[str] = []
    software_found: List[str] = []

    for img in image_results:
        exif = img["exif"]
        if exif.get("is_edited"):
            edited_files.append(img["filename"])
            software_found.append(exif.get("software", "unknown"))

    triggered = len(edited_files) > 0
    if triggered:
        detail = (
            f"Editing software detected in {len(edited_files)} image(s): "
            + ", ".join(
                f"'{f}' ({s})" for f, s in zip(edited_files, software_found)
            )
            + "."
        )
    else:
        detail = "No editing software detected in image metadata."

    return AnalysisFlag(
        rule="INTEGRITY_CHECK",
        triggered=triggered,
        score_contribution=WEIGHT_INTEGRITY if triggered else 0,
        detail=detail,
    )


# ── Rule 4: Damage Consistency (LLM Simulation) ─────────────────────

def _keyword_overlap(text_a: str, text_b: str) -> float:
    """Compute a simple word-overlap ratio between two texts (0-1)."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / max(len(words_a), len(words_b))


def _check_damage_consistency(
    image_results: List[Dict[str, Any]],
    report: Dict[str, Any],
) -> AnalysisFlag:
    """Compare reported damage description with detected damage from images.

    Uses keyword overlap as a mock for LLM-based semantic comparison.
    Designed to be replaced with a real Gemini / GPT call later.
    """
    report_damage = report.get("damage_description", "")
    if not report_damage:
        return AnalysisFlag(
            rule="DAMAGE_CONSISTENCY",
            triggered=False,
            score_contribution=0,
            detail="No damage description in report — rule skipped.",
        )

    # Aggregate detected damage from all images
    detected_parts: List[str] = []
    for img in image_results:
        dd = img.get("detected_damage", "")
        if dd:
            detected_parts.append(dd)

    if not detected_parts:
        return AnalysisFlag(
            rule="DAMAGE_CONSISTENCY",
            triggered=False,
            score_contribution=0,
            detail="No damage detected in images — rule inconclusive.",
        )

    detected_damage = " ".join(detected_parts)
    score = _keyword_overlap(report_damage, detected_damage)
    triggered = score < CONSISTENCY_THRESHOLD

    return AnalysisFlag(
        rule="DAMAGE_CONSISTENCY",
        triggered=triggered,
        score_contribution=WEIGHT_CONSISTENCY if triggered else 0,
        detail=(
            f"Damage consistency score: {score:.2f} "
            f"(threshold {CONSISTENCY_THRESHOLD}). "
            + (
                "Reported damage does not match detected damage."
                if triggered
                else "Reported damage is consistent with detected damage."
            )
        ),
    )


# ── Main Analyzer ────────────────────────────────────────────────────

def _build_explanation(flags: List[AnalysisFlag], risk_score: float) -> str:
    """Build a human-readable explanation from the triggered flags."""
    triggered = [f for f in flags if f.triggered]
    if not triggered:
        return "No inconsistencies detected. The claim evidence appears consistent."

    parts = [f"Risk score: {risk_score:.0f}/100."]
    parts.append(f"{len(triggered)} issue(s) found:")
    for f in triggered:
        parts.append(f"  - [{f.rule}] {f.detail}")
    return "\n".join(parts)


def analyze(
    image_results: List[Dict[str, Any]],
    report_data: Dict[str, Any],
    claim_id: int,
) -> AnalysisResponse:
    """Run all correlation rules and produce the final analysis.

    Args:
        image_results: Output from image_worker.process_images().
        report_data:   Output from document_worker.process_report().
        claim_id:      Database ID of the claim being analysed.

    Returns:
        AnalysisResponse with risk_score, status, flags, and explanation.
    """
    flags: List[AnalysisFlag] = [
        _check_time_consistency(image_results, report_data),
        _check_location_consistency(image_results, report_data),
        _check_integrity(image_results),
        _check_damage_consistency(image_results, report_data),
    ]

    risk_score = float(sum(f.score_contribution for f in flags))
    status = "FLAGGED" if risk_score >= FLAGGED_THRESHOLD else "CLEAN"
    explanation = _build_explanation(flags, risk_score)

    return AnalysisResponse(
        claim_id=claim_id,
        risk_score=risk_score,
        status=status,
        flags=flags,
        explanation=explanation,
    )
