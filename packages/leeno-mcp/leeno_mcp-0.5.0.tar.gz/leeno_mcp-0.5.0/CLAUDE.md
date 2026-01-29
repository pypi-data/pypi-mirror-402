# Regole per il progetto LeenO

## REGOLE INDEROGABILI

### 0. Codice non trovato nell'Elenco Prezzi → Creare Analisi Prezzo
Se il codice richiesto **NON ESISTE** nell'Elenco Prezzi, **NON usare un codice simile**.
Creare invece una nuova **Analisi di Prezzo**:

```python
# 1. Inizializza/crea foglio Analisi e nuovo blocco
oSheet, startRow = LeenoAnalysis.inizializzaAnalisi(oDoc)

# 2. Compila i dati dell'analisi
oSheet.getCellByPosition(1, startRow).String = "NP_001"  # Codice nuovo
oSheet.getCellByPosition(2, startRow).String = "mq"      # Unità misura
oSheet.getCellByPosition(3, startRow).String = "Descrizione della lavorazione..."

# 3. Aggiungi righe componenti con copia_riga_analisi()
# 4. Trasferisci a Elenco Prezzi
pyleeno.MENU_analisi_in_ElencoPrezzi()
```

Questo crea un prezzo valido che può essere usato nel COMPUTO.

### 1. Usare SEMPRE le macro LeenO
Quando si lavora con documenti LeenO (computo, contabilità, elenco prezzi), è **OBBLIGATORIO** usare le macro/funzioni esistenti di LeenO invece di manipolare manualmente celle e stili.

**Funzioni principali da usare:**

#### Inserimento voci
- `LeenoComputo.insertVoceComputoGrezza(oSheet, lrow)` - Inserisce una nuova voce copiando il template da S5
- `LeenoComputo.ins_voce_computo(cod)` - Inserisce voce con codice specificato
- `LeenoContab.insertVoceContabilita(oSheet, lrow)` - Inserisce voce in contabilità

#### Inserimento righe di misura
- `pyleeno.copia_riga_computo(lrow)` - Inserisce riga misura nel computo
- `pyleeno.copia_riga_contab(lrow)` - Inserisce riga misura in contabilità
- `pyleeno.copia_riga_analisi(lrow)` - Inserisce riga in analisi prezzi

#### Navigazione e utilità
- `LeenoComputo.circoscriveVoceComputo(oSheet, lrow)` - Trova i limiti di una voce
- `LeenoSheetUtils.numeraVoci(oSheet, lrow, flag)` - Rinumera le voci
- `LeenoSheetUtils.prossimaVoce(oSheet, lrow, direzione)` - Trova la prossima voce

### 2. Template S5
Il foglio **S5** contiene i template per:
- Righe 8-11: Template voce COMPUTO
- Riga 24: Template riga misura CONTABILITA

**MAI creare righe manualmente** - copiare sempre da S5.

### 3. Stili celle
Non impostare mai gli stili manualmente. Le funzioni LeenO applicano automaticamente gli stili corretti:
- `Comp Start Attributo` - Inizio voce
- `comp progress` - Riga dati voce
- `comp 10 s` - Riga misura
- `Comp End Attributo` - Fine voce (totali)

### 4. Formule
Le formule devono seguire il pattern LeenO:
- Quantità: `=PRODUCT(E:I)` o con IF per gestire valori vuoti
- Prezzo: `=VLOOKUP(B;elenco_prezzi;5;FALSE())`
- Importo: `=J*L`

## Percorso codice LeenO
```
C:\Users\mikib\OneDrive\Desktop\leeno\LeenO\python\pythonpath\
├── LeenoComputo.py      # Funzioni computo
├── LeenoContab.py       # Funzioni contabilità
├── LeenoSheetUtils.py   # Utilità fogli
├── pyleeno.py           # Funzioni principali
└── ...
```

## Connessione LibreOffice
```python
import uno
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext(
    "com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
```

Usare sempre l'interprete Python di LibreOffice:
```
"C:\Program Files\LibreOffice\program\python.exe"
```

## MCP Server - Integrazione Macro Native

Il MCP server utilizza le macro LeenO native tramite il modulo `leeno_macros.py`:

```python
from leeno_mcp.connection import get_macros

macros = get_macros()
if macros.is_initialized:
    # Usa funzioni native (più veloci e affidabili)
    macros.insertVoceComputoGrezza(oSheet, row)
    macros.copia_riga_computo(row)
    macros.numeraVoci(oSheet, 0, 1)
    macros.inizializzaAnalisi(oDoc)
```

### Wrapper disponibili

- `ComputoWrapper` - Operazioni su COMPUTO (add_voce, add_misura, list_voci)
- `ContabilitaWrapper` - Operazioni su CONTABILITA
- `AnalisiWrapper` - Operazioni su Analisi di Prezzo (crea_analisi, trasferisci_a_elenco_prezzi)
- `ElencoPrezziWrapper` - Operazioni su Elenco Prezzi

### Inizializzazione automatica

Le macro vengono inizializzate automaticamente alla connessione con LibreOffice.

**IMPORTANTE**: Non esistono fallback manuali. Se le macro non sono inizializzate,
le operazioni falliranno con un errore chiaro. Questo garantisce che tutte le
operazioni usino SEMPRE le macro native LeenO.
