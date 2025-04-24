from flask import Flask, render_template, request, send_file, session, redirect, url_for, jsonify
from io import BytesIO
from openpyxl.styles import Font, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import webbrowser
import threading
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'alkimyk_clave_segura'

# Filtro de plantilla para formatear fechas en los templates Jinja2
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%A'):
    from datetime import datetime
    return datetime.strptime(value, '%Y-%m-%d').strftime(format)

# Filtro de plantilla para convertir strings de fecha a objetos datetime
@app.template_filter('to_datetime')
def to_datetime_filter(value, format='%Y-%m-%d'):
    from datetime import datetime
    return datetime.strptime(value, format)

UNIDADES_POR_CANASTO = 18
MASA_POR_94_CANASTOS = {
    'soja_kg': 50,
    'harina_kg': 39,
    'chimichurri_g': 800,
    'sal_g': 500
}
CANASTOS_BASE = 94

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/canastos', methods=['GET', 'POST'])
def canastos():
    ingredientes = {}
    detalles_por_sabor = {}
    mostrar = False
    canastos = {}
    errores = []

    # Si el método es GET y hay datos en sesión, mostrar los cuadros
    if request.method == 'GET' and 'canastos' in session:
        canastos = session['canastos']
        mostrar = True

    # Si el método es POST, validar y calcular
    if request.method == 'POST':
        # --- Manejo del botón "Limpiar"
        if 'limpiar' in request.form:
            session.pop('canastos', None)
            session.pop('cupo_diario', None)
            canastos = {
                'aceituna': 0,
                'caprese': 0,
                'queso_azul': 0,
                'cebolla': 0,
                'espinaca': 0,
                'calabaza': 0,
                'brocoli': 0
            }
            session['limpiar'] = True
            return render_template('canastos.html',
                                   mostrar=False,
                                   canastos=canastos,
                                   detalles_por_sabor={},
                                   ingredientes={},
                                   total_cajas=0,
                                   cupo_diario_default=110,
                                   dias_produccion=0,
                                   errores=[],
                                   limpiar=True)
        # --- Fin manejo limpiar
        canastos = {}
        datos_formulario = {k: v.strip() for k, v in request.form.items()}
        for sabor, valor in datos_formulario.items():
            if sabor == "cupo_diario":
                continue  # No tratar este campo como un sabor
            if not valor:
                errores.append(f"El campo {sabor.capitalize()} no puede estar vacío.")
            elif not valor.isdigit():
                errores.append(f"Debe ingresar un número válido para {sabor.capitalize()}.")
            else:
                canastos[sabor] = int(valor)
        if errores:
            mostrar = False
            return render_template('canastos.html', errores=errores, mostrar=mostrar, canastos=datos_formulario)
        mostrar = True
        session['canastos'] = canastos
        total_canastos = sum(canastos.values())

        total_ingredientes = {}
        soja = MASA_POR_94_CANASTOS['soja_kg'] * total_canastos / CANASTOS_BASE
        harina = MASA_POR_94_CANASTOS['harina_kg'] * total_canastos / CANASTOS_BASE
        chimichurri = MASA_POR_94_CANASTOS['chimichurri_g'] * total_canastos / CANASTOS_BASE
        sal_masa = MASA_POR_94_CANASTOS['sal_g'] * total_canastos / CANASTOS_BASE

        total_ingredientes['Soja'] = soja
        total_ingredientes['Harina'] = harina
        total_ingredientes['Chimichurri'] = chimichurri
        total_ingredientes['Sal'] = sal_masa

        for sabor, cantidad in canastos.items():
            if cantidad == 0:
                continue
            unidades = cantidad * UNIDADES_POR_CANASTO
            detalles_por_sabor[sabor] = {}

            def add(dic, nombre, cantidad_g):
                dic[nombre] = dic.get(nombre, 0) + cantidad_g

            temp = detalles_por_sabor[sabor]

            if sabor == 'aceituna':
                add(temp, 'Muzzarella', unidades * 15)
                add(temp, 'Aceitunas', unidades * 20)
            elif sabor == 'caprese':
                tomate_total = unidades * 25
                add(temp, 'Muzzarella', unidades * 15)
                add(temp, 'Tomate', tomate_total)
                add(temp, 'Albahaca', unidades * 2)
                add(temp, 'Sal', (tomate_total / 1000) * 4)
            elif sabor == 'queso_azul':
                mezcla_total = unidades * 30
                porc_queso = 2.3 / (18 + 2.3)
                porc_muzza = 1 - porc_queso
                add(temp, 'Muzzarella', mezcla_total * porc_muzza)
                add(temp, 'Queso Azul', mezcla_total * porc_queso)
            elif sabor == 'cebolla':
                cebolla_cruda = (unidades * 40) / 0.8
                add(temp, 'Cebolla', cebolla_cruda)
                add(temp, 'Orégano', (cebolla_cruda / 1000) * 2)
                add(temp, 'Sal', (cebolla_cruda / 1000) * 5)
            elif sabor == 'espinaca':
                total_relleno = unidades * 40 / 0.9
                espinaca = total_relleno * 0.5 / 0.9
                cebolla = total_relleno * 0.25 / 0.8
                morron = total_relleno * 0.25 / 0.8
                add(temp, 'Espinaca', espinaca)
                add(temp, 'Cebolla', cebolla)
                add(temp, 'Morrón', morron)
                add(temp, 'Nuez Moscada', total_relleno / 1000 * 1)
                add(temp, 'Pimienta Negra', total_relleno / 1000 * 1)
                add(temp, 'Sal', total_relleno / 1000 * 5)
            elif sabor == 'calabaza':
                total_relleno = unidades * 40 / 0.8
                add(temp, 'Calabaza', total_relleno)
                add(temp, 'Cúrcuma', total_relleno / 1000 * 5)
                add(temp, 'Sal', total_relleno / 1000 * 5)
            elif sabor == 'brocoli':
                total_relleno = unidades * 40
                add(temp, 'Brócoli', total_relleno * 0.6)
                add(temp, 'Cebolla', total_relleno * 0.4 / 0.8)
                add(temp, 'Chimichurri', total_relleno / 1000 * 5)
                add(temp, 'Sal', total_relleno / 1000 * 5)

            for k, v in temp.items():
                total_ingredientes[k] = total_ingredientes.get(k, 0) + v

        ingredientes = total_ingredientes
        total_cajas = round((total_canastos * UNIDADES_POR_CANASTO) / (15 * 4))

        # Obtener el valor por defecto del límite diario de producción
        cupo_diario = request.form.get('cupo_diario')
        if cupo_diario and cupo_diario.isdigit():
            session['cupo_diario'] = int(cupo_diario)
            cupo_diario_default = int(cupo_diario)
        else:
            cupo_diario_default = session.get('cupo_diario', 110)

        # Calcular la cantidad de días de producción según el cupo diario
        dias_produccion = (total_canastos + cupo_diario_default - 1) // cupo_diario_default
    else:
        # Si es GET o no se envió POST, preparar valores por defecto
        total_cajas = round((sum(canastos.values()) * UNIDADES_POR_CANASTO) / (15 * 4)) if canastos else 0
        cupo_diario = request.form.get('cupo_diario')
        if cupo_diario and cupo_diario.isdigit():
            session['cupo_diario'] = int(cupo_diario)
            cupo_diario_default = int(cupo_diario)
        else:
            cupo_diario_default = session.get('cupo_diario', 110)
        total_canastos = sum(canastos.values()) if canastos else 0
        dias_produccion = (total_canastos + cupo_diario_default - 1) // cupo_diario_default if total_canastos > 0 else 0

    return render_template('canastos.html',
                           ingredientes=ingredientes,
                           mostrar=mostrar,
                           canastos=canastos,
                           detalles_por_sabor=detalles_por_sabor,
                           total_cajas=total_cajas,
                           cupo_diario_default=cupo_diario_default,
                           dias_produccion=dias_produccion)




from flask import jsonify, request, session
from datetime import datetime, timedelta

@app.route('/generar_calendario', methods=['POST'])
def generar_calendario():
    fecha_inicio = request.form.get('fecha_inicio')
    if not fecha_inicio:
        return "Fecha de inicio no proporcionada", 400

    # Recuperar cupo_diario del formulario o de la sesión
    cupo_diario = request.form.get('cupo_diario', None)
    if cupo_diario is not None:
        try:
            cupo_diario = int(cupo_diario)
        except ValueError:
            cupo_diario = 110
        session['cupo_diario'] = cupo_diario
    else:
        cupo_diario = session.get('cupo_diario', 110)

    try:
        fecha = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    except ValueError:
        return "Formato de fecha inválido", 400

    canastos = session.get('canastos', {}).copy()
    total = sum(canastos.values())
    dias = []
    producidos = 0

    while producidos < total:
        if fecha.weekday() < 5:  # Lunes a Viernes
            restante = total - producidos
            hoy = min(cupo_diario, restante)
            sabores_distribuidos = {}
            restantes = hoy
            # Distribuir los canastos entre sabores
            ranking_sabores = ['caprese', 'queso_azul', 'espinaca', 'aceituna', 'calabaza', 'brocoli', 'cebolla']
            for sabor in canastos.keys():
                # preserve existing order if not in ranking
                if sabor not in ranking_sabores:
                    ranking_sabores.append(sabor)
            for sabor in ranking_sabores:
                cantidad = canastos.get(sabor, 0)
                if cantidad <= 0:
                    continue
                asignar = min(cantidad, restantes)
                if asignar > 0:
                    sabores_distribuidos[sabor] = asignar
                    canastos[sabor] -= asignar
                    restantes -= asignar
                if restantes == 0:
                    break

            # Reiniciar hoy a 0 antes del bloque de asignación forzada
            hoy = 0
            # Asegura que haya al menos un sabor asignado si quedan canastos de algún sabor
            if not sabores_distribuidos and any(c > 0 for c in canastos.values()):
                for sabor in ranking_sabores:
                    if canastos.get(sabor, 0) > 0:
                        sabores_distribuidos[sabor] = 1
                        canastos[sabor] -= 1
                        hoy = 1
                        break

            # Solo agregar el día si hay algún sabor distribuido
            if sabores_distribuidos:
                dias.append({
                    "fecha": fecha.strftime('%Y-%m-%d'),
                    "canastos": sum(sabores_distribuidos.values()),
                    "sabores": sabores_distribuidos
                })
                producidos += sum(sabores_distribuidos.values())
        fecha += timedelta(days=1)

    return jsonify(dias)

# Ruta para generación y visualización del calendario de producción
@app.route('/calendario', methods=['GET', 'POST'])
def calendario():
    import datetime
    from flask import jsonify

    if request.method == 'POST':
        canastos = session.get('canastos', {})
        if not canastos:
            return redirect(url_for('canastos'))

        # Recuperar cupo_diario del formulario o de la sesión
        cupo_diario = request.form.get('cupo_diario', None)
        if cupo_diario is not None:
            try:
                cupo_diario = int(cupo_diario)
            except ValueError:
                cupo_diario = 110
            session['cupo_diario'] = cupo_diario
        else:
            cupo_diario = session.get('cupo_diario', 110)

        total_canastos = sum(canastos.values())
        canastos_por_dia = session.get('cupo_diario', 120)
        # Usar el último valor de cupo_diario para canastos_por_dia
        canastos_por_dia = cupo_diario

        fecha_inicio_str = request.form.get('fecha_inicio')
        if not fecha_inicio_str:
            return redirect(url_for('canastos'))

        fecha_actual = datetime.datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        calendario = []
        canastos_restantes = total_canastos
        canastos_sabores = canastos.copy()

        while canastos_restantes > 0:
            sabores_distribuidos = {}
            if fecha_actual.weekday() < 5:  # lunes a viernes
                restantes = min(canastos_restantes, canastos_por_dia)
                ranking_sabores = ['caprese', 'queso_azul', 'espinaca', 'aceituna', 'calabaza', 'brocoli', 'cebolla']
                for sabor in ranking_sabores:
                    cantidad = canastos_sabores.get(sabor, 0)
                    if cantidad <= 0:
                        continue
                    asignar = min(cantidad, restantes)
                    if asignar > 0:
                        sabores_distribuidos[sabor] = asignar
                        canastos_sabores[sabor] -= asignar
                        restantes -= asignar
                    if restantes == 0:
                        break
                # Asegura que haya al menos un sabor asignado si quedan canastos de algún sabor
                if not sabores_distribuidos and any(c > 0 for c in canastos_sabores.values()):
                    for sabor in ranking_sabores:
                        if canastos_sabores.get(sabor, 0) > 0:
                            sabores_distribuidos[sabor] = 1
                            canastos_sabores[sabor] -= 1
                            break
                if sabores_distribuidos:
                    produccion_real = sum(sabores_distribuidos.values())
                    calendario.append({
                        'fecha': fecha_actual.strftime('%Y-%m-%d'),
                        'dia_semana': fecha_actual.strftime('%A'),
                        'canastos': produccion_real,
                        'sabores': sabores_distribuidos
                    })
                    canastos_restantes -= produccion_real
            # Avanzar la fecha solo si fue un día hábil
            fecha_actual += datetime.timedelta(days=1)

        return render_template('calendario.html', calendario=calendario)

    return render_template('calendario.html', calendario=[])

@app.route('/stock', methods=['GET', 'POST'])
def stock():
    cajas = {}
    canastos = {}
    if request.method == 'POST':
        errores = []
        cajas = {}
        for sabor in ['aceituna', 'caprese', 'queso_azul', 'cebolla', 'espinaca', 'calabaza', 'brocoli']:
            valor = request.form.get(sabor, '').strip()
            if not valor:
                errores.append(f"El campo {sabor.capitalize()} no puede estar vacío.")
            elif not valor.isdigit():
                errores.append(f"Debe ingresar un número válido para {sabor.capitalize()}.")
            else:
                cajas[sabor] = int(valor)
        if errores:
            return render_template('stock.html', cajas=request.form, errores=errores)
        for sabor, cant_cajas in cajas.items():
            total_unidades = cant_cajas * 15 * 4
            canastos[sabor] = round(total_unidades / 18)
        session['canastos'] = canastos
        return redirect(url_for('canastos'))
    return render_template('stock.html', cajas=cajas, canastos=canastos)

@app.route('/exportar', methods=['POST'])
def exportar_excel():
    canastos = session.get('canastos', {})
    if not canastos:
        return "No hay datos para exportar", 400

    detalles_por_sabor = {}
    ingredientes_totales = {}
    total_canastos = sum(canastos.values())
    total_cajas = round((total_canastos * UNIDADES_POR_CANASTO) / (15 * 4))
    soja = MASA_POR_94_CANASTOS['soja_kg'] * total_canastos / CANASTOS_BASE
    harina = MASA_POR_94_CANASTOS['harina_kg'] * total_canastos / CANASTOS_BASE
    chimichurri = MASA_POR_94_CANASTOS['chimichurri_g'] * total_canastos / CANASTOS_BASE
    sal_masa = MASA_POR_94_CANASTOS['sal_g'] * total_canastos / CANASTOS_BASE

    ingredientes_totales['Soja'] = soja
    ingredientes_totales['Harina'] = harina
    ingredientes_totales['Chimichurri'] = chimichurri
    ingredientes_totales['Sal'] = sal_masa

    for sabor, cantidad in canastos.items():
        if cantidad == 0:
            continue
        unidades = cantidad * UNIDADES_POR_CANASTO
        temp = {}
        if sabor == 'aceituna':
            temp['Muzzarella'] = unidades * 15
            temp['Aceitunas'] = unidades * 20
        elif sabor == 'caprese':
            tomate_total = unidades * 25
            temp['Muzzarella'] = unidades * 15
            temp['Tomate'] = tomate_total
            temp['Albahaca'] = unidades * 2
            temp['Sal'] = (tomate_total / 1000) * 4
        elif sabor == 'queso_azul':
            mezcla_total = unidades * 30
            porc_queso = 2.3 / (18 + 2.3)
            porc_muzza = 1 - porc_queso
            temp['Muzzarella'] = mezcla_total * porc_muzza
            temp['Queso Azul'] = mezcla_total * porc_queso
        elif sabor == 'cebolla':
            cebolla_cruda = (unidades * 40) / 0.8
            temp['Cebolla'] = cebolla_cruda
            temp['Orégano'] = (cebolla_cruda / 1000) * 2
            temp['Sal'] = (cebolla_cruda / 1000) * 5
        elif sabor == 'espinaca':
            total_relleno = unidades * 40 / 0.9
            espinaca = total_relleno * 0.5 / 0.9
            cebolla = total_relleno * 0.25 / 0.8
            morron = total_relleno * 0.25 / 0.8
            temp['Espinaca'] = espinaca
            temp['Cebolla'] = cebolla
            temp['Morrón'] = morron
            temp['Nuez Moscada'] = total_relleno / 1000 * 1
            temp['Pimienta Negra'] = total_relleno / 1000 * 1
            temp['Sal'] = total_relleno / 1000 * 5
        elif sabor == 'calabaza':
            total_relleno = unidades * 40 / 0.8
            temp['Calabaza'] = total_relleno
            temp['Cúrcuma'] = total_relleno / 1000 * 5
            temp['Sal'] = total_relleno / 1000 * 5
        elif sabor == 'brocoli':
            total_relleno = unidades * 40
            temp['Brócoli'] = total_relleno * 0.6
            temp['Cebolla'] = total_relleno * 0.4 / 0.8
            temp['Chimichurri'] = total_relleno / 1000 * 5
            temp['Sal'] = total_relleno / 1000 * 5

        detalles_por_sabor[sabor] = temp
        for k, v in temp.items():
            ingredientes_totales[k] = ingredientes_totales.get(k, 0) + v

    output = BytesIO()
    wb = Workbook()

    # Ingredientes por sabor
    ws1 = wb.active
    ws1.title = "Ingredientes por sabor"
    font = Font(size=19)
    border = Border(left=Side(style='thin'), right=Side(style='thin'),
                    top=Side(style='thin'), bottom=Side(style='thin'))
    row = 1
    for sabor, ingredientes in detalles_por_sabor.items():
        if row > 1:
            row += 2
        cantidad_canastos = canastos[sabor]
        cantidad_cajas = round((cantidad_canastos * UNIDADES_POR_CANASTO) / (15 * 4))
        ws1.cell(row=row, column=1, value=f"{sabor.replace('_', ' ').capitalize()} ({cantidad_canastos} canastos, {cantidad_cajas} cajas)").font = Font(size=19, bold=True)
        row += 1
        ws1.cell(row=row, column=1, value="Ingrediente").font = font
        ws1.cell(row=row, column=2, value="Cantidad").font = font
        ws1.cell(row=row, column=3, value="Unidad").font = font
        row += 1
        for ingr, cant in ingredientes.items():
            ws1.cell(row=row, column=1, value=ingr).font = font
            if cant >= 1000:
                ws1.cell(row=row, column=2, value=round(cant/1000, 2)).font = font
                ws1.cell(row=row, column=3, value="kg").font = font
            else:
                ws1.cell(row=row, column=2, value=round(cant, 2)).font = font
                ws1.cell(row=row, column=3, value="g").font = font
            row += 1
    for r in ws1.iter_rows(min_row=1, max_row=row, min_col=1, max_col=3):
        for cell in r:
            cell.border = border
    for col in range(1, 4):
        ws1.column_dimensions[get_column_letter(col)].auto_size = True

    # Total ingredientes
    ws2 = wb.create_sheet("Total Ingredientes")
    ws2.cell(row=1, column=1, value="Ingrediente").font = font
    ws2.cell(row=1, column=2, value="Cantidad").font = font
    ws2.cell(row=1, column=3, value="Unidad").font = font
    for i, (ingr, cant) in enumerate(ingredientes_totales.items(), start=2):
        ws2.cell(row=i, column=1, value=ingr).font = font
        if ingr in ['Soja', 'Harina']:
            ws2.cell(row=i, column=2, value=round(cant, 2)).font = font
            ws2.cell(row=i, column=3, value="kg").font = font
        else:
            if cant >= 1000:
                ws2.cell(row=i, column=2, value=round(cant/1000, 2)).font = font
                ws2.cell(row=i, column=3, value="kg").font = font
            else:
                ws2.cell(row=i, column=2, value=round(cant, 2)).font = font
                ws2.cell(row=i, column=3, value="g").font = font
    i += 2
    ws2.cell(row=i, column=1, value=f"Total de ingredientes para comprar y elaborar {total_canastos} canastos").font = font
    i += 1
    ws2.cell(row=i, column=1, value=f"Total de cajas: {total_cajas}").font = font
    for r in ws2.iter_rows(min_row=1, max_row=i, min_col=1, max_col=3):
        for cell in r:
            cell.border = border
    for col in range(1, 4):
        ws2.column_dimensions[get_column_letter(col)].auto_size = True

    wb.save(output)
    output.seek(0)
    return send_file(output, download_name='produccion_alkimyk.xlsx', as_attachment=True)

@app.route('/exportar_pdf', methods=['POST'])
def exportar_pdf():
    canastos = session.get('canastos', {})
    if not canastos:
        return "No hay datos para exportar", 400

    tipo = request.form.get('tipo')
    detalles_por_sabor = {}
    total_ingredientes = {}
    total_canastos = sum(canastos.values())
    total_cajas = round((total_canastos * UNIDADES_POR_CANASTO) / (15 * 4))

    for sabor, cantidad in canastos.items():
        if cantidad == 0:
            continue
        unidades = cantidad * UNIDADES_POR_CANASTO
        temp = {}
        if sabor == 'aceituna':
            temp['Muzzarella'] = unidades * 15
            temp['Aceitunas'] = unidades * 20
        elif sabor == 'caprese':
            tomate_total = unidades * 25
            temp['Muzzarella'] = unidades * 15
            temp['Tomate'] = tomate_total
            temp['Albahaca'] = unidades * 2
            temp['Sal'] = (tomate_total / 1000) * 4
        elif sabor == 'queso_azul':
            mezcla_total = unidades * 30
            porc_queso = 2.3 / (18 + 2.3)
            porc_muzza = 1 - porc_queso
            temp['Muzzarella'] = mezcla_total * porc_muzza
            temp['Queso Azul'] = mezcla_total * porc_queso
        elif sabor == 'cebolla':
            cebolla_cruda = (unidades * 40) / 0.8
            temp['Cebolla'] = cebolla_cruda
            temp['Orégano'] = (cebolla_cruda / 1000) * 2
            temp['Sal'] = (cebolla_cruda / 1000) * 5
        elif sabor == 'espinaca':
            total_relleno = unidades * 40 / 0.9
            espinaca = total_relleno * 0.5 / 0.9
            cebolla = total_relleno * 0.25 / 0.8
            morron = total_relleno * 0.25 / 0.8
            temp['Espinaca'] = espinaca
            temp['Cebolla'] = cebolla
            temp['Morrón'] = morron
            temp['Nuez Moscada'] = total_relleno / 1000 * 1
            temp['Pimienta Negra'] = total_relleno / 1000 * 1
            temp['Sal'] = total_relleno / 1000 * 5
        elif sabor == 'calabaza':
            total_relleno = unidades * 40 / 0.8
            temp['Calabaza'] = total_relleno
            temp['Cúrcuma'] = total_relleno / 1000 * 5
            temp['Sal'] = total_relleno / 1000 * 5
        elif sabor == 'brocoli':
            total_relleno = unidades * 40
            temp['Brócoli'] = total_relleno * 0.6
            temp['Cebolla'] = total_relleno * 0.4 / 0.8
            temp['Chimichurri'] = total_relleno / 1000 * 5
            temp['Sal'] = total_relleno / 1000 * 5

        detalles_por_sabor[sabor] = temp
        for k, v in temp.items():
            total_ingredientes[k] = total_ingredientes.get(k, 0) + v

    output = BytesIO()
    pdf_output = output
    c = canvas.Canvas(pdf_output, pagesize=letter)
    width, height = letter
    try:
        c.drawImage("static/logo.png", width - 150, height - 80, width=100, preserveAspectRatio=True, mask='auto')
    except:
        pass  # Si el logo no se encuentra, no rompe el PDF

    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, height - 40, "Alkimyk Food - Producción")
    c.setFont("Helvetica", 12)

    print("Tipo de PDF:", tipo)
    print("Canastos:", canastos)
    print("Detalles por sabor:", detalles_por_sabor)
    print("Total ingredientes:", total_ingredientes)

    if tipo == 'por_sabor':
        y = height - 50
        for sabor, ingredientes in detalles_por_sabor.items():
            cantidad_canastos = canastos[sabor]
            cantidad_cajas = round((cantidad_canastos * UNIDADES_POR_CANASTO) / (15 * 4))
            c.drawString(30, y, f"{sabor.replace('_', ' ').capitalize()} ({cantidad_canastos} canastos, {cantidad_cajas} cajas)")
            y -= 20
            for ingr, cant in ingredientes.items():
                unidad = "kg" if cant >= 1000 else "g"
                c.drawString(50, y, f"{ingr}: {round(cant / 1000, 2) if unidad == 'kg' else round(cant, 2)} {unidad}")
                y -= 15
                if y < 50:
                    c.showPage()
                    y = height - 50
            y -= 10  # Espacio entre sabores
    elif tipo == 'total':
        y = height - 50
        c.drawString(30, y, "Total de Ingredientes")
        y -= 20
        for ingr, cant in total_ingredientes.items():
            if ingr in ['Soja', 'Harina']:
                unidad = "kg"
                cantidad = round(cant, 2)
            else:
                if cant >= 1000:
                    unidad = "kg"
                    cantidad = round(cant / 1000, 2)
                else:
                    unidad = "g"
                    cantidad = round(cant, 2)
            c.drawString(50, y, f"{ingr}: {cantidad} {unidad}")
            y -= 15
            if y < 50:
                c.showPage()
                y = height - 50
        y -= 10  # Espacio antes del total
        c.drawString(30, y, f"Total de canastos: {total_canastos}")
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(30, y, f"Total de cajas: {total_cajas}")

    c.save()
    pdf_output.seek(0)
    return send_file(pdf_output, download_name='produccion_alkimyk.pdf', as_attachment=True)

def abrir_navegador():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == '__main__':
    threading.Timer(1.25, abrir_navegador).start()
    app.run(debug=True)