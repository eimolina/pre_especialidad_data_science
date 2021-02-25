# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 19:44:50 2020

@author: ISAAC
"""

# import pandas as pd
# import os
import re
import time
import math
import urllib.parse
from datetime import date
import requests
# import queue
import threading
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import JavascriptException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
# from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from multiprocessing.pool import ThreadPool
W  = '\033[0m'  # white (normal)
R  = '\033[31m' # red
G  = '\033[32m' # green
O  = '\033[33m' # orange
B  = '\033[34m' # blue
P  = '\033[35m' # purple
resultado = []
class WebDriverSimanInnerJson:
    def __init__(self):
        pass
        
    def processItem(self, driver, art_key):
        today = date.today()
        item = []
        _key_ = art_key[21:len(art_key)-2]
        __producto__ = driver.execute_script("return __STATE__['Product:sae-productSearch-"+_key_+"']")
        if __producto__:
            categorias_str = __producto__["categories"]["json"][0]
            categorias = categorias_str[1:len(categorias_str)-2].split('/')
            pId = __producto__["productId"]
            psku = __producto__["productReference"]
            name = __producto__["productName"]
            desc = __producto__["description"]
            marca = __producto__["brand"]
            precio_lista_max = driver.execute_script("return __STATE__['$Product:sae-productSearch-"+_key_+".priceRange.listPrice']['highPrice']")
            precio_lista_min = driver.execute_script("return __STATE__['$Product:sae-productSearch-"+_key_+".priceRange.listPrice']['lowPrice']")
            precio_venta_max = driver.execute_script("return __STATE__['$Product:sae-productSearch-"+_key_+".priceRange.sellingPrice']['highPrice']")
            precio_venta_min = driver.execute_script("return __STATE__['$Product:sae-productSearch-"+_key_+".priceRange.sellingPrice']['lowPrice']")
            genero = None
            modelo = None
            for pindex in range(len(__producto__["properties"])):
                __property__ = driver.execute_script("return __STATE__['Product:sae-productSearch-"+_key_+".properties."+str(pindex)+"']")
                if __property__["name"] == "Género":
                    genero = __property__["values"]["json"][0]
                if __property__["name"] == "Modelo":
                    modelo = __property__["values"]["json"][0]
            item.append(today)
            item.append("SIMAN")
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
        return item
        
def getPagedLink(link,currentPage):
    if "?" in link:
        return link+'&page='+str(currentPage)
    else:
        return link+'?page='+str(currentPage)

class WebDriverProccessTask(threading.Thread):
    def __init__(self, cola, result, driver, handle, numero):
        threading.Thread.__init__(self)
        self.queue = cola
        self.driver = driver
        self.result = result
        self.handle = handle
        self.numero = numero
    def run(self):
        while True:
            link = self.queue.get()
            producto = None
            #Abre la url en el driver
            currentPage = 1
            link_t= getPagedLink(link,currentPage)
            self.driver.get(link_t)
            ExistNextPage = True
            while ExistNextPage:
                try:
                    articulos = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.vtex-product-summary-2-x-clearLink")))
                    #articulos = self.driver.find_elements_by_css_selector('a.vtex-product-summary-2-x-clearLink')
                    articulos_links = []
                    for x in articulos:
                        try:
                            href = x.get_attribute('href')
                            articulos_links.append(href)
                            print(G+link_t+ '->'+str(self.numero)+W )
                        except StaleElementReferenceException:
                            print(R+link_t+ '->'+str(self.numero)+W)
                    #articulos_links = [elem.get_attribute('href') for elem in articulos] 
                    for art_link in articulos_links:
                        art_key = urllib.parse.unquote(art_link)
                        producto = self.handle.processItem(self.driver,art_key)
                        if len(producto) > 0:
                            self.result.append(producto)  
                    nexpage = self.driver.find_elements_by_css_selector('div.vtex-search-result-3-x-buttonShowMore button') 
                    if len(nexpage) > 0:
                        currentPage+=1
                        self.driver.execute_script("return document.querySelector('.vtex-search-result-3-x-gallery').remove()")
                        self.driver.get(getPagedLink(link,currentPage))
                    else:
                        ExistNextPage = False
                except TimeoutException:
                    break
            self.queue.task_done()


def proccessThreadPool(link):
    chrome_options = Options()  
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1500,1000")
    driver = webdriver.Chrome(executable_path=r"./chromedriver.exe",options=chrome_options)
    while True:
        producto = None
        #Abre la url en el driver
        currentPage = 1
        link_t= getPagedLink(link,currentPage)
        driver.get(link_t)
        ExistNextPage = True
        while ExistNextPage:
            try:
                articulos = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.vtex-product-summary-2-x-clearLink")))
                articulos_links = []
                for x in articulos:
                    try:
                        href = x.get_attribute('href')
                        articulos_links.append(href)
                        print(G+link_t+ '->'+W )
                    except StaleElementReferenceException:
                        print(R+link_t+ '->'+W)
                #articulos_links = [elem.get_attribute('href') for elem in articulos] 
                for art_link in articulos_links:
                    art_key = urllib.parse.unquote(art_link)
                    today = date.today()
                    item = []
                    _key_ = art_key[21:len(art_key)-2]
                    __producto__ = driver.execute_script("return __STATE__['Product:sae-productSearch-"+_key_+"']")
                    if __producto__:
                        categorias_str = __producto__["categories"]["json"][0]
                        categorias = categorias_str[1:len(categorias_str)-2].split('/')
                        pId = __producto__["productId"]
                        psku = __producto__["productReference"]
                        name = __producto__["productName"]
                        desc = __producto__["description"]
                        marca = __producto__["brand"]
                        precio_lista_max = driver.execute_script("return __STATE__['$Product:sae-productSearch-"+_key_+".priceRange.listPrice']['highPrice']")
                        precio_lista_min = driver.execute_script("return __STATE__['$Product:sae-productSearch-"+_key_+".priceRange.listPrice']['lowPrice']")
                        precio_venta_max = driver.execute_script("return __STATE__['$Product:sae-productSearch-"+_key_+".priceRange.sellingPrice']['highPrice']")
                        precio_venta_min = driver.execute_script("return __STATE__['$Product:sae-productSearch-"+_key_+".priceRange.sellingPrice']['lowPrice']")
                        genero = None
                        modelo = None
                        for pindex in range(len(__producto__["properties"])):
                            __property__ = driver.execute_script("return __STATE__['Product:sae-productSearch-"+_key_+".properties."+str(pindex)+"']")
                            if __property__["name"] == "Género":
                                genero = __property__["values"]["json"][0]
                            if __property__["name"] == "Modelo":
                                modelo = __property__["values"]["json"][0]
                        item.append(today)
                        item.append("SIMAN")
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
                    if len(producto) > 0:
                        resultado.append(producto)  
                nexpage = driver.find_elements_by_css_selector('div.vtex-search-result-3-x-buttonShowMore button') 
                if len(nexpage) > 0:
                    currentPage+=1
                    driver.execute_script("return document.querySelector('.vtex-search-result-3-x-gallery').remove()")
                    driver.get(getPagedLink(link,currentPage))
                else:
                    ExistNextPage = False
            except TimeoutException:
                break

def web_driver_process_inner_json(links_categorias, container_queue):
    product_result = []
    for i in range(3): #NUMERO DE HILOS
        chrome_options = Options()  
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1500,1000")
        driver = webdriver.Chrome(executable_path=r"./chromedriver.exe",options=chrome_options)
        handle = WebDriverSimanInnerJson()
        hilo = WebDriverProccessTask(container_queue,product_result,driver,handle, i)
        hilo.setDaemon(True)
        hilo.start()  
        print("Started webdriver: --- "+str(i)+" --- from main")
    #Pone en cola las urls
    for cat in links_categorias:
        container_queue.put(cat)
    container_queue.join()
    return product_result