from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
import Utils

# Set up Chrome options
chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
chrome_options.add_argument(f"user-agent={user_agent}")

# Initialize a new Selenium WebDriver session with options
driver = webdriver.Chrome(options=chrome_options)

# Load the CSV file
csv_file_path = 'template.csv'  # Change this to the path of your CSV file
df = pd.read_csv(csv_file_path)

# Replace NaN with empty strings
df.fillna('', inplace=True)

# List to store results
results = []

# Iterate over each row in the DataFrame. 
Utils.linkedInProdileEnrichment(df, results, driver)

# Convert results to a DataFrame
results_df = pd.DataFrame(results)

# Save the results to a CSV file
output_csv_file_path = 'search_results.csv'  # Change this to your desired output file path
results_df.to_csv(output_csv_file_path, index=False)

# Close the driver
driver.quit()
