import os
import sys

# Add Homebrew lib path to environment variables
# We need to do this BEFORE importing weasyprint
if sys.platform == 'darwin':
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')

try:
    from renderer import ReportRenderer
    print("Successfully imported ReportRenderer")
    
    # If import works, run the test
    import test_all_features
    print("Test completed")
except OSError as e:
    print(f"Failed to import: {e}")
    # Try to debug by listing files in /opt/homebrew/lib matching libgobject
    import glob
    print("Found libraries:")
    print(glob.glob("/opt/homebrew/lib/libgobject*"))
except Exception as e:
    print(f"An error occurred: {e}")
