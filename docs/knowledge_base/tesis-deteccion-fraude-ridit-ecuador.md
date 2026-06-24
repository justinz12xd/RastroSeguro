MODELO DE DETECCIÓN DE FRAUDES EN LOS
SEGUROS DE VEHÍCULOS UTILIZANDO COMPONENTES
PRINCIPALES Y ANÁLISIS RIDIT

Heydi Mariana Roa López1, Fernando Sandoya Sánchez2

1 Ingeniera en Estadística Informática 2004

2 Director de Tesis, Magíster en Investigación de Operaciones, Escuela
Politécnica Nacional de Quito, Profesor de ESPOL desde 1994

RESUMEN

*El* *presente* *trabajo* *tiene* *como* *propósito* *proporcionar*
*una* *metodología* *dirigida* *a* *cuantificar* *la* *probabilidad*
*de* *fraude* *en* *las* *declaraciones* *de* *siniestros*
*vehiculares,* *denominada* *Análisis* *PRIDIT,* *específicamente*
*cuando* *se* *tienen* *variables* *cualitativas* *involucradas*
*puesto* *que* *en* *el* *Ecuador* *no* *son* *muy* *numerosos* *los*
*estudios* *dedicados* *a* *la* *detección* *de* *fraudes* *con*
*este* *tipo* *de* *variables.*

*La* *metodología* *PRIDIT* *no* *es* *más* *que* *una* *técnica*
*no-paramétrica* *más* *simple* *y* *fácil* *de* *entender* *e*
*implementar,* *además* *puede* *satisfacer* *necesidades*
*gerenciales* *debido* *a* *que* *las* *aplicaciones* *de* *esta*
*metodología* *pueden* *extenderse* *a* *clasificaciones* *mucho*
*más* *finas* *que* *la* *prueba* *binaria* *de* *detección*
*fraude/no* *fraude,* *puesto* *que* *provee* *un* *valor* *adicional*
*en* *su* *capacidad* *de* *probar* *la* *consistencia* *de* *su*
*modelo* *de* *puntuaciones* *con* *los* *patrones* *de* *las*
*variables* *de* *entrada.* *Específicamente,* *los* *pesos* *y* *las*
*puntuaciones* *obtenidos* *de* *la* *metodología* *PRIDIT* *son*
*representativos* *de* *las* *variables* *de* *entrada* *y* *pueden*
*ser* *probados* *a* *través* *de* *la* *correlación* *con* *otros*
*modelos* *de* *puntuaciones* *ya* *determinados.*

ABSTRACT

*This* *research* *has* *as* *purpose* *to* *provide* *a*
*methodology* *directed* *to* *quantify* *the* *fraud* *probability*
*in* *the* *insurance* *vehicular* *claims,* *denominated* *Analysis*
*PRIDIT,* *specifically* *when* *qualitative* *variables* *are*
*involved* *since* *in* *the* *Ecuador* *they* *are* *not* *very*
*numerous* *the* *studies* *dedicated* *to* *the* *detection* *of*
*frauds* *with* *this* *type* *of* *variables.*

*The* *methodology* *PRIDIT* *is* *not* *more* *than* *a*
*no-parametric* *technique* *statistic* *simpler* *and* *easier* *of*
*to* *understand* *and* *to* *implement,* *it* *can* *also* *satisfy*
*managerial* *necessities* *because* *the* *applications* *of* *this*
*methodology* *can* *extend* *to* *much* *finer* *classifications*
*that* *the* *binary* *test* *of* *detection* *fraud/no* *fraud,*
*since* *it* *provides* *an* *additional* *value* *in* *its*
*capacity* *to* *prove* *its* *model's* *of* *scores* *consistency*
*with* *the* *patterns* *of* *the* *entrance* *variables.*
*Specifically,* *the* *weight* *and* *the* *obtained* *scores* *of*
*the* *methodology* *PRIDIT* *is* *representative* *of* *the*
*entrance* *variables* *and* *they* *can* *already* *be* *proven*
*through* *the* *correlation* *with* *other* *models* *of* *score*
*certain.*

1 INTRODUCCIÓN Objetivos específicos:

Un término desgraciadamente muy utilizado en toda la sociedad es el de
“fraude”. Conocemos por fraude cualquier actividad en la que para
derivar un beneficio económico, se crean situaciones ficticias o se
exageran daños.

El fraude está considerado como una de las industrias criminales más
grandes en la sociedad, y según estudios de varios investigadores
aumentan en épocas donde la gente necesita dinero tales como la
Navidad, Fin de año, etc.

A pesar de que el fraude se da en casi todas las ramas, los fraudes en
los seguros se han convertido en una práctica común. El mercado
asegurador considera el fraude como un factor ineludible de riesgo y,
hoy en día las entidades luchan por desarrollar un foco de acción
frente al mismo. Es por esto que el presente estudio tiene los
siguientes objetivos:

2 Objetivo general

Aplicar un modelo de detección de fraude a una cartera real de seguro
de automóviles enfocado en las declaraciones de siniestros de
automóviles para clasificar y cuantificar el nivel de fraude de cada
una de estas declaraciones realizadas por los asegurados.

• Reducir la incertidumbre e incrementar las oportunidades de
clasificar las demandas correcta y eficientemente a cada grupo
(fraudulentas / no fraudulentas) sin importar el tipo de variables que
intervengan.

• Transformar respuestas categóricas en un conjunto de valores
numéricos que estén dentro de un intervalo \[-1,1\], lo cual refleje
la relativa anormalidad de una respuesta en particular.

• Determinar una ponderación de fraude para cada variable involucrada
en el análisis.

• Determinar una medida de poder discriminatorio que permita
clasificar las demandas en fraudulentas y no fraudulentas.

1. MOTIVACIÓN PARA LA INVESTIGACIÓN

La influencia de las acciones deshonestas por parte de los asegurados
se deja sentir tanto en el número de siniestros declarados como en la
cuantía de los mismos, si consideramos el peso que ello puede tener a
la hora de justificar la aparición de resultados técnicos negativos
durante los últimos años en el seguro de vehículos y el incremento del
valor de las primas por la contratación de estos mismos seguros, queda
más que justificada la necesidad de diseñar herramientas que ayuden a
las entidades en la detección y lucha contra el fraude.

En el Ecuador no se han hecho estudios serios al respecto, sin embargo
en otros países este tipo de estudios están bien adelantados, como por
ejemplo: En España, según la Investigación Cooperativa entre Entidades
Aseguradoras y Fondos de Pensión (ICEA), el sector del automóvil es el
que más fraudes registra, puesto que de los 46.228 casos detectados en
el 2001, el 90 por ciento correspondía a esta rama. En lo que respecta
al año en curso (2004) según datos de la ICEA, más del 75 por ciento
de los casos de fraude detectados corresponde a la rama de vehículos.

Para el caso de las compañías de seguros de nuestro país les es más
fácil pagar los siniestros reclamados por los asegurados que entrar en
trámites legales, ya que en el país no se cuenta con una unidad
investigativa a la que puedan recurrir las aseguradoras para verificar
la honestidad de los reportes de siniestros. Por todo esto, es que las
aseguradoras deberían estar interesadas en buscar métodos que les
permitan detectar y clasificar una demanda como fraudulenta o no.

2. EL SEGURO VEHICULAR EN EL ECUADOR
DURANTE LA ÚLTIMA DÉCADA

Durante la década (1.993 – 2003) en el Ecuador, muchas de las
aseguradoras que ofrecen seguros para automóviles se percataron de que
el monto de indemnización pagado a sus asegurados por causa de un
siniestro específico era muy alto. El mercado asegurador del Ecuador
durante esta última década ha visto en el ramo de seguros de
vehículos, el ramo con mayor monto pagado por siniestros en lo que
respecta a los demás ramos de seguros.

La Superintendencia de Bancos y Seguros del Ecuador dispone de la
información de los montos totales de siniestros pagados de todas las
aseguradoras en el ramo de vehículos.

CUADRO 1

MONTO TOTAL DE INDEMNIZACIÓN LIQUIDADA POR SINIESTROS VEHICULARES PARA
EL PERÍODO 1.993 – 2.003

Fuente: Superintendencia de Bancos y Seguros del Ecuador

Elaboración: Heydi Roa López

GRÁFICO 1

Monto Total de Siniestros Pagados en el
Ecuador en el Ramo de Vehículos Período
1.993- 2003

\$ (en miles de dólares)

90,000 80,599 80,000

70,000 59,907 65,601 60,000 51,06353,663

50,000

36,990 40,000

30,000 28,058

20,000

10,000

0

1993 1994 1995 1996 1997 1998 1999 2000 2001 2002 2003

Año

Elaboración: Heydi Roa López

En el GRÁFICO 1 se puede visualizar la tendencia creciente de los
pagos de siniestros a los asegurados desde 1.993 hasta 1.998,
notándose claramente la reducción de los pagos en el año 1.999 y 2.000
por los temores económicos que en ese período se suscitaron; sin
embargo a partir del 2.001 vuelve la tendencia creciente, una vez
adoptado el dólar como moneda oficial.

Para reflejar con precisión la evolución de los montos de siniestros
pagados por las aseguradoras se ha procedido a calcular los números
índices con año base 1.993 = 100. La conversión de los datos a índices
facilita la estimación de la tendencia en una serie compuesta por
números muy grandes con se está manejando (miles de dólares). Ver
TABLA I y GRÁFICO 2.

TABLA I

MONTO TOTAL DE INDEMNIZACIÓN PAGADA E ÍNDICES CON AÑO BASE 1.993 = 100

Elaboración: Heydi Roa López

GRÁFICO 2

<img src="./eti1idxg.png"
style="width:2.04856in;height:0.94124in" />Indices del
Monto Total de Siniestros Liquidados con
Año Base 1993 = 100

300 287

250 234

200 182 191 214 170

150 132 132 124 119

100

50

0

1993 1994 1995 1996 1997 1998 1999 2000 2001 2002 2003

Elaboración: Heydi Roa López

Actualmente en nuestro país, Ecuador, existen 40 compañías dedicadas al
mercado asegurador, de las cuales 27 ofrecen pólizas de seguros para
vehículos.

2.1. PAGOS DE SINIESTROS EN SEGUROS
VEHICULARES

Una de las compañías aseguradoras del país mayormente involucrada con
el seguro de vehículos es Seguros Equinoccial. Durante la última
década, esta compañía ha sido una de las que mayores pagos ha
realizado a

sus clientes por siniestros vehiculares. La información con la que se
cuenta es con los montos pagados por siniestros vehiculares en cada
una de sus sucursales desde el 2.000 hasta el 2.003.

CUADRO 2

MONTOS PAGADOS POR SINIESTROS VEHICULARES POR SEGUROS EQUINOCCIAL
(PERÍODO 2.000 – 2.003)

Fuente: Base de Datos Seguros Equinoccial del Ecuador

Elaboración: Heydi Roa López

Por la información presentada se puede concluir que los montos pagados
por siniestros de vehículos aumentan año a año y por ende son el punto
fijo de investigación por parte de los departamentos de siniestros,
quienes tendrán de ahora en adelante la tarea de implementar nuevas
técnicas de detección de

fraude en las declaraciones de siniestros.

3. LA METODOLOGÍA PRIDIT

La metodología PRIDIT constituye una nueva técnica no-paramétrica más
simple y fácil de entender e implementar, difiere de otras pruebas
estadísticas no-paramétricas, como la Chi Cuadrado, en la cual se
asume un orden natural de los datos, ya que esta técnica estadística
puede emplearse incluso con variables categóricas que pueden estar en
escalas subjetivas (severo, moderado, menor) o pueden tomar una forma
numérica donde el sistema de medición confía fuertemente en el método
experimental o en la habilidad técnica del científico involucradas en
la medición de la variable en cuestión.

TIPO DE DATOS

La mayoría de los métodos estadísticos utilizados para este tipo de
estudios requieren que los datos sean de tipo intervalo y en algunos
casos estos métodos requieren que los datos sean continuos y estén
normalmente distribuidos. Pero la metodología PRIDIT no pone ninguna
restricción en lo que respecta a los datos, así esta metodología
trabaja ya sea con variables ordinales discretas o con variables
categóricas, pero para el caso de seguros de automóviles por lo
general la mayoría de las variables son dicotómicas. Para el
desarrollo de esta

investigación se obtuvo información de 100 demandas de siniestros
vehiculares

TRANSFORMACIÓN DE LOS DATOS CATEGÓRICOS EN
PUNTUACIONES RIDIT

CUADRO 3

VARIABLES UTILIZADAS EN LA INVESTIGACIÓN

Elaboración: Heydi Roa López

Un método de puntuación de mejor desempeño para variables categóricas,
es el método de Puntuaciones RIDIT. El objetivo de este método de
puntuación es cuantificar el nivel de sospecha de fraude producida por
la representación categórica de cada variable indicadora de fraude en
una declaración de siniestro.

Sea *kt* el número de categorías disponibles y ordenadas para la
variable indicadora *t*, y sea *pt* =(*pt*1,..., *ptkt* ) las
proporciones de respuesta observadas en el conjunto entero de demandas.
Se asume que las categorías están ordenadas en relación a la
probabilidad de sospecha de fraude, en forma decreciente; por lo que una
respuesta categórica más alta indica menos sospecha de fraude.

Para la opción categórica *i* de la variable *t*, se asigna el valor
numérico o puntuación siguiente:

*Bti* =∑*ptj* -∑*ptj* *i* = 1, 2, …, *kt* *j*\<*i* *j*\>*i*

Así, este procedimiento transforma cualquier conjunto de respuestas
categóricas en un conjunto de valores numéricos dentro de un intervalo
\[-1, 1\], lo cual refleja la relativa

“anormalidad” de una respuesta particular.

sumando simplemente las puntuaciones de las variables individuales
respectivas.

TABLA III

CALCULO DE PUNTUACIONES RIDIT

Elaboración: Heydi Roa López

OBTENCIÓN DE PONDERACIONES PRIDIT Y PUNTUACIÓN
GLOBAL PARA UNA DEMANDA ENTERA

Sea *F* =(*fit* ) la notación de la matriz de las puntuaciones
individuales RIDIT para cada una de las *t* =1,2,...,*m*

variables, para cada una de las *i* =1,2,..., *N* demandas.

Esto es, *fit* = *Btk* si la demanda *i* contiene *k* niveles de
respuestas

categóricas para la variable *t*. Se obtiene una

puntuación de sospecha global para cada demanda

Sea *W* (0) = 1,1,...,1 ', la notación del primer vector transpuesto.
Luego el vector de la suma global de las puntuaciones de sospecha de
fraude obtenidas para cada demanda

denotada en la matriz es: *S*(0) = *FW* (0) . Ahora, se tiene una

medida de consistencia de la variable indicadora *t* con las
puntuaciones

globales de sospecha de fraude para las demandas.

A través del Teorema 1 se garantiza que el valor de W converge y
la fijación del peso de la variable ˆ (∞) es la primera componente
principal de

*F*'*F* .

Teorema 1: *Las* *secuencias* *de* *los* *pesos* *de* *las*
*variables* *predictoras* *W* (*n*)      *y* *la* *sumatoria* *global*
*de* *las*

*puntuaciones* *de* *sospecha* *de* *las* *demandas*
*S*(*n*)     *convergen.* *De* *modo*

*que,* *la* *fijación* *de* *peso* *de* *la* *variable* *predictora* ˆ
(∞) *es* *la* *primera* *componente* *principal* *de* *F*'*F* *,* *la*
*cual* *es* *una* *estimación* *consistente* *de*

*la* *primera* *componente* *principal* *W* (∞)       *del*
*E*(*F*'*F*))*,* *la* *t-ésima*

*componente* *principal* *se* *tiene* *explícitamente:*

*Wt*(∞) = *t*

(∝1 -*Utt* ) ∑*As* / (∝1 -*Uss* )2 *s* =1

TABLA IV

PONDERACIONES PRIDIT PARA LAS VARIABLES INDICADORAS DE FRAUDE

Matriz de componentesa

a\. 1 componentes extraídos

Elaboración: Heydi Roa López

La TABLA IV muestra que las variables indicadoras de fraude VEHUSO
y ACULPA llevan la mayor ponderación PRIDIT de 100 demandas
analizadas, seguidas de COBERT, ZONA1 y FRAQCIA, es decir
que éstas son las variables que tienen mayor pesos a la hora de
determinar un nivel de sospecha de fraude.

TABLA V

PUNTUACIÓN GLOBAL PARA UNA DEMANDA COMPLETA

Elaboración: Heydi Roa López

Los valores At de la TABLA V son son una medida del poder
discriminatorio de las t variables indicadoras de fraude para una
demanda entera.

CLASIFICACIÓN DE LAS DEMANDAS POR MEDIO DE
LAS PONDERACIONES PRIDIT

Con respecto a la clasificación, se consideran dos casos para la
proporción de demandas del grupo 1, θ conocido y θ desconocido. Cuando
θ es conocido, se ordenan las *N* demandas por medio de sus
puntuaciones unidimensionales *S* =∑*t*=1*Wt*(∞)*Xt* y luego se
clasifican las primeras *N*θ demandas en el nivel alto del grupo 1 de
sospecha de fraude.

Aquí *Xt* es la puntuación calculada de la demanda obtenida para la
variable *t*,

*Xt* =∑*i*=1 *Bti* *I* *categoríai* *dada*\] donde *IA* es el
indicador del

conjunto *A*.

Si θ es desconocido (como es este caso), se separa los dos grupos de
acuerdo a las puntuaciones globales positivas o negativas y se
clasifican las demandas dentro del grupo de bajo nivel de sospecha de
fraude si la puntuación global del nivel de sospecha de fraude es
positivo, es decir en el grupo de las demandas no fraudulentas y las
de valor negativo dentro del grupo de demandas fraudulentas.

TABLA VI

CLASIFICACIÓN DE LAS DEMANDAS

Elaboración: Heydi Roa López

Como se demuestra en la TABLA VI, cada una de las demandas tiene una
ponderación o como se la ha llamado en este caso, Score, que permite
clasificar cada demanda dentro del grupo que corresponde. Un score

positivo significa que la demanda pertenece al Grupo 2, es decir es
una demanda no fraudulenta mientras que un score negativo significa
que la demanda debe ser discriminada al grupo 1, que es el grupo de
las demandas con cierto grado de fraude.

CONCLUSIONES

1. La utilización de la técnica PRIDIT en la detección de fraudes
dentro del campo de seguros de vehículos, es mucho más eficiente que
las técnicas estadísticas tradicionales cuando dentro de las variables
involucradas existen variables con respuestas del tipo categóricas,
puesto que la técnica PRIDIT transforma el conjunto de respuestas
categóricas en un conjunto de valores numéricos dentro de un intervalo
\[-1,1\], lo cual refleja la relativa anormalidad de una respuesta en
particular.

2. La técnica PRIDIT provee además una medida que permite
determinar qué variables son más consistentes, dando ponderaciones más
altas a las variables indicadoras de fraude. En esta investigación las
variables con mayor ponderación son: ACULPA, VEHUSO, COBERT, ZONA1,
FRAQCIA. Estas variables son las que indican mayormente fraude.

3. Otra de las ventajas de la utilización de la metodología PRIDIT
que se

comprobó en esta investigación, es que provee una medida del poder
discriminatorio de las variables indicadoras de fraude. Las variables
con mayor poder discriminatorio en esta investigación fueron: ACCESOR,
ACULPA, ZONA1, VEHUSO, COBERT, FRAQCIA.

4. La medida cuantitativa del poder discriminatorio que resulta de
la técnica PRIDIT provee además la capacidad de determinar
correlaciones con otras medidas cuantitativas tales como: edad del
conductor, número de accidentes anteriores del asegurado, número de
años que el asegurado tiene licencia, etcétera. Este procedimiento
puede dejarse para un estudio posterior puesto que no es el objetivo
de la actual investigación. Además que no se cuenta con datos reales
que permitan determinar la verdadera correlación entre las variables.

REFERENCIAS

1 ROA L. HEYDI, “Modelo de Detección de Fraudes en los
Seguros de Vehículos utilizando Componentes Principales y Análisis
RIDIT” (Tesis, Instituto de Ciencias Matemáticas, Escuela Superior
Politécnica del Litoral, 2004)

2 FREUN J, WALPOLE R. <u>Estadística</u>
<u>Matemática con aplicaciones</u>, (Prentice Hall Hispanoamericana
Cuarta Edición. México, 1990)

3 JOHNSON, D, <u>(Métodos Multivariados</u> <u>aplicados al
análisis de datos</u>, (Internacional Thompson Editores, México DF,
México, 2000)

4 FERRAN A. <u>SPSS para Windows:</u> <u>Análisis
Estadístico</u>, McGraw-Hill, Madrid, España.,2001)

5 Tutorial paquete estadístico SPSS 10.0 para Windows versión en
español

6 The Journal of Risk and Insurance, Fraud
Classification Using Principal Component Analysis of RIDIT’s, Vol.69,
No. 3, 2002.

7 2004, http://www.superban.gov.ec/pages/segur os_privados.htm