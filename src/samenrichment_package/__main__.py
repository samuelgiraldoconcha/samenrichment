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
from dotenv import load_dotenv

load_dotenv()

proxy_server = os.getenv("PROXY_SERVER")
proxy_username = os.getenv("PROXY_USERNAME")
proxy_password = os.getenv("PROXY_PASSWORD")

# Get the current directory where main.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]

async def start_context(contexts, browser, index):
    stop = index
    while index == stop:
        context = await browser.new_context(
            # proxy = {
            #     "server" : proxy_server,
            #     "username" : proxy_username,
            #     "password" : proxy_password
            # },
            user_agent=random.choice(USER_AGENTS)
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

def upload_enriched_data(updates, column_mapping, index, worksheet):
    for column_name, value in updates:
        if column_name in column_mapping:
            try:
                # Index is now already the actual row number (1-based)
                current_row = index
                
                column = column_mapping[column_name]
                print(f"Updating {column_name} at row {current_row}, column {column} with: {value}")
                worksheet.update_cell(current_row, column, value)
            except Exception as e:
                print(f"Error updating {column_name}: {e}")
        else:
            print(f"Warning: Column '{column_name}' not found in sheet")

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

async def get_platform_link(contexts, index_worksheet, row, column_mapping, worksheet, platform):
    """
    Generic function to get either LinkedIn or Crunchbase links through Google search.
    
    Args:
        contexts: Browser contexts for scraping
        index_worksheet: Row index in worksheet
        row: Row data dictionary
        column_mapping: Dictionary mapping column names to indices
        worksheet: Google worksheet object
        platform: String indicating platform ("LinkedIn" or "Crunchbase")
    """
    print(f"\nProcessing row {index_worksheet}")
    
    # Get appropriate query based on platform
    query_key = platform
    google_search_query = utils.get_queries(row)["Queries"][query_key]
    print(f"Ready GoogleSearch<>{platform} query: {google_search_query}")

    # Perform scrape
    link = await scrapes.google_search_scrape(contexts, google_search_query, row["Startup"])
    
    # Get current value and determine if update needed
    column_idx = column_mapping.get(platform)
    cell_value = worksheet.cell(index_worksheet, column_idx).value
    platform_link = link if not cell_value or cell_value.strip() == "" else cell_value
    profile_name = extract_profile(platform_link)
    
    # Update worksheet
    updates = [(platform, platform_link), (f'{platform}_profile', profile_name)]
    upload_enriched_data(updates, column_mapping, index_worksheet, worksheet)

def find_blank_cells(table, column_mapping, column_idx):
    """
    Find blank cells in a specific column using the table data structure.
    
    Args:
        table: List of dictionaries containing worksheet data
        column_mapping: Dictionary mapping column names to indices
        column_idx: The column index to check for blank cells
    
    Returns:
        List of [row_number, column_idx] for blank cells
    """
    blank_cells = []
    if column_idx is None:
        raise ValueError("Column not found in the worksheet headers!")

    # Get column name from index
    column_key = next(key for key, value in column_mapping.items() if value == column_idx)
    
    for i, row in enumerate(table, start=2):  # start=2 to match worksheet row numbers
        if not row[column_key] or row[column_key].strip() == "":
            blank_cells.append([i, column_idx])
            
    return blank_cells

def extract_profile(url: str) -> str:
    """
    Extracts the company profile name from a Crunchbase URL.
    
    Args:
        url (str): The Crunchbase URL
        
    Returns:
        str: The company profile name (last part of the URL)
        
    Example:
        >>> extract_profile("https://www.crunchbase.com/organization/elythea", "crunchbase")
        'elythea'
    """
    # Remove any trailing whitespace and split by '/'
    clean_url = url.strip()
    parts = clean_url.split('/')
    
    # Return the last non-empty part
    return parts[-1].strip()

async def perform_enrichment(enrichment_to_perform: str, save_interval=10):
    print("Starting enrichment...")

    async with async_playwright() as p:
        worksheet_data = access_to_worksheet_data()
        table, column_mapping = update_table(worksheet_data)

        linkedin_col_idx = column_mapping.get("linkedin")
        blanks_linkedin = find_blank_cells(table, column_mapping, linkedin_col_idx)
        print(f"\nFound {len(blanks_linkedin)} LinkedIn blanks")

        crunchbase_col_idx = column_mapping.get("crunchbase")
        blanks_crunchbase_link = find_blank_cells(table, column_mapping, crunchbase_col_idx)
        print(f"\nFound {len(blanks_crunchbase_link)} Crunchbase blanks.")

        description_col_idx = column_mapping.get("description")
        description_blanks = find_blank_cells(table, column_mapping, description_col_idx)
        print(f"\nFound {len(description_blanks)} Description blanks.")

        while len(blanks_linkedin) > 0:
            # Initialize the browser
            browser = await p.webkit.launch(headless=True)

            # Set up contexts with rotating IPs
            number_of_contexts = 5 if len(blanks_linkedin) > 5 else len(blanks_linkedin)
            contexts = []
            tasks = [start_context(contexts, browser, i) for i in range(number_of_contexts)]
            await asyncio.gather(*tasks)
            print(f"Set up {len(contexts)} contexts.")

            # Start LinkedIn scrape session.
            tasks = [get_platform_link(contexts, blank_cell[0], table[blank_cell[0] - 2], 
                     column_mapping, worksheet_data, "linkedin") 
                     for blank_cell in blanks_linkedin]
            await asyncio.gather(*tasks)

            worksheet_data = access_to_worksheet_data()
            table, column_mapping = update_table(worksheet_data)
            blanks_linkedin = find_blank_cells(table, column_mapping, linkedin_col_idx)

            print(f"\n\nBlank LinkedIn cells: {len(blanks_linkedin)}")

            # Close the browser
            await browser.close()

        while len(blanks_crunchbase_link) > 0:
            # Initialize the browser
            browser = await p.webkit.launch(headless=True)

            # Set up contexts with rotating IPs
            number_of_contexts = 5 if len(blanks_crunchbase_link) > 5 else len(blanks_crunchbase_link)
            contexts = []
            tasks = [start_context(contexts, browser, i) for i in range(number_of_contexts)]
            await asyncio.gather(*tasks)
            print(f"Set up {len(contexts)} contexts.")

            # Start LinkedIn scrape session.
            tasks = [get_platform_link(contexts, blank_cell[0], table[blank_cell[0] - 2], 
                     column_mapping, worksheet_data, "crunchbase") 
                     for blank_cell in blanks_crunchbase_link]
            await asyncio.gather(*tasks)

            worksheet_data = access_to_worksheet_data()
            table, column_mapping = update_table(worksheet_data)
            blanks_crunchbase_link = find_blank_cells(table, column_mapping, crunchbase_col_idx)

            print(f"\n\nBlank Crunchbase cells: {len(blanks_crunchbase_link)}")

            # Close the browser
            await browser.close()

        while len(description_blanks) > 0:
            print(f"\n\nDescription blanks: {len(description_blanks)}")

            # Initialize the browser
            browser = await p.webkit.launch(headless=True)

            # Set up contexts with rotating IPs
            number_of_contexts = 5 if len(description_blanks) > 5 else len(description_blanks)
            contexts = []
            tasks = [start_context(contexts, browser, i) for i in range(number_of_contexts)]
            await asyncio.gather(*tasks)
            print(f"Set up {len(contexts)} contexts.")

            # Start LinkedIn scrape session.
            tasks = [get_platform_link(contexts, blank_cell[0], table[blank_cell[0] - 2], 
                     column_mapping, worksheet_data, "description") 
                     for blank_cell in description_blanks]
            await asyncio.gather(*tasks)

            worksheet_data = access_to_worksheet_data()
            table, column_mapping = update_table(worksheet_data)
            description_blanks = find_blank_cells(table, column_mapping, description_col_idx)

            print(f"\n\nBlank Description cells: {len(description_blanks)}")

            # Close the browser
            await browser.close()
        

# Choose operation when running the script
async def main():

    operation_to_perform = input("\nOperation to perform: \n\nEnrichment (Press 'E') \n\nPrevent sleep (Press 'P') \n\nYour selection: ")

    if operation_to_perform.lower() == "e":

        enrichment_to_perform = input("Enrichment to perform: \n\nStartup (Press 'S') \nInvestor (Press 'I') \n\nYour selection: ")

        # Start enrichment operation (using asyncio.run to handle async function)
        await asyncio.gather(perform_enrichment(enrichment_to_perform))

        utils.play_alert_sound()

    elif operation_to_perform.lower() == "p":
        utils.prevent_sleep(6000)

    else:
        print("Invalid operation")

print(sys.path)


if __name__ == "__main__":
    asyncio.run(main())
