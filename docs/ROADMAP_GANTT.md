# AI Secretary — stato e piano Gantt

Aggiornato al 24 settembre 2026. Il diagramma unisce lo stato verificato del repository alle durate indicative M1–M5 del piano tecnico. Le date future sono una stima sequenziale a partire da oggi, non una promessa di consegna; dipendenze, feedback e prove d'accettazione possono spostarle.

```mermaid
gantt
    title AI Secretary — roadmap indicativa
    dateFormat YYYY-MM-DD
    axisFormat %d %b

    section M1 · Fondazioni affidabili
    CLI locale, archivio originale, hash e Canonical Document :done, m1base, 2026-09-24, 1d
    Estensione Pi: importa, cerca, mostra, valida                :done, m1pi, 2026-09-24, 1d
    Estrazione fedele PDF/TXT/DOCX e import idempotente          :done, m1extract, 2026-09-24, 1d
    Fixture PDF/DOCX/TXT e criteri di estrazione                 :done, m1accept, 2026-09-24, 1d
    Journal audit locale e stima uso modello                     :done, m1audit, 2026-09-24, 1d
    Primo run CI su GitHub e revisione finale M1                 :done, m1ci, 2026-09-24, 1d

    section M2 · Q&A e report citabili
    Retrieval lessicale, Q&A Pi e citazioni verificate          :done, m2base, 2026-09-24, 1d
    Eval retrieval/evidence con fixture golden iniziali           :done, m2evalbase, 2026-09-24, 1d
    Verifica semantica dei claim ed evals LLM                    :active, m2, 2026-09-25, 10d
    Ricerca ibrida e misura copertura/correttezza citazioni     :m2eval, after m2, 5d

    section M3 · Dati, calcoli e grafici
    Ingestione CSV/XLSX e calcolo riproducibile                 :m3data, 2026-10-21, 10d
    Grafici, artefatti e controlli numerici                     :m3charts, after m3data, 5d

    section M4 · Pubblicazione controllata
    Gateway e primo connettore in modalità draft                :m4draft, 2026-11-05, 10d
    Approval grant, idempotenza, audit e rollback                :m4approval, after m4draft, 5d

    section M5 · Hardening continuo
    Auth, isolamento, budget, osservabilità, backup e resilienza :m5, 2026-11-20, 42d
```

## Stato al momento

- **M1 completata per la prima release locale:** PDF per blocchi con pagina/coordinate/intervallo; TXT grezzo; DOCX con ordine di paragrafi e tabelle; warning per contenuti non coperti; hash e reimportazione idempotente. Journal locale registra azioni, riferimenti e stime di token/costo Pi senza testo sorgente o query. 14 test locali verdi e workflow CI GitHub verde sul commit `dcd7dfe`.
- **M2 in corso:** `/ask-secretary <domanda>` usa il modello autenticato in Pi, dopo aver mostrato gli estratti precisi e ricevuto conferma. Il verificatore locale blocca ID inesistenti e riferimenti fuori dal pacchetto retrieval; claim e bozza vengono salvati localmente. La prova automatica controlla l'esistenza e la provenienza dell'evidenza, non l'entailment semantico.
- **Eval M2 iniziali:** due fixture sintetiche controllano il recupero della data attesa, i riferimenti citabili e il mantenimento di un tentativo di prompt injection come testo sorgente. Suite locale complessiva: 16 test verdi; i test non chiamano un modello esterno.
- **Da completare in M2:** eval live per qualità delle risposte, revisione semantica dei claim e test dell'interazione Pi end-to-end. Il report marca i claim come “da verificare”: la copertura cita ID esistenti e recuperati, ma non prova che le frasi siano supportate. La ricerca rimane lessicale (nessun embedding).
- **Non iniziato:** M3–M5. Restano CSV/XLSX, calcoli e grafici, connettori in modalità bozza, grant di approvazione, audit completo, backup e hardening.

## Pubblicazione del codice su GitHub

La repository pubblica [danydim03/ai-secretary](https://github.com/danydim03/ai-secretary) è stata creata e verificata nel browser. `main` segue la repository remota; `.env`, `data/` e `.venv/` restano esclusi. La CI GitHub è verde sul commit `dcd7dfe`; una nuova esecuzione è in corso dopo la correzione del testo Q&A.
