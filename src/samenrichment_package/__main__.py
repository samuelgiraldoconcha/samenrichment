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
import pygame

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

chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
chrome_options.add_argument(f"user-agent={user_agent}")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")

# Choose operation when running the script
def choose_operation():

    operation_to_perform = input("\nOperation to perform: \n\nEnrichment (Press 'E') \nClean results (Press 'C') \nPrevent sleep (Press 'P') \n\nYour selection: ")

    if operation_to_perform.lower() == "e":

        enrichment_to_perform = input("Enrichment to perform: \n\nStartup (Press 'S') \nInvestor (Press 'I') \n\nYour selection: ")
        
        # Start enrichment operation.
        main_enrichment(df, output_csv_file_path, enrichment_to_perform)

        # Clean the results automatically
        cleaned_file_path = f'{current_dir}/output_files/cleaned_search_results.csv'
        print(f"Output CSV file path: {output_csv_file_path}")
        print(f"Cleaned CSV file path: {cleaned_file_path}")
        if os.path.getsize(output_csv_file_path) == 0:
            print("The CSV file is empty.")
            return
        utils.clean_csv(output_csv_file_path, cleaned_file_path)
        utils.play_alert_sound()

    # If the scrape gets interrupted, this options is useful for cleaning the results that the user got so far.
    elif operation_to_perform.lower() == "c":
        cleaned_file_path = f'{current_dir}/output_files/cleaned_search_results.csv'
        utils.clean_csv(output_csv_file_path, cleaned_file_path)

    elif operation_to_perform.lower() == "p":
        utils.prevent_sleep(6000)

    else:
        print("Invalid operation") 

# Iterate over each row in the DataFrame
def main_enrichment(file, output_csv_file_path: str, enrichment_to_perform: str, save_interval=10):
    
    print("Starting scrape...")

    # Initialize a new Selenium WebDriver session with options
    driverp = webdriver.Chrome(options=chrome_options)
    last_save_time = time.time()

    # Iterate over each row in the DataFrame
    for index, row in file.iterrows():

        time.sleep(2.85 + 1.5*random.random())

        # Extract row data with default values
        startup = row.get('Startup', '')
        company_description = row.get('Industry/description', '')
        founding_date = row.get('Founding date', '')
        location = row.get('HQ Location (World)', '')
        company_stage = row.get('Stage', '')
        founder = row.get('Founder', '')
        firm = row.get('VC Firm', '')
        partner = row.get('Partner', '')

        # Queries stored in a dictionary
        queries = {
            "FounderLinkedIn": f"site:linkedin.com/in/ {startup}, {location},founder, co-founder, co founder, ceo",
            "CompanyLinkedIn": f"site:linkedin.com/in/ {startup}, {location}, company",
            "Website": f"{startup}, {company_description}",
            "Crunchbase": f"site:crunchbase.com {startup}",
            "PartnerLinkedIn": f"site:linkedin.com/in/ {firm}, {partner}, partner"
        }

        # Scrape packages stored in a list of dictionaries
        scrape_packages = [
            {"name": "FounderLinkedIn", "query": queries["FounderLinkedIn"], "link": ""},
            {"name": "Crunchbase", "query": queries["Crunchbase"], "link": ""}
        ]

        # Outputs:
        funding_date = ""
    
        # Scrape each query in scrapes
        for scrape in scrape_packages:

            if driverp.find_elements(By.CSS_SELECTOR, 'div.g-recaptcha'):
                utils.play_alert_sound()
                print("reCAPTCHA detected. Please complete the CAPTCHA manually.")
                input("Press Enter after completing the CAPTCHA...")
                driverp.refresh()
                time.sleep(2.85 + 1.5*random.random())

            # Assigns link to empty element of list scrape[n].
            try:

                # Scrape google search link
                print(scrape["query"])
                scrape["result"] = scrapes.google_search_scrape(driverp, scrape["query"])

                if scrape["name"] == "Crunchbase":
                    print("Crunchbase Scrape")
                    company_description = scrapes.scrape_crunchbase_description(driverp,scrape["link"])
                    company_stage = scrapes.scrape_crunchbase_stage(driverp,scrape["link"])
                    funding_date = scrapes.scrape_crunchbase_dateLatestFunding(driverp,scrape["link"])
            except Exception as e:
                print("No link assigned")

            if enrichment_to_perform == "s":    
                # Startup output:
                results.append({
                'Startup': startup,
                'Founding date': founding_date,
                'HQ Location (World)': location,
                'Industry/description': company_description,
                'Founder LinkedIn': scrape_packages[0]["link"],
                'Stage': company_stage,
                'Last funding date': funding_date
                })
                print(f"{startup}, Founder LinkedIn: {scrape_packages[0]["link"]}")

            if enrichment_to_perform == "i":
                #Investor output:
                results.append({
                    'Partner': scrape_packages[1]["link"],
                    'Firm': firm
                })
                print(f"{firm}, Partner LinkedIn: {scrape_packages[1]["link"]}")
            
            last_save_time = utils.save_results_periodically(results, last_save_time, save_interval, output_csv_file_path)
            print("Empty results" if results == [] else "Results saved")

    # Save the final results
    utils.save_results_periodically(results, last_save_time, 0, output_csv_file_path)
    
    # Close the driver
    driverp.quit()

def enrichment_variables(row):
     # Extract row data with default values
    row_data = {
        'startup': row.get('Startup', ''),
        'company_description': row.get('Industry/description', ''),
        'founding_date': row.get('Founding date', ''),
        'location': row.get('HQ Location (World)', ''),
        'company_stage': row.get('Stage', ''),
        'founder': row.get('Founder', ''),
        'firm': row.get('VC Firm', ''),
        'partner': row.get('Partner', '')
    }

    # Queries stored in a dictionary
    queries = {
        "FounderLinkedIn": f"site:linkedin.com/in/ {row_data['startup']}, {row_data['location']},founder, co-founder, co founder, ceo",
        "CompanyLinkedIn": f"site:linkedin.com/in/ {row_data['startup']}, {row_data['location']}, company",
        "Website": f"{row_data['startup']}, {row_data['company_description']}",
        "Crunchbase": f"site:crunchbase.com {row_data['startup']}",
        "PartnerLinkedIn": f"site:linkedin.com/in/ {row_data['firm']}, {row_data['partner']}, partner"
    }

    # Scrape packages stored in a list of dictionaries
    scrape_packages = [
        {"name": "FounderLinkedIn", "query": queries["FounderLinkedIn"], "link": ""},
        {"name": "Crunchbase", "query": queries["Crunchbase"], "link": ""}
    ]
    return {"Raw data": row_data, "Queries": queries, "Scrape packages": scrape_packages}

choose_operation()