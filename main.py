from flask import Flask, render_template_string
from sklearn.ensemble import IsolationForest
import numpy as np
import threading
import socket
import json
import math
import random
import csv
import os
import rsa
from datetime import datetime

app = Flask(__name__)
ARCHIVO_CSV = "registro_auditoria_ia.csv"

# --- CARGAR LA CLAVE PÚBLICA (RSA) ---
try:
    with open("clave_publica.pem", "rb") as f:
        CLAVE_PUBLICA = rsa.PublicKey.load_pkcs1(f.read())
except FileNotFoundError:
    print("❌ ERROR: No se encuentra el archivo 'clave_publica.pem'.")
    exit()


# --- FUNCIONES MATEMÁTICAS ---
def calcular_entropia_shannon(datos):
    if not datos: return 0.0
    frecuencias = {c: datos.count(c) for c in set(datos)}
    return sum(- (f / len(datos)) * math.log2(f / len(datos)) for f in frecuencias.values())


def calcular_varianza_entropia(datos, tamano_bloque=64):
    if len(datos) < tamano_bloque: return 0.0
    entropias_bloques = []
    for i in range(0, len(datos), tamano_bloque):
        bloque = datos[i:i + tamano_bloque]
        if len(bloque) == tamano_bloque:
            entropias_bloques.append(calcular_entropia_shannon(bloque))
    return np.var(entropias_bloques) if entropias_bloques else 0.0


# --- REGISTRO FORENSE ---
def guardar_en_csv(entropia, varianza, tamano, es_anomalia):
    es_nuevo = not os.path.exists(ARCHIVO_CSV)

    with open(ARCHIVO_CSV, mode='a', newline='', encoding='utf-8') as archivo:
        writer = csv.writer(archivo)
        if es_nuevo:
            writer.writerow(["Marca_de_Tiempo", "Entropia_Global", "Varianza_Caos", "Tamano_Bytes", "Veredicto_IA"])

        veredicto = "MALWARE (Bloqueado)" if es_anomalia else "LEGÍTIMO (Permitido)"
        tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([tiempo, f"{entropia:.4f}", f"{varianza:.4f}", tamano, veredicto])


# --- ENTRENAMIENTO DE LA IA ---
print("[⚙️] Generando dataset y entrenando Isolation Forest...")
datos_entrenamiento = []
for _ in range(1000):
    e_global = random.uniform(6.5, 7.9)
    e_varianza = random.uniform(0.0, 0.05)
    tamano = random.randint(1000, 50000)
    datos_entrenamiento.append([e_global, e_varianza, tamano])

modelo_ia = IsolationForest(contamination=0.01, random_state=42)
modelo_ia.fit(datos_entrenamiento)
print("[✅] Modelo IA entrenado. Frontera de decisión lista.")

# --- DASHBOARD WEB ---
estado = {
    "status": "ESPERANDO CONEXIÓN...", "color": "#2c3e50", "mensaje": "Conecta un dispositivo.",
    "e_global": "0.00", "e_varianza": "0.00", "tamano": "0"
}

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="1">
<style>
    body { font-family: 'Segoe UI', sans-serif; text-align: center; color: white; background-color: {{ color }}; padding: 20px; transition: 0.3s;}
    .card { background: rgba(0,0,0,0.7); padding: 30px; border-radius: 15px; display: inline-block; max-width: 90%; width: 450px;}
    .metricas { background: #111; padding: 15px; border-radius: 10px; margin-top: 20px; text-align: left; font-family: monospace; font-size: 1.1em;}
</style></head><body>
    <div class="card">
        <h3>🧠 AI BEHAVIORAL SHIELD</h3>
        <h1>{{ status }}</h1><p>{{ mensaje }}</p>
        <div class="metricas">
            ▸ Entropía Global:  <b>{{ e_global }}</b> bits/b<br>
            ▸ Varianza (Caos):  <b style="color:yellow;">{{ e_varianza }}</b><br>
            ▸ Tamaño Payload: <b>{{ tamano }}</b> Bytes
        </div>
    </div>
</body></html>
"""


@app.route('/')
def index(): return render_template_string(HTML, **estado)


# --- INTERCEPTOR USB ---
def motor_escudo_usb():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5000))
    server.listen(5)

    while True:
        conn, addr = server.accept()
        f = conn.makefile('r', encoding='utf-8')

        # 1. EL ESCUDO TOMA LA INICIATIVA: ENVÍA EL DESAFÍO (NONCE)
        nonce = os.urandom(16).hex()
        desafio = {"type": "challenge", "nonce": nonce}
        try:
            conn.send((json.dumps(desafio) + "\n").encode('utf-8'))
        except Exception:
            continue

        while True:
            try:
                linea = f.readline()
                if not linea: break
                paquete = json.loads(linea)

                # 2. CAPA CRIPTOGRÁFICA ASIMÉTRICA: Verificar el Desafío
                if paquete.get('type') == "response":
                    firma_recibida_hex = paquete.get('signature', '')

                    try:
                        # Convertimos de hexadecimal a bytes crudos
                        firma_recibida = bytes.fromhex(firma_recibida_hex)

                        # rsa.verify salta un error si la firma no es de la clave privada real
                        rsa.verify(nonce.encode('utf-8'), firma_recibida, CLAVE_PUBLICA)

                        estado.update({"status": "IDENTIDAD CONFIRMADA", "color": "#27ae60",
                                       "mensaje": "Desafío RSA superado. Canal de datos preparado."})
                    except (rsa.VerificationError, ValueError):
                        estado.update({"status": "BLOQUEO HARDWARE", "color": "#c0392b",
                                       "mensaje": "Firma RSA inválida o clonada. Conexión destruida."})
                        break  # Cierra el socket

                # 3. CAPA DE MACHINE LEARNING: Análisis estructural del tráfico
                elif paquete.get('type') == "data_transfer":
                    payload = paquete.get('payload', '')

                    e_global = calcular_entropia_shannon(payload)
                    e_varianza = calcular_varianza_entropia(payload)
                    tamano = len(payload)

                    estado.update({"e_global": f"{e_global:.2f}", "e_varianza": f"{e_varianza:.2f}", "tamano": tamano})

                    # INFERENCIA DEL MACHINE LEARNING
                    vector = np.array([[e_global, e_varianza, tamano]])
                    es_anomalo = (modelo_ia.predict(vector)[0] == -1)

                    # GUARDAMOS EL DATO EMPÍRICO EN EL EXCEL/CSV
                    guardar_en_csv(e_global, e_varianza, tamano, es_anomalo)

                    if es_anomalo:
                        estado.update({"status": "¡AMENAZA AISLADA!", "color": "#8e44ad",
                                       "mensaje": "La IA detectó una anomalía estructural. Conexión destruida."})
                        break
                    else:
                        estado.update({"status": "TRÁFICO LIMPIO", "color": "#2980b9",
                                       "mensaje": "El modelo clasifica los datos como consistentes y seguros."})
            except Exception as e:
                break


if __name__ == "__main__":
    threading.Thread(target=motor_escudo_usb, daemon=True).start()
    print("\n[+] DASHBOARD EN VIVO: Abre http://<IP_DE_TU_PC>:8080 en tu móvil.")
    app.run(host='0.0.0.0', port=8080)