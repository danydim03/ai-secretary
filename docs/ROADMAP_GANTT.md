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
    Fedeltà estrazione e riferimenti pagina/blocco              :active, m1extract, 2026-09-24, 7d
    Fixture PDF/DOCX/TXT, copertura e criteri di accettazione   :m1accept, after m1extract, 5d

    section M2 · Q&A e report citabili
    Retrieval ibrido, claim con evidenze, Writer e Verifier     :m2, 2026-10-06, 10d
    Evals e revisione umana del workflow                        :m2eval, after m2, 5d

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

- **Fatto:** scheletro Python e CLI; copia locale del file sorgente con SHA-256; Canonical Document JSON; validazione interna; ricerca lessicale con ID evidenza; estensione Pi con elenco/importazione/ricerca/visualizzazione/validazione. Ricerca e visualizzazione chiedono conferma prima di passare estratti al modello.
- **In corso:** M1, con estrazione PDF a blocchi e locatori, preservazione del testo grezzo TXT/DOCX, warning per contenuti non coperti e verifica dell'integrità della copia. Questi cambiamenti recenti non sono ancora stati verificati con la suite.
- **Da fare per chiudere M1:** fixture rappresentative, prove d'accettazione, copertura di estrazione e verifica end-to-end dell'estensione Pi.
- **Non iniziato:** M2–M5. Non ci sono ancora risposte AI citabili, OCR, retrieval vettoriale, workflow di calcolo/grafici o connettori di pubblicazione.

## Pubblicazione del codice su GitHub

La cartella non ha ancora metadati Git locali. La pubblicazione della repository `ai-secretary` è autorizzata come pubblica; la creazione remota e il push sono in attesa di un canale GitHub operativo in questa sessione. Prima del push va ricontrollato che nell'indice Git entrino solo file del progetto e che `.env`, `data/` e `.venv/` restino esclusi.
