# feed IRIS (TEST PER IRIS DEVEL - versione di sviluppo)
Alimentazione di IRIS tramite script python in sostituzione di recupero_RT

# prerequisiti
1. rwmwsgwyd funzionante
2. tabelle di IRIS per il temporeale su postgres
3. pacchetti di python indicati nel codice

# utilizzo
Il recupero viene gestito dal launcher che accetta in ingresso tre parametri
```
./launch_feed.sh  arg1 arg2 arg3
```

_arg1_ minuto al quale esegue il comando

_arg2_ flag per recupero: *R* esegue il recupero, ogni altro carattere non esegue il recupero (es. *N*)

_arg3_ tempo in secondi tra una esecuzione e la successiva (*facoltativo, default 3600*)


# ENV

> **Sono state esportate come variabili d'ambiente le variabili:**
> ```diff
> - IRIS_USER_ID
> - IRIS_DB_NAME
> - IRIS_DB_HOST
> ```

> **Le quali corrispondono**
> **per LA VERSIONE DI PRODUZIONE a**:
> ```diff
> IRIS_USER_ID *postgres*
> IRIS_DB_NAME *iris_base*
> IRIS_DB_HOST *10.10.0.19*
> ```

> **per LA VERSIONE DI SVILUPPO a**:
> ```diff
> IRIS_USER_ID *postgres*
> IRIS_DB_NAME *iris_devel*
> IRIS_DB_HOST *10.10.0.19*
> ```

Devono essere specificate le variabili:

DEBUG *True* scrive tutti gli errori o gli inserimenti dei dati, *False* scrive solo le informazioni essenziali

TIPOLOGIE elenco delle tipologie per cui esegue l'alimentazione/recupero (*vedi esempio*)

MINUTES numero di minuti che considera per il recupero o l'alimentazione diretta (*vedi note*)

IRIS_USER_PWD password dell'utente IRIS_USER_ID

NAME nome dell'autore dell'inserimento


# esempio
```
docker run -d --rm -v "$PWD":/usr/src/myapp -w /usr/src/myapp -e "IRIS_USER_ID=postgres" -e "IRIS_USER_PWD=<password>" -e "IRIS_DB_NAME=iris_base" -e "IRIS_DB_HOST=10.10.0.19" -e "TIPOLOGIE=I PP T UR N RG PA VV DV" -e "DEBUG=True" -e "MINUTES=1440" --name "recupero_all" arpasmr/feed_iris ./launch_feed.sh 8 R 3600
```
# note: uso di MINUTES
L'uso combinato di *MINUTES* e *arg1* determina il comportamento dell'alimentazione/recupero.
In particolare, nel caso dell'alimentazione diretta si suppone che non vi siano dati nel dB e quindi la query di inserimento fallisce solo se qualcun altro ha già inserito un valore (violazione della chiave primaria). In pratica, il funzionamento prevede che *MINUTES* sia *0* e che l'alimentazione avvenga al minuto *arg1*.

Ovviamente, se *arg1* è troppo vicino al momento in cui le stazioni inviano i dati, l'interrogazione al remws riporterà "Dato non presente" e quindi non verrà fatto alcun inserimento.

Se voglio usare *arg1* vicino a 0, il valore di °MINUTES* dovrà essere 10 o maggiore, in modo che venga chiesto il dato presente nel REM con marca temporale più vecchia di *MINUTES* minuti fa.

Se *MINUTES* è *0* per ottenere il pacchetto dei 10 minuti correnti conviene porre *arg1* pari a 6-8.

L'esecuzione di un'alimentazione ritardata (*MINUTES*>>0) può essere conveniente nel caso di sensori che sono sistematicamente in ritardo (es. sensori RRQA). In questo caso conviene impostare un recupero (*arg2*=R che peschi alcuni *MINUTES* minuti fa (es. *30*) e che venga lanciato ogni 10 minuti (ponendo *arg3* pari a 600).

Per il *recupero* il valore di *MINUTES* deve essere 1440 (per recuperare i dati delle 24h precedenti) mentre *arg1* può essere un valore qualunque.

Nel caso del recupero di 24h il valore di *arg3* (intervallo tra un'esecuzione e la successiva) va posto pari ad almeno 3600 secondi (che è il valore di default e può essere omesso)

L'alimentazione diretta cerca il dato dall'ora solare all'indietro di *MINUTES* minuti.

Il recupero cerca tutti i dati dall'ora UTC all'indietro di *MINUTES* minuti
