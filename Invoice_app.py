import streamlit as st
from pdf2image import convert_from_path
import pytesseract
import pandas as pd
import tempfile
import os
import re
from fpdf import FPDF

# Path to poppler (change for your machine)
poppler_path = r"D:\poppler\poppler-24.02.0\Library\bin"

st.title("AI Invoice Approval Assistant")
st.write("Upload an invoice (PDF)")

# ---- Function to extract structured fields from OCR text ----
def extract_invoice_fields(text):
    fields = {
        "Invoice Number": r"Invoice\s*Number[:\s]*([A-Za-z0-9-]+)",
        "Order Number": r"Order\s*Number[:\s]*([A-Za-z0-9-]+)",
        "Seller Name": r"Seller[:\s]*([A-Za-z\s]+)",
        "City": r"City[:\s]*([A-Za-z\s]+)",
        "PAN": r"PAN[:\s]*([A-Z0-9]+)",
        "Payment Mode": r"Payment\s*Mode[:\s]*([A-Za-z\s]+)",
        "Total Amount": r"Total\s*Amount[:\s]*([\d,]+\.\d{2})"
    }
    extracted = {}
    for field, pattern in fields.items():
        match = re.search(pattern, text, re.IGNORECASE)
        extracted[field] = match.group(1).strip() if match else ""
    return extracted

# ---- Function to create a structured PDF ----
def create_pdf(data_dict, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    page_width = pdf.w - 2 * pdf.l_margin  # available width

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Structured Invoice Data", ln=True)
    pdf.ln(5)

    # Data fields
    for key, value in data_dict.items():
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(page_width, 10, f"{key}:", border=0)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(page_width, 10, value if value else "-", border=0)
        pdf.ln(2)

    pdf.output(output_path)

# ---- File uploader ----
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(uploaded_file.read())
        tmp_pdf_path = tmp_pdf.name

    try:
        pages = convert_from_path(tmp_pdf_path, dpi=300, poppler_path=poppler_path)

        extracted_text = ""
        for page in pages:
            extracted_text += pytesseract.image_to_string(page) + "\n"

        # Show raw extracted text
        df = pd.DataFrame({"Extracted Text": [extracted_text]})
        st.subheader("Extracted Invoice Data (Raw)")
        st.dataframe(df)

        # Extract structured data
        structured_data = extract_invoice_fields(extracted_text)

        # Save structured PDF
        output_pdf_path = os.path.join(tempfile.gettempdir(), "structured_invoice.pdf")
        create_pdf(structured_data, output_pdf_path)

        # Provide download
        with open(output_pdf_path, "rb") as f:
            st.download_button(
                label="Download Structured PDF",
                data=f,
                file_name="structured_invoice.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"Error processing PDF: {e}")

    finally:
        if os.path.exists(tmp_pdf_path):
            os.remove(tmp_pdf_path)