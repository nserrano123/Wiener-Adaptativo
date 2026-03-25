"""Filtro Mediana Propuesto usando ITK para eliminación de ruido en imágenes médicas.

Usa vecindad 8-conectada excluyendo el píxel central para calcular la
mediana de los vecinos. Utiliza ITK para la carga/conversión de imágenes
y numpy para el cálculo de la mediana con exclusión del centro.

Requisitos: 3.1, 3.2
"""

import itk
import numpy as np


def apply_proposal_median(image: np.ndarray) -> np.ndarray:
    """Aplica el Filtro Mediana Propuesto a una imagen en escala de grises.

    Para cada píxel, calcula la mediana de sus 8 vecinos (vecindad 8-conectada)
    excluyendo el valor del píxel central.

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
    img_float = np.ascontiguousarray(image.astype(np.float32))

    # Convertir a imagen ITK y aplicar padding con ZeroFluxNeumann
    itk_image = itk.image_from_array(img_float, is_vector=False)

    # Usar itk.ConstantPadImageFilter para manejar bordes (replica borde)
    pad_filter = itk.MirrorPadImageFilter.New(itk_image)
    pad_size = itk.Size[2]()
    pad_size[0] = 1
    pad_size[1] = 1
    pad_filter.SetPadBound(pad_size)
    pad_filter.Update()
    padded = itk.array_from_image(pad_filter.GetOutput())

    rows, cols = img_float.shape
    output = np.empty_like(img_float)

    for i in range(rows):
        for j in range(cols):
            # Extraer vecindad 3×3 del padded (offset por 1 debido al padding)
            pi, pj = i + 1, j + 1
            window = padded[pi - 1:pi + 2, pj - 1:pj + 2].flatten()
            # Excluir el centro (índice 4 en ventana 3×3 aplanada)
            neighbors = np.concatenate([window[:4], window[5:]])
            output[i, j] = np.median(neighbors)

    if np.issubdtype(original_dtype, np.integer):
        info = np.iinfo(original_dtype)
        output = np.clip(output, info.min, info.max)

    return output.astype(original_dtype)
