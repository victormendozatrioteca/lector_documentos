# Feature Specification: Lector de Documentos con Voz

**Feature Branch**: `001-voice-document-reader`

**Created**: 2026-10-08

**Status**: Draft

**Input**: User description: "Lector de Documentos con Voz — permitir a un usuario subir un documento Markdown en español y escucharlo narrado en voz alta (español de España) directamente en el navegador, con controles de reproducción (play/pausa, detener, velocidad, línea de tiempo), respetando el orden y fidelidad del contenido narrable, generando el audio en el servidor sin enviar el texto a proveedores externos, y sin conservar documentos ni audios de forma permanente."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subir un documento y escuchar su narración (Priority: P1)

Un usuario que no puede o prefiere no leer un documento de texto quiere subir un archivo
Markdown en español y escuchar su contenido narrado en voz alta directamente en el navegador.

**Why this priority**: Es el flujo central de valor del producto: sin carga exitosa y
narración, no existe producto. Debe funcionar de forma aislada como MVP.

**Independent Test**: Puede probarse completamente subiendo un archivo `.md` válido en
español y verificando que, tras un breve procesamiento, el usuario puede reproducir el
audio resultante y escuchar el contenido en el orden correcto.

**Acceptance Scenarios**:

1. **Given** el usuario está en la página principal, **When** selecciona y sube un archivo
   `.md` válido en español de menos de 5 MB, **Then** la interfaz muestra el nombre del
   documento y el estado "cargando/procesando" y, al finalizar, indica que el audio está
   listo para reproducirse.
2. **Given** el audio ha sido generado, **When** el usuario pulsa Play, **Then** comienza a
   escuchar la narración del contenido en el mismo orden en que aparece en el documento,
   sin resúmenes, traducciones ni reescrituras.
3. **Given** el documento contiene encabezados, párrafos, citas y listas, **When** se
   reproduce el audio, **Then** se perciben pausas entre bloques y no se pronuncian las
   marcas de sintaxis Markdown (`#`, `*`, `>`, etc.).

---

### User Story 2 - Controlar la reproducción del audio (Priority: P2)

Un usuario que está escuchando un documento narrado quiere controlar la reproducción:
pausar, reanudar, detener, cambiar la velocidad y moverse en la línea de tiempo.

**Why this priority**: Una narración sin controles básicos de reproducción resulta
inutilizable para documentos largos o en contextos con interrupciones; es la segunda
pieza de valor indispensable tras la narración en sí.

**Independent Test**: Puede probarse de forma independiente una vez que existe un audio
generado (puede ser un audio de prueba), validando cada control por separado sin depender
de la lógica de carga de documentos.

**Acceptance Scenarios**:

1. **Given** el audio está en reproducción, **When** el usuario pulsa Pausa, **Then** el
   audio se detiene en la posición actual, y al pulsar Play de nuevo continúa desde esa
   misma posición.
2. **Given** el audio está en reproducción o en pausa, **When** el usuario pulsa Detener,
   **Then** el audio se detiene y la posición vuelve al inicio.
3. **Given** el audio está listo, **When** el usuario selecciona una velocidad distinta de
   1× (0,75×, 1,25×, 1,5× o 2×), **Then** el audio continúa reproduciéndose a la nueva
   velocidad sin regenerarse ni reiniciar su posición.
4. **Given** el audio está listo, **When** el usuario arrastra o hace clic en la línea de
   tiempo, **Then** la reproducción salta a la posición indicada y el tiempo transcurrido
   mostrado se actualiza en consecuencia.
5. **Given** el audio aún no está disponible, **When** el usuario observa los controles,
   **Then** los controles de reproducción aparecen deshabilitados hasta que el audio esté
   listo.

---

### User Story 3 - Manejo de contenido no narrable y elementos especiales (Priority: P2)

Un usuario sube un documento que contiene enlaces, imágenes, tablas, bloques de código u
otros elementos que no deben leerse literalmente, y espera que la narración los trate de
forma sensata sin romper la fidelidad del contenido narrable.

**Why this priority**: Sin estas reglas, la narración puede ser confusa, incorrecta o
leer contenido no apto para voz (URLs completas, código fuente), degradando seriamente la
experiencia, aunque el flujo básico (US1) ya aporte valor sin ellas.

**Independent Test**: Puede probarse con documentos de prueba que contengan cada tipo de
elemento (enlaces, imágenes con/sin texto alternativo, tablas, código en línea, bloques de
código, líneas separadoras, HTML crudo) y verificando el comportamiento esperado de cada
uno de forma independiente del resto de historias.

**Acceptance Scenarios**:

1. **Given** un documento contiene un enlace con texto visible, **When** se narra, **Then**
   se lee el texto visible del enlace pero no la URL.
2. **Given** un documento contiene una imagen con texto alternativo, **When** se narra,
   **Then** se lee únicamente el texto alternativo; si la imagen no tiene texto
   alternativo, no se narra nada para esa imagen.
3. **Given** un documento contiene una tabla, **When** se narra, **Then** se leen primero
   los encabezados de columna y después las celdas de cada fila de izquierda a derecha.
4. **Given** un documento contiene código en línea, bloques de código, URLs aisladas,
   líneas separadoras o HTML crudo, **When** se narra, **Then** estos elementos se omiten
   por completo de la narración.

---

### User Story 4 - Validación de documentos y manejo de errores (Priority: P3)

Un usuario intenta subir un archivo que no cumple los requisitos (formato incorrecto,
demasiado grande, vacío, sin contenido narrable, o falla la generación de voz), y espera
recibir un mensaje de error claro y comprensible.

**Why this priority**: Mejora la robustez y la confianza del usuario, pero el sistema ya
aporta valor principal mediante la narración de documentos válidos (US1-US3) incluso antes
de cubrir todos los casos de error.

**Independent Test**: Puede probarse de forma independiente subiendo archivos inválidos de
cada tipo (formato incorrecto, tamaño excedido, vacío, sin contenido narrable) y forzando
un fallo del motor de voz, verificando que cada caso produce un mensaje de error
específico y comprensible sin exponer detalles técnicos internos.

**Acceptance Scenarios**:

1. **Given** el usuario sube un archivo que no es `.md`, **When** se procesa la carga,
   **Then** el sistema rechaza el archivo y muestra un mensaje de error claro indicando el
   formato esperado.
2. **Given** el usuario sube un archivo `.md` mayor de 5.000.000 bytes, **When** se procesa
   la carga, **Then** el sistema rechaza el archivo e informa del límite de tamaño.
3. **Given** el usuario sube un archivo `.md` vacío o sin contenido narrable, **When** se
   procesa la carga, **Then** el sistema rechaza el archivo e indica que no hay contenido
   para narrar.
4. **Given** la generación de voz falla en el servidor, **When** el usuario espera el
   audio, **Then** el sistema muestra un error claro sin intentar automáticamente un
   proveedor de voz alternativo.

---

### Edge Cases

- ¿Qué ocurre si el usuario sube un documento `.md` válido pero con codificación distinta
  de UTF-8 o con contenido mayormente en otro idioma distinto del español? → Se rechaza
  como formato/contenido incorrecto.
- ¿Qué ocurre si el usuario navega fuera de la página o cierra la pestaña mientras se
  genera el audio? → El procesamiento en curso se cancela y los archivos temporales
  asociados se limpian.
- ¿Qué ocurre si se pierde la conexión durante la carga o la generación de audio? → El
  usuario ve un error claro y los archivos temporales se limpian; no queda un proceso
  huérfano en el servidor.
- ¿Qué ocurre si el usuario intenta reproducir un segundo documento mientras el primero
  sigue sonando? → El sistema detiene o impide la reproducción simultánea; solo un
  documento puede sonar a la vez.
- ¿Qué ocurre si el documento contiene únicamente elementos no narrables (por ejemplo,
  solo bloques de código e imágenes sin texto alternativo)? → Se trata como "sin contenido
  narrable" y se rechaza igual que un documento vacío.
- ¿Qué ocurre si el usuario cambia la velocidad de reproducción mientras el audio está en
  pausa? → La nueva velocidad se aplica y, al reanudar, continúa desde la misma posición a
  la nueva velocidad.

## Requirements *(mandatory)*

### Functional Requirements

**Carga de documentos**

- **FR-001**: El sistema MUST permitir al usuario seleccionar y subir un documento desde
  una interfaz web.
- **FR-002**: El sistema MUST aceptar únicamente archivos Markdown (`.md`) codificados en
  UTF-8 con contenido narrable en español, rechazando cualquier otro formato, codificación
  o idioma detectado.
- **FR-003**: El sistema MUST rechazar archivos que superen 5.000.000 bytes (5 MB).
- **FR-004**: El sistema MUST rechazar archivos vacíos o sin ningún contenido narrable tras
  aplicar las reglas de omisión (ver FR-010 a FR-012).
- **FR-005**: El sistema MUST mostrar en la interfaz el nombre del documento cargado y su
  estado (por ejemplo: cargando, procesando, listo, error).
- **FR-006**: El sistema MUST mantener el archivo original sin modificaciones durante todo
  el proceso.
- **FR-007**: El backend MUST validar de forma independiente el formato, la codificación,
  el idioma y el tamaño del archivo, aunque el navegador ya los haya validado previamente.

**Reglas de narración**

- **FR-008**: El sistema MUST narrar el contenido respetando estrictamente el orden en que
  aparece en el documento, sin resumir, traducir ni reescribir el texto.
- **FR-009**: El sistema MUST narrar encabezados, párrafos, citas y listas con una pausa
  perceptible entre bloques, sin pronunciar los símbolos de sintaxis Markdown.
- **FR-010**: El sistema MUST narrar el texto visible de los enlaces sin narrar la URL
  subyacente.
- **FR-011**: El sistema MUST narrar únicamente el texto alternativo de una imagen cuando
  exista, y omitir por completo cualquier imagen sin texto alternativo.
- **FR-012**: El sistema MUST narrar las tablas leyendo primero los encabezados de columna
  y después las celdas de cada fila, de izquierda a derecha.
- **FR-013**: El sistema MUST omitir de la narración el código en línea, los bloques de
  código, las URLs aisladas, las líneas separadoras y el HTML crudo.
- **FR-014**: El sistema MUST NOT ejecutar código ni descargar recursos enlazados dentro
  del documento durante el procesamiento.

**Generación de voz**

- **FR-015**: El sistema MUST generar el audio de la narración en el servidor utilizando
  un motor de síntesis de voz que se ejecute localmente (sin enviar el texto del documento
  a proveedores externos de voz).
- **FR-016**: El sistema MUST generar la voz en español de España, con calidad media,
  utilizando una voz capaz de pronunciar con claridad números y siglas.
- **FR-017**: El sistema MUST permitir que la generación de audio funcione sin conexión a
  Internet una vez que el motor de voz y su modelo estén instalados en el servidor.
- **FR-018**: El sistema MUST indicar en la interfaz cuándo se está generando el audio y
  cuándo está listo para reproducirse.
- **FR-019**: El sistema MUST mostrar un error claro si la generación de voz falla, sin
  recurrir automáticamente a un proveedor o motor de voz alternativo.

**Reproducción**

- **FR-020**: El sistema MUST permitir al usuario reproducir el audio generado
  directamente en su navegador.
- **FR-021**: La reproducción MUST comenzar únicamente cuando el usuario realiza una
  acción explícita (no debe autorreproducirse).
- **FR-022**: El sistema MUST ofrecer un control Play/Pausa que inicie, pause y reanude la
  reproducción desde la misma posición en la que se pausó.
- **FR-023**: El sistema MUST ofrecer un control Detener que pause la reproducción y
  regrese la posición al inicio del audio.
- **FR-024**: El sistema MUST ofrecer un selector de velocidad con las opciones 0,75×, 1×,
  1,25×, 1,5× y 2×, con 1× como valor predeterminado.
- **FR-025**: Cambiar la velocidad de reproducción MUST NOT regenerar el audio ni reiniciar
  la posición de reproducción.
- **FR-026**: El sistema MUST mostrar una línea de tiempo con el tiempo transcurrido y la
  duración total, permitiendo al usuario avanzar o retroceder la posición de reproducción.
- **FR-027**: Los controles de reproducción MUST permanecer deshabilitados hasta que el
  audio esté disponible, y MUST ser operables mediante teclado.
- **FR-028**: El sistema MUST impedir que suenen dos documentos simultáneamente; iniciar
  la reproducción de un nuevo documento MUST detener cualquier reproducción en curso.

**Privacidad y manejo de errores**

- **FR-029**: El sistema MUST informar al usuario de que el documento se envía al backend
  para su procesamiento.
- **FR-030**: El sistema MUST NOT conservar permanentemente los documentos subidos ni los
  audios generados.
- **FR-031**: El sistema MUST limpiar los archivos temporales asociados a un documento al
  finalizar su procesamiento, al fallar, al ser cancelado por el usuario o al perderse la
  conexión.
- **FR-032**: El sistema MUST NOT incluir el contenido del documento ni credenciales en los
  registros (logs) del sistema.
- **FR-033**: El sistema MUST mostrar los errores con mensajes comprensibles para el
  usuario, sin exponer detalles técnicos internos (trazas, rutas de archivo, nombres de
  librerías, etc.).

### Key Entities *(include if feature involves data)*

- **Documento**: Representa el archivo Markdown subido por el usuario. Atributos clave:
  nombre de archivo, tamaño, estado de validación (válido/rechazado y motivo), estado de
  procesamiento (cargando, procesando, listo, error). Es de carácter temporal: no se
  conserva tras finalizar la sesión de narración.
- **Audio narrado**: Representa el resultado de la síntesis de voz asociado a un
  documento. Atributos clave: duración total, estado (generando, listo, error). Es de
  carácter temporal: se limpia junto con el documento origen.
- **Sesión de reproducción**: Representa el estado de reproducción en el navegador de un
  audio narrado. Atributos clave: posición actual, estado (reproduciendo, en pausa,
  detenido), velocidad seleccionada. Solo puede existir una sesión de reproducción activa
  sonando a la vez.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario puede subir un documento Markdown válido en español y comenzar a
  escuchar su narración en menos de 60 segundos para un documento de hasta 5 MB.
- **SC-002**: El 100% de los documentos rechazados (formato incorrecto, tamaño excedido,
  vacíos o sin contenido narrable) muestran un mensaje de error específico y comprensible,
  verificado mediante casos de prueba para cada motivo de rechazo.
- **SC-003**: En pruebas de escucha con contenido que incluya números y siglas, al menos
  el 90% de las palabras narradas son identificadas correctamente por oyentes de prueba.
- **SC-004**: El 100% de los controles de reproducción (play/pausa, detener, velocidad,
  línea de tiempo) responden correctamente a entradas de teclado y de ratón en pruebas
  manuales de aceptación.
- **SC-005**: Ningún documento ni audio generado permanece accesible en el servidor
  transcurridos 5 minutos desde el fin de la sesión de narración (por finalización,
  cancelación, error o pérdida de conexión).
- **SC-006**: El 100% de las pruebas funcionales de las reglas de narración (encabezados,
  párrafos, listas, citas, enlaces, imágenes, tablas, elementos omitidos) pasan sin
  intervención manual.
- **SC-007**: Ningún usuario puede lograr que suenen dos documentos a la vez, verificado
  mediante pruebas manuales que intentan iniciar una segunda reproducción durante una ya
  activa.

## Assumptions

- El servicio se usa de forma anónima: no hay registro de usuarios, inicio de sesión ni
  biblioteca permanente de documentos en esta iteración.
- Solo se admiten archivos Markdown (`.md`) en UTF-8 con contenido en español; no se
  admiten PDF, Word, imágenes ni OCR, ni narración en otros idiomas.
- No se ofrece descarga del audio generado, ni historial de documentos, ni procesamiento
  por lotes de varios archivos.
- No se integran proveedores externos de síntesis de voz, pagos, suscripciones ni
  notificaciones.
- El tiempo máximo de procesamiento aceptable por documento y el dimensionamiento de
  recursos del servidor se fijan como objetivo operativo en 60 segundos para un documento
  de 5 MB (ver SC-001); este valor deberá confirmarse con pruebas de carga reales antes de
  publicar.
- La verificación de inteligibilidad de la voz (incluyendo números y siglas) se realizará
  mediante pruebas de escucha manuales antes de publicar; el umbral de aceptación
  propuesto es del 90% de palabras correctamente identificadas (ver SC-003).
- La licencia específica de los pesos del modelo de voz y el cumplimiento de las
  obligaciones de distribución del motor de síntesis (si se redistribuye) se resolverán
  como una tarea de cumplimiento legal antes de publicar, y no condicionan el
  comportamiento funcional descrito en esta especificación.
