"""Tests unitarios para el motor de filtros (FilterEngine)."""

import os
import tempfile

import numpy as np
import pytest
from PIL import Image

from backend.filter_engine import FilterEngine
from backend.models import FilterResult


@pytest.fixture
def engine(tmp_path):
    """Crea un FilterEngine con directorio de salida temporal."""
    return FilterEngine(output_dir=str(tmp_path / "filtered"))


@pytest.fixture
def sample_image_path(tmp_path):
    """Crea una imagen PNG de prueba y retorna su ruta."""
    img_array = np.random.randint(0, 256, (32, 32), dtype=np.uint8)
    img = Image.fromarray(img_array)
    path = str(tmp_path / "test_image.png")
    img.save(path)
    return path


class TestFilterEngineApplyFilter:
    """Tests para FilterEngine.apply_filter."""

    def test_wiener_adaptive_returns_filter_result(self, engine, sample_image_path):
        result = engine.apply_filter(sample_image_path, "wiener_adaptive")
        assert isinstance(result, FilterResult)
        assert result.filter_type == "wiener_adaptive"
        assert result.processing_time_ms >= 0
        assert os.path.isfile(result.filtered_image_path)

    def test_proposal_median_returns_filter_result(self, engine, sample_image_path):
        result = engine.apply_filter(sample_image_path, "proposal_median")
        assert isinstance(result, FilterResult)
        assert result.filter_type == "proposal_median"
        assert os.path.isfile(result.filtered_image_path)

    def test_adaptive_median_returns_filter_result(self, engine, sample_image_path):
        result = engine.apply_filter(sample_image_path, "adaptive_median")
        assert isinstance(result, FilterResult)
        assert result.filter_type == "adaptive_median"
        assert os.path.isfile(result.filtered_image_path)

    def test_wiener_with_custom_params(self, engine, sample_image_path):
        result = engine.apply_filter(
            sample_image_path, "wiener_adaptive", {"m": 5, "n": 5}
        )
        assert isinstance(result, FilterResult)
        assert os.path.isfile(result.filtered_image_path)

    def test_adaptive_median_with_custom_smax(self, engine, sample_image_path):
        result = engine.apply_filter(
            sample_image_path, "adaptive_median", {"smax": 5}
        )
        assert isinstance(result, FilterResult)

    def test_filtered_image_preserves_dimensions(self, engine, sample_image_path):
        result = engine.apply_filter(sample_image_path, "wiener_adaptive")
        filtered_img = Image.open(result.filtered_image_path)
        original_img = Image.open(sample_image_path)
        assert filtered_img.size == original_img.size

    def test_image_id_from_filename(self, engine, sample_image_path):
        result = engine.apply_filter(sample_image_path, "proposal_median")
        assert result.image_id == "test_image"


class TestFilterEngineErrors:
    """Tests para manejo de errores del FilterEngine."""

    def test_invalid_filter_type_raises_value_error(self, engine, sample_image_path):
        with pytest.raises(ValueError, match="Tipo de filtro no válido"):
            engine.apply_filter(sample_image_path, "invalid_filter")

    def test_file_not_found_raises_error(self, engine):
        with pytest.raises(FileNotFoundError, match="Imagen no encontrada"):
            engine.apply_filter("/nonexistent/path.png", "wiener_adaptive")

    def test_invalid_image_file_raises_runtime_error(self, engine, tmp_path):
        bad_file = str(tmp_path / "bad.png")
        with open(bad_file, "w") as f:
            f.write("not an image")
        with pytest.raises(RuntimeError, match="No se pudo cargar"):
            engine.apply_filter(bad_file, "wiener_adaptive")

    def test_invalid_wiener_params_raises_value_error(self, engine, sample_image_path):
        with pytest.raises(ValueError):
            engine.apply_filter(
                sample_image_path, "wiener_adaptive", {"m": 0, "n": 3}
            )

    def test_invalid_smax_raises_value_error(self, engine, sample_image_path):
        with pytest.raises(ValueError):
            engine.apply_filter(
                sample_image_path, "adaptive_median", {"smax": 1}
            )
