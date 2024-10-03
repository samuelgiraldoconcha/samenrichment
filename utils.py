from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
import subprocess
import pygame

def play_alert_sound():
    # Initialize Pygame mixer
    pygame.mixer.init()
    # Load the sound file
    pygame.mixer.music.load('alert_sound.wav')  # Replace with the path to your sound file
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # Wait for sound to finish playing
        pygame.time.Clock().tick(10)

def save_results_periodically(output, last_save_time, save_interval, output_csv_file_path='search_results.csv'):
    current_time = time.time()
    if current_time - last_save_time >= save_interval:
        results_df = pd.DataFrame(output)
        results_df.to_csv(output_csv_file_path, index=False)
        print(f"Results saved to {output_csv_file_path} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return current_time  # Update last_save_time
    return last_save_time  # No save, return the old last_save_time

# Iterate over each row in the DataFrame

def entire_enrichment(file, output, driverp, output_csv_file_path='search_results.csv', save_interval=10):

    last_save_time = time.time()

    # Iterate over each row in the DataFrame
    for index, row in file.iterrows():
        startup = row['Startup']
        industry = row['Industry']
        
        queryLinkedIn = f"site:linkedin.com/in/ {startup}, founder"
        queryWebsite = f"{startup}, {industry}"
        queryCrunchbase = f"site:crunchbase.com, {startup}, {industry}"

        scrapeLinkedIn = [queryLinkedIn, ""]
        scrapeWebsite = [queryWebsite, ""]
        scrapeCrunchbase = [queryCrunchbase, ""]

        scrapes = [scrapeLinkedIn, scrapeWebsite, scrapeCrunchbase]

        for scrape in scrapes:
            search_query = '+'.join(scrape[0].split())
            driverp.get(f"https://www.google.com/search?q={search_query}")
            time.sleep(2)

            if driverp.find_elements(By.CSS_SELECTOR, 'div.g-recaptcha'):
                play_alert_sound()
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
            'Website': scrapeWebsite[1],
            'Raised to Date': funding_stage if funding_stage else '',
            'Date of latest funding': funding_date if funding_date else ''
        })
        print(f"{startup}, {industry}, LinkedIn, Website, Crunchbase: {scrapeLinkedIn[1]}, {scrapeWebsite[1]}, {scrapeCrunchbase[1]}")

        last_save_time = save_results_periodically(output, last_save_time, save_interval, output_csv_file_path)

    save_results_periodically(output, last_save_time, 0, output_csv_file_path)

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
