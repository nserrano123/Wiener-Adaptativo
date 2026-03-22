"""Filtro Mediana Adaptativo para eliminación de ruido en imágenes médicas.

Implementa el algoritmo de dos niveles con ventana dinámica. En el Nivel A
se evalúa si la mediana es un valor no-impulso; en el Nivel B se decide si
conservar el píxel original o reemplazarlo por la mediana.

Requisitos: 4.1, 4.2, 4.3, 4.4
"""

import numpy as np


def apply_adaptive_median(image: np.ndarray, smax: int = 7) -> np.ndarray:
    """Aplica el Filtro Mediana Adaptativo a una imagen en escala de grises.

    Para cada píxel, ejecuta el algoritmo de dos niveles:

    Nivel A:
      A1 = Zmed - Zmin
      A2 = Zmed - Zmax
      Si A1 > 0 AND A2 < 0 → ir a Nivel B
      Si no → incrementar tamaño de ventana
        Si tamaño <= Smax → repetir Nivel A
        Si no → salida = Zmed

    Nivel B:
      B1 = Zxy - Zmin
      B2 = Zxy - Zmax
      Si B1 > 0 AND B2 < 0 → salida = Zxy
      Si no → salida = Zmed

    Args:
        image: Arreglo numpy 2D (imagen en escala de grises).
        smax: Tamaño máximo de ventana (default: 7). Debe ser >= 3.

    Returns:
        Imagen filtrada con las mismas dimensiones y dtype que la entrada.

    Raises:
        ValueError: Si la imagen no es 2D o smax < 3.
    """
    if image.ndim != 2:
        raise ValueError(f"Se esperaba una imagen 2D, se recibió {image.ndim}D")
    if smax < 3:
        raise ValueError(f"smax debe ser >= 3, se recibió {smax}")

    original_dtype = image.dtype
    rows, cols = image.shape
    img = image.astype(np.float64)
    output = np.empty_like(img)

    for i in range(rows):
        for j in range(cols):
            output[i, j] = _adaptive_median_pixel(img, i, j, rows, cols, smax)

    # Clip para mantener rango válido según dtype original
    if np.issubdtype(original_dtype, np.integer):
        info = np.iinfo(original_dtype)
        output = np.clip(output, info.min, info.max)

    return output.astype(original_dtype)


def _adaptive_median_pixel(
    img: np.ndarray, i: int, j: int, rows: int, cols: int, smax: int
) -> float:
    """Ejecuta el algoritmo de mediana adaptativa para un solo píxel.

    Args:
        img: Imagen completa como arreglo float64.
        i: Fila del píxel actual.
        j: Columna del píxel actual.
        rows: Número total de filas.
        cols: Número total de columnas.
        smax: Tamaño máximo de ventana.

    Returns:
        Valor filtrado para el píxel (i, j).
    """
    zxy = img[i, j]
    size = 3  # Tamaño inicial de ventana

    while size <= smax:
        half = size // 2
        # Extraer ventana con manejo de bordes (recorte a límites de imagen)
        r_min = max(i - half, 0)
        r_max = min(i + half, rows - 1)
        c_min = max(j - half, 0)
        c_max = min(j + half, cols - 1)

        window = img[r_min : r_max + 1, c_min : c_max + 1]

        zmin = window.min()
        zmax = window.max()
        zmed = np.median(window)

        # Nivel A
        a1 = zmed - zmin
        a2 = zmed - zmax
        if a1 > 0 and a2 < 0:
            # Zmed no es impulso → ir a Nivel B
            b1 = zxy - zmin
            b2 = zxy - zmax
            if b1 > 0 and b2 < 0:
                return zxy  # Píxel original no es impulso
            else:
                return zmed  # Reemplazar con mediana
        else:
            # Incrementar tamaño de ventana
            size += 2

    # Se alcanzó Smax sin encontrar mediana no-impulso → retornar Zmed de Smax
    half = smax // 2
    r_min = max(i - half, 0)
    r_max = min(i + half, rows - 1)
    c_min = max(j - half, 0)
    c_max = min(j + half, cols - 1)
    window = img[r_min : r_max + 1, c_min : c_max + 1]
    return np.median(window)
