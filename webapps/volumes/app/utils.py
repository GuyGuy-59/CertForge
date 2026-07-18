"""
X.509 parsing utilities — no database, no Flask, no PKI engine.
Used to inspect certificate files directly from the filesystem.
"""

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa, ed25519


def parse_cert_file(path: str) -> dict | None:
    """
    Load a PEM certificate from *path* and return a metadata dict.
    Returns None if the file is missing or unparseable.
    """
    try:
        with open(path, 'rb') as f:
            data = f.read()
        cert = x509.load_pem_x509_certificate(data)
    except Exception:
        return None

    pub = cert.public_key()
    if isinstance(pub, ec.EllipticCurvePublicKey):
        algo = f'EC {pub.curve.name}'
    elif isinstance(pub, ed25519.Ed25519PublicKey):
        algo = 'Ed25519'
    elif isinstance(pub, rsa.RSAPublicKey):
        algo = f'RSA {pub.key_size}'
    else:
        algo = 'Unknown'

    try:
        cn = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
    except (IndexError, Exception):
        cn = str(cert.subject)

    sans = []
    try:
        ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        sans = [str(v) for v in ext.value]
    except x509.ExtensionNotFound:
        pass

    crl_urls, aia_urls = _parse_distribution_points(cert)

    return {
        'cn': cn,
        'serial': f'{cert.serial_number:X}',
        'not_before': cert.not_valid_before_utc.strftime('%Y-%m-%d'),
        'not_after':  cert.not_valid_after_utc.strftime('%Y-%m-%d'),
        'fingerprint': cert.fingerprint(hashes.SHA256()).hex(':'),
        'algo': algo,
        'sans': sans,
        'crl_urls': crl_urls,
        'aia_urls': aia_urls,
        'is_ca': _is_ca(cert),
    }


def _parse_distribution_points(cert: x509.Certificate) -> tuple[list, list]:
    crl_urls, aia_urls = [], []
    try:
        dp_ext = cert.extensions.get_extension_for_class(x509.CRLDistributionPoints)
        for dp in dp_ext.value:
            if dp.full_name:
                for name in dp.full_name:
                    if isinstance(name, x509.UniformResourceIdentifier):
                        crl_urls.append(name.value)
    except x509.ExtensionNotFound:
        pass
    try:
        aia_ext = cert.extensions.get_extension_for_class(x509.AuthorityInformationAccess)
        for desc in aia_ext.value:
            if desc.access_method == x509.AuthorityInformationAccessOID.CA_ISSUERS:
                if isinstance(desc.access_location, x509.UniformResourceIdentifier):
                    aia_urls.append(desc.access_location.value)
    except x509.ExtensionNotFound:
        pass
    return crl_urls, aia_urls


def _is_ca(cert: x509.Certificate) -> bool:
    try:
        bc = cert.extensions.get_extension_for_class(x509.BasicConstraints)
        return bc.value.ca
    except x509.ExtensionNotFound:
        return False
