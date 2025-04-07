import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import fitz  # PyMuPDF

# --- Styling ---
color_primary = HexColor("#3498db")
color_secondary = HexColor("#2c3e50")
color_text_light = HexColor("#555555")
color_border = HexColor("#dddddd")
color_header_bg = HexColor("#34495e")
color_row_alt = HexColor("#f8f9f9")

styles = getSampleStyleSheet()
base_font = 'Helvetica'
bold_font = 'Helvetica-Bold'

# Add custom styles
styles.add(ParagraphStyle(name='Normal_Left', parent=styles['Normal'], 
          alignment=TA_LEFT, fontName=base_font, fontSize=9, leading=11))
styles.add(ParagraphStyle(name='Normal_Right', parent=styles['Normal_Left'], 
          alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='Normal_Center', parent=styles['Normal_Left'], 
          alignment=TA_CENTER))

styles.add(ParagraphStyle(name='Visit_Header', parent=styles['Normal_Right'], 
          fontName=bold_font, fontSize=9, textColor=color_secondary))
styles.add(ParagraphStyle(name='BillTo_Header', parent=styles['Normal_Left'], 
          fontName=bold_font, fontSize=11, textColor=color_primary, spaceAfter=4))
styles.add(ParagraphStyle(name='Section_Title', parent=styles['Normal_Left'], 
          fontName=bold_font, fontSize=13, textColor=color_primary, spaceBefore=10, 
          spaceAfter=5, borderBottomWidth=1, borderBottomColor=color_border))

# Table styles
styles.add(ParagraphStyle(name='Table_Header', parent=styles['Normal_Center'], 
          fontName=bold_font, fontSize=9, textColor='white'))
styles.add(ParagraphStyle(name='Table_Cell', parent=styles['Normal_Left'], 
          fontName=base_font, fontSize=9))
styles.add(ParagraphStyle(name='Table_Cell_Right', parent=styles['Table_Cell'], 
          alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='Table_Cell_Center', parent=styles['Table_Cell'], 
          alignment=TA_CENTER))

def generate_visit_pdf(visit_data, patient_data, services, prescriptions, suggested_filename="visit_report.pdf"):
    # File dialog setup
    options = QFileDialog.Option.DontUseNativeDialog
    file_path, _ = QFileDialog.getSaveFileName(
        None, "Save Visit Report PDF", suggested_filename,
        "PDF Files (*.pdf);;All Files (*)", options=options
    )
    
    if not file_path:
        return None
        
    if not file_path.lower().endswith(".pdf"):
        file_path += ".pdf"

    # Check template
    template_path = "pdf_template/template.pdf"
    if not os.path.exists(template_path):
        QMessageBox.critical(None, "Template Missing", 
                           f"PDF template not found at '{template_path}'")
        return None

    # Helper function
    def get_data(data_dict, key, default=''):
        return data_dict.get(key, default) or default

    # Create content buffer
    content_buffer = BytesIO()
    
    # Document setup
    doc = SimpleDocTemplate(
        content_buffer,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=73*mm,
        bottomMargin=30*mm
    )
    
    story = []
    
    # --- First Page Content ---
    # Visit Info (Right-aligned)
    visit_number = get_data(visit_data, 'visit_id', 'N/A')
    visit_date = get_data(visit_data, 'visit_date', '')
    try:
        visit_date = datetime.strptime(visit_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        pass
    
    visit_info = Table([
        [Paragraph(f"<b>Visit No:</b> #{visit_number}", styles['Visit_Header'])],
        [Paragraph(f"<b>Date:</b> {visit_date}", styles['Visit_Header'])]
    ], colWidths=[doc.width*0.3], hAlign='RIGHT')
    
    story.append(visit_info)
    story.append(Spacer(1, 8*mm))

    # Patient Details
    patient_name = get_data(patient_data, 'name', 'N/A')
    patient_sex = get_data(patient_data, 'sex', '')
    patient_father = get_data(patient_data, 'father_name', '')
    patient_phone = get_data(patient_data, 'phone_number', '')
    patient_address = get_data(patient_data, 'address', '')
    
    patient_content = [
        Paragraph("Patient Details", styles['BillTo_Header']),
        Table([
            [Paragraph(f"<b>Name:</b> {patient_name}", styles['Normal_Left']),
             Paragraph(f"<b>Sex:</b> {patient_sex}", styles['Normal_Left'])],
            [Paragraph(f"<b>Father/Husband:</b> {patient_father}", styles['Normal_Left']),
             Paragraph(f"<b>Phone:</b> {patient_phone}", styles['Normal_Left'])],
            [Paragraph(f"<b>Address:</b> {patient_address}", styles['Normal_Left']), ""]
        ], colWidths=[doc.width*0.5, doc.width*0.5], style=[
            ('SPAN', (0,2), (1,2)),
            ('VALIGN', (0,0), (-1,-1), 'TOP')
        ])
    ]
    story.extend(patient_content)
    story.append(Spacer(1, 10*mm))

    # --- Services Table ---
    if services:
        story.append(Paragraph("Services Performed", styles['Section_Title']))
        
        service_headers = [
            Paragraph('Service', styles['Table_Header']),
            Paragraph('Tooth', styles['Table_Header']),
            Paragraph('Details', styles['Table_Header']),
            Paragraph('Price (Rs.)', styles['Table_Header'])
        ]
        
        service_rows = [service_headers]
        total_services = 0.0
        for service in services:
            price = float(get_data(service, 'price_charged', 0))
            total_services += price
            tooth = get_data(service, 'tooth_number', '')
            service_rows.append([
                Paragraph(get_data(service, 'service_name', ''), styles['Table_Cell']),
                Paragraph(str(tooth), styles['Table_Cell_Center']),
                Paragraph(get_data(service, 'notes', ''), styles['Table_Cell']),
                Paragraph(f"{price:.2f}", styles['Table_Cell_Right'])
            ])
        
        service_table = Table(service_rows, 
                            colWidths=[doc.width*0.35, doc.width*0.15, doc.width*0.3, doc.width*0.2],
                            repeatRows=1)
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), color_header_bg),
            ('TEXTCOLOR', (0,0), (-1,0), 'white'),
            ('ALIGN', (3,0), (3,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, color_border),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [None, color_row_alt])
        ]))
        story.append(service_table)
        story.append(Spacer(1, 5*mm))

    # --- Prescriptions Table ---
    if prescriptions:
        story.append(Paragraph("Prescriptions Issued", styles['Section_Title']))
        
        presc_headers = [
            Paragraph('Medication', styles['Table_Header']),
            Paragraph('Qty', styles['Table_Header']),
            Paragraph('Instructions', styles['Table_Header']),
            Paragraph('Price (Rs.)', styles['Table_Header'])
        ]
        
        presc_rows = [presc_headers]
        total_prescriptions = 0.0
        for med in prescriptions:
            price = float(get_data(med, 'price_charged', 0))
            total_prescriptions += price
            presc_rows.append([
                Paragraph(get_data(med, 'medication_name', ''), styles['Table_Cell']),
                Paragraph(str(get_data(med, 'quantity', '')), styles['Table_Cell_Center']),
                Paragraph(get_data(med, 'instructions', ''), styles['Table_Cell']),
                Paragraph(f"{price:.2f}", styles['Table_Cell_Right'])
            ])
        
        presc_table = Table(presc_rows, 
                           colWidths=[doc.width*0.4, doc.width*0.1, doc.width*0.3, doc.width*0.2],
                           repeatRows=1)
        presc_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), color_header_bg),
            ('TEXTCOLOR', (0,0), (-1,0), 'white'),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
            ('ALIGN', (3,0), (3,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.5, color_border),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [None, color_row_alt])
        ]))
        story.append(presc_table)
        story.append(Spacer(1, 5*mm))

    # --- Visit Notes & Lab Results ---
    notes = get_data(visit_data, 'notes', '')
    lab_results = get_data(visit_data, 'lab_results', '')
    if notes or lab_results:
        notes_content = []
        if notes:
            notes_content.append(Paragraph(f"<b>Visit Notes:</b> {notes}", styles['Normal_Left']))
        if lab_results:
            notes_content.append(Paragraph(f"<b>Lab Results:</b> {lab_results}", styles['Normal_Left']))
        
        notes_table = Table([[note] for note in notes_content], colWidths=[doc.width])
        notes_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOX', (0,0), (-1,-1), 0.5, color_border),
            ('PADDING', (0,0), (-1,-1), 2*mm)
        ]))
        story.append(notes_table)
        story.append(Spacer(1, 5*mm))

    # --- Financial Summary ---
    total_cost = float(get_data(visit_data, 'total_amount', 0.0))
    paid_amount = float(get_data(visit_data, 'paid_amount', 0.0))
    due_amount = max(0.0, total_cost - paid_amount)
    subtotal = total_services + total_prescriptions if services or prescriptions else total_cost
    
    totals_data = [
        [Paragraph("Subtotal:", styles['Normal_Right']), Paragraph(f"Rs. {subtotal:.2f}", styles['Normal_Right'])],
        [Paragraph("Grand Total:", styles['Normal_Right']), Paragraph(f"Rs. {total_cost:.2f}", styles['Normal_Right'])],
        [Paragraph("Amount Paid:", styles['Normal_Right']), Paragraph(f"Rs. {paid_amount:.2f}", styles['Normal_Right'])],
        [Paragraph("Amount Due:", styles['Normal_Right']), Paragraph(f"Rs. {due_amount:.2f}", styles['Normal_Right'])],
    ]
    
    totals_table = Table(totals_data, colWidths=[doc.width*0.2, doc.width*0.2], hAlign='RIGHT')
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), base_font),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LINEABOVE', (0,1), (1,1), 1, color_secondary),
        ('BOTTOMPADDING', (0,1), (1,1), 2*mm)
    ]))
    story.append(totals_table)

    # Generate content PDF
    doc.build(story)

    # --- Merge with template using PyMuPDF ---
    try:
        template_doc = fitz.open(template_path)
        content_doc = fitz.open("pdf", content_buffer.getvalue())
        output_doc = fitz.open()
        
        for page_num in range(len(content_doc)):
            template_page = template_doc[page_num % len(template_doc)]
            output_page = output_doc.new_page(width=A4[0], height=A4[1])
            
            # Add template background
            output_page.show_pdf_page(output_page.rect, template_doc, page_num % len(template_doc))
            
            # Add content layer
            output_page.show_pdf_page(output_page.rect, content_doc, page_num)
        
        output_doc.save(file_path)
        return file_path
        
    except Exception as e:
        QMessageBox.critical(None, "PDF Error", f"Error generating PDF: {str(e)}")
        return None