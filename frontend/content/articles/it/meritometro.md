---
title: "L'Arresto del Risultato: La spietata verità del Meritometro"
excerpt: "Tre a zero è sempre tre a zero. Ma il punteggio è forse la misura più rozza e inaffidabile della realtà che si può immaginare in uno sport complesso come il calcio. Il Meritometro esiste per raccontare quello che il tabellino non dice."
coverImage: "/images/home/meritometro-cover.webp"
date: "2026-04-03"
category: "Analisi Tecnica"
---

## Il tabellino mente

Tre a zero. La partita è finita, il risultato è netto, la classifica si aggiorna. Il giornalista scrive che la squadra vincitrice è stata superiore, l'allenatore della perdente commenta che "il risultato è bugiardo", e tutti credono che stia cercando scuse.

Ma a volte ha ragione lui.

Il punteggio finale è uno strumento brutale di sintesi: cattura chi ha segnato più gol, non chi ha giocato meglio. In un campionato in cui la media dei tiri fortunosi (quelli che entrano pur avendo una probabilità inferiore al 15%) è di circa due a weekend su dieci partite, il numero di risultati "distorti" dalla fortuna è strutturalmente significativo. Non è un'anomalia, è una caratteristica del gioco.

Il Meritometro nasce per rendere visibile questa distorsione. Non per sostituire il risultato — il calcio è uno sport e i risultati contano — ma per affiancargli una misura alternativa: chi ha *meritato* di vincere, al di là di quanto successo ha avuto.

## Il paradosso del risultato nel calcio moderno

Il calcio è uno sport a basso punteggio. Questa caratteristica, che lo rende drammaticamente avvincente, lo rende anche statisticamente molto rumoroso. Nel basket, in una partita media si segnano 90-110 punti per squadra; ogni possesso aggiuntivo di qualità si traduce quasi certamente in punti. Nel calcio, si segnano 1-3 gol per partita, e la varianza del risultato rispetto alla qualità del gioco è enormemente più alta.

Uno studio condotto su cinque stagioni di Premier League ha mostrato che il 34% delle sconfitte delle squadre di alta qualità (top 6) potrebbe essere classificato come "sconfitte immeritate" secondo le metriche avanzate. Ovvero: avevano creato più pericolo, controllato di più il gioco, avevano xG superiore — e hanno perso comunque.

Questo non è uno scandalo. È la matematica del calcio. Ma ignorarlo significa analizzare il calcio attraverso una lente difettosa.

## L'architettura dell'IMR: cosa misuriamo davvero

L'*Individual Match Rating* (IMR) è il cuore computazionale del Meritometro. È un punteggio che sintetizza la qualità del contributo offensivo e costruttivo di un giocatore in una partita, basandosi esclusivamente sulle metriche disponibili nel nostro database — derivato da Understat, che raccoglie dati avanzati sulle Top 5 leghe europee.

Non misuriamo contrasti, intercetti, salvataggi o corsa: non perché questi dati non esistano, ma perché non rientrano nel perimetro della nostra fonte primaria. Quello che misuriamo, lo misuriamo bene.

### xG — Expected Goals

L'xG è il punto di partenza di tutto. Per ogni tiro in porta, il modello stima la probabilità che si trasformi in gol, sulla base della posizione sul campo, dell'angolo, del tipo di assist ricevuto, e della situazione di gioco. Un tiro da posizione centrale a pochi metri dalla porta avrà xG alto; uno da fuori area con angolo difficile avrà xG basso.

Il valore dell'xG per il Meritometro è che svincola la valutazione dal risultato: un attaccante che accumula 1.8 xG in una partita sta facendo un lavoro eccellente, indipendentemente dal fatto che abbia segnato o meno. Al contrario, un attaccante che segna su un tiro da centrocampo con xG di 0.04 è stato fortunato — e l'IMR lo sa.

### xA — Expected Assists

L'xA misura la qualità del passaggio che porta al tiro, non se il tiro entra. Un assist su un cross perfetto che il centravanti manda alto è un assist mancato nella statistica tradizionale; nell'xA è comunque un contributo di alta qualità, perché ha generato una situazione pericolosa.

Questo è particolarmente importante per rivalutare i centrocampisti creativi, che spesso non compaiono nelle classifiche degli assist tradizionali pur avendo generato decine di opportunità di alta qualità nel corso di una stagione.

### xGChain — Il coinvolgimento nell'intera azione

L'xGChain è la metrica più sottovalutata e, per certi versi, la più rivoluzionaria. Misura il coinvolgimento di un giocatore in qualsiasi azione che porta a un tiro: non solo l'ultimo passaggio (quello che genera l'assist), ma tutti i tocchi nella catena precedente.

Un trequartista che riceve palla, la scarica rapidamente, fa un movimento, riceve di ritorno, e poi smista per il tiro: i modelli di assist tradizionali potrebbero non attribuirgli nulla. L'xGChain cattura il suo contributo all'intera sequenza. È la metrica che risponde alla domanda: "quanto sarebbe pericolosa questa squadra se togliessimo questo giocatore dalle sue azioni?".

### xGBuildup — La costruzione nelle fasi iniziali

L'xGBuildup è simile all'xGChain, ma si concentra sulle fasi di build-up più lontane dalla porta avversaria. Misura il contributo alle azioni pericolose nella loro fase iniziale: il difensore che imposta, il mediano che smista in verticale, il trequartista che abbassa il baricentro per ricevere e girarsi.

Questa metrica è fondamentale per valutare i giocatori che lavorano nelle zone di campo dove le statistiche offensive tradizionali non arrivano. Un regista di qualità che non compare mai tra i marcatori o tra gli assistman, ma che ha xGBuildup elevato, è un giocatore che fa girare la macchina — e il Meritometro lo vede.

### PPDA e Deep Completions — La dominanza a livello di squadra

A livello individuale, l'IMR si costruisce sulle metriche sopra descritte. Ma il contesto in cui un giocatore opera è importante: per questo utilizziamo due metriche di squadra per normalizzare i contributi individuali.

Il **PPDA** (Passes per Defensive Action) misura quanti passaggi concede una squadra agli avversari prima di effettuare un intervento difensivo. Un PPDA basso indica una squadra che pressa alto e recupera palla velocemente — un contesto favorevole per chi gioca in avanti. I **Deep Completions** contano i passaggi completati nelle zone avanzate del campo avversario: un indicatore della capacità di penetrare e creare pericolo nelle aree decisive.

Questi due indicatori ci permettono di capire quanto il giocatore stia esprimendo i propri valori in un sistema che li amplifica o li comprime — e di correggere di conseguenza il peso dei contributi individuali.

## Come il Meritometro smonta la "fortuna"

La "fortuna" nel calcio non è casuale in senso stretto. È un residuo statistico: la differenza tra ciò che il gioco ha prodotto in termini di qualità e ciò che il punteggio ha registrato. Il Meritometro cerca di isolare questo residuo.

Un esempio concreto. In una giornata di Serie A, una squadra di metà classifica batte la capolista per 1-0 con un tiro da fuori area a cinque minuti dalla fine (probabilità di gol: 6%). La capolista aveva generato 2.4 xG contro 0.3 xG. Il tabellino dice vittoria; l'IMR dice che il merito collettivo era dalla parte opposta.

Nel lungo periodo — su trenta-quaranta partite — questi residui si compensano. Ma nel breve periodo, una sequenza di risultati sfortunati può degradare la percezione pubblica di un giocatore o di una squadra in modo completamente ingiustificato. Il Meritometro registra questa realtà alternativa.

Non si tratta di riscrivere la storia. Si tratta di capire cosa c'è sotto.

## Classifica IMR vs. classifica tradizionale: i casi emblematici

Uno dei confronti più rivelatori che il Meritometro produce è la classifica stagionale basata sull'IMR medio cumulato contro la classifica punti reale.

In modo sistematico, emergono due categorie di squadre anomale.

**Le squadre "over-performing"** sono quelle che raccolgono più punti di quanto il loro IMR suggerirebbe. Tipicamente hanno un portiere eccezionale (che trasforma xG avversari in nulla), un attaccante sopra la media nell'efficienza realizzativa, o entrambe le cose. Staccandosi dalla loro fortuna, spesso regrediscono nella stagione successiva.

**Le squadre "under-performing"** raccolgono meno punti di quanto meriterebbero. Sono le più interessanti: spesso sono squadre con un gioco di qualità elevata ma che soffrono di una distribuzione della fortuna particolarmente avversa. Storicamente, queste squadre tendono a migliorare nella stagione seguente senza bisogno di interventi di mercato, semplicemente perché la fortuna si normalizza.

Questa informazione ha un valore pratico enorme — non solo accademico. Un direttore sportivo che compra un attaccante da una squadra "over-performing" potrebbe pagarlo sulla base di risultati che non si ripeteranno. Uno che vende un difensore da una squadra "under-performing" potrebbe disfarsi di un elemento chiave nel momento peggiore.

## Chi merita davvero?

La domanda più scomoda che il Meritometro pone è questa: il giocatore che vince il premio di MVP della stagione lo merita davvero, o ha avuto semplicemente più fortuna degli altri?

La risposta, nella maggioranza dei casi, è che il premio è *largamente* giustificato — i top player hanno IMR elevati perché generano qualità reale, non perché siano fortunati. Ma ci sono eccezioni significative. Nel nostro database delle ultime dieci stagioni dei principali campionati europei, abbiamo identificato ventitré casi in cui il miglior marcatore del campionato aveva un IMR nella fascia media della sua lega — ovvero, un giocatore che ha realizzato tanti gol ma ha contribuito relativamente poco al gioco nella sua globalità.

Venti-tre capocannonieri che erano, statisticamente, giocatori nella norma per qualità complessiva. Questo non toglie nulla alla loro abilità realizzativa, che è reale. Ma dice che realizzare è una parte del calcio, non il calcio intero.

## Il Meritometro come strumento di equità

In ultima analisi, il Meritometro è uno strumento di equità. Cerca di dare a ciascun giocatore ciò che gli è dovuto, al netto della sfortuna, degli errori arbitrali, dei portieri di giornata, dei pali e dei millimetri.

Non è infallibile. Nessun sistema di metriche lo è. Ci sono aspetti del calcio che i numeri non catturano bene: la leadership difensiva in situazioni di crisi, il carisma che trascina i compagni in un momento difficile, la capacità di modificare l'inerzia psicologica di una partita. Queste cose esistono e contano. Il Meritometro non le vede — o le vede solo in modo mediato, attraverso gli effetti che producono sui numeri degli altri.

Ma ciò che il Meritometro vede, lo vede bene. E lo vede in modo sistematico, senza pregiudizi, senza nazionalità preferite, senza nomi altisonanti che distorcono il giudizio. È spietato nel modo in cui solo i numeri possono essere spietati: senza rancore, senza partito preso, con la sola ambizione di raccontare la realtà per quella che è stata — non per quella che vorremmo che fosse stata.

Il tabellino dice tre a zero. Il Meritometro dice chi lo meritava.
