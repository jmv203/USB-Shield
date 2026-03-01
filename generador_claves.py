# generador_claves.py
import rsa

print("Generando par de claves RSA industriales...")
clave_publica, clave_privada = rsa.newkeys(512)

with open("clave_publica.pem", "wb") as f:
    f.write(clave_publica.save_pkcs1())

with open("clave_privada.pem", "wb") as f:
    f.write(clave_privada.save_pkcs1())

print("✅ Claves generadas. ")
print("⚠️ IMPORTANTE: Pasa el archivo 'clave_privada.pem' a tu PORTÁTIL (Atacante).")
print("El PC (Escudo) solo necesita la 'clave_publica.pem'.")