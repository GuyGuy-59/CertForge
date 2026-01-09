# PKI-Manager

A comprehensive set of bash scripts for managing a complete Public Key Infrastructure (PKI). Create Certificate Authorities (CA), generate server and client certificates, and manage Certificate Revocation Lists (CRL) with ease.

## Features

- ✅ **Certificate Authority (CA) Generation** - Create self-signed root CAs with RSA or ECC algorithms
- ✅ **Server & Client Certificates** - Generate X.509 certificates and PKCS#12 containers (.p12/.pfx) for both servers and clients
- ✅ **CRL Management** - Revoke certificates and maintain Certificate Revocation Lists
- ✅ **Flexible Configuration** - Customize certificate attributes via environment variables or custom OpenSSL config files
- ✅ **Subject Alternative Names (SAN)** - Support for multiple DNS names and IP addresses
- ✅ **Algorithm Support** - RSA (4096-bit) and Elliptic Curve (secp384r1) cryptography

## 📦 Prerequisites

- **OpenSSL** (version 1.1.1 or later recommended)
- **Bash** (version 4.0 or later)
- **Unix-like environment** (Linux, macOS, WSL on Windows)

### Verify Installation

```bash
openssl version
bash --version
```

## 💡 Basic Concepts

### What is a PKI?

A **Public Key Infrastructure (PKI)** is a system for managing digital certificates. It consists of:

1. **Certificate Authority (CA)**: The root entity that signs and validates certificates
2. **Certificates**: Digital documents that bind a public key to an identity
3. **Certificate Revocation List (CRL)**: List of certificates revoked before their expiration

### Certificate Types

- **Server Certificate**: Used to authenticate a server (website, API, etc.)
  - Format: `.crt` (X.509) + `.p12` (PKCS#12 for Windows)
  - Private key: Passwordless by default (for automated services)

- **Client Certificate**: Used to authenticate a user or device
  - Format: `.p12` (PKCS#12, for browser/OS)
  - Private key: Password protected by default

### File Formats

- **`.crt`**: Public certificate in X.509 format (standard)
- **`.key`**: Private key (keep secret!)
- **`.p12` / `.pfx`**: PKCS#12 container containing certificate + private key (for Windows/browsers)
- **`.csr`**: Certificate Signing Request

## Project Structure

```
pki-manager/
├── bin/              # Executable scripts
│   ├── pki-ca        # Certificate Authority management
│   ├── pki-cert      # Certificate generation
│   └── pki-crl       # Certificate Revocation List management
├── lib/              # Common library functions
│   └── common.sh     # Shared utilities
├── templates/        # Configuration templates
│   └── ca.cnf.template
├── examples/         # Example configurations
│   └── example_cert.cnf
├── pki               # Main entry point wrapper
└── README.md         # This file
```

## 🚀 Quick Start

### Recommended Method: Using the wrapper script

```bash
# 1. Create a Certificate Authority (CA)
./pki ca create -p demo -a ec

# 2. Generate a server certificate
./pki cert -p demo -t server -a ec -n "example.com"

# 3. Generate a client certificate
./pki cert -p demo -t client -a ec -n "John Doe"
```

### Alternative Method: Using scripts directly

```bash
# Create a CA
./bin/pki-ca create -p demo -a ec

# Generate certificates
./bin/pki-cert -p demo -t server -a ec -n "example.com"
./bin/pki-cert -p demo -t client -a ec -n "John Doe"

# Manage revocation
./bin/pki-crl -p demo -r 01 -u
```

## 📋 Step-by-Step Guide

### Step 1: Create a Certificate Authority (CA)

The CA is the root of trust that will sign all your certificates.

```bash
./pki ca create -p demo -a ec
```

**What is created:**
- `demo/ca.key` - CA private key (password protected)
- `demo/ca.crt` - Self-signed CA certificate
- `demo/ca.cnf` - OpenSSL configuration
- `demo/crl/` - Infrastructure for revocation lists

**Choose the algorithm:**
- `-a ec`: Elliptic Curve (recommended, faster, 384 bits)
- `-a rsa`: RSA 4096 bits (maximum compatibility)

### Step 2: Generate Certificates

#### Server Certificate (for websites, APIs, etc.)

```bash
./pki cert -p demo -t server -a ec -n "example.com"
```

**Generated files:**
- `serverCertificate_*.crt` - Public certificate
- `serverCertificate_*.key` - Private key (passwordless by default)
- `serverCertificate_*.p12` - PKCS#12 container (for Windows)
- `serverCertificate_*.p12.pass` - .p12 file password

**With multiple domains (SAN):**
```bash
export CRT_SAN="DNS:example.com,DNS:www.example.com,DNS:*.example.com,IP:192.168.1.1"
./pki cert -p demo -t server -a ec -n "example.com"
```

#### Client Certificate (for user authentication)

```bash
./pki cert -p demo -t client -a ec -n "John Doe"
```

**Generated files:**
- `clientCertificate_*.crt` - Public certificate
- `clientCertificate_*.key` - Private key (password protected)
- `clientCertificate_*.p12` - PKCS#12 container (for browser/OS)
- `clientCertificate_*.p12.pass` - .p12 file password

### Step 3: Manage Certificate Revocation

If a certificate is compromised or no longer needed:

```bash
# Revoke a certificate and update the CRL
./pki crl -p demo -r 01 -u
```

**Find the serial number:**
```bash
openssl x509 -in demo/serverCertificate_*.crt -noout -serial
```

## 📚 Commands Overview

| Command | Description | Key Features |
|---------|-------------|--------------|
| `pki ca` | Create a Certificate Authority | Generates CA key/certificate, initializes CRL infrastructure |
| `pki cert` | Generate certificates | Server (X.509) and client (PKCS#12) certificates |
| `pki crl` | Manage CRL | Revoke certificates, update revocation lists |

## ⚙️ Custom Configuration

### Environment Variables

You can customize certificates via environment variables:

**For the CA:**
```bash
export CA_C="FR"                    # Country code (2 letters)
export CA_L="Paris"                 # Locality
export CA_O="My Company"            # Organization
export CA_OU="IT Security"          # Organizational unit
export CA_EXPIRE_DAYS=1825          # Validity period (5 years)
./pki ca create -p myproject -a ec
```

**For certificates:**
```bash
export CRT_C="FR"                    # Country code
export CRT_L="Paris"                 # Locality
export CRT_O="My Company"           # Organization (must match CA if policy_match)
export CRT_OU="DevOps"               # Organizational unit
export CRT_SAN="DNS:example.com,DNS:www.example.com,IP:192.168.1.1"  # Alternative names
export CRT_EXPIRE_DAYS=365           # Validity period
./pki cert -p myproject -t server -a ec -n "example.com"
```

**Important note:** If you don't define `CRT_O`, PKI-Manager automatically extracts the organization from the CA certificate to ensure policy matching.

## 📖 Detailed Documentation

### 1. Certificate Authority Creation

**Command:** `pki ca create`

#### Syntax

```bash
./pki ca create -p <project_name> -a <algorithm>
```

#### Options

| Option | Description | Required |
|--------|-------------|----------|
| `-p <project_name>` | Project name (creates a directory with this name) | ✅ Yes |
| `-a <algorithm>` | Encryption algorithm: `rsa` or `ec` | ✅ Yes |

#### Algorithm Comparison

| Algorithm | Key Size | Performance | Use Case |
|-----------|----------|-------------|----------|
| **RSA** | 4096 bits | Slower | Maximum compatibility |
| **EC** (secp384r1) | 384 bits | Faster | Modern systems (recommended) |

#### Environment Variables for CA

| Variable | Description | Default |
|----------|-------------|---------|
| `CA_C` | Country code (2 letters) | `FR` |
| `CA_L` | Locality/City | `Paris` |
| `CA_O` | Organization | `France` |
| `CA_OU` | Organizational Unit | `DevOps` |
| `CA_CN` | Common Name | Project name |
| `CA_EXPIRE_DAYS` | CA validity period (days) | `365` |
| `CRL_EXPIRE_DAYS` | CRL validity period (days) | `30` |

#### Examples

**Basic CA creation:**
```bash
./pki ca create -p myproject -a ec
```

**Customized CA:**
```bash
export CA_O="My Company" CA_OU="IT Security" CA_EXPIRE_DAYS=1825
./pki ca create -p production -a ec
```

**CA for development environment:**
```bash
export CA_O="Dev Company" CA_CN="Dev CA" CA_EXPIRE_DAYS=365
./pki ca create -p dev -a ec
```

#### Generated Files Structure

```
project_name/
├── ca.key              # CA private key (password protected, chmod 400)
├── ca.crt              # CA certificate (self-signed, chmod 444)
├── ca.pass             # CA key password (randomly generated)
├── ca.cnf              # OpenSSL CA configuration file
├── ca.srl              # Serial number file (auto-incremented)
├── index.txt           # Certificate database (issued/revoked)
├── index.txt.attr      # Index attributes
├── crlnumber           # CRL serial number
├── crl/
│   └── ca.crl          # Certificate Revocation List
└── newcerts/           # Copies of issued certificates (serial.pem)
```

#### Viewing CA Information

```bash
# Show CA certificate details
openssl x509 -nameopt multiline,-esc_msb,utf8 -in demo/ca.crt -text -noout | \
    egrep -i -v '^\s+([0-9a-z]{2}:){15,}'

# Show CRL details
openssl crl -in demo/crl/ca.crl -text -noout
```

---

### 2. Certificate Generation

**Command:** `pki cert` or `bin/pki-cert`

#### Syntax

```bash
./pki cert -p <project_name> -t <type> -a <algorithm> [-n <name>] [-c <cnf_file>]
```

#### Options

| Option | Description | Required |
|--------|-------------|----------|
| `-p <project_name>` | Project name (must match existing CA project) | ✅ Yes |
| `-t <type>` | Certificate type: `server` or `client` | ✅ Yes |
| `-a <algorithm>` | Algorithm: `rsa` or `ec` | ✅ Yes |
| `-n <name>` | Common Name (CN) | ❌ Optional |
| `-c <cnf_file>` | Custom OpenSSL configuration file | ❌ Optional |

#### Certificate Types

**Server Certificates:**
- Format: X.509 (`.crt`) and PKCS#12 (`.p12` / `.pfx`)
- Private key: Passwordless by default (for automated services)
- PKCS#12 container: Password protected (contains certificate + private key)
- Use case: Web servers, API endpoints, TLS/SSL services
- Note: The `.p12` file is useful for Windows servers (can be renamed to `.pfx`)

**Client Certificates:**
- Format: PKCS#12 (`.p12` / `.pfx`)
- Private key: Password protected by default
- Use case: Client authentication, email signing, VPN access

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CRT_C` | Country code | `FR` |
| `CRT_L` | Locality | `Paris` |
| `CRT_O` | Organization | `France` |
| `CRT_OU` | Organizational Unit | `DevOps` |
| `CRT_CN` | Common Name | Overridden by `-n` if provided |
| `CRT_EXPIRE_DAYS` | Certificate validity (days) | `365` |
| `CRT_SAN` | Subject Alternative Names | None |
| `NO_PASSWD` | Disable password for private key | `true` (server), `false` (client) |

#### Subject Alternative Names (SAN)

SAN allows a certificate to be valid for multiple domain names and IP addresses:

```bash
export CRT_SAN="DNS:example.com,DNS:www.example.com,DNS:*.example.com,IP:192.168.1.1"
./pki cert -p demo -t server -a ec -n "example.com"
```

#### Examples

**Basic server certificate:**
```bash
./pki cert -p demo -t server -a ec -n "api.example.com"
```

**Server certificate with SAN (multiple domains):**
```bash
export CRT_SAN="DNS:api.example.com,DNS:www.example.com,IP:192.168.1.1"
./pki cert -p demo -t server -a ec -n "api.example.com"
```

**Client certificate:**
```bash
export CRT_O="My Company" CRT_OU="Development"
./pki cert -p demo -t client -a ec -n "John Doe"
```

**Using a custom configuration file:**
```bash
./pki cert -p demo -t server -a ec -n "example.com" -c examples/example_cert.cnf
```

**Server certificate for LDAP:**
```bash
export CRT_SAN="DNS:ldap.example.com,IP:192.168.1.10"
./pki cert -p demo -t server -a ec -n "ldap.example.com"
```

#### Generated Files

**For server certificates:**
- `<type>Certificate_<timestamp>_<name>.key` - Private key
- `<type>Certificate_<timestamp>_<name>.csr` - Certificate Signing Request
- `<type>Certificate_<timestamp>_<name>.crt` - Signed certificate
- `<type>Certificate_<timestamp>_<name>.p12` - PKCS#12 container (certificate + private key)
- `<type>Certificate_<timestamp>_<name>.p12.pass` - .p12 file password

**For client certificates:**
- All files above (same structure as server certificates)
- The `.p12` file is primarily used for browser/OS import

#### Viewing Certificate Information

```bash
# Show complete certificate details
openssl x509 -in certificate.crt -text -noout

# Show certificate subject
openssl x509 -in certificate.crt -noout -subject

# Show serial number
openssl x509 -in certificate.crt -noout -serial

# Verify certificate against CA
openssl verify -CAfile demo/ca.crt certificate.crt

# For PKCS#12 files
openssl pkcs12 -info -in certificate.p12 -passin file:certificate.p12.pass
```

---

### 3. CRL Management (Certificate Revocation List)

**Command:** `pki crl`

#### Syntax

```bash
./pki crl -p <project_name> [-r <serial_number>] [-u]
```

#### Options

| Option | Description | Required |
|--------|-------------|----------|
| `-p <project_name>` | Project name (must match existing CA project) | ✅ Yes |
| `-r <serial_number>` | Serial number of certificate to revoke (hex format) | ❌ Optional |
| `-u` | Update the CRL (use with `-r` or alone) | ❌ Optional |

#### Examples

**Revoke a certificate and update CRL:**
```bash
./pki crl -p demo -r 01 -u
```

**Update CRL without revoking:**
```bash
./pki crl -p demo -u
```

**Revoke only (CRL will be updated automatically):**
```bash
./pki crl -p demo -r 02
```

#### Finding Certificate Serial Numbers

**From certificate file:**
```bash
openssl x509 -in certificate.crt -noout -serial
```

**From CA database:**
```bash
cat demo/index.txt
```

**List all certificates:**
```bash
# Show all issued certificates
cat demo/index.txt | grep "^V"

# Show revoked certificates
cat demo/index.txt | grep "^R"
```

#### Verifying CRL

```bash
# Display CRL content
openssl crl -in demo/crl/ca.crl -text -noout

# Count revoked certificates
openssl crl -in demo/crl/ca.crl -text -noout | grep -c "Serial Number:"

# Check if specific serial is revoked
openssl crl -in demo/crl/ca.crl -text -noout | grep -A 2 "Serial Number: 01"
```

---

## 🎯 Common Use Cases

### Use Case 1: Certificate for a Web Server

```bash
# 1. Create the CA
export CA_O="My Company" CA_EXPIRE_DAYS=1825
./pki ca create -p webapp -a ec

# 2. Generate the certificate with all necessary domains
export CRT_SAN="DNS:webapp.com,DNS:www.webapp.com,DNS:*.webapp.com"
./pki cert -p webapp -t server -a ec -n "webapp.com"

# 3. Install on the server (Nginx example)
# - Copy serverCertificate_*.crt to /etc/ssl/certs/
# - Copy serverCertificate_*.key to /etc/ssl/private/
```

### Use Case 2: Certificate for LDAP/Active Directory Server

```bash
# 1. Create the CA
export CA_O="serval CA" CA_EXPIRE_DAYS=730
./pki ca create -p serval -a ec

# 2. Generate the certificate with DNS and IP
export CRT_SAN="DNS:ldap.serval.int,IP:192.168.134.10"
./pki cert -p serval -t server -a ec -n "ldap.serval.int"

# 3. Use the .p12 file for Windows
# - Rename .p12 to .pfx if necessary
# - Import into Windows certificate store
```

### Use Case 3: Client Certificates for Authentication

```bash
# 1. Create the CA (if not already done)
./pki ca create -p company -a ec

# 2. Generate certificates for multiple users
export CRT_O="My Company" CRT_OU="IT Department"
./pki cert -p company -t client -a ec -n "Alice Martin"
./pki cert -p company -t client -a ec -n "Bob Dupont"

# 3. Distribute .p12 files to users
# - Password is in the .p12.pass file
# - Users can import into their browser
```

### Use Case 4: Wildcard Certificate for Subdomains

```bash
# Certificate that covers all subdomains
export CRT_SAN="DNS:*.example.com,DNS:example.com"
./pki cert -p demo -t server -a ec -n "*.example.com"
```

---

## 📝 Custom Configuration Files

### Using Custom `.cnf` Files

You can use custom OpenSSL configuration files to define advanced certificate extensions, Subject Alternative Names (SAN), and other options.

#### Example Configuration File

See `examples/example_cert.cnf` for a complete example with detailed comments. The script automatically detects these sections:

- `[v3_server]` - For server certificates
- `[v3_client]` - For client certificates
- `[v3_req]` - Generic section (fallback)

#### Usage

```bash
# Copy and customize the example
cp examples/example_cert.cnf my_cert.cnf
# Edit my_cert.cnf according to your needs

# Use with certificate generation
./pki cert -p demo -t server -a ec -n "example.com" -c my_cert.cnf
```

#### Configuration File Structure

```ini
[ req ]
default_bits = 4096
distinguished_name = req_distinguished_name
req_extensions = v3_req

[ req_distinguished_name ]
countryName = Country Name (2 letter code)
countryName_default = FR

[ v3_server ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = example.com
DNS.2 = www.example.com
DNS.3 = *.example.com
IP.1 = 192.168.1.1
```

**Note:** For most use cases, environment variables (`CRT_SAN`, etc.) are sufficient. Use `.cnf` files only for very specific configurations.

---

## Complete Workflow Example

This example demonstrates creating a complete PKI for a project called "webapp":

### Step 1: Create the Certificate Authority

```bash
export CA_O="Acme Corp" CA_OU="IT Security" CA_EXPIRE_DAYS=1825
./01_generate_CA.sh -p webapp -a ec
```

### Step 2: Generate Server Certificates

```bash
cd webapp

# Main web server
export CRT_SAN="DNS:webapp.com,DNS:www.webapp.com"
./pki cert -p webapp -t server -a ec -n "webapp.com"

# API server
export CRT_SAN="DNS:api.webapp.com,DNS:*.api.webapp.com"
./pki cert -p webapp -t server -a ec -n "api.webapp.com"
```

### Step 3: Generate Client Certificates

```bash
# Developer certificates
export CRT_O="Acme Corp" CRT_OU="Development"
./pki cert -p webapp -t client -a ec -n "Alice Developer"
./pki cert -p webapp -t client -a ec -n "Bob Developer"

# Admin certificates
export CRT_OU="Administration"
./pki cert -p webapp -t client -a ec -n "Admin User"
```

### Step 4: Verify Certificates

```bash
# Verify server certificates
for cert in webapp/server*.crt; do
    echo "=== $cert ==="
    openssl x509 -in "$cert" -noout -subject -dates
    openssl verify -CAfile webapp/ca.crt "$cert"
done

# List all issued certificates
cat webapp/index.txt
```

### Step 5: Revoke a Certificate (if needed)

```bash
# Find serial number
openssl x509 -in webapp/clientCertificate_*.crt -noout -serial

# Revoke and update CRL
./pki crl -p webapp -r 02 -u

# Verify revocation
openssl crl -in webapp/crl/ca.crl -text -noout
```

---

## File Structure Reference

```
project_name/
├── ca.key              # CA private key (password protected, chmod 400)
├── ca.crt              # CA certificate (chmod 444)
├── ca.pass             # CA key password (randomly generated)
├── ca.cnf              # OpenSSL CA configuration
├── ca.srl              # Serial number counter
├── index.txt           # Certificate database
├── index.txt.attr      # Index attributes
├── crlnumber           # CRL serial number
├── crl/
│   └── ca.crl          # Certificate Revocation List
├── newcerts/           # Copies of issued certificates
│   ├── 01.pem
│   ├── 02.pem
│   └── ...
└── <certificate_files> # Generated certificates
    ├── serverCertificate_20240101_webapp.com.key
    ├── serverCertificate_20240101_webapp.com.csr
    ├── serverCertificate_20240101_webapp.com.crt
    ├── serverCertificate_20240101_webapp.com.p12
    ├── serverCertificate_20240101_webapp.com.p12.pass
    ├── clientCertificate_20240101_JohnDoe.key
    ├── clientCertificate_20240101_JohnDoe.csr
    ├── clientCertificate_20240101_JohnDoe.crt
    ├── clientCertificate_20240101_JohnDoe.p12
    └── clientCertificate_20240101_JohnDoe.p12.pass
```

---

## Security Best Practices

⚠️ **IMPORTANT SECURITY CONSIDERATIONS:**

1. **Private Keys & Passwords**
   - Never commit private keys (`.key`) or password files (`.pass`) to version control
   - Use restrictive permissions: `chmod 600` for keys, `chmod 400` for CA key
   - Store passwords securely (consider using a password manager)

2. **CA Protection**
   - Backup CA files (`ca.key`, `ca.crt`, `ca.pass`) in a secure, encrypted location
   - The CA private key is the root of trust - if compromised, all certificates are compromised
   - Consider using hardware security modules (HSM) for production CAs

3. **Certificate Validity**
   - Set appropriate expiration dates (shorter for certificates, longer for CA)
   - Regularly update CRLs before they expire
   - Monitor certificate expiration dates

4. **Repository Security**
   - Use `.gitignore` to exclude sensitive files
   - Consider using a private, encrypted Git repository
   - Never share CA private keys or passwords

5. **Access Control**
   - Limit access to CA directory to authorized personnel only
   - Use separate CAs for different environments (dev, staging, production)

---

## 🔧 Troubleshooting

### Common Issues

**Error: "organizationName field is different between CA certificate and the request"**
- **Cause:** CA policy requires organization to match
- **Solution:** Don't define `CRT_O`, PKI-Manager will automatically extract it from the CA
- **Alternative:** Define `CRT_O` with the same value used to create the CA

**Error: "project doesn't exist yet"**
- **Cause:** The CA project doesn't exist yet
- **Solution:** Create the CA first with `./pki ca create -p <name> -a <algo>`
- **Verification:** Project name must match exactly (case-sensitive)

**Error: "ca.cnf not found"**
- **Cause:** The project directory is not a valid CA
- **Solution:** Recreate the CA with `./pki ca create`
- **Note:** CA must be created with a recent version including CRL support

**Error: "Failed to sign certificate with 'openssl ca'"**
- **Cause:** Certificate subject doesn't match CA policy
- **Solution:** Verify that organization matches (see first error)
- **Verification:** Check `ca.cnf` for policies (`policy_match`)

**Certificate verification fails**
- **Verify with CA:** `openssl verify -CAfile project/ca.crt certificate.crt`
- **Check expiration:** `openssl x509 -in certificate.crt -noout -dates`
- **Verify chain:** Ensure certificate is signed by the CA

**CRL not updating**
- **Permissions:** Check write permissions in project directory
- **Files:** Verify that `ca.key` and `ca.pass` are accessible
- **Directory:** Verify that `crl/` directory exists

**PKCS#12 import fails**
- **Password:** Verify that `.p12.pass` file exists and contains the correct password
- **Test:** `openssl pkcs12 -info -in file.p12 -passin file:file.p12.pass`
- **Note:** Some systems require interactive password entry

### Getting Help

Each script provides help information:

```bash
./pki ca --help
./pki cert -h
./pki crl -h
```

### Debugging

Test OpenSSL configuration:

```bash
# Test CA configuration
openssl ca -config demo/ca.cnf -help

# Verify a certificate
openssl x509 -in certificate.crt -text -noout

# Verify CRL
openssl crl -in demo/crl/ca.crl -text -noout

# Verify a PKCS#12 file
openssl pkcs12 -info -in certificate.p12 -passin file:certificate.p12.pass
```

### Debugging Tips

1. **Check permissions:** Ensure you have read/write rights
2. **Check paths:** Use absolute paths if necessary
3. **Check files:** Ensure all required files exist
4. **Check logs:** OpenSSL error messages are usually explicit

---

## License

See the `LICENSE.md` file for license information.

---

## Contributing

Contributions are welcome! Please ensure:
- Scripts follow bash best practices
- Error handling is comprehensive
- Documentation is updated
- Security considerations are maintained
