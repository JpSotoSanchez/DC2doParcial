/*
   Compilacion: cc tcpClientRead.c -o tcpclient
   Ejecucion: ./tcpclient <host>
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <netdb.h>
#include <stdbool.h>
#include <sys/ioctl.h>
#include <ctype.h>

#define  DIRSIZE    2048
#define  PUERTO     1234

/* ─── Utilidades de terminal ─────────────────────────────────────────────── */

int anchoTerminal() {
    struct winsize w;
    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &w) == 0 && w.ws_col > 0)
        return w.ws_col;
    return 80; /* fallback */
}

void limpiarPantalla() {
    printf("\033[2J\033[H");
    fflush(stdout);
}

// Cambian el color de lo que se imprime
void colorVerde() { printf("\033[32m"); }
void colorRojo() { printf("\033[31m"); }
void colorAmarillo() { printf("\033[33m"); }
void colorCian() { printf("\033[36m"); }
void colorGris() { printf("\033[90m"); }
void colorReset() { printf("\033[0m"); }
void negrita() { printf("\033[1m"); }

void imprimirLinea(char c, int n) {
    for (int i = 0; i < n; i++) putchar(c);
    putchar('\n');
}

void centrar(const char* texto, int ancho) {
    int len = strlen(texto);
    int pad = (ancho - len) / 2;
    if (pad < 0) pad = 0;
    printf("%*s%s\n", pad, "", texto);
}

/* ─── Arte ASCII del ahorcado ────────────────────────────────────────────── */

/*
 * 6 etapas (0 = ninguna parte, 5 = completo).
 * Usamos una representación compacta: cada etapa agrega partes.
 * El dibujo se escala horizontalmente según el ancho del terminal.
 */
void dibujarAhorcado(int errores, int ancho) {
    /* Partes:
     *  errores 0 → nada
     *  errores 1 → cabeza
     *  errores 2 → cuerpo
     *  errores 3 → brazo izq
     *  errores 4 → brazo der
     *  errores 5 → pierna izq + der
     */

     /* Calcular padding lateral para centrar el dibujo (ancho fijo ~13 chars) */
    int dibAncho = 13;
    int pad = (ancho - dibAncho) / 2;
    if (pad < 0) pad = 0;
    char P[64];
    snprintf(P, sizeof(P), "%*s", pad, "");

    colorGris();

    /* Poste */
    printf("%s  +---+\n", P);
    printf("%s  |   |\n", P);

    /* Cabeza */
    if (errores >= 1) {
        colorRojo();
        printf("%s  |  (o_o)\n", P);
        colorGris();
    }
    else {
        printf("%s  |\n", P);
    }

    /* Cuerpo + brazos */
    if (errores >= 4) {
        colorRojo();
        printf("%s  | \\(|)/\n", P);
        colorGris();
    }
    else if (errores == 3) {
        colorRojo();
        printf("%s  | \\(|\n", P);
        colorGris();
    }
    else if (errores == 2) {
        colorRojo();
        printf("%s  |  (|\n", P);
        colorGris();
    }
    else {
        printf("%s  |\n", P);
    }

    /* Piernas */
    if (errores >= 5) {
        colorRojo();
        printf("%s  | / \\\n", P);
        colorGris();
    }
    else {
        printf("%s  |\n", P);
    }

    /* Base */
    printf("%s  |\n", P);
    printf("%s__|__\n", P);
    colorReset();
}

/* ─── Entrada ────────────────────────────────────────────────────────────── */

void leerInput(char* buffer, int size) {
    fgets(buffer, size, stdin);
    buffer[strcspn(buffer, "\n")] = '\0';
}

/* ─── Tablero principal ──────────────────────────────────────────────────── */

void mostrarTablero(
    char* aciertos,
    char* palabra_mask,
    int   l,
    int   intentos,
    char* letrasIncorrectas,
    int   numIncorrectas,
    int   ancho
) {
    limpiarPantalla();

    negrita(); colorCian();
    centrar("=== AHORCADO ===", ancho);
    colorReset();

    imprimirLinea('-', ancho);

    /* Dibujo del ahorcado */
    dibujarAhorcado(intentos, ancho);
    putchar('\n');

    imprimirLinea('-', ancho);

    /* Palabra con huecos */
    {
        /* Construir string de la palabra para centrarla */
        char linea[512] = { 0 };
        for (int i = 0; i < l; i++) {
            if (aciertos[i] == '1') {
                char tmp[4];
                snprintf(tmp, sizeof(tmp), "%c ", toupper((unsigned char)palabra_mask[i]));
                strncat(linea, tmp, sizeof(linea) - strlen(linea) - 1);
            }
            else {
                strncat(linea, "_ ", sizeof(linea) - strlen(linea) - 1);
            }
        }
        /* Quitar espacio final */
        int ll = strlen(linea);
        if (ll > 0 && linea[ll - 1] == ' ') linea[ll - 1] = '\0';

        negrita();
        centrar(linea, ancho);
        colorReset();
    }

    putchar('\n');

    /* Letras correctas */
    {
        bool hayAciertos = false;
        for (int i = 0; i < l; i++) if (aciertos[i] == '1') { hayAciertos = true; break; }

        int pad = (ancho - 40) / 2; if (pad < 0) pad = 0;
        printf("%*s", pad, "");
        colorVerde(); negrita(); printf("Correctas : "); colorReset();
        if (hayAciertos) {
            /* De-duplicar para no repetir la misma letra varias veces */
            bool vistas[256] = { false };
            for (int i = 0; i < l; i++) {
                if (aciertos[i] == '1') {
                    unsigned char ch = toupper((unsigned char)palabra_mask[i]);
                    if (!vistas[ch]) {
                        colorVerde();
                        printf("%c ", ch);
                        colorReset();
                        vistas[ch] = true;
                    }
                }
            }
        }
        else {
            colorGris(); printf("(ninguna)"); colorReset();
        }
        putchar('\n');
    }

    /* Letras incorrectas */
    {
        int pad = (ancho - 40) / 2; if (pad < 0) pad = 0;
        printf("%*s", pad, "");
        colorRojo(); negrita(); printf("Incorrectas: "); colorReset();
        if (numIncorrectas > 0) {
            for (int i = 0; i < numIncorrectas; i++) {
                colorRojo();
                printf("%c ", toupper((unsigned char)letrasIncorrectas[i]));
                colorReset();
            }
        }
        else {
            colorGris(); printf("(ninguna)"); colorReset();
        }
        putchar('\n');
    }

    /* Vidas restantes */
    {
        int pad = (ancho - 40) / 2; if (pad < 0) pad = 0;
        printf("%*s", pad, "");
        printf("Vidas: ");
        for (int i = 0; i < 5 - intentos; i++) { colorVerde(); printf("♥ "); }
        for (int i = 0; i < intentos; i++) { colorGris();  printf("♡ "); }
        colorReset(); putchar('\n');
    }

    imprimirLinea('-', ancho);
}

/* ─── Main ───────────────────────────────────────────────────────────────── */

int main(int argc, char* argv[]) {
    char dir[DIRSIZE];
    int sd;
    struct hostent* hp;
    struct sockaddr_in pin;
    char* host;

    if (argc != 2) {
        fprintf(stderr, "Uso: %s <host>\n", argv[0]);
        exit(1);
    }
    host = argv[1];

    if ((hp = gethostbyname(host)) == 0) { perror("gethostbyname"); exit(1); }

    pin.sin_family = AF_INET;
    pin.sin_addr.s_addr = ((struct in_addr*)(hp->h_addr))->s_addr;
    pin.sin_port = htons(PUERTO);

    if ((sd = socket(AF_INET, SOCK_STREAM, 0)) == -1) { perror("socket");  exit(1); }
    if (connect(sd, (struct sockaddr*)&pin, sizeof(pin)) == -1) { perror("connect"); exit(1); }

    int ancho = anchoTerminal();
    char buffer[DIRSIZE];

    /* ── Login / Registro ── */
    limpiarPantalla();
    negrita(); colorCian();
    centrar("=== AHORCADO ===", ancho);
    colorReset();
    imprimirLinea('-', ancho);
    printf("  1. Iniciar sesion\n");
    printf("  2. Crear usuario\n");
    printf("  Opcion: ");
    leerInput(buffer, sizeof(buffer));

    char opcion[2];
    strcpy(opcion, (strcmp(buffer, "1") == 0) ? "0" : "1");

    strcpy(dir, opcion);
    if (send(sd, dir, strlen(dir) + 1, 0) == -1) { perror("send"); exit(1); }

    printf("  Usuario    : ");
    char usuario[50];
    leerInput(usuario, sizeof(usuario));

    printf("  Contrasena : ");
    char contrasena[50];
    leerInput(contrasena, sizeof(contrasena));

    snprintf(dir, sizeof(dir), "%s;%s", usuario, contrasena);
    if (send(sd, dir, strlen(dir) + 1, 0) == -1) { perror("send"); exit(1); }

    /* Registro: solo mensaje de confirmacion */
    if (strcmp(opcion, "1") == 0) {
        if (recv(sd, dir, sizeof(dir), 0) == -1) { perror("recv"); exit(1); }
        printf("\n  %s\n", dir);
        close(sd);
        return 0;
    }

    /* Login: recibir longitud de palabra o error */
    if (recv(sd, dir, sizeof(dir), 0) == -1) { perror("recv"); exit(1); }

    if (strcmp(dir, "-1") == 0) {
        colorRojo();
        printf("\n  Usuario o contrasena incorrectos.\n");
        colorReset();
        close(sd);
        return 0;
    }

    /* ── Bucle de juego ── */
    bool jugando = true;
    while (jugando) {
        ancho = anchoTerminal(); /* re-leer por si cambio el terminal */

        int l = atoi(dir);
        int intentos = 0;

        char aciertos[l + 1];
        memset(aciertos, '0', l);
        aciertos[l] = '\0';

        char palabra_mask[l + 1];
        memset(palabra_mask, '?', l);
        palabra_mask[l] = '\0';

        /* Letras incorrectas ya intentadas (max 26) */
        char letrasIncorrectas[27] = { 0 };
        int  numIncorrectas = 0;

        /* Letras ya intentadas para detectar repeticion */
        bool intentadas[256] = { false };

        mostrarTablero(aciertos, palabra_mask, l, intentos, letrasIncorrectas, numIncorrectas, ancho);

        char mensajeExtra[128] = { 0 };

        while (true) {
            /* Mostrar mensaje extra de la ronda anterior si hay */
            if (strlen(mensajeExtra) > 0) {
                int pad = (ancho - 50) / 2; if (pad < 0) pad = 0;
                printf("%*s%s\n\n", pad, "", mensajeExtra);
                mensajeExtra[0] = '\0';
            }

            printf("  Adivina letra o palabra completa: ");
            leerInput(buffer, sizeof(buffer));

            /* Normalizar a minusculas para comparacion interna */
            char bufferLower[DIRSIZE];
            strncpy(bufferLower, buffer, sizeof(bufferLower));
            for (int i = 0; bufferLower[i]; i++)
                bufferLower[i] = tolower((unsigned char)bufferLower[i]);

            bool esLetraSola = (strlen(bufferLower) == 1);
            char letraIntentada = esLetraSola ? bufferLower[0] : '\0';

            /* Detectar repeticion (solo aplica a letras solas) */
            if (esLetraSola && intentadas[(unsigned char)letraIntentada]) {
                mostrarTablero(aciertos, palabra_mask, l, intentos, letrasIncorrectas, numIncorrectas, ancho);
                colorAmarillo();
                int pad = (ancho - 40) / 2; if (pad < 0) pad = 0;
                printf("%*s  >> Letra '%c' ya intentada antes, intenta otra.\n\n",
                    pad, "", toupper((unsigned char)letraIntentada));
                colorReset();
                continue;
            }

            /* Marcar letra como intentada */
            if (esLetraSola)
                intentadas[(unsigned char)letraIntentada] = true;

            /* Enviar al servidor */
            strcpy(dir, bufferLower);
            if (send(sd, dir, strlen(dir) + 1, 0) == -1) { perror("send"); exit(1); }

            int prevAciertos = 0;
            for (int i = 0; i < l; i++)
                if (aciertos[i] == '1') prevAciertos++;

            /* Recibir respuesta del servidor: string de '0'/'1' de longitud l */
            if (recv(sd, dir, sizeof(dir), 0) == -1) { perror("recv"); exit(1); }

            int currAciertos = 0;
            for (int i = 0; i < l; i++) {
                if (dir[i] == '1') {
                    currAciertos++;
                    if (aciertos[i] == '0') {
                        /* Si fue palabra completa, el servidor ya nos dio todas las posiciones.
                         * Si fue letra, asignamos esa letra. */
                        if (esLetraSola)
                            palabra_mask[i] = letraIntentada;
                        /* Si fue palabra completa, la mascara la llenamos con la
                         * palabra enviada por el usuario caracter a caracter. */
                    }
                    aciertos[i] = '1';
                }
            }

            /* Si fue palabra completa y acerto, llenar la mascara con la palabra */
            if (!esLetraSola && currAciertos == l) {
                for (int i = 0; i < l && bufferLower[i] != '\0'; i++)
                    palabra_mask[i] = bufferLower[i];
            }

            bool gano = (currAciertos == l);

            if (currAciertos > prevAciertos) {
                snprintf(mensajeExtra, sizeof(mensajeExtra),
                    "\033[32m  >> Correcto! +%d letra(s)\033[0m", currAciertos - prevAciertos);
            }
            else {
                intentos++;
                /* Agregar a letras incorrectas (solo si fue letra sola y no ya registrada) */
                if (esLetraSola) {
                    bool yaEnIncorrectas = false;
                    for (int i = 0; i < numIncorrectas; i++)
                        if (letrasIncorrectas[i] == letraIntentada)
                        {
                            yaEnIncorrectas = true; break;
                        }
                    if (!yaEnIncorrectas && numIncorrectas < 26)
                        letrasIncorrectas[numIncorrectas++] = letraIntentada;
                }
                snprintf(mensajeExtra, sizeof(mensajeExtra),
                    "\033[31m  >> Fallo! (%d/5)\033[0m", intentos);
            }

            mostrarTablero(aciertos, palabra_mask, l, intentos, letrasIncorrectas, numIncorrectas, ancho);

            if (gano) {
                negrita(); colorVerde();
                centrar("*** GANASTE! ***", ancho);
                colorReset();
                putchar('\n');
                break;
            }
            if (intentos >= 5) {
                negrita(); colorRojo();
                centrar("*** PERDISTE! (5 fallos) ***", ancho);
                colorReset();
                putchar('\n');
                break;
            }
        }

        /* Pregunta por otra ronda */
        printf("  Jugar de nuevo? (y/n): ");
        leerInput(buffer, sizeof(buffer));
        strcpy(dir, buffer);
        if (send(sd, dir, strlen(dir) + 1, 0) == -1) { perror("send"); exit(1); }

        if (strcmp(buffer, "y") == 0) {
            if (recv(sd, dir, sizeof(dir), 0) == -1) { perror("recv"); exit(1); }
        }
        else {
            jugando = false;
        }
    }

    negrita(); colorCian();
    printf("\n  Gracias por jugar!\n");
    colorReset();
    close(sd);
    return 0;
}