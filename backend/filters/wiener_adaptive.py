"""Filtro Wiener Adaptativo para eliminación de ruido en imágenes médicas.

Estima media local y varianza local en una vecindad M×N, luego aplica la
fórmula de Wiener adaptativo para reducir ruido preservando bordes.

Requisitos: 2.1, 2.2, 2.3
"""

import numpy as np
from scipy.ndimage import uniform_filter


def apply_wiener_adaptive(image: np.ndarray, m: int = 3, n: int = 3) -> np.ndarray:
    """Aplica el filtro Wiener Adaptativo a una imagen en escala de grises.

    Para cada píxel, estima la media local y la varianza local en una
    vecindad de tamaño m×n. La varianza de ruido se estima como el
    promedio de todas las varianzas locales. La salida se calcula como:

        output(i,j) = mean(i,j) + max(0, (var(i,j) - noise_var) / var(i,j))
                      * (input(i,j) - mean(i,j))

    Args:
        image: Arreglo numpy 2D (imagen en escala de grises).
        m: Número de filas de la vecindad (default: 3).
        n: Número de columnas de la vecindad (default: 3).

    Returns:
        Imagen filtrada con las mismas dimensiones y dtype que la entrada.

    Raises:
        ValueError: Si la imagen no es 2D o los parámetros son inválidos.
    """
    if image.ndim != 2:
        raise ValueError(f"Se esperaba una imagen 2D, se recibió {image.ndim}D")
    if m < 1 or n < 1:
        raise ValueError(f"Los parámetros m y n deben ser >= 1, se recibió m={m}, n={n}")

    original_dtype = image.dtype
    img = image.astype(np.float64)

    # Estimar media local con filtro uniforme (vecindad m×n)
    local_mean = uniform_filter(img, size=(m, n), mode="nearest")

    # Estimar varianza local: E[X^2] - (E[X])^2
    local_mean_sq = uniform_filter(img ** 2, size=(m, n), mode="nearest")
    local_var = local_mean_sq - local_mean ** 2
    # Asegurar que la varianza no sea negativa por errores numéricos
    local_var = np.maximum(local_var, 0.0)

    # Estimar varianza de ruido como el promedio de las varianzas locales
    noise_var = np.mean(local_var)

    # Aplicar fórmula de Wiener adaptativo
    # factor = max(0, (var_local - noise_var) / var_local)
    # Evitar división por cero: donde var_local == 0, el factor es 0
    with np.errstate(divide="ignore", invalid="ignore"):
        factor = (local_var - noise_var) / local_var
    factor = np.where(local_var > 0, factor, 0.0)
    factor = np.maximum(factor, 0.0)

    output = local_mean + factor * (img - local_mean)

    # Clip para mantener rango válido según dtype original
    if np.issubdtype(original_dtype, np.integer):
        info = np.iinfo(original_dtype)
        output = np.clip(output, info.min, info.max)
    elif np.issubdtype(original_dtype, np.floating):
        # Para float, preservar el rango original de la imagen
        output = np.clip(output, img.min(), img.max())

    return output.astype(original_dtype)
