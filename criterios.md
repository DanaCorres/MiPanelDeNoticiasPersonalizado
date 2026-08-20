# Criterios editoriales del panel

Este archivo se inyecta completo en el prompt de cada corrida. Está escrito
en lenguaje natural a propósito: para cambiar el comportamiento del panel se
edita este texto, no el código.

Las reglas 1 a 4 se aplican siempre. Las reglas 5 y 6 dependen de que la
llamada a la API esté activa; si falla, el panel cae al comportamiento
anterior y las ignora.

---

## Regla 1 — La sección la decide el contenido, no la fuente

Una nota va a la sección del país del que **trata**, sin importar por qué
feed llegó. Infobae, Aristegui y Milenio publican cobertura internacional
que hoy cae por default en Nacional; eso es un error.

- Nota sobre Nicaragua, Venezuela o Cuba → Mundo.
- Nota sobre Petro, Colombia o sus actores → CO.
- Nota sobre Milei, Argentina o sus actores → AR.
- Nota sobre España → ES.
- Nacional queda solo para México.

Excepción: si la nota trata de México **y** otro país en una relación
directa —una reunión bilateral, un acuerdo, una disputa comercial— va a
Nacional. El caso de Harfuch con la ministra argentina de Seguridad es
Nacional, correctamente.

---

## Regla 2 — Qué sube y qué baja

### Alta prioridad

- Decisiones institucionales con consecuencia: resoluciones, nombramientos,
  renuncias, votaciones, sentencias.
- Movimiento dentro de los partidos: alineaciones y pleitos internos,
  relevos, procesos de sucesión, candidaturas, rupturas de grupo.
- Conflicto entre partidos: denuncias e impugnaciones de un partido contra
  otro —ante la FGR, el INE o el TEPJF—, acusaciones cruzadas, deslindes,
  alianzas que se arman o se rompen, bloqueos legislativos. Que el PRI
  denuncie a Morena es exactamente esto, y va arriba.
- Confrontaciones entre actores políticos con nombre y apellido. **Incluye el
  conflicto personal aunque no haya todavía consecuencia institucional** —una
  demanda por daño moral tras una confrontación en el Senado sí importa,
  porque dice algo del estado de las relaciones de poder.
- Política pública con efecto material: presupuesto, vivienda, salud,
  seguridad, energía, cuando hay una decisión o una postura de por medio.
- Cobertura que revela algo no sabido: investigación, documento filtrado,
  dato duro nuevo.

### Baja prioridad (se muestra, pero abajo)

- Declaraciones sin hecho detrás. Un funcionario opinando sobre algo que no
  controla ni va a ejecutar. **No cuenta como "sin hecho" que un partido
  anuncie que va a denunciar, impugnar o romper una alianza**: ahí el anuncio
  es en sí el movimiento, aunque el papel no esté presentado todavía. La
  diferencia es si quien habla tiene la capacidad de hacer lo que dice.
- Notas de reacción: la nota que existe solo porque alguien respondió a otra
  nota.
- Efemérides, aniversarios, encuestas de popularidad rutinarias.

### Ruido — se descarta

Esto no se muestra. No va al final, no va en un pliegue: no entra al panel.

- **Contenido de servicio y trámites.** Es el ruido más frecuente y llega
  casi todo por los feeds `site:` de Google News. Se reconoce por el patrón:
  el titular es una pregunta con "quiénes pueden", "cómo tramitar", "qué
  requisitos", "cuándo se paga", "paso a paso"; el cuerpo es un instructivo
  dirigido al lector, no una noticia sobre una decisión. Los dos casos del
  IMSS del 19 de agosto son el ejemplo exacto.
- SEO puro: listas, "todo lo que se sabe", explicadores genéricos sin
  novedad, calendario escolar, fechas de pago.
- Virales, deportes, clima y servicio local, salvo que escalen a decisión de
  gobierno.

### La línea entre trámite y lanzamiento

Mencionar al IMSS, al Bienestar o a cualquier institución federal **no** hace
que una nota sea política; y tampoco la descalifica. Lo que decide es si hay
un hecho nuevo.

**Sí entra** cuando el gobierno acaba de hacer algo: lanza un programa, crea
o amplía una prestación, cambia una regla, publica en el DOF, fija un monto,
extiende la cobertura a un estado o a un grupo. Hay una fecha, un actor que
decidió y algo que antes era distinto.

**No entra** cuando la nota explica cómo usar algo que ya existía. No hay
hecho nuevo: hay un lector que quiere hacer un trámite.

La prueba más rápida: **¿esta nota seguiría siendo igual de válida dentro de
seis meses?** Si sí, es contenido perenne, es trámite, fuera. Una noticia
caduca; un instructivo no.

**Excepción crítica — ATDT.** Digitalizar trámites es literalmente el trabajo
de la Agencia de Transformación Digital y Telecomunicaciones, así que sus
notas hablan de trámites todo el tiempo y la regla anterior las mataría por
error. La distinción sigue siendo la misma pero hay que aplicarla con
cuidado: "la Llave MX ya permite hacer X" es un lanzamiento y **entra**;
"cómo sacar tu Llave MX paso a paso" es un instructivo y sale. Ante la duda
con la ATDT, conservar.

Ojo con el caso mixto, que es constante: cuando el gobierno lanza algo, en
las horas siguientes el mismo medio publica la versión "cómo registrarte".
Las dos mencionan el programa nuevo. Se conserva el anuncio y se descarta la
derivada.

---

## Regla 3 — Desambiguación de "política"

En español "política" es tres cosas y el clasificador viejo las confundía.
Al asignar subsección de Nacional, distinguir:

- **Política** (el campo): partidos, poderes, elecciones, gobierno como actor,
  conflicto entre actores políticos, salud e instituciones sociales vistas
  como decisión de gobierno.
- **Seguridad**: delito y crimen organizado, hechos violentos, operativos,
  detenciones, decomisos y justicia penal. Es su propia subsección porque en
  México el volumen lo justifica; antes se mezclaba con Política y la
  saturaba. La estrategia de seguridad como *policy* —una nueva doctrina, un
  cambio de mando, el presupuesto de la Guardia Nacional— también va aquí.
- **Economía**: cuando "política" aparece como *policy* de un tema económico.
  "Política de vivienda", "política monetaria", "política arancelaria" van a
  Economía, no a Política. El caso de Canadevi pidiendo ampliar la política
  de vivienda es Economía.
- **CDMX**: cuando el actor o el efecto es capitalino, aunque sea federal el
  interlocutor.
- **Opinión**: columna o análisis firmado, aunque el tema sea político.
- **Tecnología**: regulación digital, telecom, IA en clave mexicana.

---

## Regla 4 — Diversidad de fuentes

Ninguna fuente puede ocupar más de un tercio de los lugares visibles de una
sección. Milenio entra por un feed `site:` de altísimo volumen y hoy se lleva
ocho de cada nueve espacios de Nacional > Política; eso vacía de sentido el
balance de `fuentes.yaml`.

Cuando una fuente rebasa el tope, sus notas de menor prioridad pasan al
pliegue del final —no se eliminan, ceden lugar. Este pliegue es solo para
notas legítimas desplazadas por el tope; el ruido de la regla 2 nunca llega
ahí.

---

## Regla 5 — Resúmenes

Los feeds de Google News traen solo el titular, así que ahí no hay nada que
mostrar. Generar un resumen de dos líneas para esas notas, marcado
visualmente distinto del resumen que viene del RSS original, para que en el
panel siempre se sepa qué texto es de la fuente y qué texto es generado.

El resumen responde: qué pasó, quién lo decidió, a quién afecta. No
interpreta, no adjetiva, no completa lo que la nota no dice. Si el titular es
lo único disponible y no alcanza para dos líneas honestas, mejor no generar
resumen.

---

## Regla 6 — Encuadre y contraste

No etiquetar notas individuales como "de izquierda" o "de derecha". La línea
editorial de cada medio ya va como etiqueta fija en `fuentes.yaml`, que es
donde corresponde: es un dato estable y verificable.

Por nota, en cambio, anotar observaciones descriptivas y comprobables contra
el texto:

- qué actor aparece como sujeto del titular y cuál como objeto;
- a quién se cita como voz principal;
- qué actor implicado no aparece citado;
- si el encuadre es de conflicto, de gestión o de escándalo.

Cuando la misma historia aparezca en tres o más fuentes, agruparla y mostrar
cómo la titula cada una. Ese contraste vale más que cualquier etiqueta.

**El sesgo nunca ordena.** La etiqueta editorial no se usa para decidir qué
sube; se usa para lo contrario: si una sección queda con una sola línea
editorial en sus notas destacadas, subir del pliegue la mejor nota de otra
línea sobre el mismo tema.

---

## Regla 7 — Temas con seguimiento propio

Estos temas se rastrean por encima del criterio general de su sección: si una
nota califica aquí, entra aunque sea de bajo volumen o de una fuente chica.

### Inteligencia artificial — español e inglés por igual

El idioma no es un criterio de prioridad. La cobertura en inglés no vale más
por ser en inglés, ni menos por requerir traducción del titular. Se ordena
por relevancia, no por idioma.

Cuando el mismo hecho aparece en las dos lenguas, se agrupa como una sola
historia y se conserva la fuente que lo reporta de primera mano —
normalmente la anglosajona en lanzamientos de laboratorio, normalmente la
hispanohablante cuando el ángulo es regional o regulatorio.

Al generar resúmenes de notas en inglés, el resumen va en español. El titular
se deja en su idioma original, sin traducir.

Interesa especialmente: lanzamientos y capacidades nuevas de modelos,
regulación y política pública de IA, adopción en América Latina, e impacto
laboral y editorial. Interesa poco: rondas de inversión sin producto,
listicles de herramientas, hype sin lanzamiento.

### ATDT y gobierno digital federal

Seguimiento nombrado de la **Agencia de Transformación Digital y
Telecomunicaciones (ATDT)**, la dependencia federal con rango de secretaría
encargada de la digitalización del gobierno y de la política de
telecomunicaciones, a cargo de José Antonio Peña Merino.

Términos a rastrear: `ATDT`, `Agencia de Transformación Digital`, `Peña
Merino`, `Llave MX`, `gob.mx`, `identidad digital`, `expediente único`,
`interoperabilidad`, `autonomía tecnológica`, `ciberseguridad federal`.

No confundir con la **ADIP** (Agencia Digital de Innovación Pública), que es
de la Ciudad de México. Si aparece, va a la subsección CDMX, no a Nacional.

Adyacente y del mismo interés: la extinción del IFT y el traspaso de sus
atribuciones, el presupuesto de la Agencia, los conflictos de competencia con
otras dependencias, y la política de datos abiertos.

**Subsección**: las notas de la ATDT van a Tecnología por default. Pasan a
Política cuando el eje de la nota es el conflicto —disputas de competencia,
impugnaciones, discusión legislativa sobre sus atribuciones— y no la
capacidad técnica.
