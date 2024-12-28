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
from curl_cffi import requests
from bs4 import BeautifulSoup

current_dir = os.path.dirname(os.path.abspath(__file__))
CRUNCHBASE_HTML_DIR = os.path.join(current_dir, 'html', 'crunchbase')
CRUNCHBASE_JSON_DIR = os.path.join(current_dir, 'json', 'crunchbase')


"""
Function to get links from google search
"""
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
    
    print("\n\nScraping Google Search")
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
        await page.goto(
            search_url, 
            timeout=60000,
            wait_until="domcontentloaded"  # Less strict than 'load'
        )
        print("LLEGAMOS***********************")
        link_locator = page.locator(f'a:has-text("{company}")')
        
        try:
            await link_locator.first.wait_for(timeout=10000)
            href_value = await link_locator.first.get_attribute('href')
            print(f"Found LinkedIn link: {href_value}")
            link_result = href_value
            return link_result
        except:
            print(f"No results found for query: {query}")
            return None

    except Exception as e:
        print(f"Failed scrape in query: {query}, Error: {e}")
        return None
    finally:
        await page.close()


"""
Functions to get data from crunchbase
"""
async def get_html(contexts, link):
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

    try:
        await page.goto(link)
        print("LLEGAMOS***********************")
        content = await page.content()
        print(content[:100])  # Only print first 100 characters
        return content
    except Exception as e:
        print(f"Failed scrape in company: {link}, Error: {e}")    
        return None

def json_from_html_crunchbase_summary(html_content):
    """Extract the embedded JSON data from the HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find script tags containing the JSON data
    scripts = soup.find_all('script')
    
    for script in scripts:
        script_text = script.string
        if script_text and '"properties":' in script_text:
            try:
                # Find the start of the JSON object
                start_idx = script_text.find('{"properties":')
                if start_idx == -1:
                    continue
                    
                # Find matching closing brace
                brace_count = 0
                for i, char in enumerate(script_text[start_idx:]):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = start_idx + i + 1
                            json_str = script_text[start_idx:end_idx]
                            return json.loads(json_str)
                            
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing JSON: {e}")
                continue
                
    return None



"""
Function to get specific values from crunchbase
"""


def get_crunchbase_company_value(crunchbase_profile, key_to_find):
    """
    Retrieves a value from a Crunchbase JSON file by its key.
    
    Args:
        crunchbase_profile (str): The profile ID/name of the Crunchbase file
        key_to_find (str): The key to search for in the JSON
    
    Returns:
        The value associated with the key if found, None otherwise
    """
    try:
        file_path = os.path.join(CRUNCHBASE_JSON_DIR, f'{crunchbase_profile}.json')
        
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

def get_location_from_json(company_profile):
    """
    Gets location information from a company's JSON file.
    
    Args:
        company_profile (str): The profile ID/name of the company
    
    Returns:
        str: Formatted location string (City, Region, Country) or empty string if not found
    """
    try:
        file_path = os.path.join(CRUNCHBASE_JSON_DIR, f'{company_profile}.json')
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return ""
            
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            
        # Add this debug line
        print(f"JSON structure for {company_profile}:", json.dumps(json_data, indent=2)[:500])
        
        # Navigate to location_identifiers in the JSON
        location_identifiers = json_data["cards"]["company_about_fields2"]["location_identifiers"]
        print(f"location_identifiers: {location_identifiers[:500]}")

        # Initialize variables
        city = region = country = None
        
        # Find the correct values by location_type
        for location in location_identifiers:   
            if location["location_type"] == "city":
                city = location["value"]
            elif location["location_type"] == "region":
                region = location["value"]
            elif location["location_type"] == "country":
                country = location["value"]
        
        # Check if we found all components
        if city and region and country:
            return f"{city}, {region}, {country}"
        else:
            return ""
            
    except (KeyError, IndexError, json.JSONDecodeError):
        print(f"Error processing JSON for company: {company_profile}")
        return ""
    except Exception as e:
        print(f"Error reading file: {e}")
        return ""
    


def get_founded_date_from_json(company_profile):
    """
    Retrieves the founded date from a Crunchbase JSON file.
    """
    try:
        file_path = os.path.join(CRUNCHBASE_JSON_DIR, f'{company_profile}.json')
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return ""
            
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            
        # Add this debug line
        print(f"JSON structure for {company_profile}:", json.dumps(json_data, indent=2)[:500])

        # First, let's try to find the founded_on field using a recursive search
        def find_founded_on(obj):
            if isinstance(obj, dict):
                if "founded_on" in obj:
                    return obj["founded_on"].get("value") if isinstance(obj["founded_on"], dict) else obj["founded_on"]
                for value in obj.values():
                    result = find_founded_on(value)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_founded_on(item)
                    if result:
                        return result
            return None

        founded_on = find_founded_on(json_data)
        if founded_on:
            return founded_on
        else:
            print("Founded date not found in JSON structure")
            return None

    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def get_founder_name_from_json(company_profile):
    """
    Retrieves the Founder's name from a Crunchbase JSON file.
    If no Founder is found, returns the earliest employee's name.
    
    Args:
        company_profile (str): The profile ID/name of the company
    
    Returns:
        str: Founder's or earliest employee's name if found, empty string otherwise
    """
    try:
        file_path = os.path.join(CRUNCHBASE_JSON_DIR, f'{company_profile}.json')
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return "",""
            
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            
        # Find the current_employees_featured_order_field section
        employees = json_data.get("cards", {}).get("current_employees_featured_order_field", [])
        
        if not employees:
            print(f"No employees found for company: {company_profile}")
            return "",""

        # First try to find CEO
        for employee in employees:
            title = employee.get("title", "").upper()
            if "CEO" in title:
                person_identifier = employee.get("person_identifier", {})
                return person_identifier.get("value", ""), "CEO"
        
        # If no CEO found, return the first employee in the list
        first_employee = employees[0]
        person_identifier = first_employee.get("person_identifier", {})
        earliest_name = person_identifier.get("value", "")
        
        if earliest_name:
            print(f"No CEO found, returning earliest employee: {earliest_name}")
        else:
            print(f"No valid employee name found for company: {company_profile}")
            
        return earliest_name, "Unknown"
            
    except Exception as e:
        print(f"Error reading file: {e}")
        return "",""

def get_last_funding_type_from_json(company_profile):
    """
    Retrieves the last funding type from a Crunchbase JSON file.
    """
    try:
        file_path = os.path.join(CRUNCHBASE_JSON_DIR, f'{company_profile}.json')
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return ""
            
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            
        # Add this debug line
        print(f"JSON structure for {company_profile}:", json.dumps(json_data, indent=2)[:500])

        # First, let's try to find the last_funding_type field using a recursive search
        def find_last_funding_type(obj):
            if isinstance(obj, dict):
                if "last_funding_type" in obj:
                    return obj["last_funding_type"].get("value") if isinstance(obj["last_funding_type"], dict) else obj["last_funding_type"]
                for value in obj.values():
                    result = find_last_funding_type(value)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_last_funding_type(item)
                    if result:
                        return result
            return None

        last_funding_type = find_last_funding_type(json_data)
        if last_funding_type:
            return last_funding_type
        else:
            print("Last funding type not found in JSON structure")
            return None

    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    

def get_last_funding_at_from_json(company_profile):
    """
    Retrieves the last funding type from a Crunchbase JSON file.
    """
    try:
        file_path = os.path.join(CRUNCHBASE_JSON_DIR, f'{company_profile}.json')
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return ""
            
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            
        # Add this debug line
        print(f"JSON structure for {company_profile}:", json.dumps(json_data, indent=2)[:500])

        # First, let's try to find the last_funding_type field using a recursive search
        def find_last_funding_at(obj):
            if isinstance(obj, dict):
                if "last_funding_at" in obj:
                    return obj["last_funding_at"].get("value") if isinstance(obj["last_funding_at"], dict) else obj["last_funding_at"]
                for value in obj.values():
                    result = find_last_funding_at(value)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_last_funding_at(item)
                    if result:
                        return result
            return None

        last_funding_at = find_last_funding_at(json_data)
        if last_funding_at:
            return last_funding_at
        else:
            print("Last funding at not found in JSON structure")
            return None

    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def get_investments_list_from_json(company_profile):
    try:
        file_path = os.path.join(CRUNCHBASE_JSON_DIR, f'{company_profile}.json')
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return ""
            
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            
        # Add this debug line
        print(f"JSON structure for {company_profile}:", json.dumps(json_data, indent=2)[:500])

        investment_list = json_data["cards"]["investments_list"] if "investments_list" in json_data["cards"] else []
        print(f"Investment list: {investment_list[:100]}")

        orgs_investment_list = [investment.get("organization_identifier", {}).get("value", "") for investment in investment_list]
        print(f"Orgs investment list: {orgs_investment_list}")
        return orgs_investment_list
    except Exception as e:
        print(f"Error reading file: {e}")
        return ""
