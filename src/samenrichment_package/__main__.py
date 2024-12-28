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
from curl_cffi import requests
import json

"""
Configuration
"""

load_dotenv()

proxy_server = os.getenv("PROXY_SERVER")
proxy_username = os.getenv("PROXY_USERNAME")
proxy_password = os.getenv("PROXY_PASSWORD")

# Get the current directory where main.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/116.0.1938.69 Safari/537.36", 
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
]

BROWSER_CONFIGS = [
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "impersonate": "chrome",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
    },
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
        "impersonate": "chrome99",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
    }
]



"""
Functions with the arguments of the enrichment process.
"""

async def start_context(contexts, browser, index, proxy_status:str):
    stop = index
    while index == stop:
        if proxy_status.lower() == "on":
            context = await browser.new_context(
                proxy = {
                        "server" : f"http://{proxy_server}",
                        "username" : proxy_username,
                        "password" : proxy_password
                    },
                user_agent=random.choice(USER_AGENTS)
            )
            # Set cookies
            await context.add_cookies([{
                "name": "cb_analytics_consent",
                "value": "granted",
                "domain": "crunchbase.com",
                "path": "/"
            }, {
                "name": "cf_clearance",
                "value": "g729xe8.Akdca5ohDfwaW4mlCfDnGpIUmYthiF4eFQY-1735386135-1.2.1.1-VB7onuNbeRGW0LQDSBw0xj7bDsiAvlhHAEJrFNxoHdADc6ojV6L3wKicG7PQjxci5.Cp2WRqRuawPaQBFpA4WpFk_SWxYe.tbESd7L8TMFcYwwkagMJPns02xg1D_YsDsWaTbf3OEpnyw.b4hbyLXaIvE6Jq5jVpGYV8eSVEQjBwu1J38Ub5xfOjhEJKcbvNErH9psv6epKlZgboa5qlaZqphYsmsVxd1ohe9FclUWz_UlhgpRZ0Ii3kPOXzDQXNecybTEVZ9vwVT5Sx6rHNbCawEuevAXiFH197meQbTCqlZQYPpAtE46Yp6yXY6GbiCkS8yIvdAC27gNhxrXQYPb5xVAtaOXatgu757d5_FFgqBdL_LKadcHh5MjWZcETW5nG4IFkRj5E3_35UjNwfX0kXP8UPIEShO485I89CJg.Y0M9CvnNQQ1GgXYBCsjGD",
                "domain": "crunchbase.com",
                "path": "/"
            }])
        else:
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS)
            )
        try:
            ip_page = await context.new_page()
            await ip_page.goto('https://httpbin.org/ip')
            ip_response = await ip_page.locator("pre").inner_text(timeout=5000)
            print(f"\nContext {index}: {ip_response}")
            if ip_response:
                contexts.append(context)
                index = index + 1
                await ip_page.close()
            else:
                await context.close()
         
        except Exception as ex:
            await context.close()
            print(f"Error in context {index}: {ex}")


def access_to_worksheet_range(range: list):
    # Connect to Google Sheets
    gc = gspread.oauth(
        credentials_filename=f'{current_dir}/gspread/credentials.json'
    )
    sh = gc.open("LifeX Lead Generation")
    worksheet_data = sh.worksheet("Startups Enrichment")
    return worksheet_data

def access_to_worksheet_data():
    # Connect to Google Sheets
    gc = gspread.oauth(
        credentials_filename=f'{current_dir}/gspread/credentials.json'
    )
    sh = gc.open("LifeX Lead Generation")
    worksheet_data = sh.worksheet("Startups Enrichment")
    return worksheet_data

def get_queries(row_data):
   
    founder = row_data.get('Founder', '').strip()
    company = row_data.get('Startup', '').strip()
    
    queries = {
        "linkedin": f"site:linkedin.com/in/ {company}, founder, co-founder, co founder, ceo",
        "crunchbase": f"site:crunchbase.com {company}",
    }

    scrape_packages = [
        {"name": "linkedin", "query": queries["linkedin"], "link": ""},
        {"name": "crunchbase", "query": queries["crunchbase"], "link": ""}
    ]
    return {"Queries": queries, "Scrape packages": scrape_packages}


"""
Functions to communicate with the worksheet
"""


def upload_enriched_data(updates, column_mapping, index, worksheet):
    for column_name, value in updates:
        if column_name in column_mapping:
            try:
                current_row = index
                column = column_mapping[column_name]
                print(f"Updating {column_name} at row {current_row}, column {column} with: {value}")
                worksheet.update_cell(current_row, column, value)
            except Exception as e:
                print(f"Error updating {column_name}: {e}")
        else:
            print(f"Warning: Column '{column_name}' not found in sheet")


def update_table(worksheet_data):
    # 1. Create a mapping of column names to indices.
    # 2. Convert worksheet data to list of dictionaries using header row
    rows = worksheet_data.get_all_values()
    headers = rows[0]
    column_mapping = {header: idx + 1 for idx, header in enumerate(headers)}
    print("Found columns:", column_mapping)
    data = [dict(zip(headers, row)) for row in rows[1:]]
    return data, column_mapping

def update_blank_cells(table, column_mapping, column_idx, worksheet_start, worksheet_end):
    worksheet = access_to_worksheet_data()
    table, column_mapping = update_table(worksheet)
    return utils.find_blank_cells(table, column_mapping, column_idx, worksheet_start, worksheet_end)



"""
Functions to perform the enrichment
"""



def google_sheets_API_quota_check(quota_time, quota_count):
    current_time = time.time()
    elapsed_time = current_time - quota_time
    
    # Google Sheets API has a limit of 60 requests per 60 seconds per project
    QUOTA_LIMIT = 59  # requests
    QUOTA_WINDOW = 60  # seconds
    
    if quota_count >= QUOTA_LIMIT:
        # Need to wait until the quota window resets
        sleep_time = QUOTA_WINDOW - elapsed_time
        print(f"Quota limit reached. Sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
        return current_time, 0  # Reset counter after waiting
    
    elif elapsed_time >= QUOTA_WINDOW:
        # Quota window has passed, reset counter
        return current_time, 1  # Reset timer and start new count
    
    else:
        # Within quota window and under limit
        return quota_time, quota_count + 1

async def get_platform_link(contexts, row, platform):
    # Get appropriate query based on platform
    query_key = platform.lower()
    google_search_query = get_queries(row)["Queries"][query_key]
    print(f"Searching {platform} with query: {google_search_query}")

    # Add longer random delay between requests (3-7 seconds)
    await asyncio.sleep(random.uniform(3, 7))
    
    try:
        link = await scrapes.google_search_scrape(contexts, google_search_query, row["Startup"])
        profile_name = utils.extract_profile(link)
        print(f"Found {platform} profile: {profile_name}")
        updates = [(platform, link), (f'{platform}_profile', profile_name)]
        return updates
    except Exception as e:
        print(f"Error searching {platform}: {str(e)}")
        updates = [(platform, ""), (f'{platform}_profile', "")]
        return updates

async def save_html(contexts, index_worksheet, url, file_path, column_name):
    print(f"\nProcessing row {index_worksheet}")

    html_dir = os.path.join(current_dir, "utils/html/crunchbase")
    html_file = f"{html_dir}/{file_path}.html"

    try:

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(html_file), exist_ok=True)

        # Add delay between requests to avoid triggering Cloudflare
        await asyncio.sleep(random.uniform(2, 5))

        link = url + "/" + file_path

        print(f"Link: {link}")

        # Try to get the HTML content
        content = await scrapes.get_html(contexts, link)

        # Save the content to file
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)

        updates = [(column_name, "Success")]
        return updates
    
    except Exception as e:
        print(f"Error processing row {index_worksheet}: {str(e)}")
        updates = [(column_name, None)]
        return updates


def save_json_data(json_data, output_path):
    """Save JSON data to file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return False
    
def get_crunchbase_json_data(index_worksheet, row, column_mapping, worksheet):
    print(f"\nProcessing JSON conversion for row {index_worksheet}")
    
    crunchbase_profile = row.get("crunchbase_profile", "")
    
    try:

        html_dir = os.path.join(current_dir, "utils/html/crunchbase")
        json_dir = os.path.join(current_dir, "utils/json/crunchbase")
        
        # Create JSON directory if it doesn't exist
        os.makedirs(json_dir, exist_ok=True)
        
        html_file = f"{crunchbase_profile}.html"
        file_path = os.path.join(html_dir, html_file)
        output_path = os.path.join(json_dir, f"{crunchbase_profile}.json")

        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        json_data = scrapes.json_from_html_crunchbase_summary(html_content)
        if json_data:
            if save_json_data(json_data, output_path):
                status = "Success"
            else:
                status = None
                print("Failed to save JSON")
        else:
            status = None
            print("No JSON found in HTML")
    except FileNotFoundError:
        print(  f"HTML file not found for {crunchbase_profile}")
        status = None
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        status = None
    
    updates = [("crunchbase_json_status", status), ("crunchbase_html_status", status)]
    upload_enriched_data(updates, column_mapping, index_worksheet, worksheet)


def get_field_data(index_worksheet, row, column_mapping, worksheet, crunchbase_profile, field_name):
    """
    Generic function to get data from a field
    """
    print(f"Parsing {field_name} of: {row['Startup']}")

    # Perform scrape
    field_value = scrapes.get_crunchbase_company_value(crunchbase_profile, field_name)
    
    # Update worksheet
    updates = [(field_name, field_value)]
    upload_enriched_data(updates, column_mapping, index_worksheet, worksheet)

def get_location_from_json(index_worksheet, row, column_mapping, worksheet, crunchbase_profile):
    print(f"Parsing location of: {row['Startup']}")

    # Perform scrape
    field_value = scrapes.get_location_from_json(crunchbase_profile)
    print(f"Location: {field_value if field_value else "Failed retreieving location from json"}")

    # Update worksheet
    updates = [("location", field_value)]
    upload_enriched_data(updates, column_mapping, index_worksheet, worksheet)


def get_founded_date_from_json(index_worksheet, row, column_mapping, worksheet, crunchbase_profile):
    print(f"Parsing founded date of: {row['Startup']}")

    # Perform scrape
    founded_on = scrapes.get_founded_date_from_json(crunchbase_profile)
    print(f"Founded Date: {founded_on if founded_on else "Failed retreieving founded date from json"}")

    # Update worksheet
    updates = [("founded_on", founded_on)]
    upload_enriched_data(updates, column_mapping, index_worksheet, worksheet)


def get_founder_from_json(index_worksheet, row, column_mapping, worksheet, crunchbase_profile):
    print(f"Parsing Founder of: {row['Startup']}")

    # Perform scrape
    founder_name, founder_title = scrapes.get_founder_name_from_json(crunchbase_profile)
    print(f"Founder: {founder_name if founder_name else "Failed retreieving Founder from json"}")

    # Update worksheet
    updates = [("Founder", founder_name), ("Title", founder_title)]

    upload_enriched_data(updates, column_mapping, index_worksheet, worksheet)


def get_last_funding_type_from_json(index_worksheet, row, column_mapping, worksheet, crunchbase_profile):
    print(f"Parsing last funding type of: {row['Startup']}")

    # Perform scrape
    last_funding_type = scrapes.get_last_funding_type_from_json(crunchbase_profile)
    print(f"Last Funding Type: {last_funding_type if last_funding_type else "Failed retreieving last funding type from json"}")

    # Update worksheet
    updates = [("last_funding_type", last_funding_type)]
    upload_enriched_data(updates, column_mapping, index_worksheet, worksheet)


def get_last_funding_at_from_json(index_worksheet, row, column_mapping, worksheet, crunchbase_profile):
    print(f"Parsing last funding at of: {row['Startup']}")

    # Perform scrape
    last_funding_at = scrapes.get_last_funding_at_from_json(crunchbase_profile)
    print(f"Last Funding At: {last_funding_at if last_funding_at else "Failed retreieving last funding at from json"}")

    # Update worksheet
    updates = [("last_funding_at", last_funding_at)]
    upload_enriched_data(updates, column_mapping, index_worksheet, worksheet)

def get_investments_list_from_json(index_worksheet, row, column_mapping, worksheet, crunchbase_profile):
    print(f"Parsing investments list of: {row['Startup']}")

    print(f"Investments List: {investments_list if investments_list else "Failed retreieving investments list from json"}")

    # Update worksheet
    updates = [("Startups", investment) for investment in investments_list]
    for update in updates:
        upload_enriched_data(update, column_mapping, index_worksheet, worksheet)



"""
Main function to perform the enrichment
"""

def initialize_column_variables(table, column_mapping, worksheet_start, worksheet_end):
    columns_data = {}
    
    for column_name, col_idx in column_mapping.items():
        # Only find blanks within the current batch's row range
        blanks = utils.find_blank_cells(
            table, 
            column_mapping, 
            col_idx,
            worksheet_start,  # start row
            worksheet_end   # end row
        )
        
        columns_data[column_name] = {
            'col_idx': col_idx,
            'blanks': blanks
        }
        
        print(f"\nFound {len(blanks)} {column_name} blanks in rows {worksheet_start}-{worksheet_end}")
        
    return columns_data

def set_cycle_range(row_range, worksheet):
    worksheet_start = row_range[0] + 2
    worksheet_end = row_range[1] + 2
    worksheet_start = max(0, worksheet_start)
    worksheet_end = min(len(worksheet.get_all_values()), worksheet_end)

    return worksheet_start, worksheet_end

async def start_contexts(browser, number_of_contexts, proxy_status: str):

            # Set up contexts with rotating IPs
    contexts = []
    tasks = [start_context(contexts, browser, i, proxy_status) for i in range(0, number_of_contexts)]
    await asyncio.gather(*tasks)
    print(f"Set up {len(contexts)} contexts.")
        
    return contexts

async def update_link(table, column_mapping, worksheet_data, platform, number_of_contexts, columns_data, p, proxy_status: str):     
    browser = await p.webkit.launch(headless=True)
    contexts = await start_contexts(browser, number_of_contexts, proxy_status)
    tasks = [
        get_platform_link(contexts, table[blank_cell[0] - 2], platform)
        for blank_cell in columns_data[platform]["blanks"]
    ]
    results = await asyncio.gather(*tasks)

    for blank_cell, updates in zip(columns_data[platform]["blanks"], results):
        upload_enriched_data(updates, column_mapping, blank_cell[0], worksheet_data)
        
    await browser.close()

async def update_html(number_of_contexts, column_name: str, url, columns_data, p, url_extensions, worksheet_start, proxy_status: str):
    browser = await p.webkit.launch(headless=True)
    contexts = await start_contexts(browser, number_of_contexts, proxy_status)

    # Start Crunchbase HTML scrape session
    tasks = [
        save_html(contexts, blank_cell[0], url, url_extensions[blank_cell[0]-worksheet_start], column_name) 
        for blank_cell in columns_data[column_name]["blanks"]
    ]
    await asyncio.gather(*tasks)
    await browser.close()


async def perform_startup_enrichment():

    """
    Only enriches blank cells. 
    Retries are handled manually. 
    Retries should happend after an entire cycle of enrichment is complete.
    """

    row_range_base = 10
    row_range = [1, row_range_base]


    worksheet = access_to_worksheet_range(row_range)
    table, column_mapping = update_table(worksheet)
    print(f"\nColumn mapping: {column_mapping}")

    retry_range_base = 60
    retry_range = [0, retry_range_base]
    retry_start, retry_end = set_cycle_range(retry_range, worksheet)
    tries = 0

    blank_cells = 0

    proxy_status = "off"

    while row_range[1] < len(worksheet.get_all_values()): 
        print(f"\n\n\nStarting enrichment for rows {row_range[0]}-{row_range[1]}...")
        worksheet_start, worksheet_end = set_cycle_range(row_range, worksheet)
        async with async_playwright() as p:
            
            if tries >= 2 and tries < 4:
                proxy_status = "on"
                print(f"Tries: {tries}\nProxy status: {proxy_status}")
            else:
                proxy_status = "off"
                print(f"Tries: {tries}\nProxy status: {proxy_status}")


            worksheet = access_to_worksheet_range(row_range)
            table, column_mapping = update_table(worksheet)

            # Pass row_range to initialize_column_variables
            columns_data = initialize_column_variables(table, column_mapping, worksheet_start, worksheet_end)
            
            number_of_contexts = 3
            
            await update_link(table, column_mapping, worksheet, "crunchbase", number_of_contexts, columns_data, p, proxy_status)
            columns_data["crunchbase"]["blanks"] = update_blank_cells(table, column_mapping, columns_data["crunchbase"]["col_idx"], worksheet_start, worksheet_end)
            blank_cells += len(columns_data["crunchbase"]["blanks"])

            
            url = "https://www.crunchbase.com/organization"
            # Create list of profiles for the current worksheet range
            crunchbase_profiles = [f"{table[i-2]["crunchbase_profile"]}" for i in range(worksheet_start, worksheet_end)]
            
            await update_html(number_of_contexts, "crunchbase_html_status", url, columns_data, p, crunchbase_profiles, worksheet_start, proxy_status)
            columns_data["crunchbase_html_status"]["blanks"] = update_blank_cells(table, column_mapping, columns_data["crunchbase_html_status"]["col_idx"], worksheet_start, worksheet_end)
            blank_cells += len(columns_data["crunchbase_html_status"]["blanks"])

            for crunchbase_json_blank in columns_data["crunchbase_json_status"]["blanks"]:
                get_crunchbase_json_data(crunchbase_json_blank[0], table[crunchbase_json_blank[0] - 2], column_mapping, worksheet)
            columns_data["crunchbase_json_status"]["blanks"] = update_blank_cells(table, column_mapping, columns_data["crunchbase_json_status"]["col_idx"], worksheet_start, worksheet_end)
            blank_cells += len(columns_data["crunchbase_json_status"]["blanks"])

            """
            Loops for getting data from the JSON file
            """
            """
            
            for description_blank in columns_data["short_description"]["blanks"]:
                get_field_data(description_blank[0], table[description_blank[0] - 2], 
                            column_mapping, worksheet, table[description_blank[0] - 2]["crunchbase_profile"], "short_description")       
            columns_data["short_description"]["blanks"] = await update_blank_cells(table, column_mapping, columns_data["short_description"]["col_idx"], worksheet_start, worksheet_end)

            for location_blank in columns_data["location"]["blanks"]:
                get_location_from_json(location_blank[0], table[location_blank[0] - 2], 
                            column_mapping, worksheet, table[location_blank[0] - 2]["crunchbase_profile"])
            columns_data["location"]["blanks"] = await update_blank_cells(table, column_mapping, columns_data["location"]["col_idx"], worksheet_start, worksheet_end)

            for founded_date_blank in columns_data["founded_on"]["blanks"]:
                get_founded_date_from_json(founded_date_blank[0], table[founded_date_blank[0] - 2], 
                            column_mapping, worksheet, table[founded_date_blank[0] - 2]["crunchbase_profile"])
            columns_data["founded_on"]["blanks"] = await update_blank_cells(table, column_mapping, columns_data["founded_on"]["col_idx"], worksheet_start, worksheet_end)

            for founder_blank in columns_data["Founder"]["blanks"]:
                get_founder_from_json(founder_blank[0], table[founder_blank[0] - 2], 
                            column_mapping, worksheet, table[founder_blank[0] - 2]["crunchbase_profile"]) 
            columns_data["Founder"]["blanks"] = await update_blank_cells(table, column_mapping, columns_data["Founder"]["col_idx"], worksheet_start, worksheet_end)

            for last_funding_type_blank in columns_data["last_funding_type"]["blanks"]:
                get_last_funding_type_from_json(last_funding_type_blank[0], table[last_funding_type_blank[0] - 2], 
                            column_mapping, worksheet, table[last_funding_type_blank[0] - 2]["crunchbase_profile"])
            columns_data["last_funding_type"]["blanks"] = await update_blank_cells(table, column_mapping, columns_data["last_funding_type"]["col_idx"], worksheet_start, worksheet_end)

            for last_funding_at_blank in columns_data["last_funding_at"]["blanks"]:
                get_last_funding_at_from_json(last_funding_at_blank[0], table[last_funding_at_blank[0] - 2], 
                            column_mapping, worksheet, table[last_funding_at_blank[0] - 2]["crunchbase_profile"])
            columns_data["last_funding_at"]["blanks"] = await update_blank_cells(table, column_mapping, columns_data["last_funding_at"]["col_idx"], worksheet_start, worksheet_end)
            """

            # LinkedIn
            """
            await update_link(table, column_mapping, worksheet, "linkedin", number_of_contexts, columns_data, p, proxy_status)
            columns_data["linkedin_profile"]["blanks"] = update_blank_cells(table, column_mapping, columns_data["linkedin"]["col_idx"], worksheet_start, worksheet_end)
            blank_cells += len(columns_data["linkedin_profile"]["blanks"])
            """

            if worksheet_end >= retry_end:
                print(f"Retry end reached")
                if blank_cells != 0:
                    print(f"There are blank cells")
                    tries += 1
                    if tries >= 3:
                        proxy_status = "off"
                        print(f"Tries: {tries}\nProxy status: {proxy_status}")
                        row_range = [retry_end, retry_end + row_range_base]
                        retry_range = [retry_range[0] + retry_range_base, retry_range[1] + retry_range_base]
                        retry_start, retry_end = set_cycle_range(retry_range, worksheet)
                        tries = 0
                    else:
                        row_range = [retry_start, retry_start + row_range_base]
                        retry_start, retry_end = set_cycle_range(retry_range, worksheet)
                        print(f"Tries: {tries}\nProxy status: {proxy_status}")
                else:
                    retry_range = [retry_range[0] + retry_range_base, retry_range[1] + retry_range_base]
                    retry_start, retry_end = set_cycle_range(retry_range, worksheet)
                    tries = 0
            else:
                row_range = [row_range[0] + row_range_base, row_range[1] + row_range_base]
            print(f"\nBlank cells: {blank_cells}")
            blank_cells = 0
        
async def perform_portfolio_enrichment(save_interval=10):
    print("Starting portfolio enrichment...")

    async with async_playwright() as p:
        browser = await p.webkit.launch(headless=True)
        contexts = []
        await start_context(contexts, browser, 0)
        
        if not contexts:
            print("Failed to create browser context")
            return
        context = contexts[0]

        worksheet_data = access_to_worksheet_range(range)
        table, column_mapping = update_table(worksheet_data)
        
        # Get the Crunchbase profile from user input
        crunchbase_profile = input("Enter the crunchbase profile: ")

        vc_portfolio_html_status = await scrapes.company_summary_crunchbase_html([context], crunchbase_profile)
        print(f"VC Portfolio HTML Status: {vc_portfolio_html_status}")

        vc_portfolio_json_status = scrapes.json_from_html_crunchbase_summary(crunchbase_profile)
        print(f"VC Portfolio JSON Status: {vc_portfolio_json_status}")
        
        # Get investments list
        investments_list = scrapes.get_investments_list_from_json(crunchbase_profile)

        
        if not investments_list:
            print("No investments found for this profile")
            return
            
        # Get current number of rows in worksheet
        current_rows = len(worksheet_data.get_all_values())
        
        # Calculate new rows needed
        new_rows_count = len(investments_list)
        
        # Create empty rows at the bottom
        empty_row = [""] * len(column_mapping)  # Create empty row with correct number of columns
        for _ in range(new_rows_count):
            worksheet_data.append_row(empty_row)
            
        # Get the column index for "startup"
        startup_col = column_mapping.get("Startup")
        if not startup_col:
            print("Error: 'startup' column not found in worksheet")
            return
            
        # Create a list of cells to be updated
        startup_cells = []
        for i in range(new_rows_count):
            row_number = current_rows + i + 1  # +1 because rows are 1-indexed
            startup_cells.append(row_number)
            
        print(f"Created {new_rows_count} new rows")
        print(f"Ready to fill rows {startup_cells} with investment data")
        
        # Update the cells with investment data
        for i, row_num in enumerate(startup_cells):
            if i < len(investments_list):
                worksheet_data.update_cell(row_num, startup_col, investments_list[i])
                print(f"Updated row {row_num} with {investments_list[i]}")

# Choose operation when running the script
def main():

    operation_to_perform = input("\nOperation to perform: \n\nStartup Enrichment (Press 'E') \n\nPortfolio Enrichment (Press 'P') \n\nPrevent sleep (Press 'S') \n\nYour selection: ")

    if operation_to_perform.lower() == "e":

        # Start enrichment operation (using asyncio.run to handle async function)
        asyncio.run(perform_startup_enrichment())  # Updated variable name here

        utils.play_alert_sound()

    elif operation_to_perform.lower() == "p":
        asyncio.run(perform_portfolio_enrichment())

    elif operation_to_perform.lower() == "s":
        utils.prevent_sleep(6000)

    else:
        print("Invalid operation")

print(sys.path)


if __name__ == "__main__":
    main()