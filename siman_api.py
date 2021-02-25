# -*- coding: utf-8 -*-
"""
Created on Sat Oct 24 09:32:04 2020

@author: ISAAC
"""

import pandas as pd
import queue
from selenium import webdriver
#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from datetime import date
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
#from siman import siman_module as PROYECT_CORE
from selenium.webdriver.chrome.options import Options
#from selenium.common.exceptions import JavascriptException
#from selenium.common.exceptions import NoSuchElementException
#from selenium.common.exceptions import TimeoutException
import config
import time
import requests
import base64
import json
import threading
import urllib.parse as urlparse
from urllib.parse import parse_qs

apiqueue = queue.Queue();
chrome_options = Options()  
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1500,1000")
simanqueue = queue.Queue();
principal_driver = webdriver.Chrome(executable_path=r"./chromedriver.exe",options=chrome_options)
today = date.today()
principal_driver.get('https://sv.siman.com/')
time.sleep(5)
result = []


def proccessObjectProducts(result_container, json_response):
    for product in json_response['data']['productSearch']['products']:
        item = []
        categorias_str = product["categories"][0]
        categorias = categorias_str[1:len(categorias_str)-2].split('/')
        pId = product["productId"]
        psku = product["productReference"]
        name = product["productName"]
        desc = product["description"]
        marca = product["brand"]
        precio_lista_max = product['priceRange']['listPrice']['highPrice']
        precio_lista_min = product['priceRange']['listPrice']['lowPrice']
        precio_venta_max = product['priceRange']['sellingPrice']['highPrice']
        precio_venta_min = product['priceRange']['sellingPrice']['lowPrice']
        genero = None
        modelo = None
        for pindex in range(len(product["properties"])):
            __property__ = product['properties'][pindex]
            if __property__["name"] == "Sexo":
                genero = __property__["values"][0]
            if __property__["name"] == "Modelo":
                modelo = __property__["values"][0]
        item.append(today)
        item.append(config.empresa.upper().strip())
        item.append(categorias[0].upper().strip()) #DEPARTAMENTO
        item.append(categorias[1].upper().strip() if len(categorias)> 1 else 'N/A') #CATEGORIA
        item.append(categorias[2].upper().strip() if len(categorias) > 2 else 'N/A') #SUBCATEGORIA
        item.append(pId.upper().strip()) #ID
        item.append(psku.upper().strip()) #SKU
        item.append(name.upper().strip()) #NOMBRE
        item.append(desc.upper().strip()) #DESCRIPCION
        item.append(marca.upper().strip() if marca is not None else 'N/A') #MARCA
        item.append("{:.2f}".format(precio_lista_max) if precio_lista_max is not None else '0.00') #PL-MAX
        item.append("{:.2f}".format(precio_lista_min) if precio_lista_min is not None else '0.00') #PL-MIN
        item.append("{:.2f}".format(precio_venta_max) if precio_venta_max is not None else '0.00') #PV-MAX
        item.append("{:.2f}".format(precio_venta_min) if precio_venta_min is not None else '0.00') #PV-MIN
        item.append(modelo.upper().strip() if modelo is not None else 'N/A') #MODELO
        item.append(genero.upper().strip() if genero is not None else 'N/A') #GENERO
        result_container.append(item)
        print("Articulo -> "+ str(len(result_container)))

    

class APIProccessTask(threading.Thread):
    def __init__(self, cola, result):
        threading.Thread.__init__(self)
        self.queue = cola
        self.result = result
    def run(self):
        while True:
            endpoint = self.queue.get()
            json_response = downloadProducts(endpoint)
            hasError = 'errors' in json_response
            if not hasError:
                hasProducts = 'data' in json_response and 'productSearch' in json_response['data'] and 'products' in json_response['data']['productSearch'] and len(json_response['data']['productSearch']['products']) > 0
                if hasProducts:
                    proccessObjectProducts(self.result,json_response)
            #if hasError:
                #print(endpoint)
            #avisa que la tarea termino
            self.queue.task_done()
            #print(self.queue.qsize())
                
                
def downloadProducts(url):
    req = requests.get(url)
    array = req.json()
    return array

def buildUrl(desde, hasta, query, mapp):
    estructura_query = query.split('/')
    estructura_map = mapp.split(',')
    facets = []
    for i in range(len(estructura_map)):
        if len(estructura_query) > i:
            facets.append({"key":estructura_map[i],"value":estructura_query[i]})
    filters = {
            "hideUnavailableItems":False,
            "skusFilter":"ALL",
            "simulationBehavior":"skip",
            "installmentCriteria":"MAX_WITHOUT_INTEREST",
            "productOriginVtex":True,"map":mapp,
            "query":query,
            "orderBy":"OrderByScoreDESC",
            "from":desde,
            "to":hasta,
            "selectedFacets":facets,
            "operator":"and","fuzzy":"0","facetsBehavior":"Static","withFacets":False}
    filtrosb64 = base64.urlsafe_b64encode(json.dumps(filters).encode()).decode()
    url = "https://sv.siman.com/_v/segment/graphql/v1?workspace=master&maxAge=short&appsEtag=remove&domain=store&locale=es-SV&__bindingId=a64d5203-0c28-49c6-8bcb-f7cfe303e32f&operationName=productSearchV3&variables={}&extensions={%22persistedQuery%22:{%22version%22:1,%22sha256Hash%22:%2289389dc09892c961bfea39a700388f5c846f3de00f4ccb31e07cccaeb655d6ef%22,%22sender%22:%22vtex.store-resources@0.x%22,%22provider%22:%22vtex.search-graphql@0.x%22},%22variables%22:%22"+ filtrosb64 +"%22}"
    return url

try:
    element = principal_driver.find_element_by_class_name("vtex-menu-2-x-styledLinkContainer--title-menu-departament")
    hover = ActionChains(principal_driver).move_to_element(element)
    hover.perform()
    links_elementes = WebDriverWait(principal_driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "vtex-menu-2-x-styledLink--title-menu-sub-cat")))
    links_sv = [elem.get_attribute('href') for elem in links_elementes] 
    cleaned_links = [i for i in links_sv if i]
    departamentos = []
    for link in cleaned_links:
        if 'moda' not in link and 'mac' not in link:
            link_without_server = link[21:]   
            if link_without_server[len(link_without_server)-1:] == '/':
                departamentos.append(link_without_server[0:len(link_without_server)-1])
            else:
                departamentos.append(link_without_server)
    
    for i in range(5): #NUMERO DE HILOS
        hilo = APIProccessTask(apiqueue,result)
        hilo.setDaemon(True)
        hilo.start()        
        print("Started webdriver: --- "+str(i)+" --- from main")
        
    for d in departamentos:
        total_products_in_departament = 0
        inicioproductos = 0
        finalproductos = 75
        productos = downloadProducts(buildUrl(inicioproductos,finalproductos,d,'departmento,categoria'))
        hasError = 'errors' in productos
        if hasError:
            print(productos)
        else:
            hasProducts = 'data' in productos and 'productSearch' in productos['data'] and 'products' in productos['data']['productSearch'] and len(productos['data']['productSearch']['products']) > 0
            if hasProducts:
                proccessObjectProducts(result,productos)
                total_products_in_departament = productos['data']['productSearch']['recordsFiltered'] - len(productos['data']['productSearch']['products'])
                if total_products_in_departament > 0:
                    total_pages = total_products_in_departament // 75
                    for i in range(total_pages):
                        finalproductos += 75
                        inicioproductos += 75
                        url = buildUrl(inicioproductos,finalproductos,d,'departmento,categoria')
                        apiqueue.put(url)
                        
    # for moda_link in config.siman_moda:
    #     link_without_server = moda_link[21:]
    #     removedquery = link_without_server.split('?')[0]
    #     total_products_in_departament = 0
    #     inicioproductos = 0
    #     finalproductos = 75
    #     parsed = urlparse.urlparse(moda_link)
    #     query_string = parse_qs(parsed.query)
    #     query = None
    #     mapp = query_string['map'][0]
    #     if 'query' in query_string:
    #         query = query_string['query'][0]
    #     else:
    #         query = removedquery
    #     productos = downloadProducts(buildUrl(inicioproductos,finalproductos,query,query_string['map'][0]))
    #     hasError = 'errors' in productos
    #     if hasError:
    #         print(productos)
    #     else:
    #         hasProducts = 'data' in productos and 'productSearch' in productos['data'] and 'products' in productos['data']['productSearch'] and len(productos['data']['productSearch']['products']) > 0
    #         if hasProducts:
    #             proccessObjectProducts(result,productos)
    #             total_products_in_departament = productos['data']['productSearch']['recordsFiltered'] - len(productos['data']['productSearch']['products'])
    #             if total_products_in_departament > 0:
    #                 total_pages = total_products_in_departament // 75
    #                 for i in range(total_pages):
    #                     finalproductos += 75
    #                     inicioproductos += 75
    #                     url = buildUrl(inicioproductos,finalproductos,query,mapp)
    #                     apiqueue.put(url)
    apiqueue.join()
    df = pd.DataFrame(result, columns=config.columns)
    df.to_csv('siman.csv', encoding='utf-8-sig')
finally:
    principal_driver.quit()
                

          

