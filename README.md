# AI Agent for Summarizing Research Papers

An elegant web application that extracts and summarizes text, images, and tables from PDF research papers using Google's Gemini 1.5 Flash AI.

## Features

- Beautiful, modern UI with a purple gradient theme
- Extract text from PDF files
- Extract text from images in PDFs (OCR)
- Extract data from tables in PDFs
- Generate concise summaries using Google's Gemini 1.5 Flash AI

## Requirements

- Python 3.8+
- Tesseract OCR (for image text extraction)
- Poppler (for pdf2image)
- Ghostscript (for table extraction)

## Installation

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Install system dependencies:

   ### Tesseract OCR (for image text extraction):

   **Windows:**
   1. Download and install from https://github.com/UB-Mannheim/tesseract/wiki
   2. Add the Tesseract installation directory to your PATH
      - Right-click on "This PC" or "My Computer" and select "Properties"
      - Click on "Advanced system settings"
      - Click on "Environment Variables"
      - Under "System variables", find the "Path" variable, select it and click "Edit"
      - Click "New" and add the path to Tesseract (e.g., `C:\Program Files\Tesseract-OCR`)
      - Click "OK" on all dialogs

   **macOS:**
   ```
   brew install tesseract
   ```

   **Linux:**
   ```
   sudo apt-get install tesseract-ocr
   ```

   ### Poppler (for PDF to image conversion):

   **Windows:**
   1. Download from https://github.com/oschwartz10612/poppler-windows/releases/
   2. Extract the downloaded file to a location on your computer (e.g., `C:\Program Files\poppler`)
   3. Add the `bin` directory to your system PATH:
      - Right-click on "This PC" or "My Computer" and select "Properties"
      - Click on "Advanced system settings"
      - Click on "Environment Variables"
      - Under "System variables", find the "Path" variable, select it and click "Edit"
      - Click "New" and add the path to the Poppler bin directory (e.g., `C:\Program Files\poppler\bin`)
      - Click "OK" on all dialogs
   4. Restart your command prompt or terminal

   **macOS:**
   ```
   brew install poppler
   ```

   **Linux:**
   ```
   sudo apt-get install poppler-utils
   ```

   ### Ghostscript (for table extraction):

   **Windows:**
   1. Download from https://www.ghostscript.com/download/gsdnld.html
   2. Run the installer
   3. The installer should automatically add Ghostscript to your PATH
   4. If table extraction still fails, add the Ghostscript bin directory to your PATH manually

   **macOS:**
   ```
   brew install ghostscript
   ```

   **Linux:**
   ```
   sudo apt-get install ghostscript
   ```

## Usage

1. Run the application:
   ```
   python beautiful_pdf_app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:8086
   ```

3. Upload a PDF research paper and click "Generate Summary"

4. View the AI-generated summary of the paper

## How It Works

1. Upload a PDF research paper
2. The application extracts text, images, and tables from the PDF
3. The extracted content is processed by Google's Gemini 1.5 Flash AI
4. A comprehensive summary is generated that captures the key points of the research paper

## API Key

The application uses Google's Gemini 1.5 Flash API. The current API key in the code is for demonstration purposes only. Replace it with your own API key for production use.

## Troubleshooting

### FontBBox Warnings
If you see warnings like "Could get FontBBox from font descriptor because None cannot be parsed as 4 floats", these are harmless warnings from the PDF parsing libraries and can be safely ignored. The application has been configured to suppress these warnings.

### Image Extraction Errors
If you see the error "Unable to get page count. Is poppler installed and in PATH?", you need to install Poppler and make sure it's in your system PATH. See the installation instructions above.

### Table Extraction Errors
If table extraction fails, make sure Ghostscript is properly installed and in your system PATH. See the installation instructions above.

### General Tips
1. After installing system dependencies, restart your terminal/command prompt before running the application
2. On Windows, make sure all required directories are added to your system PATH
3. If you're still having issues, try running the application with basic text extraction only:
   ```
   python main.py --basic-only
   ```
   This will skip image and table extraction and only use basic text extraction.
