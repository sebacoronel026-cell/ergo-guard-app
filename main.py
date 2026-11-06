import streamlit as strlit
import pandas as pd
import numpy as np

# Configuración de página
strlit.set_page_config(
    page_title="ErgoGuard - Dashboard Ergonómico",
    layout="wide"
)

# Estilos CSS limpios y optimizados
strlit.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp { 
        background-color: #0B0F19; 
        color: #F8FAFC; 
        font-family: 'Inter', sans-serif;
    }
    
    .metric-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        padding: 1.25rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 500;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
    }

    .title-container { text-align: center; padding: 3rem 0 1rem 0; }
    .title-text { font-size: 2.8rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.03em; margin-bottom: 0px; }
    .subtitle-text { font-size: 0.85rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.15em; margin-top: 8px; margin-bottom: 2.5rem; }
    </style>
""", unsafe_allow_html=True)

# Inicializar de forma segura el estado de sesión
if 'sesion_iniciada' not in strlit.session_state:
    strlit.session_state['sesion_iniciada'] = False

if 'analizado' not in strlit.session_state:
    strlit.session_state['analizado'] = False

# ---------------------------------------------------------
# LÓGICA DE CÁLCULO REBA (GRUPO A)
# ---------------------------------------------------------
def calcular_reba_grupo_a(df, incremento_carga, fuerza_brusca):
    tabla_a = {
        (1, 1, 1): 1, (1, 1, 2): 2, (1, 1, 3): 3, (1, 1, 4): 4,
        (1, 2, 1): 2, (1, 2, 2): 3, (1, 2, 3): 4, (1, 2, 4): 5,
        (1, 3, 1): 2, (1, 3, 2): 4, (1, 3, 3): 5, (1, 3, 4): 6,
        (1, 4, 1): 3, (1, 4, 2): 5, (1, 4, 3): 6, (1, 4, 4): 7,
        (1, 5, 1): 4, (1, 5, 2): 6, (1, 5, 3): 7, (1, 5, 4): 8,
        
        (2, 1, 1): 1, (2, 1, 2): 2, (2, 1, 3): 3, (2, 1, 4): 4,
        (2, 2, 1): 3, (2, 2, 2): 4, (2, 2, 3): 5, (2, 2, 4): 6,
        (2, 3, 1): 4, (2, 3, 2): 5, (2, 3, 3): 6, (2, 3, 4): 7,
        (2, 4, 1): 5, (2, 4, 2): 6, (2, 4, 3): 7, (2, 4, 4): 8,
        (2, 5, 1): 6, (2, 5, 2): 7, (2, 5, 3): 8, (2, 5, 4): 9,

        (3, 1, 1): 3, (3, 1, 2): 3, (3, 1, 3): 5, (3, 1, 4): 6,
        (3, 2, 1): 4, (3, 2, 2): 5, (3, 2, 3): 6, (3, 2, 4): 7,
        (3, 3, 1): 5, (3, 3, 2): 6, (3, 3, 3): 7, (3, 3, 4): 8,
        (3, 4, 1): 6, (3, 4, 2): 7, (3, 4, 3): 8, (3, 4, 4): 9,
        (3, 5, 1): 7, (3, 5, 2): 8, (3, 5, 3): 9, (3, 5, 4): 9,
    }

    res_tronco, res_cuello, res_piernas, res_grupo_a = [], [], [], []

    for _, r in df.iterrows():
        t_flex = r['tronco_flex']
        if t_flex < 0: s_t = 2
        elif t_flex <= 20: s_t = 1
        elif t_flex <= 60: s_t = 2
        else: s_t = 3
        if abs(r['tronco_inc']) > 5 or abs(r['tronco_giro']) > 5:
            s_t += 1
        s_t = min(max(s_t, 1), 5)

        c_flex = r['cuello_flex']
        if c_flex < 0: s_c = 2
        elif c_flex <= 20: s_c = 1
        else: s_c = 2
        if abs(r['cuello_inc']) > 5 or abs(r['cuello_giro']) > 5:
            s_c += 1
        s_c = min(max(s_c, 1), 3)

        rodilla_flex = abs(r['muslo_ang'] - r['pantorrilla_ang'])
        s_p = 1
        if 30 <= rodilla_flex <= 60: s_p += 1
        elif rodilla_flex > 60: s_p += 2
        s_p = min(max(s_p, 1), 4)

        score_base_a = tabla_a.get((s_c, s_t, s_p), 1)
        score_final_a = score_base_a + incremento_carga + fuerza_brusca

        res_tronco.append(s_t)
        res_cuello.append(s_c)
        res_piernas.append(s_p)
        res_grupo_a.append(score_final_a)

    df_res = df.copy()
    df_res['Puntaje_Tronco'] = res_tronco
    df_res['Puntaje_Cuello'] = res_cuello
    df_res['Puntaje_Piernas'] = res_piernas
    df_res['Score_Grupo_A'] = res_grupo_a
    return df_res

# ---------------------------------------------------------
# GENERADOR DE VISUALIZADOR 3D DE POSTURA
# ---------------------------------------------------------
def crear_avatar_3d(row_critica):
    try:
        import plotly.graph_objects as go
        t_flex = np.radians(row_critica['tronco_flex'])
        c_flex = np.radians(row_critica['cuello_flex'])
        
        pelvis = [0, 0, 0]
        cadera = [0, 0, 0.4]
        tronco_top = [0, np.sin(t_flex) * 0.5, 0.4 + np.cos(t_flex) * 0.5]
        cabeza = [0, tronco_top[1] + np.sin(c_flex) * 0.2, tronco_top[2] + np.cos(c_flex) * 0.2]
        
        rodilla_der = [0.2, 0, -0.4]
        pie_der = [0.2, 0.1, -0.9]

        x_pts = [pelvis[0], cadera[0], tronco_top[0], cabeza[0], tronco_top[0], rodilla_der[0], pie_der[0]]
        y_pts = [pelvis[1], cadera[1], tronco_top[1], cabeza[1], tronco_top[1], rodilla_der[1], pie_der[1]]
        z_pts = [pelvis[2], cadera[2], tronco_top[2], cabeza[2], tronco_top[2], rodilla_der[2], pie_der[2]]

        fig = go.Figure(data=[
            go.Scatter3d(
                x=x_pts, y=y_pts, z=z_pts,
                mode='lines+markers',
                marker=dict(size=8, color='#2563EB', symbol='circle'),
                line=dict(color='#38BDF8', width=6)
            )
        ])
        
        fig.update_layout(
            title=f"Postura Crítica - Timestamp: {int(row_critica['timestamp'])}",
            scene=dict(
                xaxis=dict(backgroundcolor="#0B0F19", gridcolor="#1F2937", showbackground=True),
                yaxis=dict(backgroundcolor="#0B0F19", gridcolor="#1F2937", showbackground=True),
                zaxis=dict(backgroundcolor="#0B0F19", gridcolor="#1F2937", showbackground=True),
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
            ),
            paper_bgcolor="#111827",
            font=dict(color="#F8FAFC", family="Inter"),
            margin=dict(l=0, r=0, t=30, b=0),
            height=350
        )
        return fig
    except Exception:
        return None

# ---------------------------------------------------------
# GENERADOR DE INFORME TÉCNICO
# ---------------------------------------------------------
def generar_html_informe(evaluador, empresa, puesto, df_eval, max_score, prom_score):
    template = """
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica', Arial, sans-serif; color: #111; margin: 40px; }}
            h1 {{ color: #0f172a; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }}
            .header-box {{ background: #f8fafc; padding: 15px; border-radius: 6px; margin-bottom: 20px; border: 1px solid #e2e8f0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; font-size: 12px; }}
            th {{ background-color: #f1f5f9; color: #334155; }}
        </style>
    </head>
    <body>
        <h1>INFORME TÉCNICO DE ERGONOMÍA - ERGOGUARD</h1>
        <p style="color: #64748B; font-size: 12px; text-transform: uppercase;">Powered by Nexómada</p>
        
        <div class="header-box">
            <h3>Datos de la Evaluación</h3>
            <p><strong>Evaluador:</strong> {evaluador}</p>
            <p><strong>Empresa:</strong> {empresa}</p>
            <p><strong>Puesto / Tarea:</strong> {puesto}</p>
        </div>

        <h3>Resumen Ejecutivo - Método REBA (Grupo A)</h3>
        <ul>
            <li><strong>Puntuación Máxima Registrada (Grupo A):</strong> {max_score}</li>
            <li><strong>Puntuación Promedio (Grupo A):</strong> {prom_score}</li>
            <li><strong>Total de Muestras Analizadas:</strong> {total_muestras} registros cinemáticos</li>
        </ul>

        <h3>Criterios de Higiene y Seguridad</h3>
        <p>El análisis postural del Grupo A evalúa los ángulos de tronco, cuello y piernas bajo los estándares internacionales de ergonomía laboral. Puntuaciones superiores a 4 requieren revisión detallada de las condiciones biomecánicas del puesto.</p>

        <h3>Muestras Registradas (Extracto)</h3>
        {tabla_html}
        
        <br><br>
        <p style="font-size: 10px; color: #94a3b8; text-align: center;">ErgoGuard Industrial Suite - Generado automáticamente</p>
    </body>
    </html>
    """
    return template.format(
        evaluador=evaluador,
        empresa=empresa,
        puesto=puesto,
        max_score=max_score,
        prom_score=prom_score,
        total_muestras=len(df_eval),
        tabla_html=df_eval.head(20).to_html(index=False)
    )

# ---------------------------------------------------------
# CONTROL DE VISTAS (PANTALLA 1 vs PANTALLA 2)
# ---------------------------------------------------------
sesion_activa = strlit.session_state.get('sesion_iniciada', False)

if not sesion_activa:
    # PANTALLA 1: INICIO (ErgoGuard / Nexómada)
    col_centro1, col_centro2, col_centro3 = strlit.columns([1, 2, 1])
    
    with col_centro2:
        strlit.markdown("""
            <div class="title-container">
                <h1 class="title-text">ErgoGuard</h1>
                <p class="subtitle-text">Powered by Nexómada</p>
            </div>
        """, unsafe_allow_html=True)
        
        with strlit.form("evaluacion_form"):
            strlit.markdown("### Configuración de la Evaluación")
            
            evaluador = strlit.text_input("Nombre del evaluador *")
            empresa = strlit.text_input("Empresa *")
            puesto = strlit.text_input("Puesto o tarea *")
            
            strlit.markdown("<br>", unsafe_allow_html=True)
            submit_button = strlit.form_submit_button(label="Iniciar Evaluación")

        if submit_button:
            if not evaluador or not empresa or not puesto:
                strlit.error("Por favor, complete todos los campos obligatorios para continuar.")
            else:
                strlit.session_state['sesion_iniciada'] = True
                strlit.session_state['evaluador'] = evaluador
                strlit.session_state['empresa'] = empresa
                strlit.session_state['puesto'] = puesto
                strlit.rerun()

else:
    # PANTALLA 2: DASHBOARD DE ANÁLISIS REBA
    with strlit.sidebar:
        strlit.markdown("### Panel ErgoGuard")
        strlit.markdown("---")
        
        if strlit.button("Reiniciar Sesión / Cambiar Evaluador"):
            strlit.session_state['sesion_iniciada'] = False
            strlit.session_state['analizado'] = False
            strlit.rerun()

        strlit.markdown("### Adquisición de Datos")
        uploaded_file = strlit.file_uploader("Subir CSV de sensores", type=["csv"])
        
        strlit.markdown("---")
        strlit.markdown("### Parámetros Manuales (REBA - Grupo A)")
        
        peso_fuerza = strlit.selectbox(
            "Peso o Fuerza ejercida:",
            ["< 2 kg (+0)", "2 kg a 10 kg (+1)", "> 10 kg (+2)"]
        )
        carga_score = 0 if "< 2" in peso_fuerza else (1 if "2 kg a 10" in peso_fuerza else 2)
        
        carga_brusca = strlit.checkbox("Aplicación brusca de fuerza (+1)")
        brusca_score = 1 if carga_brusca else 0

        ejecutar_btn = strlit.button("Ejecutar Análisis REBA")

    # CUERPO PRINCIPAL
    eval_name = strlit.session_state.get('evaluador', '')
    emp_name = strlit.session_state.get('empresa', '')
    pue_name = strlit.session_state.get('puesto', '')

    banner_template = """
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1F2937; padding-bottom: 1rem; margin-bottom: 1.5rem;">
            <h1 style="font-size: 1.8rem; font-weight: 800; color: #F8FAFC; margin: 0;">ErgoGuard <span style="color: #0284C7; font-weight: 400; font-size: 1.4rem;">| Monitor REBA (Grupo A)</span></h1>
            <div style="font-size: 0.85rem; color: #94A3B8; background: #111827; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #1F2937;">
                Evaluador: <strong style="color: #F8FAFC;">{}</strong> &nbsp;|&nbsp; Empresa: <strong style="color: #F8FAFC;">{}</strong> &nbsp;|&nbsp; Puesto: <strong style="color: #F8FAFC;">{}</strong>
            </div>
        </div>
    """
    strlit.markdown(banner_template.format(eval_name, emp_name, pue_name), unsafe_allow_html=True)

    if uploaded_file is not None:
        df_raw = pd.read_csv(uploaded_file)
        
        # El análisis OCURRE EXCLUSIVAMENTE al presionar el botón de ejecución
        if ejecutar_btn:
            strlit.session_state['df_eval'] = calcular_reba_grupo_a(df_raw, carga_score, brusca_score)
            strlit.session_state['analizado'] = True
        
        # Renderizado del dashboard condicionado a que se haya presionado el botón
        if strlit.session_state.get('analizado', False) and 'df_eval' in strlit.session_state:
            df_eval = strlit.session_state['df_eval']
            
            max_score_a = df_eval['Score_Grupo_A'].max()
            prom_score_a = round(df_eval['Score_Grupo_A'].mean(), 2)
            mediciones_totales = len(df_eval)
            extra_fuerza_val = f"+{carga_score + brusca_score}"
            
            # Tarjetas de métricas
            m1, m2, m3, m4 = strlit.columns(4)
            with m1:
                strlit.markdown('<div class="metric-card"><div class="metric-title">Puntuación Máxima A</div><div class="metric-value">{}</div></div>'.format(max_score_a), unsafe_allow_html=True)
            with m2:
                strlit.markdown('<div class="metric-card"><div class="metric-title">Promedio Grupo A</div><div class="metric-value">{}</div></div>'.format(prom_score_a), unsafe_allow_html=True)
            with m3:
                strlit.markdown('<div class="metric-card"><div class="metric-title">Total Muestras</div><div class="metric-value">{}</div></div>'.format(mediciones_totales), unsafe_allow_html=True)
            with m4:
                strlit.markdown('<div class="metric-card"><div class="metric-title">Carga / Fuerza Extra</div><div class="metric-value">{}</div></div>'.format(extra_fuerza_val), unsafe_allow_html=True)
            
            strlit.markdown("<br>", unsafe_allow_html=True)
            
            # Opciones de descarga
            col_d1, col_d2 = strlit.columns(2)
            with col_d1:
                csv_data = df_eval.to_csv(index=False).encode('utf-8')
                strlit.download_button(
                    label="Descargar Dataset Completo (CSV)",
                    data=csv_data,
                    file_name=f"ErgoGuard_REBA_{emp_name}_{pue_name}.csv",
                    mime="text/csv"
                )
            with col_d2:
                html_report = generar_html_informe(eval_name, emp_name, pue_name, df_eval, max_score_a, prom_score_a)
                strlit.download_button(
                    label="Descargar Informe Técnico (Formato Reporte)",
                    data=html_report,
                    file_name=f"Informe_ErgoGuard_{emp_name}.html",
                    mime="text/html"
                )

            strlit.markdown("<br>", unsafe_allow_html=True)
            
            # SECCIÓN CENTRAL: GRÁFICOS Y MODELO CORPORAL 3D
            col_left, col_right = strlit.columns([1.3, 1])
            
            with col_left:
                strlit.markdown("### Evolución Temporal - Puntuación Grupo A")
                strlit.line_chart(df_eval.set_index('timestamp')['Score_Grupo_A'])
                
                strlit.markdown("### Desglose de Sub-scores")
                chart_data = pd.DataFrame({
                    "Tronco": df_eval['Puntaje_Tronco'].value_counts(),
                    "Cuello": df_eval['Puntaje_Cuello'].value_counts(),
                    "Piernas": df_eval['Puntaje_Piernas'].value_counts()
                }).fillna(0)
                strlit.bar_chart(chart_data)

            with col_right:
                strlit.markdown("### Postura Crítica en 3D (Ángulos Máximos)")
                idx_max = df_eval['Score_Grupo_A'].idxmax()
                row_critica = df_eval.loc[idx_max]
                
                fig_3d = crear_avatar_3d(row_critica)
                if fig_3d is not None:
                    strlit.plotly_chart(fig_3d, use_container_width=True)
                else:
                    strlit.warning("Plotly no está disponible en este entorno. Verifique la instalación con 'python -m pip install plotly'.")
                
                val_rodilla = round(abs(row_critica['muslo_ang'] - row_critica['pantorrilla_ang']), 1)
                
                detalles_template = """
                    <div style="background: #111827; border: 1px solid #1F2937; padding: 1rem; border-radius: 8px; font-size: 0.85rem; color: #94A3B8;">
                        <strong>Detalle Biomecánico Crítico:</strong><br>
                        • Tronco Flexión: <span style="color: #F8FAFC;">{}°</span><br>
                        • Cuello Flexión: <span style="color: #F8FAFC;">{}°</span><br>
                        • Ángulo Muslo/Pierna: <span style="color: #F8FAFC;">{}°</span>
                    </div>
                """
                strlit.markdown(detalles_template.format(row_critica['tronco_flex'], row_critica['cuello_flex'], val_rodilla), unsafe_allow_html=True)

            strlit.markdown("<br>", unsafe_allow_html=True)
            with strlit.expander("Ver dataset completo con puntuaciones REBA"):
                strlit.dataframe(df_eval, use_container_width=True)
        else:
            strlit.info(f"Archivo cargado correctamente. Ajuste los parámetros manuales del Grupo A y presione el botón **'Ejecutar Análisis REBA'** para generar el reporte de {eval_name}.")
    else:
        strlit.info(f"El sistema se encuentra configurado y a la espera. Por favor, suba el archivo CSV en el panel izquierdo para iniciar la evaluación de {eval_name}.")