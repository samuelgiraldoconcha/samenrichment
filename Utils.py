from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
import subprocess
import pygame

def play_alert_sound():
    # Initialize Pygame mixer
    pygame.mixer.init()
    # Load the sound file
    pygame.mixer.music.load('alert_sound.wav')  # Replace with the path to your sound file
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # Wait for sound to finish playing
        pygame.time.Clock().tick(10)

def save_results_periodically(output, last_save_time, save_interval, output_csv_file_path='search_results.csv'):
    current_time = time.time()
    if current_time - last_save_time >= save_interval:
        results_df = pd.DataFrame(output)
        results_df.to_csv(output_csv_file_path, index=False)
        print(f"Results saved to {output_csv_file_path} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return current_time  # Update last_save_time
    return last_save_time  # No save, return the old last_save_time

# Iterate over each row in the DataFrame

def entire_enrichment(file, output, driverp, output_csv_file_path='search_results.csv', save_interval=10):

    last_save_time = time.time()

    # Iterate over each row in the DataFrame
    for index, row in file.iterrows():
        startup = row['Startup']
        industry = row['Industry']

        queryLinkedIn = f"site:linkedin.com/in/ {startup}, founder"
        queryWebsite = f"{startup}, {industry}"
        queryCrunchbase = f"site:crunchbase.com, {startup}, {industry}"

        scrapeLinkedIn = [queryLinkedIn, ""]
        scrapeWebsite = [queryWebsite, ""]
        scrapeCrunchbase = [queryCrunchbase, ""]

        scrapes = [scrapeLinkedIn, scrapeWebsite, scrapeCrunchbase]

        for scrape in scrapes:
            search_query = '+'.join(scrape[0].split())
            driverp.get(f"https://www.google.com/search?q={search_query}")
            time.sleep(2)

            if driverp.find_elements(By.CSS_SELECTOR, 'div.g-recaptcha'):
                play_alert_sound()
                print("reCAPTCHA detected. Please complete the CAPTCHA manually.")
                input("Press Enter after completing the CAPTCHA...")
                driverp.refresh()
                time.sleep(5)

            try:
                element = driverp.find_element(By.CSS_SELECTOR, 'a[jsname="UWckNb"]')
                scrape[1] = element.get_attribute('href')
                print(scrape[1])

                if scrape == scrapeCrunchbase:
                    financials_url = scrape[1] + '/company_financials'
                    driverp.get(financials_url)
                    time.sleep(3)

                    financial_signals = ["pre-seed", "seed", 'series a', 'series b', 'series c', 'series d', 'series e', 'series f', 'ipo', 'acquired']
                    found_signal = None
                    funding_date = None

                    try:
                        page_text = driverp.find_element(By.TAG_NAME, 'body').text.lower()
                        for signal in financial_signals:
                            if signal in page_text:
                                found_signal = signal.capitalize()
                                break

                        # Now scrape the date for the latest funding stage (assuming it's near the funding stage in the HTML)
                        if found_signal:
                            date_element = driverp.find_element(By.CSS_SELECTOR, '#mat-tab-nav-panel-0 > div > full-profile > page-centered-layout.overview-divider.ng-star-inserted > div > row-card > div > div:nth-child(2) > profile-section > section-card > mat-card > div.section-content-wrapper > div > obfuscation-cta > phrase-list-card:nth-child(1) > obfuscation > obfuscation-cta > markup-block > field-formatter:nth-child(12) > a')  # Replace with the actual CSS selector
                            funding_date = date_element.text.strip()
                            print(f"Date of latest funding: {funding_date}")
                            scrapeCrunchbase[1] = found_signal

                        if not found_signal:
                            print(f"No financial data found on: {financials_url}")

                    except Exception as e:
                        print(f"Error fetching financial data: {e}")

            except Exception as e:
                output.append({
                    'Query': scrape[0],
                    'URL': f"Error fetching result: {e}"
                })
                print(f"Error fetching results for query '{scrape[0]}': {e}")

        #TODO: Manage different appends according to exclude/include.
        output.append({
            'Startup': startup,
            'LinkedIn': scrapeLinkedIn[1],
            'Website': scrapeWebsite[1],
            'Raised to Date': scrapeCrunchbase[1] if scrapeCrunchbase[1] else '',
            'Date of latest funding': funding_date if funding_date else ''
        })
        print(f"{startup}, {industry}, LinkedIn, Website, Crunchbase: {scrapeLinkedIn[1]}, {scrapeWebsite[1]}, {scrapeCrunchbase[1]}")

        last_save_time = save_results_periodically(output, last_save_time, save_interval, output_csv_file_path)

    save_results_periodically(output, last_save_time, 0, output_csv_file_path)

def crunchbase_enrichment(file, output, driverp, output_csv_file_path='search_results.csv', save_interval=10):
    last_save_time = time.time()

    # Iterate over each row in the DataFrame
    for index, row in file.iterrows():
        # Construct the Crunchbase query using 'Startup' and 'Industry' and 'Website'
        startup = row['Startup']
        industry = row['Industry']

        queryCrunchbase = f"{startup}, {industry}, Crunchbase"
        scrapeCrunchbase = [queryCrunchbase, ""]

        # Encode the query for the URL
        search_query = '+'.join(scrapeCrunchbase[0].split())

        # Load the Google search results page
        driverp.get(f"https://www.google.com/search?q={search_query}")

        # Wait for the dynamic content to load (you might need to adjust the sleep time)
        time.sleep(2)

        # Check for reCAPTCHA
        if driverp.find_elements(By.CSS_SELECTOR, 'div.g-recaptcha'):
            play_alert_sound()
            print("reCAPTCHA detected. Please complete the CAPTCHA manually.")
            input("Press Enter after completing the CAPTCHA...")
            driverp.refresh()
            time.sleep(5)  # Wait for the page to reload

        # Find the first result link
        try:
            element = driverp.find_element(By.CSS_SELECTOR, 'a[jsname="UWckNb"]')
            # Append result to the list
            scrapeCrunchbase[1] = element.get_attribute('href')
            print(scrapeCrunchbase[1])

            # Append '/company_financials' to the Crunchbase link to check for financial info
            financials_url = scrapeCrunchbase[1] + '/company_financials'
            driverp.get(financials_url)
            time.sleep(3)

            # Look for financial data like "Series A", "IPO", etc., and the associated date
            financial_signals = ["pre-seed","seed",'series a', 'series b', 'series c', 'series d', 'series e', 'series f', 'ipo', 'acquired']
            found_signal = None
            funding_date = None

            try:
                page_text = driverp.find_element(By.TAG_NAME, 'body').text.lower()
                for signal in financial_signals:
                    if signal in page_text:
                        found_signal = signal.capitalize()  # Store only the signal, e.g., "Series A"
                        break

                # Extract the date of the latest funding stage
                if found_signal:
                    funding_date_element = driverp.find_element(By.CSS_SELECTOR, '#mat-tab-nav-panel-0 > div > full-profile > page-centered-layout.overview-divider.ng-star-inserted > div > row-card > div > div:nth-child(2) > profile-section > section-card > mat-card > div.section-content-wrapper > div > obfuscation-cta > phrase-list-card:nth-child(1) > obfuscation > obfuscation-cta > markup-block > field-formatter:nth-child(12) > a')  # Adjust selector as needed
                    funding_date = funding_date_element.text
                    print(f"Financial data found: {found_signal}, Date: {funding_date}")
                else:
                    print(f"No financial data found on: {financials_url}")
            except Exception as e:
                print(f"Error fetching financial data: {e}")

        except Exception as e:
            # Append error message to the list
            output.append({
                'Query': scrapeCrunchbase[0],
                'URL': f"Error fetching result: {e}"
            })
            print(f"Error fetching results for query '{scrapeCrunchbase[0]}': {e}")
            # Convert results to a DataFrame
            results_df = pd.DataFrame(output)

            # Save the results to a CSV file
            output_csv_file_path = 'search_results.csv'  # Change this to your desired output file path
            results_df.to_csv(output_csv_file_path, index=False)

        # Append results with the Crunchbase financial data and the date
        output.append({
            'Startup': startup,
            'Crunchbase URL': scrapeCrunchbase[1],
            'Raised to Date': found_signal if found_signal else '',
            'Date of Latest Funding': funding_date if funding_date else ''
        })
        print(f"{startup}, Crunchbase: {scrapeCrunchbase[1]}, {found_signal}, {funding_date}")

        # Save results periodically
        last_save_time = save_results_periodically(output, last_save_time, save_interval, output_csv_file_path)

    # Final save after completing the loop
    save_results_periodically(output, last_save_time, 0, output_csv_file_path)