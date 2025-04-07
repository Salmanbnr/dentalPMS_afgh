import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor, black, gray
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from PyQt6.QtWidgets import QFileDialog, QMessageBox

# --- Styling ---
# Define Colors
color_primary = HexColor("#3498db")    # Blue accent for headers/lines
color_secondary = HexColor("#2c3e50")  # Dark Blue/Gray for text/headers
color_text_light = HexColor("#555555") # Lighter gray text
color_border = HexColor("#dddddd")     # Light border color
color_header_bg = HexColor("#34495e")  # Dark background for headers
color_row_alt = HexColor("#f8f9f9")    # Light background for alternate rows

# Define Styles
styles = getSampleStyleSheet()
base_font = 'Helvetica'
bold_font = 'Helvetica-Bold'

styles.add(ParagraphStyle(name='Normal_Left', parent=styles['Normal'], alignment=TA_LEFT, fontName=base_font, fontSize=9, leading=11))
styles.add(ParagraphStyle(name='Normal_Right', parent=styles['Normal_Left'], alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='Normal_Center', parent=styles['Normal_Left'], alignment=TA_CENTER))

styles.add(ParagraphStyle(name='Visit_Label_Hdr', parent=styles['Normal_Right'], fontName=bold_font, fontSize=9, textColor=color_secondary))
styles.add(ParagraphStyle(name='Visit_Value_Hdr', parent=styles['Normal_Right'], fontName=base_font, fontSize=9, textColor=color_text_light))

styles.add(ParagraphStyle(name='BillTo_Header', parent=styles['Normal_Left'], fontName=bold_font, fontSize=11, textColor=color_primary, spaceAfter=4, leading=12))
styles.add(ParagraphStyle(name='BillTo_Label', parent=styles['Normal_Left'], fontName=bold_font, fontSize=9, textColor=color_text_light))
styles.add(ParagraphStyle(name='BillTo_Value', parent=styles['Normal_Left'], fontName=base_font, fontSize=9, textColor=color_secondary))

styles.add(ParagraphStyle(name='Section_Title', parent=styles['Normal_Left'], fontName=bold_font, fontSize=13, textColor=color_primary, spaceBefore=10, spaceAfter=5, borderBottomWidth=1, borderBottomColor=color_border, paddingBottom=3))

styles.add(ParagraphStyle(name='Table_Header', parent=styles['Normal_Center'], fontName=bold_font, fontSize=9, textColor='white', alignment=TA_CENTER))
styles.add(ParagraphStyle(name='Table_Cell', parent=styles['Normal_Left'], fontName=base_font, fontSize=9))
styles.add(ParagraphStyle(name='Table_Cell_Right', parent=styles['Table_Cell'], alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='Table_Cell_Center', parent=styles['Table_Cell'], alignment=TA_CENTER))

styles.add(ParagraphStyle(name='Notes_Text', parent=styles['Normal_Left'], fontSize=8, textColor=color_text_light))

styles.add(ParagraphStyle(name='Total_Label', parent=styles['Normal_Right'], fontName=base_font, fontSize=10, textColor=color_text_light))
styles.add(ParagraphStyle(name='Total_Value', parent=styles['Normal_Right'], fontName=bold_font, fontSize=10, textColor=color_secondary))
styles.add(ParagraphStyle(name='GrandTotal_Label', parent=styles['Total_Label'], fontName=bold_font, fontSize=11))
styles.add(ParagraphStyle(name='GrandTotal_Value', parent=styles['Total_Value'], fontName=bold_font, fontSize=11))

# --- PDF Generation Function ---
def generate_visit_pdf(visit_data, patient_data, services, prescriptions, suggested_filename="visit_report.pdf"):
    """
    Generates a PDF report for a patient visit by placing content on an existing PDF template.
    
    Args:
        visit_data (dict): Dictionary containing visit details.
        patient_data (dict): Dictionary containing patient details.
        services (list): List of dictionaries for services performed.
        prescriptions (list): List of dictionaries for prescriptions issued.
        suggested_filename (str): Default filename for the save dialog.
        
    Returns:
        str: The path where the PDF was saved, or None if cancelled or failed.
    """
    # --- Ask user where to save ---
    options = QFileDialog.Option.DontUseNativeDialog
    file_path, _ = QFileDialog.getSaveFileName(
        None,  # Parent widget
        "Save Visit Report PDF",
        suggested_filename,
        "PDF Files (*.pdf);;All Files (*)",
        options=options
    )
    
    if not file_path:
        return None  # User cancelled
        
    if not file_path.lower().endswith(".pdf"):
        file_path += ".pdf"
    
    # Path to template PDF
    template_path = "pdf_template/template.pdf"
    if not os.path.exists(template_path):
        QMessageBox.critical(None, "Template Missing", 
                            f"PDF template not found at '{template_path}'.\n"
                            "Please ensure the template exists.")
        return None
    
    # Helper function
    def get_data(data_dict, key, default=''):
        val = data_dict.get(key, default)
        return val if val is not None else default
    
    # Create an in-memory PDF with content
    content_buffer = BytesIO()
    
    # Set page dimensions and margins
    page_width, page_height = A4  # Standard A4 size
    left_margin = 15*mm
    right_margin = 15*mm
    top_margin = 73*mm  # Start content 73mm from top as requested
    bottom_margin = 30*mm  # End content 30mm from bottom as requested
    content_height = page_height - top_margin - bottom_margin
    
    # Create SimpleDocTemplate for content generation
    doc = SimpleDocTemplate(
        content_buffer,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )
    
    # Build content flowables
    story = []
    
    # 1. Visit Information (top right aligned)
    visit_number = get_data(visit_data, 'visit_id', 'N/A')
    visit_date_str = get_data(visit_data, 'visit_date', '')
    formatted_date = visit_date_str
    if visit_date_str:
        try:
            visit_date_obj = datetime.strptime(visit_date_str, "%Y-%m-%d")
            formatted_date = visit_date_obj.strftime("%d/%m/%Y")
        except (ValueError, TypeError): 
            pass
    
    visit_info = [
        [Paragraph('', styles['Normal_Left']), 
         Paragraph(f"<font face='{bold_font}'>Visit No:</font> #{visit_number}", styles['Visit_Value_Hdr'])],
        [Paragraph('', styles['Normal_Left']), 
         Paragraph(f"<font face='{bold_font}'>Date:</font> {formatted_date}", styles['Visit_Value_Hdr'])]
    ]
    
    visit_table = Table(visit_info, colWidths=[doc.width * 0.7, doc.width * 0.3])
    visit_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(visit_table)
    story.append(Spacer(1, 8*mm))
    
    # 2. Patient Info
    patient_name = get_data(patient_data, 'name', 'N/A')
    patient_fname = get_data(patient_data, 'father_name', '')
    patient_sex = get_data(patient_data, 'sex', '')
    patient_phone = get_data(patient_data, 'phone_number', '')
    patient_address = get_data(patient_data, 'address', '')
    
    story.append(Paragraph("Patient Details:", styles['BillTo_Header']))
    
    # Create patient info table for better layout
    patient_info_data = []
    
    # Row 1: Name and Sex
    row1 = [Paragraph(f"<font face='{bold_font}'>Name:</font> {patient_name}", styles['BillTo_Value'])]
    if patient_sex:
        row1.append(Paragraph(f"<font face='{bold_font}'>Sex:</font> {patient_sex}", styles['BillTo_Value']))
    else:
        row1.append(Paragraph("", styles['BillTo_Value']))
    patient_info_data.append(row1)
    
    # Row 2: Father/Husband and Phone
    row2 = []
    if patient_fname:
        row2.append(Paragraph(f"<font face='{bold_font}'>Father/Husband:</font> {patient_fname}", styles['BillTo_Value']))
    else:
        row2.append(Paragraph("", styles['BillTo_Value']))
        
    if patient_phone:
        row2.append(Paragraph(f"<font face='{bold_font}'>Phone:</font> {patient_phone}", styles['BillTo_Value']))
    else:
        row2.append(Paragraph("", styles['BillTo_Value']))
    patient_info_data.append(row2)
    
    # Row 3: Address (spans both columns)
    if patient_address:
        patient_info_data.append([
            Paragraph(f"<font face='{bold_font}'>Address:</font> {patient_address.replace(chr(10), ', ')}", 
                     styles['BillTo_Value']),
            Paragraph("", styles['BillTo_Value'])
        ])
    
    patient_table = Table(patient_info_data, colWidths=[doc.width * 0.5, doc.width * 0.5])
    patient_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('SPAN', (0, 2), (1, 2)) if patient_address else None  # Span address across columns
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 10*mm))
    
    # 3. Services Section
    if services:
        story.append(Paragraph("Services Performed", styles['Section_Title']))
        service_data = [[
            Paragraph('Service', styles['Table_Header']),
            Paragraph('Details (Tooth # / Notes)', styles['Table_Header']),
            Paragraph('Price (Rs.)', styles['Table_Header']),
        ]]
        
        total_service_cost = 0.0
        for service in services:
            price = float(get_data(service, 'price_charged', 0.0))
            total_service_cost += price
            tooth = str(get_data(service, 'tooth_number', ''))
            notes = get_data(service, 'notes', '')
            details = f"{'T:' + tooth if tooth else ''}{'; ' + notes if notes else ''}".strip('; ')
            
            row = [
                Paragraph(get_data(service, 'service_name', 'N/A'), styles['Table_Cell']),
                Paragraph(details, styles['Table_Cell']),
                Paragraph(f"{price:.2f}", styles['Table_Cell_Right']),
            ]
            service_data.append(row)
        
        service_table = Table(service_data, colWidths=[doc.width * 0.4, doc.width * 0.4, doc.width * 0.2])
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), color_header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),
            ('TOPPADDING', (0, 0), (-1, 0), 2*mm),
            ('GRID', (0, 0), (-1, -1), 0.5, color_border),
            # Alternating Row Colors
            *[('BACKGROUND', (0, row_idx), (-1, row_idx), color_row_alt)
               for row_idx in range(1, len(service_data)) if row_idx % 2 != 0],
            # Right align price column cells
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ]))
        story.append(KeepTogether(service_table))
        story.append(Spacer(1, 5*mm))
    
    # 4. Prescriptions Section
    if prescriptions:
        story.append(Paragraph("Prescriptions Issued", styles['Section_Title']))
        prescription_data = [[
            Paragraph('Medication', styles['Table_Header']),
            Paragraph('Qty', styles['Table_Header']),
            Paragraph('Instructions', styles['Table_Header']),
            Paragraph('Price (Rs.)', styles['Table_Header']),
        ]]
        
        total_med_cost = 0.0
        for med in prescriptions:
            price = float(get_data(med, 'price_charged', 0.0))
            total_med_cost += price
            row = [
                Paragraph(get_data(med, 'medication_name', 'N/A'), styles['Table_Cell']),
                Paragraph(str(get_data(med, 'quantity', '')), styles['Table_Cell_Center']),
                Paragraph(get_data(med, 'instructions', ''), styles['Table_Cell']),
                Paragraph(f"{price:.2f}", styles['Table_Cell_Right']),
            ]
            prescription_data.append(row)
        
        med_table = Table(prescription_data, colWidths=[doc.width*0.35, doc.width*0.1, doc.width*0.35, doc.width*0.2])
        med_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), color_header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),
            ('TOPPADDING', (0, 0), (-1, 0), 2*mm),
            ('GRID', (0, 0), (-1, -1), 0.5, color_border),
            *[('BACKGROUND', (0, row_idx), (-1, row_idx), color_row_alt)
              for row_idx in range(1, len(prescription_data)) if row_idx % 2 != 0],
            # Cell alignments
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Qty column
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # Price column
        ]))
        story.append(KeepTogether(med_table))
        story.append(Spacer(1, 5*mm))
    
    # 5. Visit Notes (Optional)
    notes = get_data(visit_data, 'notes')
    lab_results = get_data(visit_data, 'lab_results')
    if notes or lab_results:
        notes_content = []
        if notes: 
            notes_content.append(Paragraph(f"<b>Visit Notes:</b> {notes.replace(chr(10), '<br/>')}", 
                                          styles['Notes_Text']))
        if lab_results: 
            notes_content.append(Paragraph(f"<b>Lab Results:</b> {lab_results.replace(chr(10), '<br/>')}", 
                                          styles['Notes_Text']))
        
        # Create a table for notes with borders
        notes_table = Table([[note] for note in notes_content], colWidths=[doc.width])
        notes_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 0.5, color_border),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        story.append(KeepTogether(notes_table))
        story.append(Spacer(1, 5*mm))
    
    # 6. Financial Summary
    total_cost = float(get_data(visit_data, 'total_amount', 0.0))
    paid_amount = float(get_data(visit_data, 'paid_amount', 0.0))
    due_amount = max(0.0, total_cost - paid_amount)
    subtotal = total_service_cost + total_med_cost if services or prescriptions else total_cost
    
    totals_data = [
        [Paragraph("Subtotal:", styles['Total_Label']), Paragraph(f"{subtotal:.2f}", styles['Total_Value'])],
        [Paragraph("Grand Total:", styles['GrandTotal_Label']), Paragraph(f"Rs. {total_cost:.2f}", styles['GrandTotal_Value'])],
        [Paragraph("Amount Paid:", styles['Total_Label']), Paragraph(f"Rs. {paid_amount:.2f}", styles['Total_Value'])],
        [Paragraph("Amount Due:", styles['Total_Label']), Paragraph(f"Rs. {due_amount:.2f}", styles['Total_Value'])],
    ]
    
    totals_table = Table(totals_data, colWidths=[doc.width * 0.3, doc.width * 0.2], hAlign='RIGHT')
    totals_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
        # Line above Grand Total
        ('LINEABOVE', (0, 1), (1, 1), 1, color_secondary),
        ('BOTTOMPADDING', (0, 1), (1, 1), 2*mm),
        ('TOPPADDING', (0, 1), (1, 1), 2*mm),
    ]))
    story.append(totals_table)
    
    # Build the content PDF
    doc.build(story)
    
    # --- Now merge content with template ---
    try:
        # Read the template PDF
        template_pdf = PdfReader(template_path)
        
        # Read the content PDF from buffer
        content_buffer.seek(0)
        content_pdf = PdfReader(content_buffer)
        
        # Create a PDF writer for output
        output_pdf = PdfWriter()
        
        # Process each page - assuming template has same number of pages as content
        # If template is single page but content has multiple, use template for each content page
        template_page_count = len(template_pdf.pages)
        content_page_count = len(content_pdf.pages)
        
        for i in range(content_page_count):
            # Get template page (reuse last page if content has more pages)
            template_idx = min(i, template_page_count - 1)
            template_page = template_pdf.pages[template_idx]
            
            # Get content page
            content_page = content_pdf.pages[i]
            
            # Merge template and content
            template_page.merge_page(content_page)
            
            # Add to output
            output_pdf.add_page(template_page)
        
        # Write the output PDF
        with open(file_path, 'wb') as output_file:
            output_pdf.write(output_file)
        
        return file_path
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Print detailed error to console
        QMessageBox.critical(None, "PDF Generation Error", f"Failed to generate PDF.\nError: {e}")
        return None

# --- Example Usage (for testing) ---
if __name__ == '__main__':
    # Dummy data
    test_patient = {
        'patient_id': 101, 'name': 'Asad Khan', 'father_name': 'Jamil Khan',
        'sex': 'Male', 'phone_number': '0300-1234567', 'address': 'House 12, Street 4, G-9/1, Islamabad'
    }
    test_visit = {
        'visit_id': 2024040701, 'visit_date': '2024-04-07',
        'notes': 'Regular checkup.\nPatient reported mild sensitivity in upper right molar. Advised sensitive toothpaste.',
        'lab_results': 'X-Ray Ref: XR123 - No decay found.',
        'total_amount': 3500.00, 'paid_amount': 3000.00
    }
    test_services = [
        {'visit_service_id': 1, 'service_name': 'Routine Cleaning & Polishing', 'tooth_number': None, 'notes': 'Full mouth', 'price_charged': 2500.00},
        {'visit_service_id': 2, 'service_name': 'X-Ray (OPG)', 'tooth_number': None, 'notes': '', 'price_charged': 1000.00},
        {'visit_service_id': 3, 'service_name': 'Fluoride Varnish', 'tooth_number': None, 'notes': 'Applied upper arch', 'price_charged': 0.00},
    ]
    test_prescriptions = [
        {'visit_prescription_id': 1, 'medication_name': 'Sensodyne Repair & Protect', 'quantity': 1, 'instructions': 'Use twice daily', 'price_charged': 0.00},
        {'visit_prescription_id': 2, 'medication_name': 'Pain Relief Max Strength', 'quantity': 10, 'instructions': '1 tab SOS', 'price_charged': 350.50},
    ]
    
    # Need a dummy QApplication for QFileDialog
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    
    pdf_file = generate_visit_pdf(test_visit, test_patient, test_services, test_prescriptions)
    
    if pdf_file:
        print(f"Successfully generated test PDF: {pdf_file}")
        # Optional: try opening it
        try:
            import webbrowser
            webbrowser.open(f"file:///{os.path.abspath(pdf_file)}")
        except Exception as e:
            print(f"Could not auto-open PDF: {e}")
    else:
        print("PDF generation cancelled or failed.")