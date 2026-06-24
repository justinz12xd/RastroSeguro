# RastroSeguro

### Inteligencia artificial explicable para priorizar siniestros con señales de posible fraude

> **No acusa. No rechaza pagos. No reemplaza al analista.**
> Ordena el trabajo: pone primero los casos que más lo necesitan y explica por qué.

*Reto Aseguradora del Sur — hackIAthon 2026*

---

## El problema

Cada día llegan miles de siniestros. La mayoría son legítimos, pero un porcentaje
esconde señales de fraude: pólizas que reclaman a los pocos días de emitirse,
proveedores que aparecen una y otra vez, documentos incompletos o inconsistentes,
relatos sospechosamente parecidos entre casos distintos.

Hoy esas señales se revisan **una por una, a mano**, y el resultado depende de:

- **La carga de trabajo:** el analista no puede mirar todo con la misma profundidad.
- **La experiencia individual:** lo que un revisor detecta, otro lo pasa por alto.
- **La falta de contexto:** una alerta aislada no muestra si el caso forma parte de
  un patrón mayor (una red, un proveedor recurrente, una narrativa repetida).

El costo no es solo el fraude que se paga: es también el **tiempo perdido** revisando
casos limpios y la **inconsistencia** en cómo se decide qué se investiga.

---

## La oportunidad

No se trata de "cazar fraudes" automáticamente, sino de **ordenar la revisión humana**:
que el analista empiece por donde hay más riesgo y llegue con el caso ya explicado.

Si la organización pudiera, de forma consistente y trazable:

1. **Detectar** las señales de riesgo en cada siniestro,
2. **Priorizar** los casos por nivel de riesgo,
3. **Explicar** el porqué de cada alerta, y
4. **Dejar la decisión final en manos de una persona**,

…se reducen las pérdidas por fraude, se acelera la operación y se gana control y
auditoría sobre cómo se toman las decisiones.

---

## Qué es RastroSeguro

RastroSeguro es una **plataforma de priorización de siniestros**. Recibe un caso,
analiza sus señales de riesgo y entrega:

- Un **puntaje de riesgo de 0 a 100**.
- Un **semáforo claro**: 🟢 Verde (rutina) · 🟡 Amarillo (revisar) · 🔴 Rojo (prioritario).
- Una **explicación en lenguaje claro** de qué disparó la alerta y con qué evidencia.
- Una **acción sugerida** para el analista.

Todo enmarcado en un principio: **es una priorización para revisión humana, no una
acusación de fraude.**

---

## En qué se basa (nuestros principios)

RastroSeguro se construye sobre cuatro ideas que lo diferencian de una "caja negra":

1. **IA explicable, no veredictos opacos.** Cada puntaje viene acompañado de las
   razones concretas que lo elevaron. Nada de "el algoritmo dijo que sí".

2. **El humano al centro.** El sistema recomienda y ordena; **la decisión siempre es
   de la persona**. Ningún pago se rechaza automáticamente.

3. **Trazabilidad total.** Toda alerta queda registrada con su evidencia y su regla de
   origen, lista para auditoría y para defender la decisión ante quien la cuestione.

4. **Mirada de conjunto, no caso aislado.** El riesgo de un siniestro se evalúa
   **en contexto del portafolio**: relaciones entre actores, patrones repetidos y
   concentraciones que solo se ven mirando el todo.

---

## Cómo funciona (en concepto)

```
Recepción del caso  →  Lectura de señales  →  Puntaje + semáforo  →  Priorización
        ↓                      ↓                      ↓                    ↓
  con verificación      múltiples señales      explicación clara     el analista
  humana del documento  de riesgo combinadas   y evidencia por dato   decide y actúa
```

1. **Recepción con verificación.** El caso entra por archivo de datos o por documento
   (PDF/texto). Cuando es un documento, el sistema **extrae los campos, marca su nivel de
   confianza y alerta inconsistencias**, pero **exige confirmación humana** antes de
   procesar. La persona valida lo extraído; el sistema nunca asume.

2. **Lectura de señales de riesgo (equipo de analistas especializados).** En lugar de un
   único modelo monolítico, un **coordinador** reparte cada caso entre **analistas
   especializados** que trabajan en paralelo, cada uno experto en su dominio: reglas de
   negocio auditadas, comportamiento atípico frente al histórico, similitud entre relatos,
   y relaciones entre asegurados/proveedores/beneficiarios. Un paso final **consolida** sus
   hallazgos en una sola conclusión trazable. Así, ante cada pregunta el coordinador decide
   qué especialista debe responder y deja registro de quién intervino.

3. **Puntaje y semáforo.** Las señales se integran en un único puntaje 0–100 y un
   nivel de riesgo Verde/Amarillo/Rojo, fácil de leer de un vistazo.

4. **Explicación y acción.** El caso llega al analista **ya explicado**: qué se activó,
   con qué evidencia y qué se recomienda hacer.

---

## Qué resuelve (casos concretos)

RastroSeguro detecta y prioriza patrones que a mano son difíciles de ver:

- **Borde de vigencia:** siniestros que ocurren sospechosamente cerca del inicio de la
  póliza.
- **Proveedor recurrente:** talleres, clínicas o peritos que concentran un volumen
  anómalo de casos de alto riesgo.
- **Narrativa clonada:** descripciones de siniestros demasiado parecidas entre casos
  distintos (relatos "copiados").
- **Montos atípicos:** reclamos desproporcionados frente a la suma asegurada o al
  histórico del ramo.
- **Documentación inconsistente o incompleta:** expedientes que no cuadran.
- **Redes de fraude:** grupos de casos conectados por actores compartidos que, vistos
  juntos, revelan una posible operación organizada.

Y permite responder, en lenguaje natural, preguntas de negocio como:
*"¿Qué proveedores concentran el 80% de las alertas rojas?"* o
*"Muéstrame los casos prioritarios de este mes y por qué."*

---

## El valor para cada actor

| Actor | Qué gana |
|---|---|
| **Analista de siniestros** | Una bandeja **priorizada y explicada**: empieza por lo importante y no parte de cero. |
| **Equipo antifraude** | **Detección temprana de patrones** y redes que de otro modo pasarían desapercibidos. |
| **Gerencia** | Visión del riesgo del portafolio y una **estimación del impacto** de priorizar bien. |
| **Auditoría / Cumplimiento** | **Trazabilidad completa** de cada alerta y decisión, defendible y revisable. |
| **Cliente honesto** | Sus reclamos legítimos **fluyen más rápido**, porque la atención se concentra donde hay riesgo. |

---

## Lo que nos diferencia

- **Explica, no solo puntúa.** Cada alerta es entendible y auditable.
- **Prioriza, no sentencia.** Es una herramienta de apoyo a la decisión, no un juez automático.
- **Mira el conjunto.** Encuentra patrones y redes, no solo casos sueltos.
- **Coordina especialistas.** Un orquestador delega cada análisis en el experto adecuado
  (reglas, anomalías, narrativas, redes) y consolida sus hallazgos, con traza de quién participó.
- **Diseñado con ética desde el inicio.** Lenguaje de "posible fraude / requiere revisión",
  confirmación humana obligatoria y cero rechazos automáticos.
- **Pensado para integrarse.** Una capa de priorización que se acopla al flujo de
  siniestros existente, sin reemplazarlo.

---

## Ética y responsabilidad

Esto es lo más importante del proyecto, no una nota al pie:

- **Nunca acusamos de fraude.** Hablamos de *señales de riesgo* y *casos a revisar*.
- **Nunca rechazamos un pago automáticamente.** La última palabra es siempre humana.
- **Evitamos el sesgo opaco:** toda decisión es explicable y trazable.
- **Protegemos al cliente honesto:** el objetivo es agilizar lo legítimo, no entorpecerlo.

---

## Impacto esperado

- **Menos pérdidas:** los casos de mayor riesgo se revisan primero y a tiempo.
- **Más eficiencia:** menos horas gastadas en expedientes limpios.
- **Más consistencia:** todos los analistas parten del mismo criterio explicable.
- **Más control:** trazabilidad y reportes listos para auditoría y gerencia.

---

## Próximos pasos

1. **Integración** con el core de pólizas y siniestros de la aseguradora.
2. **Calibración con datos reales anonimizados** (hoy el prototipo opera sobre datos
   sintéticos: las métricas demuestran el concepto, no garantizan producción).
3. **Bucle de retroalimentación del analista** para reducir falsos positivos con el uso.
4. **Despliegue productivo** con monitoreo de la calidad del modelo en el tiempo.

---

## En una frase

> **RastroSeguro convierte miles de siniestros dispersos en una lista priorizada y
> explicada, para que el equipo humano revise primero lo que realmente importa —
> con criterio, con evidencia y sin acusar a nadie.**Último día del hackIAthon 🚀

Han sido días intensos con amigos Carlos Chile y Justin Alejandro Zambrano Lucas, de mucho aprendizaje, trabajo en equipo, ideas, errores, ajustes y bastante código. Llegar hasta este punto ya ha sido una experiencia muy valiosa para nosotros.

Como equipo, nos sentimos agradecidos por haber formado parte de este reto, por la oportunidad de construir una solución con inteligencia artificial en tan poco tiempo y por compartir este espacio con tantos equipos talentosos.

Más allá del resultado final, nos quedamos con el aprendizaje, la presión positiva de crear algo funcional, la importancia de organizarnos bien y la motivación de seguir creciendo como futuros profesionales en tecnología.

Gracias a la organización, sponsors y aliados por impulsar espacios como este, donde podemos retarnos, aprender y demostrar lo que somos capaces de construir.

#hackIAthon #IAenEcuador #AgenteIA #AgenteASUR #DesafíoTechIA #AIChallenge #IdeasQueImpactan

*RastroSeguro — hackIAthon 2026 — Reto Aseguradora del Sur*
