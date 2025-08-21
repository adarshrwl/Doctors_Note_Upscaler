"""
Enhanced Utility functions for Doctors Note Upscaler
This file contains improved helper functions with robust OCR processing,
better error handling, and enhanced text cleaning capabilities.
"""

import re  # Regular expressions for pattern matching and text replacement
import os  # For file system operations
import pytesseract  # For setting up Tesseract path
from config import Config  # Import our configuration settings
import cv2  # For image preprocessing
import numpy as np  # For image array operations
from PIL import Image, ImageEnhance, ImageFilter  # Enhanced image processing

# ===== ENHANCED MEDICAL ABBREVIATIONS DICTIONARY =====
MEDICAL_ABBREVIATIONS = {
    # Dosage abbreviations
    'mg': 'milligrams',
    'g': 'grams', 
    'kg': 'kilograms',
    'ml': 'milliliters',
    'l': 'liters',
    'mcg': 'micrograms',
    'iu': 'international units',
    'u': 'units',
    
    # Frequency abbreviations (how often to take medicine)
    'qd': 'once daily',
    'q.d.': 'once daily',
    'od': 'once daily',
    'bid': 'twice daily',
    'b.i.d.': 'twice daily', 
    'bd': 'twice daily',
    'tid': 'three times daily',
    't.i.d.': 'three times daily',
    'tds': 'three times daily',
    'qid': 'four times daily',
    'q.i.d.': 'four times daily',
    'qds': 'four times daily',
    'q4h': 'every 4 hours',
    'q6h': 'every 6 hours',
    'q8h': 'every 8 hours',
    'q12h': 'every 12 hours',
    'qhs': 'at bedtime',
    'prn': 'as needed',
    'p.r.n.': 'as needed',
    'sos': 'as needed',
    
    # Route abbreviations (how to take medicine)
    'po': 'by mouth',
    'p.o.': 'by mouth',
    'oral': 'by mouth',
    'im': 'intramuscular injection',
    'iv': 'intravenous',
    'sl': 'under the tongue',
    'top': 'apply topically',
    'inh': 'inhaled',
    'pr': 'per rectum',
    'pv': 'per vagina',
    
    # Time abbreviations
    'am': 'morning',
    'pm': 'evening',
    'ac': 'before meals',
    'pc': 'after meals',
    'hs': 'at bedtime',
    'mane': 'in the morning',
    'nocte': 'at night',
    
    # General medical terms
    'dx': 'diagnosis',
    'rx': 'prescription',
    'tx': 'treatment',
    'hx': 'history',
    'pt': 'patient',
    'dr': 'doctor',
    'md': 'doctor',
    'rph': 'pharmacist',
    
    # Common prescription instructions
    'tab': 'tablet',
    'tabs': 'tablets',
    'cap': 'capsule',
    'caps': 'capsules',
    'susp': 'suspension',
    'sol': 'solution',
    'oint': 'ointment',
    'cr': 'cream',
    'lot': 'lotion',
    'gtt': 'drops',
    'inj': 'injection',
    'syr': 'syrup',
    'elix': 'elixir',
}

# ===== ENHANCED OCR ERROR PATTERNS =====
OCR_ERROR_PATTERNS = {
    # Common character misreadings
    r'\b([0-9]+)O([0-9]+)\b': r'\1\2',  # "1O5" -> "105"
    r'\b([0-9]+)o([0-9]+)\b': r'\1\2',  # "1o5" -> "15"
    r'\bl([0-9]+)\b': r'1\2',           # "l5" -> "15"
    r'\bI([0-9]+)\b': r'1\2',           # "I5" -> "15"
    r'\b([0-9]+)l\b': r'\g<1>1',        # "5l" -> "51"
    r'\b([0-9]+)I\b': r'\g<1>1',        # "5I" -> "51"
    
    # Fix common medication name OCR errors
    r'\bAsplrln\b': 'Aspirin',
    r'\bMetforrnln\b': 'Metformin',
    r'\bLlslnopril\b': 'Lisinopril',
    r'\bAmoxlcillln\b': 'Amoxicillin',
    r'\bPrednlsone\b': 'Prednisone',
    
    # Fix dosage unit errors
    r'\bmg\b(?=[0-9])': 'mg ',          # Add space after mg
    r'\b([0-9]+)mg(?![a-z])\b': r'\1 mg',  # "5mg" -> "5 mg"
    r'\b([0-9]+)ml(?![a-z])\b': r'\1 ml',  # "5ml" -> "5 ml"
    
    # Fix spacing issues
    r'\s+': ' ',                        # Multiple spaces to single
    r'\n+': '\n',                       # Multiple newlines to single
}

def setup_tesseract():
    """
    Set up Tesseract OCR by finding its installation path.
    Enhanced version with better error handling.
    """
    print("🔧 Setting up Tesseract OCR...")
    
    # Try each potential Tesseract path
    for path in Config.TESSERACT_PATHS:
        # Expand environment variables like %USERNAME%
        expanded_path = os.path.expandvars(path)
        
        # Check if this path exists and is executable
        if path == "tesseract":
            # This means Tesseract is in the system PATH
            try:
                # Test if tesseract command works
                pytesseract.get_tesseract_version()
                print("✅ Tesseract found in system PATH")
                return
            except:
                continue
        elif os.path.isfile(expanded_path):
            # Found Tesseract executable, set the path
            pytesseract.pytesseract.tesseract_cmd = expanded_path
            print(f"✅ Tesseract found at: {expanded_path}")
            
            # Test if it works
            try:
                pytesseract.get_tesseract_version()
                return
            except Exception as e:
                print(f"⚠️ Tesseract found but not working: {e}")
                continue
    
    # If we get here, Tesseract wasn't found or working
    print("❌ Tesseract OCR not found or not working!")
    print("💡 Please install Tesseract OCR:")
    print("   1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("   2. Install to default location")
    print("   3. Or add Tesseract to your system PATH")
    raise FileNotFoundError("Tesseract OCR not found. Please install it to continue.")

def preprocess_image_for_ocr(image_path):
    """
    Preprocess image to improve OCR accuracy.
    This function applies various image enhancement techniques.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        PIL.Image: Preprocessed image ready for OCR
    """
    try:
        # Load image with OpenCV for advanced preprocessing
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply noise reduction
        denoised = cv2.medianBlur(gray, 3)
        
        # Apply adaptive thresholding to handle varying lighting
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
        
        # Convert back to PIL Image
        pil_image = Image.fromarray(processed)
        
        # Apply additional PIL enhancements
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(2.0)
        
        print("✅ Image preprocessing completed")
        return pil_image
        
    except Exception as e:
        print(f"⚠️ Image preprocessing failed: {e}")
        print("📝 Falling back to original image...")
        # Return original image if preprocessing fails
        return Image.open(image_path)

def enhanced_ocr_extraction(image_path):
    """
    Enhanced OCR extraction with multiple attempts and configurations.
    This function tries different OCR settings to get the best results.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        tuple: (success: bool, raw_text: str, confidence_score: float)
    """
    print("🔍 Starting enhanced OCR extraction...")
    
    try:
        # Preprocess the image
        processed_image = preprocess_image_for_ocr(image_path)
        
        # Try multiple OCR configurations
        ocr_configs = [
            '--oem 3 --psm 6',  # Default: single uniform block
            '--oem 3 --psm 4',  # Single column of text
            '--oem 3 --psm 8',  # Single word
            '--oem 3 --psm 7',  # Single text line
            '--oem 3 --psm 13', # Raw line, no heuristics
        ]
        
        best_text = ""
        best_confidence = 0
        all_attempts = []
        
        for i, config in enumerate(ocr_configs):
            try:
                print(f"   Trying OCR configuration {i+1}/{len(ocr_configs)}")
                
                # Extract text with current configuration
                text = pytesseract.image_to_string(processed_image, config=config)
                
                # Get confidence data
                try:
                    data = pytesseract.image_to_data(processed_image, config=config, output_type=pytesseract.Output.DICT)
                    confidences = [int(x) for x in data['conf'] if int(x) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                except:
                    avg_confidence = 50  # Default confidence if calculation fails
                
                all_attempts.append((text.strip(), avg_confidence, config))
                
                # Keep track of best result based on confidence and length
                if text.strip() and (avg_confidence > best_confidence or 
                                   (avg_confidence >= best_confidence * 0.8 and len(text.strip()) > len(best_text))):
                    best_text = text.strip()
                    best_confidence = avg_confidence
                    
            except Exception as e:
                print(f"   ⚠️ Configuration {i+1} failed: {e}")
                continue
        
        # If no good result, try with original image
        if not best_text or best_confidence < 30:
            print("🔄 Trying with original image...")
            try:
                original_image = Image.open(image_path)
                text = pytesseract.image_to_string(original_image, config='--oem 3 --psm 6')
                if text.strip():
                    best_text = text.strip()
                    best_confidence = max(best_confidence, 40)  # Assume reasonable confidence
            except Exception as e:
                print(f"   ⚠️ Original image OCR also failed: {e}")
        
        # Log all attempts for debugging
        if Config.is_debug_enabled():
            print("🐛 DEBUG: All OCR attempts:")
            for i, (text, conf, config) in enumerate(all_attempts):
                print(f"   {i+1}. Confidence: {conf:.1f}%, Config: {config}")
                print(f"      Text preview: '{text[:50]}...'")
        
        success = bool(best_text and len(best_text.strip()) >= Config.MIN_TEXT_LENGTH)
        
        if success:
            print(f"✅ OCR extraction successful (confidence: {best_confidence:.1f}%)")
        else:
            print("❌ OCR extraction failed or returned insufficient text")
            
        return success, best_text, best_confidence
        
    except Exception as e:
        print(f"❌ OCR extraction error: {e}")
        return False, "", 0

def intelligent_text_cleaning(raw_text, confidence_score=50):
    """
    Intelligent text cleaning that adapts based on OCR confidence.
    Lower confidence text gets more aggressive cleaning.
    
    Args:
        raw_text (str): The raw text extracted from OCR
        confidence_score (float): OCR confidence score (0-100)
        
    Returns:
        str: Cleaned and processed text
    """
    if not raw_text or not raw_text.strip():
        return "❌ No text could be extracted from the image"
    
    print(f"🧹 Starting intelligent text cleaning (confidence: {confidence_score:.1f}%)...")
    
    # Step 1: Basic cleanup
    text = raw_text.strip()
    
    # Step 2: Apply OCR error corrections (more aggressive for low confidence)
    text = fix_ocr_errors(text, aggressive=(confidence_score < 60))
    
    # Step 3: Handle fragmented text (common in low-quality OCR)
    text = reconstruct_fragmented_text(text)
    
    # Step 4: Replace medical abbreviations
    text = replace_medical_abbreviations_enhanced(text)
    
    # Step 5: Clean formatting
    text = clean_formatting_enhanced(text)
    
    # Step 6: Add confidence indicators
    text = add_confidence_indicators(text, confidence_score)
    
    print("✅ Text cleaning completed")
    return text

def fix_ocr_errors(text, aggressive=False):
    """
    Fix common OCR recognition errors with optional aggressive mode.
    
    Args:
        text (str): Text with potential OCR errors
        aggressive (bool): Whether to apply aggressive corrections
        
    Returns:
        str: Text with errors fixed
    """
    # Apply standard OCR error patterns
    for pattern, replacement in OCR_ERROR_PATTERNS.items():
        text = re.sub(pattern, replacement, text)
    
    if aggressive:
        # More aggressive corrections for very unclear text
        aggressive_patterns = {
            # Try to fix severely garbled medication names
            r'\b[A-Z]{2,}[a-z]{2,}[A-Z]{2,}\b': lambda m: suggest_medication_name(m.group()),
            
            # Fix obvious number-letter confusions in dosages
            r'\b(\d+)[Oo](\d+)\b': r'\1\2',  # "1O5" or "1o5" -> "15"
            r'\b[Il](\d+)\b': r'1\2',        # "I5" or "l5" -> "15"
            
            # Clean up excessive punctuation
            r'[.]{3,}': '...',
            r'[!]{2,}': '!',
            r'[?]{2,}': '?',
        }
        
        for pattern, replacement in aggressive_patterns.items():
            if callable(replacement):
                text = re.sub(pattern, replacement, text)
            else:
                text = re.sub(pattern, replacement, text)
    
    return text

def suggest_medication_name(garbled_name):
    """
    Suggest possible medication name for garbled text.
    This is a simple implementation - in a real system you'd use a medical dictionary.
    
    Args:
        garbled_name (str): Garbled medication name
        
    Returns:
        str: Suggested name or flagged unclear text
    """
    common_medications = [
        'Aspirin', 'Metformin', 'Lisinopril', 'Amoxicillin', 'Prednisone',
        'Atorvastatin', 'Simvastatin', 'Omeprazole', 'Levothyroxine', 'Warfarin'
    ]
    
    # Simple similarity check (in practice, you'd use fuzzy matching)
    garbled_lower = garbled_name.lower()
    for med in common_medications:
        if len(set(garbled_lower) & set(med.lower())) >= len(med) * 0.6:
            return f"[POSSIBLY: {med}]"
    
    return f"[UNCLEAR MEDICATION: {garbled_name}]"

def reconstruct_fragmented_text(text):
    """
    Try to reconstruct fragmented text that was split incorrectly by OCR.
    
    Args:
        text (str): Fragmented text
        
    Returns:
        str: Reconstructed text
    """
    lines = text.split('\n')
    reconstructed_lines = []
    
    i = 0
    while i < len(lines):
        current_line = lines[i].strip()
        
        # Skip empty lines
        if not current_line:
            i += 1
            continue
        
        # Look for incomplete lines that should be joined
        while (i + 1 < len(lines) and 
               should_join_lines(current_line, lines[i + 1].strip())):
            i += 1
            current_line += " " + lines[i].strip()
        
        reconstructed_lines.append(current_line)
        i += 1
    
    return '\n'.join(reconstructed_lines)

def should_join_lines(line1, line2):
    """
    Determine if two lines should be joined together.
    
    Args:
        line1 (str): First line
        line2 (str): Second line
        
    Returns:
        bool: True if lines should be joined
    """
    if not line1 or not line2:
        return False
    
    # Join if first line ends with a partial word or number
    if (re.search(r'\d+$', line1) and re.search(r'^[a-zA-Z]', line2)) or \
       (re.search(r'[a-z]$', line1) and re.search(r'^[a-z]', line2)):
        return True
    
    # Join if lines are very short (likely fragmented)
    if len(line1) < 10 and len(line2) < 10:
        return True
    
    return False

def replace_medical_abbreviations_enhanced(text):
    """
    Enhanced medical abbreviation replacement with context awareness.
    
    Args:
        text (str): Text containing medical abbreviations
        
    Returns:
        str: Text with abbreviations expanded
    """
    # Split into words while preserving structure
    words = re.findall(r'\b\w+\b|\W+', text)
    processed_words = []
    
    for word in words:
        # Skip non-word tokens (spaces, punctuation)
        if not re.match(r'\b\w+\b', word):
            processed_words.append(word)
            continue
        
        # Clean word for matching
        clean_word = word.lower().strip('.,;:!?')
        
        # Check if this word is a medical abbreviation
        if clean_word in MEDICAL_ABBREVIATIONS:
            # Replace with full meaning
            replacement = MEDICAL_ABBREVIATIONS[clean_word]
            
            # Preserve original capitalization pattern
            if word.isupper():
                replacement = replacement.upper()
            elif word.istitle():
                replacement = replacement.title()
            
            # Add explanation in parentheses for clarity
            processed_words.append(f"{replacement} ({word})")
        else:
            processed_words.append(word)
    
    return ''.join(processed_words)

def clean_formatting_enhanced(text):
    """
    Enhanced formatting cleanup with medical text awareness.
    
    Args:
        text (str): Text with formatting issues
        
    Returns:
        str: Text with improved formatting
    """
    # Fix spacing around punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])(?=[^\s])', r'\1 ', text)
    
    # Fix medical dosage formatting
    text = re.sub(r'(\d+)\s*([a-zA-Z]+)\s+(\d+)', r'\1\2 \3', text)  # "5 mg 2" -> "5mg 2"
    text = re.sub(r'(\d+)\s+(mg|g|ml|mcg|tabs?|caps?)\b', r'\1 \2', text)
    
    # Clean up excessive whitespace
    text = re.sub(r'\s{3,}', '   ', text)  # Max 3 spaces
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
    
    # Fix common medical formatting
    text = re.sub(r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+(\d+\s*mg)', r'\1 \2 \3', text)
    
    return text.strip()

def add_confidence_indicators(text, confidence_score):
    """
    Add confidence indicators to help users understand text reliability.
    
    Args:
        text (str): Processed text
        confidence_score (float): OCR confidence score
        
    Returns:
        str: Text with confidence indicators added
    """
    if confidence_score < 30:
        indicator = "⚠️ LOW CONFIDENCE - Please verify all information carefully"
        color = "RED"
    elif confidence_score < 60:
        indicator = "⚡ MEDIUM CONFIDENCE - Some text may need verification"
        color = "YELLOW"
    elif confidence_score < 80:
        indicator = "✅ GOOD CONFIDENCE - Most text should be accurate"
        color = "GREEN"
    else:
        indicator = "🎯 HIGH CONFIDENCE - Text extraction was very successful"
        color = "GREEN"
    
    # Add colored indicator if terminal supports it
    if Config.COLORS and color in Config.COLORS:
        colored_indicator = f"{Config.COLORS[color]}{indicator}{Config.COLORS['RESET']}"
    else:
        colored_indicator = indicator
    
    return f"{colored_indicator}\n{'-' * 60}\n{text}"

def validate_extracted_text_enhanced(text, confidence_score=50):
    """
    Enhanced validation that considers OCR confidence.
    
    Args:
        text (str): Extracted text to validate
        confidence_score (float): OCR confidence score
        
    Returns:
        tuple: (is_valid: bool, quality_score: str, suggestions: list)
    """
    suggestions = []
    
    if not text or not text.strip():
        return False, "FAILED", ["No text could be extracted from the image"]
    
    clean_text = re.sub(r'\[.*?\]', '', text).strip()  # Remove confidence indicators
    
    if len(clean_text) < Config.MIN_TEXT_LENGTH:
        suggestions.append(f"Text is very short ({len(clean_text)} chars)")
    
    # Check for mostly readable characters
    printable_ratio = sum(1 for c in clean_text if c.isprintable()) / len(clean_text)
    if printable_ratio < 0.7:
        suggestions.append("Text contains many unreadable characters")
    
    # Check for medical content indicators
    medical_indicators = ['mg', 'ml', 'tablet', 'capsule', 'daily', 'times', 'take', 'rx']
    found_indicators = sum(1 for indicator in medical_indicators if indicator.lower() in clean_text.lower())
    
    if found_indicators == 0:
        suggestions.append("Text doesn't appear to contain medical prescription information")
    
    # Determine quality score
    if confidence_score >= 80 and len(clean_text) > 50 and found_indicators >= 2:
        quality_score = "EXCELLENT"
    elif confidence_score >= 60 and len(clean_text) > 30 and found_indicators >= 1:
        quality_score = "GOOD"
    elif confidence_score >= 40 and len(clean_text) > 15:
        quality_score = "ACCEPTABLE"
    elif len(clean_text) > Config.MIN_TEXT_LENGTH:
        quality_score = "POOR"
        suggestions.append("Consider retaking the image with better lighting and focus")
    else:
        quality_score = "FAILED"
        suggestions.append("Image quality too poor for reliable text extraction")
    
    is_valid = quality_score in ["EXCELLENT", "GOOD", "ACCEPTABLE"]
    
    return is_valid, quality_score, suggestions

def clean_messy_text(raw_text):
    """
    Main function for cleaning messy text - enhanced version.
    This is the primary interface used by other modules.
    
    Args:
        raw_text (str): The raw text extracted from OCR
        
    Returns:
        str: Cleaned and processed text
    """
    # Use the enhanced cleaning with default confidence
    return intelligent_text_cleaning(raw_text, confidence_score=50)

# Additional utility functions remain the same as before...
def format_output_text(text, title="PROCESSED TEXT"):
    """Format text for nice console output."""
    border = "=" * Config.SEPARATOR_LENGTH
    title_line = f" {title} "
    title_border = title_line.center(Config.SEPARATOR_LENGTH, "=")
    
    return f"\n{title_border}\n{text}\n{border}"

def ensure_temp_directory():
    """Ensure the temporary directory exists for storing captured images."""
    temp_dir = Config.get_temp_dir()
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)
        print(f"📁 Created temporary directory: {temp_dir}")
    return temp_dir

def cleanup_temp_files():
    """Clean up temporary files created during processing."""
    try:
        if os.path.exists(Config.TEMP_IMAGE_PATH):
            os.remove(Config.TEMP_IMAGE_PATH)
            print("🧹 Cleaned up temporary files")
    except Exception as e:
        print(f"⚠️  Warning: Could not clean up temp files: {e}")

def log_debug_info(message, data=None):
    """Log debug information if debug mode is enabled."""
    if Config.is_debug_enabled():
        print(f"🐛 DEBUG: {message}")
        if data:
            print(f"    Data: {data}")

# Test function for development
def test_enhanced_cleaning():
    """Test the enhanced cleaning functionality."""
    test_cases = [
        ("Take 1O mg bid po", "Basic OCR error test"),
        ("AsplrIn 5Omg qd", "Medication name OCR error"),
        ("rx:\ntab\nqd\nprn", "Fragmented text test"),
        ("???  unclear text  !!!", "Unclear text handling"),
        ("Met for min 85O mg bid", "Complex medication name"),
    ]
    
    print("🧪 Testing enhanced text cleaning...")
    for test_text, description in test_cases:
        print(f"\n📝 {description}")
        print(f"Original: '{test_text}'")
        cleaned = intelligent_text_cleaning(test_text, confidence_score=45)
        print(f"Cleaned:  '{cleaned}'")
        print("-" * 50)

if __name__ == "__main__":
    test_enhanced_cleaning()