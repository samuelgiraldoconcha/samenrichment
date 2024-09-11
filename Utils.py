from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
import subprocess

def play_alert_sound():
    # AppleScript command to play a built-in macOS sound
    apple_script = '''
    tell application "Finder"
        set soundFile to ("/System/Library/Sounds/Glass.aiff" as POSIX file as alias)
        open soundFile
    end tell
    '''
    subprocess.run(['osascript', '-e', apple_script])

def flash_screen_alert():
    # AppleScript command to flash the screen
    apple_script = '''
    tell application "System Events"
        set myAlert to make new window
        tell myAlert
            set its bounds to {0, 0, 1440, 900}
            set its background color to {255, 0, 0}
        end tell
        delay 1
        close myAlert
    end tell
    '''
    subprocess.run(['osascript', '-e', apple_script])

def Enrichment(file, output, driverp):
    # Iterate over each row in the DataFrame
    for index, row in file.iterrows():
        # Construct queries using 'Startup' and 'Firstname' and industry
        startup = row['Startup']
        founder_first_name = row['Firstname']
        industry = row['Industry']

        queryLinkedIn = f"{startup}, {founder_first_name}, founder, linkedin"
        queryWebsite = f"{startup}, {industry}"

        scrapeLinkedIn = [queryLinkedIn, ""]
        scrapeWebsite = [queryWebsite, ""]

        scrapes = [scrapeLinkedIn, scrapeWebsite]

        # Do the scrape and assigns the results of the scrape.
        for scrape in scrapes:
            # Encode the query for the URL
            search_query = '+'.join(scrape[0].split())
            
            # Load the Google search results page
            driverp.get(f"https://www.google.com/search?q={search_query}")
            
            # Wait for the dynamic content to load (you might need to adjust the sleep time)
            time.sleep(3)
            
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

            except Exception as e:
                # Append error message to the list
                output.append({
                    'Query': scrape[1],
                    'URL': f"Error fetching result: {e}"
                })
                print(f"Error fetching results for query '{scrape[0]}': {e}")
                # Convert results to a DataFrame
                results_df = pd.DataFrame(output)

                # Save the results to a CSV file
                output_csv_file_path = 'search_results.csv'  # Change this to your desired output file path
                results_df.to_csv(output_csv_file_path, index=False)

        # Append results with each keyword and URL
        output.append({
            'Startup': startup,
            'Firstname': founder_first_name,
            'LinkedIn': scrapeLinkedIn[1],
            'Website' : scrapeWebsite[1]

        })
        print(f"{startup}, {industry}, {founder_first_name}, LinkedIn, Website: {scrapeLinkedIn[1]}, {scrapeWebsite[1]}")