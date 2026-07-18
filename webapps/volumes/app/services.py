"""
Service layer — orchestrates PKI operations (pki_engine) with filesystem paths
derived from config. Routes call this module; nothing here touches Flask.
"""

import os
import config
import pki_engine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ca_dir(name: str) -> str:
    return os.path.join(config.CA_BASE, name)


def _read_file(path: str) -> str | None:
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


# ---------------------------------------------------------------------------
# CA listing / detail
# ---------------------------------------------------------------------------

def list_cas() -> list[dict]:
    if not os.path.exists(config.CA_BASE):
        return []
    cas = []
    for name in sorted(os.listdir(config.CA_BASE)):
        d = ca_dir(name)
        if os.path.isdir(d) and os.path.exists(os.path.join(d, 'ca.crt')):
            parent = _read_file(os.path.join(d, 'parent'))
            cas.append({
                'name': name,
                'is_intermediate': parent is not None,
                'parent': parent,
            })
    return cas


def get_ca_info(name: str) -> dict:
    d = ca_dir(name)
    parent = _read_file(os.path.join(d, 'parent'))
    return {
        'exists': os.path.isdir(d) and os.path.exists(os.path.join(d, 'ca.crt')),
        'parent': parent,
        'chain_exists': os.path.exists(os.path.join(d, 'ca-chain.crt')),
        'aia_ca':  f'{config.BASE_URL}/aia/{name}/ca.crt'  if config.BASE_URL else None,
        'aia_crl': f'{config.BASE_URL}/aia/{name}/crl.crl' if config.BASE_URL else None,
    }


# ---------------------------------------------------------------------------
# CA creation
# ---------------------------------------------------------------------------

def create_root_ca(name: str, cn: str, org='', ou='', country='FR',
                   locality='Paris', algo='ec-p384', expire_days=3650) -> None:
    pki_engine.create_ca(
        ca_dir(name), cn, org, ou, country, locality, algo, expire_days,
    )


def create_intermediate_ca(name: str, parent_name: str, cn: str, org='', ou='',
                            country='FR', locality='Paris', algo='ec-p384',
                            expire_days=1825) -> None:
    pki_engine.create_intermediate_ca(
        ca_dir(name), ca_dir(parent_name), cn, org, ou,
        country, locality, algo, expire_days, 30, config.BASE_URL,
    )


# ---------------------------------------------------------------------------
# Certificate operations
# ---------------------------------------------------------------------------

def issue_cert(ca_name: str, cn: str, cert_type='server', algo='ec-p384',
               expire_days=365, san_str='') -> dict:
    return pki_engine.issue_certificate(
        ca_dir(ca_name), cn, cert_type, algo, expire_days, san_str, config.BASE_URL,
    )


def revoke_cert(ca_name: str, serial: str) -> None:
    pki_engine.revoke_certificate(ca_dir(ca_name), serial)
