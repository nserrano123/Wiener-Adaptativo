# Filtros de Eliminación de Ruido en Imágenes Médicas

## Contexto

Las imágenes de resonancia magnética (MR) están sujetas a ruido durante su adquisición, lo que puede dificultar el diagnóstico clínico. Los filtros de eliminación de ruido buscan reducir este ruido preservando los bordes y estructuras anatómicas relevantes. Este documento describe tres filtros implementados en la aplicación: Wiener Adaptativo, Mediana Propuesto y Mediana Adaptativo.

---

## 1. Filtro Wiener Adaptativo

### Concepto

El filtro Wiener es un filtro estadístico óptimo que minimiza el error cuadrático medio entre la imagen original (sin ruido) y la imagen estimada. La versión adaptativa ajusta su comportamiento localmente según las estadísticas de cada vecindad de píxeles, lo que le permite preservar bordes en zonas de alto contraste mientras suaviza zonas homogéneas.

### Fundamento Matemático

Para cada píxel en la posición (i, j), el filtro calcula:

- **Media local** (μ): promedio de los valores de píxel en una vecindad de tamaño M×N centrada en (i, j).
- **Varianza local** (σ²): varianza de los valores en esa misma vecindad.
- **Varianza de ruido** (σₙ²): estimada como el promedio de todas las varianzas locales de la imagen completa.

La salida se calcula como:

```
salida(i,j) = μ(i,j) + max(0, (σ²(i,j) - σₙ²) / σ²(i,j)) × (entrada(i,j) - μ(i,j))
```

**Interpretación:**

- En zonas homogéneas (varianza local ≈ varianza de ruido), el factor tiende a 0 y la salida se acerca a la media local → suavizado fuerte.
- En zonas con bordes (varianza local >> varianza de ruido), el factor tiende a 1 y la salida se acerca al valor original → preservación de detalle.

### Parámetros

- **M** (filas de la vecindad): controla el tamaño vertical de la ventana de análisis.
- **N** (columnas de la vecindad): controla el tamaño horizontal.
- Valores por defecto: M=3, N=3.
- Ventanas más grandes producen mayor suavizado pero pueden difuminar bordes finos.

### Implementación en ITK

En ITK, el filtro Wiener adaptativo no existe como un filtro predefinido con ese nombre exacto, pero se puede implementar combinando los siguientes componentes:

- **itk::MeanImageFilter**: calcula la media local en una vecindad rectangular, equivalente a estimar μ(i,j) para cada píxel.
- **itk::NeighborhoodOperatorImageFilter** con un kernel uniforme: permite calcular estadísticas locales como E[X²] necesarias para la varianza.
- **itk::SubtractImageFilter**, **itk::MultiplyImageFilter**, **itk::DivideImageFilter**: operaciones aritméticas píxel a píxel para ensamblar la fórmula de Wiener.
- **itk::StatisticsImageFilter**: calcula estadísticas globales (como el promedio de varianzas locales para estimar σₙ²).

El flujo en ITK sería: calcular la imagen de medias locales, calcular la imagen de varianzas locales (E[X²] - μ²), estimar la varianza de ruido como la media global de las varianzas locales, y finalmente aplicar la fórmula de Wiener combinando las imágenes intermedias con filtros aritméticos.

La ventaja de ITK es que opera con pipelines conectables donde cada filtro se encadena al siguiente, y soporta nativamente imágenes médicas en formatos como NIfTI y DICOM con sus metadatos.

---

## 2. Filtro Mediana Propuesto

### Concepto

El filtro de mediana propuesto es una variante del filtro de mediana clásico. En lugar de incluir el píxel central en el cálculo de la mediana, lo excluye. Para cada píxel, se toman únicamente los 8 vecinos de la vecindad 8-conectada (los píxeles adyacentes horizontal, vertical y diagonalmente), se calcula la mediana de esos 8 valores, y se reemplaza el píxel central con ese resultado.

### Fundamento

- **Vecindad 8-conectada**: los 8 píxeles que rodean al píxel central en una ventana 3×3.
- Al excluir el píxel central, el filtro es más agresivo contra el ruido impulsivo (sal y pimienta), ya que un píxel corrupto no influye en su propia corrección.
- Para píxeles en los bordes de la imagen, se usan solo los vecinos disponibles (5 vecinos en bordes, 3 en esquinas).

### Parámetros

- No tiene parámetros configurables. La vecindad es siempre 3×3 con exclusión del centro.

### Implementación en ITK

ITK ofrece **itk::MedianImageFilter** como filtro de mediana estándar, pero este incluye el píxel central en el cálculo. Para implementar la variante propuesta (excluyendo el centro), se requiere un enfoque personalizado:

- **itk::NeighborhoodIterator**: permite recorrer la imagen accediendo a los vecinos de cada píxel de forma eficiente. Se configura con un radio de 1 (ventana 3×3) y se itera sobre cada píxel, recolectando los 8 vecinos (excluyendo el índice central del iterador).
- **itk::ImageRegionIterator**: se usa en paralelo para escribir los valores de salida.
- **itk::BoundaryCondition** (por ejemplo, ZeroFluxNeumannBoundaryCondition): maneja automáticamente los píxeles de borde, replicando el valor del borde más cercano cuando la ventana se sale de la imagen.

El algoritmo con ITK sería: crear un NeighborhoodIterator con radio [1,1], para cada posición extraer los 8 valores vecinos (saltando el índice central), ordenarlos, tomar la mediana, y escribirla en la imagen de salida.

La ventaja de usar NeighborhoodIterator de ITK sobre una implementación manual con bucles es la eficiencia en el manejo de bordes y la compatibilidad con el pipeline de ITK para encadenar con otros filtros.

---

## 3. Filtro Mediana Adaptativo

### Concepto

El filtro de mediana adaptativo es una extensión inteligente del filtro de mediana que ajusta dinámicamente el tamaño de la ventana para cada píxel. Su objetivo principal es distinguir entre ruido impulsivo y detalles legítimos de la imagen, algo que el filtro de mediana estándar no puede hacer con un tamaño de ventana fijo.

### Algoritmo de Dos Niveles

El algoritmo opera en dos niveles para cada píxel:

**Nivel A — ¿La mediana es confiable?**

Se calcula en la ventana actual:

- Zmin: valor mínimo en la ventana
- Zmax: valor máximo en la ventana
- Zmed: mediana de la ventana
- Zxy: valor del píxel actual

Se evalúa: ¿Zmin < Zmed < Zmax?

- **Sí** → la mediana no es un valor extremo (no es ruido impulsivo), se pasa al Nivel B.
- **No** → la mediana misma podría ser ruido. Se incrementa el tamaño de la ventana en 2 (de 3×3 a 5×5, luego 7×7, etc.) y se repite el Nivel A.
- Si se alcanza el tamaño máximo Smax sin encontrar una mediana confiable, se retorna la mediana de la ventana Smax.

**Nivel B — ¿El píxel original es confiable?**

Se evalúa: ¿Zmin < Zxy < Zmax?

- **Sí** → el píxel original no es un valor extremo, se conserva (salida = Zxy).
- **No** → el píxel podría ser ruido impulsivo, se reemplaza por la mediana (salida = Zmed).

### Parámetros

- **Smax** (tamaño máximo de ventana): limita hasta dónde puede crecer la ventana. Valor por defecto: 7.
- Valores más grandes permiten detectar ruido en imágenes con mucho ruido impulsivo, pero aumentan el costo computacional.

### Implementación en ITK

ITK no incluye un filtro de mediana adaptativo predefinido, por lo que se implementa como un filtro personalizado:

- **itk::ImageToImageFilter**: clase base para crear filtros personalizados en ITK. Se hereda de esta clase y se implementa el método `GenerateData()` o `DynamicThreadedGenerateData()` con el algoritmo de dos niveles.
- **itk::ConstNeighborhoodIterator**: permite acceder a vecindades de tamaño variable. Para cada píxel, se comienza con radio 1 (ventana 3×3) y se incrementa hasta Smax/2 según lo requiera el Nivel A.
- **itk::ImageRegion**: define la región de la ventana actual, permitiendo extraer subregiones de la imagen para calcular Zmin, Zmax y Zmed.

El flujo en ITK sería: para cada píxel, iniciar con ventana 3×3, extraer la región usando ConstNeighborhoodIterator, calcular las estadísticas (min, max, mediana), evaluar el Nivel A, crecer la ventana si es necesario, y finalmente evaluar el Nivel B para decidir el valor de salida.

Una optimización importante en ITK es usar `DynamicThreadedGenerateData()` para paralelizar el procesamiento, ya que cada píxel se procesa de forma independiente. Esto aprovecha los múltiples núcleos del procesador para acelerar el filtrado de volúmenes grandes.

---

## Comparación de los Tres Filtros

| Característica         | Wiener Adaptativo              | Mediana Propuesto  | Mediana Adaptativo            |
| ---------------------- | ------------------------------ | ------------------ | ----------------------------- |
| Dominio de operación   | Estadístico (media/varianza)   | Espacial (mediana) | Espacial (mediana)            |
| Tipo de ruido objetivo | Ruido gaussiano                | Ruido impulsivo    | Ruido impulsivo               |
| Preservación de bordes | Alta (adaptativo por varianza) | Moderada           | Alta (adaptativo por ventana) |
| Ventana                | Fija (M×N)                     | Fija (3×3)         | Dinámica (3 a Smax)           |
| Parámetros             | M, N                           | Ninguno            | Smax                          |
| Costo computacional    | Bajo                           | Bajo               | Medio-Alto                    |

---

## Relación con ITK

ITK (Insight Toolkit) es una biblioteca de código abierto para procesamiento y análisis de imágenes médicas. Proporciona:

- Soporte nativo para formatos médicos (DICOM, NIfTI, MetaImage).
- Pipeline de procesamiento donde los filtros se conectan en cadena.
- Iteradores especializados (NeighborhoodIterator) para acceso eficiente a vecindades.
- Paralelización automática mediante threading.
- Manejo de imágenes N-dimensionales (2D, 3D, 4D).

En esta implementación, se utiliza ITK (Insight Toolkit) para Python (`itk`) como motor principal de procesamiento:

- **Filtro Wiener Adaptativo**: usa `itk.MeanImageFilter` para calcular medias locales, `itk.SquareImageFilter` para elevar al cuadrado, y NumPy para ensamblar la fórmula de Wiener.
- **Filtro Mediana Propuesto**: usa `itk.MirrorPadImageFilter` para manejar bordes con padding espejo, y NumPy para el cálculo de la mediana excluyendo el centro.
- **Filtro Mediana Adaptativo**: usa `itk.MirrorPadImageFilter` para padding de bordes con ventana máxima, y NumPy para el algoritmo adaptativo de dos niveles.

La biblioteca nibabel se usa para leer archivos NIfTI, que es el formato estándar para imágenes de resonancia magnética volumétricas.
