"""Motor de filtros para procesamiento de imágenes médicas.

Orquesta la carga de imágenes, despacho al filtro correcto, medición de
tiempo de procesamiento y almacenamiento del resultado.

Requisitos: 2.4, 3.3, 6.2
"""

import os
import tempfile
import time
import uuid

import numpy as np
from PIL import Image

from backend.filters.adaptive_median import apply_adaptive_median
from backend.filters.proposal_median import apply_proposal_median
from backend.filters.wiener_adaptive import apply_wiener_adaptive
from backend.models import VALID_FILTER_TYPES, FilterResult

# NIfTI extensions
_NIFTI_EXTENSIONS = {".nii", ".nii.gz"}


def _is_nifti(path: str) -> bool:
    lower = path.lower()
    return lower.endswith(".nii.gz") or lower.endswith(".nii")


class FilterEngine:
    """Motor principal que orquesta la aplicación de filtros de imagen."""

    def __init__(self, output_dir: str | None = None) -> None:
        """Inicializa el motor de filtros.

        Args:
            output_dir: Directorio donde se guardan las imágenes filtradas.
                        Si es None, se usa un directorio temporal.
        """
        self._output_dir = output_dir or os.path.join(
            tempfile.gettempdir(), "medical_images", "filtered"
        )
        os.makedirs(self._output_dir, exist_ok=True)

    def apply_filter(
        self, image_path: str, filter_type: str, params: dict | None = None
    ) -> FilterResult:
        """Aplica el filtro especificado a la imagen y retorna el resultado.

        Args:
            image_path: Ruta al archivo de imagen a procesar.
            filter_type: Tipo de filtro a aplicar. Debe ser uno de
                         VALID_FILTER_TYPES.
            params: Parámetros específicos del filtro (opcional).

        Returns:
            FilterResult con la ruta de la imagen filtrada y métricas.

        Raises:
            FileNotFoundError: Si image_path no existe.
            ValueError: Si filter_type no es válido o los parámetros son
                        inválidos.
            RuntimeError: Si ocurre un error durante el procesamiento.
        """
        params = params or {}

        # Validar tipo de filtro
        if filter_type not in VALID_FILTER_TYPES:
            raise ValueError(
                f"Tipo de filtro no válido: '{filter_type}'. "
                f"Valores permitidos: {sorted(VALID_FILTER_TYPES)}"
            )

        # Validar que el archivo existe
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

        # Cargar imagen como arreglo numpy 2D (escala de grises)
        image = self._load_image(image_path)

        # Extraer image_id del nombre del archivo (sin extensión)
        image_id = os.path.splitext(os.path.basename(image_path))[0]

        # Medir tiempo de procesamiento y aplicar filtro
        start = time.perf_counter()
        try:
            filtered = self._dispatch(image, filter_type, params)
        except ValueError:
            raise
        except Exception as exc:
            raise RuntimeError(
                f"Error en el procesamiento de imagen: {exc}"
            ) from exc
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        # Guardar imagen filtrada
        filtered_path = self._save_image(filtered, filter_type)

        return FilterResult(
            image_id=image_id,
            filter_type=filter_type,
            filtered_image_path=filtered_path,
            processing_time_ms=round(elapsed_ms, 2),
        )

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    @staticmethod
    def _load_image(image_path: str) -> np.ndarray:
        """Carga una imagen y la convierte a escala de grises 2D."""
        try:
            if _is_nifti(image_path):
                import nibabel as nib
                nii = nib.load(image_path)
                data = np.asarray(nii.dataobj, dtype=np.float64)
                # Take the middle slice of the largest dimension for 3D volumes
                if data.ndim == 3:
                    mid = data.shape[2] // 2
                    data = data[:, :, mid]
                elif data.ndim > 3:
                    # 4D+ : take first volume, middle slice
                    data = data[:, :, data.shape[2] // 2, 0]
                # Normalize to 0-255 uint8
                dmin, dmax = data.min(), data.max()
                if dmax - dmin > 0:
                    data = (data - dmin) / (dmax - dmin) * 255.0
                return data.astype(np.uint8)
            else:
                img = Image.open(image_path).convert("L")
                return np.array(img)
        except Exception as exc:
            raise RuntimeError(
                f"No se pudo cargar la imagen '{image_path}': {exc}"
            ) from exc

    @staticmethod
    def _dispatch(
        image: np.ndarray, filter_type: str, params: dict
    ) -> np.ndarray:
        """Despacha al filtro correcto según filter_type."""
        if filter_type == "wiener_adaptive":
            m = int(params.get("m", 3))
            n = int(params.get("n", 3))
            return apply_wiener_adaptive(image, m=m, n=n)

        if filter_type == "proposal_median":
            return apply_proposal_median(image)

        if filter_type == "adaptive_median":
            smax = int(params.get("smax", 7))
            return apply_adaptive_median(image, smax=smax)

        # Nunca debería llegar aquí gracias a la validación previa
        raise ValueError(f"Filtro no implementado: {filter_type}")

    def _save_image(self, image: np.ndarray, filter_type: str) -> str:
        """Guarda la imagen filtrada como PNG y retorna la ruta."""
        filename = f"{filter_type}_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(self._output_dir, filename)
        img = Image.fromarray(image)
        img.save(output_path)
        return output_path
