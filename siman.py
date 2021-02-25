# -*- coding: utf-8 -*-
"""
Created on Sun Aug 23 12:07:06 2020

@author: ISAAC
"""
import pandas as pd
import queue
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from datetime import date
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from siman import siman_module as PROYECT_CORE
from selenium.webdriver.chrome.options import Options
import config
import time

chrome_options = Options()  
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1500,1000")
simanqueue = queue.Queue();
principal_driver = webdriver.Chrome(executable_path=r"./chromedriver.exe",options=chrome_options)
today = date.today()
principal_driver.get('https://sv.siman.com/')
time.sleep(5)
try:
    element = principal_driver.find_element_by_class_name("vtex-menu-2-x-styledLinkContainer--title-menu-departament")
    hover = ActionChains(principal_driver).move_to_element(element)
    hover.perform()
    links_elementes = WebDriverWait(principal_driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "vtex-menu-2-x-styledLink--title-menu-sub-cat")))
    links_sv = [elem.get_attribute('href') for elem in links_elementes] 
    cleaned_links = [i for i in links_sv if i] 
    products = PROYECT_CORE.web_driver_process_inner_json(cleaned_links,simanqueue)
    df = pd.DataFrame(products, columns=config.columns)
    df.to_csv('siman.csv', encoding='utf-8-sig')
finally:
    principal_driver.quit()
                

          

