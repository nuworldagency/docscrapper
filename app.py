import streamlit as st
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
from datetime import datetime
import time

# Set up page config
st.set_page_config(
    page_title="Document Scraper",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
    }
    .stTextInput>div>div>input {
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_content(url):
    try:
        driver = setup_selenium()
        driver.get(url)
        time.sleep(2)  # Allow JavaScript to load
        page_source = driver.page_source
        driver.quit()
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Remove unwanted elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Extract text content
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        st.error(f"Error scraping content: {str(e)}")
        return None

def create_pdf(content, filename):
    try:
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        y = height - 50
        
        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Scraped Document Content")
        y -= 30
        
        # Add timestamp
        c.setFont("Helvetica", 10)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.drawString(50, y, f"Generated on: {timestamp}")
        y -= 30
        
        # Add content
        c.setFont("Helvetica", 12)
        words = content.split()
        line = ""
        for word in words:
            if len(line + " " + word) * 6 < width - 100:  # Approximate character width
                line = line + " " + word if line else word
            else:
                c.drawString(50, y, line)
                y -= 20
                if y < 50:  # New page if near bottom
                    c.showPage()
                    y = height - 50
                line = word
        
        if line:  # Draw any remaining text
            c.drawString(50, y, line)
            
        c.save()
        return True
    except Exception as e:
        st.error(f"Error creating PDF: {str(e)}")
        return False

def main():
    st.title("📄 Document Repository Scraper")
    st.markdown("### Extract and format document content from any website")
    
    url = st.text_input("Enter the URL to scrape:", placeholder="https://example.com/docs")
    
    col1, col2 = st.columns(2)
    with col1:
        wait_time = st.slider("Page Load Wait Time (seconds)", 1, 10, 2)
    with col2:
        max_pages = st.number_input("Maximum Pages to Scrape", 1, 100, 1)
    
    if st.button("Start Scraping"):
        if url:
            with st.spinner("Scraping content..."):
                content = scrape_content(url)
                
                if content:
                    st.success("Content scraped successfully!")
                    
                    # Create PDF
                    output_dir = "output"
                    os.makedirs(output_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_filename = os.path.join(output_dir, f"scraped_content_{timestamp}.pdf")
                    
                    if create_pdf(content, pdf_filename):
                        with open(pdf_filename, "rb") as pdf_file:
                            st.download_button(
                                label="Download PDF",
                                data=pdf_file,
                                file_name=f"scraped_content_{timestamp}.pdf",
                                mime="application/pdf"
                            )
                    else:
                        st.error("Failed to create PDF")
                else:
                    st.error("Failed to scrape content")
        else:
            st.warning("Please enter a URL")

if __name__ == "__main__":
    main()
