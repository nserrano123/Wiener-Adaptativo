"""Modelos de datos para la aplicación de filtros de imágenes médicas."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple

VALID_FILTER_TYPES = {"wiener_adaptive", "proposal_median", "adaptive_median"}


@dataclass
class UploadedImage:
    """Representa una imagen subida al sistema."""

    image_id: str
    filename: str
    file_path: str
    format: str
    dimensions: Tuple[int, int]
    uploaded_at: datetime


@dataclass
class FilterRequest:
    """Solicitud de aplicación de filtro sobre una imagen."""

    image_id: str
    filter_type: str
    params: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.filter_type not in VALID_FILTER_TYPES:
            raise ValueError(
                f"Tipo de filtro no válido: '{self.filter_type}'. "
                f"Valores permitidos: {sorted(VALID_FILTER_TYPES)}"
            )


@dataclass
class FilterResult:
    """Resultado de la aplicación de un filtro."""

    image_id: str
    filter_type: str
    filtered_image_path: str
    processing_time_ms: float
