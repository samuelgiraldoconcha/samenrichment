import pandas as pd
import time
from selenium.webdriver.common.by import By

def save_results_periodically(output, last_save_time, save_interval, output_csv_file_path='search_results.csv'):
    current_time = time.time()
    if current_time - last_save_time >= save_interval:
        results_df = pd.DataFrame(output)
        results_df.to_csv(output_csv_file_path, index=False)
        print(f"Results saved to {output_csv_file_path} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return current_time  # Update last_save_time
    return last_save_time  # No save, return the old last_save_time

def play_alert_sound():
    # Path to the alert sound file
    sound_file = 'alert_sound.wav'  # Replace with the path to your sound file
    playsound(sound_file)

def Enrichment(file, output, driverp, output_csv_file_path='search_results.csv', save_interval=10):
    last_save_time = time.time()
    
    # Iterate over each row in the DataFrame
    for index, row in file.iterrows():
        startup = row['Startup']
        industry = row['Industry']

        queryLinkedIn = f"{startup}, {industry}, founder, linkedin"
        queryWebsite = f"{startup}, {industry}"

        scrapeLinkedIn = [queryLinkedIn, ""]
        scrapeWebsite = [queryWebsite, ""]
        scrapes = [scrapeLinkedIn, scrapeWebsite]

        # Scrape for each query
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
            except Exception as e:
                output.append({'Query': scrape[0], 'URL': f"Error fetching result: {e}"})
                print(f"Error fetching results for query '{scrape[0]}': {e}")

        # Append results
        output.append({
            'Startup': startup,
            'LinkedIn': scrapeLinkedIn[1],
            'Website': scrapeWebsite[1]
        })
        print(f"{startup}, {industry}, {scrapeLinkedIn[1]}, {scrapeWebsite[1]}")

        # Save results periodically
        last_save_time = save_results_periodically(output, last_save_time, save_interval, output_csv_file_path)
    
    # Final save after completing the loop
    save_results_periodically(output, last_save_time, 0, output_csv_file_path)
