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
from core import utecdatacore as PROYECT_CORE
from core import config
#from bs4 import BeautifulSoup

curacaoqueue = queue.Queue();
caps = DesiredCapabilities().CHROME
caps["pageLoadStrategy"] = "eager"  #['eager','normal','none']
principal_driver = webdriver.Chrome(desired_capabilities=caps, executable_path=r"./chromedriver.exe")
temp_departamento = None
today = date.today()
principal_driver.get('https://www.lacuracaonline.com/elsalvador/')
try:
    element = WebDriverWait(principal_driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.action.nav-toggle.desktop.enabled")))
    hover = ActionChains(principal_driver).move_to_element(element)
    hover.perform()
    elem_a_categories = principal_driver.find_elements(By.CSS_SELECTOR,"li.level2.ui-menu-item > a");
    links_categories = [elem.get_attribute('href') for elem in elem_a_categories] 
    cleaned_links = [i for i in links_categories if "yomequedoencasa" not in i and "promociones" not in i]
    products = PROYECT_CORE.web_driver_process_individual_items(cleaned_links,principal_driver,curacaoqueue)
    df = pd.DataFrame(products, columns=config.columns)
    df.to_csv('lacuracao.csv', encoding='utf-8-sig')
finally:
    principal_driver.quit()
                

          

