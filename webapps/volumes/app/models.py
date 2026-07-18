import sqlite3
import config


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect(config.DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db() -> None:
    import os
    os.makedirs(config.PKI_DATA_DIR, exist_ok=True)
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS certificates (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ca_name     TEXT NOT NULL,
            serial      TEXT NOT NULL,
            base        TEXT NOT NULL,
            cn          TEXT NOT NULL,
            cert_type   TEXT NOT NULL,
            algo        TEXT,
            not_before  TEXT,
            not_after   TEXT,
            public_key  TEXT,
            fingerprint TEXT,
            status      TEXT NOT NULL DEFAULT 'valid',
            revoked_at  TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            UNIQUE(ca_name, serial)
        );
    ''')
    try:
        db.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                   (config.ADMIN_USER, config.ADMIN_PASSWORD))
        db.commit()
    except Exception:
        db.rollback()
    db.close()


def get_user_password(username: str) -> str | None:
    db = get_db()
    row = db.execute('SELECT password FROM users WHERE username=?', (username,)).fetchone()
    db.close()
    return row['password'] if row else None


def record_cert(ca_name: str, cn: str, cert_type: str, result: dict) -> None:
    db = get_db()
    db.execute(
        '''INSERT OR IGNORE INTO certificates
           (ca_name, serial, base, cn, cert_type, algo,
            not_before, not_after, public_key, fingerprint)
           VALUES (?,?,?,?,?,?,?,?,?,?)''',
        (ca_name, result['serial'], result['base'], cn, cert_type,
         result.get('algo'), result.get('not_before'), result.get('not_after'),
         result.get('public_key_pem'), result.get('fingerprint')),
    )
    db.commit()
    db.close()


def get_certs(ca_name: str) -> list:
    db = get_db()
    rows = db.execute(
        'SELECT * FROM certificates WHERE ca_name=? ORDER BY created_at DESC',
        (ca_name,),
    ).fetchall()
    db.close()
    return rows


def get_cert_base(ca_name: str, serial: str) -> str | None:
    db = get_db()
    row = db.execute(
        'SELECT base FROM certificates WHERE ca_name=? AND serial=?', (ca_name, serial)
    ).fetchone()
    db.close()
    return row['base'] if row else None


def get_cert(ca_name: str, serial: str):
    db = get_db()
    row = db.execute(
        'SELECT * FROM certificates WHERE ca_name=? AND serial=?', (ca_name, serial)
    ).fetchone()
    db.close()
    return row


def revoke_cert_db(ca_name: str, serial: str) -> None:
    db = get_db()
    db.execute(
        "UPDATE certificates SET status='revoked', revoked_at=datetime('now') "
        "WHERE ca_name=? AND serial=?",
        (ca_name, serial),
    )
    db.commit()
    db.close()
