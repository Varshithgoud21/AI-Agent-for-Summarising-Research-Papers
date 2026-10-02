# Import necessary libraries
from flask import Flask, request, render_template_string  # Web framework
import os                                                # File operations
import PyPDF2                                           # PDF text extraction
import requests                                         # API requests
import uuid                                             # Generate unique IDs
import time                                             # Timestamps
import warnings                                         # Warning management
import argparse                                         # Command line arguments
import sys                                               # System functions

# Suppress common PDF parsing warnings
warnings.filterwarnings("ignore", message="Could get FontBBox from font descriptor")

# Parse command line arguments
parser = argparse.ArgumentParser(description='AI Agent for Summarizing Research Papers')
parser.add_argument('--basic-only', action='store_true',
                    help='Use only basic text extraction (skip images and tables)')
args = parser.parse_args()

# ===== OPTIONAL DEPENDENCIES =====
# Try to import image processing libraries (for OCR)
try:
    import cv2                                          # OpenCV for image processing
    import numpy as np                                  # Numerical operations
    import pytesseract                                  # OCR engine
    from pdf2image import convert_from_path             # Convert PDF to images
    IMAGES_SUPPORT = True                               # Flag for image support
except ImportError:
    IMAGES_SUPPORT = False                              # Disable if libraries missing

# Try to import table extraction libraries
try:
    import camelot                                      # Table extraction
    TABLES_SUPPORT = True                               # Flag for table support
except ImportError:
    TABLES_SUPPORT = False                              # Disable if library missing

# ===== FLASK APP SETUP =====
app = Flask(__name__)                                   # Initialize Flask app

# Set maximum file size (16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create directories for storing files if they don't exist
os.makedirs('pdfs', exist_ok=True)                      # Store uploaded PDFs
os.makedirs('summaries', exist_ok=True)                 # Store generated summaries

# ===== IMAGE TEXT EXTRACTION =====
def extract_text_from_images(images):
    """Extract text from images using OCR (Optical Character Recognition)"""
    if not IMAGES_SUPPORT:
        return "Image extraction not supported. Install required dependencies."

    try:
        extracted_text = ""
        for img in images:
            # Convert to grayscale for better OCR results
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply threshold to get a binary image (improves OCR accuracy)
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

            # Perform OCR using Tesseract
            text = pytesseract.image_to_string(binary)
            extracted_text += text + "\n\n"

        return extracted_text
    except Exception as e:
        print(f"Error extracting text from images: {str(e)}")
        return f"Error extracting text from images: {str(e)}"

# ===== TABLE EXTRACTION =====
def extract_tables_from_pdf(pdf_path):
    """Extract tables from PDF file using Camelot"""
    if not TABLES_SUPPORT:
        return "Table extraction not supported. Install required dependencies."

    try:
        # Use camelot to extract tables from all pages
        tables = camelot.read_pdf(pdf_path, pages='all')

        extracted_text = ""
        for i, table in enumerate(tables):
            extracted_text += f"Table {i+1}:\n"
            extracted_text += table.df.to_string() + "\n\n"  # Convert table to string

        return extracted_text
    except Exception as e:
        print(f"Error extracting tables: {str(e)}")
        return f"Error extracting tables: {str(e)}"

# ===== MAIN PDF TEXT EXTRACTION =====
def extract_text_from_pdf(pdf_path):
    """Extract all content from a PDF file: text, images, and tables"""
    try:
        # === 1. Extract regular text ===
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n\n"
            print(f"Successfully extracted regular text: {len(text)} characters")
        except Exception as e:
            print(f"Error extracting regular text: {str(e)}")
            text = f"Error extracting regular text: {str(e)}"

        # === 2. Extract text from images (if supported) ===
        image_text = ""
        if IMAGES_SUPPORT and not args.basic_only:
            try:
                # Convert PDF to images
                print("Converting PDF to images for OCR...")

                try:
                    # Try to convert PDF to images
                    images = convert_from_path(pdf_path)

                    # Convert PIL images to OpenCV format
                    cv_images = []
                    for img in images:
                        # Convert PIL image to numpy array
                        open_cv_image = np.array(img)
                        # Convert RGB to BGR (OpenCV format)
                        open_cv_image = open_cv_image[:, :, ::-1].copy()
                        cv_images.append(open_cv_image)

                    # Extract text from images
                    print("Extracting text from images using OCR...")
                    image_text = extract_text_from_images(cv_images)
                    print(f"Successfully extracted text from images: {len(image_text)} characters")

                except Exception as e:
                    error_msg = str(e)
                    if "Unable to get page count" in error_msg or "poppler" in error_msg.lower():
                        print("\n" + "="*80)
                        print("ERROR: Poppler is not properly installed or not in your PATH")
                        print("\nTo fix this issue:")
                        print("1. Install Poppler:")
                        print("   - Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/")
                        print("   - macOS: brew install poppler")
                        print("   - Linux: sudo apt-get install poppler-utils")
                        print("\n2. Add Poppler to your PATH:")
                        print("   - Windows: Add the bin directory to your system PATH")
                        print("   - Restart your terminal/command prompt after installation")
                        print("="*80 + "\n")

                        image_text = "Image text extraction failed: Poppler is not installed or not in PATH. " + \
                                    "See console for installation instructions."
                    else:
                        print(f"Error converting PDF to images: {error_msg}")
                        image_text = f"Error converting PDF to images: {error_msg}"

            except Exception as e:
                print(f"Error in image extraction process: {str(e)}")
                image_text = f"Error in image extraction process: {str(e)}"
        elif args.basic_only:
            image_text = "Image extraction skipped (--basic-only mode enabled)."
            print("Image extraction skipped - basic-only mode enabled")
        else:
            image_text = "Image extraction not supported. Install required dependencies."
            print("Image extraction skipped - dependencies not available")

        # === 3. Extract tables (if supported) ===
        table_text = ""
        if TABLES_SUPPORT and not args.basic_only:
            try:
                print("Extracting tables from PDF...")
                try:
                    table_text = extract_tables_from_pdf(pdf_path)
                    print(f"Successfully extracted text from tables: {len(table_text)} characters")
                except Exception as e:
                    error_msg = str(e)
                    if "ghostscript" in error_msg.lower():
                        print("\n" + "="*80)
                        print("ERROR: Ghostscript is not properly installed or not in your PATH")
                        print("\nTo fix this issue:")
                        print("1. Install Ghostscript:")
                        print("   - Windows: Download from https://www.ghostscript.com/download/gsdnld.html")
                        print("   - macOS: brew install ghostscript")
                        print("   - Linux: sudo apt-get install ghostscript")
                        print("\n2. Add Ghostscript to your PATH (Windows)")
                        print("   - Restart your terminal/command prompt after installation")
                        print("="*80 + "\n")

                        table_text = "Table extraction failed: Ghostscript is not installed or not in PATH. " + \
                                    "See console for installation instructions."
                    else:
                        print(f"Error extracting tables: {error_msg}")
                        table_text = f"Error extracting tables: {error_msg}"
            except Exception as e:
                print(f"Error in table extraction process: {str(e)}")
                table_text = f"Error in table extraction process: {str(e)}"
        elif args.basic_only:
            table_text = "Table extraction skipped (--basic-only mode enabled)."
            print("Table extraction skipped - basic-only mode enabled")
        else:
            table_text = "Table extraction not supported. Install required dependencies."
            print("Table extraction skipped - dependencies not available")

        # === 4. Combine all extracted text ===
        combined_text = "=== EXTRACTED TEXT FROM DOCUMENT ===\n\n" + text

        if IMAGES_SUPPORT:
            combined_text += "\n\n=== EXTRACTED TEXT FROM IMAGES ===\n\n" + image_text

        if TABLES_SUPPORT:
            combined_text += "\n\n=== EXTRACTED TEXT FROM TABLES ===\n\n" + table_text

        return combined_text
    except Exception as e:
        print(f"Error in main extraction process: {str(e)}")
        # Return at least the text if we have it, otherwise raise the exception
        if 'text' in locals() and text:
            return text
        raise

# ===== AI SUMMARIZATION =====
def summarize_with_gemini(text):
    """Summarize text using Google's Gemini 1.5 Flash AI model"""
    try:
        # API key for Google Gemini (replace with your own for production)
        api_key = "AIzaSyA3HTh5b8YdptHQPcQa7E2bLToX2jpAInI"

        # Using Gemini 1.5 Flash model for faster response times
        model = "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

        # Set up headers and parameters for the API request
        headers = {
            "Content-Type": "application/json",
        }
        params = {
            "key": api_key
        }

        # Create a detailed prompt for summarizing research papers
        prompt = f"""You are a research assistant that creates concise summaries of academic papers.

Please analyze the following content from a research paper and create a comprehensive summary in 3-5 paragraphs.
"""

        # Add information about available extraction methods
        if IMAGES_SUPPORT:
            prompt += "The content includes text extracted from the document and images (using OCR)."

        if TABLES_SUPPORT:
            prompt += " It also includes tables extracted from the document."

        # Add specific focus areas for the summary
        prompt += """
Focus on:
- The main research question or objective
- The methodology used
- Key findings and results
- Main conclusions and implications
"""

        # Add focus on tables and figures if available
        if IMAGES_SUPPORT or TABLES_SUPPORT:
            prompt += "- Any important data from tables or figures\n"

        # Add the extracted text to the prompt
        prompt += f"""
Here is the extracted content:

{text}"""

        # Configure the API request payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,           # Controls randomness (0.0-1.0)
                "maxOutputTokens": 1500       # Limits response length
            }
        }

        # Send the request to the Gemini API
        print(f"Sending request to Gemini API...")
        response = requests.post(url, json=payload, headers=headers, params=params)
        print(f"API Response status code: {response.status_code}")
        response_json = response.json()

        # Extract and return the summary from the response
        if "candidates" in response_json and len(response_json["candidates"]) > 0:
            print("Successfully received summary from API")
            return response_json["candidates"][0]["content"]["parts"][0]["text"]
        else:
            print(f"API Error: {response_json}")
            return "Failed to generate summary. Please try again."
    except Exception as e:
        print(f"Error in summarization: {str(e)}")
        return f"Error in summarization: {str(e)}"

# ===== HTML TEMPLATES =====
# Base template with CSS styling and page structure
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AN AI Agent For Summarizing Research Paper</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* CSS Variables for consistent theming */
        :root {
            --primary: #5e60ce;          /* Main purple color */
            --primary-light: #f0f0ff;    /* Light purple for backgrounds */
            --secondary: #6930c3;        /* Secondary purple */
            --accent: #7400b8;           /* Accent purple for gradients */
            --success: #2dce89;          /* Green for success messages */
            --warning: #ffd43b;          /* Yellow for warnings */
            --danger: #f5365c;           /* Red for errors */
            --dark: #32325d;             /* Dark blue for text */
            --medium: #8898aa;           /* Medium gray for secondary text */
            --light: #f6f9fc;            /* Light gray for backgrounds */
            --white: #ffffff;            /* White */
            --shadow: 0 4px 6px rgba(0, 0, 0, 0.07);  /* Subtle shadow */
            --radius: 8px;               /* Border radius */
        }

        /* Reset and base styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--light);
            color: var(--dark);
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Header styles */
        .header {
            background: linear-gradient(120deg, #5e60ce, #7400b8);
            color: var(--white);
            padding: 3rem 0;
            text-align: center;
            box-shadow: var(--shadow);
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .tagline {
            font-size: 1.2rem;
            font-weight: 300;
            opacity: 0.9;
            margin-top: 1rem;
            letter-spacing: 0.2px;
        }

        .powered-by {
            display: inline-block;
            background-color: rgba(255, 255, 255, 0.2);
            color: var(--white);
            padding: 0.5rem 1.5rem;
            border-radius: 30px;
            margin-top: 1.5rem;
            font-size: 0.9rem;
        }

        /* Main content container */
        .container {
            width: 90%;
            max-width: 1200px;
            margin: 2rem auto;
            flex: 1;
        }

        /* Card component */
        .card {
            background-color: var(--white);
            border-radius: var(--radius);
            box-shadow: 0 7px 14px rgba(50, 50, 93, 0.1), 0 3px 6px rgba(0, 0, 0, 0.08);
            padding: 3rem;
            margin-bottom: 2.5rem;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid rgba(0, 0, 0, 0.05);
            text-align: center;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(50, 50, 93, 0.1), 0 5px 15px rgba(0, 0, 0, 0.07);
        }

        .card-title {
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--dark);
            letter-spacing: -0.3px;
        }

        .card-subtitle {
            font-size: 1.1rem;
            color: var(--medium);
            margin-bottom: 2rem;
        }

        /* File upload form */
        .upload-form {
            margin-top: 2rem;
        }

        .file-input-wrapper {
            position: relative;
            margin: 2rem 0;
            border: 2px dashed var(--primary);
            border-radius: var(--radius);
            padding: 3rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .file-input-wrapper:hover {
            background-color: var(--primary-light);
        }

        .file-input {
            position: absolute;
            width: 0.1px;
            height: 0.1px;
            opacity: 0;
            overflow: hidden;
            z-index: -1;
        }

        .file-input-label {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1.5rem;
            cursor: pointer;
        }

        .file-icon {
            font-size: 2.5rem;
            color: var(--primary);
        }

        .file-text {
            font-size: 1.1rem;
            color: var(--medium);
        }

        .file-name {
            margin-top: 1rem;
            font-size: 0.9rem;
            color: var(--primary);
            font-weight: 500;
            display: none;
        }

        /* Button styles */
        .btn {
            background: linear-gradient(to right, var(--primary), var(--accent));
            color: var(--white);
            border: none;
            border-radius: 30px;
            padding: 0.9rem 1.8rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-block;
            text-align: center;
            text-decoration: none;
            box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
            letter-spacing: 0.5px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 7px 14px rgba(50, 50, 93, 0.1), 0 3px 6px rgba(0, 0, 0, 0.08);
            filter: brightness(105%);
        }

        .btn:active {
            transform: translateY(0);
            box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
            filter: brightness(100%);
        }

        .btn-block {
            display: block;
            width: 100%;
        }

        /* Summary box */
        .summary-box {
            background-color: var(--primary-light);
            border-radius: var(--radius);
            padding: 2rem;
            margin: 1.8rem 0;
            line-height: 1.8;
            border-left: 4px solid var(--primary);
            font-size: 1.05rem;
            color: var(--dark);
        }

        /* File info display */
        .file-info {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            color: var(--medium);
        }

        .file-info-icon {
            color: var(--primary);
        }

        /* Loading spinner */
        .loading {
            display: none;
            text-align: center;
            padding: 2rem;
        }

        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-left-color: var(--primary);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Footer styles */
        .footer {
            background-color: var(--dark);
            color: var(--light);
            text-align: center;
            padding: 1.5rem 0;
            margin-top: auto;
        }

        .footer p {
            font-size: 0.9rem;
        }

        /* Responsive styles */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.5rem;
            }

            .card {
                padding: 1.5rem;
            }

            .file-input-wrapper {
                padding: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Agent: Summarizing Research Papers</h1>
        <p class="tagline">Transform complex research papers into concise, easy-to-understand summaries</p>
        <div class="powered-by">Powered by Google Gemini 1.5 Flash</div>
    </div>

    <div class="container">
        <!-- Content will be inserted here -->
    </div>

    <div class="footer">
        <p>&copy; 2023 PDF Summarizer. All rights reserved.</p>
    </div>
</body>
</html>
"""

# Template for the home page with file upload
INDEX_TEMPLATE = """
<div class="card">
    <h2 class="card-title">Upload Your Research Paper</h2>
    <p class="card-subtitle">Select a PDF file to generate an AI-powered summary</p>

    <form action="/upload" method="POST" enctype="multipart/form-data" class="upload-form" id="upload-form">
        <div class="file-input-wrapper" id="file-drop-area">
            <label for="pdf-upload" class="file-input-label">
                <span class="file-icon">⬆️</span>
                <span class="file-text">Drag & drop your PDF here or click to browse</span>
            </label>
            <input type="file" id="pdf-upload" name="pdf" accept="application/pdf" class="file-input" required>
            <div class="file-name" id="file-name">No file selected</div>
        </div>

        <button type="submit" class="btn btn-block">Generate Summary</button>
    </form>

    <div class="loading" id="loading">
        <div class="spinner"></div>
        <p>Processing your PDF... This may take a minute.</p>
    </div>
</div>

<script>
    // Display file name when selected
    document.getElementById('pdf-upload').addEventListener('change', function(e) {
        const fileName = e.target.files[0] ? e.target.files[0].name : 'No file selected';
        const fileNameElement = document.getElementById('file-name');
        fileNameElement.textContent = fileName;
        fileNameElement.style.display = 'block';
    });

    // Show loading spinner when form is submitted
    document.getElementById('upload-form').addEventListener('submit', function() {
        document.getElementById('loading').style.display = 'block';
    });

    // Drag and drop functionality
    const dropArea = document.getElementById('file-drop-area');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.style.backgroundColor = 'var(--primary-light)';
    }

    function unhighlight() {
        dropArea.style.backgroundColor = '';
    }

    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length) {
            document.getElementById('pdf-upload').files = files;
            const fileName = files[0].name;
            const fileNameElement = document.getElementById('file-name');
            fileNameElement.textContent = fileName;
            fileNameElement.style.display = 'block';
        }
    }
</script>
"""

# Template for displaying the summary results
RESULT_TEMPLATE = """
<div class="card">
    <h2 class="card-title">Summary Results</h2>

    <div class="file-info">
        <span class="file-info-icon">📄</span>
        <span>{{ filename }}</span>
    </div>

    <div class="summary-box">
        {{ summary|safe }}
    </div>

    <a href="/" class="btn">Process Another PDF</a>
</div>
"""

# Template for displaying errors
ERROR_TEMPLATE = """
<div class="card">
    <h2 class="card-title" style="color: var(--danger);">Error</h2>

    <div style="background-color: rgba(239, 71, 111, 0.1); border-radius: var(--radius); padding: 1.5rem; margin: 1.5rem 0; border-left: 4px solid var(--danger);">
        <p>{{ error }}</p>
    </div>

    <a href="/" class="btn">Try Again</a>
</div>
"""

# ===== FLASK ROUTES =====
@app.route('/')
def index():
    """Home page route - displays the file upload form"""
    # Insert the index template into the base template
    complete_template = BASE_TEMPLATE.replace('<!-- Content will be inserted here -->', INDEX_TEMPLATE)

    return render_template_string(
        complete_template,
        images_support=IMAGES_SUPPORT,
        tables_support=TABLES_SUPPORT
    )

@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload, process PDF, and display summary"""
    try:
        # Check if a file was included in the request
        if 'pdf' not in request.files:
            # Insert the error template into the base template
            complete_template = BASE_TEMPLATE.replace('<!-- Content will be inserted here -->', ERROR_TEMPLATE)

            return render_template_string(
                complete_template,
                error="No file part in the request"
            )

        # Get the uploaded file
        pdf = request.files['pdf']

        # Check if a file was selected
        if pdf.filename == '':
            # Insert the error template into the base template
            complete_template = BASE_TEMPLATE.replace('<!-- Content will be inserted here -->', ERROR_TEMPLATE)

            return render_template_string(
                complete_template,
                error="No file selected"
            )

        # Generate a unique filename to avoid collisions
        unique_id = str(uuid.uuid4())
        timestamp = int(time.time())
        filename = f"{timestamp}_{unique_id}_{pdf.filename}"
        file_path = os.path.join('pdfs', filename)

        # Save the uploaded file
        pdf.save(file_path)

        # Extract text from PDF (including images and tables if supported)
        extracted_text = extract_text_from_pdf(file_path)

        # Summarize the text using Gemini AI
        summary = summarize_with_gemini(extracted_text)

        # Save the summary to a file
        summary_filename = f"{timestamp}_{unique_id}_summary.txt"
        summary_path = os.path.join('summaries', summary_filename)
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        # Format the summary with line breaks for HTML display
        formatted_summary = summary.replace('\n', '<br>')

        # Insert the result template into the base template
        complete_template = BASE_TEMPLATE.replace('<!-- Content will be inserted here -->', RESULT_TEMPLATE)

        # Return the results page
        return render_template_string(
            complete_template,
            filename=pdf.filename,
            summary=formatted_summary,
            images_support=IMAGES_SUPPORT,
            tables_support=TABLES_SUPPORT
        )
    except Exception as e:
        # Handle any errors that occur during processing
        # Insert the error template into the base template
        complete_template = BASE_TEMPLATE.replace('<!-- Content will be inserted here -->', ERROR_TEMPLATE)

        return render_template_string(
            complete_template,
            error=f"An error occurred: {str(e)}"
        )

# ===== APPLICATION ENTRY POINT =====
if __name__ == '__main__':
    # Print startup information
    print("Starting Flask server on port 8086...")

    if args.basic_only:
        print("\n" + "="*50)
        print("RUNNING IN BASIC-ONLY MODE")
        print("Only basic text extraction will be used")
        print("Image and table extraction are disabled")
        print("="*50)

    print("\nAvailable features:")
    print("✓ Text Extraction")

    if args.basic_only:
        print("✗ Image Text Extraction (disabled in basic-only mode)")
        print("✗ Table Extraction (disabled in basic-only mode)")
    else:
        print(f"{'✓' if IMAGES_SUPPORT else '✗'} Image Text Extraction")
        print(f"{'✓' if TABLES_SUPPORT else '✗'} Table Extraction")

    print("\nServer will be available at http://127.0.0.1:8086")

    # Start the Flask server
    app.run(debug=True, host='127.0.0.1', port=8086)
