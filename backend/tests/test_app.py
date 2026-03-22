"""Tests para la aplicación Flask y endpoints."""

import io
import logging

import pytest
from PIL import Image

from backend.app import create_app, image_store


@pytest.fixture
def client():
    """Crea un cliente de test para la aplicación Flask."""
    app = create_app()
    app.config["TESTING"] = True
    image_store.clear()
    with app.test_client() as client:
        yield client


def _make_png_bytes(width=10, height=10):
    """Helper: genera bytes de una imagen PNG válida."""
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def _make_jpeg_bytes(width=10, height=10):
    """Helper: genera bytes de una imagen JPEG válida."""
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


# --- Health check tests ---


def test_health_check_returns_ok(client):
    """GET /api/health retorna status ok con código 200."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"status": "ok"}


def test_health_check_content_type(client):
    """GET /api/health retorna content-type JSON."""
    response = client.get("/api/health")
    assert response.content_type == "application/json"


# --- Upload endpoint tests ---


def test_upload_valid_png(client):
    """POST /api/upload con PNG válido retorna 200 con image_id y preview_url."""
    data = {"file": (io.BytesIO(_make_png_bytes()), "test.png")}
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    json_data = response.get_json()
    assert "image_id" in json_data
    assert json_data["image_id"] != ""
    assert "preview_url" in json_data
    assert json_data["preview_url"] == f"/api/images/{json_data['image_id']}"


def test_upload_valid_jpeg(client):
    """POST /api/upload con JPEG válido retorna 200."""
    data = {"file": (io.BytesIO(_make_jpeg_bytes()), "photo.jpg")}
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    json_data = response.get_json()
    assert "image_id" in json_data


def test_upload_stores_metadata(client):
    """POST /api/upload almacena metadatos en image_store."""
    data = {"file": (io.BytesIO(_make_png_bytes(20, 30)), "scan.png")}
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    image_id = response.get_json()["image_id"]
    assert image_id in image_store
    stored = image_store[image_id]
    assert stored.format == "PNG"
    assert stored.filename == "scan.png"
    assert stored.dimensions == (20, 30)


def test_upload_no_file_returns_400(client):
    """POST /api/upload sin archivo retorna 400."""
    response = client.post("/api/upload", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    json_data = response.get_json()
    assert "error" in json_data
    assert json_data["error"] == "No se proporcionó archivo"


def test_upload_text_file_returns_400(client):
    """POST /api/upload con archivo de texto retorna 400."""
    data = {"file": (io.BytesIO(b"hello world"), "readme.txt")}
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["error"] == "Formato de archivo no soportado"


def test_upload_corrupt_png_returns_400(client):
    """POST /api/upload con PNG corrupto retorna 400."""
    data = {"file": (io.BytesIO(b"not a real png"), "fake.png")}
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["error"] == "Formato de archivo no soportado"


# --- Helper: upload an image and return image_id ---


def _upload_png(client, width=10, height=10):
    """Upload a PNG image and return the image_id."""
    data = {"file": (io.BytesIO(_make_png_bytes(width, height)), "test.png")}
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    return response.get_json()["image_id"]


# --- GET /api/images/<image_id> tests ---


def test_get_image_returns_file(client):
    """GET /api/images/<image_id> retorna el archivo de imagen."""
    image_id = _upload_png(client)
    response = client.get(f"/api/images/{image_id}")
    assert response.status_code == 200


def test_get_image_not_found(client):
    """GET /api/images/<image_id> con id inexistente retorna 404."""
    response = client.get("/api/images/nonexistent-id")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Imagen no encontrada"


# --- POST /api/filter tests ---


def test_filter_valid_request(client):
    """POST /api/filter con solicitud válida retorna 200 con imagen."""
    image_id = _upload_png(client, 20, 20)
    response = client.post("/api/filter", json={
        "image_id": image_id,
        "filter_type": "proposal_median",
        "params": {},
    })
    assert response.status_code == 200
    assert response.content_type == "image/png"
    assert len(response.data) > 0


def test_filter_wiener_with_params(client):
    """POST /api/filter con filtro wiener y parámetros válidos retorna 200."""
    image_id = _upload_png(client, 20, 20)
    response = client.post("/api/filter", json={
        "image_id": image_id,
        "filter_type": "wiener_adaptive",
        "params": {"m": 3, "n": 3},
    })
    assert response.status_code == 200
    assert response.content_type == "image/png"


def test_filter_adaptive_median_with_params(client):
    """POST /api/filter con filtro adaptive_median y parámetros válidos retorna 200."""
    image_id = _upload_png(client, 20, 20)
    response = client.post("/api/filter", json={
        "image_id": image_id,
        "filter_type": "adaptive_median",
        "params": {"smax": 7},
    })
    assert response.status_code == 200
    assert response.content_type == "image/png"


def test_filter_image_not_found(client):
    """POST /api/filter con image_id inexistente retorna 404."""
    response = client.post("/api/filter", json={
        "image_id": "nonexistent-id",
        "filter_type": "proposal_median",
        "params": {},
    })
    assert response.status_code == 404
    assert response.get_json()["error"] == "Imagen no encontrada"


def test_filter_invalid_filter_type(client):
    """POST /api/filter con filter_type inválido retorna 400."""
    image_id = _upload_png(client)
    response = client.post("/api/filter", json={
        "image_id": image_id,
        "filter_type": "invalid_filter",
        "params": {},
    })
    assert response.status_code == 400
    assert response.get_json()["error"] == "Tipo de filtro no válido"


def test_filter_wiener_invalid_params_m_zero(client):
    """POST /api/filter con m=0 para wiener retorna 400."""
    image_id = _upload_png(client)
    response = client.post("/api/filter", json={
        "image_id": image_id,
        "filter_type": "wiener_adaptive",
        "params": {"m": 0, "n": 3},
    })
    assert response.status_code == 400
    assert "Parámetros inválidos" in response.get_json()["error"]


def test_filter_wiener_invalid_params_n_negative(client):
    """POST /api/filter con n negativo para wiener retorna 400."""
    image_id = _upload_png(client)
    response = client.post("/api/filter", json={
        "image_id": image_id,
        "filter_type": "wiener_adaptive",
        "params": {"m": 3, "n": -1},
    })
    assert response.status_code == 400
    assert "Parámetros inválidos" in response.get_json()["error"]


def test_filter_adaptive_median_smax_too_small(client):
    """POST /api/filter con smax < 3 para adaptive_median retorna 400."""
    image_id = _upload_png(client)
    response = client.post("/api/filter", json={
        "image_id": image_id,
        "filter_type": "adaptive_median",
        "params": {"smax": 1},
    })
    assert response.status_code == 400
    assert "Parámetros inválidos" in response.get_json()["error"]


def test_filter_no_json_body(client):
    """POST /api/filter sin cuerpo JSON retorna 400."""
    response = client.post("/api/filter", data="not json", content_type="text/plain")
    assert response.status_code == 400


def test_filter_missing_image_id(client):
    """POST /api/filter sin image_id retorna 400."""
    response = client.post("/api/filter", json={
        "filter_type": "proposal_median",
    })
    assert response.status_code == 400


# --- Global error handler tests ---


def test_413_request_entity_too_large(client):
    """POST /api/upload con archivo demasiado grande retorna 413."""
    # Set a very small max content length to trigger 413
    app = create_app()
    app.config["TESTING"] = True
    app.config["MAX_CONTENT_LENGTH"] = 10  # 10 bytes
    image_store.clear()
    with app.test_client() as small_client:
        large_data = b"x" * 100
        data = {"file": (io.BytesIO(large_data), "big.png")}
        response = small_client.post(
            "/api/upload", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 413
        json_data = response.get_json()
        assert json_data["error"] == "La imagen excede el tamaño máximo permitido"


def test_404_global_handler_unknown_route(client):
    """GET a una ruta inexistente retorna 404 con JSON."""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data["error"] == "Imagen no encontrada"


def test_500_internal_error_in_filter(client, monkeypatch):
    """POST /api/filter que causa excepción interna retorna 500."""
    image_id = _upload_png(client, 20, 20)

    def _boom(*args, **kwargs):
        raise RuntimeError("Unexpected ITK crash")

    from backend import filter_engine
    monkeypatch.setattr(filter_engine.FilterEngine, "apply_filter", _boom)

    response = client.post("/api/filter", json={
        "image_id": image_id,
        "filter_type": "proposal_median",
        "params": {},
    })
    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data["error"] == "Error en el procesamiento de imagen"


def test_structured_logging_on_filter_error(client, caplog):
    """Verifica que errores en /api/filter generan logs con contexto."""
    with caplog.at_level(logging.WARNING):
        response = client.post("/api/filter", json={
            "image_id": "nonexistent-id",
            "filter_type": "proposal_median",
            "params": {},
        })
    assert response.status_code == 404
    assert any("nonexistent-id" in record.message for record in caplog.records)


def test_structured_logging_on_invalid_filter_type(client, caplog):
    """Verifica que filter_type inválido genera log con contexto."""
    image_id = _upload_png(client)
    with caplog.at_level(logging.WARNING):
        response = client.post("/api/filter", json={
            "image_id": image_id,
            "filter_type": "bad_filter",
            "params": {},
        })
    assert response.status_code == 400
    assert any("bad_filter" in record.message for record in caplog.records)
