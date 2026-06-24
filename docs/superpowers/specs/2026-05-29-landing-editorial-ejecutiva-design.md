# Rediseño landing: segunda mitad en lenguaje editorial ejecutivo

## Objetivo

Mantener el hero actual de la landing, pero rediseñar desde la sección de magnitud hacia abajo para que la experiencia se sienta más ejecutiva, premium y memorable. El problema actual es que después del hero la página cae en superficies demasiado blancas y homogéneas, lo que reduce contraste, ritmo visual y percepción de valor.

## Resultado buscado

La segunda mitad debe sentirse coherente con el hero, con más dirección de arte y más jerarquía visual. Debe conservar un tono institucional y serio, pero dejar de parecer una secuencia de tarjetas genéricas.

## Dirección visual aprobada

- Estilo: editorial ejecutiva
- Base cromática: azul petróleo + marfil
- Acentos: verde muy puntual para validación o confianza; no como color dominante
- Sensación: institucional, premium, clara, con contraste y ritmo entre secciones

## Alcance

Este cambio aplica solo a la landing en `frontend/app/landing/page.tsx` y a los estilos que la soportan en `frontend/app/globals.css`, además de ajustes menores en componentes visuales de la landing si hacen falta para sostener el nuevo lenguaje.

No incluye:

- cambios de copy estructural profundos
- rediseño del hero principal
- cambios en la plataforma `/platform`

## Problema detectado

La mitad inferior de la landing usa fondos muy similares entre sí (`background`, `surface-low`, blanco) y tarjetas repetidas con poca variación. Eso produce:

- pérdida de tensión visual después del hero
- secciones que no construyen narrativa entre sí
- una percepción demasiado simple o genérica
- poca separación emocional entre “problema”, “solución” y “cierre”

## Propuesta de diseño

### 1. Sección Magnitud

La sección de magnitud pasará de un bloque claro estándar a una banda editorial marfil con una composición más protagonista.

Cambios:

- fondo marfil cálido con sutil textura o gradiente sobrio
- bloque del `10%` como ancla visual dominante
- una pieza lateral o superior con tinte azul petróleo para enmarcar la cifra
- facts secundarios presentados con divisores finos y más aire, en lugar de parecer tabla plana

Objetivo:

Que la magnitud del problema se sienta como una declaración ejecutiva, no como un bloque informativo normal.

### 2. Sección Problema

La sección de problema debe introducir más tensión y contraste que la anterior.

Cambios:

- usar una banda más profunda o entintada, cercana al azul petróleo desaturado
- reemplazar las tres tarjetas blancas por módulos con fondos diferenciados dentro de la misma familia cromática
- reforzar la jerarquía de cada pregunta con tipografía más visible y una pequeña señal visual editorial

Objetivo:

Que el usuario perciba claramente que aquí hablamos de fricción operativa real, no de beneficios todavía.

### 3. Sección Solución

La sección de solución debe ser el gran punto de alivio visual y estratégico.

Cambios:

- convertirla en una banda premium con fondo azul petróleo más marcado
- mantener el flujo/animación como pieza central, pero alojado dentro de un contenedor claro o translúcido de alto contraste
- hacer que los pilares y el flujo se lean como parte de una narrativa de transformación, no como una lista aislada

Objetivo:

Que “solución” contraste claramente contra “problema” y se sienta como el momento de claridad de la landing.

### 4. Cierre

El cierre debe dejar de parecer otra caja blanca convencional.

Cambios:

- transformarlo en una pieza más ejecutiva, tipo bloque de decisión o recomendación final
- fondo con mayor carácter visual que la maqueta actual
- CTA principal integrado en una composición de confianza y decisión
- mantener la nota ética visible, pero mejor integrada al lenguaje premium

Objetivo:

Cerrar con sensación de convicción, confianza y valor operativo.

## Sistema visual

### Color

- Priorizar azul petróleo para contraste estructural
- Usar marfil para descanso visual premium
- Reservar verde para elementos de validación, evidencia o confianza
- Reducir el uso de blanco puro en fondos amplios de la segunda mitad

### Ritmo

- Alternar bandas claras y oscuras con intención
- Evitar que dos secciones consecutivas usen la misma sensación de fondo
- Crear progresión narrativa: magnitud → tensión → claridad → decisión

### Superficies

- Menos tarjetas genéricas repetidas
- Más bloques compuestos y paneles con propósito editorial
- Divisores, tintes y contraste antes que cajas blancas planas

### Tipografía

- Mantener la familia actual
- Subir presencia de cifras, headings y subtítulos de sección
- Hacer que los títulos lideren más la composición

## Comportamiento responsive

- El rediseño debe conservar buena lectura en móvil
- Las bandas de color deben mantenerse intencionales en pantallas pequeñas
- Las animaciones ya corregidas en móvil deben seguir funcionando
- El cambio visual no debe depender de hover para percibirse como premium

## Implementación prevista

- actualizar estructura de clases en `frontend/app/landing/page.tsx`
- añadir nuevas clases y variables de soporte en `frontend/app/globals.css`
- ajustar componentes de landing solo donde sea necesario para integrarlos al nuevo sistema visual

## Riesgos y mitigaciones

- Riesgo: que la segunda mitad se vuelva demasiado oscura y rompa la continuidad con el hero.
  Mitigación: usar contraste alternado con marfil y mantener acentos de luz en contenidos.

- Riesgo: que el rediseño se vea decorativo pero no institucional.
  Mitigación: limitar la paleta, usar tipografía sobria y evitar ornamentos gratuitos.

- Riesgo: que móvil pierda legibilidad.
  Mitigación: comprobar stacking, padding, contraste y orden visual en cada banda.

## Validación

El trabajo se considerará correcto si:

- la segunda mitad deja de sentirse blanca, plana o genérica
- hay más contraste entre secciones
- el lenguaje visual sigue alineado con el hero actual
- la percepción general mejora hacia “ejecutiva premium”
- la landing sigue compilando y funcionando correctamente
