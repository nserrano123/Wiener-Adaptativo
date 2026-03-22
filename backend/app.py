"""Aplicación Flask para procesamiento de filtros de imágenes médicas."""

import logging
import os
import tempfile
import traceback
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from PIL import Image
from werkzeug.exceptions import RequestEntityTooLarge
import numpy as np

from backend.filter_engine import FilterEngine
from backend.models import VALID_FILTER_TYPES, UploadedImage

# Structured logging configuration
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# In-memory store for uploaded images keyed by image_id
image_store: dict[str, UploadedImage] = {}

# Supported file extensions and their format labels
ALLOWED_EXTENSIONS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".dcm": "DICOM",
    ".nii": "NIfTI",
}

# Magic bytes for format detection
DICOM_MAGIC = b"DICM"
NIFTI_MAGIC_1 = b"\x1c\x01"  # 348 as little-endian int16 (NIfTI-1 header size)
NIFTI_MAGIC_2 = b"n+1\x00"


def _detect_format(file_storage):
    """Detect image format from file extension and content validation.

    Returns (format_label, dimensions) on success, or (None, None) on failure.
    """
    filename = file_storage.filename or ""
    _, ext = os.path.splitext(filename.lower())

    # Handle .nii.gz as a special case
    if filename.lower().endswith(".nii.gz"):
        ext = ".nii"

    if ext not in ALLOWED_EXTENSIONS:
        return None, None

    fmt = ALLOWED_EXTENSIONS[ext]

    if fmt in ("PNG", "JPEG"):
        try:
            file_storage.stream.seek(0)
            img = Image.open(file_storage.stream)
            img.verify()
            dims = img.size  # (width, height)
            file_storage.stream.seek(0)
            return fmt, dims
        except Exception:
            return None, None

    if fmt == "DICOM":
        file_storage.stream.seek(128)
        magic = file_storage.stream.read(4)
        file_storage.stream.seek(0)
        if magic != DICOM_MAGIC:
            return None, None
        return fmt, (0, 0)

    if fmt == "NIfTI":
        # For .nii files, accept based on extension (content may be gzipped)
        file_storage.stream.seek(0)
        return fmt, (0, 0)

    return None, None


def create_app():
    """Crea y configura la aplicación Flask."""
    app = Flask(__name__)

    CORS(app)

    app.config["UPLOAD_FOLDER"] = os.path.join(tempfile.gettempdir(), "medical_images")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"})

    @app.route("/api/upload", methods=["POST"])
    def upload_image():
        if "file" not in request.files:
            return jsonify({"error": "No se proporcionó archivo"}), 400

        file = request.files["file"]

        if file.filename == "" or file.filename is None:
            return jsonify({"error": "No se proporcionó archivo"}), 400

        fmt, dims = _detect_format(file)
        if fmt is None:
            return jsonify({"error": "Formato de archivo no soportado"}), 400

        image_id = str(uuid.uuid4())
        original_filename = file.filename
        _, ext = os.path.splitext(original_filename.lower())
        if original_filename.lower().endswith(".nii.gz"):
            ext = ".nii.gz"

        save_path = os.path.join(app.config["UPLOAD_FOLDER"], image_id + ext)
        file.save(save_path)

        uploaded = UploadedImage(
            image_id=image_id,
            filename=original_filename,
            file_path=save_path,
            format=fmt,
            dimensions=dims,
            uploaded_at=datetime.now(timezone.utc),
        )
        image_store[image_id] = uploaded

        return jsonify({
            "image_id": image_id,
            "preview_url": f"/api/images/{image_id}",
        }), 200

    @app.route("/api/images/<image_id>", methods=["GET"])
    def get_image(image_id):
        if image_id not in image_store:
            return jsonify({"error": "Imagen no encontrada"}), 404
        uploaded = image_store[image_id]
        # NIfTI files can't be displayed directly in the browser — convert to PNG
        if uploaded.format == "NIfTI":
            try:
                import io as _io
                import nibabel as nib
                nii = nib.load(uploaded.file_path)
                data = np.asarray(nii.dataobj, dtype=np.float64)
                if data.ndim == 3:
                    data = data[:, :, data.shape[2] // 2]
                elif data.ndim > 3:
                    data = data[:, :, data.shape[2] // 2, 0]
                dmin, dmax = data.min(), data.max()
                if dmax - dmin > 0:
                    data = (data - dmin) / (dmax - dmin) * 255.0
                img = Image.fromarray(data.astype(np.uint8))
                buf = _io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                return send_file(buf, mimetype="image/png")
            except Exception:
                return jsonify({"error": "Error al convertir imagen NIfTI"}), 500
        return send_file(uploaded.file_path)

    @app.route("/api/filter", methods=["POST"])
    def apply_filter():
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({"error": "Cuerpo JSON requerido"}), 400

        image_id = body.get("image_id")
        filter_type = body.get("filter_type")
        params = body.get("params", {})

        ctx = {"image_id": image_id, "filter_type": filter_type}

        if not image_id:
            logger.warning("Missing image_id in filter request", extra={"context": ctx})
            return jsonify({"error": "image_id es requerido"}), 400

        if image_id not in image_store:
            logger.warning("Image not found: %s", image_id, extra={"context": ctx})
            return jsonify({"error": "Imagen no encontrada"}), 404

        if filter_type not in VALID_FILTER_TYPES:
            logger.warning("Invalid filter_type: %s", filter_type, extra={"context": ctx})
            return jsonify({"error": "Tipo de filtro no válido"}), 400

        # Validate parameters per filter type
        validation_error = _validate_filter_params(filter_type, params)
        if validation_error:
            logger.warning("Invalid params: %s", validation_error, extra={"context": ctx})
            return jsonify({"error": validation_error}), 400

        uploaded = image_store[image_id]
        engine = FilterEngine()

        try:
            result = engine.apply_filter(
                uploaded.file_path, filter_type, params
            )
        except (ValueError, FileNotFoundError) as exc:
            logger.error(
                "Filter error: %s", exc,
                extra={"context": {**ctx, "stack_trace": traceback.format_exc()}},
            )
            return jsonify({"error": str(exc)}), 400
        except Exception:
            logger.error(
                "Internal processing error",
                extra={"context": {**ctx, "stack_trace": traceback.format_exc()}},
            )
            return jsonify({"error": "Error en el procesamiento de imagen"}), 500

        logger.info(
            "Filter applied successfully in %.2fms",
            result.processing_time_ms,
            extra={"context": ctx},
        )
        return send_file(
            result.filtered_image_path,
            mimetype="image/png",
            as_attachment=False,
        )

    # --- Global error handlers ---

    @app.errorhandler(400)
    def bad_request(error):
        logger.warning("Bad request: %s", error, extra={"context": {}})
        return jsonify({"error": getattr(error, "description", "Solicitud inválida")}), 400

    @app.errorhandler(404)
    def not_found(error):
        logger.warning("Not found: %s %s", request.method, request.path, extra={"context": {}})
        return jsonify({"error": "Imagen no encontrada"}), 404

    @app.errorhandler(413)
    @app.errorhandler(RequestEntityTooLarge)
    def request_entity_too_large(error):
        logger.warning("Upload too large: %s", request.path, extra={"context": {}})
        return jsonify({"error": "La imagen excede el tamaño máximo permitido"}), 413

    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(
            "Internal server error: %s",
            error,
            extra={"context": {"stack_trace": traceback.format_exc()}},
        )
        return jsonify({"error": "Error en el procesamiento de imagen"}), 500

    return app


def _validate_filter_params(filter_type: str, params: dict) -> str | None:
    """Validate filter-specific parameters. Returns error message or None."""
    if filter_type == "wiener_adaptive":
        try:
            m = int(params.get("m", 3))
            n = int(params.get("n", 3))
        except (TypeError, ValueError):
            return "Parámetros inválidos: m y n deben ser enteros"
        if m < 1 or n < 1:
            return "Parámetros inválidos: m y n deben ser >= 1"

    elif filter_type == "adaptive_median":
        try:
            smax = int(params.get("smax", 7))
        except (TypeError, ValueError):
            return "Parámetros inválidos: smax debe ser un entero"
        if smax < 3:
            return "Parámetros inválidos: smax debe ser >= 3"

    return None


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
