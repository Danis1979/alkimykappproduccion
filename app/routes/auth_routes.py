from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import Usuario
from werkzeug.security import check_password_hash
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Usuario.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['usuario'] = user.nombre
            session['rol'] = user.rol
            flash('Inicio de sesión exitoso', 'success')
            return redirect('/')
        else:
            flash('Credenciales inválidas', 'danger')
    return render_template('login_admin.html')