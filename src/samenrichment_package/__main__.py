from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
from .utils import utils, scrapes
import sys
import os
import random

print(sys.path)

# Get the current directory where main.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Now read the CSV file
df = pd.read_csv(f"{current_dir}/input_files/template.csv", comment='#')

# Replace NaN with empty strings
df.fillna('', inplace=True)

# List to store results
results = []
output_csv_file_path = f"{current_dir}/output_files/search_results.csv"

# Choose operation when running the script
def choose_operation():

    operation_to_perform = input("\nOperation to perform: \n\nEnrichment (Press 'E') \nClean results (Press 'C') \nPrevent sleep (Press 'P') \n\nYour selection: ")

    if operation_to_perform.lower() == "e":

        # Start enrichment operation.
        main_enrichment(df, results, set_chrome_options(), output_csv_file_path)

        # Clean the results automatically
        cleaned_file_path = f'{current_dir}/output_files/cleaned_search_results.csv'
        utils.clean_csv(output_csv_file_path, cleaned_file_path)
        utils.play_alert_sound()

        # Close the driver
        start_chrome_driver().quit()

    # If the scrape gets interrupted, this options is useful for cleaning the results that the user got so far.
    elif operation_to_perform.lower() == "c":
        cleaned_file_path = f'{current_dir}/output_files/cleaned_search_results.csv'
        utils.clean_csv(output_csv_file_path, cleaned_file_path)

    elif operation_to_perform.lower() == "p":
        utils.prevent_sleep(6000)

    else:
        print("Invalid operation") 



# Iterate over each row in the DataFrame
def main_enrichment(file, output, output_csv_file_path: str, save_interval=10):
    
    print("Starting scrape...")

    # Initialize a new Selenium WebDriver session with options
    driverp = start_chrome_driver()

    try:
        last_save_time = time.time()

        # Add pause flag
        is_paused = False

        # Iterate over each row in the DataFrame
        for index, row in file.iterrows():

            time.sleep(2.85 + 1.5*random.random())

            # Variables of the rows
            startup = row['Startup']
            company_description = row['Industry/description']
            founding_date = row['Founding date']
            location = row['HQ Location (World)']
            company_stage = row['Stage']
            founder = row['Founder'] if 'Founder' in row else ""
            firm = row['VC Firm'] if 'VC Firm' in row else ""
            partner = row["Partner"] if "Partner" in row else ""
            
            # Queries
            queryFounderLinkedIn = f"site:linkedin.com/in/ {startup}, {location},founder, co-founder, co founder, ceo"
            queryCompanyLinkedIn = f"site:linkedin.com/in/ {startup}, {location}, company"
            queryWebsite = f"{startup}, {company_description}"
            queryCrunchbase = f"site:crunchbase.com {startup}"
            queryPartnerLinkedIn = f"site:linkedin.com/in/ {firm}, {partner}, partner"

            # Scrape packages
            scrapeFounderLinkedIn = [queryFounderLinkedIn, ""]
            scrapeCompanyLinkedIn = [queryCompanyLinkedIn, ""]
            scrapeWebsite = [queryWebsite, ""]
            scrapeCrunchbase = [queryCrunchbase, ""]
            scrapePartnerLinkedIn = [queryPartnerLinkedIn, ""]

            # Choose which scrape packages to use
            scrapes = [scrapeFounderLinkedIn, scrapeCrunchbase]

            # Outputs:
            funding_date = ""
        
            # Scrape each query in scrapes
            for scrape in scrapes:

                if driverp.find_elements(By.CSS_SELECTOR, 'div.g-recaptcha'):
                    utils.play_alert_sound()
                    print("reCAPTCHA detected. Please complete the CAPTCHA manually.")
                    input("Press Enter after completing the CAPTCHA...")
                    driverp.refresh()
                    time.sleep(2.85 + 1.5*random.random())

                # Assigns link to empty element of list scrape[n].
                try:

                    # Scrape google search link
                    scrape[1] = scrapes.google_search_scrape(driverp, scrape[0])

                    if scrape == scrapeCrunchbase:
                        print("Crunchbase Scrape")
                        company_description = scrapes.scrape_crunchbase_description(driverp,scrape[1])
                        company_stage = scrapes.scrape_crunchbase_stage(driverp,scrape[1])
                        funding_date = scrapes.scrape_crunchbase_dateLatestFunding(driverp,scrape[1])
                except Exception as e:
                    # output.append({
                    #     'Query': scrape[0],
                    #     'URL': f"Error fetching result: {e}"
                    # })
                    # print(f"Error fetching results for query '{scrape[0]}': {e}")
                    print("No link assigned")

            # Startup output:
            output.append({
                'Startup': startup,
                'Founding date': founding_date,
                'HQ Location (World)': location,
                'Industry/description': company_description,
                'Founder LinkedIn': scrapeFounderLinkedIn[1],
                'Stage': company_stage,
                'Last funding date': funding_date
            })
            print(f"{startup}, Founder LinkedIn: {scrapeFounderLinkedIn[1]}")

            #Investor output:
            # output.append({
            #     'Partner': scrapePartnerLinkedIn[1],
            #     'Firm': firm
            # })
            # print(f"{firm}, Partner LinkedIn: {scrapePartnerLinkedIn[1]}")

            last_save_time = utils.save_results_periodically(output, last_save_time, save_interval, output_csv_file_path)

        utils.save_results_periodically(output, last_save_time, 0, output_csv_file_path)
    finally:
        # Make sure to terminate the prevent_sleep process when done
        scrapes.prevent_sleep_process.terminate()
        scrapes.prevent_sleep_process.join()


def start_chrome_driver():
    return webdriver.Chrome(options=set_chrome_options())
def set_chrome_options():
    chrome_options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    return chrome_options