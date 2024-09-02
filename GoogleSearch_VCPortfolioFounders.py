from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time

# Set up Chrome options
chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
chrome_options.add_argument(f"user-agent={user_agent}")

# Initialize a new Selenium WebDriver session with options
driver = webdriver.Chrome(options=chrome_options)

# Load the CSV file
csv_file_path = 'LinkedIn profiles scrape test.csv'  # Change this to the path of your CSV file
df = pd.read_csv(csv_file_path, header=None)

# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    # Join columns with commas and add the suffix
    query = ', '.join(row.dropna().astype(str).tolist()) + ', founder, linkedin'
    
    # Encode the query for the URL
    search_query = '+'.join(query.split())
    
    # Load the Google search results page
    driver.get(f"https://www.google.com/search?q={search_query}")
    
    # Wait for the dynamic content to load (you might need to adjust the sleep time)
    time.sleep(3)
    
    # Find the first result link
    try:
        element = driver.find_element(By.CSS_SELECTOR, 'a[jsname="UWckNb"]')
        # Print the URL of the first result
        print(f"Results for query '{query}': {element.get_attribute('href')}")
    except Exception as e:
        print(f"Error fetching results for query '{query}': {e}")

# Close the driver
driver.quit()
