# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 12:46:22 2021

@author: ISAAC
"""
import os
import time
import sqlalchemy #import create_engine
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import pandas as pd
import pyodbc
import datetime
import sys  
from datetime import datetime,timedelta

now = datetime.now()
nombreArchivo="siman.csv" #le pones el nombre de del archivo mas la extensión
nombreArchivo2="lacuracao.csv" #le pones el nombre de del archivo mas la extensión

#Se está leyendo el archivo excel
#os.chdir("/") # le pones la ruta donde tenes el archivo
fich1=nombreArchivo
fich2=nombreArchivo2
DataImport=pd.read_csv(fich1) #Cambias el nombre de la hoja de excel que tiene el archivo
DataImport2=pd.read_csv(fich2) #Cambias el nombre de la hoja de excel que tiene el archivo
#print(DataImport2.iloc[:, 1:])
#Se crea la conexión a la base de datos para insertar datos
engine = create_engine('mssql+pyodbc://localhost/siman?driver=SQL+Server+Native+Client+11.0?trusted_connection=yes', deprecate_large_types=True)#, encoding=\"latin1\")#, encoding=\"utf-8\")\n",
statement = text("""DELETE FROM testconsolidado; DELETE FROM consolidado;""")
with engine.connect() as con:
      con.execute(statement)
     
DataImport.iloc[:, 1:].to_sql('testconsolidado', engine,if_exists='append', index=False)
DataImport2.iloc[:, 1:].to_sql('testconsolidado', engine,if_exists='append', index=False)

query_consolidado = "insert into [siman].[dbo].[consolidado]([siman].[dbo].[consolidado].[categoria],[siman].[dbo].[consolidado].[departamento],[siman].[dbo].[consolidado].[descripcion],[siman].[dbo].[consolidado].[empresa],[siman].[dbo].[consolidado].[genero],[siman].[dbo].[consolidado].[id],[siman].[dbo].[consolidado].[listaPrecioMax],[siman].[dbo].[consolidado].[listaPrecioMin],[siman].[dbo].[consolidado].[marca],[siman].[dbo].[consolidado].[modelo],[siman].[dbo].[consolidado].[nombre],[siman].[dbo].[consolidado].[precioVentaMax],[siman].[dbo].[consolidado].[precioVentaMin],[siman].[dbo].[consolidado].[Sku],[siman].[dbo].[consolidado].[subCategoria],[siman].[dbo].[consolidado].[fechaIngreso],[habilitado])SELECT  [siman].[dbo].[testconsolidado].[Categoria]	,[siman].[dbo].[testconsolidado].[Departamento]	,[siman].[dbo].[testconsolidado].[Descripcion],[siman].[dbo].[testconsolidado].[Empresa],[siman].[dbo].[testconsolidado].[Genero],[siman].[dbo].[testconsolidado].[id],[siman].[dbo].[testconsolidado].[ListaPreciosMax],[siman].[dbo].[testconsolidado].[ListaPreciosMin],[siman].[dbo].[testconsolidado].[Marca],[siman].[dbo].[testconsolidado].[Modelo],[siman].[dbo].[testconsolidado].[Nombre],[siman].[dbo].[testconsolidado].[PrecioVentaMax],[siman].[dbo].[testconsolidado].[PrecioVentaMin],[siman].[dbo].[testconsolidado].[Sku],[siman].[dbo].[testconsolidado].[SubCategoria],[siman].[dbo].[testconsolidado].[Fecha],1 as habilitado FROM [siman].[dbo].[testconsolidado];"
with engine.connect() as con:
      con.execute(query_consolidado)