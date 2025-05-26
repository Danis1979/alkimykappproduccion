from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime

planificacion = Blueprint('planificacion', __name__)

@planificacion.route('/planificacion')
def planificacion_view():
    if 'usuario' not in session:
        flash("Debe iniciar sesión para acceder a la planificación", "warning")
        return redirect(url_for('login_admin'))

    canastos = session.get('canastos', {})
    total_canastos = sum(canastos.values())

    # Calcular total de cajas y cajas por sabor
    total_cajas = 0
    cajas_por_sabor = {}
    for sabor, cantidad in canastos.items():
        unidades_por_canasto = 32 if sabor == 'original' else 18
        total_unidades = cantidad * unidades_por_canasto
        cajas = round(total_unidades / (108 if sabor == 'original' else 60))
        total_cajas += cajas
        cajas_por_sabor[sabor] = cajas

    total_ingredientes_fmt = session.get('total_ingredientes_fmt', {})

    return render_template('planificacion.html',
                           canastos=canastos,
                           total_canastos=total_canastos,
                           total_cajas=total_cajas,
                           cajas_por_sabor=cajas_por_sabor,
                           total_ingredientes_fmt=total_ingredientes_fmt)

@planificacion.route('/generar_calendario', methods=['POST'])
def generar_calendario():
    canastos = session.get('canastos', {})
    cupo_diario = session.get('cupo_diario', 150)
    dias_habilitados = session.get('dias_habilitados', ['lunes', 'martes', 'miércoles', 'jueves', 'viernes'])
    fecha_inicio = datetime.strptime(request.form.get('fecha_inicio'), "%Y-%m-%d")

    cards = []
    for sabor, total in canastos.items():
        unidades_restantes = total
        while unidades_restantes > 0:
            cantidad = min(cupo_diario, unidades_restantes)
            cards.append({'sabor': sabor.capitalize(), 'cantidad': cantidad})
            unidades_restantes -= cantidad

    session['cards_calendario'] = cards
    session['fecha_inicio'] = fecha_inicio.strftime('%Y-%m-%d')
    return redirect(url_for('planificacion.calendario'))

@planificacion.route('/calendario')
def calendario():
    cards = session.get('cards_calendario', [])
    fecha_inicio = session.get('fecha_inicio')
    return render_template('calendario.html', cards=cards, fecha_inicio=fecha_inicio)