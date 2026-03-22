# Plan de Implementación: Filtros de Imágenes Médicas

## Visión General

Implementación incremental de una aplicación web para procesamiento de imágenes médicas con tres filtros de eliminación de ruido (Wiener Adaptativo, Mediana Propuesto, Mediana Adaptativo). Backend en Python/Flask con ITK, frontend en React, tests con Hypothesis.

## Tareas

- [x] 1. Configurar estructura del proyecto y dependencias del backend
  - [x] 1.1 Crear estructura de directorios del backend (`backend/`, `backend/filters/`, `backend/tests/`)
    - Crear `requirements.txt` con Flask, itk, Hypothesis, pytest y dependencias necesarias
    - Crear `backend/__init__.py` y `backend/filters/__init__.py`
    - _Requisitos: 7.1_

  - [x] 1.2 Implementar modelos de datos (`backend/models.py`)
    - Implementar dataclasses `UploadedImage`, `FilterRequest`, `FilterResult` según el diseño
    - Incluir validación de `filter_type` contra valores permitidos
    - _Requisitos: 1.1, 2.1, 6.1_

  - [x] 1.3 Implementar endpoint de health check (`backend/app.py`)
    - Crear aplicación Flask con configuración CORS
    - Implementar `GET /api/health` que retorne `{ "status": "ok" }`
    - _Requisitos: 6.1_

- [x] 2. Implementar endpoint de carga de imágenes
  - [x] 2.1 Implementar `POST /api/upload` en `backend/app.py`
    - Aceptar `multipart/form-data` con archivo de imagen
    - Validar formato de imagen (DICOM, NIfTI, PNG, JPEG)
    - Generar `image_id` UUID, almacenar en directorio temporal
    - Retornar `{ image_id, preview_url }` con código 200
    - Retornar error 400 para archivos inválidos con mensaje descriptivo
    - _Requisitos: 1.1, 1.2_

  - [ ]\* 2.2 Escribir test de propiedad para aceptación de imágenes válidas
    - **Propiedad 1: Aceptación de imágenes válidas**
    - Generar imágenes aleatorias en formatos válidos (PNG, JPEG) con Hypothesis
    - Verificar que el endpoint retorna 200 y un `image_id` no vacío
    - **Valida: Requisitos 1.1**

  - [ ]\* 2.3 Escribir test de propiedad para rechazo de archivos inválidos
    - **Propiedad 2: Rechazo de archivos inválidos**
    - Generar datos binarios aleatorios, archivos de texto y archivos corruptos con Hypothesis
    - Verificar que el endpoint retorna código 4xx con mensaje descriptivo
    - **Valida: Requisitos 1.2**

  - [ ]\* 2.4 Escribir tests unitarios para el endpoint de upload
    - Test con imagen PNG válida → 200
    - Test con archivo de texto → 400
    - Test sin archivo adjunto → 400
    - _Requisitos: 1.1, 1.2_

- [x] 3. Checkpoint - Verificar que el backend base funciona
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implementar Filtro Wiener Adaptativo
  - [x] 4.1 Implementar `filters/wiener_adaptive.py`
    - Implementar clase/función que aplique el filtro Wiener Adaptativo usando ITK
    - Estimar media local y desviación estándar en vecindad M×N
    - Operar en dominio de frecuencia
    - Aceptar parámetros `m` y `n` (default: 3×3)
    - _Requisitos: 2.1, 2.2, 2.3_

  - [ ]\* 4.2 Escribir test de propiedad para preservación de dimensiones (Wiener)
    - **Propiedad 3: Preservación de dimensiones en todos los filtros** (instancia Wiener)
    - Generar imágenes aleatorias de diferentes tamaños con Hypothesis
    - Verificar que la imagen filtrada tiene las mismas dimensiones que la original
    - **Valida: Requisitos 2.1, 3.1, 4.1, 5.3**

  - [ ]\* 4.3 Escribir test de propiedad para sensibilidad paramétrica del Wiener
    - **Propiedad 4: Sensibilidad paramétrica del Filtro Wiener**
    - Generar imágenes aleatorias y pares de parámetros (M₁,N₁) ≠ (M₂,N₂) con Hypothesis
    - Verificar que los resultados difieren en al menos un píxel
    - **Valida: Requisitos 2.3**

  - [ ]\* 4.4 Escribir tests unitarios para Filtro Wiener Adaptativo
    - Test con imagen conocida y resultado esperado calculado manualmente
    - Test con parámetros por defecto (3×3)
    - Test con parámetros personalizados
    - _Requisitos: 2.1, 2.2, 2.3_

- [x] 5. Implementar Filtro Mediana Propuesto
  - [x] 5.1 Implementar `filters/proposal_median.py`
    - Implementar filtro que use vecindad 8-conectada excluyendo el píxel central
    - Calcular mediana de los 8 vecinos para cada píxel interior
    - Manejar correctamente los píxeles de borde
    - Sin parámetros configurables
    - _Requisitos: 3.1, 3.2_

  - [ ]\* 5.2 Escribir test de propiedad para corrección del Filtro Mediana Propuesto
    - **Propiedad 5: Corrección del Filtro Mediana Propuesto**
    - Generar imágenes aleatorias con Hypothesis
    - Para cada píxel interior, verificar que la salida es la mediana de los 8 vecinos excluyendo el central
    - **Valida: Requisitos 3.1, 3.2**

  - [ ]\* 5.3 Escribir test de propiedad para preservación de dimensiones (Mediana Propuesto)
    - **Propiedad 3: Preservación de dimensiones en todos los filtros** (instancia Mediana Propuesto)
    - Generar imágenes aleatorias de diferentes tamaños con Hypothesis
    - Verificar que la imagen filtrada tiene las mismas dimensiones que la original
    - **Valida: Requisitos 2.1, 3.1, 4.1, 5.3**

  - [ ]\* 5.4 Escribir tests unitarios para Filtro Mediana Propuesto
    - Test con matriz 3×3 conocida verificando que el píxel central se reemplaza por la mediana de los 8 vecinos
    - Test de comportamiento en bordes y esquinas
    - _Requisitos: 3.1, 3.2_

- [x] 6. Implementar Filtro Mediana Adaptativo
  - [x] 6.1 Implementar `filters/adaptive_median.py`
    - Implementar algoritmo de dos niveles (Nivel A y Nivel B) según el diseño
    - Nivel A: evaluar si Zmed está entre Zmin y Zmax, incrementar ventana si no
    - Nivel B: evaluar si Zxy está entre Zmin y Zmax, retornar Zxy o Zmed
    - Aceptar parámetro `smax` (default: 7)
    - Manejar caso borde cuando se alcanza Smax
    - _Requisitos: 4.1, 4.2, 4.3, 4.4_

  - [ ]\* 6.2 Escribir test de propiedad para corrección del algoritmo Mediana Adaptativo
    - **Propiedad 6: Corrección del algoritmo Mediana Adaptativo**
    - Generar imágenes aleatorias y valores de Smax con Hypothesis
    - Verificar las tres condiciones: (a) salida = Zxy cuando ambos están entre Zmin/Zmax, (b) salida = Zmed cuando Zxy no está entre Zmin/Zmax, (c) salida = Zmed de Smax cuando ninguna ventana cumple
    - **Valida: Requisitos 4.1, 4.2, 4.3, 4.4**

  - [ ]\* 6.3 Escribir test de propiedad para preservación de dimensiones (Mediana Adaptativo)
    - **Propiedad 3: Preservación de dimensiones en todos los filtros** (instancia Mediana Adaptativo)
    - Generar imágenes aleatorias de diferentes tamaños con Hypothesis
    - Verificar que la imagen filtrada tiene las mismas dimensiones que la original
    - **Valida: Requisitos 2.1, 3.1, 4.1, 5.3**

  - [ ]\* 6.4 Escribir tests unitarios para Filtro Mediana Adaptativo
    - Test del Nivel A con ventana construida manualmente
    - Test del Nivel B con ventana construida manualmente
    - Test del caso borde cuando se alcanza Smax
    - _Requisitos: 4.1, 4.2, 4.3, 4.4_

- [x] 7. Checkpoint - Verificar que los tres filtros funcionan correctamente
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implementar Motor de Filtros y endpoint de filtrado
  - [x] 8.1 Implementar `backend/filter_engine.py`
    - Crear clase `FilterEngine` con método `apply_filter(image_path, filter_type, params)`
    - Despachar al filtro correcto según `filter_type`
    - Capturar excepciones de ITK y traducirlas a errores descriptivos
    - Medir tiempo de procesamiento
    - _Requisitos: 2.4, 3.3, 6.2_

  - [x] 8.2 Implementar `POST /api/filter` en `backend/app.py`
    - Validar `image_id` existe, `filter_type` es válido, parámetros dentro de rango
    - Invocar `FilterEngine.apply_filter` y retornar imagen filtrada
    - Retornar códigos de error apropiados (400, 404, 500) según tabla de errores del diseño
    - _Requisitos: 2.4, 3.3, 6.2, 6.3_

  - [ ]\* 8.3 Escribir test de propiedad para respuesta válida de la API de filtrado
    - **Propiedad 7: Respuesta válida de la API de filtrado**
    - Generar imágenes aleatorias, subir vía API, aplicar cada tipo de filtro con Hypothesis
    - Verificar que la respuesta es 200 y contiene datos de imagen decodificables con mismas dimensiones
    - **Valida: Requisitos 2.4, 3.3, 6.3**

  - [ ]\* 8.4 Escribir test de propiedad para preservación de metadatos
    - **Propiedad 8: Preservación de metadatos (round-trip)**
    - Generar imágenes con metadatos aleatorios con Hypothesis
    - Aplicar cada filtro y verificar que los metadatos se preservan idénticos
    - **Valida: Requisitos 7.2**

  - [ ]\* 8.5 Escribir test de propiedad para manejo de errores en procesamiento
    - **Propiedad 9: Manejo de errores en procesamiento**
    - Generar solicitudes con datos inválidos (image_id inexistente, filter_type inválido, parámetros fuera de rango) con Hypothesis
    - Verificar que el sistema retorna 4xx/5xx con mensaje descriptivo sin crash
    - **Valida: Requisitos 1.2, 7.3**

  - [ ]\* 8.6 Escribir tests unitarios para el endpoint de filtrado y motor de filtros
    - Test con image_id válido y filtro válido → 200
    - Test con image_id inexistente → 404
    - Test con filter_type inválido → 400
    - Test con parámetros fuera de rango → 400
    - _Requisitos: 2.4, 6.2, 6.3, 7.3_

- [x] 9. Checkpoint - Verificar que la API completa funciona
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implementar frontend React
  - [x] 10.1 Configurar proyecto React y dependencias
    - Crear proyecto con estructura `frontend/src/components/`
    - Instalar dependencias: axios (o fetch), CSS framework si necesario
    - Configurar proxy para comunicación con backend Flask
    - _Requisitos: 5.1_

  - [x] 10.2 Implementar componente `ImageUploader`
    - Crear componente de carga de archivos con validación de formato en cliente
    - Enviar imagen a `POST /api/upload` y almacenar `image_id` en estado
    - Mostrar preview de la imagen original tras carga exitosa
    - Mostrar mensajes de error amigables si la carga falla
    - _Requisitos: 1.1, 1.2, 5.1_

  - [x] 10.3 Implementar componente `FilterSelector`
    - Crear panel con selección de los tres tipos de filtro
    - Mostrar campos de parámetros según el filtro seleccionado (M, N para Wiener; Smax para Mediana Adaptativo)
    - Validar parámetros antes de enviar solicitud
    - Enviar solicitud a `POST /api/filter`
    - _Requisitos: 5.2, 2.3, 4.3_

  - [x] 10.4 Implementar componente `ImageViewer`
    - Crear visualización lado a lado: imagen original a la izquierda, filtrada a la derecha
    - Mostrar información del filtro aplicado y tiempo de procesamiento
    - Manejar estado de carga mientras se procesa el filtro
    - _Requisitos: 5.3, 5.4_

  - [x] 10.5 Integrar componentes en `App`
    - Componer `ImageUploader`, `FilterSelector` e `ImageViewer` en el layout principal
    - Gestionar estado global (image_id, imagen original, imagen filtrada)
    - Manejar flujo completo: carga → selección de filtro → visualización
    - _Requisitos: 5.1, 5.2, 5.3, 5.4_

- [x] 11. Integración y manejo de errores end-to-end
  - [x] 11.1 Implementar manejo de errores completo en el backend
    - Agregar manejadores globales de excepciones en Flask
    - Implementar logging estructurado con contexto (image_id, filter_type, stack trace)
    - Verificar que todos los escenarios de error de la tabla del diseño retornan los códigos y mensajes correctos
    - _Requisitos: 7.3_

  - [x] 11.2 Implementar manejo de errores en el frontend
    - Mostrar mensajes de error amigables al usuario sin exponer detalles técnicos
    - Manejar errores de red y timeouts
    - Manejar estados de carga y feedback visual durante el procesamiento
    - _Requisitos: 7.3, 5.4_

- [x] 12. Checkpoint final - Verificar integración completa
  - Ensure all tests pass, ask the user if questions arise.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- Los tests de propiedades validan propiedades universales de corrección usando Hypothesis (mínimo 100 iteraciones)
- Los tests unitarios validan ejemplos concretos y casos borde
