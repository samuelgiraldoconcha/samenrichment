from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random
import subprocess
from . import utils
from urllib.parse import quote
#from . import models
import multiprocessing

def google_search_scrape(driverp, query):
    # 30% chance to scroll
    if random.random() < 0.3:
        driverp.execute_script(f"window.scrollTo(0, {random.randint(100, 500)})")
        time.sleep(0.5 + random.random())
    
    search_params = [
    "?q=",
    "?query=",
    "?search="
    ]

    # Randomly choose search param
    search_param = random.choice(search_params)

    search_query = quote(query)
    driverp.get(f"https://www.google.com/search{search_param}{search_query}")
    time.sleep(2)

    element = driverp.find_element(By.CSS_SELECTOR, 'a[jsname="UWckNb"]')
    scraped_link = element.get_attribute('href')
    print(f'Link: {scraped_link}')
    return scraped_link

#Scrape company info from crunchbase, needs a crunchbase link
def scrape_crunchbase_dateLatestFunding(driverp, scrape_link):
    print("Scrape Date of latest funding")
    financials_url = scrape_link + '/company_financials'
    driverp.get(financials_url)
    
    if driverp.find_elements(By.CSS_SELECTOR, 'div.g-recaptcha'):
        utils.play_alert_sound()
        print("reCAPTCHA detected. Please complete the CAPTCHA manually.")
        input("Press Enter after completing the CAPTCHA...")
        driverp.refresh()
        time.sleep(2.85 + 1.5*random.random())
    
    # Add random delay after page load
    time.sleep(0.4+0.5*random.random())    
    # Simulate human-like scrolling
    scroll_height = random.randint(100, 300)
    driverp.execute_script(f"window.scrollTo(0, {scroll_height})")

    # Define all CSS selectors
    selectors = [
        '#mat-tab-nav-panel-0 > div > full-profile > page-centered-layout.overview-divider.ng-star-inserted > div > row-card > div > div:nth-child(2) > profile-section > section-card > mat-card > div.section-content-wrapper > phrase-list-card:nth-child(1) > obfuscation > markup-block > field-formatter:nth-child(10) > a',
        '#mat-tab-nav-panel-0 > div > full-profile > page-centered-layout.overview-divider.ng-star-inserted > div > row-card > div > div:nth-child(2) > profile-section > section-card > mat-card > div.section-content-wrapper > div > obfuscation-cta > phrase-list-card:nth-child(1) > obfuscation > obfuscation-cta > markup-block > field-formatter:nth-child(12) > a',
        '#mat-tab-nav-panel-0 > div > full-profile > page-centered-layout.overview-divider.ng-star-inserted > div > row-card > div > div:nth-child(2) > profile-section > section-card > mat-card > div.section-content-wrapper > phrase-list-card:nth-child(1) > obfuscation > markup-block > field-formatter:nth-child(8) > a',
        '#mat-tab-nav-panel-0 > div > full-profile > page-centered-layout.overview-divider.ng-star-inserted > div > row-card > div > div:nth-child(2) > profile-section > section-card > mat-card > div.section-content-wrapper > phrase-list-card:nth-child(1) > obfuscation > markup-block > field-formatter:nth-child(10) > a'
    ]

    funding_date = ""
    for selector in selectors:
        try:
            funding_date = driverp.find_element(By.CSS_SELECTOR, selector).text
            if funding_date:  # If we found a date, break the loop
                break
        except:
            continue

    print(funding_date)
    return funding_date

def scrape_crunchbase_description(driverp, scrape_link):
    print("Description")
    driverp.get(scrape_link)

    if driverp.find_elements(By.CSS_SELECTOR, 'div.g-recaptcha'):
        utils.play_alert_sound()
        print("reCAPTCHA detected. Please complete the CAPTCHA manually.")
        input("Press Enter after completing the CAPTCHA...")
        driverp.refresh()
        time.sleep(2.85 + 1.5*random.random())

    # Add random delay after page load
    time.sleep(0.4+0.5*random.random())    
    # Simulate human-like scrolling
    scroll_height = random.randint(100, 300)
    driverp.execute_script(f"window.scrollTo(0, {scroll_height})")

    description = driverp.find_element(By.CSS_SELECTOR, '#mat-tab-nav-panel-0 > div > full-profile > page-centered-layout.overview-divider.ng-star-inserted > div > row-card > div > div:nth-child(1) > profile-section > section-card > mat-card > div.section-content-wrapper > description-card > div > span').text
    print(description)
    return description

def scrape_crunchbase_stage(driverp, scrape_link):
    print("Stage")
    driverp.get(scrape_link)

    if driverp.find_elements(By.CSS_SELECTOR, 'div.g-recaptcha'):
        utils.play_alert_sound()
        print("reCAPTCHA detected. Please complete the CAPTCHA manually.")
        input("Press Enter after completing the CAPTCHA...")
        driverp.refresh()
        time.sleep(2.85 + 1.5*random.random())

    # Add random delay after page load
    time.sleep(0.4+0.5*random.random())    
    # Simulate human-like scrolling
    scroll_height = random.randint(100, 300)
    driverp.execute_script(f"window.scrollTo(0, {scroll_height})")

    stage = driverp.find_element(By.CSS_SELECTOR, '#mat-tab-nav-panel-0 > div > full-profile > page-centered-layout.overview-divider.ng-star-inserted > div > row-card > div > div:nth-child(1) > profile-section > section-card > mat-card > div.section-content-wrapper > fields-card > ul > li:nth-child(3) > label-with-icon > span > field-formatter > a').text
    print(stage)
    return stage

# def scrape_linkedin_no_session(driverp, scrape_link):
#     #base-contextual-sign-in-modal > div > section > button > icon > svg
#     #main-content > section.core-rail.mx-auto.papabear\:w-core-rail-width.mamabear\:max-w-\[790px\].babybear\:max-w-\[790px\] > div > section.core-section-container.core-section-container--with-border.border-b-1.border-solid.border-color-border-faint.py-4.text-color-text > div > p
#     print(f'Link: {scrape_link}')
#     press_button(driverp,scrape_link,"base-contextual-sign-in-modal > div > section > button > icon > svg")
#     time.sleep(2)
#     description_tag = driverp.find_element(By.CSS_SELECTOR, "[data-test-id='about-us__description']")
#     description = description_tag.text.strip()
#     print(f'Decription:{description}')
#     return description

def press_button(driver, url, tag):
    print("Button")
    try:
        # Navigate to the provided URL
        driver.get(url)
        
        # Wait until the button is clickable and then click it
        button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, tag))
        )
        button.click()
        print("Button clicked successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        