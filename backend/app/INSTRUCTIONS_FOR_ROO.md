# LEGGI DI SVILUPPO PER ROO CODE
1. **Dati Reali:** È vietato l'uso di dati finti (mock/seed). Le metriche xG, xGA, xPTS devono essere estratte dai dati reali sincronizzati dallo scraper Understat.
2. **Logica Understat:** La classifica deve calcolare i Delta (es. xG - Goals) per ogni squadra. Se i valori sono 0.0, la query è sbagliata.
3. **UI Nerd Zone:** La tabella deve replicare esattamente le colonne di Understat (M, W, D, L, G, GA, PTS, xG, xGA, xPTS) con i delta colorati ad apice.
4. **Verifica:** Prima di considerare il task finito, esegui un `curl` e assicurati che `xg` non sia `0.0`.