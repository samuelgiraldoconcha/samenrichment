from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
import subprocess
from . import utils
#from . import models

# Iterate over each row in the DataFrame
def entire_enrichment(file, output, driverp, output_csv_file_path: str, save_interval=10):
    
    print("Starting scrape...")

    # Prevent sleep of screen so the scrape doesn't stop because the screen starts sleeping.
    #utils.prevent_sleep(3600)
    last_save_time = time.time()

    # Iterate over each row in the DataFrame
    for index, row in file.iterrows():
        startup = row['Startup']
        description = row['Industry/description']
        location = row['HQ Location (World)']
        
        queryLinkedIn = f"site:linkedin.com/in/ {startup}, {location}, founder"
        #queryWebsite = f"{startup}, {description}"
        #queryCrunchbase = f"site:crunchbase.com, {startup}, {description}"

        scrapeLinkedIn = [queryLinkedIn, ""]
        #scrapeWebsite = [queryWebsite, ""]
        #scrapeCrunchbase = [queryCrunchbase, ""]

        #scrapes = [scrapeLinkedIn, scrapeWebsite]
        scrapes = [scrapeLinkedIn]

        for scrape in scrapes:
            search_query = '+'.join(scrape[0].split())
            driverp.get(f"https://www.google.com/search?q={search_query}")
            time.sleep(2)

            if driverp.find_elements(By.CSS_SELECTOR, 'div.g-recaptcha'):
                utils.play_alert_sound()
                print("reCAPTCHA detected. Please complete the CAPTCHA manually.")
                input("Press Enter after completing the CAPTCHA...")
                driverp.refresh()
                time.sleep(5)

            try:
                element = driverp.find_element(By.CSS_SELECTOR, 'a[jsname="UWckNb"]')
                scrape[1] = element.get_attribute('href')
                print(scrape[1])

                if scrape == scrapeCrunchbase:
                    crunchbase_results = scrape_crunchbase(driverp,scrape[1])
                    funding_stage = crunchbase_results[0]
                    funding_date = crunchbase_results[1]

            except Exception as e:
                output.append({
                    'Query': scrape[0],
                    'URL': f"Error fetching result: {e}"
                })
                print(f"Error fetching results for query '{scrape[0]}': {e}")

        #TODO: Manage different appends according to exclude/include.
        output.append({
            'Startup': startup,
            'LinkedIn': scrapeLinkedIn[1],
        })
        print(f"{startup}, LinkedIn, Website")

        last_save_time = utils.save_results_periodically(output, last_save_time, save_interval, output_csv_file_path)

    utils.save_results_periodically(output, last_save_time, 0, output_csv_file_path)

#Scrape company info from crunchbase, needs a crunchbase link
def scrape_crunchbase(driverp,scrape_link):
    financials_url = scrape_link + '/company_financials'
    driverp.get(financials_url)
    time.sleep(3)

    financial_signals = ["pre-seed", "seed", 'series a', 'series b', 'series c', 'series d', 'series e', 'series f', 'ipo', 'acquired']
    fund_signal = None
    funding_date = None

    try:
        page_text = driverp.find_element(By.TAG_NAME, 'body').text.lower()
        for signal in financial_signals:
            if signal in page_text:
                fund_signal = signal.capitalize()
                break

        # Now scrape the date for the latest funding stage (assuming it's near the funding stage in the HTML)
        if fund_signal:
            date_element = driverp.find_element(By.CSS_SELECTOR, '#mat-tab-nav-panel-0 > div > full-profile > page-centered-layout.overview-divider.ng-star-inserted > div > row-card > div > div:nth-child(2) > profile-section > section-card > mat-card > div.section-content-wrapper > div > obfuscation-cta > phrase-list-card:nth-child(1) > obfuscation > obfuscation-cta > markup-block > field-formatter:nth-child(12) > a')
            funding_date = date_element.text.strip()
            print(f"Date of latest funding: {funding_date}")

        if not fund_signal:
            print(f"No financial data found on: {financials_url}")

    except Exception as e:
        print(f"Error fetching financial data: {e}")
    return [fund_signal, funding_date]
