"""Filtro Mediana Adaptativo usando ITK para eliminación de ruido en imágenes médicas.

Implementa el algoritmo de dos niveles con ventana dinámica. Utiliza ITK
para padding de bordes y numpy para el algoritmo adaptativo.

Requisitos: 4.1, 4.2, 4.3, 4.4
"""

import itk
import numpy as np


def apply_adaptive_median(image: np.ndarray, smax: int = 7) -> np.ndarray:
    """Aplica el Filtro Mediana Adaptativo a una imagen en escala de grises.

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
    img_float = np.ascontiguousarray(image.astype(np.float32))

    # Usar ITK para padding con mirror boundary
    itk_image = itk.image_from_array(img_float, is_vector=False)
    max_half = smax // 2
    pad_filter = itk.MirrorPadImageFilter.New(itk_image)
    pad_size = itk.Size[2]()
    pad_size[0] = max_half
    pad_size[1] = max_half
    pad_filter.SetPadBound(pad_size)
    pad_filter.Update()
    padded = itk.array_from_image(pad_filter.GetOutput())

    rows, cols = img_float.shape
    output = np.empty_like(img_float)

    for i in range(rows):
        for j in range(cols):
            output[i, j] = _adaptive_pixel(padded, i + max_half, j + max_half, smax)

    if np.issubdtype(original_dtype, np.integer):
        info = np.iinfo(original_dtype)
        output = np.clip(output, info.min, info.max)

    return output.astype(original_dtype)


def _adaptive_pixel(padded, pi, pj, smax):
    """Algoritmo de dos niveles para un píxel."""
    zxy = float(padded[pi, pj])
    size = 3
    last_zmed = None

    while size <= smax:
        half = size // 2
        window = padded[pi - half:pi + half + 1, pj - half:pj + half + 1].flatten()
        window.sort()
        zmin = float(window[0])
        zmax = float(window[-1])
        n = len(window)
        zmed = float(window[n // 2])
        last_zmed = zmed

        # Nivel A
        if (zmed - zmin) > 0 and (zmed - zmax) < 0:
            # Nivel B
            if (zxy - zmin) > 0 and (zxy - zmax) < 0:
                return zxy
            else:
                return zmed
        else:
            size += 2

    return last_zmed if last_zmed is not None else zxy
