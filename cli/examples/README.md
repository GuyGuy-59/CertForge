# PKI-Manager Usage Examples

This directory contains configuration examples and use cases for PKI-Manager.

## Available Files

### `example_cert.cnf`
Custom OpenSSL configuration file with detailed comments explaining each section. Use this file as a reference to create your own configurations.

## Practical Examples

### Example 1: Simple Server Certificate

```bash
# 1. Create a Certificate Authority
./pki ca create -p mycompany -a ec

# 2. Generate a server certificate for a domain
./pki cert -p mycompany -t server -a ec -n "www.mycompany.com"
```

### Example 2: Server Certificate with Multiple Domains (SAN)

```bash
# Set Subject Alternative Names
export CRT_SAN="DNS:mycompany.com,DNS:www.mycompany.com,DNS:api.mycompany.com,IP:192.168.1.100"

# Generate the certificate
./pki cert -p mycompany -t server -a ec -n "mycompany.com"
```

### Example 3: Server Certificate with Custom Configuration File

```bash
# Copy and modify the example
cp examples/example_cert.cnf my_server.cnf
# Edit my_server.cnf according to your needs

# Generate the certificate with custom configuration
./pki cert -p mycompany -t server -a ec -n "example.com" -c my_server.cnf
```

### Example 4: Client Certificate for Authentication

```bash
# Generate a client certificate for a user
export CRT_O="My Company" CRT_OU="IT Department"
./pki cert -p mycompany -t client -a ec -n "John Doe"
```

### Example 5: Complete Workflow for a Web Server

```bash
# Step 1: Create the CA with a custom organization
export CA_O="My Company" CA_OU="IT Security" CA_EXPIRE_DAYS=1825
./pki ca create -p webapp -a ec

# Step 2: Generate a server certificate with SAN
export CRT_SAN="DNS:webapp.com,DNS:www.webapp.com,DNS:*.webapp.com"
./pki cert -p webapp -t server -a ec -n "webapp.com"

# Step 3: Verify the certificate
openssl x509 -in webapp/serverCertificate_*.crt -text -noout | grep -A 2 "Subject Alternative Name"
```

### Example 6: Certificate for LDAP Server

```bash
# Create the CA
export CA_O="serval CA" CA_EXPIRE_DAYS=730
./pki ca create -p serval -a ec

# Generate the certificate with SAN for LDAP
export CRT_SAN="DNS:ldap.serval.int,IP:192.168.134.10"
./pki cert -p serval -t server -a ec -n "ldap.serval.int"

# The .p12 certificate is automatically generated for Windows installation
```

## Important Notes

1. **Organization Matching**: If your CA uses `policy_match` for `organizationName`, ensure that certificates use the same organization. PKI-Manager automatically extracts the organization from the CA if `CRT_O` is not defined.

2. **Subject Alternative Names (SAN)**: For server certificates, always use SAN to include all necessary domains and IPs.

3. **Generated Files**:
   - Server certificates: `.crt`, `.key`, `.p12` (and `.p12.pass`)
   - Client certificates: `.crt`, `.key`, `.p12` (and `.p12.pass`)

4. **Installation**:
   - Linux/Unix: Use `.crt` and `.key` files
   - Windows: Use the `.p12` file (can be renamed to `.pfx`)

## Need Help?

See the [main README](../README.md) for more details on all available options.
