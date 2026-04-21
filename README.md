# Ahorcado TCP

Juego del Ahorcado implementado sobre una arquitectura cliente-servidor TCP. Varios jugadores pueden conectarse simultáneamente; cada uno corre su propia sesión de forma independiente. Existe autenticación con usuario y contraseña que se guarda en el servidor: primero se crea una cuenta y luego se puede iniciar sesión con ella.

---

## Integrantes

- Álvaro Samuel Velázquez Ramírez — 0262147
- José Pablo Soto Sánchez — 0262205
- Jaime Rincón Burboa — 0260590

---

## Lenguajes de programación

**C — Servidor**

El uso de C en el servidor permite obtener alto rendimiento y control preciso sobre los recursos del sistema, lo cual es fundamental en una arquitectura cliente-servidor con múltiples conexiones simultáneas. Al trabajar directamente con sockets y memoria, se reduce el consumo de CPU y RAM, y se pueden implementar mecanismos eficientes de concurrencia mediante `fork()`, lo que hace al servidor más escalable. Aunque requiere mayor cuidado en la programación, ofrece una base robusta para manejar múltiples sesiones de juego de forma independiente.

**Python — Cliente**

El cliente en Python usa **Tkinter** para presentar una interfaz gráfica (GUI) de escritorio. Tkinter viene incluido en la instalación estándar de Python, por lo que no se requieren dependencias externas. La comunicación con el servidor se maneja en hilos (`threading`) para que la UI nunca se bloquee mientras espera respuesta de red.

---

## Cómo se juega

Al conectarse, el jugador puede crear una cuenta nueva o iniciar sesión. Sin credenciales válidas no se puede jugar.

Una vez autenticado, el servidor elige una palabra aleatoria y el jugador debe adivinarla:

- Escribe **una letra** para intentarla.
- Escribe **la palabra completa** para adivinarla en un solo intento.
- Si aciertas, la letra se revela en su posición.
- Si fallas, se acumula un error y se dibuja una parte del ahorcado.
- **Máximo 5 fallos** antes de perder.
- Las letras ya intentadas se detectan en el cliente y avisan **sin contar como fallo**.
- Las letras no distinguen entre mayúsculas y minúsculas.

Al terminar cada ronda (victoria o derrota) puedes pedir una nueva palabra sin desconectarte.

---

## Requisitos

| Componente | Requisito |
|---|---|
| Servidor | GCC, Linux/macOS o WSL2 en Windows |
| Cliente | Python 3.x con Tkinter (incluido por defecto) |
| Puerto | TCP **5000** |

> **Windows:** el servidor usa `fork()` y sockets POSIX, por lo que debe compilarse y ejecutarse dentro de **WSL2** (Ubuntu). El cliente Python puede correr en Windows nativo o también dentro de WSL2.

---

## Compilación

```bash
# Servidor (Linux / macOS / WSL2)
cc tcpServer.c -o tcpserver
```

---

## Ejecución

**1. Crear el archivo de usuarios** (solo la primera vez):

```bash
touch users
```

**2. Iniciar el servidor:**

```bash
./tcpserver
```

**3. Conectar el cliente** (en otra terminal):

```bash
python tcpClient.py <host>

# Ejemplo local
python tcpClient.py 127.0.0.1
```

Se abrirá una ventana gráfica de 1024×768 con el menú principal.

Para simular múltiples jugadores, abre varias terminales y ejecuta el cliente en cada una. El servidor crea un proceso hijo independiente por conexión mediante `fork()`.

---

## Interfaz gráfica (cliente)

La interfaz está construida con **Tkinter** y presenta las siguientes pantallas:

| Pantalla | Descripción |
|---|---|
| **Menú principal** | Opciones: Iniciar sesión, Crear usuario, Instrucciones, Salir |
| **Login / Registro** | Formulario de usuario y contraseña con validación |
| **Pantalla de juego** | Ahorcado ASCII, palabra oculta, letras correctas/incorrectas, contador de vidas |
| **Acerca de** | Instrucciones del juego con scroll |

La ventana es de tamaño fijo (no redimensionable) y usa una paleta de colores oscura con acentos en cian, verde y ámbar.

---

## Características técnicas

| Característica | Detalle |
|---|---|
| Protocolo | TCP (`SOCK_STREAM`) — modo conexión |
| Puerto | 5000 |
| Concurrencia | `fork()` por cada cliente aceptado |
| Autenticación | Login y registro persistidos en archivo `users` |
| Interfaz | GUI Tkinter, ventana 1024×768, tema oscuro con colores ANSI |
| Threading | Operaciones de red en hilo separado para no bloquear la UI |
| Letras repetidas | Detectadas en el cliente, sin consumir turno |
| Multironda | Nueva palabra sin desconectarse |

---

## Estructura del proyecto

```
.
├── tcpServer.c         # Servidor: lógica del juego, fork, autenticación
├── ahorcado_client.py  # Cliente: interfaz gráfica Tkinter
└── users               # Base de usuarios (se crea en tiempo de ejecución)
```

---

## Protocolo de comunicación

```
Cliente (Python/Tkinter)           Servidor (C)
  │                                    │
  │── opcion + "usuario;contraseña" ──►│   opcion: "0"=login, "1"=registro
  │◄── longitud de palabra ────────────│   (o "-1" si falla login)
  │                                    │
  │  [bucle de juego]                  │
  │── letra o palabra ────────────────►│
  │◄── string de 0s y 1s ──────────────│   posiciones acertadas (ej: "01001")
  │                                    │
  │── "y" / "n" (otra ronda) ─────────►│
  │◄── longitud de nueva palabra ──────│   solo si se envió "y"
```

### Notas del protocolo

- Cada mensaje se termina con un byte nulo (`\0`) para delimitar el fin del paquete.
- El cliente usa `sendall()` para garantizar el envío completo y acumula chunks en un buffer hasta recibir el `\0`.
- Para el **registro** (`"1"`), el cliente cierra el socket inmediatamente tras recibir la confirmación del servidor — no inicia partida.
- Para el **login** (`"0"`), si la respuesta es distinta de `"-1"`, se interpreta directamente como la longitud de la primera palabra y comienza la partida.