"""Tests for the claim analysis pipeline.

Covers:
  - Utility functions (haversine, hashing)
  - Correlation engine rules (time, location, integrity, damage)
  - Edge cases (missing EXIF, missing GPS, no flags)
"""

import math
from datetime import datetime

import pytest

from app.utils.haversine import haversine_km, safe_distance
from app.utils.hashing import sha256_file
from app.services.claim_analyzer import (
    _check_time_consistency,
    _check_location_consistency,
    _check_integrity,
    _check_damage_consistency,
    _keyword_overlap,
    analyze,
    WEIGHT_TIME,
    WEIGHT_LOCATION,
    WEIGHT_INTEGRITY,
    WEIGHT_CONSISTENCY,
)


# ═══════════════════════════════════════════════════════════════════════
# Utility tests
# ═══════════════════════════════════════════════════════════════════════

class TestHaversine:
    def test_same_point_returns_zero(self):
        assert haversine_km(0.0, 0.0, 0.0, 0.0) == 0.0

    def test_known_distance_accra_kumasi(self):
        # Accra (5.6037, -0.1870) to Kumasi (6.6885, -1.6244) ≈ 196 km
        dist = haversine_km(5.6037, -0.1870, 6.6885, -1.6244)
        assert 190 < dist < 210

    def test_known_distance_london_paris(self):
        # London (51.5074, -0.1278) to Paris (48.8566, 2.3522) ≈ 344 km
        dist = haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
        assert 340 < dist < 350

    def test_symmetry(self):
        d1 = haversine_km(5.0, 10.0, 6.0, 11.0)
        d2 = haversine_km(6.0, 11.0, 5.0, 10.0)
        assert abs(d1 - d2) < 1e-6

    def test_safe_distance_none_coords(self):
        assert safe_distance(None, (5.0, 10.0)) is None
        assert safe_distance((5.0, 10.0), None) is None
        assert safe_distance(None, None) is None

    def test_safe_distance_valid(self):
        result = safe_distance((5.6037, -0.1870), (5.6037, -0.1870))
        assert result is not None
        assert result == 0.0


class TestHashing:
    def test_deterministic(self):
        data = b"hello world"
        h1 = sha256_file(data)
        h2 = sha256_file(data)
        assert h1 == h2

    def test_known_hash(self):
        # SHA-256 of empty bytes
        assert sha256_file(b"") == (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    def test_different_inputs_different_hashes(self):
        assert sha256_file(b"a") != sha256_file(b"b")


# ═══════════════════════════════════════════════════════════════════════
# Helper builders for test data
# ═══════════════════════════════════════════════════════════════════════

def _make_image_result(
    filename: str = "photo.jpg",
    datetime_original=None,
    gps_lat=None,
    gps_lon=None,
    software=None,
    is_edited=False,
    detected_damage="front bumper dent, scratches",
):
    return {
        "filename": filename,
        "file_hash": "abc123",
        "exif": {
            "datetime_original": datetime_original,
            "gps_lat": gps_lat,
            "gps_lon": gps_lon,
            "camera_make": "TestCam",
            "camera_model": "T1",
            "software": software,
            "is_edited": is_edited,
        },
        "detected_damage": detected_damage,
    }


def _make_report(
    incident_date="2026-03-15",
    incident_time="14:30",
    location_text="Accra, Independence Avenue",
    plate_number="GR-1234-20",
    damage_description="Front bumper severely dented. Scratches on the hood.",
    gps_lat=5.5600,
    gps_lon=-0.1870,
):
    return {
        "incident_date": incident_date,
        "incident_time": incident_time,
        "location_text": location_text,
        "plate_number": plate_number,
        "damage_description": damage_description,
        "gps_lat": gps_lat,
        "gps_lon": gps_lon,
    }


# ═══════════════════════════════════════════════════════════════════════
# Rule 1: Time Consistency
# ═══════════════════════════════════════════════════════════════════════

class TestTimeConsistency:
    def test_within_threshold_no_flag(self):
        img = _make_image_result(
            datetime_original=datetime(2026, 3, 15, 16, 0)  # 1.5h after
        )
        report = _make_report()
        flag = _check_time_consistency([img], report)
        assert not flag.triggered
        assert flag.score_contribution == 0

    def test_exceeds_24h_flags(self):
        img = _make_image_result(
            datetime_original=datetime(2026, 3, 18, 14, 30)  # 3 days later
        )
        report = _make_report()
        flag = _check_time_consistency([img], report)
        assert flag.triggered
        assert flag.score_contribution == WEIGHT_TIME

    def test_photo_before_incident_flags(self):
        img = _make_image_result(
            datetime_original=datetime(2026, 3, 10, 10, 0)  # 5 days before
        )
        report = _make_report()
        flag = _check_time_consistency([img], report)
        assert flag.triggered
        assert flag.score_contribution == WEIGHT_TIME

    def test_no_exif_datetime_inconclusive(self):
        img = _make_image_result(datetime_original=None)
        report = _make_report()
        flag = _check_time_consistency([img], report)
        assert not flag.triggered

    def test_no_report_datetime_skipped(self):
        img = _make_image_result(
            datetime_original=datetime(2026, 3, 15, 16, 0)
        )
        report = _make_report(incident_date="", incident_time="")
        flag = _check_time_consistency([img], report)
        assert not flag.triggered


# ═══════════════════════════════════════════════════════════════════════
# Rule 2: Location Consistency
# ═══════════════════════════════════════════════════════════════════════

class TestLocationConsistency:
    def test_close_location_no_flag(self):
        # Photo GPS very close to report GPS
        img = _make_image_result(gps_lat=5.5610, gps_lon=-0.1880)
        report = _make_report(gps_lat=5.5600, gps_lon=-0.1870)
        flag = _check_location_consistency([img], report)
        assert not flag.triggered

    def test_far_location_flags(self):
        # Photo GPS in Kumasi, report in Accra (~196 km)
        img = _make_image_result(gps_lat=6.6885, gps_lon=-1.6244)
        report = _make_report(gps_lat=5.5600, gps_lon=-0.1870)
        flag = _check_location_consistency([img], report)
        assert flag.triggered
        assert flag.score_contribution == WEIGHT_LOCATION

    def test_no_photo_gps_inconclusive(self):
        img = _make_image_result(gps_lat=None, gps_lon=None)
        report = _make_report()
        flag = _check_location_consistency([img], report)
        assert not flag.triggered

    def test_no_report_gps_skipped(self):
        img = _make_image_result(gps_lat=5.56, gps_lon=-0.187)
        report = _make_report(gps_lat=None, gps_lon=None)
        flag = _check_location_consistency([img], report)
        assert not flag.triggered


# ═══════════════════════════════════════════════════════════════════════
# Rule 3: Integrity Check
# ═══════════════════════════════════════════════════════════════════════

class TestIntegrityCheck:
    def test_no_software_no_flag(self):
        img = _make_image_result(software=None, is_edited=False)
        flag = _check_integrity([img])
        assert not flag.triggered

    def test_photoshop_flags(self):
        img = _make_image_result(
            software="Adobe Photoshop CC 2024", is_edited=True
        )
        flag = _check_integrity([img])
        assert flag.triggered
        assert flag.score_contribution == WEIGHT_INTEGRITY

    def test_canva_flags(self):
        img = _make_image_result(software="Canva", is_edited=True)
        flag = _check_integrity([img])
        assert flag.triggered

    def test_legitimate_software_no_flag(self):
        img = _make_image_result(
            software="Apple iOS 17.0", is_edited=False
        )
        flag = _check_integrity([img])
        assert not flag.triggered


# ═══════════════════════════════════════════════════════════════════════
# Rule 4: Damage Consistency
# ═══════════════════════════════════════════════════════════════════════

class TestDamageConsistency:
    def test_keyword_overlap_identical(self):
        assert _keyword_overlap("front bumper dent", "front bumper dent") == 1.0

    def test_keyword_overlap_no_match(self):
        assert _keyword_overlap("front bumper", "rear window shattered") == 0.0

    def test_keyword_overlap_partial(self):
        score = _keyword_overlap("front bumper dent", "front bumper crack")
        assert 0.0 < score < 1.0

    def test_consistent_damage_no_flag(self):
        img = _make_image_result(
            detected_damage="front bumper dent, scratches on hood"
        )
        report = _make_report(
            damage_description="Front bumper severely dented. Scratches on the hood."
        )
        flag = _check_damage_consistency([img], report)
        assert not flag.triggered

    def test_inconsistent_damage_flags(self):
        img = _make_image_result(
            detected_damage="rear window shattered, trunk crushed"
        )
        report = _make_report(
            damage_description="Minor scratch on left door."
        )
        flag = _check_damage_consistency([img], report)
        assert flag.triggered
        assert flag.score_contribution == WEIGHT_CONSISTENCY

    def test_no_report_damage_skipped(self):
        img = _make_image_result()
        report = _make_report(damage_description="")
        flag = _check_damage_consistency([img], report)
        assert not flag.triggered


# ═══════════════════════════════════════════════════════════════════════
# Full analyzer integration
# ═══════════════════════════════════════════════════════════════════════

class TestAnalyzer:
    def test_clean_claim(self):
        """All evidence is consistent → CLEAN with score 0."""
        img = _make_image_result(
            datetime_original=datetime(2026, 3, 15, 15, 0),
            gps_lat=5.5610,
            gps_lon=-0.1880,
            detected_damage="front bumper dent, scratches on hood",
        )
        report = _make_report()
        result = analyze([img], report, claim_id=1)
        assert result.status == "CLEAN"
        assert result.risk_score == 0
        assert result.claim_id == 1

    def test_fully_flagged_claim(self):
        """All rules triggered → FLAGGED with max score 100."""
        img = _make_image_result(
            datetime_original=datetime(2026, 3, 20, 14, 30),  # 5 days late
            gps_lat=6.6885,  # Kumasi
            gps_lon=-1.6244,
            software="Adobe Photoshop",
            is_edited=True,
            detected_damage="rear window shattered",  # mismatch
        )
        report = _make_report(
            damage_description="Minor scratch on left door."
        )
        result = analyze([img], report, claim_id=42)
        assert result.status == "FLAGGED"
        assert result.risk_score == 100
        assert len([f for f in result.flags if f.triggered]) == 4

    def test_partial_flags(self):
        """Only time flag triggered → score = 30."""
        img = _make_image_result(
            datetime_original=datetime(2026, 3, 18, 14, 30),  # 3 days late
            gps_lat=5.5610,
            gps_lon=-0.1880,
            detected_damage="front bumper dent, scratches on hood",
        )
        report = _make_report()
        result = analyze([img], report, claim_id=5)
        assert result.risk_score == WEIGHT_TIME
        assert result.status == "CLEAN"  # 30 < 50

    def test_no_exif_all_inconclusive(self):
        """Images with no EXIF → no flags, CLEAN."""
        img = _make_image_result(
            datetime_original=None,
            gps_lat=None,
            gps_lon=None,
            detected_damage="front bumper dent, scratches on hood",
        )
        report = _make_report()
        result = analyze([img], report, claim_id=99)
        assert result.status == "CLEAN"
        assert result.risk_score == 0
