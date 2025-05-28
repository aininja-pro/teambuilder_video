import os
import tempfile
from datetime import datetime
from typing import List, Dict
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import pdfkit
import streamlit as st

def generate_docx(scope_items: List[Dict[str, str]], job_name: str = "Job", version: int = 1) -> str:
    """
    Generate a DOCX document from scope items.
    
    Args:
        scope_items: List of scope items with 'code', 'title', and 'details' keys
        job_name: Name of the job for the document title
        version: Version number for the document
        
    Returns:
        str: Path to the generated DOCX file
        
    Raises:
        Exception: If document generation fails
    """
    try:
        # Create a new document
        doc = Document()
        
        # Add title
        title = doc.add_heading(f'{job_name} - Scope Summary', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add metadata
        date_str = datetime.now().strftime("%Y-%m-%d")
        doc.add_paragraph(f"Generated: {date_str}")
        doc.add_paragraph(f"Version: {version}")
        doc.add_paragraph("")  # Empty line
        
        # Group scope items by cost code
        grouped_items = {}
        for item in scope_items:
            code = item['code']
            if code not in grouped_items:
                grouped_items[code] = []
            grouped_items[code].append(item)
        
        # Sort by cost code
        sorted_codes = sorted(grouped_items.keys())
        
        # Add scope items by division
        for code in sorted_codes:
            items = grouped_items[code]
            
            # Add division header
            from parse_scope import COST_CODE_MAPPING
            division_name = COST_CODE_MAPPING.get(code, "Unknown Division")
            doc.add_heading(f"Division {code}: {division_name}", level=1)
            
            # Add items for this division
            for item in items:
                # Add item title as subheading
                doc.add_heading(item['title'], level=2)
                
                # Add item details
                doc.add_paragraph(item['details'])
                doc.add_paragraph("")  # Empty line between items
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_file_path = temp_file.name
        temp_file.close()
        
        # Save document
        doc.save(temp_file_path)
        
        return temp_file_path
        
    except Exception as e:
        raise Exception(f"DOCX generation failed: {str(e)}")

def generate_pdf(docx_path: str, job_name: str = "Job", version: int = 1) -> str:
    """
    Generate a PDF from a DOCX file or create a PDF directly from scope items.
    
    Args:
        docx_path: Path to the DOCX file to convert (or None to create from scope_items)
        job_name: Name of the job for the document title
        version: Version number for the document
        
    Returns:
        str: Path to the generated PDF file
        
    Raises:
        Exception: If PDF generation fails
    """
    try:
        # Create temporary file for PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file_path = temp_file.name
        temp_file.close()
        
        # Try to use pdfkit to convert DOCX to PDF
        # Note: This requires wkhtmltopdf to be installed
        try:
            # For now, we'll create a simple HTML version and convert to PDF
            # This is a fallback since direct DOCX to PDF conversion is complex
            html_content = create_html_from_docx_path(docx_path, job_name, version)
            
            # Configure pdfkit options
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            }
            
            # Generate PDF from HTML
            pdfkit.from_string(html_content, temp_file_path, options=options)
            
        except Exception as pdfkit_error:
            # If pdfkit fails, create a simple text-based PDF using reportlab as fallback
            st.warning("pdfkit failed, using fallback PDF generation")
            temp_file_path = create_simple_pdf_fallback(docx_path, job_name, version)
        
        return temp_file_path
        
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")

def create_html_from_docx_path(docx_path: str, job_name: str, version: int) -> str:
    """
    Create HTML content from a DOCX file for PDF conversion.
    
    Args:
        docx_path: Path to the DOCX file
        job_name: Name of the job
        version: Version number
        
    Returns:
        str: HTML content
    """
    try:
        # Read the DOCX file
        doc = Document(docx_path)
        
        # Start HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{job_name} - Scope Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
                h2 {{ color: #34495e; margin-top: 20px; }}
                h3 {{ color: #7f8c8d; }}
                p {{ margin: 10px 0; line-height: 1.6; }}
                .metadata {{ color: #7f8c8d; font-style: italic; }}
            </style>
        </head>
        <body>
        """
        
        # Extract content from DOCX
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                html_content += "<br>"
                continue
                
            # Determine heading level based on style
            if paragraph.style.name.startswith('Heading'):
                level = paragraph.style.name.split()[-1] if paragraph.style.name.split()[-1].isdigit() else "1"
                html_content += f"<h{level}>{text}</h{level}>"
            else:
                html_content += f"<p>{text}</p>"
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        # Fallback HTML if DOCX reading fails
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{job_name} - Scope Summary</title>
        </head>
        <body>
            <h1>{job_name} - Scope Summary</h1>
            <p>Generated: {date_str}</p>
            <p>Version: {version}</p>
            <p>Error reading DOCX content: {str(e)}</p>
        </body>
        </html>
        """

def create_simple_pdf_fallback(docx_path: str, job_name: str, version: int) -> str:
    """
    Create a simple PDF using reportlab as fallback.
    
    Args:
        docx_path: Path to the DOCX file (for content extraction)
        job_name: Name of the job
        version: Version number
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        
        # Create temporary file for PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file_path = temp_file.name
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(temp_file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        title = Paragraph(f"{job_name} - Scope Summary", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add metadata
        date_str = datetime.now().strftime("%Y-%m-%d")
        story.append(Paragraph(f"Generated: {date_str}", styles['Normal']))
        story.append(Paragraph(f"Version: {version}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Try to extract content from DOCX
        try:
            docx_doc = Document(docx_path)
            for paragraph in docx_doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    if paragraph.style.name.startswith('Heading'):
                        story.append(Paragraph(text, styles['Heading1']))
                    else:
                        story.append(Paragraph(text, styles['Normal']))
                    story.append(Spacer(1, 6))
        except Exception:
            story.append(Paragraph("Error extracting content from DOCX file.", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return temp_file_path
        
    except ImportError:
        # If reportlab is not available, create a simple text file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w')
        temp_file.write(f"{job_name} - Scope Summary\n")
        temp_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n")
        temp_file.write(f"Version: {version}\n\n")
        temp_file.write("PDF generation libraries not available. This is a text fallback.\n")
        temp_file.close()
        return temp_file.name
    except Exception as e:
        raise Exception(f"Fallback PDF generation failed: {str(e)}")

def create_filename(job_name: str, version: int, extension: str) -> str:
    """
    Create a standardized filename for generated documents.
    
    Args:
        job_name: Name of the job
        version: Version number
        extension: File extension (e.g., 'docx', 'pdf')
        
    Returns:
        str: Formatted filename
    """
    date_str = datetime.now().strftime("%Y%m%d")
    safe_job_name = "".join(c for c in job_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_job_name = safe_job_name.replace(' ', '_')
    
    return f"{safe_job_name}_ScopeSummary_{date_str}_v{version}.{extension}" 