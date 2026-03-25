"""Filtro Wiener Adaptativo usando ITK para eliminación de ruido en imágenes médicas.

Estima media local y varianza local en una vecindad M×N, luego aplica la
fórmula de Wiener adaptativo para reducir ruido preservando bordes.

Requisitos: 2.1, 2.2, 2.3
"""

import itk
import numpy as np


def apply_wiener_adaptive(image: np.ndarray, m: int = 3, n: int = 3) -> np.ndarray:
    """Aplica el filtro Wiener Adaptativo a una imagen en escala de grises usando ITK.

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
    img_float = np.ascontiguousarray(image.astype(np.float32))

    # Convertir numpy a imagen ITK (is_vector=False para 2D escalar)
    itk_image = itk.image_from_array(img_float, is_vector=False)

    # Calcular media local usando itk.MeanImageFilter con vecindad M×N
    radius_mean = [n // 2, m // 2]  # ITK usa [x, y] = [cols, rows]
    mean_filter = itk.MeanImageFilter.New(itk_image)
    mean_filter.SetRadius(radius_mean)
    mean_filter.Update()
    local_mean = itk.array_view_from_image(mean_filter.GetOutput()).astype(np.float64)

    # Calcular E[X^2] para la varianza local
    square_filter = itk.SquareImageFilter.New(itk_image)
    square_filter.Update()
    squared_itk = square_filter.GetOutput()

    # Media de X^2
    mean_sq_filter = itk.MeanImageFilter.New(squared_itk)
    mean_sq_filter.SetRadius(radius_mean)
    mean_sq_filter.Update()
    local_mean_sq = itk.array_view_from_image(mean_sq_filter.GetOutput()).astype(np.float64)

    img_f64 = img_float.astype(np.float64)

    # Varianza local = E[X^2] - (E[X])^2
    local_var = local_mean_sq - local_mean ** 2
    local_var = np.maximum(local_var, 0.0)

    # Estimar varianza de ruido como promedio de varianzas locales
    noise_var = np.mean(local_var)

    # Aplicar fórmula de Wiener adaptativo
    with np.errstate(divide="ignore", invalid="ignore"):
        factor = (local_var - noise_var) / local_var
    factor = np.where(local_var > 0, factor, 0.0)
    factor = np.maximum(factor, 0.0)

    output = local_mean + factor * (img_f64 - local_mean)

    # Clip para mantener rango válido según dtype original
    if np.issubdtype(original_dtype, np.integer):
        info = np.iinfo(original_dtype)
        output = np.clip(output, info.min, info.max)
    elif np.issubdtype(original_dtype, np.floating):
        output = np.clip(output, img_f64.min(), img_f64.max())

    return output.astype(original_dtype)
