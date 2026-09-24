import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, TextBox, Button, RadioButtons
from scipy.integrate import cumulative_trapezoid
import tkinter as tk

# ==========================================
# 1. DATOS ESPACIALES Y DE PARTÍCULAS
# ==========================================
# Malla espacial continua
x = np.linspace(-3, 3, 50)
y = np.linspace(-3, 3, 50)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)

# Muestra atómica dual (100 partículas de cada especie)
np.random.seed(42)
N_atomos = 100
X_a, Y_a = np.random.uniform(-2.5, 2.5, N_atomos), np.random.uniform(-2.5, 2.5, N_atomos)
R_a = np.sqrt(X_a**2 + Y_a**2)

X_b, Y_b = np.random.uniform(-2.5, 2.5, N_atomos), np.random.uniform(-2.5, 2.5, N_atomos)
R_b = np.sqrt(X_b**2 + Y_b**2)

# Constantes físicas y tiempo
t_array = np.linspace(0, 10, 500)
Q_v = 1.5
T = 300.0

# Biblioteca de Fórmulas Predefinidas
FORMULAS = {
    "Pulso Gaussiano": "H_0 + lam * Q_v * np.exp(-2*(t-5)**2) * np.cos(3*R)",
    "Onda Viajera":    "H_0 + lam * Q_v * np.sin(2*R - 3*t) * np.exp(-0.1*R**2)",
    "Oscilador":       "H_0 + lam * Q_v * (0.5*R**2) * np.cos(2*t)",
    "Campo Pulsante":  "H_0 + lam * Q_v * np.exp(-0.5*R) * np.sin(4*t)",
    "Solitón":         "H_0 + lam * Q_v / (1 + (R - t)**2)"
}

ecuacion_actual = FORMULAS["Pulso Gaussiano"]
modo_vista = 0  # 0: Malla Continua, 1: Átomos Red, 2: Colisionador Dual
animando = False

# ==========================================
# 2. INTERFAZ Y PANELES
# ==========================================
fig = plt.figure(figsize=(16, 9.5))
plt.subplots_adjust(left=0.05, bottom=0.38, right=0.95, top=0.88)

fig.text(0.5, 0.95, r'Laboratorio Cuántico Unificado: $H^\star(R,t) = H_0(R) + \lambda \hat{Q}_v f(R,t)$', 
         fontsize=18, fontweight='bold', ha='center', color='darkblue')

ax3d = fig.add_subplot(121, projection='3d')
ax2d = fig.add_subplot(122)

ax2d.set_title('Probabilidad Global de Transición $P_R(t)$')
ax2d.set_xlabel('Tiempo (s)')
ax2d.set_ylabel('Probabilidad')
linea_prob, = ax2d.plot([], [], color='crimson', linewidth=3)
linea_tiempo = ax2d.axvline(0, color='blue', linestyle='--', label='Tiempo Actual')
ax2d.axhline(1.0, color='black', linestyle=':', alpha=0.5)
ax2d.set_xlim(0, 10)
ax2d.set_ylim(0, 1.1)

# ==========================================
# 3. WIDGETS Y CONTROLES
# ==========================================
# Fila de Ecuación y Botones
ax_box       = plt.axes([0.12, 0.28, 0.38, 0.04])
ax_btn_copy  = plt.axes([0.51, 0.28, 0.05, 0.04])
ax_btn_paste = plt.axes([0.57, 0.28, 0.05, 0.04])
ax_btn_vista = plt.axes([0.63, 0.28, 0.15, 0.04])
ax_btn_play  = plt.axes([0.79, 0.28, 0.12, 0.04])

# Sliders
ax_tiempo = plt.axes([0.12, 0.20, 0.45, 0.03])
ax_lam    = plt.axes([0.12, 0.13, 0.45, 0.03])
ax_masa_a = plt.axes([0.65, 0.20, 0.26, 0.03])
ax_masa_b = plt.axes([0.65, 0.13, 0.26, 0.03])

# Panel de Fórmulas Predefinidas (RadioButtons corregido)
ax_radio = plt.axes([0.05, 0.01, 0.90, 0.09], facecolor='whitesmoke')
radio_formulas = RadioButtons(ax_radio, list(FORMULAS.keys()), active=0)

txt_formula = TextBox(ax_box, r'$H^\star$ = ', initial=ecuacion_actual)
btn_copy  = Button(ax_btn_copy, 'Copiar')
btn_paste = Button(ax_btn_paste, 'Pegar')
btn_vista = Button(ax_btn_vista, 'Vista: Malla 3D', color='lightblue')
btn_play  = Button(ax_btn_play, '▶ PLAY', color='lightgreen')

slider_tiempo = Slider(ax_tiempo, 'Tiempo (t)', 0.0, 10.0, valinit=0.0, color='cyan')
slider_lam    = Slider(ax_lam, 'Fuerza (λ)', 0.0, 5.0, valinit=1.5, color='orange')
slider_masa_a = Slider(ax_masa_a, 'Masa Azul', 1.0, 200.0, valinit=1.0, color='dodgerblue')
slider_masa_b = Slider(ax_masa_b, 'Masa Verde', 1.0, 200.0, valinit=40.0, color='limegreen')

# ==========================================
# 4. FUNCIONES DE INTERACCIÓN
# ==========================================
def portapapeles(accion, texto=""):
    try:
        r = tk.Tk(); r.withdraw()
        if accion == 'c': r.clipboard_clear(); r.clipboard_append(texto); r.update()
        else: texto = r.clipboard_get()
        r.destroy(); return texto
    except: return ""

btn_copy.on_clicked(lambda x: portapapeles('c', txt_formula.text))
btn_paste.on_clicked(lambda x: txt_formula.set_val(portapapeles('p')) or actualizar_simulacion())

def cambiar_formula_preset(label):
    txt_formula.set_val(FORMULAS[label])
    actualizar_simulacion()

radio_formulas.on_clicked(cambiar_formula_preset)

NOMBRES_VISTA = ['Vista: Malla 3D', 'Vista: Átomos Red', 'Vista: Colisionador Dual']
COLORES_VISTA = ['lightblue', 'plum', 'salmon']

def cambiar_modo_vista(event):
    global modo_vista
    modo_vista = (modo_vista + 1) % 3
    btn_vista.label.set_text(NOMBRES_VISTA[modo_vista])
    btn_vista.color = COLORES_VISTA[modo_vista]
    actualizar_simulacion()

btn_vista.on_clicked(cambiar_modo_vista)

# ==========================================
# 5. MOTOR FÍSICO Y RENDERIZADO
# ==========================================
def actualizar_simulacion(*args):
    ax3d.clear()
    ax3d.set_title(f'Espacio Cuántico ({NOMBRES_VISTA[modo_vista]})')
    ax3d.set_zlim(10, 25)
    ax3d.set_xlabel('Espacio X'); ax3d.set_ylabel('Espacio Y'); ax3d.set_zlabel('Energía (H*)')

    t_val = slider_tiempo.val
    lam_val = slider_lam.val
    m_a, m_b = slider_masa_a.val, slider_masa_b.val
    formula = txt_formula.text

    try:
        # Entorno base para evaluación continua 3D
        entorno_grid = {'np': np, 'R': R, 'X': X, 'Y': Y, 't': t_val, 'lam': lam_val, 'Q_v': Q_v, 'H_0': 10 + R**2}
        H_star_grid = eval(formula, entorno_grid)

        # Entorno para 2D probabilidad
        entorno_2d = {'np': np, 'R': 0, 'X': 0, 'Y': 0, 't': t_array, 'lam': lam_val, 'Q_v': Q_v, 'H_0': 10.0}
        H_star_2d = eval(formula, entorno_2d)
    except Exception:
        return

    # Renderizado según la vista seleccionada
    if modo_vista == 0:
        # Malla 3D continua
        ax3d.plot_surface(X, Y, H_star_grid, cmap='magma', edgecolor='none', alpha=0.95)

    elif modo_vista == 1:
        # Red monoatómica
        X_red, Y_red = X[::2, ::2], Y[::2, ::2]
        H_red = H_star_grid[::2, ::2]
        vib = np.random.normal(0, 0.04, X_red.shape) * (H_red - 10) / np.sqrt(m_a)
        ax3d.scatter(X_red + vib, Y_red + vib, H_red + vib, c=H_red, cmap='magma', s=60, edgecolors='k')

    elif modo_vista == 2:
        # Colisionador Dual de Especies Atómicas
        entorno_A = {'np': np, 'R': R_a, 'X': X_a, 'Y': Y_a, 't': t_val, 'lam': lam_val, 'Q_v': Q_v, 'H_0': 10 + R_a**2}
        entorno_B = {'np': np, 'R': R_b, 'X': X_b, 'Y': Y_b, 't': t_val, 'lam': lam_val, 'Q_v': Q_v, 'H_0': 10 + R_b**2}
        
        H_A, H_B = eval(formula, entorno_A), eval(formula, entorno_B)
        
        vib_A = np.random.normal(0, 0.08, N_atomos) * (H_A - 10) / np.sqrt(m_a)
        vib_B = np.random.normal(0, 0.08, N_atomos) * (H_B - 10) / np.sqrt(m_b)

        Z_a, Z_b = H_A + vib_A, H_B + vib_B

        col_A = ['gold' if z > 16 else 'dodgerblue' for z in Z_a]
        col_B = ['gold' if z > 16 else 'limegreen' for z in Z_b]
        sz_A = [130 if z > 16 else 45 for z in Z_a]
        sz_B = [130 if z > 16 else 45 for z in Z_b]

        xm, ym = np.meshgrid(np.linspace(-3, 3, 15), np.linspace(-3, 3, 15))
        ax3d.plot_wireframe(xm, ym, 10 + xm**2 + ym**2, color='gray', alpha=0.15)
        ax3d.scatter(X_a + vib_A, Y_a + vib_A, Z_a, c=col_A, s=sz_A, edgecolors='k')
        ax3d.scatter(X_b + vib_B, Y_b + vib_B, Z_b, c=col_B, s=sz_B, edgecolors='k')

    # Actualización del gráfico de probabilidad
    k_base = 0.03
    k_R = k_base + 0.8 * (H_star_2d - 10.0) * (T / 300)
    k_R = np.maximum(k_R, 0)
    integral_kR = cumulative_trapezoid(k_R, t_array, initial=0)
    P_R = 1 - np.exp(-integral_kR)

    linea_prob.set_data(t_array, P_R)
    linea_tiempo.set_xdata([t_val])
    fig.canvas.draw_idle()

# ==========================================
# 6. ANIMACIÓN
# ==========================================
timer = fig.canvas.new_timer(interval=50)

def bucle_animacion():
    t_nuevo = slider_tiempo.val + 0.05
    if t_nuevo > 10.0: t_nuevo = 0.0
    slider_tiempo.set_val(t_nuevo)

timer.add_callback(bucle_animacion)

def toggle_play(event):
    global animando
    animando = not animando
    if animando:
        btn_play.label.set_text('⏸ PAUSA')
        btn_play.color = 'lightcoral'
        timer.start()
    else:
        btn_play.label.set_text('▶ PLAY')
        btn_play.color = 'lightgreen'
        timer.stop()

btn_play.on_clicked(toggle_play)

slider_tiempo.on_changed(actualizar_simulacion)
slider_lam.on_changed(actualizar_simulacion)
slider_masa_a.on_changed(actualizar_simulacion)
slider_masa_b.on_changed(actualizar_simulacion)
txt_formula.on_submit(actualizar_simulacion)

actualizar_simulacion()
plt.show()