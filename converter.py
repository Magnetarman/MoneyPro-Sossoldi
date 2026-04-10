import csv
import re
import argparse
import sys
from datetime import datetime

# ==========================================
# CONFIGURAZIONE E DIZIONARI
# ==========================================

MAPPATURA_MESI = {
    'gen': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'mag': '05', 'giu': '06', 'lug': '07', 'ago': '08',
    'set': '09', 'ott': '10', 'nov': '11', 'dic': '12'
}

SOSSOLDI_HEADER = [
    'table_name', 'id', 'name', 'symbol', 'color', 'startingValue', 'active',
    'mainAccount', 'createdAt', 'updatedAt', 'countNetWorth', 'position', 'date',
    'amount', 'type', 'note', 'idCategory', 'idBankAccount', 'idBankAccountTransfer',
    'recurring', 'idRecurringTransaction', 'fromDate', 'toDate', 'recurrency',
    'lastInsertion', 'parent', 'code', 'mainCurrency'
]

# TIMESTAMP BASE DA CUI PARTIREAMO PER CREATED_AT ecc.
NOW_STR = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000000")

def pulisci_importo(importo_str):
    """
    Pulisce la stringa dell'importo e restituisce un float e se era originale negativo.
    """
    if not importo_str.strip():
        return 0.0, False
        
    s = importo_str.replace('€', '').replace(' ', '').replace('\xa0', '').strip()
    is_negative = '-' in s
    s = s.replace('-', '')
    s = s.replace('.', '') # se ci fossero punti per le migliaia
    s = s.replace(',', '.')
    
    try:
        valore = float(s)
        return valore, is_negative
    except ValueError:
        return 0.0, False

def formatta_data(data_str):
    """
    Converte da "10 mar 2018, 00:14:33" in formato ISO 8601 esteso
    """
    if not data_str.strip():
        return ""
    
    # Rimuoviamo la virgola
    data_str = data_str.replace(',', '')
    parti = data_str.split(' ')
    if len(parti) >= 4:
        giorno = parti[0].zfill(2)
        mese_str = parti[1].lower()
        anno = parti[2]
        orario = parti[3]
        mese = MAPPATURA_MESI.get(mese_str, '01')
        return f"{anno}-{mese}-{giorno}T{orario}.000000"
    return ""

def popola_record(table_name, id_val, **kwargs):
    """
    Crea un dizionario per Sossoldi inizializzato tutto a stringa vuota,
    compilando solo i valori richiesti dai kwargs.
    """
    record = {k: '' for k in SOSSOLDI_HEADER}
    record['table_name'] = table_name
    record['id'] = id_val
    for k, v in kwargs.items():
        if k in record:
            record[k] = v
    return record

def esegui_conversione(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        # Passiamo il delimiter corretto
        reader = csv.DictReader(f, delimiter=';')
        righe = list(reader)

    # -----------------------------------
    # 1. ESTREZIONE ENTITÀ E SALDI INIZIALI
    # -----------------------------------
    bank_accounts = {}      # Nome -> ID
    bank_starting_vals = {} # Nome -> Saldo (float)
    categories = {}         # Nome -> ID (con gerarchia)
    category_tree = {}      # Mappa Nome -> id per relazioni list
    
    id_bank = 1
    id_category = 1
    
    for riga in righe:
        conto = riga.get('Conto', '').strip()
        conto_a = riga.get('Conto (a)', '').strip()
        categoria = riga.get('Categoria', '').strip()
        tipo_trans = riga.get('Tipo di transazione', '').strip()
        somma_str = riga.get('Somma', '').strip()
        
        # Gestione Bank Account
        if conto and conto not in bank_accounts:
            bank_accounts[conto] = id_bank
            bank_starting_vals[conto] = 0.0
            id_bank += 1
            
        if conto_a and conto_a not in bank_accounts:
            bank_accounts[conto_a] = id_bank
            bank_starting_vals[conto_a] = 0.0
            id_bank += 1
            
        if tipo_trans.lower() == 'saldo iniziale':
            valore, _ = pulisci_importo(somma_str)
            bank_starting_vals[conto] = valore
            
        # Gestione Categorie (Genitore: Figlio)
        if categoria:
            parts = [p.strip() for p in categoria.split(':')]
            parent_name = parts[0]
            
            # Determiniamo il tipo dalla transazione
            # Se la transazione è un'Entrata o la somma iniziale positiva per category IN (di solito le categorie sono usate per IN/OUT)
            c_type = 'IN' if tipo_trans.lower() == 'entrata' else 'OUT'
            
            if parent_name not in categories:
                categories[parent_name] = {'id': id_category, 'parent': '', 'type': c_type}
                id_category += 1
            elif c_type == 'IN': # Se almeno una volta è IN, la consideriamo IN (es. stipendi)
                categories[parent_name]['type'] = 'IN'
                
            if len(parts) > 1:
                child_name = categoria # Salviamo tutto come chiave unica nel dizionario globale
                if child_name not in categories:
                    categories[child_name] = {'id': id_category, 'parent': categories[parent_name]['id'], 'type': c_type}
                    id_category += 1
                elif c_type == 'IN':
                    categories[child_name]['type'] = 'IN'

    # -----------------------------------
    # 2. GENERAZIONE OUTPUT SOSSOLDI
    # -----------------------------------
    sossoldi_rows = []
    
    # Currency Tassativo
    sossoldi_rows.append(popola_record(
        'currency', 1, name='Euro', symbol='€', code='EUR', mainCurrency=1
    ))

    # Bank Accounts
    for name, id_b in bank_accounts.items():
        starting_val = bank_starting_vals.get(name, 0.0)
        sossoldi_rows.append(popola_record(
            'bankAccount', id_b, 
            name=name, symbol='account_balance', color=(id_b - 1) % 5, 
            startingValue=round(starting_val, 2),
            active=1, mainAccount=1 if id_b==1 else 0, 
            createdAt=NOW_STR, updatedAt=NOW_STR, countNetWorth=1, position=0
        ))

    # Categories
    for cat_name, data in categories.items():
        # Utilizziamo l'intero nome (inclusi i parent separati da due punti) per evitare duplicati visivi in Sossoldi UI
        # A meno che il nome figlio non sia identico al padre (Money Pro a volte fa Padre:Padre). In quel caso deduplichiamo la stringa visiva.
        parts = [p.strip() for p in cat_name.split(':')]
        name_display = " - ".join(parts) if len(parts) > 1 and parts[0] != parts[1] else parts[0]
        
        # Assegnazione Colore
        # Sossoldi mappa il campo 'color' all'indice della lista categoryColorList
        # Indice 2 = Red per OUT
        # Indice 8 = Green per IN
        cat_type = data['type']
        cat_color = 2 if cat_type == 'OUT' else 8
        
        sossoldi_rows.append(popola_record(
            'categoryTransaction', data['id'],
            name=name_display, symbol='category', color=cat_color,
            createdAt=NOW_STR, updatedAt=NOW_STR, position=0, 
            type=cat_type,
            parent=data['parent'] if data['parent'] else ''
        ))

    # Transazioni
    id_trans = 1
    
    for riga in righe:
        tipo_trans = riga.get('Tipo di transazione', '').strip()
        if tipo_trans.lower() == 'saldo iniziale':
            continue # Li abbiamo già gestiti nei bank accounts startingValue
            
        conto = riga.get('Conto', '').strip()
        conto_a = riga.get('Conto (a)', '').strip()
        categoria = riga.get('Categoria', '').strip()
        descrizione = riga.get('Descrizione', '').strip()
        data_trans = formatta_data(riga.get('Data', '').strip())
        
        if not data_trans:
            continue # Salto righe vuote
            
        # Determina gli importi
        somma_str = riga.get('Somma', '').strip()
        importo_ricevuto_str = riga.get('Importo ricevuto', '').strip()
        
        # Nel caso di trasferimenti la somma potrebbe essere su importo ricevuto
        str_da_pulire = somma_str if somma_str else importo_ricevuto_str
        importo_val, is_negative = pulisci_importo(str_da_pulire)
        
        # Tipo Logico Mappatura
        t_type = "OUT"
        id_acc_transfer = ""
        
        if conto_a or tipo_trans.lower() == 'trasferimento':
            t_type = "TRSF"
            id_acc_transfer = bank_accounts.get(conto_a, "")
        elif tipo_trans.lower() == 'entrata':
            t_type = "IN"
        elif tipo_trans.lower() == 'spesa':
            t_type = "OUT"
        elif tipo_trans.lower() == 'modifica del saldo':
            t_type = "OUT" if is_negative else "IN"

        # Categoria collegamento
        cat_id = categories.get(categoria, {}).get('id', '') if categoria else ''
        acc_id = bank_accounts.get(conto, '')
        
        if str(acc_id) == "":
            print(f"Skipping riga orfana di account: {riga}")
            continue

        # Disabilitiamo il recurring per evitare constraint (Foreign Key failure) su Sossoldi, 
        # dato che richiederebbe entità recurringTransaction dedicate non generate in questo script.
        is_recurring = 0
            
        sossoldi_rows.append(popola_record(
            'transaction', id_trans,
            date=data_trans,
            amount=round(importo_val, 2),
            type=t_type,
            note=descrizione,
            idCategory=cat_id if cat_id else '',
            idBankAccount=int(acc_id) if acc_id else '',
            idBankAccountTransfer=int(id_acc_transfer) if id_acc_transfer else '',
            recurring=is_recurring,
            idRecurringTransaction='',
            createdAt=data_trans,
            updatedAt=NOW_STR
        ))
        id_trans += 1

    # -----------------------------------
    # 3. SCRITTURA CSV FINALE
    # -----------------------------------
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        # Sossoldi richiede strict virgole per la compatibilità sqlite dumper e MAI \n singolo.
        # Usa \r\n perché il parser Dart (CsvToListConverter di default) di Sossoldi splitta ESATTAMENTE sulle CRLF.
        # Se usiamo \n il file viene visto dal parser Dart come un'unica grande riga!
        writer = csv.DictWriter(f, fieldnames=SOSSOLDI_HEADER, lineterminator='\r\n')
        writer.writeheader()
        for row in sossoldi_rows:
            writer.writerow(row)
            
    print(f"[OK] Conversione completata!\n- Valute create: 1\n- Bank Accounts: {len(bank_accounts)}\n- Categorie (incluse Parent): {len(categories)}\n- Transazioni processate: {id_trans - 1}\nFile salvato in: {output_file}")


def parse_arguments():
    """
    Gestisce gli argomenti da riga di comando.
    """
    parser = argparse.ArgumentParser(
        description="Convertitore di esportazioni Money Pro (CSV) nel formato compatibile con Sossoldi."
    )
    parser.add_argument(
        "-i", "--input",
        default="money_pro.csv",
        help="Percorso del file CSV esportato da Money Pro (default: money_pro.csv)"
    )
    parser.add_argument(
        "-o", "--output",
        default="sossoldi_generato.csv",
        help="Percorso del file CSV da generare per Sossoldi (default: sossoldi_generato.csv)"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    FILE_SORGENTE = args.input
    FILE_DESTINAZIONE = args.output
    
    print(f"[*] Inizializzazione migrazione da '{FILE_SORGENTE}' a '{FILE_DESTINAZIONE}'...")
    
    try:
        esegui_conversione(FILE_SORGENTE, FILE_DESTINAZIONE)
    except FileNotFoundError:
        print(f"[ERR] Errore: Il file di input '{FILE_SORGENTE}' non è stato trovato.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERR] Errore durante la conversione: {e}")
        sys.exit(1)
