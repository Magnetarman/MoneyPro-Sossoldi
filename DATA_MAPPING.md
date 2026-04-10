# Mappatura Dati Dettagliata: [Money Pro](https://money.pro/it/android/) → [Sossoldi](https://github.com/RIP-Comm/sossoldi)

## 1. Analisi Strutturale dei File

### Sorgente (Money Pro Completo - `money_pro.csv`)
Il file esportato completo presenta differenze chiave rispetto alla copia analizzata in precedenza:
- **Formato e Separatore**: CSV con separatore **punto e virgola (`;`)**. Questo è fondamentale per il parsing corretto, in quanto la virgola è usata sia all'interno delle date (es. `10 mar 2018, 00:14:33`) sia nei decimali (es. `16,1 €`).
- **Encoding**: UTF-8 (mantiene i caratteri speciali come `€`, spazi non-breaking).
- **Header**: `Data;Somma;Conto;Importo ricevuto;Conto (a);Bilancio;Categoria;Descrizione;Tipo di transazione;Agente;`
  *(Nota: c'è un `;` vuoto alla fine dell'header che genera una colonna vuota extra)*

### Destinazione (Sossoldi - `sossoldi.csv`)
Il CSV di Sossoldi è invariato (multi-tabella, flat), le entità attese sono: `bankAccount`, `categoryTransaction`, `transaction`, `recurringTransaction`, `currency`.

---

## 2. Differenze e Nuovi Tipi di Transazione in Money Pro

L'analisi del file completo ha fatto emergere tre casistiche assenti o mascherate nel campione ridotto:

### A. Tipi speciali di transazione
Oltre a `Spesa`, `Entrata` e `Trasferimento`, esistono:
1.  **`Saldo iniziale`**: Rappresenta l'apertura del conto. 
    - **Soluzione per Sossoldi**: Può essere gestito aggregando i valori del `Saldo iniziale` per ogni conto e inserendoli nel campo `startingValue` del record `bankAccount` corrispondente. L'importo da inserire è il valore della colonna `Somma` associata. Un'alternativa più sporca è creare una transazione `IN` o `OUT` fittizia. La scelta preferibile è l'aggiornamento di `startingValue`.
2.  **`Modifica del saldo`**: Rappresenta una quadratura manuale dell'utente (es. ammanchi o eccedenze).
    - **Soluzione per Sossoldi**: Si mappa come normale transazione senza categoria (l'elenco vuoto è valido). 
    - Se l'importo è **positivo**, diventa `type: IN`.
    - Se l'importo è **negativo** (es. `-10 €`), diventa `type: OUT` prendendone il valore assoluto (`amount: 10`).

### B. Somme Negative Inaspettate
Sebbene le spese siano normate con stringhe positive ("16,1 €" diventa spesa grazie al campo `Spesa`), nelle transazioni di `Modifica del saldo` Money Pro inserisce esplicitamente il segno meno (es. `-10 €`).
- **Gestione**: Per Sossoldi, il campo `amount` deve essere SEMPRE un `float` positivo assoluto. Il segno algebrico è ricavato unicamente dal `type` (`IN`/`OUT`). Le stringhe "`-10 €`" vanno pulite scartando il meno e marcate come `OUT`.

### C. Anomalie di Formattazione nelle Categorie
Alcune categorie in Money Pro appaiono duplicate per disattenzione dell'utente o bug del tool sorgente (es. `Stipendio: FreeLance Stipendio: FreeLance Stipendio: FreeLance` oppure `Personale: Capelli Personale: Capelli`).
- **Gestione**: Possono essere inglobate così come sono generate dallo split. In Sossoldi genereranno stringhe categoriche più lunghe, che comunque saranno uniche nell'ID. Non serve una normalizzazione semantica troppo spinta.

---

## 3. Logica di Conversione e Mappatura Aggiornata

### A. Trasformazione Valori

1.  **Date (`Data` → `date`)**:
    - Parsing: Estrazione dal formato `GG mmm AAAA, HH:MM:SS` sostituendo i mesi in italiano con il numero, producendo il formato ISO 8601 esteso `YYYY-MM-DDTHH:MM:SS.000000`.
2.  **Importi (`Somma`/`Importo ricevuto` → `amount`)**:
    - Rimuovere: `-`, ` `, `"`, `€`, `\u00A0`.
    - Sostituire: `,` $\rightarrow$ `.`.
    - L'`amount` finale è `Math.abs(valore_pulito)`.
3.  **Mapping Tipo Transazione (`type`)**:
    - Se `Tipo di transazione` = `Trasferimento` o `Conto (a)` è visibile $\rightarrow$ `TRSF`.
    - Se `Tipo di transazione` = `Entrata` $\rightarrow$ `IN`.
    - Se `Tipo di transazione` = `Spesa` $\rightarrow$ `OUT`.
    - Se `Tipo di transazione` = `Saldo iniziale` $\rightarrow$ Nessuna transazione creata, ma aggiorna lo `startingValue` del `bankAccount`.
    - Se `Tipo di transazione` = `Modifica del saldo` $\rightarrow$ Valuta il segno della stringa. Se contiene `-` è `OUT`, altrimenti `IN`.
4.  **Generazione Identificativi**:
    - Ogni transazione, account, e categoria dovrà avere ID generati sequenzialmente da `1`.

### B. Gestione Entità Relazionali (Lookup Dictionaries)

- **Conti (`bankAccount`)**: Scansionare il file. Raccogliere nomi univoci da `Conto` e `Conto (a)`. Verificare le righe di tipo `Saldo iniziale` per accreditare lo `startingValue` all'account. I colori sono assegnati ciclicamente tra 5 varianti.
- **Categorie (`categoryTransaction`)**: Raccogliere ogni stringa distinta in `Categoria`. Se c'è `Parent: Figlio`, il nome visualizzato diventa `Parent - Figlio` (se diversi).
    - **Colori**: Mappatura fissa basata sulla `categoryColorList` di Sossoldi: **Rosso (2)** per `OUT`, **Verde (8)** per `IN`.

---

## 4. Workflow di Generazione per lo Script di Conversione

L'algoritmo ideale per lo script di migrazione procederà per passi successivi:

1.  **Fase 1: Lettura Grezza e Setup**
    - Parsing del CSV col separatore `;`.
    - Ignorare l'ultima colonna "vuota".
2.  **Fase 2: Indicizzazione Entità Base**
    - Identificare tutte le istanze uniche di `Conto`. Generare dizionario `{ NomeConto: ID_ACCOUNT }`.
    - Rilevare tutti i `Saldo iniziale` per iniettare i valori di `startingValue`.
    - Identificare stringhe uniche di `Categoria`. Estrarre genitore, poi figlio, creare IDs in mappa.
3.  **Fase 3: Rendering Entità Statiche**
    - Scrivere nel file `sossoldi.csv` la valuta base (Euro).
    - Scrivere i record `bankAccount` includendo il `startingValue`.
    - Scrivere i record `categoryTransaction`.
4.  **Fase 4: Trasposizione Transazioni**
    - Per ogni riga: saltare i `Saldo iniziale`.
    - Formattare importi sempre come float positivi.
    - Dedurre `IN/OUT/TRSF` base. Assicurarsi di impostare `idBankAccount` (ed `idBankAccountTransfer` su TRSF).
    - Se il `Descrizione` fa intuire che sia ricorrente, creare `recurringTransaction` e scriverlo, inserendo un ID di referral in `idRecurringTransaction`.
    - Scrivere il record `transaction`.
5.  **Fase Finale**: Salvataggio dei record in formato CSV multi-tabella. Il file prodotto utilizza terminatori di riga **CRLF (`\r\n`)**, requisito fondamentale per il parser CSV di Sossoldi (basato su Flutter/Dart).

---

## 5. Utilizzo del Script (`converter.py`)

A seguito degli aggiornamenti, lo script supporta l'esecuzione da riga di comando:

```bash
python converter.py -i <file_sorgente.csv> -o <file_destinazione.csv>
```

- `-i`, `--input`: Percorso del file CSV esportato da Money Pro.
- `-o`, `--output`: Percorso del file CSV da generare.
