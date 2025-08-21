"""
Enhanced Doctors Note Upscaler - Main Application
This version includes robust OCR processing with better error handling
and multiple extraction attempts for unclear prescriptions.
"""

import cv2  # OpenCV for camera operations and image processing
import pytesseract  # Tesseract OCR for text extraction from images
from PIL import Image, ImageTk  # PIL for image handling and processing
import os  # For file system operations
import tkinter as tk  # GUI library for file dialogs
from tkinter import filedialog, messagebox  # For file selection and error messages
import sys  # For system operations

# Import our enhanced modules
from config import Config  # Configuration settings
from utils import (enhanced_ocr_extraction, intelligent_text_cleaning, 
                  setup_tesseract, validate_extracted_text_enhanced,
                  preprocess_image_for_ocr)  # Enhanced utility functions

class DoctorsNoteUpscaler:
    """
    Enhanced main class for the Doctors Note Upscaler application.
    Now includes robust OCR processing and better error handling.
    """
    
    def __init__(self):
        """Initialize the application with enhanced setup."""
        print("🏥 Welcome to Enhanced Doctors Note Upscaler!")
        print("=" * 60)
        
        # Set up Tesseract OCR path
        try:
            setup_tesseract()
            print("✅ OCR system initialized successfully")
        except Exception as e:
            print(f"❌ OCR setup failed: {e}")
            print("⚠️  Some features may not work properly")
        
        # Create temp directory if it doesn't exist
        os.makedirs(os.path.dirname(Config.TEMP_IMAGE_PATH), exist_ok=True)
        
    def upload_and_scan_document(self):
        """
        Enhanced function to upload an image file and extract text from it.
        Now includes multiple OCR attempts and better error handling.
        """
        print("\n📁 Starting enhanced file upload process...")
        
        try:
            # Create a temporary tkinter window for file dialog
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            # Open file dialog to let user select an image
            file_path = filedialog.askopenfilename(
                title="Select a prescription image",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                    ("All files", "*.*")
                ]
            )
            
            # Check if user selected a file
            if not file_path:
                print("❌ No file selected. Returning to main menu.")
                root.destroy()
                return
            
            print(f"📄 Processing file: {os.path.basename(file_path)}")
            
            # Enhanced OCR extraction with multiple attempts
            success, raw_text, confidence = enhanced_ocr_extraction(file_path)
            
            if not success:
                print("❌ Could not extract readable text from the image.")
                print("💡 Tips for better results:")
                print("   • Ensure good lighting")
                print("   • Keep the prescription flat and straight")
                print("   • Make sure text is clear and not blurry")
                print("   • Try capturing the image again")
                root.destroy()
                return
            
            print(f"✅ Text extraction completed! (Confidence: {confidence:.1f}%)")
            
            # Display raw extracted text
            print("\n" + "="*30 + " RAW OCR TEXT " + "="*30)
            print(raw_text)
            
            # Apply intelligent text cleaning
            print(f"\n🧹 Applying intelligent text cleaning...")
            cleaned_text = intelligent_text_cleaning(raw_text, confidence)
            
            # Validate the results
            is_valid, quality_score, suggestions = validate_extracted_text_enhanced(cleaned_text, confidence)
            
            print(f"\n📊 Quality Assessment: {quality_score}")
            if suggestions:
                print("💡 Suggestions:")
                for suggestion in suggestions:
                    print(f"   • {suggestion}")
            
            # Display cleaned text
            print("\n" + "="*30 + " PROCESSED TEXT " + "="*30)
            print(cleaned_text)
            print("="*70)
            
            # Offer to save results
            self.offer_save_results(raw_text, cleaned_text, quality_score)
            
            # Clean up
            root.destroy()
            
        except FileNotFoundError:
            print("❌ Error: Selected file not found.")
        except Exception as e:
            print(f"❌ Error processing file: {str(e)}")
            print("💡 Tip: Make sure the image is clear and contains readable text.")
            if Config.is_debug_enabled():
                import traceback
                traceback.print_exc()
    
    def camera_scan_and_process(self):
        """
        Enhanced function to use webcam with better image capture and processing.
        """
        print("\n📷 Starting enhanced camera capture...")
        print("Controls:")
        print("  - Press 's' to capture and scan")
        print("  - Press 'p' to preview/process current frame")
        print("  - Press 'r' to reset and try again")
        print("  - Press 'q' to quit camera mode")
        
        try:
            # Initialize camera with enhanced settings
            cap = cv2.VideoCapture(Config.DEFAULT_CAMERA_INDEX)
            
            if not cap.isOpened():
                print("❌ Error: Could not open camera.")
                print("💡 Troubleshooting tips:")
                print("   • Make sure camera is connected")
                print("   • Close other apps using the camera")
                print("   • Try a different camera index")
                return
            
            # Set enhanced camera properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Enable autofocus
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Enable auto exposure
            
            print("✅ Camera opened successfully!")
            print("🎯 Position your prescription in the camera view...")
            
            frame_count = 0
            best_frame = None
            
            while True:
                # Capture frame-by-frame
                ret, frame = cap.read()
                frame_count += 1
                
                if not ret:
                    print("❌ Error: Failed to capture frame from camera.")
                    break
                
                # Add enhanced instruction overlay
                self.add_camera_overlay(frame, frame_count)
                
                # Display the camera feed
                cv2.imshow('Enhanced Prescription Scanner', frame)
                
                # Wait for key press
                key = cv2.waitKey(1) & 0xFF
                
                # Handle different key presses
                if key == ord('s'):
                    print("\n📸 Capturing image...")
                    best_frame = frame.copy()
                    cv2.imwrite(Config.TEMP_IMAGE_PATH, best_frame)
                    self._process_captured_image_enhanced()
                    
                elif key == ord('p'):
                    print("\n👁️ Preview processing current frame...")
                    temp_preview_path = Config.TEMP_IMAGE_PATH.replace('.jpg', '_preview.jpg')
                    cv2.imwrite(temp_preview_path, frame)
                    self._preview_frame_quality(temp_preview_path)
                    
                elif key == ord('r'):
                    print("\n🔄 Reset - continue capturing...")
                    best_frame = None
                    
                elif key == ord('q'):
                    print("👋 Exiting camera mode...")
                    break
            
            # Clean up camera resources
            cap.release()
            cv2.destroyAllWindows()
            
        except Exception as e:
            print(f"❌ Camera error: {str(e)}")
            print("💡 Try checking your camera connection or permissions.")
            if Config.is_debug_enabled():
                import traceback
                traceback.print_exc()
    
    def add_camera_overlay(self, frame, frame_count):
        """
        Add helpful overlay information to camera frame.
        
        Args:
            frame: OpenCV frame
            frame_count: Current frame number
        """
        height, width = frame.shape[:2]
        
        # Add main instructions
        cv2.putText(frame, "Position prescription clearly in view", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add control instructions
        cv2.putText(frame, "Controls: 's'=Scan, 'p'=Preview, 'r'=Reset, 'q'=Quit", 
                   (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add frame guidelines
        margin = 50
        cv2.rectangle(frame, (margin, margin), (width - margin, height - margin), (0, 255, 255), 2)
        cv2.putText(frame, "Keep prescription within yellow border", 
                   (margin, margin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Add quality indicator
        quality_color = (0, 255, 0) if frame_count % 30 < 15 else (0, 255, 255)
        cv2.circle(frame, (width - 30, 30), 10, quality_color, -1)
    
    def _preview_frame_quality(self, temp_path):
        """
        Preview the quality of current frame without full processing.
        
        Args:
            temp_path: Path to temporary preview image
        """
        try:
            # Quick quality assessment
            img = cv2.imread(temp_path, cv2.IMREAD_GRAYSCALE)
            
            # Calculate image sharpness (Laplacian variance)
            laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
            
            # Calculate brightness
            brightness = img.mean()
            
            # Provide quality feedback
            if laplacian_var > 100:
                sharpness_status = "✅ Good sharpness"
            elif laplacian_var > 50:
                sharpness_status = "⚠️ Moderate sharpness"
            else:
                sharpness_status = "❌ Poor sharpness - move closer or refocus"
            
            if 80 < brightness < 180:
                brightness_status = "✅ Good lighting"
            elif brightness < 80:
                brightness_status = "❌ Too dark - add more light"
            else:
                brightness_status = "❌ Too bright - reduce lighting"
            
            print(f"📊 Frame Quality Preview:")
            print(f"   {sharpness_status} (score: {laplacian_var:.1f})")
            print(f"   {brightness_status} (score: {brightness:.1f})")
            
            # Clean up preview file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except Exception as e:
            print(f"⚠️ Could not assess frame quality: {e}")
    
    def _process_captured_image_enhanced(self):
        """
        Enhanced processing of captured image with detailed feedback.
        """
        try:
            print("🔄 Processing captured image with enhanced OCR...")
            
            # Use enhanced OCR extraction
            success, raw_text, confidence = enhanced_ocr_extraction(Config.TEMP_IMAGE_PATH)
            
            if not success:
                print("❌ Could not extract readable text from captured image.")
                print("💡 Try these improvements:")
                print("   • Better lighting on the prescription")
                print("   • Hold camera steadier")
                print("   • Move closer to the text")
                print("   • Ensure prescription is flat")
                return
            
            print(f"✅ Text extraction successful! (Confidence: {confidence:.1f}%)")
            print("\n" + "="*30 + " RAW OCR TEXT " + "="*30)
            print(raw_text)
            
            # Apply intelligent cleaning
            print("\n🧹 Applying intelligent text processing...")
            cleaned_text = intelligent_text_cleaning(raw_text, confidence)
            
            # Validate results
            is_valid, quality_score, suggestions = validate_extracted_text_enhanced(cleaned_text, confidence)
            
            print(f"\n📊 Processing Quality: {quality_score}")
            if suggestions:
                print("💡 Recommendations:")
                for suggestion in suggestions:
                    print(f"   • {suggestion}")
            
            # Display final results
            print("\n" + "="*30 + " PROCESSED TEXT " + "="*30)
            print(cleaned_text)
            print("="*70)
            
            # Offer to save or retry
            if quality_score in ["POOR", "FAILED"]:
                print("\n🔄 Would you like to try capturing again? (Press 'r' in camera view)")
            else:
                self.offer_save_results(raw_text, cleaned_text, quality_score)
            
        except Exception as e:
            print(f"❌ Error processing captured image: {str(e)}")
            if Config.is_debug_enabled():
                import traceback
                traceback.print_exc()
    
    def offer_save_results(self, raw_text, cleaned_text, quality_score):
        """
        Offer to save processing results to a file.
        
        Args:
            raw_text: Original OCR text
            cleaned_text: Processed text
            quality_score: Quality assessment
        """
        try:
            response = input("\n💾 Would you like to save these results? (y/N): ").strip().lower()
            
            if response in ['y', 'yes']:
                # Create results directory
                results_dir = "results"
                os.makedirs(results_dir, exist_ok=True)
                
                # Generate filename with timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"prescription_scan_{timestamp}.txt"
                filepath = os.path.join(results_dir, filename)
                
                # Save results
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Doctors Note Upscaler - Scan Results\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Quality Score: {quality_score}\n")
                    f.write("="*60 + "\n\n")
                    
                    f.write("RAW OCR TEXT:\n")
                    f.write("-"*30 + "\n")
                    f.write(raw_text + "\n\n")
                    
                    f.write("PROCESSED TEXT:\n")
                    f.write("-"*30 + "\n")
                    f.write(cleaned_text + "\n")
                
                print(f"✅ Results saved to: {filepath}")
                
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
    
    def show_menu(self):
        """
        Enhanced main menu with additional options.
        """
        while True:
            print("\n" + "="*60)
            print("🏥 ENHANCED DOCTORS NOTE UPSCALER - MAIN MENU")
            print("="*60)
            print("Choose an option:")
            print("1. 📁 Upload image file to scan")
            print("2. 📷 Use webcam to capture and scan")
            print("3. 🔧 Test OCR with sample image")
            print("4. ⚙️ Configure settings")
            print("5. ❓ Help and Tips")
            print("6. 📊 View recent results")
            print("7. 🚪 Exit")
            print("-" * 60)
            
            try:
                choice = input("Enter your choice (1-7): ").strip()
                
                if choice == '1':
                    self.upload_and_scan_document()
                elif choice == '2':
                    self.camera_scan_and_process()
                elif choice == '3':
                    self.test_ocr_functionality()
                elif choice == '4':
                    self.configure_settings()
                elif choice == '5':
                    self.show_enhanced_help()
                elif choice == '6':
                    self.view_recent_results()
                elif choice == '7':
                    print("👋 Thank you for using Enhanced Doctors Note Upscaler!")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-7.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
    
    def test_ocr_functionality(self):
        """Test OCR with built-in functionality check."""
        print("\n🧪 Testing OCR functionality...")
        
        try:
            # Test Tesseract installation
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract version: {version}")
            
            # Test with a simple image (if available)
            test_image_path = "test_prescription.jpg"  # User can provide this
            
            if os.path.exists(test_image_path):
                print(f"📄 Testing with: {test_image_path}")
                success, raw_text, confidence = enhanced_ocr_extraction(test_image_path)
                
                if success:
                    print(f"✅ Test successful! Confidence: {confidence:.1f}%")
                    print(f"Preview: '{raw_text[:100]}...'")
                else:
                    print("❌ Test failed - could not extract text")
            else:
                print("💡 To test with your own image, place 'test_prescription.jpg' in the application folder")
                
        except Exception as e:
            print(f"❌ OCR test failed: {e}")
    
    def configure_settings(self):
        """Allow user to configure application settings."""
        print("\n⚙️ Configuration Settings")
        print("-" * 40)
        print(f"Current camera index: {Config.DEFAULT_CAMERA_INDEX}")
        print(f"Current camera resolution: {Config.CAMERA_WIDTH}x{Config.CAMERA_HEIGHT}")
        print(f"Debug mode: {Config.DEBUG_MODE}")
        print(f"Minimum text length: {Config.MIN_TEXT_LENGTH}")
        
        print("\nConfiguration options:")
        print("1. Change camera index")
        print("2. Toggle debug mode")
        print("3. View all settings")
        print("4. Back to main menu")
        
        choice = input("Choose option (1-4): ").strip()
        
        if choice == '1':
            try:
                new_index = int(input("Enter new camera index (0-9): "))
                Config.DEFAULT_CAMERA_INDEX = new_index
                print(f"✅ Camera index set to: {new_index}")
            except ValueError:
                print("❌ Invalid camera index")
                
        elif choice == '2':
            Config.DEBUG_MODE = not Config.DEBUG_MODE
            print(f"✅ Debug mode: {'enabled' if Config.DEBUG_MODE else 'disabled'}")
            
        elif choice == '3':
            Config.print_config_info()
    
    def show_enhanced_help(self):
        """Display comprehensive help information."""
        print("\n" + "="*60)
        print("❓ ENHANCED HELP AND TIPS")
        print("="*60)
        
        print("📋 For BEST results:")
        print("  • Use good, even lighting (natural light is best)")
        print("  • Keep the prescription completely flat")
        print("  • Ensure text is in focus and not blurry")
        print("  • Fill the camera frame with the prescription")
        print("  • Hold the camera steady when capturing")
        print("  • Use high contrast (dark text on white paper)")
        
        print("\n🔧 TROUBLESHOOTING common issues:")
        print("  • No text detected: Improve lighting and focus")
        print("  • Garbled text: Move closer or use better lighting")
        print("  • Camera won't open: Close other camera apps")
        print("  • Low confidence scores: Retake with better conditions")
        print("  • Partial text: Ensure entire prescription is in frame")
        
        print("\n💊 MEDICAL abbreviations automatically handled:")
        print("  • Dosages: mg→milligrams, ml→milliliters, mcg→micrograms")
        print("  • Frequency: bid→twice daily, tid→three times daily, qd→once daily")
        print("  • Routes: po→by mouth, im→injection, top→topical")
        print("  • Timing: ac→before meals, pc→after meals, hs→at bedtime")
        
        print("\n🎯 UNDERSTANDING confidence scores:")
        print("  • 80-100%: Excellent - text should be very accurate")
        print("  • 60-79%: Good - most text accurate, verify important details")
        print("  • 40-59%: Acceptable - check all medication names and doses")
        print("  • Below 40%: Poor - manually verify all information")
        
        print("\n📱 CAMERA controls:")
        print("  • 's' key: Capture and process image")
        print("  • 'p' key: Preview quality without processing")
        print("  • 'r' key: Reset and continue")
        print("  • 'q' key: Quit camera mode")
        
        print("="*60)
    
    def view_recent_results(self):
        """View recently saved scan results."""
        results_dir = "results"
        
        if not os.path.exists(results_dir):
            print("📂 No saved results found.")
            return
        
        result_files = [f for f in os.listdir(results_dir) if f.endswith('.txt')]
        
        if not result_files:
            print("📂 No saved results found.")
            return
        
        print(f"\n📊 Found {len(result_files)} saved result(s):")
        result_files.sort(reverse=True)  # Most recent first
        
        for i, filename in enumerate(result_files[:5], 1):  # Show last 5
            filepath = os.path.join(results_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    timestamp = lines[1].strip() if len(lines) > 1 else "Unknown"
                    quality = lines[2].strip() if len(lines) > 2 else "Unknown"
                
                print(f"  {i}. {filename}")
                print(f"     {timestamp}")
                print(f"     {quality}")
                print()
            except Exception as e:
                print(f"  {i}. {filename} (Error reading: {e})")

def main():
    """
    Enhanced main function with better error handling.
    """
    try:
        print("🚀 Starting Enhanced Doctors Note Upscaler...")
        
        # Create an instance of our enhanced application
        app = DoctorsNoteUpscaler()
        
        # Show the main menu to start interaction
        app.show_menu()
        
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user. Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        print("💡 Please check your installation and try again.")
        if Config.is_debug_enabled():
            import traceback
            traceback.print_exc()
    finally:
        # Clean up any temporary files
        try:
            from utils import cleanup_temp_files
            cleanup_temp_files()
        except:
            pass

if __name__ == "__main__":
    main()