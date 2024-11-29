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
import gspread

print(sys.path)

# Get the current directory where main.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))

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
        
        # Download worksheet data before performing enrichment
        worksheet_data = download_worksheet_data()

        # Start enrichment operation
        perform_enrichment(worksheet_data, output_csv_file_path, enrichment_to_perform)

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
def perform_enrichment(worksheet, output_csv_file_path: str, enrichment_to_perform: str, save_interval=10):
    print("Starting enrichment...")

    # Get all the values from the worksheet
    rows = worksheet.get_all_values()
    
    # Get header row and create a mapping of column names to indices
    headers = rows[0]
    column_mapping = {header: idx + 1 for idx, header in enumerate(headers)}
    print("Found columns:", column_mapping)

    # Convert worksheet data to list of dictionaries using header row
    data = [dict(zip(headers, row)) for row in rows[1:]]

    # Initialize a new Selenium WebDriver session with options
    driverp = webdriver.Chrome(options=chrome_options)

    for index, row in enumerate(data):
        print(f"\nProcessing row {index + 2}")  # +2 because index starts at 0 and we skip header
        time.sleep(2.85 + 1.5*random.random())
        queries = get_queries(row)

        for scrape in queries["Scrape packages"]:
            utils.detect_reCAPTCHA(driverp)

            try:
                link = scrapes.google_search_scrape(driverp, scrape["query"])
                linkedin_link = link if scrape["name"] == "FounderLinkedIn" else linkedin_link
                crunchbase_link = link if scrape["name"] == "Crunchbase" else crunchbase_link
                print(f"Scraped query: {scrape['query']}")

                if enrichment_to_perform.lower() == "s" and scrape["name"] == "Crunchbase":
                    print("Crunchbase Scrape")
                    description = scrapes.scrape_crunchbase_description(driverp, crunchbase_link)
                    stage = scrapes.scrape_crunchbase_stage(driverp, crunchbase_link)
                    funding_date = scrapes.scrape_crunchbase_dateLatestFunding(driverp, crunchbase_link)
                    
                    # Create updates using column mapping
                    updates = [
                        ("Industry/Description", description),
                        ("Stage", stage),
                        ("Last Funding Date", funding_date),
                        ("LinkedIn", linkedin_link)
                    ]

                    for column_name, value in updates:
                        if column_name in column_mapping:
                            try:
                                current_row = index + 2  # +2 because index starts at 0 and we skip header
                                column = column_mapping[column_name]
                                print(f"Updating {column_name} at row {current_row}, column {column} with: {value}")
                                worksheet.update_cell(current_row, column, value)
                                time.sleep(1)  # Avoid rate limits
                            except Exception as e:
                                print(f"Error updating {column_name}: {e}")
                        else:
                            print(f"Warning: Column '{column_name}' not found in sheet")

                elif enrichment_to_perform.lower() == "i":
                    updates = [
                        ("Partner", scrape["link"]),
                        ("VC Firm", row["VC Firm"])
                    ]

                    for column_name, value in updates:
                        if column_name in column_mapping:
                            try:
                                current_row = index + 2
                                column = column_mapping[column_name]
                                print(f"Updating {column_name} at row {current_row}, column {column} with: {value}")
                                worksheet.update_cell(current_row, column, value)
                                time.sleep(1)  # Avoid rate limits
                            except Exception as e:
                                print(f"Error updating {column_name}: {e}")
                        else:
                            print(f"Warning: Column '{column_name}' not found in sheet")

            except Exception as e:
                print(f"Error during scraping/updating: {e}")
                continue
            
    # Close the driver
    driverp.quit()

def get_queries(row_data):

    # Queries stored in a dictionary
    queries = {
        "FounderLinkedIn": f"site:linkedin.com/in/ {row_data['Startup']}, {row_data['HQ Location (World)']},founder, co-founder, co founder, ceo",
        "CompanyLinkedIn": f"site:linked   in.com/in/ {row_data['Startup']}, {row_data['HQ Location (World)']}, company",
        "Website": f"{row_data['Startup']}, {row_data['Industry/Description']}",
        "Crunchbase": f"site:crunchbase.com {row_data['Startup']}",
        "PartnerLinkedIn": f"site:linkedin.com/in/ {row_data['VC Firm']}, {row_data['Partner']}, partner"
    }

    # Scrape packages stored in a list of dictionaries
    scrape_packages = [
        {"name": "FounderLinkedIn", "query": queries["FounderLinkedIn"], "link": ""},
        {"name": "Crunchbase", "query": queries["Crunchbase"], "link": ""}
    ]
    return {"Queries": queries, "Scrape packages": scrape_packages}

def download_worksheet_data():
    # Connect to Google Sheets
    gc = gspread.oauth(
        credentials_filename=f'{current_dir}/gspread/credentials.json'
    )
    sh = gc.open("LifeX Lead Generation")
    worksheet_data = sh.worksheet("Scrape Enrichment")
    return worksheet_data

def upload_enriched_data(action_elected, worksheet, row_data, crunchbase_link, linkedin_link):
    # Upload enriched data to the worksheet
    if action_elected == "s":    
        # Startup output:
        results.append({
        'Startup': row_data["Raw data"]["startup"],
        'Founding date': row_data["Raw data"]["founding_date"],
        'HQ Location (World)': row_data["Raw data"]["location"],
        'Industry/description': row_data["Raw data"]["company_description"],
        'Crunchbase': crunchbase_link,
        'Founder LinkedIn': linkedin_link,
        'Stage': row_data["Raw data"]["company_stage"],
        'Last funding date': row_data["Raw data"]["last_funding_date"]
        })
        print(f"{row_data['Raw data']['startup']}, Founder LinkedIn: {scrape['link']}")

    if action_elected == "i":
        #Investor output:
        results.append({
            'Partner': scrape["link"],
            'Firm': row_data["Raw data"]["firm"]
        })
        print(f"{row_data['Raw data']['firm']}, Partner LinkedIn: {scrape['link']}")

choose_operation()