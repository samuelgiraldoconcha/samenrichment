from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
from .utils import utils, scrapes
import sys
import os

print(sys.path)

# Get the current directory where main.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Now read the CSV file
df = pd.read_csv(f"{current_dir}/input_files/template.csv")

# Replace NaN with empty strings
df.fillna('', inplace=True)

# List to store results
results = []
output_csv_file_path = f"{current_dir}/output_files/search_results.csv"

operation_to_perform = input("\nOperation to perform: \n\nEnrichment (Press 'E') \nClean results (Press 'C') \nPrevent sleep (Press 'P') \n\nYour selection: ")

if operation_to_perform.lower() == "e":
    print(operation_to_perform)
    
    # Set up Chrome options
    chrome_options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")

    # Initialize a new Selenium WebDriver session with options
    driver = webdriver.Chrome(options=chrome_options)

    # Start scrape operation.
    scrapes.entire_enrichment(df, results, driver, output_csv_file_path)

# If the scrape gets interrupted, this options is useful for cleaning the results that the user got so far.
elif operation_to_perform.lower() == "c":
    print(operation_to_perform)
    cleaned_file_path = f'{current_dir}/output_files/cleaned_search_results.csv'
    utils.clean_csv(output_csv_file_path, cleaned_file_path)

elif operation_to_perform.lower() == "p":
    print(operation_to_perform)
    utils.prevent_sleep(6000)

else:
    print("Invalid operation") 

# Clean the results automatically
cleaned_file_path = f'{current_dir}/output_files/cleaned_search_results.csv'
utils.clean_csv(output_csv_file_path, cleaned_file_path)
utils.play_alert_sound()

# Close the driver
driver.quit()
