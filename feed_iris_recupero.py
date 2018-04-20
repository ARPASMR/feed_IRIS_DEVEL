# Alimentazione di IRIS
# logica di funzionamento: il programma legge le variabili di ambiente e può eseguire l'alimentazione in diverse modalità
# a. diretta: non ci sono ancora dati e vengono acquisiti direttamente dal REM (datainizio e datafine coincidono)
# b. in recupero: possono esserci delle lacune che vengono identificate e il dato corrispondente richiesto al REMWS_GATEWAY
#    in questo caso il recupero va da datainizio a datafine
# 1. inizializzazione
# 2. richiesta elenco sensori al db (df_sensori)

# FASE 1
#inizializzazione
import os
import pandas as pd
# import numpy as np
from sqlalchemy import *
import datetime as dt
import json as js
import requests
# variabili di ambiente (da togliere in produzione)
REMWS_GATEWAY='http://10.10.0.15:9099'
url=REMWS_GATEWAY
DEBUG=False
IRIS_TABLE_NAME='m_osservazioni_tr'
IRIS_SCHEMA_NAME='realtime'
AUTORE=os.getenv('COMPUTERNAME')
MINUTES= 1440 # minuti di recupero
if (AUTORE==None):
    AUTORE=os.getenv('HOSTNAME')
    MINUTES=0 # minuti di recupero in caso GMT+0
    IRIS_USER_ID=os.getenv('IRIS_USER_ID')
    IRIS_USER_PWD=os.getenv('IRIS_USER_PWD')
    IRIS_DB_NAME=os.getenv('IRIS_DB_NAME')
    IRIS_DB_HOST=os.getenv('IRIS_DB_HOST')
    h=os.getenv('TIPOLOGIE') # elenco delle tipologie da cercare nella tabella delle osservazioni realtime, è una stringa
    # trasformo la stringa in lista
TIPOLOGIE=h.split()
# inizializzazione delle date
datafine=dt.datetime.utcnow()
datainizio=datafine-dt.timedelta(minutes=MINUTES)
#definizione delle funzioni
# la funzione legge il blocco di dati e lo trasforma in DataFrame
def seleziona_richiesta(Risposta):
    # definisco dataframe della risposta
    df_risposta=pd.DataFrame(columns=['data_e_ora','misura','validita'])
    # dizionario di appoggio con la selezione dei dati
    aa=Risposta['data']['sensor_data_list'][0]['data']
    # ciclo lettura
    for i in range(1,len(aa)-1):
    #    print(i,aa[i]['datarow'].split(";")[2])
        df_risposta.loc[i-1]=[aa[i]['datarow'].split(";")[0],aa[i]['datarow'].split(";")[1],aa[i]['datarow'].split(";")[2]]
    return df_risposta
def Inserisci_in_realtime(schema,table,idsensore,tipo,operatore,datar,misura,autore):
    # la funzione crea la query da per l'inserimento del dato
    s=dt.datetime.now()
    mystring=s.strftime("%Y-%m-%d %H:%M")
    Query_Insert="INSERT into "+schema+"."+table+\
    " (idsensore,nometipologia,idoperatore,data_e_ora,misura, autore,data)\
    VALUES ("+str(idsensore)+",'"+tipo+"',"+str(operatore)+",'"+\
    datar.strftime("%Y-%m-%d %H:%M")+"',"+str(misura)+",'"+ autore+"','"+mystring+"');"
    return Query_Insert
def Richiesta_remwsgwy (framedati):
    #funzione di colloquio con il remws: manda la dichiesta e decodifica la risposta
    richiesta={
        'header':{'id': 10},
        'data':{'sensors_list':[framedati]}
        }
    try:
        r=requests.post(url,data=js.dumps(richiesta))

    except:
        print("Errore: REMWS non raggiungibile", end="\r")
    ci_sono_dati=False
    if(len(r.text)>0):
        risposta=js.loads(r.text)
        #controllo progressivamente se la risposta è buona e se ci sono dati
        outcome=risposta['data']['outcome']
        if (outcome==0):
            if (len(risposta['data']['sensor_data_list'])>0):
                ci_sono_dati=True
        else:
            return []
    if(ci_sono_dati):
        # estraggo il dato
        return risposta['data']['sensor_data_list'][0]['data']
    else:
        return []
###
#FASE 2 - query al dB
engine = create_engine('postgresql+pg8000://'+IRIS_USER_ID+':'+IRIS_USER_PWD+'@'+IRIS_DB_HOST+'/'+IRIS_DB_NAME)
conn=engine.connect()

#preparazione dell'elenco dei sensori
Query='Select *  from "dati_di_base"."anagraficasensori" where "anagraficasensori"."datafine" is NULL and idrete in (1,4);'
df_sensori=pd.read_sql(Query, conn)
 
#query di richiesta dati già presenti nel dB
QueryDati='Select * from "'+IRIS_SCHEMA_NAME+'"."'+IRIS_TABLE_NAME+'" where "m_osservazioni_tr"."data_e_ora" between \''+datainizio.strftime("%Y-%m-%d %H:%M")+'\' and \''+datafine.strftime("%Y-%m-%d %H:%M")+'\';'
df_dati=pd.read_sql(QueryDati, conn)

#ALIMETAZIONE IN RECUPERO
# suppongo di avere già dei dati, vedo qule datomanca, lo chiedo e loinserisco.
# Se l'inserimento fallisce vuol dire che qualcun altro ha inserito il dato (ovvero un processo in parallelo, il che è possibilestrano...)

# selezione dell'ora
minuto=int(datainizio.minute/10)*10
data_ricerca=dt.datetime(datainizio.year,datainizio.month,datainizio.day,datainizio.hour,minuto,0)
df_section=df_sensori[df_sensori.nometipologia.isin(TIPOLOGIE)]
#ciclo sui sensori:
# strutturo la richiesta
id_operatore=1
function=1
frame_dati={}
frame_dati["sensor_id"]=0
frame_dati["granularity"]=1 # chiedo solo i 10 minuti
frame_dati["start"]=data_ricerca.strftime("%Y-%m-%d %H:%M")
frame_dati["finish"]=data_ricerca.strftime("%Y-%m-%d %H:%M")
#suppongo che in df_section ci siano solo i sensori che mi interessano e faccio il ciclo di richiesta
s=dt.datetime.now()
conn=engine.connect()
# inizio del ciclo vero e proprio
for row in df_section.itertuples():
    #estraggo i dati dal dataframe
    element=df_dati[df_dati.idsensore==row.idsensore]
    frame_dati["sensor_id"]=row.idsensore
    # assegno operatore e funzione corretti
    if(row.nometipologia=='PP' or row.nometipologia=='N'):
        id_operatore=4
        function=3
    else:
         id_operatore=1
         function=1
    #selezione del valore orario se la frequenza è 60
    if(row.frequenza==60):
        id_periodo=3
        PERIODO=int(MINUTES/60)
        attesi=pd.date_range(data_ricerca, periods=PERIODO,freq='60min')
    else:
        id_periodo=1
        PERIODO=int(MINUTES/10)
        attesi=pd.date_range(data_ricerca, periods=PERIODO,freq='10min')
    #ho selezionato il periodo atteso: estraggo il dataframe degli elementi attesi
    df=attesi.isin(element['data_e_ora'])    
    #eseguo il ciclo di richiesta sui dati mancanti
    for dato_mancante in attesi[~df]:
        frame_dati["start"]=dato_mancante.strftime("%Y-%m-%d %H:%M")
        frame_dati["finish"]=dato_mancante.strftime("%Y-%m-%d %H:%M")
        frame_dati["operator_id"]=id_operatore
        frame_dati["function_id"]=function
        aa=Richiesta_remwsgwy(frame_dati)
        if (len(aa)>2):
        # prendo solo il primo element
            misura=aa[1]['datarow'].split(";")[1]
            QueryInsert=Inserisci_in_realtime(IRIS_SCHEMA_NAME,IRIS_TABLE_NAME,\
            row.idsensore,row.nometipologia,id_operatore,dato_mancante,misura,AUTORE)
            try:
                conn.execute(QueryInsert)
                print("+++++++Query eseguita per ",row.idsensore, dato_mancante.strftime("%Y-%m-%d %H:%M"))
            except:
                print("Query non riuscita! per ",row.idsensore, dato_mancante.strftime("%Y-%m-%d %H:%M"))
        else:
            print ("Attenzione: dato di ", row.idsensore, " ASSENTE nel REM per", dato_mancante.strftime("%Y-%m-%d %H:%M"))
print(s,dt.datetime.now())