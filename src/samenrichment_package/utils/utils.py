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

def get_queries(row_data):
    # Queries stored in a dictionary
    queries = {
        "linkedin": f"site:linkedin.com/in/ {row_data['Startup']}, {row_data['HQ Location (World)']},founder, co-founder, co founder, ceo",
        "crunchbase": f"site:crunchbase.com {row_data['Startup']}",
    }

    # Scrape packages stored in a list of dictionaries
    scrape_packages = [
        {"name": "linkedin", "query": queries["linkedin"], "link": ""},
        {"name": "crunchbase", "query": queries["crunchbase"], "link": ""}
    ]
    return {"Queries": queries, "Scrape packages": scrape_packages}