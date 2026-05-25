import streamlit as st
import cv2
import numpy as np
from fpdf import FPDF
from PIL import Image

# --- FUNZIONE PER GENERARE IL PDF ---
def crea_pdf(nome, intervento, mq, totale):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="VITERBO RESTAURI - PREVENTIVO UFFICIALE", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Cliente: {nome}", ln=True)
    pdf.cell(200, 10, txt=f"Tipo di Intervento: {intervento}", ln=True)
    pdf.cell(200, 10, txt=f"Superficie stimata: {mq} mq", ln=True)
    
    pdf.ln(10)
    pdf.set_draw_color(0, 0, 0)
    pdf.cell(200, 0, border='T', ln=True) 
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"TOTALE STIMATO: EUR {totale:,.2f}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- CONFIGURAZIONE WEBAPP ---
st.set_page_config(page_title="Viterbo Restauri Pro", layout="wide")

# Barra laterale
st.sidebar.title("🏗️ Viterbo Restauri")
st.sidebar.subheader("Dati Cliente")
nome_cliente = st.sidebar.text_input("Nome Cliente", "Cliente Esempio")
intervento = st.sidebar.selectbox("Intervento", ["Pittura Standard", "Pittura Antimuffa", "Gres Porcellanato"])

# Area Principale
st.title("Sistema Smart di Ristrutturazione")

file_caricato = st.file_uploader("Carica la Planimetria", type=['jpg', 'png', 'jpeg'])

if file_caricato and nome_cliente:
    # Lettura dell'immagine
    file_bytes = np.asarray(bytearray(file_caricato.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Planimetria Originale")
        st.image(img, channels="BGR", use_column_width=True)

    # Analisi Spazi (Trova contorni e colora)
    grigio = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(grigio, 225, 255, cv2.THRESH_BINARY_INV)
    contorni, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    img_colorata = img.copy()
    stanze_trovate = 0
    for cnt in contorni:
        if cv2.contourArea(cnt) > 1000:
            cv2.drawContours(img_colorata, [cnt], -1, (200, 255, 200), -1)
            stanze_trovate += 1
            
    risultato = cv2.addWeighted(img_colorata, 0.4, img, 0.6, 0)

    with col2:
        st.subheader("Zoning Aree")
        st.image(risultato, channels="BGR", use_column_width=True)

    # Calcolo Costi
    st.divider()
    st.header("🧮 Preventivo")
    
    prezzi = {"Pittura Standard": 15, "Pittura Antimuffa": 22, "Gres Porcellanato": 65}
    # Calcolo fittizio per l'esempio (15 mq per ogni stanza trovata)
    mq_stimati = stanze_trovate * 15 
    if mq_stimati == 0:
        mq_stimati = 50 # Valore di base se non trova stanze
        
    totale = mq_stimati * prezzi[intervento]

    st.metric(label=f"Superficie stimata", value=f"{mq_stimati} mq")
    st.subheader(f"Totale Stimato: € {totale:,.2f}")

    # Bottone PDF
    pdf_bytes = crea_pdf(nome_cliente, intervento, mq_stimati, totale)
    st.download_button(
        label="📥 Scarica Preventivo PDF",
        data=pdf_bytes,
        file_name=f"Preventivo_{nome_cliente.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )