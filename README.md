# PKI-Manager

A comprehensive set of bash scripts for managing a complete Public Key Infrastructure (PKI). Create Certificate Authorities (CA), generate server and client certificates, and manage Certificate Revocation Lists (CRL) with ease.

## Features

- ✅ **Certificate Authority (CA) Generation** - Create self-signed root CAs with RSA or ECC algorithms
- ✅ **Server & Client Certificates** - Generate X.509 certificates and PKCS#12 containers (.p12/.pfx) for both servers and clients
- ✅ **CRL Management** - Revoke certificates and maintain Certificate Revocation Lists
- ✅ **Flexible Configuration** - Customize certificate attributes via environment variables or custom OpenSSL config files
- ✅ **Subject Alternative Names (SAN)** - Support for multiple DNS names and IP addresses
- ✅ **Algorithm Support** - RSA (4096-bit) and Elliptic Curve (secp384r1) cryptography

## 📦 Prérequis

- **OpenSSL** (version 1.1.1 ou supérieure recommandée)
- **Bash** (version 4.0 ou supérieure)
- **Environnement Unix-like** (Linux, macOS, WSL sur Windows)

### Vérifier l'installation

```bash
openssl version
bash --version
```

## 💡 Concepts de base

### Qu'est-ce qu'une PKI ?

Une **Public Key Infrastructure (PKI)** est un système qui permet de gérer des certificats numériques. Elle comprend :

1. **Autorité de certification (CA)** : L'entité racine qui signe et valide les certificats
2. **Certificats** : Documents numériques qui lient une clé publique à une identité
3. **Liste de révocation (CRL)** : Liste des certificats révoqués avant leur expiration

### Types de certificats

- **Certificat serveur** : Utilisé pour authentifier un serveur (site web, API, etc.)
  - Format : `.crt` (X.509) + `.p12` (PKCS#12 pour Windows)
  - Clé privée : Sans mot de passe par défaut (pour services automatisés)

- **Certificat client** : Utilisé pour authentifier un utilisateur ou un appareil
  - Format : `.p12` (PKCS#12, pour navigateur/OS)
  - Clé privée : Protégée par mot de passe par défaut

### Formats de fichiers

- **`.crt`** : Certificat public au format X.509 (standard)
- **`.key`** : Clé privée (à garder secrète !)
- **`.p12` / `.pfx`** : Conteneur PKCS#12 contenant certificat + clé privée (pour Windows/navigateurs)
- **`.csr`** : Certificate Signing Request (demande de signature)

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

## 🚀 Démarrage rapide

### Méthode recommandée : Utiliser le script wrapper

```bash
# 1. Créer une autorité de certification (CA)
./pki ca create -p demo -a ec

# 2. Générer un certificat serveur
./pki cert -p demo -t server -a ec -n "example.com"

# 3. Générer un certificat client
./pki cert -p demo -t client -a ec -n "John Doe"
```

### Méthode alternative : Utiliser les scripts directement

```bash
# Créer une CA
./bin/pki-ca create -p demo -a ec

# Générer des certificats
./bin/pki-cert -p demo -t server -a ec -n "example.com"
./bin/pki-cert -p demo -t client -a ec -n "John Doe"

# Gérer la révocation
./bin/pki-crl -p demo -r 01 -u
```

## 📋 Guide pas à pas

### Étape 1 : Créer une autorité de certification (CA)

La CA est la racine de confiance qui signera tous vos certificats.

```bash
./pki ca create -p demo -a ec
```

**Ce qui est créé :**
- `demo/ca.key` - Clé privée de la CA (protégée par mot de passe)
- `demo/ca.crt` - Certificat auto-signé de la CA
- `demo/ca.cnf` - Configuration OpenSSL
- `demo/crl/` - Infrastructure pour les listes de révocation

**Choisir l'algorithme :**
- `-a ec` : Elliptic Curve (recommandé, plus rapide, 384 bits)
- `-a rsa` : RSA 4096 bits (compatibilité maximale)

### Étape 2 : Générer des certificats

#### Certificat serveur (pour sites web, API, etc.)

```bash
./pki cert -p demo -t server -a ec -n "example.com"
```

**Fichiers générés :**
- `serverCertificate_*.crt` - Certificat public
- `serverCertificate_*.key` - Clé privée (sans mot de passe par défaut)
- `serverCertificate_*.p12` - Conteneur PKCS#12 (pour Windows)
- `serverCertificate_*.p12.pass` - Mot de passe du fichier .p12

**Avec plusieurs domaines (SAN) :**
```bash
export CRT_SAN="DNS:example.com,DNS:www.example.com,DNS:*.example.com,IP:192.168.1.1"
./pki cert -p demo -t server -a ec -n "example.com"
```

#### Certificat client (pour authentification utilisateur)

```bash
./pki cert -p demo -t client -a ec -n "John Doe"
```

**Fichiers générés :**
- `clientCertificate_*.crt` - Certificat public
- `clientCertificate_*.key` - Clé privée (protégée par mot de passe)
- `clientCertificate_*.p12` - Conteneur PKCS#12 (pour navigateur/OS)
- `clientCertificate_*.p12.pass` - Mot de passe du fichier .p12

### Étape 3 : Gérer la révocation de certificats

Si un certificat est compromis ou n'est plus nécessaire :

```bash
# Révoker un certificat et mettre à jour la CRL
./pki crl -p demo -r 01 -u
```

**Trouver le numéro de série :**
```bash
openssl x509 -in demo/serverCertificate_*.crt -noout -serial
```

## 📚 Vue d'ensemble des commandes

| Commande | Description | Fonctionnalités principales |
|----------|-------------|------------------------------|
| `pki ca` | Créer une autorité de certification | Génère la clé/certificat CA, initialise l'infrastructure CRL |
| `pki cert` | Générer des certificats | Certificats serveur (X.509) et client (PKCS#12) |
| `pki crl` | Gérer la CRL | Révoquer des certificats, mettre à jour les listes de révocation |

## ⚙️ Configuration personnalisée

### Variables d'environnement

Vous pouvez personnaliser les certificats via des variables d'environnement :

**Pour la CA :**
```bash
export CA_C="FR"                    # Code pays (2 lettres)
export CA_L="Paris"                 # Localité
export CA_O="Mon Entreprise"        # Organisation
export CA_OU="IT Security"           # Unité organisationnelle
export CA_EXPIRE_DAYS=1825           # Durée de validité (5 ans)
./pki ca create -p myproject -a ec
```

**Pour les certificats :**
```bash
export CRT_C="FR"                    # Code pays
export CRT_L="Paris"                 # Localité
export CRT_O="Mon Entreprise"       # Organisation (doit correspondre au CA si policy_match)
export CRT_OU="DevOps"               # Unité organisationnelle
export CRT_SAN="DNS:example.com,DNS:www.example.com,IP:192.168.1.1"  # Noms alternatifs
export CRT_EXPIRE_DAYS=365           # Durée de validité
./pki cert -p myproject -t server -a ec -n "example.com"
```

**Note importante :** Si vous ne définissez pas `CRT_O`, PKI-Manager extrait automatiquement l'organisation du certificat CA pour garantir la correspondance avec la politique.

## 📖 Documentation détaillée

### 1. Création d'une autorité de certification

**Commande :** `pki ca create`

#### Syntaxe

```bash
./pki ca create -p <nom_projet> -a <algorithme>
```

#### Options

| Option | Description | Requis |
|--------|-------------|--------|
| `-p <nom_projet>` | Nom du projet (crée un répertoire avec ce nom) | ✅ Oui |
| `-a <algorithme>` | Algorithme de chiffrement : `rsa` ou `ec` | ✅ Oui |

#### Comparaison des algorithmes

| Algorithme | Taille de clé | Performance | Cas d'usage |
|------------|---------------|-------------|-------------|
| **RSA** | 4096 bits | Plus lent | Compatibilité maximale |
| **EC** (secp384r1) | 384 bits | Plus rapide | Systèmes modernes (recommandé) |

#### Variables d'environnement pour la CA

| Variable | Description | Par défaut |
|----------|-------------|------------|
| `CA_C` | Code pays (2 lettres) | `FR` |
| `CA_L` | Localité/Ville | `Paris` |
| `CA_O` | Organisation | `France` |
| `CA_OU` | Unité organisationnelle | `DevOps` |
| `CA_CN` | Nom commun | Nom du projet |
| `CA_EXPIRE_DAYS` | Durée de validité CA (jours) | `365` |
| `CRL_EXPIRE_DAYS` | Durée de validité CRL (jours) | `30` |

#### Exemples

**Création basique d'une CA :**
```bash
./pki ca create -p myproject -a ec
```

**CA personnalisée :**
```bash
export CA_O="Mon Entreprise" CA_OU="Sécurité IT" CA_EXPIRE_DAYS=1825
./pki ca create -p production -a ec
```

**CA pour un environnement de développement :**
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

#### Exemples

**Certificat serveur basique :**
```bash
./pki cert -p demo -t server -a ec -n "api.example.com"
```

**Certificat serveur avec SAN (plusieurs domaines) :**
```bash
export CRT_SAN="DNS:api.example.com,DNS:www.example.com,IP:192.168.1.1"
./pki cert -p demo -t server -a ec -n "api.example.com"
```

**Certificat client :**
```bash
export CRT_O="Mon Entreprise" CRT_OU="Développement"
./pki cert -p demo -t client -a ec -n "Jean Dupont"
```

**Utilisation d'un fichier de configuration personnalisé :**
```bash
./pki cert -p demo -t server -a ec -n "example.com" -c examples/example_cert.cnf
```

**Certificat serveur pour LDAP :**
```bash
export CRT_SAN="DNS:ldap.example.com,IP:192.168.1.10"
./pki cert -p demo -t server -a ec -n "ldap.example.com"
```

#### Fichiers générés

**Pour les certificats serveur :**
- `<type>Certificate_<timestamp>_<name>.key` - Clé privée
- `<type>Certificate_<timestamp>_<name>.csr` - Demande de signature de certificat
- `<type>Certificate_<timestamp>_<name>.crt` - Certificat signé
- `<type>Certificate_<timestamp>_<name>.p12` - Conteneur PKCS#12 (certificat + clé privée)
- `<type>Certificate_<timestamp>_<name>.p12.pass` - Mot de passe du fichier .p12

**Pour les certificats client :**
- Tous les fichiers ci-dessus (même structure que les certificats serveur)
- Le fichier `.p12` est principalement utilisé pour l'import dans le navigateur/OS

#### Afficher les informations d'un certificat

```bash
# Afficher les détails complets du certificat
openssl x509 -in certificate.crt -text -noout

# Afficher le sujet du certificat
openssl x509 -in certificate.crt -noout -subject

# Afficher le numéro de série
openssl x509 -in certificate.crt -noout -serial

# Vérifier le certificat contre la CA
openssl verify -CAfile demo/ca.crt certificate.crt

# Pour les fichiers PKCS#12
openssl pkcs12 -info -in certificate.p12 -passin file:certificate.p12.pass
```

---

### 3. Gestion de la CRL (Liste de révocation)

**Commande :** `pki crl`

#### Syntaxe

```bash
./pki crl -p <nom_projet> [-r <numéro_série>] [-u]
```

#### Options

| Option | Description | Requis |
|--------|-------------|--------|
| `-p <nom_projet>` | Nom du projet (doit correspondre à un projet CA existant) | ✅ Oui |
| `-r <numéro_série>` | Numéro de série du certificat à révoquer (format hex) | ❌ Optionnel |
| `-u` | Mettre à jour la CRL (utiliser avec `-r` ou seul) | ❌ Optionnel |

#### Exemples

**Révoquer un certificat et mettre à jour la CRL :**
```bash
./pki crl -p demo -r 01 -u
```

**Mettre à jour la CRL sans révoquer :**
```bash
./pki crl -p demo -u
```

**Révoquer uniquement (la CRL sera mise à jour automatiquement) :**
```bash
./pki crl -p demo -r 02
```

#### Trouver le numéro de série d'un certificat

**Depuis le fichier certificat :**
```bash
openssl x509 -in certificate.crt -noout -serial
```

**Depuis la base de données de la CA :**
```bash
cat demo/index.txt
```

**Lister tous les certificats :**
```bash
# Afficher tous les certificats émis
cat demo/index.txt | grep "^V"

# Afficher les certificats révoqués
cat demo/index.txt | grep "^R"
```

#### Vérifier la CRL

```bash
# Afficher le contenu de la CRL
openssl crl -in demo/crl/ca.crl -text -noout

# Compter les certificats révoqués
openssl crl -in demo/crl/ca.crl -text -noout | grep -c "Serial Number:"

# Vérifier si un numéro de série spécifique est révoqué
openssl crl -in demo/crl/ca.crl -text -noout | grep -A 2 "Serial Number: 01"
```

---

## 🎯 Cas d'usage courants

### Cas d'usage 1 : Certificat pour un serveur web

```bash
# 1. Créer la CA
export CA_O="Mon Entreprise" CA_EXPIRE_DAYS=1825
./pki ca create -p webapp -a ec

# 2. Générer le certificat avec tous les domaines nécessaires
export CRT_SAN="DNS:webapp.com,DNS:www.webapp.com,DNS:*.webapp.com"
./pki cert -p webapp -t server -a ec -n "webapp.com"

# 3. Installer sur le serveur (exemple Nginx)
# - Copier serverCertificate_*.crt vers /etc/ssl/certs/
# - Copier serverCertificate_*.key vers /etc/ssl/private/
```

### Cas d'usage 2 : Certificat pour serveur LDAP/Active Directory

```bash
# 1. Créer la CA
export CA_O="serval CA" CA_EXPIRE_DAYS=730
./pki ca create -p serval -a ec

# 2. Générer le certificat avec DNS et IP
export CRT_SAN="DNS:ldap.serval.int,IP:192.168.134.10"
./pki cert -p serval -t server -a ec -n "ldap.serval.int"

# 3. Utiliser le fichier .p12 pour Windows
# - Renommer .p12 en .pfx si nécessaire
# - Importer dans le magasin de certificats Windows
```

### Cas d'usage 3 : Certificats clients pour authentification

```bash
# 1. Créer la CA (si pas déjà fait)
./pki ca create -p company -a ec

# 2. Générer des certificats pour plusieurs utilisateurs
export CRT_O="Mon Entreprise" CRT_OU="IT Department"
./pki cert -p company -t client -a ec -n "Alice Martin"
./pki cert -p company -t client -a ec -n "Bob Dupont"

# 3. Distribuer les fichiers .p12 aux utilisateurs
# - Le mot de passe est dans le fichier .p12.pass
# - Les utilisateurs peuvent importer dans leur navigateur
```

### Cas d'usage 4 : Certificat wildcard pour sous-domaines

```bash
# Certificat qui couvre tous les sous-domaines
export CRT_SAN="DNS:*.example.com,DNS:example.com"
./pki cert -p demo -t server -a ec -n "*.example.com"
```

---

## 📝 Fichiers de configuration personnalisés

### Utiliser des fichiers `.cnf` personnalisés

Vous pouvez utiliser des fichiers de configuration OpenSSL personnalisés pour définir des extensions avancées, des Subject Alternative Names (SAN), et d'autres options.

#### Fichier de configuration exemple

Consultez `examples/example_cert.cnf` pour un exemple complet avec commentaires détaillés. Le script détecte automatiquement ces sections :

- `[v3_server]` - Pour les certificats serveur
- `[v3_client]` - Pour les certificats client
- `[v3_req]` - Section générique (fallback)

#### Utilisation

```bash
# Copier et personnaliser l'exemple
cp examples/example_cert.cnf my_cert.cnf
# Éditer my_cert.cnf selon vos besoins

# Utiliser avec la génération de certificat
./pki cert -p demo -t server -a ec -n "example.com" -c my_cert.cnf
```

#### Structure du fichier de configuration

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

**Note :** Pour la plupart des cas d'usage, les variables d'environnement (`CRT_SAN`, etc.) sont suffisantes. Utilisez les fichiers `.cnf` uniquement pour des configurations très spécifiques.

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

## 🔧 Dépannage

### Problèmes courants

**Erreur : "organizationName field is different between CA certificate and the request"**
- **Cause :** La politique CA exige que l'organisation corresponde
- **Solution :** Ne définissez pas `CRT_O`, PKI-Manager l'extraira automatiquement du CA
- **Alternative :** Définissez `CRT_O` avec la même valeur que celle utilisée pour créer la CA

**Erreur : "project doesn't exist yet"**
- **Cause :** Le projet CA n'existe pas encore
- **Solution :** Créez d'abord la CA avec `./pki ca create -p <nom> -a <algo>`
- **Vérification :** Le nom du projet doit correspondre exactement (sensible à la casse)

**Erreur : "ca.cnf not found"**
- **Cause :** Le répertoire du projet n'est pas une CA valide
- **Solution :** Recréez la CA avec `./pki ca create`
- **Note :** La CA doit être créée avec une version récente incluant le support CRL

**Erreur : "Failed to sign certificate with 'openssl ca'"**
- **Cause :** Le sujet du certificat ne correspond pas à la politique CA
- **Solution :** Vérifiez que l'organisation correspond (voir première erreur)
- **Vérification :** Consultez `ca.cnf` pour voir les politiques (`policy_match`)

**La vérification du certificat échoue**
- **Vérifier avec la CA :** `openssl verify -CAfile project/ca.crt certificate.crt`
- **Vérifier l'expiration :** `openssl x509 -in certificate.crt -noout -dates`
- **Vérifier la chaîne :** Assurez-vous que le certificat est signé par la CA

**La CRL ne se met pas à jour**
- **Permissions :** Vérifiez les permissions d'écriture dans le répertoire du projet
- **Fichiers :** Vérifiez que `ca.key` et `ca.pass` sont accessibles
- **Répertoire :** Vérifiez que le répertoire `crl/` existe

**L'import PKCS#12 échoue**
- **Mot de passe :** Vérifiez que le fichier `.p12.pass` existe et contient le bon mot de passe
- **Test :** `openssl pkcs12 -info -in file.p12 -passin file:file.p12.pass`
- **Note :** Certains systèmes nécessitent la saisie interactive du mot de passe

### Obtenir de l'aide

Chaque script fournit des informations d'aide :

```bash
./pki ca --help
./pki cert -h
./pki crl -h
```

### Débogage

Testez la configuration OpenSSL :

```bash
# Tester la configuration CA
openssl ca -config demo/ca.cnf -help

# Vérifier un certificat
openssl x509 -in certificate.crt -text -noout

# Vérifier la CRL
openssl crl -in demo/crl/ca.crl -text -noout

# Vérifier un fichier PKCS#12
openssl pkcs12 -info -in certificate.p12 -passin file:certificate.p12.pass
```

### Conseils de débogage

1. **Vérifier les permissions** : Assurez-vous d'avoir les droits de lecture/écriture
2. **Vérifier les chemins** : Utilisez des chemins absolus si nécessaire
3. **Vérifier les fichiers** : Assurez-vous que tous les fichiers requis existent
4. **Consulter les logs** : Les messages d'erreur OpenSSL sont généralement explicites

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
