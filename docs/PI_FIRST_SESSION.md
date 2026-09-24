# Prima sessione di lavoro con Pi

Apri un terminale nella cartella `ai-secretary` ed esegui `pi`. Pi caricherà `AGENTS.md` come istruzioni del progetto. Incolla questo prompt come prima richiesta:

```text
Leggi AGENTS.md, README.md e il piano tecnico in ../../../ai-secretary-implementation-plan.md. Continua la milestone aperta senza chiedere una chiave API: usa il provider già autenticato in Pi per le richieste AI. Mantieni documenti, archivio, claim ed artefatti in locale. Prima di inviare estratti mostra i passaggi esatti e chiedi il consenso; non collegare altri servizi esterni né pubblicare senza una richiesta esplicita. Aggiungi test mirati, verifica il flusso e aggiorna la roadmap con fatti e limiti osservati.
```

Pi è il cockpit da cui sviluppi e controlli il progetto; non è il server che deve ricevere i tuoi documenti in background. Avviandolo dalla cartella del repository e autorizzando il progetto, l'estensione locale `.pi/extensions/ai-secretary.ts` rende disponibili gli strumenti `secretary_*` per elencare, importare, cercare evidenze lessicali, mostrare e validare i documenti. Digitando `/ask-secretary <domanda>` Pi cerca localmente, mostra gli estratti esatti e chiede conferma prima di inviarli al modello già configurato in Pi, poi valida i riferimenti e prepara una bozza nell'editor e in `data/runs/`. Lo strumento di elenco mostra prima i nomi file; quello di lettura mostra i primi sei blocchi con un estratto massimo di 900 caratteri ciascuno. Non serve una chiave API separata nel repository: viene usato l'accesso del provider attualmente selezionato in Pi. Importazione, condivisione dei nomi file e condivisione del testo chiedono consensi distinti; in modalità senza UI si bloccano. Puoi digitare `/secretary` per un promemoria. Originali e artefatti restano nell'archivio locale `data/`.

Questo è un workflow Q&A single-agent, non ancora un gruppo di agenti autonomi. Il verificatore blocca ID assenti o non inclusi nei risultati della ricerca, ma non valuta se l'evidenza provi semanticamente la frase: controlla la bozza prima di usarla. In seguito Pi potrà avviare e monitorare job dell'orchestratore locale tramite strumenti dedicati; il runtime del prodotto resterà separato e non riceverà permessi esterni senza una decisione esplicita.

## Controllo accesso al modello

Pi 0.87.1 risulta installato nel sistema. Il provider OpenAI Codex configurato in questo ambiente è stato verificato come pronto. Per controllare un provider senza stampare credenziali, esegui `pi auth check --provider openai-codex --no-refresh`. Se il controllo non è pronto, scegli/configura l'accesso con Pi; non incollare chiavi in chat o nel repository. `OPENAI_API_KEY` serve solo a un'app che chiama direttamente l'API: questo workflow usa invece l'autenticazione del provider ospitata da Pi.
