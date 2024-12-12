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

current_dir = os.path.dirname(os.path.abspath(__file__))

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



# def scrape_linkedin_no_session(driverp, scrape_link):
#     #base-contextual-sign-in-modal > div > section > button > icon > svg
#     #main-content > section.core-rail.mx-auto.papabear\:w-core-rail-width.mamabear\:max-w-\[790px\].babybear\:max-w-\[790px\] > div > section.core-section-container.core-section-container--with-border.border-b-1.border-solid.border-color-border-faint.py-4.text-color-text > div > p
#     print(f'Link: {scrape_link}')
#     press_button(driverp,scrape_link,"base-contextual-sign-in-modal > div > section > button > icon > svg")
#     time.sleep(2)
#     description_tag = driverp.find_element(By.CSS_SELECTOR, "[data-test-id='about-us__description']")
#     description = description_tag.text.strip()
#     print(f'Decription:{description}')
#     return description

def press_button(driver, url, tag):
    print("Button")
    try:
        # Navigate to the provided URL
        driver.get(url)
        
        # Wait until the button is clickable and then click it
        button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, tag))
        )
        button.click()
        print("Button clicked successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        