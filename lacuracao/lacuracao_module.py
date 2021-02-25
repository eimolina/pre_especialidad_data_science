# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 19:44:50 2020

@author: ISAAC
"""

# import pandas as pd
# import os
# import re
# import time
# import math
# import urllib.parse
from datetime import date
import requests
# import queue
import threading
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import JavascriptException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
# from selenium.webdriver.common.action_chains import ActionChains
    
class BeautifulSoupCuracaoItem:
    def __init__(self):
        pass
        
    def processItem(self,content,data):
        today = date.today()
        product = []
        soup = BeautifulSoup(content,'html.parser')
        table_attributes = soup.find('table',attrs={'id':'product-attribute-specs-table'})
        product_info_main = soup.find('div',attrs={'class':'product-info-main'})
        #breadcrumbs = soup.find('div',attrs={'class':'breadcrums'})
        #categorias = breadcrumbs.find_all('li',attrs={'class':'item category'})
        marca = table_attributes.find('td',attrs={'data-th':'Marca'})
        modelo = table_attributes.find('td',attrs={'data-th':'Modelo'})
        precio = product_info_main.find('span',attrs={'class':'price'})
        precio_especial = product_info_main.find('span',attrs={'class':'special-price'})
        if precio_especial:
            precio_especial = precio_especial.find('span',attrs={'class':'price'})
        nombre = product_info_main.find('span',attrs={'itemprop':'name'})
        pid = product_info_main.find('div',attrs={'itemprop':'sku'})
        product.append(today)
        product.append('LACURACAO')
        product.append(data[1][1].upper().strip())
        product.append(data[1][1].upper().strip())
        product.append(data[1][2].upper().strip())
        product.append(pid.text.upper().strip() if pid else 'N/A')
        product.append(pid.text.upper().strip() if pid else 'N/A')
        product.append(nombre.text if nombre else 'N/A')
        product.append('N/A') #DESCRIPCION
        product.append(marca.text.upper().strip() if marca else 'N/A')
        product.append(float(precio.text.lstrip('$').replace(',','')) if precio else 0.00) #PRECIO LISTA MAXIMO
        product.append(float(precio.text.lstrip('$').replace(',','')) if precio else 0.00) #PRECIO LISTA MINIMO
        if precio_especial:
            product.append(float(precio_especial.text.lstrip('$').replace(',','')) if precio_especial else 0.00) #PRECIO VENTAMAX
            product.append(float(precio_especial.text.lstrip('$').replace(',','')) if precio_especial else 0.00) #PRECIO VENTAMIN
        else:
            product.append(float(precio.text.lstrip('$').replace(',','')) if precio else 0.00) #PRECIO VENTA MAXIMO
            product.append(float(precio.text.lstrip('$').replace(',','')) if precio else 0.00) #PRECIO VENTA MINIMO
        
        product.append(modelo.text.upper().strip() if modelo else 'N/A')
        product.append('N/A') #GENERO
        return product
    
        

class WebDriverProccessTask(threading.Thread):
    def __init__(self, cola, result, driver, handle):
        threading.Thread.__init__(self)
        self.queue = cola
        self.driver = driver
        self.result = result
        self.handle = handle
    def run(self):
        while True:
            data = self.queue.get()
            producto = None
            try:
                req = requests.get(data[0])
                producto = self.handle.processItem(req.text,data)
                #Coloca el codigo fuente en la salida
                self.result.append(producto)
                #avisa que la tarea termino
                self.queue.task_done()
            except JavascriptException: 
                print('ended thread') 
            finally:
                print(self.queue.qsize())
                
    
def web_driver_process_individual_items(links_categorias, driver, container_queue):
    products = []
    for i in range(3): #NUMERO DE HILOS
        handle = BeautifulSoupCuracaoItem()
        hilo = WebDriverProccessTask(container_queue,products,None,handle)
        hilo.setDaemon(True)
        hilo.start()        
        print("Started webdriver: --- "+str(i)+" --- from main")
    for cat in links_categorias:
        #if "televisores" in cat:
        currentPage = 1
        pages = 1
        ExistNextPage = True
        while ExistNextPage:
            driver.get(cat+'?p='+str(currentPage))
            try:
                driver.find_element(By.CSS_SELECTOR,".message.info.empty")
                ExistNextPage = False
            except NoSuchElementException:    
                elem_a_products = driver.find_elements(By.CSS_SELECTOR,"a.product")
                breadcrumbs = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.breadcrumbs .item:not(.home) *")))
                categorias = [elem.get_attribute('innerHTML') for elem in breadcrumbs]
                links_products = [elem.get_attribute('href') for elem in elem_a_products] 
                for item in links_products:
                    data = [item, categorias]
                    container_queue.put(data)     
                
                pages_items = driver.find_elements(By.CSS_SELECTOR,"ul.pages-items")
                if pages_items:
                    pages = len(pages_items[0].find_elements_by_tag_name('li')) -1
                if currentPage < pages:
                    currentPage += 1
                else:
                    ExistNextPage = False
                    
    container_queue.join()
    return products