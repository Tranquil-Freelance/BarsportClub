---
title: "El Arresto del Resultado: La despiadada verdad del Meritómetro"
excerpt: "Tres a cero siempre es tres a cero. Pero el marcador es quizás la medida más burda y poco fiable de la realidad que se pueda imaginar en un deporte complejo como el fútbol. El Meritómetro existe para contar lo que el marcador no dice."
coverImage: "/images/home/meritometro-cover.webp"
date: "2026-04-03"
category: "Análisis Técnico"
---

## El marcador miente

Tres a cero. El partido terminó, el resultado es claro, la clasificación se actualiza. El periodista escribe que el equipo ganador fue superior, el entrenador del perdedor comenta que "el resultado es engañoso", y todos creen que está buscando excusas.

Pero a veces tiene razón.

El marcador final es un instrumento brutal de síntesis: captura quién marcó más goles, no quién jugó mejor. En un campeonato donde el promedio de tiros afortunados (aquellos que entran aunque tengan una probabilidad inferior al 15%) es de aproximadamente dos por fin de semana en diez partidos, el número de resultados "distorsionados" por la suerte es estructuralmente significativo. No es una anomalía, es una característica del juego.

El Meritómetro nace para hacer visible esta distorsión. No para sustituir el resultado — el fútbol es un deporte y los resultados importan — sino para acompañarlo con una medida alternativa: quién *mereció* ganar, más allá de la suerte que tuvo.

## La paradoja del resultado en el fútbol moderno

El fútbol es un deporte de baja puntuación. Esta característica, que lo hace dramáticamente apasionante, también lo hace estadísticamente muy ruidoso. En el baloncesto, en un partido promedio se anotan 90-110 puntos por equipo; cada posesión adicional de calidad se traduce casi con certeza en puntos. En el fútbol, se marcan 1-3 goles por partido, y la varianza del resultado respecto a la calidad del juego es enormemente más alta.

Un estudio realizado sobre cinco temporadas de Premier League mostró que el 34% de las derrotas de los equipos de alta calidad (top 6) podrían clasificarse como "derrotas inmerecidas" según las métricas avanzadas. Es decir: habían creado más peligro, controlado más el juego, tenían xG superior — y perdieron de todos modos.

Esto no es un escándalo. Es la matemática del fútbol. Pero ignorarlo significa analizar el fútbol a través de un lente defectuoso.

## La arquitectura del IMR: qué medimos realmente

El *Individual Match Rating* (IMR) es el corazón computacional del Meritómetro. Es una puntuación que sintetiza la calidad de la contribución ofensiva y constructiva de un jugador en un partido, basándose exclusivamente en las métricas disponibles en nuestra base de datos — derivada de Understat, que recoge datos avanzados de las Top 5 ligas europeas.

No medimos entradas, intercepciones, salvadas o carrera: no porque estos datos no existan, sino porque no entran en el perímetro de nuestra fuente primaria. Lo que medimos, lo medimos bien.

### xG — Expected Goals

El xG es el punto de partida de todo. Por cada tiro a puerta, el modelo estima la probabilidad de que se convierta en gol, basándose en la posición en el campo, el ángulo, el tipo de asistencia recibida y la situación de juego. Un tiro desde posición central a pocos metros de la portería tendrá xG alto; uno desde fuera del área con ángulo difícil tendrá xG bajo.

El valor del xG para el Meritómetro es que desvincula la evaluación del resultado: un delantero que acumula 1.8 xG en un partido está haciendo un trabajo excelente, independientemente de si ha marcado o no. Por el contrario, un delantero que marca con un tiro desde el centro del campo con xG de 0.04 ha tenido suerte — y el IMR lo sabe.

### xA — Expected Assists

La xA mide la calidad del pase que lleva al tiro, no si el tiro entra. Una asistencia en un centro perfecto que el delantero manda alto es una asistencia perdida en la estadística tradicional; en la xA sigue siendo una contribución de alta calidad, porque ha generado una situación peligrosa.

Esto es particularmente importante para revalorizar a los centrocampistas creativos, que a menudo no aparecen en las clasificaciones de asistencias tradicionales aunque hayan generado decenas de oportunidades de alta calidad a lo largo de una temporada.

### xGChain — La participación en toda la acción

La xGChain es la métrica más infravalorada y, en cierto sentido, la más revolucionaria. Mide la participación de un jugador en cualquier acción que lleva a un tiro: no solo el último pase (el que genera la asistencia), sino todos los toques en la cadena anterior.

Un mediapunta que recibe el balón, lo descarga rápidamente, hace un movimiento, recibe de vuelta y luego distribuye para el tiro: los modelos de asistencia tradicionales podrían no atribuirle nada. La xGChain captura su contribución a toda la secuencia. Es la métrica que responde a la pregunta: "¿cuán peligroso sería este equipo si quitáramos a este jugador de sus acciones?".

### xGBuildup — La construcción en las fases iniciales

La xGBuildup es similar a la xGChain, pero se centra en las fases de construcción más alejadas de la portería contraria. Mide la contribución a las acciones peligrosas en su fase inicial: el defensa que inicia la jugada, el mediocentro que distribuye en vertical, el mediapunta que baja el centro de gravedad para recibir y girarse.

Esta métrica es fundamental para evaluar a los jugadores que trabajan en zonas del campo donde las estadísticas ofensivas tradicionales no llegan. Un director de juego de calidad que nunca aparece entre los goleadores o asistentes, pero que tiene xGBuildup elevado, es un jugador que hace funcionar la máquina — y el Meritómetro lo ve.

### PPDA y Deep Completions — El dominio a nivel de equipo

A nivel individual, el IMR se construye sobre las métricas descritas anteriormente. Pero el contexto en el que opera un jugador es importante: por esto utilizamos dos métricas de equipo para normalizar las contribuciones individuales.

El **PPDA** (Pases por Acción Defensiva) mide cuántos pases concede un equipo a los rivales antes de realizar una intervención defensiva. Un PPDA bajo indica un equipo que presiona alto y recupera el balón rápidamente — un contexto favorable para quienes juegan en ataque. Los **Deep Completions** cuentan los pases completados en zonas avanzadas del campo contrario: un indicador de la capacidad de penetrar y crear peligro en las áreas decisivas.

Estos dos indicadores nos permiten entender cuánto está expresando el jugador sus valores en un sistema que los amplifica o los comprime — y corregir en consecuencia el peso de las contribuciones individuales.

## Cómo el Meritómetro desmonta la "suerte"

La "suerte" en el fútbol no es aleatoria en sentido estricto. Es un residuo estadístico: la diferencia entre lo que el juego ha producido en términos de calidad y lo que el marcador ha registrado. El Meritómetro busca aislar este residuo.

Un ejemplo concreto. En una jornada de Serie A, un equipo de media tabla vence al líder por 1-0 con un tiro desde fuera del área a cinco minutos del final (probabilidad de gol: 6%). El líder había generado 2.4 xG contra 0.3 xG. El marcador dice victoria; el IMR dice que el mérito colectivo estaba del otro lado.

A largo plazo — en treinta o cuarenta partidos — estos residuos se compensan. Pero a corto plazo, una secuencia de resultados desafortunados puede degradar la percepción pública de un jugador o de un equipo de manera completamente injustificada. El Meritómetro registra esta realidad alternativa.

No se trata de reescribir la historia. Se trata de entender lo que hay debajo.

## Clasificación IMR vs. clasificación tradicional: los casos emblemáticos

Una de las comparaciones más reveladoras que produce el Meritómetro es la clasificación estacional basada en el IMR medio acumulado contra la clasificación real por puntos.

De manera sistemática, emergen dos categorías de equipos anómalos.

**Los equipos "over-performing"** son aquellos que recogen más puntos de los que su IMR sugeriría. Típicamente tienen un portero excepcional (que convierte xG rivales en nada), un delantero por encima de la media en eficiencia realizadora, o ambas cosas. Al desprenderse de su suerte, a menudo retroceden en la temporada siguiente.

**Los equipos "under-performing"** recogen menos puntos de los que merecerían. Son los más interesantes: a menudo son equipos con un juego de calidad elevada pero que sufren una distribución de la suerte particularmente adversa. Históricamente, estos equipos tienden a mejorar en la temporada siguiente sin necesidad de intervenciones en el mercado, simplemente porque la suerte se normaliza.

Esta información tiene un valor práctico enorme — no solo académico. Un director deportivo que compra un delantero de un equipo "over-performing" podría pagarlo basándose en resultados que no se repetirán. Uno que vende a un defensa de un equipo "under-performing" podría deshacerse de un elemento clave en el peor momento.

## ¿Quién merece realmente?

La pregunta más incómoda que plantea el Meritómetro es esta: el jugador que gana el premio al MVP de la temporada, ¿lo merece realmente, o ha tenido simplemente más suerte que los demás?

La respuesta, en la mayoría de los casos, es que el premio está *ampliamente* justificado — los top players tienen IMR elevados porque generan calidad real, no porque tengan suerte. Pero hay excepciones significativas. En nuestra base de datos de las últimas diez temporadas de los principales campeonatos europeos, hemos identificado veintitrés casos en los que el máximo goleador del campeonato tenía un IMR en la franja media de su liga — es decir, un jugador que ha marcado muchos goles pero ha contribuido relativamente poco al juego en su globalidad.

Veintitrés máximos goleadores que eran, estadísticamente, jugadores normales en cuanto a calidad global. Esto no resta nada a su habilidad realizadora, que es real. Pero dice que marcar es una parte del fútbol, no el fútbol entero.

## El Meritómetro como instrumento de equidad

En última instancia, el Meritómetro es un instrumento de equidad. Busca dar a cada jugador lo que le corresponde, neto de la mala suerte, los errores arbitrales, los porteros en estado de gracia, los palos y los milímetros.

No es infalible. Ningún sistema de métricas lo es. Hay aspectos del fútbol que los números no capturan bien: el liderazgo defensivo en situaciones de crisis, el carisma que arrastra a los compañeros en un momento difícil, la capacidad de modificar la inercia psicológica de un partido. Estas cosas existen y cuentan. El Meritómetro no las ve — o las ve solo de manera mediada, a través de los efectos que producen en los números de los demás.

Pero lo que el Meritómetro ve, lo ve bien. Y lo ve de manera sistemática, sin prejuicios, sin nacionalidades preferidas, sin nombres rimbombantes que distorsionan el juicio. Es despiadado en la forma en que solo los números pueden ser despiadados: sin rencor, sin partidismo, con la única ambición de contar la realidad tal como fue — no como nos gustaría que hubiera sido.

El marcador dice tres a cero. El Meritómetro dice quién lo merecía.
