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
csv_file_path = 'template.csv'  # Change this to the path of your CSV file
df = pd.read_csv(csv_file_path)

# List to store results
results = []

# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    # Construct query using 'Startup' and 'Firstname'
    startup = row['Startup']
    founder_first_name = row['Firstname']
    query = f"{startup} {founder_first_name}, founder, linkedin"
    
    # Encode the query for the URL
    search_query = '+'.join(query.split())
    
    # Load the Google search results page
    driver.get(f"https://www.google.com/search?q={search_query}")
    
    # Wait for the dynamic content to load (you might need to adjust the sleep time)
    time.sleep(3)
    
    # Find the first result link
    try:
        element = driver.find_element(By.CSS_SELECTOR, 'a[jsname="UWckNb"]')
        # Append result to the list
        result_url = element.get_attribute('href')
        print(f"{query}: {element.get_attribute('href')}")

    except Exception as e:
        # Append error message to the list
        results.append({
            'Query': query,
            'URL': f"Error fetching result: {e}"
        })
        print(f"Error fetching results for query '{query}': {e}")
        
    # Append results with each keyword and URL
    results.append({
        'Startup': startup,
        'Firstname': founder_first_name,
        'URL': result_url
    })

# Convert results to a DataFrame
results_df = pd.DataFrame(results)

# Save the results to a CSV file
output_csv_file_path = 'search_results.csv'  # Change this to your desired output file path
results_df.to_csv(output_csv_file_path, index=False)

# Close the driver
driver.quit()
