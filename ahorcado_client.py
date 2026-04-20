"""
Ahorcado - Cliente TCP con UI Tkinter
Compilacion: python3 ahorcado_client.py <host>
"""

import sys
import socket
import threading
import tkinter as tk
from tkinter import font as tkfont

# ─── Configuracion de red ─────────────────────────────────────────────────── #

PUERTO = 5000
DIRSIZE = 2048

# ─── Paleta de colores ────────────────────────────────────────────────────── #

BG        = "#0d0f14"
BG2       = "#141720"
BG3       = "#1c2030"
BORDER    = "#2a2f45"
CYAN      = "#4ee8d4"
CYAN_DIM  = "#1f6b62"
GREEN     = "#3dffa0"
GREEN_DIM = "#1a5c42"
RED       = "#ff4f5e"
RED_DIM   = "#5c1e25"
AMBER     = "#ffb830"
AMBER_DIM = "#5c3f0a"
GRAY      = "#4a5068"
WHITE     = "#e8eaf0"
WHITE_DIM = "#7880a0"

FONT_MONO = "Courier"
FONT_SANS = "Helvetica"

# ─── Figuras del ahorcado (ASCII) ─────────────────────────────────────────── #

FIGURAS = [
    # 0 errores
    ("  +---+\n"
     "  |   |\n"
     "  |\n"
     "  |\n"
     "  |\n"
     "  |\n"
     "__|__"),
    # 1 error
    ("  +---+\n"
     "  |   |\n"
     "  |  (o_o)\n"
     "  |\n"
     "  |\n"
     "  |\n"
     "__|__"),
    # 2 errores
    ("  +---+\n"
     "  |   |\n"
     "  |  (o_o)\n"
     "  |  (|\n"
     "  |\n"
     "  |\n"
     "__|__"),
    # 3 errores
    ("  +---+\n"
     "  |   |\n"
     "  |  (o_o)\n"
     r"  | \(|" + "\n"
     "  |\n"
     "  |\n"
     "__|__"),
    # 4 errores
    ("  +---+\n"
     "  |   |\n"
     "  |  (o_o)\n"
     r"  | \(|)/" + "\n"
     "  |\n"
     "  |\n"
     "__|__"),
    # 5 errores
    ("  +---+\n"
     "  |   |\n"
     "  |  (o_o)\n"
     r"  | \(|)/" + "\n"
     "  | / \\\n"
     "  |\n"
     "__|__"),
]

# ─── Utilidad: conexion TCP ───────────────────────────────────────────────── #

def conectar(host):
    hp = socket.gethostbyname(host)
    sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sd.connect((hp, PUERTO))
    return sd

def enviar(sd, msg):
    data = (msg + "\0").encode()
    sd.sendall(data)

def recibir(sd):
    buf = b""
    while True:
        chunk = sd.recv(DIRSIZE)
        if not chunk:
            break
        buf += chunk
        if b"\0" in buf:
            break
    return buf.rstrip(b"\0").decode(errors="replace")


# ═══════════════════════════════════════════════════════════════════════════ #
#  WIDGETS REUTILIZABLES
# ═══════════════════════════════════════════════════════════════════════════ #

def make_btn(parent, text, cmd, color=CYAN, width=220, pady=10):
    frm = tk.Frame(parent, bg=color, padx=1, pady=1)
    inner = tk.Frame(frm, bg=BG2)
    inner.pack(fill="both", expand=True)
    lbl = tk.Label(
        inner, text=text, bg=BG2, fg=color,
        font=(FONT_MONO, 12, "bold"),
        cursor="hand2", width=width // 10,
        pady=pady, padx=16,
    )
    lbl.pack(fill="both", expand=True)
    lbl.bind("<Button-1>", lambda e: cmd())
    lbl.bind("<Enter>", lambda e: (lbl.config(bg=color, fg=BG),))
    lbl.bind("<Leave>", lambda e: (lbl.config(bg=BG2, fg=color),))
    frm.bind("<Button-1>", lambda e: cmd())
    return frm

def make_entry(parent, show=None):
    frm = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    inner = tk.Frame(frm, bg=BG3)
    inner.pack(fill="both", expand=True)
    e = tk.Entry(
        inner, bg=BG3, fg=WHITE, insertbackground=CYAN,
        font=(FONT_MONO, 13), relief="flat",
        highlightthickness=0, show=show,
    )
    e.pack(fill="x", padx=8, pady=6)
    return frm, e

def make_label(parent, text, size=12, color=WHITE_DIM, bold=False, anchor="w"):
    weight = "bold" if bold else "normal"
    return tk.Label(
        parent, text=text, bg=BG, fg=color,
        font=(FONT_MONO, size, weight), anchor=anchor,
    )

def separator(parent, color=BORDER):
    tk.Frame(parent, bg=color, height=1).pack(fill="x", pady=8)


# ═══════════════════════════════════════════════════════════════════════════ #
#  PANTALLAS
# ═══════════════════════════════════════════════════════════════════════════ #

class App(tk.Tk):
    def __init__(self, host):
        super().__init__()
        self.host = host
        self.sd = None
        self.title("Ahorcado")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("1024x768")
        self._frame = None
        self.mostrar(MenuPrincipal)

    def mostrar(self, FrameClass, **kwargs):
        if self._frame:
            self._frame.destroy()
        self._frame = FrameClass(self, **kwargs)
        self._frame.pack(fill="both", expand=True)


# ─── Menú principal ────────────────────────────────────────────────────── #

class MenuPrincipal(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._build()

    def _build(self):
        self.pack_propagate(False)

        # Header
        hdr = tk.Frame(self, bg=BG2, pady=28)
        hdr.pack(fill="x")
        tk.Label(hdr, text="=== AHORCADO ===", bg=BG2, fg=CYAN,
                 font=(FONT_MONO, 22, "bold")).pack()
        tk.Label(hdr, text="Juego de palabras en red", bg=BG2, fg=WHITE_DIM,
                 font=(FONT_MONO, 10)).pack(pady=(4, 0))

        tk.Frame(self, bg=CYAN, height=2).pack(fill="x")

        body = tk.Frame(self, bg=BG, padx=60)
        body.pack(fill="both", expand=True, pady=40)

        tk.Label(body, text="Selecciona una opción:", bg=BG, fg=WHITE_DIM,
                 font=(FONT_MONO, 11)).pack(anchor="w", pady=(0, 20))

        make_btn(body, "▶  Iniciar sesión", self._login, CYAN).pack(fill="x", pady=6)
        make_btn(body, "✦  Crear usuario",  self._registro, GREEN).pack(fill="x", pady=6)
        make_btn(body, "◉  Acerca de / Instrucciones", self._acerca, AMBER).pack(fill="x", pady=6)
        make_btn(body, "✕  Salir", self.master.destroy, GRAY).pack(fill="x", pady=6)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side="bottom")
        tk.Label(self, text=f"Servidor: {self.master.host}:{PUERTO}",
                 bg=BG, fg=GRAY, font=(FONT_MONO, 9)).pack(side="bottom", pady=6)

    def _login(self):    self.master.mostrar(PantallaLogin, opcion="0")
    def _registro(self): self.master.mostrar(PantallaLogin, opcion="1")
    def _acerca(self):   self.master.mostrar(PantallaAcercaDe)


# ─── Login / Registro ──────────────────────────────────────────────────── #

class PantallaLogin(tk.Frame):
    def __init__(self, master, opcion="0"):
        super().__init__(master, bg=BG)
        self.opcion = opcion
        self.error_var = tk.StringVar()
        self._build()

    def _build(self):
        titulo = "Iniciar sesión" if self.opcion == "0" else "Crear usuario"
        color  = CYAN if self.opcion == "0" else GREEN

        hdr = tk.Frame(self, bg=BG2, pady=24)
        hdr.pack(fill="x")
        tk.Label(hdr, text=titulo.upper(), bg=BG2, fg=color,
                 font=(FONT_MONO, 18, "bold")).pack()
        tk.Frame(self, bg=color, height=2).pack(fill="x")

        body = tk.Frame(self, bg=BG, padx=60)
        body.pack(fill="both", expand=True, pady=30)

        tk.Label(body, text="Usuario", bg=BG, fg=WHITE_DIM,
                 font=(FONT_MONO, 11)).pack(anchor="w", pady=(0, 4))
        uf, self.ent_user = make_entry(body)
        uf.pack(fill="x", pady=(0, 16))

        tk.Label(body, text="Contraseña", bg=BG, fg=WHITE_DIM,
                 font=(FONT_MONO, 11)).pack(anchor="w", pady=(0, 4))
        pf, self.ent_pass = make_entry(body, show="•")
        pf.pack(fill="x", pady=(0, 24))

        self.ent_pass.bind("<Return>", lambda e: self._enviar())

        tk.Label(body, textvariable=self.error_var, bg=BG, fg=RED,
                 font=(FONT_MONO, 10), wraplength=460).pack(pady=(0, 10))

        make_btn(body, "Continuar →", self._enviar, color).pack(fill="x", pady=4)
        make_btn(body, "← Volver", lambda: self.master.mostrar(MenuPrincipal),
                 GRAY).pack(fill="x", pady=4)

        self.ent_user.focus()

    def _enviar(self):
        user = self.ent_user.get().strip()
        pw   = self.ent_pass.get().strip()
        if not user or not pw:
            self.error_var.set("Por favor ingresa usuario y contraseña.")
            return
        self.error_var.set("Conectando...")
        self.update()
        threading.Thread(target=self._conectar, args=(user, pw), daemon=True).start()

    def _conectar(self, user, pw):
        try:
            sd = conectar(self.master.host)
            enviar(sd, f"{self.opcion}{user};{pw}")

            resp = recibir(sd)

            if self.opcion == "1":
                sd.close()
                self.after(0, lambda: self._msg_registro(resp))
            else:
                if resp == "-1":
                    sd.close()
                    self.after(0, lambda: self.error_var.set(
                        "Usuario o contraseña incorrectos."))
                else:
                    self.master.sd = sd
                    l = int(resp)
                    self.after(0, lambda: self.master.mostrar(PantallaJuego, l=l))
        except Exception as ex:
            self.after(0, lambda: self.error_var.set(f"Error: {ex}"))

    def _msg_registro(self, msg):
        self.error_var.set("")
        top = tk.Toplevel(self, bg=BG)
        top.title("Registro")
        top.geometry("360x200")
        top.resizable(False, False)
        top.grab_set()
        tk.Frame(top, bg=GREEN, height=3).pack(fill="x")
        tk.Label(top, text="✔ " + msg, bg=BG, fg=GREEN,
                 font=(FONT_MONO, 12, "bold"), wraplength=320,
                 justify="center").pack(expand=True)
        make_btn(top, "Volver al menú", lambda: (top.destroy(),
                 self.master.mostrar(MenuPrincipal)), GREEN).pack(pady=16, padx=40, fill="x")


# ─── Pantalla de juego ─────────────────────────────────────────────────── #

class PantallaJuego(tk.Frame):
    def __init__(self, master, l):
        super().__init__(master, bg=BG)
        self.l = l
        self.intentos = 0
        self.aciertos = ['0'] * l
        self.palabra_mask = ['?'] * l
        self.letras_incorrectas = []
        self.letras_intentadas = set()
        self.msg_var  = tk.StringVar()
        self.juego_terminado = False
        self._build()
        self.ent_letra.focus()

    # ── Construcción de la UI ──

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG2, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="=== AHORCADO ===", bg=BG2, fg=CYAN,
                 font=(FONT_MONO, 16, "bold")).pack()
        tk.Frame(self, bg=CYAN, height=2).pack(fill="x")

        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=20, pady=10)

        # Columna izquierda: ahorcado + vidas
        left = tk.Frame(content, bg=BG, width=220)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        self.lbl_figura = tk.Label(
            left, text=FIGURAS[0], bg=BG, fg=GRAY,
            font=(FONT_MONO, 13), justify="left", anchor="nw",
        )
        self.lbl_figura.pack(anchor="w", pady=(10, 4))

        self.lbl_vidas = tk.Label(left, text="", bg=BG, fg=GREEN,
                                  font=(FONT_MONO, 13))
        self.lbl_vidas.pack(anchor="w")

        # Columna derecha: palabra + letras + input
        right = tk.Frame(content, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", pady=(8, 12))

        # Palabra oculta
        self.lbl_palabra = tk.Label(
            right, text="", bg=BG, fg=WHITE,
            font=(FONT_MONO, 26, "bold"), anchor="center",
            letterSpacing=6 if hasattr(tk.Label, "letterSpacing") else None,
        )
        self.lbl_palabra.pack(fill="x", pady=(0, 12))

        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", pady=(0, 12))

        # Letras
        row_c = tk.Frame(right, bg=BG)
        row_c.pack(fill="x", pady=2)
        tk.Label(row_c, text="Correctas  :", bg=BG, fg=GREEN,
                 font=(FONT_MONO, 10, "bold")).pack(side="left")
        self.lbl_correctas = tk.Label(row_c, text="(ninguna)", bg=BG, fg=GREEN,
                                      font=(FONT_MONO, 10))
        self.lbl_correctas.pack(side="left", padx=6)

        row_i = tk.Frame(right, bg=BG)
        row_i.pack(fill="x", pady=2)
        tk.Label(row_i, text="Incorrectas:", bg=BG, fg=RED,
                 font=(FONT_MONO, 10, "bold")).pack(side="left")
        self.lbl_incorrectas = tk.Label(row_i, text="(ninguna)", bg=BG, fg=RED,
                                        font=(FONT_MONO, 10))
        self.lbl_incorrectas.pack(side="left", padx=6)

        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", pady=10)

        # Mensaje extra
        self.lbl_msg = tk.Label(
            right, textvariable=self.msg_var, bg=BG, fg=AMBER,
            font=(FONT_MONO, 10, "bold"), anchor="w", wraplength=340,
        )
        self.lbl_msg.pack(fill="x", pady=(0, 8))

        # Input
        row_inp = tk.Frame(right, bg=BG)
        row_inp.pack(fill="x")
        tk.Label(row_inp, text="Letra o palabra:", bg=BG, fg=WHITE_DIM,
                 font=(FONT_MONO, 10)).pack(side="left", pady=4)

        ef, self.ent_letra = make_entry(right)
        ef.pack(fill="x", pady=4)
        self.ent_letra.bind("<Return>", lambda e: self._intentar())

        self.btn_intentar = make_btn(right, "Adivinar →", self._intentar, CYAN)
        self.btn_intentar.pack(fill="x", pady=4)

        # Resultado final (oculto inicialmente)
        self.frm_fin = tk.Frame(right, bg=BG)
        self.lbl_resultado = tk.Label(
            self.frm_fin, text="", bg=BG, fg=GREEN,
            font=(FONT_MONO, 16, "bold"), anchor="center",
        )
        self.lbl_resultado.pack(fill="x", pady=6)
        make_btn(self.frm_fin, "Jugar de nuevo", self._jugar_nuevo, GREEN).pack(fill="x", pady=3)
        make_btn(self.frm_fin, "Salir al menú", self._salir_menu, GRAY).pack(fill="x", pady=3)

        self._actualizar_ui()

    # ── Lógica ──

    def _actualizar_ui(self):
        # Figura
        color_fig = RED if self.intentos > 0 else GRAY
        self.lbl_figura.config(text=FIGURAS[self.intentos], fg=color_fig)

        # Vidas
        vidas_txt = "♥ " * (5 - self.intentos) + "♡ " * self.intentos
        self.lbl_vidas.config(text=vidas_txt)

        # Palabra
        tokens = []
        for i in range(self.l):
            tokens.append(self.palabra_mask[i].upper() if self.aciertos[i] == '1' else '_')
        self.lbl_palabra.config(text="  ".join(tokens))

        # Letras correctas
        vistas = set()
        correctas = []
        for i in range(self.l):
            if self.aciertos[i] == '1':
                ch = self.palabra_mask[i].upper()
                if ch not in vistas:
                    correctas.append(ch)
                    vistas.add(ch)
        self.lbl_correctas.config(
            text="  ".join(correctas) if correctas else "(ninguna)")

        # Letras incorrectas
        self.lbl_incorrectas.config(
            text="  ".join(l.upper() for l in self.letras_incorrectas)
            if self.letras_incorrectas else "(ninguna)")

    def _intentar(self):
        if self.juego_terminado:
            return
        texto = self.ent_letra.get().strip().lower()
        self.ent_letra.delete(0, "end")
        if not texto:
            return

        es_letra_sola = len(texto) == 1

        if es_letra_sola and texto in self.letras_intentadas:
            self.msg_var.set(f">> Letra '{texto.upper()}' ya intentada, prueba otra.")
            self.lbl_msg.config(fg=AMBER)
            return

        if es_letra_sola:
            self.letras_intentadas.add(texto)

        threading.Thread(
            target=self._enviar_intento,
            args=(texto, es_letra_sola),
            daemon=True,
        ).start()

    def _enviar_intento(self, texto, es_letra_sola):
        try:
            prev_aciertos = self.aciertos.count('1')
            enviar(self.master.sd, texto)
            resp = recibir(self.master.sd)

            curr_aciertos = 0
            for i in range(self.l):
                if resp[i] == '1':
                    curr_aciertos += 1
                    if self.aciertos[i] == '0' and es_letra_sola:
                        self.palabra_mask[i] = texto
                    self.aciertos[i] = '1'

            if not es_letra_sola and curr_aciertos == self.l:
                for i in range(min(self.l, len(texto))):
                    self.palabra_mask[i] = texto[i]

            gano = (curr_aciertos == self.l)

            if curr_aciertos > prev_aciertos:
                msg = f">> ¡Correcto! +{curr_aciertos - prev_aciertos} letra(s)"
                msg_color = GREEN
            else:
                self.intentos += 1
                if es_letra_sola and texto not in self.letras_incorrectas:
                    self.letras_incorrectas.append(texto)
                msg = f">> ¡Fallo! ({self.intentos}/5)"
                msg_color = RED

            self.after(0, lambda: self._post_intento(msg, msg_color, gano))
        except Exception as ex:
            self.after(0, lambda: self.msg_var.set(f"Error de red: {ex}"))

    def _post_intento(self, msg, msg_color, gano):
        self.msg_var.set(msg)
        self.lbl_msg.config(fg=msg_color)
        self._actualizar_ui()

        if gano:
            self._fin(True)
        elif self.intentos >= 5:
            self._fin(False)

    def _fin(self, gano):
        self.juego_terminado = True
        self.btn_intentar.pack_forget()
        if gano:
            self.lbl_resultado.config(text="★  ¡GANASTE!  ★", fg=GREEN)
        else:
            self.lbl_resultado.config(text="✗  ¡PERDISTE! (5 fallos)", fg=RED)
        self.frm_fin.pack(fill="x", pady=8)

    def _jugar_nuevo(self):
        threading.Thread(target=self._pedir_nueva, daemon=True).start()

    def _pedir_nueva(self):
        try:
            enviar(self.master.sd, "y")
            resp = recibir(self.master.sd)
            l = int(resp)
            self.after(0, lambda: self.master.mostrar(PantallaJuego, l=l))
        except Exception as ex:
            self.after(0, lambda: self.msg_var.set(f"Error: {ex}"))

    def _salir_menu(self):
        try:
            enviar(self.master.sd, "n")
            self.master.sd.close()
        except Exception:
            pass
        self.master.sd = None
        self.master.mostrar(MenuPrincipal)


# ─── Acerca de / Instrucciones ─────────────────────────────────────────── #

class PantallaAcercaDe(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG2, pady=20)
        hdr.pack(fill="x")
        tk.Label(hdr, text="=== ACERCA DE ===", bg=BG2, fg=AMBER,
                 font=(FONT_MONO, 18, "bold")).pack()
        tk.Frame(self, bg=AMBER, height=2).pack(fill="x")

        # Canvas con scroll
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview,
                          bg=BG3, troughcolor=BG2, activebackground=CYAN)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG, padx=40)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=canvas.winfo_width())
        inner.bind("<Configure>", _resize)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

        def _scroll(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _scroll)

        def sec(title, color=AMBER):
            tk.Frame(inner, bg=BG, height=12).pack()
            tk.Label(inner, text=title, bg=BG, fg=color,
                     font=(FONT_MONO, 13, "bold"), anchor="w").pack(fill="x")
            tk.Frame(inner, bg=color, height=1).pack(fill="x", pady=(2, 8))

        def row(text, color=WHITE_DIM, indent=0):
            tk.Label(inner, text=(" " * indent) + text, bg=BG, fg=color,
                     font=(FONT_MONO, 11), anchor="w", justify="left",
                     wraplength=500).pack(fill="x", pady=1)

        # ─ 1. Integrantes ─
        sec("1. Integrantes del equipo")
        row("▸  Jaime Rincón Burboa",              WHITE)
        row("▸  Álvaro Samuel Velázquez Ramírez",  WHITE)
        row("▸  José Pablo Soto Sánchez",           WHITE)
        tk.Frame(inner, bg=BG, height=8).pack()
        row("Materia  :  Cómputo Distribuido",  CYAN)
        row("Profesor :  Juan Carlos López Pimentel", CYAN)

        # ─ 2. Instrucciones ─
        sec("2. Instrucciones del juego")

        row("Cómo se juega:", WHITE, 0)
        row("El servidor elige una palabra secreta al azar.", WHITE_DIM, 2)
        row("Puedes adivinarla de dos formas:", WHITE_DIM, 2)
        row("a) Escribiendo una sola letra por turno.", WHITE_DIM, 4)
        row("b) Escribiendo la palabra completa de una sola vez.", WHITE_DIM, 4)
        tk.Frame(inner, bg=BG, height=8).pack()

        row("Cómo se gana:", GREEN, 0)
        row("• Descubriendo todas las letras antes de 5 errores.", WHITE_DIM, 2)
        row("• O escribiendo la palabra completa correctamente.", WHITE_DIM, 2)
        tk.Frame(inner, bg=BG, height=8).pack()

        row("Cómo se pierde:", RED, 0)
        row("• Acumulando 5 fallos (letras o palabras incorrectas).", WHITE_DIM, 2)
        row("• Cada fallo dibuja una parte del ahorcado.", WHITE_DIM, 2)
        tk.Frame(inner, bg=BG, height=8).pack()

        row("Reglas adicionales:", AMBER, 0)
        row("• Las letras no distinguen mayúsculas/minúsculas.", WHITE_DIM, 2)
        row("• Si repites una letra, se avisa sin penalización.", WHITE_DIM, 2)
        row("• Al terminar, puedes jugar de nuevo con otra palabra.", WHITE_DIM, 2)

        # ─ Ahorcado decorativo ─
        tk.Frame(inner, bg=BG, height=20).pack()
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x")
        tk.Label(inner, text=FIGURAS[5], bg=BG, fg=GRAY,
                 font=(FONT_MONO, 11), justify="left").pack(anchor="center", pady=14)
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x")
        tk.Frame(inner, bg=BG, height=20).pack()

        make_btn(inner, "← Volver al menú",
                 lambda: self.master.mostrar(MenuPrincipal), AMBER).pack(fill="x", pady=12)


# ═══════════════════════════════════════════════════════════════════════════ #
#  PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════ #

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Uso: python3 {sys.argv[0]} <host>")
        sys.exit(1)

    app = App(sys.argv[1])
    app.mainloop()