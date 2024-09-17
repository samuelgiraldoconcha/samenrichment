from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
import subprocess

def Enrichment(file, output, driverp):
    # Iterate over each row in the DataFrame
    for index, row in file.iterrows():
        # Construct queries using 'Startup', 'Firstname' and industry
        startup = row['Startup']
        founder_first_name = row['Firstname']
        industry = row['Industry']

        queryLinkedIn = f"{startup}, {founder_first_name}, founder, linkedin"
        queryWebsite = f"{startup}, {industry}"
        queryCrunchbase = f"{startup}, {industry}, Crunchbase"

        scrapeLinkedIn = [queryLinkedIn, ""]
        scrapeWebsite = [queryWebsite, ""]
        scrapeCrunchbase = [queryCrunchbase, ""]

        scrapes = [scrapeLinkedIn, scrapeWebsite, scrapeCrunchbase]

        # Do the scrape and assign the results of the scrape.
        for scrape in scrapes:
            # Encode the query for the URL
            search_query = '+'.join(scrape[0].split())
            
            # Load the Google search results page
            driverp.get(f"https://www.google.com/search?q={search_query}")
            
            # Wait for the dynamic content to load (you might need to adjust the sleep time)
            time.sleep(2)
            
            # Check for reCAPTCHA
            if driverp.find_elements(By.CSS_SELECTOR, 'div.g-recaptcha'):
                play_alert_sound()
                flash_screen_alert()
                print("reCAPTCHA detected. Please complete the CAPTCHA manually.")
                input("Press Enter after completing the CAPTCHA...")
                driverp.refresh()
                time.sleep(5)  # Wait for the page to reload

            # Find the first result link
            try:
                element = driverp.find_element(By.CSS_SELECTOR, 'a[jsname="UWckNb"]')
                # Append result to the list
                scrape[1] = element.get_attribute('href')
                print(scrape[1])

                # If this is the Crunchbase query, add '/company_financials' to the URL and check for financial info
                if scrape == scrapeCrunchbase:
                    # Append '/company_financials' to the Crunchbase link
                    financials_url = scrape[1] + '/company_financials'
                    driverp.get(financials_url)
                    time.sleep(3)

                    # Look for financial data like "Series A", "IPO", etc.
                    financial_signals = ['series a', 'series b', 'series c', 'series d', 'series e', 'series f', 'ipo', 'acquired']
                    found_signal = None

                    try:
                        page_text = driverp.find_element(By.TAG_NAME, 'body').text.lower()
                        for signal in financial_signals:
                            if signal in page_text:
                                found_signal = signal.capitalize()  # Store only the signal, e.g., "Series A"
                                break

                        if found_signal:
                            scrapeCrunchbase[1] = found_signal
                            print(f"Financial data found: {found_signal}")
                        else:
                            print(f"No financial data found on: {financials_url}")
                    except Exception as e:
                        print(f"Error fetching financial data: {e}")

            except Exception as e:
                # Append error message to the list
                output.append({
                    'Query': scrape[0],
                    'URL': f"Error fetching result: {e}"
                })
                print(f"Error fetching results for query '{scrape[0]}': {e}")
                # Convert results to a DataFrame
                results_df = pd.DataFrame(output)

                # Save the results to a CSV file
                output_csv_file_path = 'search_results.csv'  # Change this to your desired output file path
                results_df.to_csv(output_csv_file_path, index=False)

        # Append results with each keyword and URL, including Crunchbase financial data if found
        output.append({
            'Startup': startup,
            'Firstname': founder_first_name,
            'LinkedIn': scrapeLinkedIn[1],
            'Website': scrapeWebsite[1],
            'Raised to Date': scrapeCrunchbase[1] if scrapeCrunchbase[1] else ''
        })
        print(f"{startup}, {industry}, {founder_first_name}, LinkedIn, Website, Crunchbase: {scrapeLinkedIn[1]}, {scrapeWebsite[1]}, {scrapeCrunchbase[1]}")
