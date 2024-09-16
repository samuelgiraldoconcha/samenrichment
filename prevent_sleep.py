import subprocess
import time

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

# Keep the Mac awake for 1 hour (3600 seconds)
prevent_sleep(3600)
