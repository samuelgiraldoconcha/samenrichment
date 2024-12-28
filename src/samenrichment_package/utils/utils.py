import pandas as pd
import subprocess
import time
import pygame
import os
import random
from playwright.async_api import async_playwright
import asyncio

def play_alert_sound():
    # Initialize Pygame mixer
    pygame.mixer.init()
    # Load the sound file
    pygame.mixer.music.load('samenrichment_package/utils/assets/alert_sound.wav')  # Replace with the path to your sound file
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # Wait for sound to finish playing
        pygame.time.Clock().tick(10)

def prevent_sleep(duration):
    print("Preventing screen sleep...")
    # Run the 'caffeinate' command to prevent sleep
    process = subprocess.Popen(['caffeinate', '-u', '-t', str(duration)])
    
    # Keep the script running for the specified duration
    try:
        time.sleep(duration)
    except KeyboardInterrupt:
        print("Script interrupted.")
    finally:
        # Terminate the caffeinate process when the script ends
        process.terminate()
        print("Resuming normal sleep mode.")

def clean_csv(input_file: str, output_file: str):
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)

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
        cleaned_df_csv = cleaned_df.to_csv(output_file, index=False)

        print("Cleaned CSV saved as 'cleaned_search_results.csv'.")
    except pd.errors.EmptyDataError:
        print(f"No data found in {input_file}.")
        return
    return cleaned_df_csv

async def detect_reCAPTCHA(page):
    # Check for the presence of the reCAPTCHA element
    captcha_count = await page.locator('div.g-recaptcha').count()
    if captcha_count > 0:
        play_alert_sound()
        print("reCAPTCHA detected. Please complete the CAPTCHA manually.")

def find_blank_cells(table, column_mapping, column_idx, worksheet_start, worksheet_end):
    """
    Find blank cells in a specific column within a given row range.
    
    Args:
        table: List of dictionaries containing worksheet data
        column_mapping: Dictionary mapping column names to indices
        column_idx: The column index to check for blank cells
        start_row: Starting row number (inclusive)
        end_row: Ending row number (exclusive)
    
    Returns:
        List of [row_number, column_idx, try_number] for blank cells
    """
    blank_cells = []

    column_name = next(key for key, value in column_mapping.items() if value == column_idx)
    
    for i in range(worksheet_start, worksheet_end):
        actual_row = table[i-2]  # Convert back to table row number
        actual_row_num = i
        
        # Check if the column exists and handle None values
        cell_value = actual_row.get(column_name)
        if cell_value is None or (isinstance(cell_value, str) and cell_value.strip() == ""):
            blank_cells.append([actual_row_num, column_idx, cell_value])
            
    return blank_cells

def extract_profile(url: str) -> str:
    """
    Extracts the company profile name from a Crunchbase URL.
    
    Args:
        url (str): The Crunchbase URL
        
    Returns:
        str: The company profile name (last part of the URL)
        
    Example:
        >>> extract_profile("https://www.crunchbase.com/organization/elythea", "crunchbase")
        'elythea'
    """
    # Remove any trailing whitespace and split by '/'
    clean_url = url.strip()
    parts = clean_url.split('/')
    
    # Return the last non-empty part
    return parts[-1].strip()