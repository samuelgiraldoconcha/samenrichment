from urllib.parse import quote
import pandas as pd
import time
import random
import subprocess
from . import utils
from urllib.parse import quote
#from . import models
import multiprocessing
from playwright.async_api import async_playwright
import asyncio
import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
CRUNCHBASE_DIR = os.path.join(current_dir, '.json', 'crunchbase')

async def google_search_scrape(contexts, query, company):
    """
    Performs a Google search for the given query using Playwright.
    Returns the first search result link if found.
    """
    page = await contexts[random.randint(0,len(contexts)-1)].new_page()
    
    # Block expensive resources
    await page.route("**/*.{png,jpg,jpeg,gif,webp,pdf,mp4,webm,mp3,wav}", lambda route: route.abort())
    await page.route("**/*{analytics,advertising,doubleclick,tracking}*", lambda route: route.abort())
    
    await asyncio.sleep(2.85 + 1.5 * random.random())
    await utils.detect_reCAPTCHA(page)
    
    print("Scraping Google Search")
    link_result = ""

    # 30% chance to scroll randomly
    if random.random() < 0.3:
        scroll_position = random.randint(100, 500)
        await page.evaluate(f"window.scrollTo(0, {scroll_position})")
        await page.wait_for_timeout(500 + random.randint(0, 500))

    # Randomly choose a search parameter
    search_params = ["?q=", "?query=", "?search="]
    search_param = random.choice(search_params)

    # Format the search URL
    search_query = quote(query)
    search_url = f"https://www.google.com/search{search_param}{search_query}"

    try:
        await page.goto(search_url)
        print("LLEGAMOS***********************")
        link_locator = page.locator(f'a:has-text("{company}")')
        # Ensure at least one result exists
        if await link_locator.count() > 0:
            # Get the href attribute of the first result
            href_value = await link_locator.first.get_attribute('href')
            print(f"Found LinkedIn link: {href_value}")
            link_result = href_value
        else: 
            print(f"No results found for query: {query}")

    except Exception as e:
        print(f"Failed scrape in query: {query}, Error: {e}")
    
    finally:
        return link_result
    
async def company_info_crunchbase(contexts, query, crunchbase_profile):
    """
    Scrapes entire html of company info from crunchbase.
    Stores in a json file.
    Scrapes the following:
    - Name of first founder
    - Founded Date
    - Description
    - Stages
    - Date of latest funding
    """
    page = await contexts[random.randint(0,len(contexts)-1)].new_page()
    
    # Block expensive resources
    await page.route("**/*.{png,jpg,jpeg,gif,webp,pdf,mp4,webm,mp3,wav}", lambda route: route.abort())
    await page.route("**/*{analytics,advertising,doubleclick,tracking}*", lambda route: route.abort())
    
    await asyncio.sleep(2.85 + 1.5 * random.random())
    await utils.detect_reCAPTCHA(page)
    
    print("Scraping Crunchbase's company profile API")
    content = ""

    # 30% chance to scroll randomly
    if random.random() < 0.3:
        scroll_position = random.randint(100, 500)
        await page.evaluate(f"window.scrollTo(0, {scroll_position})")
        await page.wait_for_timeout(500 + random.randint(0, 500))

    # Randomly choose a search parameter
    search_params = ["?q=", "?query=", "?search="]
    search_param = random.choice(search_params)

    # Format Crunchbase's company profile API URL
    search_url = f'https://www.crunchbase.com/v4/data/entities/organizations/{crunchbase_profile}?field_ids=%5B%22identifier%22,%22layout_id%22,%22facet_ids%22,%22title%22,%22short_description%22,%22is_locked%22%5D&layout_mode=view_v2'

    try:
        await page.goto(search_url)
        print("LLEGAMOS***********************")
        content = await page.content()
        print(content[:100])  # Only print first 100 characters
        
        # Save JSON content to file
        try:
            json_content = json.loads(content)
            os.makedirs(CRUNCHBASE_DIR, exist_ok=True)  # Create directory if it doesn't exist
            file_path = os.path.join(CRUNCHBASE_DIR, f'{crunchbase_profile}.json')
            with open(file_path, 'w') as f:
                json.dump(json_content, f, indent=2)
            preview = json.dumps(json_content, indent=2)[:100]
            print(f"Content saved to: {file_path}")
            print("Content preview:")
            print(preview + "...")
        except json.JSONDecodeError:
            print("Content is not valid JSON. First 500 characters:")
            print(content[:500] + "...")
            return content   
    except Exception as e:
        print(f"Failed scrape in query: {query}, Error: {e}")    
        return content
    finally:
        return content
    


#Scrape company info from crunchbase, needs a crunchbase link
async def scrape_crunchbase_dateLatestFunding(page, scrape_link):
    # Block expensive resources before navigation
    await page.route("**/*.{png,jpg,jpeg,gif,webp,pdf,mp4,webm,mp3,wav}", lambda route: route.abort())
    await page.route("**/*{analytics,advertising,doubleclick,tracking}*", lambda route: route.abort())
    
    print("Scrape Date of latest funding")
    financials_url = scrape_link + '/company_financials'
    await page.goto(financials_url)
    
    # Add random delay after page load
    await asyncio.sleep(0.4 + 0.5 * random.random())

    # Simulate human-like scrolling
    scroll_height = random.randint(100, 300)
    await page.evaluate(f"window.scrollTo(0, {scroll_height})")

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
            funding_date = await page.locator(
            selector
            ).inner_text()
            if funding_date:  # If we found a date, break the loop
                break
        except:
            continue

    print(funding_date)
    return funding_date

async def scrape_crunchbase_description(page, scrape_link):
    print("Description")
    description = ""
    await page.goto(scrape_link)

    # Add random delay after page load
    await asyncio.sleep(0.4 + 0.5 * random.random())

    # Simulate human-like scrolling
    scroll_height = random.randint(100, 300)
    await page.evaluate(f"window.scrollTo(0, {scroll_height})")

    # Extract the description
    try:
        description = await page.locator(
            '#mat-tab-nav-panel-0 > div > full-profile > page-centered-layout.overview-divider.ng-star-inserted > div > row-card > div > div:nth-child(1) > profile-section > section-card > mat-card > div.section-content-wrapper > description-card > div > span'
        ).inner_text()
        print(description)
    except Exception as e:
        print(f"Error extracting description: {e}")
    finally:

        return description

async def scrape_crunchbase_stage(page, scrape_link):
    print("Stage")
    stage = ""
    await page.goto(scrape_link)

    # Add random delay after page load
    await asyncio.sleep(0.4 + 0.5 * random.random())

    # Simulate human-like scrolling
    scroll_height = random.randint(100, 300)
    await page.evaluate(f"window.scrollTo(0, {scroll_height})")

    # Extract the description
    try:
        stage = await page.locator(
            '#mat-tab-nav-panel-0 > div > full-profile > page-centered-layout.overview-divider.ng-star-inserted > div > row-card > div > div:nth-child(1) > profile-section > section-card > mat-card > div.section-content-wrapper > fields-card > ul > li:nth-child(3) > label-with-icon > span > field-formatter > a'
        ).inner_text()
        print(stage)
    except Exception as e:
        print(f"Error extracting description: {e}")
    finally:
        return stage

        
def get_crunchbase_value(crunchbase_profile, key_to_find):
    """
    Retrieves a value from a Crunchbase JSON file by its key.
    
    Args:
        crunchbase_profile (str): The profile ID/name of the Crunchbase file
        key_to_find (str): The key to search for in the JSON
    
    Returns:
        The value associated with the key if found, None otherwise
    """
    try:
        file_path = os.path.join(CRUNCHBASE_DIR, f'{crunchbase_profile}.json')
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        def find_key(obj, key):
            if isinstance(obj, dict):
                if key in obj:
                    return obj[key]
                for k, v in obj.items():
                    result = find_key(v, key)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_key(item, key)
                    if result is not None:
                        return result
            return None
            
        result = find_key(data, key_to_find)
        if result is not None:
            print(f"Found value for key '{key_to_find}': {result}")
            return result
        else:
            print(f"Key '{key_to_find}' not found in file")
            return None
            
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
        