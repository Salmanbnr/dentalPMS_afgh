# pdf/visit_pdf.py
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor, black, gray, lightgrey, white
from PyQt6.QtWidgets import QFileDialog, QMessageBox # For save dialog

# --- Configuration ---
CLINIC_NAME = "Salman Dental Clinic"
DOCTOR_NAME = "Dr. Muhammad Salman"
QUALIFICATIONS = "BDS, MD, DBS"
PHONE_NUMBER = "03411738830"
CLINIC_ADDRESS = "Nawagai Buner"
LOGO_PATH = "logo.png"  # Assumes logo.png is in the root directory where the script runs
# Check if logo exists, handle gracefully if not
LOGO_EXISTS = os.path.exists(LOGO_PATH)

# --- Styling ---
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='ClinicName', parent=styles['h1'], fontSize=18, alignment=TA_CENTER, spaceBottom=6))
styles.add(ParagraphStyle(name='DoctorInfo', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, spaceBottom=10))
styles.add(ParagraphStyle(name='Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, textColor=gray))
styles.add(ParagraphStyle(name='SectionHeader', parent=styles['h2'], fontSize=12, spaceBefore=10, spaceAfter=5, textColor=HexColor("#3498db"))) # Blue header
styles.add(ParagraphStyle(name='TableHeader', parent=styles['Normal'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=9, textColor=white))
styles.add(ParagraphStyle(name='TableCell', parent=styles['Normal'], fontSize=9))
styles.add(ParagraphStyle(name='TableCellRight', parent=styles['TableCell'], alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='PatientLabel', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle(name='PatientValue', parent=styles['Normal'], fontSize=10))

# Colors
header_bg_color = HexColor("#3498db") # Blue header background
table_header_color = HexColor("#34495e") # Dark blue/gray table header
table_grid_color = lightgrey
alt_row_color = HexColor("#f8f9f9") # Very light gray for alternating rows

# --- PDF Generation Function ---

def generate_visit_pdf(visit_data, patient_data, services, prescriptions, suggested_filename="visit_report.pdf"):
    """
    Generates a professional A4 PDF report for a patient visit.

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

    # Ensure the path ends with .pdf
    if not file_path.lower().endswith(".pdf"):
        file_path += ".pdf"

    # --- Document Setup ---
    doc = SimpleDocTemplate(file_path, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=20*mm) # Increased bottom margin for footer
    story = []
    width, height = A4 # Page dimensions

    # --- Build Flowables ---

    # 1. Header (Clinic Info & Logo)
    header_table_data = []
    if LOGO_EXISTS:
        try:
            logo = Image(LOGO_PATH, width=30*mm, height=15*mm) # Adjust size as needed
            logo.hAlign = 'LEFT'
            clinic_info = [
                Paragraph(CLINIC_NAME, styles['ClinicName']),
                Paragraph(f"{DOCTOR_NAME} ({QUALIFICATIONS})", styles['DoctorInfo']),
                Paragraph(f"Phone: {PHONE_NUMBER}", styles['DoctorInfo']),
            ]
            # Arrange logo and text side-by-side in a table
            header_table_data = [[logo, clinic_info]]
            header_table_style = TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'), # Center the text block
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ])
            header_table = Table(header_table_data, colWidths=[40*mm, width - 30*mm - 40*mm]) # Adjust colWidths
            header_table.setStyle(header_table_style)
            story.append(header_table)

        except Exception as e:
            print(f"Warning: Could not load logo '{LOGO_PATH}'. Error: {e}")
            # Fallback to text-only header if logo fails
            story.append(Paragraph(CLINIC_NAME, styles['ClinicName']))
            story.append(Paragraph(f"{DOCTOR_NAME} ({QUALIFICATIONS})", styles['DoctorInfo']))
            story.append(Paragraph(f"Phone: {PHONE_NUMBER}", styles['DoctorInfo']))
    else:
        print(f"Warning: Logo file '{LOGO_PATH}' not found.")
        # Text-only header
        story.append(Paragraph(CLINIC_NAME, styles['ClinicName']))
        story.append(Paragraph(f"{DOCTOR_NAME} ({QUALIFICATIONS})", styles['DoctorInfo']))
        story.append(Paragraph(f"Phone: {PHONE_NUMBER}", styles['DoctorInfo']))

    story.append(Spacer(1, 8*mm)) # Space after header

    # 2. Patient and Visit Info Section
    story.append(Paragraph("Visit & Patient Details", styles['SectionHeader']))
    visit_date_str = visit_data.get('visit_date', 'N/A')
    try:
        # Attempt to format date nicely
        visit_date_obj = datetime.strptime(visit_date_str, "%Y-%m-%d")
        formatted_date = visit_date_obj.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        formatted_date = visit_date_str # Use original string if format fails

    patient_info_data = [
        [Paragraph("Patient Name:", styles['PatientLabel']), Paragraph(patient_data.get('name', 'N/A'), styles['PatientValue'])],
        [Paragraph("Patient ID:", styles['PatientLabel']), Paragraph(str(patient_data.get('patient_id', 'N/A')), styles['PatientValue'])],
        [Paragraph("Visit ID:", styles['PatientLabel']), Paragraph(str(visit_data.get('visit_id', 'N/A')), styles['PatientValue'])],
        [Paragraph("Visit Date:", styles['PatientLabel']), Paragraph(formatted_date, styles['PatientValue'])],
    ]
    patient_table = Table(patient_info_data, colWidths=[40*mm, width - 30*mm - 40*mm])
    patient_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 5*mm))

    # 3. Visit Notes and Lab Results (Optional)
    notes = visit_data.get('notes')
    lab_results = visit_data.get('lab_results')
    if notes or lab_results:
        story.append(Paragraph("Visit Notes & Observations", styles['SectionHeader']))
        if notes:
             story.append(Paragraph(f"<b>Notes:</b> {notes.replace(chr(10), '<br/>')}", styles['TableCell'])) # Replace newline with <br/>
             story.append(Spacer(1, 2*mm))
        if lab_results:
             story.append(Paragraph(f"<b>Lab Results:</b> {lab_results.replace(chr(10), '<br/>')}", styles['TableCell']))
        story.append(Spacer(1, 5*mm))

    # 4. Services Section
    if services:
        story.append(Paragraph("Services Performed", styles['SectionHeader']))
        service_data = [[
            Paragraph('Service', styles['TableHeader']),
            Paragraph('Tooth #', styles['TableHeader']),
            Paragraph('Notes', styles['TableHeader']),
            Paragraph('Price', styles['TableHeader']),
        ]]
        total_service_cost = 0.0
        for i, service in enumerate(services):
            price = service.get('price_charged', 0.0)
            total_service_cost += price
            row_style = styles['TableCell'] if i % 2 == 0 else styles['TableCell'] # Use same style for now, apply bg color below
            row = [
                Paragraph(service.get('service_name', 'N/A'), row_style),
                Paragraph(str(service.get('tooth_number', '')), row_style),
                Paragraph(service.get('notes', ''), row_style),
                Paragraph(f"{price:.2f}", styles['TableCellRight']),
            ]
            service_data.append(row)

        # Add Total Row
        service_data.append([
            Paragraph("<b>Service Total:</b>", styles['TableCellRight']), '', '',
            Paragraph(f"<b>{total_service_cost:.2f}</b>", styles['TableCellRight'])
        ])

        service_table = Table(service_data, colWidths=[60*mm, 20*mm, width - 30*mm - 110*mm, 30*mm])
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), table_header_color), # Header background
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'), # Right align price column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),
            ('TOPPADDING', (0, 0), (-1, 0), 2*mm),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2*mm), # Padding for content rows
            ('TOPPADDING', (0, 1), (-1, -1), 1*mm),
            # Grid lines
            ('GRID', (0, 0), (-1, -2), 0.5, table_grid_color), # Grid for all but last row
            ('LINEABOVE', (0, -1), (-1, -1), 1, black), # Line above total
            ('LINEBELOW', (0, -1), (-1, -1), 1, black), # Line below total
            ('SPAN', (0, -1), (2, -1)), # Span "Service Total" text
            # Alternating Row Colors (applied to content rows)
            # This requires iterating and adding commands
            *[( 'BACKGROUND', (0, row_idx), (-1, row_idx), alt_row_color)
                for row_idx in range(1, len(service_data) -1) if row_idx % 2 != 0], # -1 to skip total row
        ]))
        story.append(KeepTogether(service_table)) # Keep table together if possible
        story.append(Spacer(1, 5*mm))

    # 5. Prescriptions Section
    if prescriptions:
        story.append(Paragraph("Prescriptions Issued", styles['SectionHeader']))
        prescription_data = [[
            Paragraph('Medication', styles['TableHeader']),
            Paragraph('Qty', styles['TableHeader']),
            Paragraph('Instructions', styles['TableHeader']),
            Paragraph('Price', styles['TableHeader']),
        ]]
        total_med_cost = 0.0
        for i, med in enumerate(prescriptions):
            price = med.get('price_charged', 0.0)
            total_med_cost += price
            row_style = styles['TableCell']
            row = [
                Paragraph(med.get('medication_name', 'N/A'), row_style),
                Paragraph(str(med.get('quantity', '')), styles['TableCellRight']), # Right align Qty
                Paragraph(med.get('instructions', ''), row_style),
                Paragraph(f"{price:.2f}", styles['TableCellRight']),
            ]
            prescription_data.append(row)

        # Add Total Row
        prescription_data.append([
            Paragraph("<b>Medication Total:</b>", styles['TableCellRight']), '', '',
            Paragraph(f"<b>{total_med_cost:.2f}</b>", styles['TableCellRight'])
        ])

        med_table = Table(prescription_data, colWidths=[60*mm, 20*mm, width - 30*mm - 110*mm, 30*mm])
        med_table.setStyle(TableStyle([
             ('BACKGROUND', (0, 0), (-1, 0), table_header_color),
             ('TEXTCOLOR', (0, 0), (-1, 0), white),
             ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
             ('ALIGN', (1, 0), (1, -1), 'RIGHT'), # Right align Qty column
             ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'), # Right align Price column
             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
             ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),
             ('TOPPADDING', (0, 0), (-1, 0), 2*mm),
             ('BOTTOMPADDING', (0, 1), (-1, -1), 2*mm),
             ('TOPPADDING', (0, 1), (-1, -1), 1*mm),
             ('GRID', (0, 0), (-1, -2), 0.5, table_grid_color),
             ('LINEABOVE', (0, -1), (-1, -1), 1, black),
             ('LINEBELOW', (0, -1), (-1, -1), 1, black),
             ('SPAN', (0, -1), (2, -1)), # Span "Medication Total"
              *[( 'BACKGROUND', (0, row_idx), (-1, row_idx), alt_row_color)
                for row_idx in range(1, len(prescription_data) -1) if row_idx % 2 != 0],
         ]))
        story.append(KeepTogether(med_table))
        story.append(Spacer(1, 5*mm))

    # 6. Financial Summary
    story.append(Paragraph("Financial Summary", styles['SectionHeader']))
    total_cost = visit_data.get('total_amount', 0.0)
    paid_amount = visit_data.get('paid_amount', 0.0)
    due_amount = max(0.0, total_cost - paid_amount)

    financial_data = [
        [Paragraph("Total Bill:", styles['PatientLabel']), Paragraph(f"{total_cost:.2f}", styles['TableCellRight'])],
        [Paragraph("Amount Paid:", styles['PatientLabel']), Paragraph(f"{paid_amount:.2f}", styles['TableCellRight'])],
        [Paragraph("Amount Due:", styles['PatientLabel']), Paragraph(f"{due_amount:.2f}", styles['TableCellRight'])],
    ]
    financial_table = Table(financial_data, colWidths=[width - 30*mm - 40*mm, 40*mm]) # Label | Value
    financial_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'), # Right align everything for this simple table
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
        ('LINEABOVE', (0, -1), (-1, -1), 1, black), # Line above Amount Due
        ('FONTNAME', (0, -1), (0, -1), 'Helvetica-Bold'), # Bold Amount Due Label
        ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'), # Bold Amount Due Value
    ]))
    story.append(financial_table)

    # --- Footer ---
    # We use the onFirstPage and onLaterPages arguments of SimpleDocTemplate for footers
    def footer(canvas, doc):
        canvas.saveState()
        footer_text = f"{CLINIC_NAME} - {CLINIC_ADDRESS} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        p = Paragraph(footer_text, styles['Footer'])
        w, h = p.wrap(doc.width, doc.bottomMargin)
        p.drawOn(canvas, doc.leftMargin, h) # Draw at bottom left margin
        canvas.restoreState()

    # --- Build PDF ---
    try:
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        return file_path
    except PermissionError:
         QMessageBox.critical(None, "Permission Error",
                             f"Could not save PDF to '{file_path}'.\n"
                             "Please ensure the file is not open in another application and you have write permissions.")
         return None
    except Exception as e:
        QMessageBox.critical(None, "PDF Generation Error", f"Failed to generate PDF.\nError: {e}")
        return None

# --- Example Usage (for testing this file directly) ---
if __name__ == '__main__':
    # Create dummy data for testing
    test_patient = {'patient_id': 101, 'name': 'Test Patient'}
    test_visit = {'visit_id': 202, 'visit_date': '2024-01-15', 'notes': 'Regular checkup, patient reported mild sensitivity.', 'lab_results': 'X-Ray Ref: XR123 - No issues found.', 'total_amount': 275.50, 'paid_amount': 200.00}
    test_services = [
        {'visit_service_id': 1, 'service_name': 'Routine Cleaning', 'tooth_number': None, 'notes': 'Standard procedure', 'price_charged': 120.00},
        {'visit_service_id': 2, 'service_name': 'X-Ray (Bitewing)', 'tooth_number': None, 'notes': '', 'price_charged': 55.50},
         {'visit_service_id': 3, 'service_name': 'Fluoride Varnish', 'tooth_number': None, 'notes': 'Applied to all teeth', 'price_charged': 0.0}, # Example Free
    ] * 5 # Make services list longer to test pagination
    test_prescriptions = [
        {'visit_prescription_id': 1, 'medication_name': 'PainAway Forte', 'quantity': 20, 'instructions': '1 tablet every 6 hours as needed for pain', 'price_charged': 100.00},
    ]

    # --- Need a dummy QApplication to show QFileDialog ---
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    # --- End dummy app setup ---

    pdf_file = generate_visit_pdf(test_visit, test_patient, test_services, test_prescriptions)

    if pdf_file:
        print(f"Successfully generated test PDF: {pdf_file}")
        # Optional: try opening it
        # import webbrowser, os
        # webbrowser.open(f"file:///{os.path.abspath(pdf_file)}")
    else:
        print("PDF generation cancelled or failed.")

    # sys.exit(app.exec()) # Exit dummy app if needed