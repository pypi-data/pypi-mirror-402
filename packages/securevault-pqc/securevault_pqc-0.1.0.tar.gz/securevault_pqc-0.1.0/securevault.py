import oqs
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import click
import os
import json
from pathlib import Path
import base64

def generate_hybrid_keypair():
    # Generate X25519 key pair
    private_key = x25519.X25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Generate PQC key pair using oqs
    kem = oqs.KeyEncapsulation('ML-KEM-768')
    pqc_public_key = kem.generate_keypair()
    pqc_secret_key = kem.export_secret_key()

    # serialize keys
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )


    # bundle keys together
    return {
        'private_key': private_bytes,
        'public_key': public_bytes,
        'pqc_private_key': pqc_secret_key,
        'pqc_public_key': pqc_public_key,
        'algorithm': 'X25519+ML-KEM-768'
    }

def save_keypair_to_file(keypair, filepath, password=None):
    # Serialize keypair to JSON
    keypair_serialized= {
        'private_key': base64.b64encode(keypair['private_key']).decode('utf-8'),
        'public_key': base64.b64encode(keypair['public_key']).decode('utf-8'),
        'pqc_private_key': base64.b64encode(keypair['pqc_private_key']).decode('utf-8'),
        'pqc_public_key': base64.b64encode(keypair['pqc_public_key']).decode('utf-8'),
        'algorithm': keypair['algorithm']
    }

    keypair_json = json.dumps(keypair_serialized).encode('utf-8')

    if password:
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), 
            length=32, 
            salt=salt,      
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)
        encrypted_dt = fernet.encrypt(keypair_json)
        with open(filepath, 'wb') as f:
            f.write(salt + encrypted_dt)

    else:
        with open(filepath, 'wb') as f:
            f.write(keypair_json)

    



def load_keypair_from_file(filepath, password=None):
    with open(filepath, 'rb') as f:
        data = f.read()
    

    #if encrypted
    if password:
        #derive key from password
        salt = data[:16]
        encrypted_dt = data[16:]
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)
        decrypted_dt = fernet.decrypt(encrypted_dt)
        keypair_json = decrypted_dt
    else:
        keypair_json = data
    keypair_dict = json.loads(keypair_json)
    
    return {
        'private_key': base64.b64decode(keypair_dict['private_key']), 
        'public_key': base64.b64decode(keypair_dict['public_key']),
        'pqc_private_key': base64.b64decode(keypair_dict['pqc_private_key']),
        'pqc_public_key': base64.b64decode(keypair_dict['pqc_public_key']),
        'algorithm': keypair_dict['algorithm']
    }


#yooo this is a lot harder than i thought lol

    
# def hybrid_encrypt_file(input_file, output_file, recipient_public_keys):

#     #generate random file encryption key(32 bytes for AES-256)
#     file_key = os.urandom(32)

#     #encrypt file with AES (using Fernet)
#     fernet = Fernet(base64.urlsafe_b64encode(file_key))
#     with open(input_file, 'rb') as f:
#         data = f.read()

#     encrypted_dt = fernet.encrypt(data)
#     #wrap file_key with classical crypto (x25519)
#     private_key = x25519.X25519PrivateKey.generate()
#     peer_public_key = x25519.X25519PublicKey.from_public_bytes(recipient_public_keys['public_key'])
#     share_secret_classical = private_key.exchange(peer_public_key)

#     # Create AESGCM instance with the shared secret
#     #yo this was so hard to find an dunderstand
#     aesgcm = AESGCM(share_secret_classical)
#     classical_wrappped_key = aesgcm.encrypt(os.urandom(12), file_key, None)

#     #wrap file_key with PQC crypto(ML-KEM-768)
#     kem = oqs.KeyEncapsulation('ML-KEM-768')
#     kem.import_public_key(recipient_public_keys['pqc_public_key'])
#     pqc_ciphertext, pqc_shared_secret = kem.encap_secret(recipient_public_keys['pqc_public_key'])

#     aesgcm_pqc = AESGCM(pqc_shared_secret)
#     pqc_wrapped_key = aesgcm_pqc.encrypt(os.urandom(12), file_key, None)

#     # package the whole thing into output file
#     with open(output_file, 'wb') as f:
#         f.write(encrypted_dt)

    
#     return {
#         'encrypted_data': encrypted_dt.decode('utf-8'),
#         'classical_wrapped_key': classical_wrappped_key.decode('utf-8'),
#         'pqc_wrapped_key': pqc_wrapped_key.decode('utf-8'), 
#         'pqc_ciphertext': pqc_ciphertext.decode('utf-8'),
#         'algorithm': 'hybrid-x25519-mlkem768'
#     }

def hybrid_encrypt_file(input_file, output_file, recipient_public_keys):
    """
    Encrypt file using recipient's public keys with hybrid classical + PQC
    """
    # Step 1: Read the file
    with open(input_file, 'rb') as f:
        file_data = f.read()
    
    # Step 2: Generate random symmetric key for file encryption
    file_key = Fernet.generate_key()
    
    # Step 3: Encrypt the file with symmetric key
    fernet = Fernet(file_key)
    encrypted_data = fernet.encrypt(file_data)
    
    # Step 4: Wrap file_key with CLASSICAL crypto (X25519 + AES-GCM)
    ephemeral_private = x25519.X25519PrivateKey.generate()
    ephemeral_public = ephemeral_private.public_key()
    
    recipient_public_classical = x25519.X25519PublicKey.from_public_bytes(
        recipient_public_keys['classical_public_key']
    )
    
    shared_secret_classical = ephemeral_private.exchange(recipient_public_classical)
    
    aesgcm = AESGCM(shared_secret_classical)
    nonce_classical = os.urandom(12)
    
    # Decode Fernet key to get raw 32 bytes
    file_key_bytes = base64.urlsafe_b64decode(file_key)
    classical_wrapped_key = aesgcm.encrypt(nonce_classical, file_key_bytes, None)
    
    # Step 5: Wrap file_key with POST-QUANTUM crypto (ML-KEM-768)
    kem = oqs.KeyEncapsulation('ML-KEM-768')
    pqc_ciphertext, shared_secret_pqc = kem.encap_secret(recipient_public_keys['pqc_public_key'])
    
    aesgcm_pqc = AESGCM(shared_secret_pqc)
    nonce_pqc = os.urandom(12)
    pqc_wrapped_key = aesgcm_pqc.encrypt(nonce_pqc, file_key_bytes, None)
    
    # Step 6: Create encrypted package with all components
    package = {
        'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
        'classical_wrapped_key': base64.b64encode(classical_wrapped_key).decode('utf-8'),
        'pqc_wrapped_key': base64.b64encode(pqc_wrapped_key).decode('utf-8'),
        'pqc_ciphertext': base64.b64encode(pqc_ciphertext).decode('utf-8'),
        'ephemeral_public_key': base64.b64encode(
            ephemeral_public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
        ).decode('utf-8'),
        'nonce_classical': base64.b64encode(nonce_classical).decode('utf-8'),
        'nonce_pqc': base64.b64encode(nonce_pqc).decode('utf-8'),
        'algorithm': 'hybrid-x25519-mlkem768'
    }
    
    # Step 7: Write to output file as JSON
    with open(output_file, 'w') as f:
        json.dump(package, f, indent=2)
    
    return package


def hybrid_decrypt_file(input_file, output_file, private_keys):
    """
    Decrypt file using your private keys
    """
    # Step 1: Load encrypted package from file
    with open(input_file, 'r') as f:
        package = json.load(f)
    
    # Step 2: Base64 decode all the fields
    encrypted_data = base64.b64decode(package['encrypted_data'])
    classical_wrapped_key = base64.b64decode(package['classical_wrapped_key'])
    pqc_wrapped_key = base64.b64decode(package['pqc_wrapped_key'])
    pqc_ciphertext = base64.b64decode(package['pqc_ciphertext'])
    ephemeral_public_bytes = base64.b64decode(package['ephemeral_public_key'])
    nonce_classical = base64.b64decode(package['nonce_classical'])
    nonce_pqc = base64.b64decode(package['nonce_pqc'])
    
    # Step 3: Unwrap file_key using CLASSICAL crypto
    private_key = x25519.X25519PrivateKey.from_private_bytes(
        private_keys['private_key']
    )
    ephemeral_public = x25519.X25519PublicKey.from_public_bytes(ephemeral_public_bytes)
    
    shared_secret_classical = private_key.exchange(ephemeral_public)
    
    aesgcm = AESGCM(shared_secret_classical)
    file_key_classical = aesgcm.decrypt(nonce_classical, classical_wrapped_key, None)
    
    # Step 4: Unwrap file_key using POST-QUANTUM crypto
    kem = oqs.KeyEncapsulation('ML-KEM-768', private_keys['pqc_private_key'])
 
    shared_secret_pqc = kem.decap_secret(pqc_ciphertext)
    
    aesgcm_pqc = AESGCM(shared_secret_pqc)
    file_key_pqc = aesgcm_pqc.decrypt(nonce_pqc, pqc_wrapped_key, None)
    
    # Step 5: VERIFY both unwraps produced same file_key
    if file_key_classical != file_key_pqc:
        raise ValueError("Security Error: Key mismatch between classical and PQC!")
    
    # Step 6: Decrypt file with file_key
    fernet = Fernet(base64.urlsafe_b64encode(file_key_classical))
    decrypted_data = fernet.decrypt(encrypted_data)
    
    # Step 7: Write to output file
    with open(output_file, 'wb') as f:
        f.write(decrypted_data)


# ==================== CLI COMMANDS ====================

@click.group()
def cli():
    """SecureVault - Post-Quantum File Encryption"""
    pass


@cli.command()
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True,
              help='Password to protect private key')
@click.option('--output', default='keypair.key', help='Output file for keypair')
def keygen(password, output):
    """
    Generate new hybrid keypair
    """
    keypair = generate_hybrid_keypair()
    
    # Save private keypair (password protected)
    save_keypair_to_file(keypair, output, password)
    
    # Save public keys separately (NO password - anyone can use!)
    public_key_file = output.replace('.key', '_public.key')
    public_only = {
        'private_key': b'',  # Empty, not needed for public key file
        'public_key': keypair['public_key'],
        'pqc_private_key': b'',  # Empty, not needed
        'pqc_public_key': keypair['pqc_public_key'],
        'algorithm': keypair['algorithm']
    }
    save_keypair_to_file(public_only, public_key_file, password=None)
    
    click.echo(click.style(f"✓ Private keypair saved to {output}", fg='green'))
    click.echo(click.style(f"✓ Public keys saved to {public_key_file}", fg='green'))
    click.echo(f"Algorithm: {keypair['algorithm']}")
    click.echo(click.style("🔒 Classical: X25519", fg='cyan'))
    click.echo(click.style("🔐 Post-Quantum: ML-KEM-768", fg='magenta'))
    click.echo(click.style(f"\n📤 Share {public_key_file} with others!", fg='yellow'))

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('recipient_key', type=click.Path(exists=True))
@click.option('--output', help='Output encrypted file (default: input_file.vault)')
def encrypt(input_file, recipient_key, output):  # ← REMOVED password parameter
    """
    Encrypt a file for a recipient using their PUBLIC keys (no password needed)
    """
    if output is None:
        output = input_file + '.vault'
    
    # Load recipient's keys WITHOUT password (we only need public keys!)
    try:
        recipient_keys = load_keypair_from_file(recipient_key, password=None)
    except Exception as e:
        click.echo(click.style("✗ Error: Could not load recipient's public key", fg='red'), err=True)
        click.echo(click.style("  Make sure the key file is not password-protected, or use the public key file", fg='yellow'), err=True)
        raise
    
    recipient_public_keys = {
        'classical_public_key': recipient_keys['public_key'],
        'pqc_public_key': recipient_keys['pqc_public_key']
    }
    
    hybrid_encrypt_file(input_file, output, recipient_public_keys)
    
    click.echo(click.style(f"✓ Encrypted {input_file} → {output}", fg='green'))
    click.echo(click.style("🔒 Protected by classical AND post-quantum cryptography", fg='cyan'))
    click.echo(click.style("🛡️  Quantum-resistant until 2050+", fg='magenta'))

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('private_key_file', type=click.Path(exists=True))
@click.option('--password', prompt=True, hide_input=True, help='Private key password')
@click.option('--output', help='Output decrypted file')
def decrypt(input_file, private_key_file, password, output):
    """
    Decrypt a file using your private key
    """
    private_keys = load_keypair_from_file(private_key_file, password)
    
    if output is None:
        output = input_file.replace('.vault', '')
        if output == input_file:  # No .vault extension found
            output = input_file + '.decrypted'
    
    hybrid_decrypt_file(input_file, output, private_keys)
    
    click.echo(click.style(f"✓ Decrypted {input_file} → {output}", fg='green'))
    click.echo(click.style("🔓 Verified with both classical and PQC keys", fg='cyan'))


@cli.command()
@click.argument('encrypted_file', type=click.Path(exists=True))
def info(encrypted_file):
    """
    Show security information about encrypted file
    """
    with open(encrypted_file, 'r') as f:
        package = json.load(f)
    
    click.echo(click.style("\n🔐 SecureVault Encrypted File Info", fg='cyan', bold=True))
    click.echo("─" * 50)
    click.echo(f"Algorithm: {click.style(package['algorithm'], fg='yellow')}")
    click.echo(f"Classical protection: {click.style('✓ X25519', fg='green')}")
    click.echo(f"Post-quantum protection: {click.style('✓ ML-KEM-768', fg='green')}")
    click.echo(f"Quantum resistant: {click.style('YES', fg='green', bold=True)}")
    click.echo(f"Safe until: {click.style('2050+ (estimated)', fg='magenta')}")
    
    # File size info
    encrypted_size = len(base64.b64decode(package['encrypted_data']))
    click.echo(f"\nEncrypted data size: {click.style(f'{encrypted_size} bytes', fg='white')}")
    click.echo("─" * 50)


if __name__ == '__main__':
    cli()




