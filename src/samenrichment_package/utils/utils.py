import pandas as pd
import subprocess
import time
import pygame
import os

def save_results_periodically(output, last_save_time, save_interval, output_csv_file_path):
    current_time = time.time()
    if current_time - last_save_time >= save_interval:
        results_df = pd.DataFrame(output)
        results_df.to_csv(output_csv_file_path, index=False)
        print(f"Results saved to {output_csv_file_path} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return current_time  # Update last_save_time
    return last_save_time  # No save, return the old last_save_times

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

    return cleaned_df_csv


