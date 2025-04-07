# pdf/visit_pdf.py
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether, PageBreak, Frame, BaseDocTemplate, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor, black, gray, lightgrey, white
from reportlab.pdfgen import canvas
from PyQt6.QtWidgets import QFileDialog, QMessageBox # For save dialog
from pathlib import Path
import base64 # Though not strictly needed if using Image directly

# --- Configuration ---
CLINIC_NAME = "Salman Dental Clinic"
DOCTOR_NAME = "Dr. Muhammad Salman"
QUALIFICATIONS = "BDS, MD, DBS"
DOCTOR_PHONE = "03411738830" # Renamed for clarity
CLINIC_ADDRESS = "Nawagai Buner"
CLINIC_PHONE = DOCTOR_PHONE # Assuming clinic phone is same as doctor's for footer
LOGO_PATH_STR = "logo.png"  # Assumes logo.png is in the root directory

# Check if logo exists
LOGO_EXISTS = os.path.exists(LOGO_PATH_STR)
LOGO_IMG = None
LOGO_WIDTH, LOGO_HEIGHT = 25*mm, 12.5*mm # Desired logo dimensions
if LOGO_EXISTS:
    try:
        LOGO_IMG = Image(LOGO_PATH_STR, width=LOGO_WIDTH, height=LOGO_HEIGHT)
        LOGO_IMG.hAlign = 'LEFT'
    except Exception as e:
        print(f"Warning: Could not load logo image '{LOGO_PATH_STR}'. Error: {e}")
        LOGO_EXISTS = False # Treat as non-existent if loading fails

# --- Styling (Inspired by Template) ---
# Define Colors
color_primary = HexColor("#3498db") # Blue accent (like template headers/lines)
color_secondary = HexColor("#2c3e50") # Dark Blue/Gray for text/headers
color_text_light = HexColor("#555555") # Lighter gray text
color_border = HexColor("#dddddd") # Light border color
color_header_bg = HexColor("#34495e") # Dark background for table headers
color_row_alt = HexColor("#f8f9f9") # Very light background for alternate rows

# Define Styles
styles = getSampleStyleSheet()
# Using Helvetica as a standard clean font. Register Roboto TTF if available & preferred.
base_font = 'Helvetica'
bold_font = 'Helvetica-Bold'

styles.add(ParagraphStyle(name='Normal_Left', parent=styles['Normal'], alignment=TA_LEFT, fontName=base_font, fontSize=9, leading=11))
styles.add(ParagraphStyle(name='Normal_Right', parent=styles['Normal_Left'], alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='Normal_Center', parent=styles['Normal_Left'], alignment=TA_CENTER))

styles.add(ParagraphStyle(name='Clinic_Name_Hdr', parent=styles['Normal_Left'], fontName=bold_font, fontSize=16, textColor=color_secondary, spaceAfter=1))
styles.add(ParagraphStyle(name='Doctor_Info_Hdr', parent=styles['Normal_Left'], fontName=base_font, fontSize=8, textColor=color_text_light, spaceAfter=1, leading=9))

styles.add(ParagraphStyle(name='Visit_Label_Hdr', parent=styles['Normal_Right'], fontName=bold_font, fontSize=9, textColor=color_secondary))
styles.add(ParagraphStyle(name='Visit_Value_Hdr', parent=styles['Normal_Right'], fontName=base_font, fontSize=9, textColor=color_text_light))

styles.add(ParagraphStyle(name='BillTo_Header', parent=styles['Normal_Left'], fontName=bold_font, fontSize=11, textColor=color_primary, spaceAfter=4, leading=12))
styles.add(ParagraphStyle(name='BillTo_Label', parent=styles['Normal_Left'], fontName=bold_font, fontSize=9, textColor=color_text_light))
styles.add(ParagraphStyle(name='BillTo_Value', parent=styles['Normal_Left'], fontName=base_font, fontSize=9, textColor=color_secondary))

styles.add(ParagraphStyle(name='Section_Title', parent=styles['Normal_Left'], fontName=bold_font, fontSize=13, textColor=color_primary, spaceBefore=10, spaceAfter=5, borderBottomWidth=1, borderBottomColor=color_border, paddingBottom=3))

styles.add(ParagraphStyle(name='Table_Header', parent=styles['Normal_Center'], fontName=bold_font, fontSize=9, textColor=white, alignment=TA_CENTER))
styles.add(ParagraphStyle(name='Table_Cell', parent=styles['Normal_Left'], fontName=base_font, fontSize=9))
styles.add(ParagraphStyle(name='Table_Cell_Right', parent=styles['Table_Cell'], alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='Table_Cell_Center', parent=styles['Table_Cell'], alignment=TA_CENTER))

styles.add(ParagraphStyle(name='Notes_Text', parent=styles['Normal_Left'], fontSize=8, textColor=color_text_light))

styles.add(ParagraphStyle(name='Total_Label', parent=styles['Normal_Right'], fontName=base_font, fontSize=10, textColor=color_text_light))
styles.add(ParagraphStyle(name='Total_Value', parent=styles['Normal_Right'], fontName=bold_font, fontSize=10, textColor=color_secondary))
styles.add(ParagraphStyle(name='GrandTotal_Label', parent=styles['Total_Label'], fontName=bold_font, fontSize=11))
styles.add(ParagraphStyle(name='GrandTotal_Value', parent=styles['Total_Value'], fontName=bold_font, fontSize=11))

styles.add(ParagraphStyle(name='Footer_Text', parent=styles['Normal_Center'], fontSize=7, textColor=gray))

# --- Page Setup and Header/Footer ---
class VisitDocTemplate(BaseDocTemplate):
    """Custom Document Template to handle repeating header/footer."""
    def __init__(self, filename, **kw):
        self.allowSplitting = 0
        BaseDocTemplate.__init__(self, filename, **kw)
        # Define Frames
        # Frame for header content (adjust height based on content)
        frame_header = Frame(self.leftMargin, self.height + self.bottomMargin, self.width, 35*mm,
                             leftPadding=0, bottomPadding=5*mm, rightPadding=0, topPadding=10*mm,
                             id='frame_header', showBoundary=0) # showBoundary=1 for debugging
        # Frame for main body content
        frame_body = Frame(self.leftMargin, self.bottomMargin + 15*mm, self.width, self.height - 35*mm - 5*mm, # Adjusted height and bottom margin
                           leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0,
                           id='frame_body', showBoundary=0)
        # Frame for footer content (adjust height)
        frame_footer = Frame(self.leftMargin, self.bottomMargin, self.width, 15*mm,
                             leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=3*mm,
                             id='frame_footer', showBoundary=0)

        # Add Page Templates
        main_page = PageTemplate(id='main', frames=[frame_header, frame_body, frame_footer], onPage=self._draw_header_footer)
        self.addPageTemplates([main_page])

    def _draw_header_footer(self, canvas, doc):
        """Draws the header and footer on each page."""
        canvas.saveState()
        w, h = doc.pagesize

        # --- Header Drawing ---
        header_y = h - doc.topMargin + 5*mm # Adjust vertical position as needed

        # Draw Logo (if exists)
        if LOGO_EXISTS and LOGO_IMG:
             LOGO_IMG.drawOn(canvas, doc.leftMargin, header_y - LOGO_HEIGHT) # Draw logo

        # Draw Clinic/Doctor Info (Position relative to logo or left margin)
        info_x = doc.leftMargin + (LOGO_WIDTH + 5*mm if LOGO_EXISTS else 0)
        info_block = [
            Paragraph(CLINIC_NAME, styles['Clinic_Name_Hdr']),
            Paragraph(f"{DOCTOR_NAME} ({QUALIFICATIONS})", styles['Doctor_Info_Hdr']),
            Paragraph(f"Phone: {DOCTOR_PHONE}", styles['Doctor_Info_Hdr']),
        ]
        info_width = doc.width * 0.5 # Approx width for clinic info
        info_height = sum([p.wrapOn(canvas, info_width, 1000)[1] for p in info_block]) + 3*mm # Calculate height
        current_y = header_y
        for p in info_block:
            p_w, p_h = p.wrapOn(canvas, info_width, 1000)
            p.drawOn(canvas, info_x, current_y - p_h)
            current_y -= p_h

        # Draw Visit Info (Invoice No, Date - on right)
        visit_info_x = doc.leftMargin + doc.width - 50*mm # X position for right alignment start
        visit_info_width = 50*mm # Width of the visit info block
        visit_number = doc.visit_data.get('visit_id', 'N/A') # Get data passed via build
        visit_date_str = doc.visit_data.get('visit_date', '')
        formatted_date = visit_date_str
        if visit_date_str:
            try:
                visit_date_obj = datetime.strptime(visit_date_str, "%Y-%m-%d")
                formatted_date = visit_date_obj.strftime("%d/%m/%Y")
            except (ValueError, TypeError): pass

        visit_block = [
            Paragraph(f"<font face='{bold_font}'>Visit No:</font> #{visit_number}", styles['Visit_Value_Hdr']),
            Paragraph(f"<font face='{bold_font}'>Date:</font> {formatted_date}", styles['Visit_Value_Hdr']),
        ]
        current_y = header_y
        for p in visit_block:
             p_w, p_h = p.wrapOn(canvas, visit_info_width, 1000)
             p.drawOn(canvas, visit_info_x, current_y - p_h)
             current_y -= (p_h + 1) # Add small gap

        # Optional: Draw a line below header
        canvas.setStrokeColor(color_border)
        canvas.setLineWidth(0.5)
        line_y = h - doc.topMargin - 25*mm # Adjust Y position of line
        canvas.line(doc.leftMargin, line_y, doc.leftMargin + doc.width, line_y)

        # --- Footer Drawing ---
        footer_y = doc.bottomMargin # Position footer at the bottom margin
        footer_text_line1 = f"{CLINIC_NAME} - {CLINIC_ADDRESS}"
        footer_text_line2 = f"Phone: {CLINIC_PHONE} | Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Page {canvas.getPageNumber()}"

        p1 = Paragraph(footer_text_line1, styles['Footer_Text'])
        p2 = Paragraph(footer_text_line2, styles['Footer_Text'])
        w1, h1 = p1.wrapOn(canvas, doc.width, 1000)
        w2, h2 = p2.wrapOn(canvas, doc.width, 1000)

        p1.drawOn(canvas, doc.leftMargin, footer_y + h2) # Draw line 1 above line 2
        p2.drawOn(canvas, doc.leftMargin, footer_y)     # Draw line 2 at bottom

        canvas.restoreState()


# --- PDF Generation Function ---

def generate_visit_pdf(visit_data, patient_data, services, prescriptions, suggested_filename="visit_report.pdf"):
    """
    Generates a professional A4 PDF report for a patient visit, saving the file.

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

    # --- Document Setup ---
    doc = VisitDocTemplate(file_path, pagesize=A4,
                          leftMargin=15*mm, rightMargin=15*mm,
                          topMargin=30*mm, bottomMargin=20*mm) # Margins adjusted for header/footer frames

    # --- Pass data needed for header/footer ---
    doc.visit_data = visit_data # Make data accessible in onPage

    # --- Build Flowables (Content for the body frame) ---
    story = []

    # Helper function
    def get_data(data_dict, key, default=''):
        val = data_dict.get(key, default)
        return val if val is not None else default

    # 1. Patient Info ("BILL TO" Style) - Positioned using layout or table
    patient_name = get_data(patient_data, 'name', 'N/A')
    patient_fname = get_data(patient_data, 'father_name', '')
    patient_sex = get_data(patient_data, 'sex', '')
    patient_phone = get_data(patient_data, 'phone_number', '')
    patient_address = get_data(patient_data, 'address', '')

    bill_to_content = [
        Paragraph("Patient Details:", styles['BillTo_Header']),
        Paragraph(f"<font face='{bold_font}'>Name:</font> {patient_name}", styles['BillTo_Value']),
    ]
    if patient_fname: bill_to_content.append(Paragraph(f"<font face='{bold_font}'>Father/Husband:</font> {patient_fname}", styles['BillTo_Value']))
    if patient_sex: bill_to_content.append(Paragraph(f"<font face='{bold_font}'>Sex:</font> {patient_sex}", styles['BillTo_Value']))
    if patient_phone: bill_to_content.append(Paragraph(f"<font face='{bold_font}'>Phone:</font> {patient_phone}", styles['BillTo_Value']))
    if patient_address: bill_to_content.append(Paragraph(f"<font face='{bold_font}'>Address:</font> {patient_address.replace(chr(10), ', ')}", styles['BillTo_Value'])) # Replace newline for address

    # Use a table to position BILL TO on the right (adjust colWidths)
    # [[Spacer, BillToContent]] structure
    bill_to_table = Table([
        [Spacer(1, 1), bill_to_content] # Empty spacer on left, content on right
    ], colWidths=[doc.width * 0.5, doc.width * 0.5], style=TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(bill_to_table)
    story.append(Spacer(1, 8*mm))

    # 2. Services Section
    if services:
        story.append(Paragraph("Services Performed", styles['Section_Title']))
        service_data = [[
            Paragraph('Service', styles['Table_Header']),
            Paragraph('Details (Tooth # / Notes)', styles['Table_Header']),
            Paragraph('Price (Rs.)', styles['Table_Header']),
        ]]
        total_service_cost = 0.0
        for i, service in enumerate(services):
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

        service_table = Table(service_data, colWidths=[doc.width * 0.4, doc.width * 0.4, doc.width * 0.2]) # Adjust widths
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), color_header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),
            ('TOPPADDING', (0, 0), (-1, 0), 2*mm),
            ('GRID', (0, 0), (-1, -1), 0.5, color_border),
             # Alternating Row Colors
            *[( 'BACKGROUND', (0, row_idx), (-1, row_idx), color_row_alt)
                for row_idx in range(1, len(service_data)) if row_idx % 2 != 0],
            # Right align price column cells
             ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ]))
        story.append(KeepTogether(service_table))
        story.append(Spacer(1, 5*mm))

    # 3. Prescriptions Section
    if prescriptions:
        story.append(Paragraph("Prescriptions Issued", styles['Section_Title']))
        prescription_data = [[
            Paragraph('Medication', styles['Table_Header']),
            Paragraph('Qty', styles['Table_Header']),
            Paragraph('Instructions', styles['Table_Header']),
            Paragraph('Price (Rs.)', styles['Table_Header']),
        ]]
        total_med_cost = 0.0
        for i, med in enumerate(prescriptions):
            price = float(get_data(med, 'price_charged', 0.0))
            total_med_cost += price
            row = [
                Paragraph(get_data(med, 'medication_name', 'N/A'), styles['Table_Cell']),
                Paragraph(str(get_data(med, 'quantity', '')), styles['Table_Cell_Center']),
                Paragraph(get_data(med, 'instructions', ''), styles['Table_Cell']),
                Paragraph(f"{price:.2f}", styles['Table_Cell_Right']),
            ]
            prescription_data.append(row)

        med_table = Table(prescription_data, colWidths=[doc.width*0.35, doc.width*0.1, doc.width*0.35, doc.width*0.2]) # Adjust widths
        med_table.setStyle(TableStyle([
             ('BACKGROUND', (0, 0), (-1, 0), color_header_bg),
             ('TEXTCOLOR', (0, 0), (-1, 0), white),
             ('ALIGN', (0, 0), (-1, 0), 'CENTER'), # Header alignment
             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
             ('FONTNAME', (0, 0), (-1, 0), bold_font),
             ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),
             ('TOPPADDING', (0, 0), (-1, 0), 2*mm),
             ('GRID', (0, 0), (-1, -1), 0.5, color_border),
              *[( 'BACKGROUND', (0, row_idx), (-1, row_idx), color_row_alt)
                for row_idx in range(1, len(prescription_data)) if row_idx % 2 != 0],
             # Cell alignments
             ('ALIGN', (1, 1), (1, -1), 'CENTER'), # Qty column
             ('ALIGN', (3, 1), (3, -1), 'RIGHT'),  # Price column
         ]))
        story.append(KeepTogether(med_table))
        story.append(Spacer(1, 5*mm))

    # 4. Visit Notes (Optional)
    notes = get_data(visit_data, 'notes')
    lab_results = get_data(visit_data, 'lab_results')
    if notes or lab_results:
        notes_content = []
        if notes: notes_content.append(Paragraph(f"<b>Visit Notes:</b> {notes.replace(chr(10), '<br/>')}", styles['Notes_Text']))
        if lab_results: notes_content.append(Paragraph(f"<b>Lab Results:</b> {lab_results.replace(chr(10), '<br/>')}", styles['Notes_Text']))
        story.append(KeepTogether(notes_content)) # Keep notes together
        story.append(Spacer(1, 5*mm))


    # 5. Financial Summary (Positioned Right)
    total_cost = float(get_data(visit_data, 'total_amount', 0.0))
    paid_amount = float(get_data(visit_data, 'paid_amount', 0.0))
    due_amount = max(0.0, total_cost - paid_amount)
    # Ideally calculate subtotal from items, using total_cost as fallback here
    subtotal = total_service_cost + total_med_cost if services or prescriptions else total_cost

    totals_data = [
        [Paragraph("Subtotal:", styles['Total_Label']), Paragraph(f"{subtotal:.2f}", styles['Total_Value'])],
        # Add Tax row here if applicable
        [Paragraph("Grand Total:", styles['GrandTotal_Label']), Paragraph(f"Rs. {total_cost:.2f}", styles['GrandTotal_Value'])],
        [Paragraph("Amount Paid:", styles['Total_Label']), Paragraph(f"Rs. {paid_amount:.2f}", styles['Total_Value'])],
        [Paragraph("Amount Due:", styles['Total_Label']), Paragraph(f"Rs. {due_amount:.2f}", styles['Total_Value'])],
    ]

    totals_table = Table(totals_data, colWidths=[doc.width * 0.3, doc.width * 0.2], hAlign='RIGHT') # Position on right
    totals_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
        # Line above Grand Total
        ('LINEABOVE', (0, 1), (1, 1), 1, color_secondary),
        ('BOTTOMPADDING', (0, 1), (1, 1), 2*mm), # Extra padding around total
        ('TOPPADDING', (0, 1), (1, 1), 2*mm),
    ]))
    story.append(totals_table)

    # --- Build PDF ---
    try:
        doc.build(story)
        return file_path
    except PermissionError:
         QMessageBox.critical(None, "Permission Error",
                             f"Could not save PDF to '{file_path}'.\n"
                             "Please ensure the file is not open in another application and you have write permissions.")
         return None
    except Exception as e:
        import traceback
        print(traceback.format_exc()) # Print detailed error to console
        QMessageBox.critical(None, "PDF Generation Error", f"Failed to generate PDF.\nError: {e}")
        return None

# --- Example Usage (for testing this file directly) ---
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
    ]*3 # Repeat for pagination testing
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

    # sys.exit(app.exec()) # Keep app running if needed for dialogs