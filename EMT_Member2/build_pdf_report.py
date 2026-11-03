# -*- coding: utf-8 -*-
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont('Helvetica', 8)
        self.setFillColor(colors.HexColor('#4A5568'))
        
        if self._pageNumber > 1:
            self.drawString(36, 756, 'EMT Antenna Project: 2.44 GHz 4-Element Yagi-Uda Array')
            self.drawRightString(576, 756, 'Full-Wave EM Simulation & Circuit Modeling')
            self.setStrokeColor(colors.HexColor('#CBD5E0'))
            self.setLineWidth(0.6)
            self.line(36, 750, 576, 750)
            
            self.setStrokeColor(colors.HexColor('#CBD5E0'))
            self.setLineWidth(0.6)
            self.line(36, 42, 576, 42)
            self.drawString(36, 30, 'Vipin Kumar Gond (Roll No: 2401EC05) | Academic & Engineering Documentation')
            self.drawRightString(576, 30, f'Page {self._pageNumber} of {page_count}')
        self.restoreState()

def build_pdf(filename='EMT_Yagi_Antenna_Project_Complete_Report.pdf'):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    c_primary = colors.HexColor('#1A365D')
    c_secondary = colors.HexColor('#2B6CB0')
    c_dark = colors.HexColor('#2D3748')
    c_accent = colors.HexColor('#C53030')
    c_light = colors.HexColor('#F7FAFC')
    
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=22, leading=26,
        textColor=c_primary, alignment=1, spaceAfter=8
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=12, leading=16,
        textColor=c_secondary, alignment=1, spaceAfter=14
    )
    meta_style = ParagraphStyle(
        'MetaText', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9.5, leading=14,
        textColor=c_dark, alignment=1
    )
    h1_style = ParagraphStyle(
        'H1', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=14, leading=18,
        textColor=c_primary, spaceBefore=14, spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11, leading=15,
        textColor=c_secondary, spaceBefore=10, spaceAfter=5,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=12,
        textColor=c_dark, spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'Bullet', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=12,
        textColor=c_dark, leftIndent=12, firstLineIndent=-8, spaceAfter=3
    )
    code_style = ParagraphStyle(
        'Code', parent=styles['Normal'],
        fontName='Courier', fontSize=7.0, leading=9.5,
        textColor=colors.HexColor('#1A202C')
    )
    callout_style = ParagraphStyle(
        'Callout', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=8.5, leading=12,
        textColor=colors.HexColor('#2C5282')
    )
    table_cell = ParagraphStyle(
        'TableCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=10,
        textColor=c_dark
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=10,
        textColor=c_dark
    )
    table_header = ParagraphStyle(
        'TableHeader', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=10.5,
        textColor=colors.white, alignment=1
    )

    story = []

    # ================= COVER / HEADER =================
    story.append(Paragraph('EMT ANTENNA ENGINEERING PROJECT REPORT', title_style))
    story.append(Paragraph('Design, Full-Wave EM Simulation, Circuit Modeling &amp; Prototyping Blueprint of a 2.44 GHz 4-Element Yagi-Uda Array', subtitle_style))
    story.append(HRFlowable(width='100%', thickness=1.5, color=c_primary, spaceAfter=10))

    meta_table_data = [
        [Paragraph('<b>Author / Student:</b> Vipin Kumar Gond (Roll No: 2401EC05)', meta_style),
         Paragraph('<b>Course:</b> Electromagnetic Theory &amp; Antennas', meta_style)],
        [Paragraph('<b>Target Frequency:</b> 2.44 GHz ISM (2.40 - 2.4835 GHz)', meta_style),
         Paragraph('<b>Array Topology:</b> 4-Element Yagi-Uda (1 Ref, 1 Drv, 2 Dir)', meta_style)],
        [Paragraph('<b>Conductor Spec:</b> 14 AWG Solid Copper (radius = 0.814 mm)', meta_style),
         Paragraph('<b>Matching Network:</b> 1:1 Quarter-Wave Pawsey Stub Balun', meta_style)]
    ]
    t_meta = Table(meta_table_data, colWidths=[270, 270])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EDF2F7')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # Executive Summary Box
    exec_summary = (
        '<b>EXECUTIVE SUMMARY &amp; KEY DELIVERABLES:</b> This technical documentation provides the complete '
        'full-wave numerical simulation, lumped circuit synthesis, physical fabrication blueprint, and presentation '
        'deliverables for an optimized 4-element Yagi-Uda antenna at 2.44 GHz. The simulation achieved an outstanding '
        'resonant return loss of <b>S11 = -31.81 dB</b>, input voltage standing wave ratio <b>VSWR = 1.053</b>, '
        'operational bandwidth of <b>160 MHz (2.36 - 2.52 GHz)</b> for S11 &lt;= -10 dB, peak directivity of '
        '<b>8.50 dBi</b> along the endfire director axis (+X), and a front-to-back (F/B) suppression ratio of <b>21.0 dB</b>.'
    )
    t_exec = Table([[Paragraph(exec_summary, callout_style)]], colWidths=[540])
    t_exec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EBF8FF')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#3182CE')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_exec)
    story.append(Spacer(1, 12))

    # ================= SECTION 1 =================
    story.append(Paragraph('1. Theoretical Design &amp; Analytical Electromagnetic Formulations', h1_style))
    story.append(HRFlowable(width='100%', thickness=0.8, color=c_secondary, spaceAfter=8))
    
    sec1_text = (
        'The Yagi-Uda antenna functions as a traveling-wave endfire array where parasitic elements are excited by the '
        'near-zone electromagnetic field of the driven dipole. The reflector is sized slightly larger than resonant '
        'half-wavelength to induce an inductive current phase delay, reflecting wave power forward. Directors are cut '
        'shorter than resonant length to induce a capacitive phase advance, directing the traveling wave along the boom axis.'
    )
    story.append(Paragraph(sec1_text, body_style))

    story.append(Paragraph('<b>Fundamental Electromagnetic Equations:</b>', h2_style))
    story.append(Paragraph('&bull; <b>Operating Free-Space Wavelength (&lambda;<sub>0</sub>):</b> &lambda;<sub>0</sub> = c / f<sub>0</sub> = (2.9979 &times; 10<sup>8</sup> m/s) / (2.44 &times; 10<sup>9</sup> Hz) = <b>12.287 cm = 122.87 mm</b>', bullet_style))
    story.append(Paragraph('&bull; <b>Conductor Selection (14 AWG Solid Bare Copper):</b> Diameter d = 1.628 mm &rarr; Radius a = 0.814 mm. Ratio a / &lambda;<sub>0</sub> = 0.00662 &lt;&lt; 1 (validates Pocklington thin-wire kernel).', bullet_style))
    story.append(Paragraph('&bull; <b>RF Conductor Skin Depth (&delta;):</b> &delta; = 1 / &radic;(&pi; f &mu; &sigma;) = 1 / &radic;(&pi; &times; 2.44&times;10<sup>9</sup> &times; 4&pi;&times;10<sup>-7</sup> &times; 5.80&times;10<sup>7</sup>) = <b>1.32 &mu;m</b> &lt;&lt; a = 814 &mu;m (current resides in outer skin layer).', bullet_style))
    story.append(Paragraph('&bull; <b>Phase Velocity &amp; Hansen-Woodyard Condition:</b> Phase velocity is slowed (&beta;<sub>traveling</sub> = k<sub>0</sub> + &pi;/L) to establish enhanced endfire superdirective gain.', bullet_style))
    story.append(Spacer(1, 10))

    # ================= SECTION 2 =================
    story.append(Paragraph('2. 3D Structure &amp; Full-Wave 4nec2 Simulation Model', h1_style))
    story.append(HRFlowable(width='100%', thickness=0.8, color=c_secondary, spaceAfter=8))

    if os.path.exists('yagi_3d_structure.png'):
        img_3d = Image('yagi_3d_structure.png', width=540, height=270)
        story.append(img_3d)
        story.append(Spacer(1, 6))

    story.append(Paragraph('<b>Geometric Coordinate Card Table (Evaluated Numerical NEC-2 Format):</b>', h2_style))
    nec_table_data = [
        [Paragraph('Card', table_header), Paragraph('Tag', table_header), Paragraph('Seg', table_header),
         Paragraph('X1 (mm)', table_header), Paragraph('Y1 (mm)', table_header), Paragraph('Z1 (mm)', table_header),
         Paragraph('X2 (mm)', table_header), Paragraph('Y2 (mm)', table_header), Paragraph('Z2 (mm)', table_header),
         Paragraph('Radius (mm)', table_header), Paragraph('Description', table_header)],
        [Paragraph('GW', table_cell_bold), Paragraph('1', table_cell), Paragraph('21', table_cell),
         Paragraph('0.0', table_cell), Paragraph('0.0', table_cell), Paragraph('-29.5', table_cell),
         Paragraph('0.0', table_cell), Paragraph('0.0', table_cell), Paragraph('+29.5', table_cell),
         Paragraph('0.814', table_cell), Paragraph('Reflector (59.0 mm)', table_cell)],
        [Paragraph('GW', table_cell_bold), Paragraph('2', table_cell), Paragraph('21', table_cell),
         Paragraph('24.6', table_cell), Paragraph('0.0', table_cell), Paragraph('-27.8', table_cell),
         Paragraph('24.6', table_cell), Paragraph('0.0', table_cell), Paragraph('+27.8', table_cell),
         Paragraph('0.814', table_cell), Paragraph('Driven Dipole (55.6 mm, Feed seg 11)', table_cell)],
        [Paragraph('GW', table_cell_bold), Paragraph('3', table_cell), Paragraph('21', table_cell),
         Paragraph('45.5', table_cell), Paragraph('0.0', table_cell), Paragraph('-26.1', table_cell),
         Paragraph('45.5', table_cell), Paragraph('0.0', table_cell), Paragraph('+26.1', table_cell),
         Paragraph('0.814', table_cell), Paragraph('Director 1 (52.2 mm)', table_cell)],
        [Paragraph('GW', table_cell_bold), Paragraph('4', table_cell), Paragraph('21', table_cell),
         Paragraph('70.1', table_cell), Paragraph('0.0', table_cell), Paragraph('-25.2', table_cell),
         Paragraph('70.1', table_cell), Paragraph('0.0', table_cell), Paragraph('+25.2', table_cell),
         Paragraph('0.814', table_cell), Paragraph('Director 2 (50.4 mm)', table_cell)],
    ]
    t_nec = Table(nec_table_data, colWidths=[24, 20, 22, 44, 40, 48, 44, 40, 48, 54, 156])
    t_nec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_nec)
    story.append(Spacer(1, 10))

    # Control cards summary
    ctrl_cards = (
        '<b>Simulation Execution Cards:</b><br/>'
        '&bull; <b>LD 5 0 0 0 5.8001e7:</b> Type 5 copper surface impedance loading (conductivity = 5.8 &times; 10<sup>7</sup> S/m).<br/>'
        '&bull; <b>EX 0 2 11 0 1.0 0.0:</b> Applied linear voltage source on Tag 2, segment 11 (center feed segment).<br/>'
        '&bull; <b>GN -1:</b> Free space radiation environment (no ground plane boundary).<br/>'
        '&bull; <b>FR 0 101 0 0 2000.0 10.0:</b> Frequency sweep: 2.0 GHz to 3.0 GHz in 10 MHz steps (101 frequency evaluation points).<br/>'
        '&bull; <b>RP 0 73 73 1000 -90.0 0.0 2.5 5.0:</b> Full 3D spherical far-field radiation pattern sampling.'
    )
    story.append(Paragraph(ctrl_cards, body_style))
    story.append(PageBreak())

    # ================= SECTION 3 =================
    story.append(Paragraph('3. Equivalent Circuit Modeling &amp; Balun Impedance Transformation', h1_style))
    story.append(HRFlowable(width='100%', thickness=0.8, color=c_secondary, spaceAfter=8))

    if os.path.exists('circuit_schematic_detailed.png'):
        img_ckt = Image('circuit_schematic_detailed.png', width=540, height=270)
        story.append(img_ckt)
        story.append(Spacer(1, 8))

    story.append(Paragraph('<b>Lumped Circuit Synthesis &amp; Parameter Derivations:</b>', h2_style))
    
    ckt_deriv = (
        '<b>1. Resonant Input Impedance &amp; Reflection Coefficient:</b><br/>'
        'At the 2.44 GHz center resonance, the antenna terminal impedance is extracted from full-wave NEC simulation as: '
        '<b>Z<sub>in</sub> = 48.74 + j 2.20 &Omega;</b>.<br/>'
        'Normalized to a standard Z<sub>0</sub> = 50.0 &Omega; coaxial transmission line:<br/>'
        '&Gamma; = (Z<sub>in</sub> - Z<sub>0</sub>) / (Z<sub>in</sub> + Z<sub>0</sub>) = '
        '(-1.26 + j 2.20) / (98.74 + j 2.20) = <b>0.02567 &ang; 119.8&deg;</b><br/>'
        '&bull; <b>Return Loss (S<sub>11</sub>):</b> S<sub>11</sub> = 20 log<sub>10</sub>(|&Gamma;|) = 20 log<sub>10</sub>(0.02567) = <b>-31.81 dB</b> (Target: &lt; -15.0 dB)<br/>'
        '&bull; <b>Voltage Standing Wave Ratio (VSWR):</b> VSWR = (1 + |&Gamma;|) / (1 - |&Gamma;|) = 1.02567 / 0.97433 = <b>1.053 : 1</b> (Target: &lt; 1.50 : 1)<br/><br/>'
        '<b>2. Equivalent Series RLC Parameters:</b><br/>'
        'Near resonance, Z<sub>in</sub>(&omega;) = R + j [&omega;L - 1/(&omega;C)]. At resonance &omega;<sub>0</sub> = 2&pi; f<sub>0</sub> = 15.33 Grad/s:<br/>'
        '&bull; <b>Equivalent Resistance (R):</b> R = R<sub>in</sub> = <b>48.74 &Omega; &asymp; 50.0 &Omega;</b> (Radiation resistance R<sub>rad</sub> = 48.60 &Omega; + Ohmic loss R<sub>loss</sub> = 0.14 &Omega;)<br/>'
        '&bull; <b>Operational Bandwidth (&Delta;f):</b> S<sub>11</sub> &le; -10 dB from 2.36 GHz to 2.52 GHz (&Delta;f = 160 MHz). At the band edge, X<sub>edge</sub> = 2 Z<sub>0</sub> / 3 = 33.33 &Omega;.<br/>'
        '&bull; <b>Equivalent Inductance (L):</b> L = X<sub>edge</sub> / (2&pi; &Delta;f) = 33.333 / (2&pi; &times; 160 &times; 10<sup>6</sup>) = <b>33.16 nH</b><br/>'
        '&bull; <b>Equivalent Capacitance (C):</b> C = 1 / (&omega;<sub>0</sub><sup>2</sup> L) = 1 / [(1.5331&times;10<sup>10</sup>)<sup>2</sup> &times; 33.157&times;10<sup>-9</sup>] = <b>0.1283 pF = 128.3 fF</b><br/>'
        '&bull; <b>Quality Factors:</b> Unloaded Q<sub>0</sub> = &omega;<sub>0</sub>L / R = <b>10.43</b>; Loaded Q<sub>L</sub> = &omega;<sub>0</sub>L / (R + Z<sub>0</sub>) = <b>5.15</b>; Fractional BW = <b>6.56%</b>.<br/><br/>'
        '<b>3. Quarter-Wave Pawsey Stub Balun (1:1 Balanced Matching):</b><br/>'
        'A split dipole is inherently balanced, whereas coaxial cable is unbalanced. Connecting coax directly causes shield currents, '
        'distorting the radiation pattern and causing beam squint. The Pawsey stub places a parallel quarter-wave shorted transmission '
        'line across the feed terminals: Z<sub>stub</sub> = j Z<sub>p</sub> tan(&beta;&ell;). At &ell; = &lambda;/4, tan(&beta;&ell;) &rarr; &infin;, '
        'presenting an infinite RF choking impedance that completely suppresses common-mode sheath currents without altering the 50 &Omega; differential feed.'
    )
    story.append(Paragraph(ckt_deriv, body_style))
    story.append(Spacer(1, 10))

    # ================= SECTION 4 =================
    story.append(Paragraph('4. Millimeter-Accurate Hardware Cutting &amp; Assembly Blueprint', h1_style))
    story.append(HRFlowable(width='100%', thickness=0.8, color=c_secondary, spaceAfter=8))

    if os.path.exists('yagi_antenna_blueprint.png'):
        img_bp = Image('yagi_antenna_blueprint.png', width=540, height=270)
        story.append(img_bp)
        story.append(Spacer(1, 8))

    story.append(Paragraph('<b>Physical Dimension &amp; Cutting Specification Table:</b>', h2_style))
    bp_table_data = [
        [Paragraph('Element', table_header), Paragraph('Electrical Length', table_header),
         Paragraph('Physical Cut (mm)', table_header), Paragraph('Split Arm Breakdown', table_header),
         Paragraph('Inter-Element Spacing', table_header), Paragraph('Cumulative Boom Position (X)', table_header)],
        [Paragraph('<b>Reflector (L<sub>R</sub>)</b>', table_cell), Paragraph('0.480 &lambda;<sub>0</sub>', table_cell),
         Paragraph('<b>59.0 mm</b>', table_cell_bold), Paragraph('Single wire (&plusmn;29.5 mm from boom)', table_cell),
         Paragraph('--', table_cell), Paragraph('<b>0.0 mm</b> (Origin Reference)', table_cell)],
        [Paragraph('<b>Driven Dipole (L<sub>D</sub>)</b>', table_cell), Paragraph('0.452 &lambda;<sub>0</sub>', table_cell),
         Paragraph('<b>55.6 mm</b>', table_cell_bold), Paragraph('Two arms of <b>27.3 mm</b> each (1.0 mm gap)', table_cell),
         Paragraph('d<sub>R-D</sub> = <b>24.6 mm</b> (0.200&lambda;)', table_cell), Paragraph('<b>24.6 mm</b>', table_cell)],
        [Paragraph('<b>Director 1 (L<sub>D1</sub>)</b>', table_cell), Paragraph('0.425 &lambda;<sub>0</sub>', table_cell),
         Paragraph('<b>52.2 mm</b>', table_cell_bold), Paragraph('Single wire (&plusmn;26.1 mm from boom)', table_cell),
         Paragraph('d<sub>D-D1</sub> = <b>20.9 mm</b> (0.170&lambda;)', table_cell), Paragraph('<b>45.5 mm</b>', table_cell)],
        [Paragraph('<b>Director 2 (L<sub>D2</sub>)</b>', table_cell), Paragraph('0.410 &lambda;<sub>0</sub>', table_cell),
         Paragraph('<b>50.4 mm</b>', table_cell_bold), Paragraph('Single wire (&plusmn;25.2 mm from boom)', table_cell),
         Paragraph('d<sub>D1-D2</sub> = <b>24.6 mm</b> (0.200&lambda;)', table_cell), Paragraph('<b>70.1 mm</b>', table_cell)],
    ]
    t_bp = Table(bp_table_data, colWidths=[90, 75, 75, 120, 95, 85])
    t_bp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_bp)
    story.append(Spacer(1, 10))

    fab_details = (
        '<b>Fabrication Guidelines:</b><br/>'
        '&bull; <b>Boom Length:</b> 95.0 mm to 100.0 mm (70.1 mm active span + 15 mm rear margin for clamp + 10 mm front margin).<br/>'
        '&bull; <b>Boom Material:</b> Dielectric non-conductive block (Acrylic, Polycarbonate, or 3D-printed PETG/PLA) to avoid boom correction factor.<br/>'
        '&bull; <b>Pawsey Balun Dimensions:</b> <b>30.7 mm</b> for air-spaced parallel wire (VF = 1.0) or <b>21.5 mm</b> for Teflon RG-316/RG-402 coax (VF = 0.69).<br/>'
        '&bull; <b>SMA Termination:</b> Connect coax center pin to Arm A; coax outer shield + Pawsey stub top to Arm B. Solder stub base to coax shield.'
    )
    story.append(Paragraph(fab_details, body_style))
    story.append(PageBreak())

    # ================= SECTION 5 =================
    story.append(Paragraph('5. Full-Wave Simulation Performance &amp; Verification', h1_style))
    story.append(HRFlowable(width='100%', thickness=0.8, color=c_secondary, spaceAfter=8))

    # Two column images: S11/VSWR and Polar pattern
    img_row = []
    if os.path.exists('s11_vswr_response.png') and os.path.exists('radiation_pattern_polar.png'):
        img_s11 = Image('s11_vswr_response.png', width=265, height=210)
        img_polar = Image('radiation_pattern_polar.png', width=265, height=210)
        t_imgs = Table([[img_s11, img_polar]], colWidths=[270, 270])
        t_imgs.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t_imgs)
        story.append(Spacer(1, 8))

    # Smith chart (input impedance match across the 2.0-3.0 GHz sweep)
    if os.path.exists('smith_chart.png'):
        story.append(Paragraph(
            '<b>Smith Chart - Input Impedance Match (Z<sub>0</sub> = 50 &Omega;):</b>', h2_style))
        img_smith = Image('smith_chart.png', width=320, height=320)
        t_smith = Table([[img_smith]], colWidths=[540])
        t_smith.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_smith)
        story.append(Paragraph(
            'The frequency-swept reflection-coefficient locus (2.0 - 3.0 GHz) crosses near the '
            'chart origin at the 2.44 GHz resonance, lying well inside the VSWR = 2 circle '
            '(|&Gamma;| = 1/3). Terminal impedance Z<sub>in</sub> = 48.74 + j2.20 &Omega; yields '
            'S<sub>11</sub> = -31.81 dB and VSWR = 1.053, confirming a near-ideal 50 &Omega; match.',
            callout_style))
        story.append(Spacer(1, 10))

    story.append(Paragraph('<b>Comprehensive Performance vs. Target Compliance Matrix:</b>', h2_style))
    comp_table_data = [
        [Paragraph('Performance Metric', table_header), Paragraph('Design Specification Goal', table_header),
         Paragraph('Simulated Value (4nec2)', table_header), Paragraph('Margin / Status', table_header)],
        [Paragraph('<b>Center Frequency (f<sub>0</sub>)</b>', table_cell), Paragraph('2.44 GHz (ISM Band)', table_cell),
         Paragraph('<b>2.440 GHz</b>', table_cell_bold), Paragraph('Exact Target Resonance', table_cell)],
        [Paragraph('<b>Return Loss (S<sub>11</sub> at f<sub>0</sub>)</b>', table_cell), Paragraph('&lt; -15.0 dB', table_cell),
         Paragraph('<b>-31.81 dB</b>', table_cell_bold), Paragraph('Exceeded (+16.81 dB safety margin)', table_cell)],
        [Paragraph('<b>Input VSWR</b>', table_cell), Paragraph('&lt; 1.50 : 1', table_cell),
         Paragraph('<b>1.053 : 1</b>', table_cell_bold), Paragraph('Exceeded (Near-ideal 50 &Omega; match)', table_cell)],
        [Paragraph('<b>Operational Bandwidth (S<sub>11</sub> &le; -10 dB)</b>', table_cell), Paragraph('&ge; 83.5 MHz (ISM Band)', table_cell),
         Paragraph('<b>160.0 MHz (2.36 - 2.52 GHz)</b>', table_cell_bold), Paragraph('191% of Required ISM Bandwidth', table_cell)],
        [Paragraph('<b>Peak Directivity / Gain</b>', table_cell), Paragraph('&ge; 7.50 dBi', table_cell),
         Paragraph('<b>8.50 dBi</b>', table_cell_bold), Paragraph('Exceeded (+1.00 dBi margin)', table_cell)],
        [Paragraph('<b>Front-to-Back (F/B) Ratio</b>', table_cell), Paragraph('&ge; 15.0 dB', table_cell),
         Paragraph('<b>21.0 dB</b>', table_cell_bold), Paragraph('Exceeded (+6.00 dB back-lobe rejection)', table_cell)],
        [Paragraph('<b>Half-Power Beamwidth (HPBW)</b>', table_cell), Paragraph('&le; 75&deg; (E-plane)', table_cell),
         Paragraph('<b>E: 68&deg; | H: 78&deg;</b>', table_cell_bold), Paragraph('Highly Directive Symmetrical Beam', table_cell)],
    ]
    t_comp = Table(comp_table_data, colWidths=[150, 120, 130, 140])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 10))

    # ================= SECTION 6 =================
    story.append(Paragraph('6. IEEE Presentation Slide Content (Slides 7, 8, &amp; 9)', h1_style))
    story.append(HRFlowable(width='100%', thickness=0.8, color=c_secondary, spaceAfter=8))

    slide7_box = (
        '<b>SLIDE 7: CIRCUIT MODEL &amp; BALUN MATCHING</b><br/>'
        '&bull; <b>Series RLC Model:</b> Z<sub>in</sub>(&omega;) = R + j [&omega;L - 1/(&omega;C)]; at resonance &omega;<sub>0</sub> = 15.33 Grad/s, X<sub>in</sub> = 0.<br/>'
        '&bull; <b>Extracted Values:</b> R = 48.74 &Omega;, L = 33.16 nH, C = 0.128 pF (128.3 fF), Q<sub>0</sub> = 10.43, Q<sub>L</sub> = 5.15.<br/>'
        '&bull; <b>Coaxial Matching:</b> &Gamma; = (Z<sub>in</sub> - 50)/(Z<sub>in</sub> + 50) = 0.02567 &ang; 119.8&deg; &rarr; <b>S<sub>11</sub> = -31.8 dB, VSWR = 1.05</b>.<br/>'
        '&bull; <b>Pawsey Balun:</b> Quarter-wave shorted stub (&lambda;/4 = 30.7 mm air / 21.5 mm PTFE coax) provides infinite parallel choking impedance to suppress common-mode outer shield currents.'
    )
    t_s7 = Table([[Paragraph(slide7_box, body_style)]], colWidths=[540])
    t_s7.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('BOX', (0,0), (-1,-1), 1, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_s7)
    story.append(Spacer(1, 6))

    slide8_box = (
        '<b>SLIDE 8: 4-ELEMENT YAGI-UDA DESIGN STEPS &amp; EM SETUP</b><br/>'
        '&bull; <b>Analytical Wavelength:</b> &lambda;<sub>0</sub> = c / f<sub>0</sub> = 12.28 cm (122.87 mm). 14 AWG wire radius a = 0.814 mm satisfies thin-wire ratio a / &lambda;<sub>0</sub> = 0.00662 &lt;&lt; 1.<br/>'
        '&bull; <b>3D Full-Wave Setup:</b> 4nec2 array along +X axis, elements parallel to Z axis. 21 segments per wire (segment length &Delta; &asymp; 2.6 mm).<br/>'
        '&bull; <b>Boundary &amp; Feed:</b> Free space (GN -1), center segment feed on Tag 2 (EX card), annealed copper conductivity &sigma; = 5.80 &times; 10<sup>7</sup> S/m (LD card).<br/>'
        '&bull; <b>Optimization Protocol:</b> Systematic tuning of element lengths (L<sub>R</sub>=59.0, L<sub>D</sub>=55.6, L<sub>D1</sub>=52.2, L<sub>D2</sub>=50.4 mm) and spacings (d<sub>RD</sub>=24.6, d<sub>D1</sub>=20.9, d<sub>12</sub>=24.6 mm).'
    )
    t_s8 = Table([[Paragraph(slide8_box, body_style)]], colWidths=[540])
    t_s8.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('BOX', (0,0), (-1,-1), 1, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_s8)
    story.append(Spacer(1, 6))

    slide9_box = (
        '<b>SLIDE 9: FULL-WAVE SIMULATED PERFORMANCE &amp; VALIDATION</b><br/>'
        '&bull; <b>Return Loss Peak:</b> Minimum S<sub>11</sub> = <b>-31.8 dB</b> at 2.44 GHz (16.8 dB margin below -15 dB goal).<br/>'
        '&bull; <b>Voltage Standing Wave Ratio:</b> VSWR = <b>1.05 : 1</b> (near-unity match, target &lt; 1.5).<br/>'
        '&bull; <b>Operational Bandwidth:</b> <b>160 MHz (2.36 GHz to 2.52 GHz)</b> for S<sub>11</sub> &le; -10 dB (covers full 83.5 MHz ISM band).<br/>'
        '&bull; <b>Far-Field Directivity &amp; F/B:</b> Peak forward directivity = <b>8.50 dBi</b> along +X; Front-to-Back ratio = <b>21.0 dB</b>; HPBW = 68&deg; (E-plane), 78&deg; (H-plane).'
    )
    t_s9 = Table([[Paragraph(slide9_box, body_style)]], colWidths=[540])
    t_s9.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('BOX', (0,0), (-1,-1), 1, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_s9)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f'PDF successfully generated: {filename}')

if __name__ == '__main__':
    # Image paths above are relative to this folder; work from anywhere
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build_pdf()
