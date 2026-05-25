import streamlit as st
import cv2
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from fpdf import FPDF

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Viterbo Restauri Pro", layout="wide")
st.title("🏗️ Sistema Professionale Ristrutturazioni")

# Sidebar
st.sidebar.header("Dati Cliente & Listino")
nome_cliente = st.sidebar.text_input("Nome Cliente", "Cliente Esempio")
intervento = st.sidebar.selectbox("Tipo di Intervento", ["Pittura Standard", "Pittura Antimuffa", "Gres Porcellanato"])
prezzi_mq = {"Pittura Standard": 15, "Pittura Antimuffa": 22, "Gres Porcellanato": 65}

# 1. CARICAMENTO
file = st.file_uploader("Carica la Planimetria (PNG/JPG)", type=['png', 'jpg', 'jpeg'])

if file:
    img_pil = Image.open(file)
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    
    st.info("📏 FASE 1: Traccia una linea su una misura nota (es. la larghezza di una porta o un muro)")
    
    # Canvas per calibrazione
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=3,
        stroke_color="#FF0000",
        background_image=img_pil,
        drawing_mode="line",
        height=img_pil.height * (800 / img_pil.width), # Mantiene le proporzioni
        width=800,
        key="canvas",
    )

    misura_reale = st.number_input("Lunghezza della linea tracciata (metri):", value=0.80)

    if canvas_result.json_data and len(canvas_result.json_data["objects"]) > 0:
        # Recupero pixel linea
        obj = canvas_result.json_data["objects"][-1]
        dist_px = np.sqrt(obj["width"]**2 + obj["height"]**2)
        ppm = dist_px / misura_reale # Pixel Per Metro
        
        st.success(f"Calibrazione: 1 metro = {ppm:.2f} pixel")

        if st.button("🚀 Elabora Planimetria e Calcola Costi"):
            # 2. ANALISI AVANZATA (Morfologia per linee sottili)
            grigio = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(grigio, 230, 255, cv2.THRESH_BINARY_INV)
            
            # Chiudiamo i buchi nelle linee (fondamentale per la tua immagine)
            kernel = np.ones((5,5), np.uint8)
            chiusura = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Trova stanze
            contorni, gerarchia = cv2.findContours(chiusura, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            
            img_risultato = img_cv.copy()
            mq_totali = 0
            
            if gerarchia is not None:
                for i, cnt in enumerate(contorni):
                    if gerarchia[0][i][3] != -1: # Se è un'area interna (stanza)
                        area_px = cv2.contourArea(cnt)
                        if area_px > (ppm * ppm * 0.5): # Filtro: almeno 0.5mq
                            # Colore e Disegno
                            colore = (np.random.randint(180, 255), np.random.randint(180, 255), np.random.randint(180, 255))
                            cv2.drawContours(img_risultato, [cnt], -1, colore, -1)
                            
                            # Calcolo MQ Reali
                            area_mq = area_px / (ppm**2)
                            mq_totali += area_mq
                            
                            # Testo su immagine
                            M = cv2.moments(cnt)
                            if M["m00"] != 0:
                                cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
                                cv2.putText(img_risultato, f"{area_mq:.1f}m2", (cx-20, cy), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)

            # Visualizzazione Risultato
            st.image(img_risultato, channels="BGR", caption="Planimetria Elaborata")
            
            # 3. RISULTATI ECONOMICI
            totale_euro = mq_totali * prezzi_mq[intervento]
            
            c1, c2 = st.columns(2)
            c1.metric("Superficie Totale", f"{mq_totali:.2f} m²")
            c2.metric("Costo Stimato", f"€ {totale_euro:,.2f}")
