import os
import sys
import hashlib
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# === 1️⃣  Your predefined strings ===
certificate_string = "-----BEGIN CERTIFICATE-----\nMIIDWTCCAkGgAwIBAgIUXXAkRUudo3v1TUQOW2xDNJrf7B4wDQYJKoZIhvcNAQEL\nBQAwTTFLMEkGA1UECwxCQW1hem9uIFdlYiBTZXJ2aWNlcyBPPUFtYXpvbi5jb20g\nSW5jLiBMPVNlYXR0bGUgU1Q9V2FzaGluZ3RvbiBDPVVTMB4XDTI1MTAwNTEwNDgw\nNVoXDTQ5MTIzMTIzNTk1OVowHjEcMBoGA1UEAwwTQVdTIElvVCBDZXJ0aWZpY2F0\nZTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALc1Jxhmp9fjak5r+Cuo\nN4B0SB+eUCb/3C3SK22Fd4zC7E6KNNBaspF4rXrng55FJsIgVwEAy9QhNfxiy5Bo\nKwzT8usMEiUXxOL6Hx4bRU4GSYq1sJMZG1PwdzFZVceCoaukqgL+AcpknSCCbdVP\n6ZMoiZK1whgbrcuaCcggCnaXufvtiFdT1wfnMXqy7GIHTlxLRYVgTcpYNNS6VbOW\nS728O1YOs09aIA8Uq7843ZgSBjHSgycmzVAnQZp5Z/QOcusPltjBjMWD7UyEVsmU\nYcdOvxTgnOeZg6myK6y37pNcJJm+qsqGCnhrgTrVehP0nqJlPcGK2vcquJ7p4aG5\noB0CAwEAAaNgMF4wHwYDVR0jBBgwFoAUYrqCGUPGZ661FFzFr/x5ePHXwEEwHQYD\nVR0OBBYEFFDQIZbdGxzRaAJd6+L2iB26azF8MAwGA1UdEwEB/wQCMAAwDgYDVR0P\nAQH/BAQDAgeAMA0GCSqGSIb3DQEBCwUAA4IBAQCckhOht9GcvwuwmCG4jXKJ0291\nfQYjKSj12ap/b4MuBrI0fzfi0ibD5OtDUYxL+3SPzw9dxcI1DRZZ7CHHrEFsn9DJ\nfOF0RAQCg3QKLgy6QfXE+b2j5x15TD5Ult+orTtFqaDFIvf++UhtoD6FSlLtH2jX\nHOlF4w/JLSyiMkJU8b1k3hBJRMllaP8bkw120M8PEEaUdy2xsuKraBcbDEK7MW89\nn6BAzAAc2NuW7DJOadQCrnYGiiGK9pezkYNWFlt/Cqr8aMuZDLiTB3LNkwUP2LzS\n/w803Lc7t5+NfYtu4jMpsrgKFDju+7BXIlqkC8cxUWGTWixK7cR9MWjXAsxd\n-----END CERTIFICATE-----\n"
private_key_string = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEAtzUnGGan1+NqTmv4K6g3gHRIH55QJv/cLdIrbYV3jMLsToo0\n0FqykXiteueDnkUmwiBXAQDL1CE1/GLLkGgrDNPy6wwSJRfE4vofHhtFTgZJirWw\nkxkbU/B3MVlVx4Khq6SqAv4BymSdIIJt1U/pkyiJkrXCGButy5oJyCAKdpe5++2I\nV1PXB+cxerLsYgdOXEtFhWBNylg01LpVs5ZLvbw7Vg6zT1ogDxSrvzjdmBIGMdKD\nJybNUCdBmnln9A5y6w+W2MGMxYPtTIRWyZRhx06/FOCc55mDqbIrrLfuk1wkmb6q\nyoYKeGuBOtV6E/SeomU9wYra9yq4nunhobmgHQIDAQABAoIBAFB7Yx9PCXDHkI2+\n1JipHyio7H4nV+KqB5mBeF52gVwuzQx7nlPhZAyPzPXu+lzu1+XzuwTPyrr3k/W5\nmN9pQ3AxM8eZ1+a/mFh1tHHPXRS3olrzEgysvNqVCmd9bTdl5Yu3nJAP8c1tgbEk\nWweYQW3KIxV2Dzvz/NcyZhWqLa6GnSjYVZOk83oPgYFNXgBR90j8L/2B8fjxv0Am\nqMq2TWViMswbmk+iCMMJdYgt5rxGB5OiP4hBSE5zO5YWQvh8PLUvtZUzC/Pejcbg\n5lnRMvKXan6HgIFJBGXMFs2IOdGuyHADt7GyXON3VucUiX69j4IMkMXekbCvqpjt\n8RmcvGkCgYEA89/34HI6uO5tatHlWj3MiGbn1k7qX07YAdVTlcSo5lFf9mBAiKhA\nd/1PtrPhiwrsMayIAVmHW9ffuer52SS9gCwbOMt3q2ldLb/qkVcrZA89mpk9T4KJ\nuZ2HkPB2zSzAH4cUtUd2xN+ZLZ0HgVrgzXEzsyyjgYCp5RP1zTAfRscCgYEAwFED\nfO3X1ysJmUR+ZySIPmINlSYL8Z9NaBDdsr5CvYup7idrRC3z7ulBbAo5ywAhy2aG\nv6tK5LHHbpAX2aflbwHs2xCk5/eq4tr8fzGlHKEfV5zAbFmBoIzh4WmDqn+E+IKl\n6ClSQkFOAr/CVfPu0wcCY4YzxWHu05Kz04Av7fsCgYEA4bcspBb1lM5QhSqJ3ZEP\nKjwcXbUipV3C/Udlmluve6Rbbhw9/n3DVYslaVNp8BgG7h7irmUfq/jMgDYkUz73\nCZdJBrMDKqpVbI+RWj3U0kJs4RbtsRZ/xEUyAQse2d2OYF/U4cen/KV7D8Wj+ayU\nHnGkyTQKjUT5eiWUPfpJKGcCgYBSYeHmoFQ3nf4Mo+Sp9mJOpt4+p/+xz5XvIFp3\n+TzJyYxPsp8mo7C9BTq7N14uca4IXbEXZh88/FL8L8mnuV51QRPfe6/IlrWjXD+R\nlQivzO2KMGHViDoZNoCEeRin7txdQEolu527OBJc5xwuicIir/v7+j8vLJaMF2nl\nDiJ6BQKBgQCPRcZ65/gVHIrR/ryGUZzUbVXGiYmLtcv88A5Fm+hFg+/HjHfEesd8\nwUY0dT+scRQR3KggjA752Ur8ul92fDEngyQAxYAHir7OmPp90/4NoliIMRxGT0n9\n3WL0MBmt1SPNUnsz3BFHn9S1VBbWEt25/OYsdRSVhSYavukKc6ZaPQ==\n-----END RSA PRIVATE KEY-----\n"
 

# === 2️⃣ Normalize PEMs ===
def normalize_pem_string(pem_str: str) -> bytes:
    """Convert JSON escaped newlines to real newlines, normalize to LF, and append null terminator."""
    if "\\n" in pem_str:
        pem_str = pem_str.encode("utf-8").decode("unicode_escape")
    pem_bytes = pem_str.replace("\r\n", "\n").replace("\r", "\n").encode("ascii")
    if not pem_bytes.endswith(b"\n"):
        pem_bytes += b"\n"
    if not pem_bytes.endswith(b"\n\0"):
        pem_bytes += b"\0"
    return pem_bytes

cert_bytes = normalize_pem_string(certificate_string)
key_bytes = normalize_pem_string(private_key_string)

# === 3️⃣ Load & verify ===
try:
    cert = x509.load_pem_x509_certificate(cert_bytes, default_backend())
    private_key = serialization.load_pem_private_key(key_bytes, password=None, backend=default_backend())
    print("✅ Certificate and private key parsed successfully.")
except Exception as e:
    print(f"❌ Parsing error: {e}")
    sys.exit(1)

# === 4️⃣ Check key–cert match ===
if cert.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
) != private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
):
    print("❌ Mismatch: Private key does NOT match certificate.")
    sys.exit(1)
else:
    print("✅ Verified: Private key matches certificate.")

# === 5️⃣ Save normalized files ===
output_folder = r"C:\Boris _ Formal_Tests\IoT Link Devices\temp"
cert_path = os.path.join(output_folder, "IoTCore_certificate_final.pem.crt")
key_path = os.path.join(output_folder, "private_final.pem.key")

with open(cert_path, "wb") as f:
    f.write(cert_bytes)
with open(key_path, "wb") as f:
    f.write(key_bytes)

print("\n📁 Files saved successfully:")
print(f"   → {cert_path}")
print(f"   → {key_path}")

# === 6️⃣ Print fingerprints ===
cert_fp = hashlib.sha256(cert_bytes).hexdigest()
key_fp = hashlib.sha256(key_bytes).hexdigest()
print(f"\n🔍 Certificate SHA256 fingerprint: {cert_fp}")
print(f"🔍 Private key SHA256 fingerprint:  {key_fp}")

# === 7️⃣ Confirm file end bytes ===
print("\n🧾 Final 4 bytes of key file:")
with open(key_path, "rb") as f:
    tail = f.read()[-4:]
print(tail.hex(), "(should end with 0a00)")
 