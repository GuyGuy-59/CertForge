"""
Flask Blueprint — all HTTP routes.
Business logic lives in services.py; DB in models.py; config in config.py.
"""

import os
from functools import wraps

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, send_file, abort, jsonify)

import config
import models
import services
import utils
from pki_engine import ALGORITHMS

bp = Blueprint('main', __name__)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('main.login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect(url_for('main.dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        stored = models.get_user_password(username)
        if stored and stored == password:
            session['user'] = username
            next_url = request.args.get('next') or ''
            if not next_url.startswith('/') or next_url.startswith('//'):
                next_url = url_for('main.dashboard')
            return redirect(next_url)
        error = 'Invalid credentials.'
    return render_template('login.html', error=error)


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))


# ---------------------------------------------------------------------------
# Dashboard (single-page shell)
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', cas=services.list_cas(), algorithms=ALGORITHMS)


# ---------------------------------------------------------------------------
# CA JSON — used by the CA panel modal
# ---------------------------------------------------------------------------

@bp.route('/ca/<ca_name>/json')
@login_required
def ca_detail_json(ca_name):
    info = services.get_ca_info(ca_name)
    if not info['exists']:
        abort(404)
    certs = [dict(c) for c in models.get_certs(ca_name)]
    return jsonify({
        'name':        ca_name,
        'parent':      info['parent'],
        'chain_exists': info['chain_exists'],
        'aia_ca':      info['aia_ca'],
        'aia_crl':     info['aia_crl'],
        'certs':       certs,
    })


# ---------------------------------------------------------------------------
# CA management (POST only — GET redirects to dashboard)
# ---------------------------------------------------------------------------

@bp.route('/ca/new', methods=['GET', 'POST'])
@login_required
def ca_new():
    if request.method == 'GET':
        return redirect(url_for('main.dashboard'))

    name        = request.form.get('name', '').strip().replace(' ', '_')
    cn          = request.form.get('cn', '').strip()
    org         = request.form.get('org', '').strip()
    ou          = request.form.get('ou', '').strip()
    country     = request.form.get('country', 'FR').strip()
    locality    = request.form.get('locality', 'Paris').strip()
    algo        = request.form.get('algo', 'ec-p384')
    expire_days = int(request.form.get('expire_days', 3650))
    ca_type     = request.form.get('ca_type', 'root')
    parent_name = request.form.get('parent_ca', '')

    if not name or not cn:
        flash('Name and CN are required.', 'danger')
        return redirect(url_for('main.dashboard'))

    if os.path.exists(services.ca_dir(name)):
        flash(f'CA "{name}" already exists.', 'danger')
        return redirect(url_for('main.dashboard'))

    try:
        if ca_type == 'intermediate' and parent_name:
            services.create_intermediate_ca(
                name, parent_name, cn, org, ou, country, locality, algo, expire_days,
            )
        else:
            services.create_root_ca(
                name, cn, org, ou, country, locality, algo, expire_days,
            )
        flash(f'CA "{name}" created.', 'success')
        return redirect(url_for('main.dashboard', open=name))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('main.dashboard'))


# ---------------------------------------------------------------------------
# Certificate management (POST only — GET redirects to dashboard)
# ---------------------------------------------------------------------------

@bp.route('/ca/<ca_name>/cert/new', methods=['GET', 'POST'])
@login_required
def cert_new(ca_name):
    if request.method == 'GET':
        return redirect(url_for('main.dashboard'))

    if not services.get_ca_info(ca_name)['exists']:
        abort(404)

    cn          = request.form.get('cn', '').strip()
    cert_type   = request.form.get('cert_type', 'server')
    algo        = request.form.get('algo', 'ec-p384')
    expire_days = int(request.form.get('expire_days', 365))
    san_str     = request.form.get('san', '').strip()

    if not cn:
        flash('CN is required.', 'danger')
        return redirect(url_for('main.dashboard', open=ca_name))

    try:
        result = services.issue_cert(ca_name, cn, cert_type, algo, expire_days, san_str)
        models.record_cert(ca_name, cn, cert_type, result)
        flash(f'Certificate "{cn}" issued.', 'success')
        return redirect(url_for('main.dashboard', open=ca_name))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('main.dashboard', open=ca_name))


@bp.route('/ca/<ca_name>/cert/<serial>/revoke', methods=['POST'])
@login_required
def cert_revoke(ca_name, serial):
    if not services.get_ca_info(ca_name)['exists']:
        abort(404)
    xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        services.revoke_cert(ca_name, serial)
        models.revoke_cert_db(ca_name, serial)
        if xhr:
            return jsonify({'ok': True})
        flash(f'Certificate {serial} revoked.', 'success')
    except Exception as e:
        if xhr:
            return jsonify({'ok': False, 'error': str(e)}), 400
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('main.dashboard', open=ca_name))


# ---------------------------------------------------------------------------
# Cert detail JSON — used by the cert detail modal
# ---------------------------------------------------------------------------

@bp.route('/ca/<ca_name>/cert/<serial>/json')
@login_required
def cert_detail_json(ca_name, serial):
    cert = models.get_cert(ca_name, serial)
    if not cert:
        abort(404)
    cert_path = os.path.join(services.ca_dir(ca_name), f'{cert["base"]}.crt')
    x509_info = utils.parse_cert_file(cert_path) or {}
    return jsonify({
        'cn':          cert['cn'],
        'serial':      cert['serial'],
        'cert_type':   cert['cert_type'],
        'algo':        cert['algo'],
        'not_after':   cert['not_after'],
        'status':      cert['status'],
        'revoked_at':  cert['revoked_at'],
        'base':        cert['base'],
        'not_before':  x509_info.get('not_before', ''),
        'fingerprint': x509_info.get('fingerprint', ''),
        'sans':        x509_info.get('sans', []),
        'crl_urls':    x509_info.get('crl_urls', []),
        'aia_urls':    x509_info.get('aia_urls', []),
    })


# ---------------------------------------------------------------------------
# Downloads (authenticated)
# ---------------------------------------------------------------------------

@bp.route('/ca/<ca_name>/download/<path:filename>')
@login_required
def ca_download(ca_name, filename):
    safe = os.path.basename(filename)
    path = os.path.join(services.ca_dir(ca_name), safe)
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=safe)


@bp.route('/ca/<ca_name>/cert/<serial>/download/<ext>')
@login_required
def cert_download(ca_name, serial, ext):
    base = models.get_cert_base(ca_name, serial)
    if not base:
        abort(404)
    path = os.path.join(services.ca_dir(ca_name), f'{base}.{ext}')
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=f'{base}.{ext}')


@bp.route('/crl/<ca_name>/download')
@login_required
def crl_download(ca_name):
    path = os.path.join(services.ca_dir(ca_name), 'crl', 'ca.crl')
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True,
                     download_name=f'{ca_name}-ca.crl',
                     mimetype='application/x-pem-file')


# ---------------------------------------------------------------------------
# Public AIA endpoints — no login required
# ---------------------------------------------------------------------------

@bp.route('/aia/<ca_name>/ca.crt')
def aia_ca_cert(ca_name):
    path = os.path.join(services.ca_dir(ca_name), 'ca.crt')
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype='application/x-x509-ca-cert', download_name='ca.crt')


@bp.route('/aia/<ca_name>/crl.crl')
def aia_crl(ca_name):
    path = os.path.join(services.ca_dir(ca_name), 'crl', 'ca.crl.der')
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype='application/pkix-crl', download_name='ca.crl')


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@bp.route('/health')
def health():
    return jsonify({'status': 'ok'})
