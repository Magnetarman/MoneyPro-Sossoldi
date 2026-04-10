<div align="center">
<img src="img/banner.jpg" alt="Sossoldi Converter Banner" width="800">
</div>

# Money Pro to Sossoldi Converter

Un semplice script Python per convertire le esportazioni CSV di **[Money Pro](https://money.pro/it/android/)** nel formato compatibile con l'importazione di **[Sossoldi](https://github.com/Sossoldi/sossoldi)**.

## Caratteristiche

- **Mappatura Conti**: Riconoscimento automatico dei conti bancari e dei saldi iniziali.
- **Gerarchia Categorie**: Supporto per categorie e sottocategorie (`Genitore:Figlio`).
- **Tipi di Transazione**: Gestione corretta di Entrate, Spese, Trasferimenti e Modifiche del Saldo.
- **Compatibilità Sossoldi**: Generazione di file CSV con terminatori di riga CRLF (`\r\n`) richiesti dal parser di Sossoldi.
- **Localizzazione**: Configurato per le abbreviazioni dei mesi in italiano (es. `gen`, `feb`).

## Requisiti

- Python 3.8 o superiore.
- Nessuna dipendenza esterna (utilizza solo librerie standard).

## Installazione

1. Clona questo repository:
   ```bash
   git clone https://github.com/tuo-username/Sossoldi-Converter.git
   cd Sossoldi-Converter
   ```
2. (Opzionale) Crea un ambiente virtuale:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Su Windows: venv\Scripts\activate
   ```

## Utilizzo

Esporta i tuoi dati da Money Pro in formato CSV (assicurati di includere tutte le transazioni) e usa lo script:

```bash
python converter.py -i percorso/al/tuo/money_pro.csv -o sossoldi_import.csv
```

### Argomenti

- `-i`, `--input`: Percorso del file CSV di Money Pro (default: `money_pro.csv`).
- `-o`, `--output`: Percorso del file CSV generato per Sossoldi (default: `sossoldi_generato.csv`).

## Limitazioni Note

- **Lingua**: Attualmente supporta esportazioni Money Pro in lingua italiana. Se utilizzi un'altra lingua, modifica il dizionario `MAPPATURA_MESI` in `converter.py`.
- **Ricorrenze**: Le transazioni ricorrenti sono importate come transazioni singole (il flag `recurring` è impostato a `0` per evitare errori di vincoli nel database Sossoldi).
- **Categorie e Icone**: A causa della struttura particolare del CSV di Money Pro, le categorie vengono importate senza icone e potrebbero presentare duplicati nel caso di gerarchie complesse. Tuttavia, l'esperienza d'uso (caso personale con archivio inizializzato nel 2018 ed oltre 10 conti monitorati) mostra che con circa 30 minuti di configurazione manuale in Sossoldi per ripristinare icone e gerarchie, si ottiene un risultato visuale e gestionale nettamente superiore a quello originale di Money Pro.

## Contribuire

Le Pull Request per migliorare il codice o risolvere le limitazioni sopra elencate sono benvenute. Tuttavia, si prega di notare che queste non hanno una priorità critica: il progetto è considerato concluso per le necessità dell'autore, avendo permesso una migrazione corretta e soddisfacente da Money Pro a Sossoldi.

## Licenza

Questo progetto è distribuito sotto la licenza MIT. Vedi il file `LICENSE` per i dettagli (se presente).

---
*Nota: Questo tool non è affiliato ufficialmente con [Money Pro](https://money.pro/it/android/) o Sossoldi.*
