/*
   Compilacion: cc tcpserver.c -lnsl -o tcpserver
   Ejecución: ./tcpserver
*/

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdbool.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <signal.h>
#include <unistd.h>

#define  DIRSIZE    2048
#define  PUERTO     5000
#define  MAX_WORD   100   // longitud maxima de palabra

int                  sd, sd_actual;
// BUG FIX: addrlen debe ser socklen_t, no int, ya que accept() requiere socklen_t*.
// Ademas, no se inicializaba antes de pasarlo a accept(), causando comportamiento
// indefinido (accept podia truncar o ignorar la direccion del cliente).
socklen_t            addrlen;
struct sockaddr_in   sind, pin;

char* palabras[] = {
    "murcielago",
    "xilofono",
    "volcan",
    "terremoto",
    "mariposa",
    "telescopio",
    "laberinto",
    "piramide",
    "quetzal",
    "brujula",
    "fantasma",
    "jitomate",
    "oxigeno",
    "zoologico",
    "valle",
    "eclipse",
    "dragon",
    "cactus",
    "universo",
    "gladiador",
    "tsunami",
    "relampago",
    "cocodrilo",
    "pantano",
    "alquimia",
    "horizonte",
    "biblioteca",
    "cangrejo",
    "vendaval",
    "volcan"
};

char* randomWord() {
    int pos = rand() % 30;
    return palabras[pos];
}

void guess(char* dir, int* aciertos, char* respuesta, char* buffer) {
    if (strlen(dir) == 1) {
        for (int i = 0; i < (int)strlen(respuesta); i++) {
            if (dir[0] == respuesta[i]) aciertos[i] = 1;
        }
    }
    else {
        if (strcmp(dir, respuesta) == 0) {
            for (int i = 0; i < (int)strlen(respuesta); i++) {
                aciertos[i] = 1;
            }
        }
    }

    int i;
    for (i = 0; i < (int)strlen(respuesta); i++) {
        buffer[i] = aciertos[i] + '0';
    }
    buffer[i] = '\0';
}

bool isUser(char dir[]) {
    FILE* pointer = fopen("users", "r");
    if (pointer == NULL) {
        perror("Error opening file");
        exit(1);
    }

    char buffer[100];
    while (fgets(buffer, sizeof(buffer), pointer) != NULL) {
        buffer[strcspn(buffer, "\r\n")] = '\0';

        // Skip blank lines
        if (strlen(buffer) == 0) continue;

        char* saveptr1, * saveptr2;
        char dirCopy[256];
        strcpy(dirCopy, dir);

        char* token = strtok_r(dirCopy, ";", &saveptr1);
        char* filetoken = strtok_r(buffer, ";", &saveptr2);

        bool bandera = true;

        // Both sides must have the same number of fields, all matching
        while (token != NULL || filetoken != NULL) {
            if (token == NULL || filetoken == NULL ||
                strcmp(token, filetoken) != 0) {
                bandera = false;
                break;
            }
            token = strtok_r(NULL, ";", &saveptr1);
            filetoken = strtok_r(NULL, ";", &saveptr2);
        }

        if (bandera) {
            fclose(pointer);
            return true;
        }
    }

    fclose(pointer);
    return false;
}

int addUser(char dir[]) {
    FILE* pointer = fopen("users", "r");
    if (pointer == NULL) {
        perror("Error opening file");
        exit(1);
    }

    char buffer[100];
    while (fgets(buffer, sizeof(buffer), pointer) != NULL) {
        buffer[strcspn(buffer, "\r\n")] = '\0';

        char* saveptr1, * saveptr2;
        char dirCopy[256];
        strcpy(dirCopy, dir);

        char* token = strtok_r(dirCopy, ";", &saveptr1);
        char* filetoken = strtok_r(buffer, ";", &saveptr2);

        if (token != NULL && filetoken != NULL &&
            strcmp(token, filetoken) == 0) {
            fclose(pointer);
            return 1;
        }
    }
    fclose(pointer);

    pointer = fopen("users", "a");
    if (pointer == NULL) {
        perror("Error opening file");
        exit(1);
    }
    fprintf(pointer, "%s\n", dir);
    fclose(pointer);
    return 0;
}

void aborta_handler(int sig) {
    printf("....abortando el proceso servidor %d\n", sig);
    close(sd);
    close(sd_actual);
    exit(1);
}

int main() {
    char dir[DIRSIZE];

    if (signal(SIGINT, aborta_handler) == SIG_ERR) {
        perror("Could not set signal handler");
        return 1;
    }

    if ((sd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
        perror("socket");
        exit(1);
    }

    int opt = 1;
    if (setsockopt(sd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) == -1) {
        perror("setsockopt");
        exit(1);
    }

    sind.sin_family = AF_INET;
    sind.sin_addr.s_addr = INADDR_ANY;
    sind.sin_port = htons(PUERTO);

    if (bind(sd, (struct sockaddr*)&sind, sizeof(sind)) == -1) {
        perror("bind");
        exit(1);
    }

    if (listen(sd, 5) == -1) {
        perror("listen");
        exit(1);
    }

    pid_t child;
    while (true) {
        printf("Waiting for connection\n");
        // BUG FIX: addrlen debe inicializarse ANTES de cada accept().
        // Sin esto, accept() recibe un tamano basura y puede fallar o no
        // llenar pin correctamente.
        addrlen = sizeof(pin);
        if ((sd_actual = accept(sd, (struct sockaddr*)&pin, &addrlen)) == -1) {
            perror("accept");
            exit(1);
        }
        printf("Connection\n");
        child = fork();
        srand(time(NULL));
        if ((int)child == 0) break;
        else close(sd_actual);
    }

    char cond = 't';
    while (cond == 't') {
        if (recv(sd_actual, dir, sizeof(dir), 0) == -1) {
            perror("recv");
            exit(1);
        }

        // INICIO DE SESION
        if (dir[0] == '0') {
            bool status = isUser(dir+1);
            if (status) {
                char* roundWord = randomWord();
                char  len[4];
                char  resultado[MAX_WORD];
                int   l = strlen(roundWord);
                // BUG FIX: el array aciertos se declaraba como VLA (int aciertos[l])
                // y se reutilizaba en partidas siguientes con un nuevo 'l' distinto.
                // Esto causaba desbordamiento de buffer si la nueva palabra era mas
                // larga que la original. Se usa un array de tamano fijo MAX_WORD.
                int   aciertos[MAX_WORD];
                memset(aciertos, 0, sizeof(aciertos));
                int   intentos = 0;
                int   cf = 0;

                printf("Palabra de esta ronda: %s\n", roundWord);

                snprintf(len, sizeof(len), "%d", l);
                strcpy(dir, len);
                if (send(sd_actual, dir, strlen(dir) + 1, 0) == -1) {
                    perror("send");
                    exit(1);
                }

                while (true) {
                    if (recv(sd_actual, dir, sizeof(dir), 0) == -1) {
                        perror("recv");
                        exit(1);
                    }

                    guess(dir, aciertos, roundWord, resultado);
                    strcpy(dir, resultado);
                    if (send(sd_actual, dir, strlen(dir) + 1, 0) == -1) {
                        perror("send");
                        exit(1);
                    }

                    int c = 0;
                    for (int i = 0; i < l; i++) {
                        c += aciertos[i];
                    }

                    if (c <= cf) intentos++;
                    cf = c;

                    if (c == l || intentos >= 5) {
                        if (recv(sd_actual, dir, sizeof(dir), 0) == -1) {
                            perror("recv");
                            exit(1);
                        }

                        if (strcmp(dir, "y") == 0) {
                            roundWord = randomWord();
                            l = strlen(roundWord);
                            memset(aciertos, 0, sizeof(aciertos));
                            intentos = 0;
                            cf = 0;

                            printf("Palabra de esta ronda: %s\n", roundWord);

                            snprintf(len, sizeof(len), "%d", l);
                            strcpy(dir, len);
                            if (send(sd_actual, dir, strlen(dir) + 1, 0) == -1) {
                                perror("send");
                                exit(1);
                            }
                        }
                        if (strcmp(dir, "n") == 0) {
                            cond = 'f';
                            break;
                        }
                    }
                }
            }
            else {
                strcpy(dir, "-1");
                if (send(sd_actual, dir, strlen(dir) + 1, 0) == -1) {
                    perror("send");
                    exit(1);
                }
                cond = 'f';
            }
        }

        // CREAR USUARIO
        else if (dir[0] == '1') {

            int status = addUser(dir+1);
            if (status == 0) strcpy(dir, "Usuario Agregado");
            else             strcpy(dir, "Usuario ya Existe");

            if (send(sd_actual, dir, strlen(dir) + 1, 0) == -1) {
                perror("send");
                exit(1);
            }
        }
        else cond = 'f';
    }

    close(sd_actual);
    close(sd);
    printf("Conexion cerrada\n");
    return 0;
}
