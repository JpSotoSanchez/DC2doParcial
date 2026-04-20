
# Ahorcado TCP

Juego del Ahorcado implementado en C sobre una arquitectura cliente-servidor TCP. Varios jugadores pueden conectarse simultáneamente; cada uno corre su propia sesión de forma independiente. Existe una autentificación con usuario y contraseña que se guarda en el servidor, primero se crea una cuenta y luego se puedo iniciar sesión con ella.

---

## Integrantes

- Álvaro Samuel Velázquez Ramírez 0262147
- José Pablo Soto Sánchez 0262205
- Jaime Rincón Burboa 0260590

## Lenguajes de programación

- C para el servidor
El uso de C en el servidor permite obtener un alto rendimiento y un control preciso sobre los recursos del sistema, lo cual es fundamental en una arquitectura cliente-servidor con múltiples conexiones simultáneas. Al trabajar directamente con sockets y memoria, se reduce el consumo de CPU y RAM, y se pueden implementar mecanismos eficientes de concurrencia, lo que hace al servidor más escalable y rápido. Aunque requiere mayor cuidado en la programación, ofrece una base robusta para manejar múltiples sesiones de juego de forma independiente.

- Python para el cliente
El cliente en Python facilita el desarrollo gracias a su sintaxis clara y sus bibliotecas de alto nivel, lo que permite implementar rápidamente la GUI del juego y la interacción con el usuario. No es necesario optimizar tanto el rendimiento como en el servidor, por lo que se prioriza la legibilidad y la portabilidad. 

## Compilación

```bash
# Servidor
cc tcpServer.c -o tcpserver

---

## Ejecución

**1. Iniciar el servidor** (crear el archivo de usuarios si no existe):

```bash
touch users
./tcpserver
```

**2. Conectar clientes** (en terminales separadas):

```bash
./tcpclient <host>

# Ejemplo local
./tcpclient localhost
```

Para simular múltiples jugadores, abre varias terminales y ejecuta `./tcpclient localhost` en cada una. El servidor crea un proceso hijo independiente por conexión.

---

## Cómo se juega

Al conectarse, el jugador puede iniciar sesión o crear una cuenta nueva. Sin credenciales válidas no se puede jugar.

Una vez autenticado, el servidor elige una palabra aleatoria y el jugador debe adivinarla:

- Escribe **una letra** para intentarla.
- Escribe **la palabra completa** para adivinarla de un solo intento.
- Si aciertas, la letra se revela en su posición.
- Si fallas, se acumula un error y aparece una parte del ahorcado.
- **Máximo 5 fallos** antes de perder.
- Las letras ya intentadas se detectan y avisan sin contar como fallo.

Al terminar cada ronda (victoria o derrota) puedes pedir una nueva palabra sin desconectarte.

---

## Características técnicas

| Característica | Detalle |
|---|---|
| Protocolo | TCP (`SOCK_STREAM`) — modo conexión |
| Concurrencia | `fork()` por cada cliente aceptado |
| Autenticación | Login y registro persistidos en archivo `users` |
| Interfaz | ASCII con colores ANSI, ahorcado animado, se adapta al ancho del terminal |
| Letras repetidas | Detectadas en el cliente, sin consumir turno |
| Multironda | Nueva palabra sin desconectarse |

---

## Estructura del proyecto

```
.
├── tcpServer.c   # Servidor: lógica del juego, fork, autenticación
├── tcpClient.c   # Cliente: interfaz ASCII interactiva
└── users         # Base de usuarios (se crea en tiempo de ejecución)
```

---

## Protocolo de comunicación

```
Cliente                        Servidor
  │                               │
  │── "0" (login) ──────────────► │
  │── "usuario;contraseña" ─────► │
  │◄── longitud de palabra ───────│  (o "-1" si falla)
  │                               │
  │  [bucle de juego]             │
  │── letra o palabra ──────────► │
  │◄── string de 0s y 1s ─────────│  (posiciones acertadas)
  │                               │
  │── "y" / "n" (otra ronda) ───► │
```
