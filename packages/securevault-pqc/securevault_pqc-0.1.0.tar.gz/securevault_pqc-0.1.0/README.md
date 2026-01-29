# SecureVault - Post-Quantum File Encryption
***Protect your files from future quantum computers.***
##

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey)
![Cryptography](https://img.shields.io/badge/crypto-ML--KEM--768-purple)
![NIST](https://img.shields.io/badge/NIST-Post--Quantum-orange)
![Status](https://img.shields.io/badge/status-active-success)


## The Problem
Quantum computers will break RSA/ECC encryption within 10-20 years. 
Attackers are stealing encrypted data NOW to decrypt LATER.

This is what we called "**harvest now, decrypt later**" attacks.

## The Solution
SecureVault uses ML-KEM-768 (NIST standardized post-quantum crypto) 
in hybrid mode with X25519 for maximum security. Even if quantum computers break one layer, your data stays protected.

## Features

- **Hybrid encryption**: X25519 + ML-KEM-768 (defense in depth²)
- **Password-protected keys**: PBKDF2 key derivation (100k iterations)
- **Cross-platform**: Works on Linux, macOS, and Windows
- **Future-proof**: Quantum-resistant for 30+ years
- **Easy CLI**: Simple commands, no crypto knowledge needed
- **Educational**: Shows security info about your files

## Installation

### Prerequisites
- Python 3.9 or higher
- pip

### Setup
```bash
# Clone the repo
git clone https://github.com/yourusername/securevault.git
cd securevault

# Install dependencies
pip install -r requirements.txt
```

## Quick Start
```bash
# 1. Generate your keypair
python3 secure_vault.py keygen --password mypassword --output my_keys.key
# Creates: my_keys.key (private) and my_keys_public.key (public)

# 2. Encrypt a file
echo "Secret data" > secret.txt
python3 secure_vault.py encrypt secret.txt my_keys_public.key

# 3. Check security info
python3 secure_vault.py info secret.txt.vault

# 4. Decrypt it
python3 secure_vault.py decrypt secret.txt.vault my_keys.key --password mypassword
```

## Technical Details
- Hybrid: X25519 + ML-KEM-768
- File encryption: AES-256-GCM (Fernet)
- Key derivation: PBKDF2

## Performance
[Benchmark results]

## Why This Matters
[Quantum threat timeline]
[Use cases]
