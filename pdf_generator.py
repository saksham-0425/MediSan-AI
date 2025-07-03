from fpdf import FPDF
from datetime import datetime
import textwrap

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "MediScan AI - Pneumonia Report", border=False, ln=1, align="C")

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 0, "C")

def generate_pdf(patient_name, age, gender, prediction, confidence, xray_path, heatmap_path, output_path, notes=""):
    pdf = PDF()
    pdf.add_page()

    pdf.set_font("Arial", "", 12)

    # 🔹 Patient Information
    pdf.cell(0, 10, f"Patient Name: {patient_name}", ln=1)
    pdf.cell(0, 10, f"Age: {age}", ln=1)
    pdf.cell(0, 10, f"Gender: {gender}", ln=1)
    pdf.cell(0, 10, f"Prediction: {prediction}", ln=1)
    pdf.cell(0, 10, f"Confidence: {confidence}%", ln=1)

    pdf.ln(5)

    # 🔸 Doctor's Notes (if available)
    if notes.strip():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Doctor's Notes:", ln=1)
        pdf.set_font("Arial", "", 12)
        wrapped = textwrap.wrap(notes, width=90)
        for line in wrapped:
            pdf.multi_cell(0, 8, line)
        pdf.ln(5)

    # 🩻 Chest X-ray Image
    if xray_path:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Chest X-ray:", ln=1)
        try:
            pdf.image(xray_path, w=100)
        except:
            pdf.cell(0, 10, "[Error displaying X-ray image]", ln=1)
        pdf.ln(5)

    # 🔥 Grad-CAM Heatmap Image
    if heatmap_path:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Grad-CAM Heatmap:", ln=1)
        try:
            pdf.image(heatmap_path, w=100)
        except:
            pdf.cell(0, 10, "[Error displaying heatmap image]", ln=1)

    pdf.output(output_path)
    return output_path
