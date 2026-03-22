"""Filtro Mediana Propuesto para eliminación de ruido en imágenes médicas.

Usa vecindad 8-conectada excluyendo el píxel central para calcular la
mediana de los vecinos. Sin parámetros configurables.

Requisitos: 3.1, 3.2
"""

import numpy as np


def apply_proposal_median(image: np.ndarray) -> np.ndarray:
    """Aplica el Filtro Mediana Propuesto a una imagen en escala de grises.

    Para cada píxel, calcula la mediana de sus vecinos en la vecindad
    8-conectada (los 8 píxeles adyacentes), excluyendo el valor del
    píxel central. Para píxeles de borde/esquina, se usan solo los
    vecinos disponibles.

    Args:
        image: Arreglo numpy 2D (imagen en escala de grises).

    Returns:
        Imagen filtrada con las mismas dimensiones y dtype que la entrada.

    Raises:
        ValueError: Si la imagen no es 2D.
    """
    if image.ndim != 2:
        raise ValueError(f"Se esperaba una imagen 2D, se recibió {image.ndim}D")

    original_dtype = image.dtype
    rows, cols = image.shape
    img = image.astype(np.float64)
    output = np.empty_like(img)

    for i in range(rows):
        for j in range(cols):
            neighbors = []
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == 0 and dj == 0:
                        continue
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols:
                        neighbors.append(img[ni, nj])
            output[i, j] = np.median(neighbors)

    # Clip para mantener rango válido según dtype original
    if np.issubdtype(original_dtype, np.integer):
        info = np.iinfo(original_dtype)
        output = np.clip(output, info.min, info.max)

    return output.astype(original_dtype)
