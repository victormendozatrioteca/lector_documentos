<!--
Informe de impacto de sincronizacion (retirar antes de realizar el commit):
- Version: 2.3.0 -> 2.4.0; seleccion del modelo y obligaciones de licencia.
- Principios modificados: Sintesis de voz y Voz natural fijan es_ES-davefx-medium;
  Stack Tecnologico incorpora licencias y aceptacion del responsable;
  Decisiones explicitas distingue decisiones tomadas y pendientes.
- Secciones agregadas o eliminadas: ninguna.
- Plantillas dependientes: sin cambios; consumen esta constitucion en tiempo de ejecucion.
- Pendiente: aclarar la licencia especifica de los pesos antes de redistribuirlos;
  CC0 del dataset y MIT del repositorio no acreditan por si solas esa licencia.
-->

# Constitucion del Proyecto: Lector de Documentos con Voz

## 1. Naturaleza del Proyecto

Esta es una aplicacion web para subir un documento Markdown y escucharlo con una
voz sintetizada de calidad natural. El frontend recibe el fichero y permite
reproducir el audio; el backend en Python procesa el texto y genera la voz.
"Voz humana" significa una voz TTS natural, no una grabacion de una persona ni
clonacion de voces.

## 2. Stack Tecnologico (Reglas de Implementacion)

- **Frontend / UI:** React con TypeScript y Vite. Usar Tailwind CSS para los estilos.
- **Backend:** Python con FastAPI. Recibir el documento mediante `multipart/form-data`
  y entregar audio reproducible por el navegador, sin usar los altavoces del servidor.
- **Gestion de Python:** Usar exclusivamente `uv` para entorno, dependencias y
  ejecucion. Declarar la version de Python en `pyproject.toml`, versionar `uv.lock`
  y usar `uv sync --locked` y `uv run` para instalar y ejecutar.
- **Sintesis de voz:** Usar Piper mantenido por OHF en el backend Python con
  `es_ES-davefx-medium`, variante espanol de Espana (`es_ES`), calidad media,
  un hablante y frecuencia de muestreo de 22.050 Hz. El modelo requiere
  `es_ES-davefx-medium.onnx` y su configuracion `es_ES-davefx-medium.onnx.json`.
  La sintesis debe ejecutarse localmente en el servidor, sin servicios
  TTS externos ni claves de proveedor. Con el motor y modelo instalados, debe
  funcionar sin acceso a Internet. No sustituir Piper por `speechSynthesis`.
  Documentar en `plan.md` la version del motor, modelo, variante regional,
  formato de audio, recursos necesarios y licencias del motor y del modelo.
  Documentar la descarga inicial y conservacion del modelo como recurso de la
  aplicacion, separado de los documentos y audios temporales del usuario.
- **Licencias consultadas y aceptacion:** El responsable acepta las condiciones
  verificadas el 2026-10-08. La [ficha de davefx-medium](https://huggingface.co/rhasspy/piper-voices/blob/main/es/es_ES/davefx/medium/MODEL_CARD)
  declara CC0 para el dataset: permite reutilizacion, modificacion y uso comercial
  sin exigir atribucion. El [repositorio de voces](https://huggingface.co/rhasspy/piper-voices/blob/main/README.md)
  declara MIT; su declaracion general no se debe presentar como prueba concluyente
  de una licencia independiente para los pesos. La ficha no declara esa licencia
  expresamente; aclararla y documentar su alcance antes de redistribuir los pesos.
  Esta incertidumbre no queda resuelta por la aceptacion del responsable.
  El [motor Piper de OHF](https://github.com/OHF-Voice/piper1-gpl/blob/main/COPYING)
  utiliza GPL-3.0, que permite uso comercial. Al distribuir software cubierto,
  conservar avisos y licencia y proporcionar el codigo fuente correspondiente
  conforme a sus condiciones. El acceso web a Piper ejecutado en el servidor no
  obliga por si solo a publicar el backend por GPL-3.0. Antes de distribuir una
  aplicacion o imagen Docker que lo incluya, revisar el alcance del copyleft sobre
  la integracion y las obligaciones de todos los componentes. Registrar en
  `plan.md` las versiones y revisiones exactas y sus evidencias de licencia.
- **Persistencia:** No usar base de datos ni conservar documentos o audios de forma
  permanente salvo que una especificacion aprobada lo requiera.

## 3. Reglas de Dominio y Logica de Negocio

Estas reglas son obligatorias y no se pueden cambiar desde el codigo:

- **Entrada inicial:** Aceptar solo archivos `.md` en UTF-8. PDF, Word y otros
  formatos quedan fuera del alcance hasta que se apruebe una especificacion.
  El tamano maximo del fichero es 5 MB (5.000.000 bytes), inclusive; el limite
  corresponde al archivo, no al envoltorio de la peticion multipart.
- **Idioma:** El contenido narrable del documento y la voz de lectura deben estar
  en espanol. No ofrecer traduccion ni lectura en otros idiomas en esta iteracion.
- **Lectura fiel:** Respetar el orden y contenido narrable segun las reglas basicas
  siguientes. No resumir, traducir ni reescribir el texto. Usar un parser Markdown
  mantenido; las exclusiones expresas de estas reglas no constituyen un resumen.
- **Markdown narrable:** Leer encabezados, parrafos, citas y elementos de listas
  con pausas entre bloques, sin pronunciar sus marcadores de formato. Leer el
  texto visible de los enlaces, no sus URLs; para imagenes, leer solo el texto
  alternativo si existe, sin generar descripciones. Leer tablas por filas,
  primero los encabezados y despues las celdas de izquierda a derecha, con pausas
  entre celdas. Omitir codigo en linea, bloques de codigo, URLs aisladas y lineas
  separadoras. Omitir HTML crudo, sin renderizarlo ni ejecutarlo. Conservar la
  puntuacion del texto narrable. Incluir ejemplos y pruebas de estas reglas en `spec.md`.
- **Voz natural:** Usar `es_ES-davefx-medium` como voz predeterminada en espanol
  de Espana. Definir en `spec.md`
  una prueba de escucha con textos en espanol que compruebe pronunciacion e
  inteligibilidad, incluidos numeros y siglas; registrar el resultado en `plan.md`.
- **Reproduccion:** Ofrecer controles de reproducir, pausar, reanudar y detener.
  Iniciar la reproduccion por accion del usuario; no reproducir documentos simultaneamente.
  El boton Play/Pausa debe reflejar el estado actual; reanudar conserva la posicion
  y detener pausa y vuelve al inicio. Ofrecer un selector de velocidad con valores
  0,75x, 1x, 1,25x, 1,5x y 2x; usar 1x por defecto. Aplicar el cambio mediante
  `playbackRate` en el navegador, sin regenerar la voz ni reiniciar la posicion.
  Mostrar una linea de tiempo con tiempo transcurrido y duracion total, que permita
  avanzar o retroceder arrastrando o pulsando en ella. Deshabilitar estos controles
  hasta que el audio y sus metadatos esten disponibles. Los botones, selector y
  linea de tiempo deben ser accesibles por teclado y tener etiquetas comprensibles.
- **Privacidad:** Informar que el fichero se envia al backend y que Piper genera
  la voz en ese servidor, no en el navegador. No enviar el texto a proveedores
  TTS externos ni usar uno como alternativa automatica si Piper falla.
  No incluir documentos ni credenciales en los registros.
- **Seguridad:** Nunca ejecutar codigo ni instrucciones del documento, ni descargar
  sus enlaces automaticamente. Tratar el archivo como datos no confiables.
- **Archivos temporales:** No modificar el original. Eliminar los temporales al
  terminar, fallar o cancelar; el plan debe definir su limpieza si se pierde la conexion.

## 4. Estructura y Estilo de Codigo

- **Estructura simple:** Usar `/frontend` y `/backend`, con pruebas junto a cada parte.
  Evitar Clean Architecture, microservicios y capas sin una necesidad documentada.
- **Responsabilidades:** Separar carga y validacion, conversion Markdown y motor TTS
  con funciones o modulos pequenos; no crear un framework interno.
- **Estilo:** Usar componentes funcionales y Hooks en React. En Python, preferir
  funciones con anotaciones de tipos; usar clases solo cuando aporten una necesidad real.
- **Nomenclatura:** `snake_case` para funciones y variables Python; `camelCase` para
  funciones y variables TypeScript; `PascalCase` para componentes, clases y tipos.
- **Secretos:** Piper no requiere claves de proveedor. Si otras integraciones
  requieren secretos, mantenerlos en el backend mediante variables de entorno;
  nunca enviarlos al navegador ni versionarlos.

## 5. Manejo de Errores y Validaciones

- **Validacion:** Comprobar en el backend extension, codificacion, contenido narrable
  y tamano antes de sintetizar. Rechazar archivos mayores de 5.000.000 bytes con
  HTTP `413`; aplicar el limite durante la carga, sin leer un fichero ilimitado
  completo en memoria. El frontend debe advertir si se supera el mismo limite,
  pero no sustituye la validacion del servidor. Definir tiempos de espera en `spec.md`.
- **UI:** Mostrar estados de carga, generacion, reproduccion y error. Traducir los
  fallos a mensajes claros; no mostrar stack traces ni errores crudos del proveedor.
- **API:** Usar codigos HTTP semanticos: `400` para entrada invalida, `413` para
  exceso de tamano, `415` para formato no admitido, `503` si Piper o el modelo no
  estan disponibles y `500` ante un fallo interno de sintesis. Definir en el
  contrato API la respuesta para tiempo de procesamiento agotado; reservar `504`
  para tiempos de espera de un servicio ascendente cuando se actue como gateway.
  No devolver exito cuando falle la sintesis.
- **Pruebas:** Cubrir carga, conversion, errores del motor y controles de audio.
  Verificar el limite exacto de 5.000.000 bytes y el rechazo de 5.000.001 bytes,
  las reglas de narracion, Play/Pausa, reanudacion, detencion, cambio de velocidad
  sin reinicio y desplazamiento por la linea de tiempo.
  Las pruebas habituales deben usar dobles TTS y no necesitar red ni credenciales.
  Verificar la voz real antes de publicar cambios del motor.
- **Calidad:** Antes de integrar, ejecutar pruebas y compilacion del frontend y
  `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` y
  `uv run mypy .` desde el backend; declarar las herramientas de desarrollo.

## 6. Comportamiento del Agente de IA (Reglas SDD)

- **Cero codigo sombra:** Construir estrictamente lo documentado en `spec.md`.
  No agregar cuentas, pagos, historiales, descarga de audio ni formatos adicionales
  "por si acaso".
- **Fuente de la verdad:** Seguir el flujo `spec.md`, `plan.md`, `tasks.md` e
  implementacion. Vincular cada tarea con un requisito y sus criterios de aceptacion.
- **Conflictos:** Si una peticion contradice esta constitucion o tiene una falla
  logica, detener los cambios afectados, explicar el problema y solicitar actualizar
  la constitucion y/o `spec.md`, segun corresponda, antes de tocar codigo fuente.
- **Decisiones explicitas:** Piper y `es_ES-davefx-medium` son el motor y modelo
  elegidos. No inventar la version del motor, licencias no acreditadas, tiempos
  de espera, requisitos de hardware ni politicas de almacenamiento. Resolver
  estos aspectos en los artefactos SDD antes de implementar lo que dependa de ellos.
- **Verificacion:** Incluir pruebas de los cambios y pruebas de regresion para
  correcciones; informar que se verifico y que no pudo comprobarse.

## Gobernanza

Esta constitucion prevalece sobre planes y codigo. Cada revision debe comprobar
su cumplimiento. Las enmiendas requieren aprobacion del responsable del proyecto,
motivo documentado y actualizacion de los artefactos afectados. Usar SemVer:
MAJOR para reglas incompatibles, MINOR para obligaciones nuevas y PATCH para
aclaraciones. Conservar la fecha de ratificacion y actualizar la de enmienda.

**Version**: 2.4.0 | **Ratified**: 2026-10-08 | **Last Amended**: 2026-10-08
