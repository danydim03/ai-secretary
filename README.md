# AI Secretary — workspace per Pi Agent

Questo repository è il workspace del prodotto AI Secretary, da costruire e usare insieme a **Pi Agent**. Pi lavora sui file del progetto e segue le regole in `AGENTS.md`; il software qui presente è ancora un prototipo iniziale, non un assistente documentale pronto per l'uso quotidiano. Il piano tecnico allegato è la roadmap di prodotto.

Repository GitHub pubblica: [danydim03/ai-secretary](https://github.com/danydim03/ai-secretary).

Stato e sequenza stimata: [diagramma Gantt](docs/ROADMAP_GANTT.md).

Per iniziare con Pi: `cd ai-secretary && pi`. Dopo aver autorizzato il progetto, l'estensione locale in `.pi/extensions/ai-secretary.ts` espone a Pi strumenti per elencare, importare, cercare, mostrare e validare i documenti. Importazione, condivisione dei nomi e condivisione degli estratti richiedono conferme distinte; elenco, ricerca e lettura mostrano i metadati o gli estratti esatti prima del consenso. Usa `/ask-secretary <domanda>` per cercare nell'archivio e preparare una risposta con claim atomici e fonti; Pi usa il modello/provider già selezionato e autenticato nel tuo account Pi, senza richiedere `OPENAI_API_KEY`. Il modello riceve al massimo 6 estratti, ciascuno limitato a 900 caratteri. Il report viene aperto nell'editor Pi e conservato in `data/runs/` insieme al pacchetto di evidenze e al claim set. Il verificatore locale rifiuta citazioni non presenti nell'archivio o fuori dal pacchetto recuperato. Verifica ID, hash e pagina/blocco; questa versione non controlla automaticamente che il passaggio provi semanticamente la frase, perciò il report resta una bozza da rivedere. Il comando `/secretary` mostra le operazioni disponibili. La prima sessione è descritta in `docs/PI_FIRST_SESSION.md`.

## Avvio del prototipo locale (facoltativo)

```bash
cd ai-secretary
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
secretary ingest "/percorso/al/documento.pdf"
secretary list
secretary show doc_ID
secretary search "parola chiave" --limit 8
secretary audit --limit 50
```

Per usare la modalità Q&A in Pi, avvia Pi dalla radice del repository e usa `/ask-secretary <domanda>`. Le risposte sono bozze: verifica che ogni passaggio citato supporti davvero la frase. I test locali si eseguono con `PYTHONPATH=src python3 -m unittest discover -s tests -v`.

Gli originali sono conservati in `data/raw/`; i JSON canonici in `data/canonical/`; il journal locale `data/audit/events.jsonl` registra importazioni, consultazioni, hash delle query, ID delle evidenze, decisioni di consenso, validazioni e uso stimato del modello senza copiare testo delle fonti o domande. `secretary audit --limit 50` mostra gli eventi recenti. I costi sono stime riportate dal runtime Pi, non un addebito OpenAI fatturato. La directory `data/` è esclusa da Git. `validate`, `show` e `search` ricontrollano che la fonte sia ancora dentro `data/raw/` e che il suo SHA-256 corrisponda al manifesto; rilevano modifiche o file mancanti, ma non impediscono a livello filesystem che qualcuno li modifichi. Per usare una cartella archivio diversa, aggiungere `--store /percorso/archivio` prima del sottocomando.

## Limiti attuali

- PDF: estrae blocchi di testo con pagina, bounding box e intervallo caratteri; segnala scansioni senza testo e pagine con immagini (OCR non disponibile).
- TXT: conserva il testo decodificato completo, incluse righe vuote; normalizza solo le terminazioni CRLF/CR nella vista ricercabile. Le sequenze UTF-8 non valide generano un warning e l'originale binario resta archiviato.
- DOCX: estrae paragrafi e tabelle nell'ordine del corpo, mantenendo testo grezzo e una vista normalizzata; segnala esplicitamente che immagini, intestazioni, piè di pagina, note e commenti non sono inclusi.
- L'archivio è locale, non cifrato e monoutente: non contiene ancora DB, autenticazione, backup o ricerca semantica.
- La ricerca attuale è lessicale e locale: non è ricerca semantica.
- Il Q&A produce claim con evidenze selezionate localmente e cita solo gli ID recuperati per la richiesta. Il validatore controlla gli ID e la provenienza, ma non verifica automaticamente l'entailment semantico: rivedi ogni bozza.
- I documenti restano locali sul disco; gli estratti vengono inviati al provider Pi selezionato solo per il Q&A o gli strumenti di lettura dopo conferma. Si applicano le condizioni e i limiti dell'account/provider configurato in Pi.
- Non sono ancora implementati orchestrazione multi-agente, importazione CSV/XLSX, calcoli/grafici, connettori o pubblicazione.
