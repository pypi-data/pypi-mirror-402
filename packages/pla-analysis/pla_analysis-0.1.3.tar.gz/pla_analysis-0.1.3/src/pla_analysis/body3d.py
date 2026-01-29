import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil
import tempfile
from pathlib import Path

class BodyTracker:
    """
    Clase interna para realizar el seguimiento del punto negro en los frames.
    """
    def __init__(self, frames_folder):
        self.frames_folder = frames_folder
        self.frames = sorted(
            [f for f in os.listdir(frames_folder) if f.endswith(('.tif', '.png', '.jpg'))]
        )
        if not self.frames:
            raise ValueError(f"No se encontraron imágenes en '{frames_folder}'")

        self.escala_px_mm = None
        self.roi = None
        self.umbral = 127
        self.desplazamientos = []
        # Para dibujar la estela del movimiento
        self.trayectoria = [] 
        
        # Para el reporte comparativo
        self.img_inicio = None
        self.img_max_desp = None
        self.max_desp_registrado = 0.0

    def configurar_escala_interactiva(self):
        """Abre interfaz gráfica para calibrar escala."""
        primer_frame = os.path.join(self.frames_folder, self.frames[0])
        img = cv2.imread(primer_frame, cv2.IMREAD_GRAYSCALE)
        
        # Guardamos imagen inicial para el reporte
        self.img_inicio = img.copy()
        
        img_clean = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img_display = img_clean.copy()
        
        puntos = []
        nombre_ventana = 'Calibracion: Click Inicio y Fin (r=Reset, ENTER=Confirmar)'

        def click_event(event, x, y, flags, params):
            if event == cv2.EVENT_LBUTTONDOWN:
                if len(puntos) >= 2:
                    puntos.clear()
                    img_display[:] = img_clean[:] 
                
                puntos.append((x, y))
                cv2.circle(img_display, (x, y), 5, (0, 255, 0), -1)
                
                if len(puntos) == 2:
                    cv2.line(img_display, puntos[0], puntos[1], (0, 255, 0), 2)
                
                cv2.imshow(nombre_ventana, img_display)

        print("Selecciona dos puntos para la escala.")
        cv2.namedWindow(nombre_ventana)
        cv2.setMouseCallback(nombre_ventana, click_event)
        cv2.imshow(nombre_ventana, img_display)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('r'):
                puntos.clear()
                img_display[:] = img_clean[:]
                cv2.imshow(nombre_ventana, img_display)
            elif key == 13: # ENTER
                if len(puntos) == 2: break
                else: print("Necesitas 2 puntos.")
        
        cv2.destroyAllWindows()

        dist_px = np.sqrt((puntos[1][0] - puntos[0][0])**2 + (puntos[1][1] - puntos[0][1])**2)
        print(f"Distancia en píxeles: {dist_px:.2f}")
        
        while True:
            try:
                entrada = input(f"¿Cuántos mm son esos {dist_px:.2f} px en la realidad?: ")
                dist_real = float(entrada)
                if dist_real <= 0: continue
                break
            except ValueError:
                print("Introduce un número válido.")
            
        self.escala_px_mm = dist_px / dist_real
        return self.escala_px_mm

    def seleccionar_roi_interactiva(self):
        """Abre interfaz para seleccionar ROI."""
        primer_frame = os.path.join(self.frames_folder, self.frames[0])
        img = cv2.imread(primer_frame, cv2.IMREAD_GRAYSCALE)
        
        print("Selecciona la región de interés a analizar y pulsa ENTER")
        try:
            roi = cv2.selectROI('Selecciona la region de interes', img, showCrosshair=True)
        finally:
            cv2.destroyAllWindows()
        
        if roi[2] == 0 or roi[3] == 0:
            raise ValueError("Región no válida.")
        self.roi = roi
        return roi

    def calibrar_umbral_interactivo(self):
        """Abre interfaz con slider para umbral."""
        primer_frame = os.path.join(self.frames_folder, self.frames[0])
        img = cv2.imread(primer_frame, cv2.IMREAD_GRAYSCALE)
        x, y, w, h = self.roi
        img_roi = img[y:y+h, x:x+w]

        def nada(x): pass

        ventana_umbral = 'Ajuste Blanco y Negro (ENTER para confirmar)'
        cv2.namedWindow(ventana_umbral)
        cv2.createTrackbar('Umbral', ventana_umbral, self.umbral, 255, nada)
        
        print("Ajusta el umbral hasta aislar el punto negro y pulsa ENTER")
        while True:
            u = cv2.getTrackbarPos('Umbral', ventana_umbral)
            self.umbral = u
            _, th = cv2.threshold(img_roi, u, 255, cv2.THRESH_BINARY)
            cv2.imshow(ventana_umbral, th)
            if cv2.waitKey(1) & 0xFF == 13: break
        
        cv2.destroyAllWindows()
        return self.umbral

    def _dibujar_dashboard(self, frame_bgr, desplazamiento_actual, frame_idx):
        h_video, w_video = frame_bgr.shape[:2]
        ancho_panel = 500
        fondo_color = (245, 245, 245)
        panel = np.ones((h_video, ancho_panel, 3), dtype=np.uint8)
        panel[:] = fondo_color
        
        # --- HEADER ---
        altura_header = 140
        cv2.rectangle(panel, (0, 0), (ancho_panel, altura_header), (230, 230, 230), -1)
        cv2.line(panel, (0, altura_header), (ancho_panel, altura_header), (180, 180, 180), 1)

        texto_disp = f"{desplazamiento_actual:.3f} mm" if desplazamiento_actual is not None else "--"
        
        cv2.putText(panel, "Analisis en Tiempo Real", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 80, 80), 1, cv2.LINE_AA)
        cv2.putText(panel, "Desplazamiento horizontal:", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)
        cv2.putText(panel, texto_disp, (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 150), 2, cv2.LINE_AA)
        
        progreso = frame_idx / len(self.frames)
        w_barra = ancho_panel - 40
        cv2.rectangle(panel, (20, 125), (20 + w_barra, 130), (200, 200, 200), -1)
        cv2.rectangle(panel, (20, 125), (20 + int(w_barra * progreso), 130), (0, 180, 0), -1)

        # --- GRÁFICA ---
        datos_validos = [d for d in self.desplazamientos if d is not None]
        
        if len(datos_validos) > 1:
            margen_x = 40
            margen_y_inf = 40
            y_inicio_grafica = altura_header + 20 
            h_grafica = h_video - y_inicio_grafica - margen_y_inf
            w_grafica = ancho_panel - 2 * margen_x
            
            min_val = min(datos_validos)
            max_val = max(datos_validos)
            
            # Estabilización
            if abs(max_val - min_val) < 1.0:
                centro = (max_val + min_val) / 2
                min_val = centro - 0.5
                max_val = centro + 0.5
            
            span = max_val - min_val
            min_val -= span * 0.1
            max_val += span * 0.1
            rango_val = max_val - min_val

            puntos_plot = []
            total_frames = len(self.frames)
            
            for i, val in enumerate(datos_validos):
                px = int(margen_x + (i / total_frames) * w_grafica)
                val_norm = (val - min_val) / rango_val
                py = int((y_inicio_grafica + h_grafica) - (val_norm * h_grafica))
                puntos_plot.append((px, py))
            
            color_ejes = (100, 100, 100)
            cv2.line(panel, (margen_x, y_inicio_grafica), (margen_x, h_video - margen_y_inf), color_ejes, 1)
            cv2.line(panel, (margen_x, h_video - margen_y_inf), (ancho_panel - margen_x, h_video - margen_y_inf), color_ejes, 1)

            if len(puntos_plot) > 1:
                cv2.polylines(panel, [np.array(puntos_plot)], False, (200, 50, 0), 2, cv2.LINE_AA)
            
            if puntos_plot:
                cv2.circle(panel, puntos_plot[-1], 4, (0, 0, 255), -1, cv2.LINE_AA)

        return np.hstack((frame_bgr, panel))

    def procesar(self, guardar_video=False, nombre_video_salida="resultado_analisis.mp4"):
        x, y, w, h = self.roi
        pos_inicial_x = None

        print(f"Procesando {len(self.frames)} frames...")
        cv2.namedWindow("Analisis en Vivo", cv2.WINDOW_NORMAL)
        
        video_writer = None
        
        # Reiniciar para este análisis
        self.img_max_desp = self.img_inicio.copy() # Por defecto
        self.max_desp_registrado = 0.0
        
        for idx, frame_name in enumerate(self.frames):
            path = os.path.join(self.frames_folder, frame_name)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            frame_vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            
            # --- Detección ---
            img_roi = img[y:y+h, x:x+w]
            _, img_bin = cv2.threshold(img_roi, self.umbral, 255, cv2.THRESH_BINARY)
            img_inv = cv2.bitwise_not(img_bin)
            
            M = cv2.moments(img_inv)
            desp_mm = None
            
            if M["m00"] != 0:
                cx_global = x + int(M["m10"] / M["m00"])
                cy_global = y + int(M["m01"] / M["m00"])
                
                # Guardar trayectoria (Estela)
                self.trayectoria.append((cx_global, cy_global))
                
                # Visualización
                cv2.rectangle(frame_vis, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Dibujar Estela (Línea amarilla)
                if len(self.trayectoria) > 1:
                    cv2.polylines(frame_vis, [np.array(self.trayectoria)], False, (0, 255, 255), 1, cv2.LINE_AA)
                
                cv2.circle(frame_vis, (cx_global, cy_global), 5, (0, 0, 255), -1)
                
                if pos_inicial_x is None:
                    pos_inicial_x = cx_global
                    desp_mm = 0.0
                else:
                    desp_px = cx_global - pos_inicial_x
                    desp_mm = desp_px / self.escala_px_mm
                    
                    # Chequear si este es el frame de máximo desplazamiento absoluto
                    if abs(desp_mm) > abs(self.max_desp_registrado):
                        self.max_desp_registrado = desp_mm
                        self.img_max_desp = img.copy() # Guardar foto original en B/N
            else:
                cv2.rectangle(frame_vis, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame_vis, "LOST", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
            
            self.desplazamientos.append(desp_mm)

            # --- Dashboard ---
            dashboard = self._dibujar_dashboard(frame_vis, desp_mm, idx)
            cv2.imshow("Analisis en Vivo", dashboard)
            
            # --- Grabar ---
            if guardar_video:
                if video_writer is None:
                    h_dash, w_dash = dashboard.shape[:2]
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
                    video_writer = cv2.VideoWriter(nombre_video_salida, fourcc, 25.0, (w_dash, h_dash))
                video_writer.write(dashboard)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\nAnálisis interrumpido.")
                break
        
        if video_writer:
            video_writer.release()
            print(f"Video guardado como: {nombre_video_salida}")

        cv2.destroyAllWindows()
        return self.desplazamientos

    def generar_reporte_comparativo(self, save_path="resultado_comparacion.png"):
        """Genera una imagen resumen con Inicio vs Máximo Desplazamiento."""
        if self.img_inicio is None or self.img_max_desp is None:
            return

        print("Generando reporte comparativo...")
        
        # Crear figura de Matplotlib
        fig = plt.figure(figsize=(12, 6))
        gs = fig.add_gridspec(1, 3) # 1 fila, 3 columnas

        # 1. Imagen Inicio
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.imshow(self.img_inicio, cmap='gray')
        ax1.set_title("Inicio (0 mm)")
        ax1.axis('off')
        # Dibujar recuadro de ROI referencia
        if self.roi:
            x, y, w, h = self.roi
            rect = plt.Rectangle((x, y), w, h, linewidth=2, edgecolor='g', facecolor='none')
            ax1.add_patch(rect)

        # 2. Imagen Máximo
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.imshow(self.img_max_desp, cmap='gray')
        ax2.set_title(f"Desplazamiento horizontal máximo\n({self.max_desp_registrado:.2f} mm)")
        ax2.axis('off')
        if self.roi:
            x, y, w, h = self.roi
            # ROI en rojo para el máximo
            rect = plt.Rectangle((x, y), w, h, linewidth=2, edgecolor='r', facecolor='none')
            ax2.add_patch(rect)

        # 3. Gráfica Final
        ax3 = fig.add_subplot(gs[0, 2])
        validos = [d for d in self.desplazamientos if d is not None]
        if validos:
            ax3.plot(validos, color='blue', label='Desplazamiento')
            ax3.axhline(self.max_desp_registrado, color='red', linestyle='--', alpha=0.7)
            ax3.set_title("Evolución Temporal")
            ax3.set_xlabel("Frames")
            ax3.set_ylabel("Desplazamiento (mm)")
            ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150)
        plt.close()
        print(f"Reporte guardado como: {save_path}")


def _extraer_frames_a_temp(video_path, temp_dir):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video no encontrado: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError("No se pudo abrir el video.")
    print(f"Extrayendo frames del video completo...")
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        filename = os.path.join(temp_dir, f"frame_{count:06d}.tif")
        cv2.imwrite(filename, gray)
        count += 1
    cap.release()
    print(f"\nTotal frames extraídos: {count}")
    return count

def analyze(video_path, plot_result=True, save_video=True):
    """
    Función principal.
    """
    temp_dir = tempfile.mkdtemp(prefix="pla_body3d_")
    
    try:
        num_frames = _extraer_frames_a_temp(video_path, temp_dir)
        if num_frames == 0: return None

        tracker = BodyTracker(temp_dir)
        tracker.configurar_escala_interactiva()
        tracker.seleccionar_roi_interactiva()
        tracker.calibrar_umbral_interactivo()
        
        # Procesar y Grabar
        desplazamientos = tracker.procesar(guardar_video=save_video, nombre_video_salida="resultado_video.mp4")
        
        # Generar Reporte Comparativo (Visual)
        tracker.generar_reporte_comparativo("reporte_comparativo.png")
        
        validos = [d for d in desplazamientos if d is not None]
        if not validos: return {}
            
        max_disp_izq = min(validos)
        max_disp_abs = max(validos, key=abs)
        
        results = {
            "max_displacement_left": max_disp_izq,
            "max_displacement_absolute": max_disp_abs,
            "raw_data": desplazamientos,
            "total_frames": num_frames
        }

        print(f"\nDesplazamiento horizontal máximo: {max_disp_izq:.4f} mm")

        if plot_result:
            plt.figure(figsize=(10, 5))
            plt.plot(desplazamientos, label="Desplazamiento")
            plt.axhline(max_disp_izq, color='r', linestyle='--', label=f"Max: {max_disp_izq:.2f}mm")
            plt.title("Resultado Final: Análisis de desplazamiento horizontal")
            plt.xlabel("Frame")
            plt.ylabel("Desplazamiento (mm)")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.show()

        return results

    except Exception as e:
        print(f"Error durante el análisis: {e}")
        import traceback
        traceback.print_exc() 
        return None
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)