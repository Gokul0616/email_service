"""
DKIM Key Generator for pixelrisewebco.com
Generates production-ready DKIM keys for real email delivery
"""

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import base64

def generate_dkim_keys_for_domain(domain: str):
    """Generate DKIM private and public keys for a domain"""
    
    print(f"Generating DKIM keys for {domain}...")
    
    # Generate a new RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Convert public key to DKIM format
    public_key_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Base64 encode for DNS record
    public_key_b64 = base64.b64encode(public_key_der).decode('ascii')
    
    # Create DKIM DNS record value
    dkim_record = f"v=DKIM1; k=rsa; p={public_key_b64}"
    
    return {
        'private_key': private_pem,
        'public_key': public_pem,
        'dkim_record': dkim_record,
        'domain': domain
    }

if __name__ == "__main__":
    # Generate keys for pixelrisewebco.com
    keys = generate_dkim_keys_for_domain("pixelrisewebco.com")
    
    # Save private key
    with open("/app/backend/dkim_private_pixelrisewebco.key", "wb") as f:
        f.write(keys['private_key'])
    
    # Save public key
    with open("/app/backend/dkim_public_pixelrisewebco.key", "wb") as f:
        f.write(keys['public_key'])
    
    print(f"✅ DKIM keys generated for {keys['domain']}")
    print(f"📝 DKIM DNS Record: {keys['dkim_record']}")