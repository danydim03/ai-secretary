# AI Secretary — workspace per Pi Agent

Questo repository è il workspace del prodotto AI Secretary, da costruire e usare insieme a **Pi Agent**. Pi lavora sui file del progetto e segue le regole in `AGENTS.md`; il software qui presente è ancora un prototipo iniziale, non un assistente documentale pronto per l'uso quotidiano. Il piano tecnico allegato è la roadmap di prodotto.

Repository GitHub pubblica: [danydim03/ai-secretary](https://github.com/danydim03/ai-secretary).

Stato e sequenza stimata: [diagramma Gantt](docs/ROADMAP_GANTT.md).

Per iniziare con Pi: `cd ai-secretary && pi`. Dopo aver autorizzato il progetto, l'estensione locale in `.pi/extensions/ai-secretary.ts` espone a Pi strumenti per elencare, importare, cercare, mostrare e validare i documenti. Ricerca e visualizzazione richiedono una conferma esplicita prima che estratti siano passati al modello. Il comando `/secretary` mostra le operazioni disponibili. La prima sessione è descritta in `docs/PI_FIRST_SESSION.md`. Pi Agent è il cockpit di sviluppo e controllo; gli agenti del prodotto verranno orchestrati dal runtime locale del progetto, non avviati automaticamente all'apertura di Pi. Il prototipo CLI resta utilizzabile separatamente.

## Avvio del prototipo locale (facoltativo)

```bash
cd ai-secretary
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
secretary ingest "/percorso/al/documento.pdf"
secretary list
secretary show doc_ID
secretary search "parola chiave" --limit 8
```

Gli originali sono conservati in `data/raw/`; i JSON canonici in `data/canonical/`. La directory `data/` è esclusa da Git. `validate`, `show` e `search` ricontrollano che la fonte sia ancora dentro `data/raw/` e che il suo SHA-256 corrisponda al manifesto; rilevano modifiche o file mancanti, ma non impediscono a livello filesystem che qualcuno li modifichi. Per usare una cartella archivio diversa, aggiungere `--store /percorso/archivio` prima del sottocomando.

## Limiti attuali

- PDF: estrae blocchi di testo con pagina, bounding box e intervallo caratteri; segnala scansioni senza testo e pagine con immagini (OCR non disponibile).
- TXT: conserva il testo decodificato completo, incluse righe vuote; normalizza solo le terminazioni CRLF/CR nella vista ricercabile. Le sequenze UTF-8 non valide generano un warning e l'originale binario resta archiviato.
- DOCX: estrae paragrafi e tabelle nell'ordine del corpo, mantenendo testo grezzo e una vista normalizzata; segnala esplicitamente che immagini, intestazioni, piè di pagina, note e commenti non sono inclusi.
- L'archivio è locale, non cifrato e monoutente: non contiene ancora DB, autenticazione, backup o ricerca semantica.
- La ricerca attuale è lessicale e locale: non è ricerca semantica e non produce risposte AI.
- Non sono ancora implementati claim con evidenze, orchestrazione di agenti o pubblicazione.

Per attivare successivamente una funzione che chiama OpenAI, configurare `OPENAI_API_KEY` nell'ambiente locale/secret manager; non inserire segreti nei file del progetto.
