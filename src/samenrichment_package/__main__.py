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

# Choose operation when running the script
def choose_operation():

    operation_to_perform = input("\nOperation to perform: \n\nEnrichment (Press 'E') \n\nPrevent sleep (Press 'P') \n\nYour selection: ")

    if operation_to_perform.lower() == "e":

        enrichment_to_perform = input("Enrichment to perform: \n\nStartup (Press 'S') \nInvestor (Press 'I') \n\nYour selection: ")
        
        # Download worksheet data before performing enrichment
        worksheet_data = download_worksheet_data()

        # Start enrichment operation
        perform_enrichment(worksheet_data, enrichment_to_perform)

        utils.play_alert_sound()

    elif operation_to_perform.lower() == "p":
        utils.prevent_sleep(6000)

    else:
        print("Invalid operation") 

# Iterate over each row in the DataFrame
def perform_enrichment(worksheet, enrichment_to_perform: str, save_interval=10):
    print("Starting enrichment...")

    chrome_options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")

    #proxy = rand_proxy()
    #chrome_options.add_argument(f"--proxy-server={proxy}")

    #TODO: Decide wether to change to request based or keep selenium based.
    #TODO: Change all places with driverp, to browser.
    browser = webdriver.Chrome(options=chrome_options)
    rows = worksheet.get_all_values()
    
    # Get header row and create a mapping of column names to indices
    headers = rows[0]
    column_mapping = {header: idx + 1 for idx, header in enumerate(headers)}
    print("Found columns:", column_mapping)

    # Convert worksheet data to list of dictionaries using header row
    data = [dict(zip(headers, row)) for row in rows[1:]]
    for index, row in enumerate(data):
        print(f"\nProcessing row {index + 2}")  # +2 because index starts at 0 and we skip header
        time.sleep(2.85 + 1.5*random.random())
        queries = get_queries(row)

        for scrape in queries["Scrape packages"]:
            utils.detect_reCAPTCHA(browser)
            link = scrapes.google_search_scrape(browser, scrape["query"])
            description = ""
            stage = ""
            funding_date = ""

            print(f"Scraped query: {scrape['query']}")
            if scrape["name"] == "FounderLinkedIn":
                linkedin_link = link
                updates = [
                    ("LinkedIn", linkedin_link)
                ]
                upload_enriched_data(updates, column_mapping, index, worksheet)
        
            elif scrape["name"] == "Crunchbase":
                print("Crunchbase Scrape")
                crunchbase_link = link
                try:        
                    description = scrapes.scrape_crunchbase_description(browser, crunchbase_link)
                    stage = scrapes.scrape_crunchbase_stage(browser, crunchbase_link)
                    funding_date = scrapes.scrape_crunchbase_dateLatestFunding(browser, crunchbase_link)
                except Exception as e:
                    print(f"Error during scraping/updating: {e}")
                    continue

                # Define the columns to update and their corresponding values
                # Format: (Google Sheet Column Name, Value to Insert)
                updates = [
                    ("Industry/Description", description),
                    ("Stage", stage),
                    ("Last Funding Date", funding_date),
                    ("Crunchbase", crunchbase_link)
                ]
                upload_enriched_data(updates, column_mapping, index, worksheet)
            
    # Close the driver
    browser.quit()

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

def upload_enriched_data(updates, column_mapping, index, worksheet):
 # Iterate through each column update
    for column_name, value in updates:
        # Check if the column exists in our sheet's header mapping
        if column_name in column_mapping:
            try:
                # Calculate the actual row number in the sheet
                # Add 2 because:
                # +1 for zero-based index
                # +1 for header row at the top
                current_row = index + 2
                
                # Get the column letter/number from our mapping
                column = column_mapping[column_name]
                
                # Log the update operation for debugging
                print(f"Updating {column_name} at row {current_row}, column {column} with: {value}")
                
                # Update the specific cell in Google Sheets
                worksheet.update_cell(current_row, column, value)
            except Exception as e:
                print(f"Error updating {column_name}: {e}")
        else:
            print(f"Warning: Column '{column_name}' not found in sheet")

def rand_proxy():
    return proxy

print(sys.path)

# Get the current directory where main.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))

choose_operation()