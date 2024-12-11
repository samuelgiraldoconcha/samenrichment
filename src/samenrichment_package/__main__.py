from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import asyncio
import pandas as pd
import time
import random
import gspread
import os
import sys
from .utils import utils, scrapes
import httpx
from gspread.utils import ValueRenderOption


# Get the current directory where main.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))

def access_to_worksheet_data():
    # Connect to Google Sheets
    gc = gspread.oauth(
        credentials_filename=f'{current_dir}/gspread/credentials.json'
    )
    sh = gc.open("LifeX Lead Generation")
    worksheet_data = sh.worksheet("Scrape Enrichment")
    return worksheet_data

def update_table(worksheet):
    # 1. Get worksheet data
    # 2. Create a mapping of column names to indices.
    # 3. Convert worksheet data to list of dictionaries using header row
    rows = worksheet.get_all_values()
    headers = rows[0]
    column_mapping = {header: idx + 1 for idx, header in enumerate(headers)}
    print("Found columns:", column_mapping)
    data = [dict(zip(headers, row)) for row in rows[1:]]
    return data, column_mapping

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

async def start_context(contexts, browser, index):
    stop = index
    while index == stop:
        context = await browser.new_context(
            proxy = {
                "server" : "http://gate.smartproxy.com:7000",
                "username" : "sp5ncwtwdd",
                "password" : "1iY+leztcI8lS6dRu9"
            }
        )
        try:
            ip_page = await context.new_page()
            await ip_page.goto('https://httpbin.org/ip')
            ip_response = await ip_page.locator("pre").inner_text(timeout=5000)
            print(f"Context {index}: {ip_response}")
            if ip_response:
                contexts.append(context)
                index = index + 1
                ip_page.close()
            else:
                context.close()
         
        except Exception as ex:
            context.close()
            print(f"Error in context {index}: {ex}")

async def get_linkedin_link(contexts, index, row, column_mapping, worksheet):
    print(f"\nProcessing row {index + 2}")  # +2 because index starts at 0 and we skip header
    google_search_query = utils.get_queries(row)["Queries"]["FounderLinkedIn"]
    print(f"Ready GoogleSearch<>LinkedIn query: {google_search_query}")

    link = await scrapes.google_search_scrape(contexts, index, google_search_query, row["Startup"]) # LinkedIn scrape
    linkedin_col_idx = column_mapping.get("LinkedIn")
    cell_value = worksheet.cell(index + 2, linkedin_col_idx).value
    linkedin_link = link if not cell_value or cell_value.strip() == "" else cell_value
    updates = [
        ("LinkedIn", linkedin_link)
    ]
    upload_enriched_data(updates, column_mapping, index, worksheet)     

async def get_crunchbase_link(contexts, i, row, column_mapping, worksheet):

    print(f"\nProcessing row {i + 2}")  # +2 because index starts at 0 and we skip header
    # Random context generates new page.
    
    try:
        queries = get_queries(row)
        print("Ready page and queries")
    except:
        print("Failed at creating new page for scrape")

    asyncio.sleep(2.85 + 1.5 * random.random())
    for scrape in queries["Scrape packages"]:
        page = await contexts[i % 10].new_page()
        await utils.detect_reCAPTCHA(page)
        link = await scrapes.google_search_scrape(page, scrape["query"], row["Startup"])
        description = ""
        stage = ""
        funding_date = ""
        print(f"Scraped query: {scrape['query']}")

        # LinkedIn scrape
        if scrape["name"] == "FounderLinkedIn":
            linkedin_link = link if row["LinkedIn"] == "" else row["LinkedIn"]
            updates = [
                ("LinkedIn", linkedin_link)
            ]
            upload_enriched_data(updates, column_mapping, i, worksheet)



        # Crunchbase scrape
        elif scrape["name"] == "Crunchbase":
            print("Crunchbase Scrape")
            crunchbase_link = link if row["Crunchbase"] == "" else row["Crunchbase"]
            # try:
            #     description,= await scrapes.scrape_crunchbase_description(page, crunchbase_link) if row["Industry/Description"] == "" else row["Industry/Description"]
            #     stage = await scrapes.scrape_crunchbase_stage(page, crunchbase_link) if row["Stage"] == "" else row["Stage"]
            #     funding_date = await scrapes.scrape_crunchbase_dateLatestFunding(page, crunchbase_link) if row["Last Funding Date"] == "" else row["Last Funding Stage"]
            # except Exception as e:
            #     print(f"Error during scraping/updating: {e}")
            #     continue
            updates = [
                # ("Industry/Description", description),
                # ("Stage", stage),
                # ("Last Funding Date", funding_date),
                ("Crunchbase", crunchbase_link)
            ]
            upload_enriched_data(updates, column_mapping, i, worksheet)

async def perform_enrichment(worksheet, enrichment_to_perform: str, save_interval=10):
    print("Starting enrichment...")

    async with async_playwright() as p:
        table, column_mapping = update_table(worksheet)
        blanks_linkedin = [1]
        linkedin_col_idx = column_mapping.get("LinkedIn")
        blanks_crunchbase_link_ = [1]

        while len(blanks_linkedin) > 0:
            # Initialize the browser
            browser = await p.webkit.launch(headless=True)

            # Set up contexts with rotating IPs
            contexts = []
            tasks = [start_context(contexts, browser, i) for i in range(10)]
            await asyncio.gather(*tasks)
            print(f"Set up {len(contexts)} contexts.")

            # Start LinkedIn scrape session.
            tasks = [get_linkedin_link(contexts, i, row, column_mapping, worksheet) for i, row in enumerate(table)]
            await asyncio.gather(*tasks)

            # Count blank cells
            blanks_linkedin = []
            if linkedin_col_idx is None:
                raise ValueError("LinkedIn column not found in the worksheet headers!")

            for i, row in enumerate(table, start=2):  # Start from row 2 (after headers)
                cell_value = worksheet.cell(i, linkedin_col_idx).value
                if not cell_value or cell_value.strip() == "":
                    blanks_linkedin.append([i,linkedin_col_idx])

            print(f"\n\nBlank cells: {len(blanks_linkedin)}")

            # Close the browser
            await browser.close()

# Choose operation when running the script
async def main():

    operation_to_perform = input("\nOperation to perform: \n\nEnrichment (Press 'E') \n\nPrevent sleep (Press 'P') \n\nYour selection: ")

    if operation_to_perform.lower() == "e":

        enrichment_to_perform = input("Enrichment to perform: \n\nStartup (Press 'S') \nInvestor (Press 'I') \n\nYour selection: ")
        
        # Download worksheet data before performing enrichment
        worksheet_data = access_to_worksheet_data()

        # Start enrichment operation (using asyncio.run to handle async function)
        await asyncio.gather(perform_enrichment(worksheet_data, enrichment_to_perform))

        utils.play_alert_sound()

    elif operation_to_perform.lower() == "p":
        utils.prevent_sleep(6000)

    else:
        print("Invalid operation")

print(sys.path)


if __name__ == "__main__":
    asyncio.run(main())
