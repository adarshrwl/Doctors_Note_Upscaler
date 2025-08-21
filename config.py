"""
Configuration file for Doctors Note Upscaler
This file contains all the settings and configurations used throughout the application.
Having settings in one place makes it easy to modify the application's behavior.
"""

import os  # For file path operations

class Config:
    """
    Configuration class containing all application settings.
    This class uses class variables to store settings that can be accessed
    from anywhere in the application without creating an instance.
    """
    
    # ===== FILE PATHS =====
    # Path where temporary images (like webcam captures) are saved
    # We use a 'temp' folder in the current directory to keep things organized
    TEMP_IMAGE_PATH = os.path.join("temp", "captured_image.jpg")
    
    # ===== TESSERACT OCR SETTINGS =====
    # Common installation paths for Tesseract OCR on Windows
    # The application will try these paths to find Tesseract automatically
    TESSERACT_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",  # Default 64-bit installation
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",  # 32-bit installation
        r"C:\Users\%USERNAME%\AppData\Local\Tesseract-OCR\tesseract.exe",  # User installation
        "tesseract"  # If Tesseract is in system PATH
    ]
    
    # ===== CAMERA SETTINGS =====
    # Default camera index (0 is usually the built-in webcam)
    DEFAULT_CAMERA_INDEX = 0
    
    # Camera resolution settings for better image quality
    # Higher resolution = better OCR accuracy but slower processing
    CAMERA_WIDTH = 1280
    CAMERA_HEIGHT = 720
    
    # ===== OCR SETTINGS =====
    # Tesseract OCR configuration options
    # These settings optimize OCR for medical text recognition
    TESSERACT_CONFIG = '--oem 3 --psm 6'  
    # oem 3: Use both legacy and LSTM OCR engine modes
    # psm 6: Assume a single uniform block of text
    
    # ===== TEXT PROCESSING SETTINGS =====
    # Minimum text length to consider valid (helps filter out noise)
    MIN_TEXT_LENGTH = 3
    
    # Words that are commonly unclear in prescriptions
    # These will be flagged for manual verification
    UNCLEAR_INDICATORS = [
        "unclear",
        "illegible", 
        "???",
        "...",
        "____"
    ]
    
    # ===== APPLICATION SETTINGS =====
    # Application name and version info
    APP_NAME = "Doctors Note Upscaler"
    APP_VERSION = "1.0.0"
    
    # Enable/disable debug mode for additional logging
    DEBUG_MODE = False  # Set to True for troubleshooting
    
    # ===== DISPLAY SETTINGS =====
    # Console output formatting
    SEPARATOR_LENGTH = 70  # Length of separator lines in output
    
    # Colors for console output (if terminal supports it)
    # These are ANSI color codes that work in most terminals
    COLORS = {
        'GREEN': '\033[92m',    # Success messages
        'RED': '\033[91m',      # Error messages  
        'YELLOW': '\033[93m',   # Warning messages
        'BLUE': '\033[94m',     # Info messages
        'RESET': '\033[0m'      # Reset to default color
    }
    
    @classmethod
    def get_temp_dir(cls):
        """
        Get the temporary directory path and create it if it doesn't exist.
        This is a class method, which means you can call it without creating
        an instance of the Config class.
        
        Returns:
            str: Path to the temporary directory
        """
        temp_dir = os.path.dirname(cls.TEMP_IMAGE_PATH)
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    @classmethod
    def is_debug_enabled(cls):
        """
        Check if debug mode is enabled.
        
        Returns:
            bool: True if debug mode is enabled, False otherwise
        """
        return cls.DEBUG_MODE
    
    @classmethod
    def print_config_info(cls):
        """
        Print current configuration settings.
        Useful for troubleshooting and setup verification.
        """
        print(f"\n📋 {cls.APP_NAME} v{cls.APP_VERSION} Configuration:")
        print("-" * 40)
        print(f"Temp Image Path: {cls.TEMP_IMAGE_PATH}")
        print(f"Camera Resolution: {cls.CAMERA_WIDTH}x{cls.CAMERA_HEIGHT}")
        print(f"Debug Mode: {cls.DEBUG_MODE}")
        print(f"Min Text Length: {cls.MIN_TEXT_LENGTH}")
        print("-" * 40)

# Example of how to use this configuration file:
# 
# From other files, you can import and use these settings like this:
# 
# from config import Config
# 
# # Access settings
# temp_path = Config.TEMP_IMAGE_PATH
# camera_width = Config.CAMERA_WIDTH
# 
# # Use class methods
# Config.print_config_info()
# debug_enabled = Config.is_debug_enabled()