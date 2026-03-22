"""Tests para los modelos de datos."""

import pytest
from datetime import datetime

from backend.models import (
    VALID_FILTER_TYPES,
    FilterRequest,
    FilterResult,
    UploadedImage,
)


class TestUploadedImage:
    def test_create_uploaded_image(self):
        now = datetime.now()
        img = UploadedImage(
            image_id="abc-123",
            filename="scan.png",
            file_path="/tmp/scan.png",
            format="PNG",
            dimensions=(512, 512),
            uploaded_at=now,
        )
        assert img.image_id == "abc-123"
        assert img.filename == "scan.png"
        assert img.file_path == "/tmp/scan.png"
        assert img.format == "PNG"
        assert img.dimensions == (512, 512)
        assert img.uploaded_at == now


class TestFilterRequest:
    @pytest.mark.parametrize("ft", sorted(VALID_FILTER_TYPES))
    def test_valid_filter_types(self, ft):
        req = FilterRequest(image_id="img-1", filter_type=ft)
        assert req.filter_type == ft
        assert req.params == {}

    def test_invalid_filter_type_raises(self):
        with pytest.raises(ValueError, match="Tipo de filtro no válido"):
            FilterRequest(image_id="img-1", filter_type="invalid_filter")

    def test_custom_params(self):
        req = FilterRequest(
            image_id="img-1",
            filter_type="wiener_adaptive",
            params={"m": 5, "n": 5},
        )
        assert req.params == {"m": 5, "n": 5}


class TestFilterResult:
    def test_create_filter_result(self):
        result = FilterResult(
            image_id="img-1",
            filter_type="adaptive_median",
            filtered_image_path="/tmp/filtered.png",
            processing_time_ms=42.5,
        )
        assert result.image_id == "img-1"
        assert result.filter_type == "adaptive_median"
        assert result.filtered_image_path == "/tmp/filtered.png"
        assert result.processing_time_ms == 42.5


class TestValidFilterTypes:
    def test_contains_expected_types(self):
        assert VALID_FILTER_TYPES == {
            "wiener_adaptive",
            "proposal_median",
            "adaptive_median",
        }
