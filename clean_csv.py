import pandas as pd

# Read the CSV file
df = pd.read_csv('search_results.csv')

# Define error keywords that indicate rows with errors
error_keywords = [
    "Error fetching result",
    "no such element",
    "Message:",
    "Stacktrace:",
    "Session info",
    "chromedriver",
    "selenium.dev",
    "Unable to locate element"
]

# Function to check if a row contains any of the error messages
def contains_error(row):
    return any(keyword.lower() in str(row).lower() for keyword in error_keywords)

# Filter out rows that contain error messages
cleaned_df = df[~df.apply(lambda row: contains_error(row.to_string()), axis=1)]

# Save the cleaned DataFrame to a new CSV
cleaned_df.to_csv('cleaned_search_results.csv', index=False)

print("Cleaned CSV saved as 'cleaned_search_results.csv'.")
