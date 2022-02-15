from dataclasses import dataclass
from lib2to3.pgen2 import driver
from multiprocessing.connection import wait
import re
import sys
from threading import Thread
from time import sleep
import traceback
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException,TimeoutException

import multiprocessing
import concurrent.futures

import pandas as pd


def get_hrefs(driver,i):
    driver.get(f"https://carsandbids.com/past-auctions/?page={i}")
    hrefs = []
    WebDriverWait(driver,20).until(EC.presence_of_element_located((By.CLASS_NAME, "auction-item ")))

    for i in range(1,51):
        try:
            a= driver.find_element(By.XPATH ,F"/html/body/div/div[2]/div[2]/div/ul[1]/li[{i}]/div[2]/div/a")
        except NoSuchElementException:
            return hrefs
        hrefs.append(a.get_attribute("href"))

    return hrefs

def add_to_df(driver,link,df):
    driver.get(link.split("-")[0])

    WebDriverWait(driver,20).until(EC.presence_of_element_located((By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[2]/dl[1]/dd[1]/a')))
 
    name = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[1]/div/div[1]/h1')
    make = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[2]/dl[1]/dd[1]/a')
    try:
        model = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[2]/dl[1]/dd[2]/a')
    except NoSuchElementException:
        return
    mileage = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[2]/dl[1]/dd[3]')
    title_status = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[2]/dl[1]/dd[5]')
    location = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[2]/dl[1]/dd[6]/a')
    engine = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[2]/dl[2]/dd[1]')
    drivetrain = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[2]/dl[2]/dd[2]')
    transmission = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[2]/dl[2]/dd[3]')
    body_style = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[2]/dl[2]/dd[4]')
    color = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[2]/dl[2]/dd[5]')
    state_of_acution = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[3]/div[1]/div/div/ul').text
    if "Cancelled" in state_of_acution:
        return
    price = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[6]/div/div/span')

    higlights_list = driver.find_elements(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[3]/div[2]/div/ul/li')
    flaws_list = driver.find_elements(By.XPATH, '/html/body/div/div[2]/div[5]/div[1]/div[3]/div[5]/div/ul/li')
    num_of_bids = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[3]/div[1]/div/div/ul/li[3]/span[2]')
    num_of_comments = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[3]/div[1]/div/div/ul/li[4]/span[2]')
    num_of_images = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[2]/div/div[1]/div/div[2]/div[2]/div[4]/div')
    if engine.text.find("Electric") != -1:
        return
    d_year = name.text.split(" ")[0]
    d_title = title_status.text.split(" ")[0]
    d_loc = location.text.split(",")[1].split(" ")[1]
    d_engine_size = engine.text.split(" ")[0]
    d_engine_type = engine.text.split(" ")[-1]
    d_trans_type = transmission.text.split(" ")[0]

    if len(transmission.text.split(" ")) != 1:
        d_trans_speed = transmission.text[transmission.text.find("(")+1:transmission.text.find(")")]
    else:
        d_trans_speed = None

    num_of_images = num_of_images.text[num_of_images.text.find("(")+1:num_of_images.text.find(")")]

    row = {
        'year' : d_year,
        'make' : make.text,
        'model': model.text,
        'mileage': mileage.text,
        'state of origin': d_loc,
        'engine size': d_engine_size,
        'engine type': d_engine_type,
        'drivetrain': drivetrain.text,
        'transmmision type': d_trans_type,
        'number of gears': d_trans_speed,
        'body_style': body_style.text,
        'color': color.text,
        'numberg of higlights': len(higlights_list),
        'number of flaws': len(flaws_list),
        'price': price.text,
        'num of bids': num_of_bids.text,
        'num of comments': num_of_comments.text,
        'num of images': num_of_images,
    }

    df.append(row)

driver = webdriver.Firefox(executable_path="./geckodriver")

data = []

for i in range(1,118):
    links = get_hrefs(driver,i)

    for link in links:
        try:
            add_to_df(driver,link,data)
        except NoSuchElementException as e:
            print(f"{link} - {e}")
        except TimeoutException:
            print(link, " not found")

    df = pd.DataFrame(data)

    df.to_csv(f"my_data_{i}.csv")
