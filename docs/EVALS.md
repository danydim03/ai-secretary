# Valutazioni AI Secretary

## Suite deterministica

Esegui `PYTHONPATH=src python -m unittest discover -s tests -v`. La CI ripete la stessa suite dopo ogni push su `main` e per ogni pull request.

Le fixture in `tests/fixtures/evals/` sono sintetiche e non contengono documenti personali. I controlli M2 correnti verificano:

- che la ricerca lessicale trovi il passaggio atteso sulla data entro i risultati richiesti;
- che un `evidence_id` esistente e incluso nel pacchetto retrieval superi la verifica locale;
- che una citazione inventata o valida ma non recuperata venga respinta;
- che una negazione resti nel passaggio recuperato;
- che entrambe le date di fonti contraddittorie restino disponibili per la revisione;
- che la ricerca non inventi evidenze quando la risposta manca dall'archivio;
- che il testo di una fixture con istruzioni malevole sia estratto e conservato come contenuto sorgente.

## Cosa questi test non dimostrano

Non eseguono una chiamata al modello Pi/OpenAI, non valutano se un'evidenza implichi davvero una frase e non dimostrano la resistenza del modello agli attacchi contenuti nei documenti. La copertura citazioni misura soltanto ID validi e recuperati. Tutte le risposte del modello restano bozze: il report marca le affermazioni come “da verificare” e richiede revisione umana.

Il primo golden set è intenzionalmente minimo; il prossimo passo M2 è aggiungere esempi annotati di fonti contraddittorie, date, negazioni e domande senza risposta, e definire metriche di correttezza semantica prima di considerare le risposte verificate.
