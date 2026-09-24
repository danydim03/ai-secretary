# Prima sessione di lavoro con Pi

Apri un terminale nella cartella `ai-secretary` ed esegui `pi`. Pi caricherà `AGENTS.md` come istruzioni del progetto. Incolla questo prompt come prima richiesta:

```text
Leggi AGENTS.md, README.md e il piano tecnico in ../../../ai-secretary-implementation-plan.md. Voglio costruire l'AI Secretary usando Pi Agent come ambiente in cui lavoriamo insieme sul prodotto. Prima di modificare codice, riassumi lo stato attuale e proponi una slice M1 concreta: ingestione locale PDF/TXT/DOCX, copia immutabile, hash SHA-256, Canonical Document con riferimenti e warning, validazione schema. Mantieni tutto locale e non configurare servizi esterni o API a pagamento. Poi implementa la slice concordata, spiegami come usarla da Pi e quali limiti restano. Se una scelta richiede una dipendenza o un account esterno, fermati su quella scelta e continua il lavoro indipendente.
```

Pi è il cockpit da cui sviluppi e controlli il progetto; non è il server che deve ricevere i tuoi documenti in background. Avviandolo dalla cartella del repository e autorizzando il progetto, l'estensione locale `.pi/extensions/ai-secretary.ts` rende disponibili gli strumenti `secretary_*` per elencare, importare, cercare evidenze lessicali, mostrare e validare i documenti. Ricerca e visualizzazione chiedono conferma interattiva prima di passare estratti al modello; senza interfaccia interattiva si bloccano. Puoi digitare `/secretary` per un promemoria. L'importazione crea copie e artefatti solo nell'archivio locale `data/`.

Questo è il primo ponte Pi→prodotto, non ancora un gruppo di agenti autonomi. La ricerca restituisce evidenze con riferimenti alla fonte, ma non genera risposte AI. In seguito Pi potrà avviare e monitorare job dell'orchestratore locale tramite strumenti dedicati; il runtime del prodotto resterà separato e non riceverà permessi esterni senza una decisione esplicita.

## Controllo accesso al modello

Pi 0.87.1 risulta installato nel sistema. Per verificare se il provider configurato è pronto, esegui `pi auth check --provider google --no-refresh` (non usare `--credentials`, che stampa il segreto). Se usi un provider diverso, sostituisci `google` con il suo nome. Se il controllo non è pronto, scegli/configura un provider con `pi` o la procedura di autenticazione Pi; non incollare chiavi in chat o nel repository.
