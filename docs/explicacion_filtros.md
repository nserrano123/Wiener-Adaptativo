# Filtros de Eliminación de Ruido en Imágenes Médicas

## Contexto

Las imágenes de resonancia magnética (MR) están sujetas a ruido durante su adquisición, lo que puede dificultar el diagnóstico clínico. Los filtros de eliminación de ruido buscan reducir este ruido preservando los bordes y estructuras anatómicas relevantes. Este documento describe tres filtros implementados en la aplicación — Wiener Adaptativo, Mediana Propuesto y Mediana Adaptativo — junto con su implementación conceptual en ITK y un análisis comparativo.

---

## 1. Filtro Wiener Adaptativo

### Concepto

El filtro Wiener es un filtro estadístico óptimo que minimiza el error cuadrático medio entre la imagen original (sin ruido) y la imagen estimada. La versión adaptativa ajusta su comportamiento localmente según las estadísticas de cada vecindad de píxeles, lo que le permite preservar bordes en zonas de alto contraste mientras suaviza zonas homogéneas.

### Fundamento Matemático

Para cada píxel en la posición (i, j), el filtro calcula:

- **Media local** (μ): promedio de los valores de píxel en una vecindad de tamaño M×N.
- **Varianza local** (σ²): varianza de los valores en esa misma vecindad.
- **Varianza de ruido** (σₙ²): estimada como el promedio de todas las varianzas locales.

La salida se calcula como:

```
salida(i,j) = μ(i,j) + max(0, (σ²(i,j) - σₙ²) / σ²(i,j)) × (entrada(i,j) - μ(i,j))
```

**Interpretación:**

- En zonas homogéneas (σ² ≈ σₙ²), el factor tiende a 0 → la salida se acerca a la media local (suavizado fuerte).
- En zonas con bordes (σ² >> σₙ²), el factor tiende a 1 → la salida conserva el valor original (preservación de detalle).

### Parámetros

| Parámetro | Descripción             | Default |
| --------- | ----------------------- | ------- |
| M         | Filas de la vecindad    | 3       |
| N         | Columnas de la vecindad | 3       |

Ventanas más grandes producen mayor suavizado pero pueden difuminar bordes finos.

### Implementación en ITK

El filtro Wiener adaptativo se construye en ITK combinando varios filtros del pipeline:

1. **itk::MeanImageFilter**: calcula la media local μ(i,j) en una vecindad rectangular de radio [N/2, M/2]. ITK implementa este filtro como un promedio uniforme usando un kernel rectangular, recorriendo la imagen con un iterador de vecindad interno. El radio se especifica en formato [x, y] (columnas, filas).

2. **itk::SquareImageFilter**: eleva cada píxel al cuadrado para obtener X². Este es un filtro unario píxel-a-píxel que opera en el pipeline sin necesidad de vecindad.

3. Se aplica nuevamente **itk::MeanImageFilter** sobre la imagen X² para obtener E[X²], la media local de los cuadrados.

4. La varianza local se obtiene como E[X²] - μ², y la varianza de ruido como el promedio global de las varianzas locales. Estas operaciones aritméticas se realizan con los arrays resultantes.

5. Finalmente se ensambla la fórmula de Wiener: para cada píxel se calcula el factor adaptativo y se pondera entre la media local y el valor original.

El concepto clave de ITK aquí es el **pipeline de filtros**: cada filtro se conecta al siguiente mediante `SetInput()` / `GetOutput()`, y la ejecución se propaga automáticamente al llamar `Update()`. Esto permite construir cadenas de procesamiento complejas de forma modular.

---

## 2. Filtro Mediana Propuesto

### Concepto

El filtro de mediana propuesto es una variante del filtro de mediana clásico. En lugar de incluir el píxel central en el cálculo de la mediana, lo excluye. Para cada píxel, se toman únicamente los 8 vecinos de la vecindad 8-conectada (los píxeles adyacentes horizontal, vertical y diagonalmente), se calcula la mediana de esos 8 valores, y se reemplaza el píxel central con ese resultado.

### Fundamento

- **Vecindad 8-conectada**: los 8 píxeles que rodean al píxel central en una ventana 3×3.
- Al excluir el píxel central, el filtro es más agresivo contra el ruido impulsivo (sal y pimienta), ya que un píxel corrupto no influye en su propia corrección.
- Para píxeles en los bordes de la imagen, se usan los vecinos disponibles con condición de borde espejo.

### Parámetros

No tiene parámetros configurables. La vecindad es siempre 3×3 con exclusión del centro.

### Implementación en ITK

ITK ofrece **itk::MedianImageFilter** como filtro de mediana estándar, pero este incluye el píxel central. Para la variante propuesta se utilizan los siguientes conceptos de ITK:

1. **itk::MirrorPadImageFilter**: extiende la imagen con padding espejo en los bordes. Esto resuelve el problema de los píxeles de borde: en lugar de manejar casos especiales, se agregan filas/columnas espejo alrededor de la imagen para que todos los píxeles tengan 8 vecinos completos. El padding espejo replica los valores del borde como si la imagen se reflejara, lo que produce resultados más naturales que el padding con ceros.

2. **itk::NeighborhoodIterator**: es el mecanismo central de ITK para acceder a vecindades. Se configura con un radio (en este caso [1,1] para ventana 3×3) y permite recorrer la imagen accediendo a los vecinos de cada píxel mediante índices. En una vecindad 3×3 linealizada, los índices 0-8 representan los 9 píxeles, donde el índice 4 es el centro. El filtro propuesto recolecta los índices 0-3 y 5-8 (excluyendo el 4), calcula la mediana, y la escribe en la imagen de salida.

3. **Condiciones de borde**: ITK maneja automáticamente los bordes a través de `BoundaryCondition`. Con el padding espejo previo, todos los accesos a vecindad son válidos sin necesidad de verificaciones adicionales.

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

- **Sí** → la mediana no es un valor extremo (no es impulso), se pasa al Nivel B.
- **No** → la mediana podría ser ruido. Se incrementa la ventana de 3×3 a 5×5, luego 7×7, etc.
- Si se alcanza Smax sin mediana confiable → salida = Zmed de la ventana Smax.

**Nivel B — ¿El píxel original es confiable?**

Se evalúa: ¿Zmin < Zxy < Zmax?

- **Sí** → el píxel no es impulso, se conserva (salida = Zxy).
- **No** → el píxel es probablemente ruido, se reemplaza (salida = Zmed).

### Parámetros

| Parámetro | Descripción              | Default |
| --------- | ------------------------ | ------- |
| Smax      | Tamaño máximo de ventana | 7       |

Valores más grandes permiten detectar ruido en imágenes muy ruidosas, pero aumentan el costo computacional.

### Implementación en ITK

ITK no incluye un filtro de mediana adaptativo predefinido. Se implementa como un filtro personalizado usando:

1. **itk::MirrorPadImageFilter**: se aplica padding espejo con radio Smax/2 alrededor de la imagen. Esto permite que el algoritmo crezca la ventana hasta Smax sin preocuparse por los bordes. El padding espejo es preferible al padding con ceros porque no introduce valores artificiales que podrían confundir al algoritmo de detección de impulsos.

2. **itk::ImageToImageFilter** (clase base): en ITK, los filtros personalizados heredan de esta clase. Se implementa el método `DynamicThreadedGenerateData()` que recibe una región de la imagen y procesa cada píxel de forma independiente. Esto permite paralelización automática.

3. **Acceso a vecindades de tamaño variable**: para cada píxel, el algoritmo comienza con ventana 3×3 y puede crecer hasta Smax×Smax. En ITK esto se logra extrayendo subregiones de la imagen paddeada usando `itk::ImageRegion` con tamaño dinámico, o usando `ConstNeighborhoodIterator` con el radio máximo y accediendo solo a los píxeles dentro del radio actual.

4. **Paralelización**: dado que cada píxel se procesa independientemente (solo lectura de vecinos), ITK puede dividir la imagen en regiones y procesarlas en paralelo usando `DynamicThreadedGenerateData()`, aprovechando todos los núcleos del procesador.

---

## Comparativo de los Tres Filtros

### Tabla Comparativa General

| Característica                | Wiener Adaptativo            | Mediana Propuesto          | Mediana Adaptativo         |
| ----------------------------- | ---------------------------- | -------------------------- | -------------------------- |
| **Dominio**                   | Estadístico (media/varianza) | Espacial (mediana)         | Espacial (mediana)         |
| **Tipo de ruido objetivo**    | Gaussiano                    | Impulsivo (sal y pimienta) | Impulsivo (sal y pimienta) |
| **Preservación de bordes**    | Alta                         | Moderada                   | Alta                       |
| **Ventana**                   | Fija (M×N)                   | Fija (3×3)                 | Dinámica (3 a Smax)        |
| **Parámetros**                | M, N                         | Ninguno                    | Smax                       |
| **Complejidad computacional** | O(W×H)                       | O(W×H)                     | O(W×H×Smax²) peor caso     |
| **Adaptabilidad**             | Por varianza local           | No adaptativo              | Por tamaño de ventana      |

### Comparativo por Tipo de Ruido

| Tipo de ruido                   | Wiener Adaptativo                          | Mediana Propuesto                                    | Mediana Adaptativo                            |
| ------------------------------- | ------------------------------------------ | ---------------------------------------------------- | --------------------------------------------- |
| Gaussiano (distribución normal) | Excelente — diseñado para esto             | Pobre — la mediana no es óptima para ruido gaussiano | Pobre — mismo problema que mediana estándar   |
| Impulsivo (sal y pimienta)      | Pobre — la media se contamina con impulsos | Bueno — la mediana ignora valores extremos           | Excelente — detecta y reemplaza solo impulsos |
| Mixto (gaussiano + impulsivo)   | Moderado                                   | Moderado                                             | Bueno — maneja impulsos y preserva señal      |

### Comparativo por Preservación de Detalle

| Aspecto          | Wiener Adaptativo                                | Mediana Propuesto          | Mediana Adaptativo                           |
| ---------------- | ------------------------------------------------ | -------------------------- | -------------------------------------------- |
| Bordes fuertes   | Preserva bien (alta varianza local → factor ≈ 1) | Puede suavizar ligeramente | Preserva bien (píxel no-impulso se conserva) |
| Texturas finas   | Puede difuminar con ventanas grandes             | Pierde textura fina        | Preserva mejor que mediana fija              |
| Zonas homogéneas | Suavizado fuerte (baja varianza → factor ≈ 0)    | Suavizado moderado         | Suavizado solo donde hay impulsos            |

### Comparativo por Rendimiento Computacional

| Aspecto                 | Wiener Adaptativo                                  | Mediana Propuesto             | Mediana Adaptativo                    |
| ----------------------- | -------------------------------------------------- | ----------------------------- | ------------------------------------- |
| Operaciones por píxel   | 2 pasadas de media + aritmética                    | 1 ordenamiento de 8 valores   | 1-N ordenamientos (ventana creciente) |
| Paralelizable           | Sí (filtros ITK son paralelos)                     | Sí (cada píxel independiente) | Sí (cada píxel independiente)         |
| Uso de memoria          | 3 imágenes intermedias (media, cuadrado, varianza) | 1 imagen paddeada             | 1 imagen paddeada                     |
| Tiempo típico (256×256) | ~5ms                                               | ~50ms                         | ~200ms (depende de Smax y ruido)      |

### Cuándo Usar Cada Filtro

**Wiener Adaptativo**: cuando el ruido es predominantemente gaussiano (ruido térmico en MR, ruido electrónico). Es el filtro más rápido y produce resultados suaves sin artefactos. Ideal para preprocesamiento general de imágenes MR.

**Mediana Propuesto**: cuando hay ruido impulsivo moderado y se necesita un filtro simple sin parámetros que ajustar. Útil como primer paso de limpieza rápida. La exclusión del centro lo hace más efectivo que la mediana estándar para impulsos aislados.

**Mediana Adaptativo**: cuando hay ruido impulsivo significativo y se necesita preservar el máximo detalle posible. Es el más sofisticado de los tres: solo modifica píxeles que identifica como ruido, dejando intactos los demás. Ideal cuando la calidad de la imagen es crítica para el diagnóstico.

---

## Relación con ITK

ITK (Insight Toolkit) es una biblioteca de código abierto para procesamiento y análisis de imágenes médicas. Los conceptos clave de ITK utilizados en estos filtros son:

- **Pipeline de procesamiento**: los filtros se conectan en cadena mediante `SetInput()`/`GetOutput()`. La ejecución se propaga automáticamente, y cada filtro solo procesa cuando se solicita su salida. Esto permite construir cadenas complejas de forma modular y eficiente en memoria.

- **Iteradores de vecindad**: `NeighborhoodIterator` y `ConstNeighborhoodIterator` permiten acceder eficientemente a los vecinos de cada píxel sin cálculos manuales de índices. Soportan diferentes condiciones de borde (zero-flux, periodic, mirror).

- **Padding de imágenes**: `MirrorPadImageFilter` extiende la imagen con reflexión espejo, eliminando la necesidad de manejar casos especiales en los bordes. Esto simplifica los algoritmos y produce resultados más naturales en los bordes.

- **Filtros aritméticos**: `SquareImageFilter`, `SubtractImageFilter`, `MultiplyImageFilter` permiten operaciones píxel-a-píxel dentro del pipeline, útiles para construir filtros compuestos como el Wiener.

- **Paralelización**: ITK divide automáticamente la imagen en regiones y las procesa en paralelo usando `DynamicThreadedGenerateData()`, aprovechando múltiples núcleos sin que el desarrollador gestione threads manualmente.

- **Soporte de formatos médicos**: ITK lee y escribe nativamente DICOM, NIfTI, MetaImage y otros formatos médicos, preservando metadatos como orientación espacial, resolución y datos del paciente.

En esta implementación, los filtros utilizan ITK para las operaciones de procesamiento de imagen (medias locales, padding espejo, conversión de formatos) y NumPy para las operaciones aritméticas finales y el algoritmo adaptativo, combinando la robustez del pipeline de ITK con la flexibilidad de NumPy.
