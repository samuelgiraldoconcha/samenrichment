import pandas as pd
import subprocess
import time
import pygame
import os
from selenium.webdriver.common.by import By
import random

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

def detect_reCAPTCHA(driver):
    if driver.find_elements(By.CSS_SELECTOR, 'div.g-recaptcha'):
        play_alert_sound()
        print("reCAPTCHA detected. Please complete the CAPTCHA manually.")
        input("Press Enter after completing the CAPTCHA...")
        driver.refresh()
        time.sleep(2.85 + 1.5*random.random())