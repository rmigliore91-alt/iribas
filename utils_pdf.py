from fpdf import FPDF
import pandas as pd
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 18)
        self.set_text_color(161, 28, 50) # Crimson Red Iribas
        self.cell(0, 10, "Instituto Iribas - Informe Gerencial", align="C")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Generado por Analítica Médica el {datetime.now().strftime('%d/%m/%Y')} - Pag. {self.page_no()}/{{nb}}", align="C")

def crear_tabla(pdf, df_head, title):
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(38, 76, 141) # Dark Blue Iribas
    pdf.cell(0, 10, title, ln=True)
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    
    if len(df_head.columns) == 0:
        return
    col_width = pdf.epw / len(df_head.columns)
    
    # Header
    pdf.set_font("helvetica", "B", 10)
    for col in df_head.columns:
        pdf.cell(col_width, 10, str(col), border=1, align="C")
    pdf.ln()
    
    # Data
    pdf.set_font("helvetica", "", 9)
    for i, row in df_head.iterrows():
        for item in row:
            val = str(item)
            if isinstance(item, (int, float)):
                if item > 1000:
                    val = f"{item:,.0f}" 
            pdf.cell(col_width, 8, val[:35], border=1, align="C")
        pdf.ln()
    pdf.ln(5)

def generar_informe_pdf(df, min_d, max_d):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Periodo Analizado
    pdf.set_font("helvetica", "", 11)
    fecha_txt = f"Período de Análisis: {min_d} al {max_d}" if min_d and max_d else "Período de Análisis: Histórico General (Todos los datos cargados)"
    pdf.cell(0, 10, fecha_txt, ln=True)
    pdf.ln(5)
    
    # 1. Dashboard Global (Financiero)
    volumen = len(df)
    ingresos = df["TOTAL"].sum() if "TOTAL" in df.columns else 0
    ticket = ingresos / volumen if volumen > 0 else 0
    
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Resumen General de Operaciones", ln=True)
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, f"Total de Estudios Realizados: {volumen:,}", ln=True)
    pdf.cell(0, 8, f"Facturacion Total (GN): {ingresos:,.0f}", ln=True)
    pdf.cell(0, 8, f"Ticket Promedio (GN): {ticket:,.0f}", ln=True)
    pdf.ln(10)
    
    # 2. Sector
    if "Sector" in df.columns:
        df_sec = df.groupby("Sector").agg(Estudios=("Sector", "count"))
        if "TOTAL" in df.columns:
            df_sec["Facturacion"] = df.groupby("Sector")["TOTAL"].sum()
        df_sec = df_sec.reset_index().sort_values("Estudios", ascending=False).head(10)
        crear_tabla(pdf, df_sec, "Rendimiento por Sector Medico (Top 10)")
        
    # 3. Doctores
    if "Doctor Tratante" in df.columns:
        df_doc = df.groupby("Doctor Tratante").agg(Derivaciones=("Doctor Tratante", "count"))
        if "TOTAL" in df.columns:
            df_doc["Importe (GN)"] = df.groupby("Doctor Tratante")["TOTAL"].sum()
        df_doc = df_doc.reset_index().sort_values("Derivaciones", ascending=False).head(10)
        crear_tabla(pdf, df_doc, "Top 10 Doctores Derivantes")
        
    # 4. Radiologos
    if "Doctor Informante" in df.columns:
        df_rad = df.groupby("Doctor Informante").agg(Informes_Realizados=("Doctor Informante", "count")).reset_index().sort_values("Informes_Realizados", ascending=False).head(10)
        crear_tabla(pdf, df_rad, "Productividad de Radiologos Informantes (Top 10)")
        
    # 5. Seguros
    if "Seguro" in df.columns:
        df_seg = df.groupby("Seguro").agg(Volumen=("Seguro", "count"))
        if "TOTAL" in df.columns:
            df_seg["Facturacion"] = df.groupby("Seguro")["TOTAL"].sum()
        df_seg = df_seg.reset_index().sort_values("Volumen", ascending=False).head(10)
        crear_tabla(pdf, df_seg, "Ranking de Seguros Medicos (Top 10)")
        
    return bytes(pdf.output())
