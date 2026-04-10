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

## Licenza

Questo progetto è distribuito sotto la licenza MIT. Vedi il file `LICENSE` per i dettagli (se presente).

---
*Nota: Questo tool non è affiliato ufficialmente con [Money Pro](https://money.pro/it/android/) o Sossoldi.*
