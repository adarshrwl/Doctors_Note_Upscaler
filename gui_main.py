"""
GUI Main Application for Doctors Note Upscaler
This file creates the main GUI window using PyQt6 and integrates with the existing application logic.
"""

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QTextEdit, QLabel, QMenuBar, 
                            QStatusBar, QFileDialog, QMessageBox, QSplitter,
                            QFrame, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont, QIcon, QPalette, QColor

# Import your existing modules
from config import Config
from utils import clean_messy_text, setup_tesseract
from main import DoctorsNoteUpscaler

class OCRWorker(QThread):
    """
    Worker thread for OCR processing to keep GUI responsive.
    This prevents the interface from freezing during OCR operations.
    """
    finished = pyqtSignal(str, str)  # raw_text, cleaned_text
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        
    def run(self):
        try:
            import pytesseract
            from PIL import Image
            
            self.progress.emit("Loading image...")
            
            # Load and process the image
            image = Image.open(self.image_path)
            
            # Convert image to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            self.progress.emit("Extracting text...")
            
            # Extract text using Tesseract OCR
            raw_text = pytesseract.image_to_string(image, config=Config.TESSERACT_CONFIG)
            
            if not raw_text.strip():
                self.error.emit("No text found in the image. Please try with a clearer image.")
                return
            
            self.progress.emit("Cleaning text...")
            
            # Clean the messy text
            cleaned_text = clean_messy_text(raw_text)
            
            self.finished.emit(raw_text, cleaned_text)
            
        except Exception as e:
            self.error.emit(f"Error processing image: {str(e)}")

class CameraWindow(QWidget):
    """
    Separate window for camera capture functionality.
    """
    image_captured = pyqtSignal(str)  # image_path
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
    def init_ui(self):
        self.setWindowTitle("Camera Capture - Doctors Note Upscaler")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Position your prescription in the camera view and click 'Capture'")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("font-size: 14px; padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        layout.addWidget(instructions)
        
        # Camera display area (placeholder)
        self.camera_label = QLabel("Camera feed will appear here")
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setStyleSheet("border: 2px solid #ccc; background-color: #f5f5f5;")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.camera_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.capture_btn = QPushButton("📸 Capture Image")
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.capture_btn.clicked.connect(self.capture_image)
        
        self.close_btn = QPushButton("❌ Close Camera")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.capture_btn)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def showEvent(self, event):
        """Initialize camera when window is shown."""
        super().showEvent(event)
        self.start_camera()
        
    def closeEvent(self, event):
        """Clean up camera when window is closed."""
        self.stop_camera()
        super().closeEvent(event)
        
    def start_camera(self):
        """Start the camera feed."""
        try:
            import cv2
            self.camera = cv2.VideoCapture(Config.DEFAULT_CAMERA_INDEX)
            
            if not self.camera.isOpened():
                QMessageBox.warning(self, "Camera Error", 
                                  "Could not open camera. Please check your camera connection.")
                return
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            
            self.timer.start(30)  # Update every 30ms for smooth video
            self.camera_label.setText("Camera starting...")
            
        except ImportError:
            QMessageBox.critical(self, "Missing Dependency", 
                               "OpenCV is required for camera functionality. Please install it with: pip install opencv-python")
        except Exception as e:
            QMessageBox.critical(self, "Camera Error", f"Error starting camera: {str(e)}")
    
    def stop_camera(self):
        """Stop the camera feed."""
        if self.timer.isActive():
            self.timer.stop()
        
        if self.camera and self.camera.isOpened():
            self.camera.release()
            
    def update_frame(self):
        """Update camera frame."""
        if not self.camera or not self.camera.isOpened():
            return
            
        try:
            import cv2
            from PyQt6.QtGui import QImage, QPixmap
            
            ret, frame = self.camera.read()
            if ret:
                # Convert frame to Qt format
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                # Scale image to fit label
                pixmap = QPixmap.fromImage(qt_image)
                scaled_pixmap = pixmap.scaled(self.camera_label.size(), 
                                           Qt.AspectRatioMode.KeepAspectRatio, 
                                           Qt.TransformationMode.SmoothTransformation)
                self.camera_label.setPixmap(scaled_pixmap)
                
        except Exception as e:
            print(f"Error updating frame: {e}")
    
    def capture_image(self):
        """Capture current frame and save it."""
        if not self.camera or not self.camera.isOpened():
            QMessageBox.warning(self, "Camera Error", "Camera is not available.")
            return
            
        try:
            import cv2
            
            ret, frame = self.camera.read()
            if ret:
                # Save the captured frame
                os.makedirs(os.path.dirname(Config.TEMP_IMAGE_PATH), exist_ok=True)
                cv2.imwrite(Config.TEMP_IMAGE_PATH, frame)
                
                # Emit signal with image path
                self.image_captured.emit(Config.TEMP_IMAGE_PATH)
                
                # Show success message
                QMessageBox.information(self, "Success", "Image captured successfully!")
                
                # Close camera window
                self.close()
                
        except Exception as e:
            QMessageBox.critical(self, "Capture Error", f"Error capturing image: {str(e)}")

class MainWindow(QMainWindow):
    """
    Main application window with modern GUI design.
    """
    
    def __init__(self):
        super().__init__()
        self.ocr_worker = None
        self.camera_window = None
        self.init_ui()
        self.setup_tesseract()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"{Config.APP_NAME} - v{Config.APP_VERSION}")
        self.setGeometry(100, 100, 1000, 700)
        
        # Set application icon (if available)
        # self.setWindowIcon(QIcon('icon.png'))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title section
        title_layout = self.create_title_section()
        main_layout.addLayout(title_layout)
        
        # Buttons section
        button_layout = self.create_button_section()
        main_layout.addLayout(button_layout)
        
        # Results section
        results_layout = self.create_results_section()
        main_layout.addLayout(results_layout)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        central_widget.setLayout(main_layout)
        
        # Apply modern styling
        self.apply_modern_style()
        
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        help_action = QAction('How to Use', self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_title_section(self):
        """Create the title section of the interface."""
        layout = QVBoxLayout()
        
        # Main title
        title_label = QLabel("🏥 Doctors Note Upscaler")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            padding: 20px;
        """)
        
        # Subtitle
        subtitle_label = QLabel("Extract and clean text from medical prescriptions")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("""
            font-size: 16px;
            color: #7f8c8d;
            padding-bottom: 20px;
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        
        return layout
    
    def create_button_section(self):
        """Create the main action buttons."""
        layout = QHBoxLayout()
        layout.setSpacing(20)
        
        # Upload button
        self.upload_btn = QPushButton("📁 Upload Prescription Image")
        self.upload_btn.setMinimumSize(250, 60)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.upload_btn.clicked.connect(self.upload_image)
        
        # Camera button
        self.camera_btn = QPushButton("📷 Capture via Webcam")
        self.camera_btn.setMinimumSize(250, 60)
        self.camera_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.camera_btn.clicked.connect(self.capture_via_camera)
        
        layout.addStretch()
        layout.addWidget(self.upload_btn)
        layout.addWidget(self.camera_btn)
        layout.addStretch()
        
        return layout
    
    def create_results_section(self):
        """Create the results display section."""
        layout = QVBoxLayout()
        
        # Section title
        results_title = QLabel("📋 OCR Results")
        results_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px 0;
        """)
        
        # Create splitter for raw and cleaned text
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Raw text section
        raw_frame = QFrame()
        raw_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        raw_layout = QVBoxLayout()
        
        raw_title = QLabel("Raw OCR Text")
        raw_title.setStyleSheet("font-weight: bold; color: #e74c3c; padding: 5px;")
        
        self.raw_text_edit = QTextEdit()
        self.raw_text_edit.setPlaceholderText("Raw OCR text will appear here...")
        self.raw_text_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background-color: #fdf2e9;
            }
        """)
        
        raw_layout.addWidget(raw_title)
        raw_layout.addWidget(self.raw_text_edit)
        raw_frame.setLayout(raw_layout)
        
        # Cleaned text section
        cleaned_frame = QFrame()
        cleaned_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        cleaned_layout = QVBoxLayout()
        
        cleaned_title = QLabel("Cleaned & Processed Text")
        cleaned_title.setStyleSheet("font-weight: bold; color: #27ae60; padding: 5px;")
        
        self.cleaned_text_edit = QTextEdit()
        self.cleaned_text_edit.setPlaceholderText("Processed text will appear here...")
        self.cleaned_text_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Arial', sans-serif;
                font-size: 13px;
                background-color: #eafaf1;
            }
        """)
        
        cleaned_layout.addWidget(cleaned_title)
        cleaned_layout.addWidget(self.cleaned_text_edit)
        cleaned_frame.setLayout(cleaned_layout)
        
        # Add frames to splitter
        splitter.addWidget(raw_frame)
        splitter.addWidget(cleaned_frame)
        splitter.setSizes([500, 500])  # Equal sizes
        
        layout.addWidget(results_title)
        layout.addWidget(splitter)
        
        return layout
    
    def apply_modern_style(self):
        """Apply modern styling to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QWidget {
                background-color: #ecf0f1;
            }
            QMenuBar {
                background-color: #34495e;
                color: white;
                padding: 5px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #2c3e50;
            }
            QStatusBar {
                background-color: #34495e;
                color: white;
                padding: 5px;
            }
        """)
    
    def setup_tesseract(self):
        """Set up Tesseract OCR."""
        try:
            setup_tesseract()
            self.status_bar.showMessage("Tesseract OCR ready")
        except Exception as e:
            QMessageBox.critical(self, "Setup Error", 
                               f"Failed to setup Tesseract OCR: {str(e)}")
            self.status_bar.showMessage("Tesseract setup failed")
    
    def upload_image(self):
        """Handle image upload and processing."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Prescription Image",
            "",
            "Image files (*.png *.jpg *.jpeg *.gif *.bmp *.tiff);;All files (*.*)"
        )
        
        if file_path:
            self.process_image(file_path)
    
    def capture_via_camera(self):
        """Open camera window for image capture."""
        self.camera_window = CameraWindow()
        self.camera_window.image_captured.connect(self.process_image)
        self.camera_window.show()
    
    def process_image(self, image_path):
        """Process the selected/captured image with OCR."""
        self.status_bar.showMessage("Processing image...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Disable buttons during processing
        self.upload_btn.setEnabled(False)
        self.camera_btn.setEnabled(False)
        
        # Clear previous results
        self.raw_text_edit.clear()
        self.cleaned_text_edit.clear()
        
        # Start OCR worker thread
        self.ocr_worker = OCRWorker(image_path)
        self.ocr_worker.finished.connect(self.on_ocr_finished)
        self.ocr_worker.error.connect(self.on_ocr_error)
        self.ocr_worker.progress.connect(self.on_ocr_progress)
        self.ocr_worker.start()
    
    def on_ocr_finished(self, raw_text, cleaned_text):
        """Handle OCR completion."""
        self.raw_text_edit.setPlainText(raw_text)
        self.cleaned_text_edit.setPlainText(cleaned_text)
        
        self.status_bar.showMessage("OCR processing completed successfully")
        self.progress_bar.setVisible(False)
        
        # Re-enable buttons
        self.upload_btn.setEnabled(True)
        self.camera_btn.setEnabled(True)
    
    def on_ocr_error(self, error_message):
        """Handle OCR errors."""
        QMessageBox.warning(self, "OCR Error", error_message)
        
        self.status_bar.showMessage("OCR processing failed")
        self.progress_bar.setVisible(False)
        
        # Re-enable buttons
        self.upload_btn.setEnabled(True)
        self.camera_btn.setEnabled(True)
    
    def on_ocr_progress(self, message):
        """Handle OCR progress updates."""
        self.status_bar.showMessage(message)
    
    def show_help(self):
        """Show help dialog."""
        help_text = """
        <h2>How to Use Doctors Note Upscaler</h2>
        
        <h3>📋 For best results:</h3>
        <ul>
        <li>Ensure good lighting on the prescription</li>
        <li>Keep the prescription flat and straight</li>
        <li>Make sure text is not blurry or cut off</li>
        <li>Use high contrast (dark text on light background)</li>
        </ul>
        
        <h3>🔧 Common issues:</h3>
        <ul>
        <li>If no text is detected, try better lighting</li>
        <li>If text is unclear, position camera closer</li>
        <li>If camera won't open, close other apps using camera</li>
        </ul>
        
        <h3>💊 Medical abbreviations handled:</h3>
        <ul>
        <li>mg → milligrams</li>
        <li>qd → once daily</li>
        <li>bid → twice daily</li>
        <li>tid → three times daily</li>
        <li>po → by mouth</li>
        <li>And many more...</li>
        </ul>
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("Help - How to Use")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.exec()
    
    def show_about(self):
        """Show about dialog."""
        about_text = f"""
        <h2>{Config.APP_NAME}</h2>
        <p><b>Version:</b> {Config.APP_VERSION}</p>
        <p><b>Description:</b> Extract and clean text from medical prescriptions using OCR technology.</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Image file upload processing</li>
        <li>Webcam capture functionality</li>
        <li>Medical abbreviation expansion</li>
        <li>Text cleaning and formatting</li>
        </ul>
        """
        
        msg = QMessageBox()
        msg.setWindowTitle(f"About {Config.APP_NAME}")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_text)
        msg.exec()

def main():
    """Main function to run the GUI application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName(Config.APP_NAME)
    app.setApplicationVersion(Config.APP_VERSION)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()