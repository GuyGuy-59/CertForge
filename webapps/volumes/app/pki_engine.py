import os
import datetime
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519
from cryptography.hazmat.primitives.serialization import pkcs12

ALGORITHMS = [
    ('ec-p384',  'EC P-384 (secp384r1)',  'safe',    'NIST P-384 · 192-bit · FIPS approved · recommended'),
    ('ec-p521',  'EC P-521 (secp521r1)',  'safe',    'NIST P-521 · 260-bit · FIPS approved · strongest NIST curve'),
    ('ed25519',  'Ed25519',               'safe',    'Ed25519 · 128-bit · very fast · modern · RFC 8410 · non-FIPS'),
    ('ec-p256',  'EC P-256 (prime256v1)', 'safe',    'NIST P-256 · 128-bit · maximum compatibility'),
    ('rsa-4096', 'RSA 4096-bit',          'safe',    'RSA 4096 · strong, but ~10x slower than EC'),
    ('rsa-2048', 'RSA 2048-bit',          'warning', 'RSA 2048 · minimum acceptable · prefer EC for a new PKI'),
]


def _write(path: str, data: bytes, mode: int = 0o644) -> None:
    if os.path.exists(path):
        os.chmod(path, 0o644)
    with open(path, 'wb') as f:
        f.write(data)
    os.chmod(path, mode)


def generate_key(algo: str):
    if algo in ('ec', 'ec-p384'):
        return ec.generate_private_key(ec.SECP384R1())
    if algo == 'ec-p521':
        return ec.generate_private_key(ec.SECP521R1())
    if algo == 'ed25519':
        return ed25519.Ed25519PrivateKey.generate()
    if algo == 'ec-p256':
        return ec.generate_private_key(ec.SECP256R1())
    if algo in ('rsa', 'rsa-4096'):
        return rsa.generate_private_key(65537, 4096)
    if algo == 'rsa-2048':
        return rsa.generate_private_key(65537, 2048)
    raise ValueError(f"Unknown algorithm: {algo}")


def _sign_hash(key):
    if isinstance(key, ed25519.Ed25519PrivateKey):
        return None  # Ed25519 has built-in hash, must pass None to .sign()
    if isinstance(key, ec.EllipticCurvePrivateKey):
        return hashes.SHA512() if isinstance(key.curve, ec.SECP521R1) else hashes.SHA384()
    return hashes.SHA256()


def _key_pem(key) -> bytes:
    fmt = (serialization.PrivateFormat.PKCS8
           if isinstance(key, ed25519.Ed25519PrivateKey)
           else serialization.PrivateFormat.TraditionalOpenSSL)
    return key.private_bytes(serialization.Encoding.PEM, fmt, serialization.NoEncryption())


def _algo_name(key) -> str:
    if isinstance(key, ed25519.Ed25519PrivateKey):
        return 'Ed25519'
    if isinstance(key, ec.EllipticCurvePrivateKey):
        if isinstance(key.curve, ec.SECP521R1):
            return 'EC P-521'
        if isinstance(key.curve, ec.SECP384R1):
            return 'EC P-384'
        return 'EC P-256'
    return f'RSA {key.key_size}'


def _subject(cn, org='', ou='', country='FR', locality='Paris'):
    attrs = [
        x509.NameAttribute(NameOID.COUNTRY_NAME, country or 'FR'),
        x509.NameAttribute(NameOID.LOCALITY_NAME, locality or 'Paris'),
    ]
    if org:
        attrs.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, org))
    if ou:
        attrs.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, ou))
    attrs.append(x509.NameAttribute(NameOID.COMMON_NAME, cn))
    return x509.Name(attrs)


def _aia_extensions(base_url: str, ca_name: str):
    crl_url = f"{base_url}/aia/{ca_name}/crl.crl"
    ca_url = f"{base_url}/aia/{ca_name}/ca.crt"
    crl_dp = x509.CRLDistributionPoints([
        x509.DistributionPoint(
            full_name=[x509.UniformResourceIdentifier(crl_url)],
            relative_name=None, reasons=None, crl_issuer=None,
        )
    ])
    aia = x509.AuthorityInformationAccess([
        x509.AccessDescription(
            x509.AuthorityInformationAccessOID.CA_ISSUERS,
            x509.UniformResourceIdentifier(ca_url),
        )
    ])
    return crl_dp, aia


def _index_add(ca_dir: str, cert: x509.Certificate, cn: str) -> None:
    index_path = os.path.join(ca_dir, 'index.txt')
    not_after = cert.not_valid_after_utc.strftime('%y%m%d%H%M%SZ')
    serial_hex = f'{cert.serial_number:X}'
    line = f'V\t{not_after}\t\t{serial_hex}\tunknown\t/CN={cn}\n'
    with open(index_path, 'a') as f:
        f.write(line)


def _init_ca_dir(ca_dir: str) -> None:
    os.makedirs(ca_dir, exist_ok=True)
    os.makedirs(os.path.join(ca_dir, 'newcerts'), exist_ok=True)
    os.makedirs(os.path.join(ca_dir, 'crl'), exist_ok=True)
    for fname, content in [('index.txt', b''), ('index.txt.attr', b'unique_subject = yes\n')]:
        p = os.path.join(ca_dir, fname)
        if not os.path.exists(p):
            _write(p, content)
    for fname in ['ca.srl', 'crlnumber']:
        p = os.path.join(ca_dir, fname)
        if not os.path.exists(p):
            _write(p, b'01\n')


def _next_serial(ca_dir: str) -> int:
    serial_path = os.path.join(ca_dir, 'ca.srl')
    with open(serial_path) as f:
        serial_hex = f.read().strip()
    serial_num = int(serial_hex, 16)
    _write(serial_path, f'{serial_num + 1:02X}\n'.encode())
    return serial_num


def create_ca(ca_dir: str, cn: str, org='', ou='', country='FR', locality='Paris',
              algo='ec-p384', expire_days=3650, crl_expire_days=30) -> None:
    _init_ca_dir(ca_dir)
    key = generate_key(algo)
    subject = _subject(cn, org, ou, country, locality)
    now = datetime.datetime.now(datetime.timezone.utc)

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=expire_days))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .add_extension(x509.KeyUsage(
            digital_signature=True, key_cert_sign=True, crl_sign=True,
            content_commitment=False, key_encipherment=False, data_encipherment=False,
            key_agreement=False, encipher_only=False, decipher_only=False,
        ), critical=True)
        .sign(key, _sign_hash(key))
    )

    _write(os.path.join(ca_dir, 'ca.key'), _key_pem(key), 0o400)
    _write(os.path.join(ca_dir, 'ca.crt'), cert.public_bytes(serialization.Encoding.PEM))
    _build_crl(ca_dir, cert, key, crl_expire_days)


def create_intermediate_ca(ca_dir: str, parent_ca_dir: str, cn: str, org='', ou='',
                            country='FR', locality='Paris', algo='ec-p384',
                            expire_days=1825, crl_expire_days=30, base_url='') -> None:
    _init_ca_dir(ca_dir)

    with open(os.path.join(parent_ca_dir, 'ca.crt'), 'rb') as f:
        parent_cert = x509.load_pem_x509_certificate(f.read())
    with open(os.path.join(parent_ca_dir, 'ca.key'), 'rb') as f:
        parent_key = serialization.load_pem_private_key(f.read(), password=None)

    serial_num = _next_serial(parent_ca_dir)
    key = generate_key(algo)
    subject = _subject(cn, org, ou, country, locality)
    now = datetime.datetime.now(datetime.timezone.utc)

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(parent_cert.subject)
        .public_key(key.public_key())
        .serial_number(serial_num)
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=expire_days))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(parent_cert.public_key()), critical=False)
        .add_extension(x509.KeyUsage(
            digital_signature=True, key_cert_sign=True, crl_sign=True,
            content_commitment=False, key_encipherment=False, data_encipherment=False,
            key_agreement=False, encipher_only=False, decipher_only=False,
        ), critical=True)
    )

    if base_url:
        crl_dp, aia = _aia_extensions(base_url, os.path.basename(parent_ca_dir))
        builder = builder.add_extension(crl_dp, critical=False).add_extension(aia, critical=False)

    cert = builder.sign(parent_key, _sign_hash(parent_key))

    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    parent_pem = parent_cert.public_bytes(serialization.Encoding.PEM)

    _write(os.path.join(ca_dir, 'ca.key'), _key_pem(key), 0o400)
    _write(os.path.join(ca_dir, 'ca.crt'), cert_pem)
    _write(os.path.join(ca_dir, 'ca-chain.crt'), cert_pem + parent_pem)
    _write(os.path.join(ca_dir, 'parent'), os.path.basename(parent_ca_dir).encode())

    # Record in parent
    serial_hex = f'{serial_num:X}'
    _index_add(parent_ca_dir, cert, cn)
    _write(os.path.join(parent_ca_dir, 'newcerts', f'{serial_hex}.pem'), cert_pem)

    _build_crl(ca_dir, cert, key, crl_expire_days)


def issue_certificate(ca_dir: str, cn: str, cert_type: str = 'server',
                      algo: str = 'ec-p384', expire_days: int = 365,
                      san_str: str = '', base_url: str = '') -> dict:
    with open(os.path.join(ca_dir, 'ca.crt'), 'rb') as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())
    with open(os.path.join(ca_dir, 'ca.key'), 'rb') as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)

    serial_num = _next_serial(ca_dir)
    serial_hex = f'{serial_num:X}'
    key = generate_key(algo)
    now = datetime.datetime.now(datetime.timezone.utc)

    sans = []
    for s in (san_str or '').split(','):
        s = s.strip()
        if not s:
            continue
        try:
            sans.append(x509.IPAddress(ipaddress.ip_address(s)))
        except ValueError:
            sans.append(x509.DNSName(s))
    if not sans:
        sans.append(x509.DNSName(cn))

    builder = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)]))
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(serial_num)
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=expire_days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_cert.public_key()), critical=False)
        .add_extension(x509.SubjectAlternativeName(sans), critical=False)
    )

    if cert_type == 'server':
        builder = (builder
            .add_extension(x509.KeyUsage(
                digital_signature=True, key_encipherment=True, content_commitment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=False,
                crl_sign=False, encipher_only=False, decipher_only=False,
            ), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False))
    else:
        builder = (builder
            .add_extension(x509.KeyUsage(
                digital_signature=True, key_encipherment=False, content_commitment=True,
                data_encipherment=False, key_agreement=False, key_cert_sign=False,
                crl_sign=False, encipher_only=False, decipher_only=False,
            ), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False))

    ca_name = os.path.basename(ca_dir)
    if base_url:
        crl_dp, aia = _aia_extensions(base_url, ca_name)
        builder = builder.add_extension(crl_dp, critical=False).add_extension(aia, critical=False)

    cert = builder.sign(ca_key, _sign_hash(ca_key))

    key_pem = _key_pem(key)
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    pub_pem = key.public_key().public_bytes(serialization.Encoding.PEM,
                                            serialization.PublicFormat.SubjectPublicKeyInfo)

    base = cn.replace('/', '_').replace(' ', '_').replace('*', 'wildcard')
    _write(os.path.join(ca_dir, 'newcerts', f'{serial_hex}.pem'), cert_pem)
    _write(os.path.join(ca_dir, f'{base}.crt'), cert_pem)
    _write(os.path.join(ca_dir, f'{base}.key'), key_pem, 0o400)

    # PKCS#12 — include chain if intermediate
    chain_path = os.path.join(ca_dir, 'ca-chain.crt')
    if os.path.exists(chain_path):
        chain_certs = []
        with open(chain_path, 'rb') as f:
            data = f.read()
        for chunk in data.split(b'-----END CERTIFICATE-----'):
            chunk = chunk.strip()
            if chunk:
                chain_certs.append(
                    x509.load_pem_x509_certificate(chunk + b'\n-----END CERTIFICATE-----\n')
                )
    else:
        chain_certs = [ca_cert]

    p12 = pkcs12.serialize_key_and_certificates(
        cn.encode(), key, cert, chain_certs, serialization.NoEncryption()
    )
    _write(os.path.join(ca_dir, f'{base}.p12'), p12)

    _index_add(ca_dir, cert, cn)

    return {
        'base': base,
        'serial': serial_hex,
        'not_before': cert.not_valid_before_utc.strftime('%Y-%m-%d'),
        'not_after': cert.not_valid_after_utc.strftime('%Y-%m-%d'),
        'fingerprint': cert.fingerprint(hashes.SHA256()).hex(':'),
        'public_key_pem': pub_pem.decode(),
        'algo': _algo_name(key),
    }


def revoke_certificate(ca_dir: str, serial_hex: str) -> None:
    index_path = os.path.join(ca_dir, 'index.txt')
    lines = []
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime('%y%m%d%H%M%SZ')
    with open(index_path) as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if (len(parts) >= 4 and parts[0] == 'V'
                    and parts[3].upper() == serial_hex.upper()):
                # V expiry  \t\t serial ... → R expiry revtime serial ...
                parts[0] = 'R'
                parts[2] = now_str
                line = '\t'.join(parts) + '\n'
            lines.append(line)
    with open(index_path, 'w') as f:
        f.writelines(lines)

    with open(os.path.join(ca_dir, 'ca.crt'), 'rb') as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())
    with open(os.path.join(ca_dir, 'ca.key'), 'rb') as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)

    crl_expire_days = 30
    crl_path = os.path.join(ca_dir, 'crl', 'ca.crl')
    if os.path.exists(crl_path):
        try:
            with open(crl_path, 'rb') as f:
                old_crl = x509.load_pem_x509_crl(f.read())
            delta = old_crl.next_update_utc - old_crl.last_update_utc
            crl_expire_days = max(1, delta.days)
        except Exception:
            pass

    _build_crl(ca_dir, ca_cert, ca_key, crl_expire_days)


def _build_crl(ca_dir: str, ca_cert: x509.Certificate, ca_key, crl_expire_days: int) -> None:
    os.makedirs(os.path.join(ca_dir, 'crl'), exist_ok=True)
    crlnum_path = os.path.join(ca_dir, 'crlnumber')
    with open(crlnum_path) as f:
        crl_num = int(f.read().strip(), 16)
    _write(crlnum_path, f'{crl_num + 1:02X}\n'.encode())

    now = datetime.datetime.now(datetime.timezone.utc)
    builder = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(ca_cert.subject)
        .last_update(now)
        .next_update(now + datetime.timedelta(days=crl_expire_days))
        .add_extension(x509.CRLNumber(crl_num), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_cert.public_key()), critical=False)
    )

    index_path = os.path.join(ca_dir, 'index.txt')
    if os.path.exists(index_path):
        with open(index_path) as f:
            for line in f:
                parts = line.strip().split('\t')
                if parts and parts[0] == 'R' and len(parts) >= 4:
                    try:
                        serial_num = int(parts[3], 16)
                        try:
                            rev_time = datetime.datetime.strptime(
                                parts[2], '%y%m%d%H%M%SZ'
                            ).replace(tzinfo=datetime.timezone.utc)
                        except Exception:
                            rev_time = now
                        rc = (
                            x509.RevokedCertificateBuilder()
                            .serial_number(serial_num)
                            .revocation_date(rev_time)
                            .add_extension(
                                x509.CRLReason(x509.ReasonFlags.unspecified), critical=False
                            )
                            .build()
                        )
                        builder = builder.add_revoked_certificate(rc)
                    except Exception:
                        pass

    crl = builder.sign(ca_key, _sign_hash(ca_key))
    _write(os.path.join(ca_dir, 'crl', 'ca.crl'), crl.public_bytes(serialization.Encoding.PEM))
    _write(os.path.join(ca_dir, 'crl', 'ca.crl.der'), crl.public_bytes(serialization.Encoding.DER))
