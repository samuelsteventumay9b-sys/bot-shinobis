import discord
from discord.ext import commands
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 🔥 Esto permite acceder a los miembros y sus roles

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'🟢 El bot está conectado como {bot.user}')

@bot.command()
async def hola(ctx):
    await ctx.send('¡Hola, shinobi! Estoy listo para servir a tu aldea.')

@bot.command()
async def paga(ctx):
    await ctx.send('neko rm 20min')

# AQUI IREMOS AGREGANDO LOS DEMÁS COMANDOS
# _________________________________________________________________________________________

# Cargar inventario desde JSON
def actualizar_datos_en_tiempo_real(inventario, servidor):
    roles_aldeas = {
        "konoha": {"habitantes": "【🍃】Konohagakure【🍃】", "productores": "【👷】Productor Konoha【👷】"},
        "kumogakure": {"habitantes": "【☁️】Kumogakure【☁️】", "productores": "【👷】Productor Kumogakure【👷】"},
        "kirigakure": {"habitantes": "【💧】Kirigakure【💧】", "productores": "【👷】Productor Kirigakure【👷】"},
        "kinkogakure": {"habitantes": "【⚒️】Kinkōgakure【⚒️】", "productores": "【👷】Productor Kinkogakure【👷】"},
        "sunagakure": {"habitantes": "【⏳】Sunagakure【⏳】", "productores": "【👷】Productor Sunagakure【👷】"},
        "iwagakure": {"habitantes": "【🗻】Iwagakure【🗻】", "productores": "【👷】 Productor Iwagakure【👷】"}
    }

    for aldea, roles in roles_aldeas.items():
        rol_habitantes = discord.utils.get(servidor.roles, name=roles["habitantes"])
        rol_productores = discord.utils.get(servidor.roles, name=roles["productores"])

        if rol_habitantes:
            inventario[aldea]["habitantes"] = sum(1 for m in servidor.members if rol_habitantes in m.roles)
        if rol_productores:
            inventario[aldea]["productores"] = sum(1 for m in servidor.members if rol_productores in m.roles)

    return inventario

def cargar_inventario(ctx=None):
    with open('recursos_generales_aldeas.json', 'r', encoding='utf-8') as archivo:
        inventario = json.load(archivo)

    if ctx is not None:
        inventario = actualizar_datos_en_tiempo_real(inventario, ctx.guild)

        # 🔁 Guardamos los datos actualizados en el archivo JSON
        with open('recursos_generales_aldeas.json', 'w', encoding='utf-8') as archivo:
            json.dump(inventario, archivo, ensure_ascii=False, indent=2)

    return inventario

# COMANDO INVENTARIO
@bot.command(name='economia')
async def economia(ctx, aldea: str):
    inventario = cargar_inventario(ctx)

    # Buscar sin importar mayúsculas/minúsculas
    nombre_encontrado = None
    for nombre in inventario.keys():
        if nombre.lower() == aldea.lower():
            nombre_encontrado = nombre
            break

    if not nombre_encontrado:
        await ctx.send(f"⚠️ Aldea '{aldea}' no encontrada.")
        return

    datos = inventario[nombre_encontrado]
    embed = discord.Embed(
        title=f"📦 Inventario de {nombre_encontrado}",
        color=discord.Color.gold()
    )

    embed.add_field(name="👥 Habitantes", value=datos["habitantes"], inline=False)
    embed.add_field(name="👷 Productores", value=datos["productores"], inline=False)
    embed.add_field(name="🍙 Comida", value=datos["comida"], inline=True)
    embed.add_field(name="💧 Agua", value=datos["agua"], inline=True)
    embed.add_field(name="🧥 Ropa", value=datos["ropas"], inline=True)
    embed.add_field(name="💊 Medicamentos", value=datos["medicamentos"], inline=True)
    embed.add_field(name="⛏️ Minerales", value=datos["minerales"], inline=True)

    await ctx.send(embed=embed)


#_________________________________________________________________________________________

# Guardar inventario en JSON
def guardar_inventario(inventario):
    with open('recursos_generales_aldeas.json', 'w', encoding='utf-8') as archivo:
        json.dump(inventario, archivo, indent=2, ensure_ascii=False)

# COMANDO PARA EDITAR INVENTARIO
@bot.command(name='editar')
async def editar(ctx, aldea: str, recurso: str, cantidad: int):
    inventario = cargar_inventario()
    nombre_encontrado = None

    for nombre in inventario.keys():
        if nombre.lower() == aldea.lower():
            nombre_encontrado = nombre
            break

    if not nombre_encontrado:
        await ctx.send(f"⚠️ Aldea '{aldea}' no encontrada.")
        return

    if recurso not in inventario[nombre_encontrado]:
        await ctx.send(f"⚠️ Recurso '{recurso}' no válido. Usa: minerales, comida, agua, ropas, medicamentos, habitantes, productores.")
        return

    inventario[nombre_encontrado][recurso] += cantidad
    guardar_inventario(inventario)

    signo = "➕" if cantidad >= 0 else "➖"
    await ctx.send(f"{signo} Se han actualizado los recursos de **{nombre_encontrado}**: `{recurso}` ahora es `{inventario[nombre_encontrado][recurso]}`.")
# _____________________________________________________________________________________________
def guardar_inventario(inventario):
    with open('recursos_generales_aldeas.json', 'w', encoding='utf-8') as archivo:
        json.dump(inventario, archivo, indent=2, ensure_ascii=False)

# Producción por tipo de productor
produccion_diaria = {
    "comida": 8,
    "agua": 4,
    "ropas": 4,
    "medicamentos": 3,
    "minerales": 4
}

@bot.command(name="producir")
async def producir(ctx, aldea: str):
    inventario = cargar_inventario()
    aldea = aldea.lower()

    if aldea not in inventario:
        await ctx.send(f"⚠️ La aldea '{aldea}' no existe.")
        return

    datos = inventario[aldea]
    tipo = datos.get("tipo_productor", "ninguno")
    productores = datos.get("productores", 0)
    usos_restantes = datos.get("usos_productores_restantes", 0)

    if tipo == "ninguno":
        await ctx.send(f"🚫 La aldea {aldea.capitalize()} no produce ningún recurso directamente.")
        return

    if productores == 0:
        await ctx.send(f"⚠️ La aldea {aldea.capitalize()} no tiene productores asignados.")
        return

    if usos_restantes <= 0:
        await ctx.send(f"❌ Ya se han usado todos los turnos de producción de esta semana.")
        return

    # Producción por 1 productor
    cantidad = produccion_diaria[tipo]
    datos[tipo] += cantidad
    datos["usos_productores_restantes"] = usos_restantes - 1

    guardar_inventario(inventario)

    await ctx.send(
        f"✅ Un productor de **{aldea.capitalize()}** ha producido **{cantidad} unidades de {tipo}**.\n"
        f"📉 Usos restantes esta semana: {datos['usos_productores_restantes']}/{productores * 4}"
    )
#_____________________________________________________________________________________________

recursos_robar = ["comida", "agua", "ropas", "medicamentos", "minerales"]

@bot.command(name="roboalmacen")
async def robo_almacen(ctx, aldea: str, tipo: str, recurso_especifico: str = None):
    import json
    import os
    import re
    from datetime import datetime

    inventario = cargar_inventario()
    archivo_caravanas = 'caravanas.json'

    aldea = aldea.lower()
    tipo = tipo.lower()
    autor_id = str(ctx.author.id)

    if aldea not in inventario:
        await ctx.send(f"⚠️ La aldea '{aldea}' no fue encontrada.")
        return

    datos_aldea = inventario[aldea]
    if datos_aldea["robos_almacen"] >= 1:
        await ctx.send(f"🚫 La aldea **{aldea.capitalize()}** ya ha realizado su robo de almacén esta semana.")
        return

    recursos_validos = ["comida", "agua", "ropas", "medicamentos", "minerales"]
    resultado = {}

    if tipo == "normal":
        for recurso in recursos_validos:
            cantidad = round(datos_aldea[recurso] * 0.2)
            datos_aldea[recurso] -= cantidad
            resultado[recurso] = cantidad

    elif tipo == "guerra":
        for recurso in recursos_validos:
            cantidad = round(datos_aldea[recurso] * 0.5)
            datos_aldea[recurso] -= cantidad
            resultado[recurso] = cantidad

    elif tipo == "especifico":
        if not recurso_especifico:
            await ctx.send("⚠️ Debes especificar qué recurso deseas robar. Ejemplo: `!roboalmacen konoha especifico agua`")
            return

        recurso_especifico = recurso_especifico.lower()
        if recurso_especifico not in recursos_validos:
            await ctx.send(f"⚠️ El recurso '{recurso_especifico}' no es válido.")
            return

        cantidad = round(datos_aldea[recurso_especifico] * 0.7)
        datos_aldea[recurso_especifico] -= cantidad
        resultado[recurso_especifico] = cantidad

    else:
        await ctx.send("❌ Tipo de robo inválido. Usa: `normal`, `guerra` o `especifico`.")
        return

    # Registrar el robo en el inventario
    datos_aldea["robos_almacen"] += 1
    guardar_inventario(inventario)

    # Cargar archivo de caravanas
    if not os.path.exists(archivo_caravanas):
        with open(archivo_caravanas, 'w', encoding='utf-8') as f:
            json.dump({"caravanas_activas": [], "robos_caravanas": {}}, f, indent=2, ensure_ascii=False)

    with open(archivo_caravanas, 'r', encoding='utf-8') as f:
        datos_caravanas = json.load(f)

    # Crear caravana robada
    hoy = datetime.now().strftime("%Y-%m-%d")
    nueva_caravana = {
        "tipo": "recursos",
        "origen": aldea,
        "destino": "desconocido",  # ← ¡clave para no romper vercaravanas!
        "encargado_id": autor_id,
        "escoltas": [],
        "recursos": resultado,
        "fecha_envio": hoy,
        "robada": True  # ← nueva clave para saber que esta caravana no pertenece a la aldea
    }

    datos_caravanas["caravanas_activas"].append(nueva_caravana)

    with open(archivo_caravanas, 'w', encoding='utf-8') as f:
        json.dump(datos_caravanas, f, indent=2, ensure_ascii=False)

    # Mostrar resultado al jugador
    texto = "\n".join([f"🔹 {k.capitalize()}: {v} unidades robadas" for k, v in resultado.items()])
    await ctx.send(
        f"💣 Robo de tipo **{tipo.upper()}** ejecutado exitosamente en **{aldea.capitalize()}**:\n{texto}\n\n"
        f"🧳 Se ha creado una caravana para que transportes lo robado. ¡Escóndelo bien! 😈"
    )
# _____________________________________________________________________________________________
@bot.command(name="reset1") 
async def resetear_datos(ctx):
    import os
    import json

    # Reiniciar inventario económico
    inventario = cargar_inventario()
    
    for aldea, datos in inventario.items():
        # Reiniciar recursos a 100
        for recurso in ["comida", "agua", "ropas", "medicamentos", "minerales"]:
            datos[recurso] = 100

        # Reiniciar contadores
        datos["produccion_robada"] = 0
        datos["robos_almacen"] = 0
        datos["robos_productores"] = 0

        # Reiniciar usos de producción
        datos["usos_productores_restantes"] = datos["productores"] * 4

    guardar_inventario(inventario)

    # Reiniciar misiones
    try:
        with open('misiones_aldeas.json', 'r', encoding='utf-8') as archivo_misiones:
            misiones = json.load(archivo_misiones)

        for aldea in misiones:
            misiones[aldea]["misiones"]["genin"] = 0
            misiones[aldea]["misiones"]["chunin"] = 0
            misiones[aldea]["misiones"]["jonin"] = 0
            misiones[aldea]["usuarios"] = {}

        with open('misiones_aldeas.json', 'w', encoding='utf-8') as archivo_misiones:
            json.dump(misiones, archivo_misiones, ensure_ascii=False, indent=2)

    except FileNotFoundError:
        await ctx.send("⚠️ Archivo de misiones no encontrado. ¿Seguro que lo creaste?")
        return

    # Reiniciar caravanas
    try:
        ruta_caravanas = 'caravanas.json'
        if os.path.exists(ruta_caravanas):
            with open(ruta_caravanas, 'r', encoding='utf-8') as f:
                datos_caravanas = json.load(f)

            datos_caravanas["caravanas_activas"] = []
            datos_caravanas["robos_caravanas"] = {}

            with open(ruta_caravanas, 'w', encoding='utf-8') as f:
                json.dump(datos_caravanas, f, indent=2, ensure_ascii=False)
        else:
            with open(ruta_caravanas, 'w', encoding='utf-8') as f:
                json.dump({
                    "caravanas_activas": [],
                    "robos_caravanas": {}
                }, f, indent=2, ensure_ascii=False)
    except Exception as e:
        await ctx.send(f"❌ Error al reiniciar caravanas: {str(e)}")
        return

    # 💣 BORRAR EL ARCHIVO DE ROBOS SEMANALES (si existe)
    try:
        if os.path.exists('robos_semanales.json'):
            os.remove('robos_semanales.json')
    except Exception as e:
        await ctx.send(f"⚠️ Error al eliminar robos_semanales.json: {str(e)}")
        return

    await ctx.send("🔄 Todos los recursos, contadores, misiones, caravanas y robos han sido reiniciados exitosamente.")
# __________________________________________________________________________________________
# PROGRAMACION PARA MISIONES: 
@bot.command(name="mision")
async def mision(ctx, aldea: str, rango: str):
    import os  # Asegúrate de importar esto arriba si no lo has hecho

    aldea = aldea.lower()
    rango = rango.lower()
    archivo_misiones = 'misiones_aldeas.json'

    # Validar existencia del archivo
    if not os.path.exists(archivo_misiones):
        await ctx.send("⚠️ Archivo de misiones no encontrado.")
        return

    # Validar aldea
    roles_aldea_discord = {
        "konoha": "【🍃】Konohagakure【🍃】",
        "kumogakure": "【☁️】Kumogakure【☁️】",
        "kirigakure": "【💧】Kirigakure【💧】",
        "kinkogakure": "【⚒️】Kinkōgakure【⚒️】",
        "sunagakure": "【⏳】Sunagakure【⏳】",
        "iwagakure": "【🗻】Iwagakure【🗻】"
    }

    if aldea not in roles_aldea_discord:
        await ctx.send("⚠️ Aldea no válida.")
        return

    # Validar que el usuario pertenece a esa aldea
    roles_usuario = [r.name for r in ctx.author.roles]
    if roles_aldea_discord[aldea] not in roles_usuario:
        await ctx.send("🚫 No perteneces a esa aldea. No puedes hacer misiones para ella.")
        return

    # Determinar rol ninja del jugador
    es_genin = "【🎓】Genin【🎓】" in roles_usuario
    es_chunin = "【🍁】Chunin【🍁】" in roles_usuario
    es_jonin = "【🥀】Jounin【🥀】" in roles_usuario

    if not (es_genin or es_chunin or es_jonin):
        await ctx.send("⚠️ No tienes un rango ninja válido.")
        return

    # Validar que puede hacer esa misión según su rango
    if rango == "genin" and not (es_genin or es_chunin or es_jonin):
        await ctx.send("❌ No puedes hacer misiones de rango Genin.")
        return
    if rango == "chunin" and not (es_chunin or es_jonin):
        await ctx.send("❌ No puedes hacer misiones de rango Chunin.")
        return
    if rango == "jonin" and not es_jonin:
        await ctx.send("❌ Solo Jounin puede hacer misiones de rango Jonin.")
        return

    # Cargar archivo y registrar misión
    with open(archivo_misiones, 'r', encoding='utf-8') as archivo:
        misiones = json.load(archivo)

    usuario_id = str(ctx.author.id)
    aldea_misiones = misiones.get(aldea, {"misiones": {"genin": 0, "chunin": 0, "jonin": 0}, "usuarios": {}})
    usuario_misiones = aldea_misiones["usuarios"].get(usuario_id, [])

    if rango in usuario_misiones:
        await ctx.send(f"⚠️ Ya realizaste una misión de rango **{rango}** esta semana.")
        return

    if len(usuario_misiones) >= 2:
        await ctx.send("🚫 Ya completaste el límite de **2 misiones** esta semana.")
        return

    # Registrar misión
    aldea_misiones["misiones"][rango] += 1
    usuario_misiones.append(rango)
    aldea_misiones["usuarios"][usuario_id] = usuario_misiones
    misiones[aldea] = aldea_misiones

    with open(archivo_misiones, 'w', encoding='utf-8') as archivo:
        json.dump(misiones, archivo, indent=2, ensure_ascii=False)

    await ctx.send(f"✅ Misión de rango **{rango.upper()}** completada exitosamente para **{aldea.capitalize()}**.")
@bot.command(name='estadomisiones')
async def estado_misiones(ctx, aldea: str):
    aldea = aldea.lower()

    try:
        with open('misiones_aldeas.json', 'r', encoding='utf-8') as archivo:
            misiones = json.load(archivo)
    except FileNotFoundError:
        await ctx.send("⚠️ Archivo de misiones no encontrado.")
        return

    if aldea not in misiones:
        await ctx.send(f"⚠️ La aldea '{aldea}' no existe.")
        return

    datos = misiones[aldea]["misiones"]

    embed = discord.Embed(
        title=f"📘 Estado de Misiones - {aldea.capitalize()}",
        color=discord.Color.blue()
    )
    embed.add_field(name="🔰 Genin", value=f"{datos['genin']} misiones", inline=False)
    embed.add_field(name="🎖️ Chunin", value=f"{datos['chunin']} misiones", inline=False)
    embed.add_field(name="🛡️ Jonin", value=f"{datos['jonin']} misiones", inline=False)

    await ctx.send(embed=embed)
# __________________________________________________________________________________________
# PROGRAMACION PARA NEGOCIOS ENTRE ALDEAS (CARAVANAS DE RECURSOS):
@bot.command(name="enviarcaravana")
async def enviar_caravana(ctx, tipo_caravana: str, aldea_origen: str, aldea_destino: str, encargado_str: str, *args):
    import os
    import json
    import re
    from datetime import datetime

    tipo_caravana = tipo_caravana.lower()
    aldea_origen = aldea_origen.lower()
    aldea_destino = aldea_destino.lower()

    archivo_caravanas = 'caravanas.json'
    archivo_inventario = 'recursos_generales_aldeas.json'
    archivo_armas = 'armas_aldeas.json'

    if not os.path.exists(archivo_caravanas):
        with open(archivo_caravanas, 'w', encoding='utf-8') as f:
            json.dump({"caravanas_activas": [], "robos_caravanas": {}}, f, indent=2, ensure_ascii=False)

    with open(archivo_caravanas, 'r', encoding='utf-8') as f:
        datos_caravanas = json.load(f)

    caravanas_activas = datos_caravanas.get("caravanas_activas", [])

    with open(archivo_inventario, 'r', encoding='utf-8') as f:
        inventario = json.load(f)

    with open(archivo_armas, 'r', encoding='utf-8') as f:
        armas_aldeas = json.load(f)

    if aldea_origen not in inventario or aldea_destino not in inventario:
        await ctx.send("⚠️ Aldea no válida. Verifica el nombre de origen y destino.")
        return

    roles_aldea_discord = {
        "konoha": "【🍃】Konohagakure【🍃】",
        "kumogakure": "【☁️】Kumogakure【☁️】",
        "kirigakure": "【💧】Kirigakure【💧】",
        "kinkogakure": "【⚒️】Kinkōgakure【⚒️】",
        "sunagakure": "【⏳】Sunagakure【⏳】",
        "iwagakure": "【🗻】Iwagakure【🗻】"
    }

    rol_aldea = discord.utils.get(ctx.guild.roles, name=roles_aldea_discord[aldea_origen])
    if rol_aldea not in ctx.author.roles:
        await ctx.send("🚫 No puedes enviar caravanas desde una aldea a la que no perteneces.")
        return

    encargado_id = int(re.search(r"\d+", encargado_str).group())
    encargado = ctx.guild.get_member(encargado_id)
    if not encargado:
        await ctx.send("❌ No se pudo identificar al encargado.")
        return

    if rol_aldea not in encargado.roles:
        await ctx.send("🚫 El encargado no pertenece a la aldea de origen.")
        return

    if tipo_caravana in ["recursos", "armas"]:
        rol_productor = discord.utils.get(ctx.guild.roles, name=f"【👷】Productor {aldea_origen.capitalize()}【👷】")
        if rol_productor not in ctx.author.roles:
            await ctx.send("🚫 Solo los productores pueden enviar caravanas de recursos o armas.")
            return

    hoy = datetime.now().strftime("%Y-%m-%d")
    semanales = [c for c in caravanas_activas if c["origen"] == aldea_origen]
    diarias = [c for c in semanales if c["fecha_envio"] == hoy]

    if len(semanales) >= 4:
        await ctx.send("🚫 Ya enviaste las **4 caravanas semanales** permitidas.")
        return
    if len(diarias) >= 1:
        await ctx.send("🚫 Solo puedes enviar **una caravana por día**.")
        return

    carga = {}
    escoltas = []
    personas = []

    if tipo_caravana == "personas":
        if "escoltas:" in args:
            idx = args.index("escoltas:")
            personas = args[:idx]
            escoltas = args[idx+1:]
        else:
            personas = args

        if len(escoltas) > 2:
            await ctx.send("⚠️ Solo puedes tener un máximo de **2 escoltas**.")
            return

        carga = {"personas": personas}

    elif tipo_caravana == "armas":
        if not args:
            await ctx.send("❌ Debes especificar las armas que deseas enviar.")
            return

        armas_carga = {}
        total_armas = 0

        for arg in args:
            if ":" not in arg:
                await ctx.send(f"❌ Formato inválido en `{arg}`. Usa el formato `arma:cantidad`.")
                return
            nombre, cantidad = arg.split(":")
            nombre = nombre.strip()
            cantidad = int(cantidad)
            nombre_lower = nombre.lower()
            if cantidad <= 0:
                await ctx.send(f"❌ La cantidad de '{nombre}' debe ser mayor a cero.")
                return
            encontrada = False
            for id_arma, arma in list(armas_aldeas[aldea_origen].items()):
                if arma["nombre"].strip().lower() == nombre_lower:
                    if arma["cantidad"] < cantidad:
                        await ctx.send(f"❌ No hay suficientes unidades de '{nombre}' en el inventario de {aldea_origen}.")
                        return
                    armas_aldeas[aldea_origen][id_arma]["cantidad"] -= cantidad
                    if armas_aldeas[aldea_origen][id_arma]["cantidad"] <= 0:
                        del armas_aldeas[aldea_origen][id_arma]
                    armas_carga[nombre] = armas_carga.get(nombre, 0) + cantidad
                    total_armas += cantidad
                    encontrada = True
                    break
            if not encontrada:
                await ctx.send(f"❌ El arma '{nombre}' no existe en el inventario de la aldea.")
                return

        if total_armas > 8:
            await ctx.send("⚠️ Solo puedes transportar **hasta 8 armas** por caravana.")
            return

        if not armas_carga:
            await ctx.send("❌ No se cargó ninguna arma válida. Caravana cancelada.")
            return

        carga = {"armas": armas_carga}

    elif tipo_caravana == "recursos":
        total = 0
        for r in args:
            if ":" not in r:
                continue
            tipo, cantidad = r.split(":")
            tipo = tipo.lower()
            cantidad = int(cantidad)
            if tipo not in ["comida", "agua", "ropas", "medicamentos", "minerales"]:
                await ctx.send(f"❌ Recurso inválido: `{tipo}`.")
                return
            if cantidad <= 0:
                await ctx.send("❌ No puedes enviar cantidades negativas o cero.")
                return
            if inventario[aldea_origen][tipo] < cantidad:
                await ctx.send(f"❌ No tienes suficiente `{tipo}` en el inventario.")
                return
            carga[tipo] = cantidad
            total += cantidad

        if total > 40:
            await ctx.send("⚠️ Solo puedes enviar un máximo de **40 recursos** por caravana.")
            return

        for tipo, cant in carga.items():
            inventario[aldea_origen][tipo] -= cant

    nueva_caravana = {
        "tipo": tipo_caravana,
        "origen": aldea_origen,
        "destino": aldea_destino,
        "encargado_id": str(encargado.id),
        "escoltas": escoltas,
        "recursos": carga,
        "fecha_envio": hoy
    }

    if tipo_caravana == "personas":
        nueva_caravana["personas"] = personas

    caravanas_activas.append(nueva_caravana)
    datos_caravanas["caravanas_activas"] = caravanas_activas

    with open(archivo_caravanas, 'w', encoding='utf-8') as f:
        json.dump(datos_caravanas, f, indent=2, ensure_ascii=False)

    with open(archivo_inventario, 'w', encoding='utf-8') as f:
        json.dump(inventario, f, indent=2, ensure_ascii=False)

    with open(archivo_armas, 'w', encoding='utf-8') as f:
        json.dump(armas_aldeas, f, indent=2, ensure_ascii=False)

    resumen = ""
    if tipo_caravana == "personas":
        resumen = "🧍 Personas escoltadas:\n" + "\n".join([f" - {p}" for p in personas]) if personas else "⚠️ No hay personas."
    elif tipo_caravana == "armas":
        resumen = "🔫 Armas transportadas:\n" + "\n".join([f" - {nombre}: {cant}" for nombre, cant in carga.get("armas", {}).items()])
    else:
        resumen = "\n".join([f"🔹 {k.capitalize()}: {v}" for k, v in carga.items()])

    escoltas_info = "\n".join([f"🛡️ Escolta: {e}" for e in escoltas]) if escoltas else "🔓 Sin escoltas."

    await ctx.send(
        f"📦 Caravana **{tipo_caravana.upper()}** enviada de **{aldea_origen.capitalize()}** a **{aldea_destino.capitalize()}**.\n"
        f"🧭 Encargado: {encargado.mention}\n"
        f"{escoltas_info}\n"
        f"{resumen}"
    )

# __________________________________________________________________________________________
# PROGRAMACION ENTREGA DE MERCANCIAS (CARAVANAS DE RECURSOS):
@bot.command(name="entregarmercancia")
async def entregar_mercancia(ctx, destino_entrega=None, *args):
    import os
    import json
    import re

    archivo_caravanas = 'caravanas.json'
    archivo_inventario = 'recursos_generales_aldeas.json'
    archivo_armas = 'armas_aldeas.json'
    archivo_usuarios = 'armas_usuarios.json'

    if not os.path.exists(archivo_caravanas):
        await ctx.send("⚠️ No hay caravanas registradas.")
        return

    with open(archivo_caravanas, 'r', encoding='utf-8') as f:
        datos_caravanas = json.load(f)

    caravanas_activas = datos_caravanas.get("caravanas_activas", [])
    autor_id = str(ctx.author.id)

    caravana = next((c for c in caravanas_activas if c["encargado_id"] == autor_id), None)

    if not caravana:
        await ctx.send("🚫 No tienes ninguna caravana activa registrada.")
        return

    tipo = caravana["tipo"]
    origen = caravana["origen"]
    destino_original = caravana["destino"]
    carga = caravana["recursos"]
    escoltas = caravana.get("escoltas", [])
    personas = carga.get("personas", [])
    es_robada = caravana.get("robada", False)

    nuevo_encargado = None
    destino_final = destino_original

    if destino_entrega:
        if destino_entrega.startswith("<@") and destino_entrega.endswith(">"):
            match = re.search(r"\d+", destino_entrega)
            if match:
                user_id = int(match.group())
                nuevo_encargado = ctx.guild.get_member(user_id)
                if not nuevo_encargado:
                    await ctx.send("❌ No se pudo encontrar al jugador mencionado.")
                    return
                if not es_robada and tipo != "personas":
                    if not any("Productor" in r.name for r in nuevo_encargado.roles):
                        await ctx.send("❌ Solo productores pueden recibir caravanas de recursos o armas.")
                        return
        else:
            destino_final = destino_entrega.lower()

    entrega_parcial = {}
    if args and not nuevo_encargado and tipo == "recursos":
        for r in args:
            if ":" not in r:
                continue
            tipo_r, cantidad = r.split(":")
            tipo_r = tipo_r.lower()
            cantidad = int(cantidad)
            if tipo_r not in carga or cantidad > carga[tipo_r]:
                await ctx.send(f"❌ No puedes entregar más de lo que llevas de {tipo_r}.")
                return
            entrega_parcial[tipo_r] = cantidad

    elif args and not nuevo_encargado and tipo == "armas":
        entrega_armas = {}
        for r in args:
            if ":" not in r:
                await ctx.send(f"❌ Formato inválido en `{r}`. Usa `arma:cantidad`.")
                return
            nombre, cantidad = r.split(":")
            nombre = nombre.strip()
            cantidad = int(cantidad)
            if nombre not in carga.get("armas", {}):
                await ctx.send(f"❌ El arma `{nombre}` no está en la caravana.")
                return
            if cantidad > carga["armas"][nombre]:
                await ctx.send(f"❌ Solo llevas {carga['armas'][nombre]} de `{nombre}`.")
                return
            entrega_armas[nombre] = cantidad
        entrega_parcial = entrega_armas

    embed = discord.Embed(
        title="📦 Entrega de Mercancía",
        description=f"Desde **{origen.capitalize()}**",
        color=discord.Color.green()
    )

    if nuevo_encargado:
        caravana["encargado_id"] = str(nuevo_encargado.id)
        msg = f"📦 Has transferido la **caravana completa** a {nuevo_encargado.mention}."
        embed.add_field(name="📍 Nueva Entrega", value=msg, inline=False)

    elif tipo == "recursos":
        with open(archivo_inventario, 'r', encoding='utf-8') as f:
            inventario = json.load(f)

        if destino_final not in inventario:
            await ctx.send(f"⚠️ La aldea destino '{destino_final}' no existe.")
            return

        for tipo_r, cant in entrega_parcial.items():
            inventario[destino_final][tipo_r] += cant
            embed.add_field(name=f"📦 {tipo_r.capitalize()}", value=f"{cant} unidades", inline=True)
            carga[tipo_r] -= cant
            if carga[tipo_r] <= 0:
                del carga[tipo_r]

        with open(archivo_inventario, 'w', encoding='utf-8') as f:
            json.dump(inventario, f, indent=2, ensure_ascii=False)

    elif tipo == "armas":
        with open(archivo_armas, 'r', encoding='utf-8') as f:
            data_armas = json.load(f)
        with open(archivo_usuarios, 'r', encoding='utf-8') as f:
            data_usuarios = json.load(f)

        armas_a_entregar = entrega_parcial if entrega_parcial else carga.get("armas", {})

        if nuevo_encargado:
            user_id = str(nuevo_encargado.id)
            user_inv = data_usuarios.get(user_id, [])
            for nombre, cantidad in armas_a_entregar.items():
                for _ in range(cantidad):
                    user_inv.append({
                        "id": "transporte",
                        "nombre": nombre,
                        "fecha_creacion": "transferencia"
                    })
                embed.add_field(name="🗡️ Arma entregada a usuario", value=f"{nombre}: {cantidad}", inline=True)
            data_usuarios[user_id] = user_inv

            with open(archivo_usuarios, 'w', encoding='utf-8') as f:
                json.dump(data_usuarios, f, indent=2, ensure_ascii=False)
        else:
            if destino_final not in data_armas:
                await ctx.send(f"❌ La aldea destino '{destino_final}' no es válida.")
                return
            for nombre, cantidad in armas_a_entregar.items():
                nombre_lower = nombre.lower()
                encontrada = False
                for id_arma, info in data_armas[destino_final].items():
                    if info["nombre"].strip().lower() == nombre_lower:
                        data_armas[destino_final][id_arma]["cantidad"] += cantidad
                        encontrada = True
                        break
                if not encontrada:
                    nuevo_id = str(max([int(k) for k in data_armas[destino_final].keys()] + [0]) + 1)
                    data_armas[destino_final][nuevo_id] = {
                        "nombre": nombre,
                        "cantidad": cantidad,
                        "fecha_creacion": "transferencia"
                    }
                embed.add_field(name="🗡️ Arma entregada a aldea", value=f"{nombre}: {cantidad}", inline=True)

            with open(archivo_armas, 'w', encoding='utf-8') as f:
                json.dump(data_armas, f, indent=2, ensure_ascii=False)

        for nombre, cantidad in armas_a_entregar.items():
            carga["armas"][nombre] -= cantidad
            if carga["armas"][nombre] <= 0:
                del carga["armas"][nombre]

        if not carga["armas"]:
            carga.clear()

    elif tipo == "personas":
        for persona in personas:
            embed.add_field(name="🧍 Persona escoltada", value=persona, inline=True)
        carga["personas"] = []

    if escoltas:
        embed.set_footer(text=f"Escoltas: {', '.join(escoltas)}")

    if not carga or nuevo_encargado:
        datos_caravanas["caravanas_activas"] = [
            c for c in caravanas_activas if c["encargado_id"] != autor_id
        ]

    with open(archivo_caravanas, 'w', encoding='utf-8') as f:
        json.dump(datos_caravanas, f, indent=2, ensure_ascii=False)

    embed.set_author(name=f"Entregado por: {ctx.author.display_name}")
    await ctx.send(embed=embed)


#___________________________________________________________________________________________________________________
# VER CARAVANAS :D (ESPIONAJE :3) 
@bot.command(name="vercaravanas")
async def ver_caravanas(ctx):
    import os
    import json

    archivo_caravanas = 'caravanas.json'

    if not os.path.exists(archivo_caravanas):
        await ctx.send("⚠️ No se encontró el archivo de caravanas.")
        return

    with open(archivo_caravanas, 'r', encoding='utf-8') as f:
        datos_caravanas = json.load(f)

    caravanas = datos_caravanas.get("caravanas_activas", [])

    if not caravanas:
        await ctx.send("📭 No hay caravanas activas en este momento.")
        return

    embed = discord.Embed(
        title="🚚 Caravanas Activas",
        description="Lista de caravanas en tránsito entre aldeas",
        color=discord.Color.orange()
    )

    for idx, caravana in enumerate(caravanas, start=1):
        encargado_id = int(caravana['encargado_id'])
        encargado_mention = f"<@{encargado_id}>"
        origen = caravana['origen'].capitalize()
        destino = caravana['destino'].capitalize()
        fecha = caravana['fecha_envio']
        tipo = caravana.get('tipo', 'recursos')
        escoltas = caravana.get('escoltas', [])

        contenido = (
            f"🏳️ **Origen:** {origen}\n"
            f"🎯 **Destino:** {destino}\n"
            f"👤 **Encargado:** {encargado_mention}\n"
            f"📅 **Fecha:** {fecha}\n"
            f"📦 **Tipo de Caravana:** {tipo.capitalize()}\n"
        )

        if tipo == "recursos":
            recursos = "\n".join([f"🔹 {k.capitalize()}: {v}" for k, v in caravana["recursos"].items()])
            contenido += f"{recursos}\n"

        elif tipo == "armas":
            armas = caravana.get("recursos", {}).get("armas", [])
            armas_texto = "\n".join([f"🗡️ {a}" for a in armas]) if armas else "⚠️ No hay armas especificadas."
            contenido += f"{armas_texto}\n"

        elif tipo == "personas":
            personas = caravana.get("recursos", {}).get("personas", [])
            personas_texto = "\n".join([f"🧍 {p}" for p in personas]) if personas else "⚠️ No se están escoltando personas."
            contenido += f"{personas_texto}\n"

        if escoltas:
            escolta_texto = ", ".join(escoltas)
            contenido += f"🛡️ **Escoltas:** {escolta_texto}\n"

        embed.add_field(name=f"📦 Caravana #{idx}", value=contenido, inline=False)

    await ctx.send(embed=embed)
#___________________________________________________________________________________________________________________
# ROBAR CARAVANAS >:D
@bot.command(name="robocaravana")
async def robar_caravana(ctx, id_caravana: int, *nuevos_escoltas):
    import json
    import os

    archivo_caravanas = 'caravanas.json'
    archivo_robos = 'robos_semanales.json'

    if not os.path.exists(archivo_caravanas):
        await ctx.send("⚠️ No hay caravanas activas.")
        return

    with open(archivo_caravanas, 'r', encoding='utf-8') as f:
        datos_caravanas = json.load(f)

    caravanas = datos_caravanas.get("caravanas_activas", [])

    if id_caravana < 1 or id_caravana > len(caravanas):
        await ctx.send("⚠️ ID de caravana inválido.")
        return

    caravana = caravanas[id_caravana - 1]
    aldea_origen = caravana["origen"]
    es_robada = caravana.get("robada", False)

    # Cargar robos semanales
    robos_realizados = {}
    if os.path.exists(archivo_robos):
        with open(archivo_robos, 'r', encoding='utf-8') as f:
            robos_realizados = json.load(f)

    # Solo limitar robos si la caravana aún no ha sido robada
    if not es_robada:
        robos_actuales = robos_realizados.get(aldea_origen, 0)
        if robos_actuales >= 2:
            await ctx.send(f"🚫 Ya se han robado 2 caravanas de {aldea_origen.capitalize()} esta semana.")
            return
        robos_realizados[aldea_origen] = robos_actuales + 1

    # Transferir propiedad
    caravana["robada"] = True
    caravana["origen"] = "desconocido"
    caravana["encargado_id"] = str(ctx.author.id)

    # ⚠️ Cambiar escoltas
    if nuevos_escoltas:
        caravana["escoltas"] = list(nuevos_escoltas)
    else:
        caravana["escoltas"] = []

    # Guardar cambios
    with open(archivo_caravanas, 'w', encoding='utf-8') as f:
        json.dump(datos_caravanas, f, indent=2, ensure_ascii=False)

    with open(archivo_robos, 'w', encoding='utf-8') as f:
        json.dump(robos_realizados, f, indent=2, ensure_ascii=False)

    # Mensaje de éxito
    nuevos_escort_txt = (
        f"🛡️ Nuevos escoltas: {', '.join(nuevos_escoltas)}"
        if nuevos_escoltas else "🛡️ Esta caravana ahora viaja sin escoltas."
    )

    await ctx.send(
        f"💥 ¡Caravana #{id_caravana} robada exitosamente!\n"
        f"Ahora eres el nuevo encargado: {ctx.author.mention}.\n"
        f"{nuevos_escort_txt}"
    )
 
 # _______________________________________________________________________________________________
 # CONSUMIR LOS RECURSOS DE LA ALDEA :D

@bot.command(name="sanar")
async def sanar(ctx):
    await consumir_recurso(ctx, recurso="medicamentos", cantidad=6, solo_productor=True)

@bot.command(name="cambiarropa")
async def cambiarropa(ctx):
    await consumir_recurso(ctx, recurso="ropas", cantidad=2)

@bot.command(name="consumirropa")
async def consumirropa(ctx):
    await consumir_recurso(ctx, recurso="ropas", cantidad=2)

@bot.command(name="beberagua")
async def beberagua(ctx):
    await consumir_recurso(ctx, recurso="agua", cantidad=2)

@bot.command(name="comer")
async def comer(ctx):
    await consumir_recurso(ctx, recurso="comida", cantidad=4)

@bot.command(name="creararma1")
async def creararma(ctx):
    await consumir_recurso(ctx, recurso="minerales", cantidad=3, solo_productor=True, solo_kinko=True)

@bot.command(name="reparararma")
async def reparararma(ctx):
    await consumir_recurso(ctx, recurso="minerales", cantidad=1, solo_productor=True, solo_kinko=True)

@bot.command(name="repararlegendaria")
async def repararlegendaria(ctx):
    await consumir_recurso(ctx, recurso="minerales", cantidad=20, solo_productor=True, solo_kinko=True)

# _______________________________________
# Función base para consumo de recursos

async def consumir_recurso(ctx, recurso, cantidad, solo_productor=False, solo_kinko=False):
    import json
    import os

    archivo_inventario = 'recursos_generales_aldeas.json'
    if not os.path.exists(archivo_inventario):
        await ctx.send("❌ No se encontró el archivo de inventario.")
        return

    with open(archivo_inventario, 'r', encoding='utf-8') as f:
        inventario = json.load(f)

    # Mapear roles de aldeas
    roles_aldea = {
        "konoha": "【🍃】Konohagakure【🍃】",
        "kumogakure": "【☁️】Kumogakure【☁️】",
        "kirigakure": "【💧】Kirigakure【💧】",
        "kinkogakure": "【⚒️】Kinkōgakure【⚒️】",
        "sunagakure": "【⏳】Sunagakure【⏳】",
        "iwagakure": "【🗻】Iwagakure【🗻】"
    }

    roles_productores = {
        "konoha": "【👷】Productor Konoha【👷】",
        "kumogakure": "【👷】Productor Kumogakure【👷】",
        "kirigakure": "【👷】Productor Kirigakure【👷】",
        "kinkogakure": "【👷】Productor Kinkogakure【👷】",
        "sunagakure": "【👷】Productor Sunagakure【👷】",
        "iwagakure": "【👷】Productor Iwagakure【👷】"
    }

    # Detectar a qué aldea pertenece el usuario
    roles_usuario = [r.name.strip() for r in ctx.author.roles]
    aldea_usuario = None

    for aldea, rol_discord in roles_aldea.items():
        if rol_discord in roles_usuario:
            aldea_usuario = aldea
            break

    if not aldea_usuario:
        await ctx.send("🚫 No perteneces a ninguna aldea válida.")
        return

    if solo_productor:
        rol_prod = roles_productores[aldea_usuario]
        if rol_prod not in roles_usuario:
            await ctx.send("🚫 Este comando solo puede ser usado por **productores**.")
            return

    if solo_kinko and aldea_usuario != "kinkogakure":
        await ctx.send("🚫 Solo los productores de **Kinkogakure** pueden usar este comando.")
        return

    # Validar recurso disponible
    recursos_aldea = inventario[aldea_usuario]
    if recursos_aldea.get(recurso, 0) < cantidad:
        await ctx.send(f"⚠️ No hay suficientes `{recurso}` en el inventario de tu aldea.")
        return

    # Descontar
    inventario[aldea_usuario][recurso] -= cantidad

    with open(archivo_inventario, 'w', encoding='utf-8') as f:
        json.dump(inventario, f, indent=2, ensure_ascii=False)

    await ctx.send(
        f"✅ Has consumido **{cantidad} unidades de {recurso}** de tu aldea (**{aldea_usuario.capitalize()}**)."
    )
# NUEVA VERSION DE LA CREACION DE ARMAS :D
@bot.command(name="creararma")
async def crear_arma(ctx, *, nombre_arma: str):
    import json
    import os
    from datetime import datetime

    archivo_inventario = 'recursos_generales_aldeas.json'
    archivo_armas = 'armas_aldeas.json'

    # Verificación de archivos
    if not os.path.exists(archivo_inventario) or not os.path.exists(archivo_armas):
        await ctx.send("❌ Archivos de inventario o armas no encontrados.")
        return

    # Verificación de roles
    roles = {r.name for r in ctx.author.roles}
    if "【⚒️】Kinkōgakure【⚒️】" not in roles or "【👷】Productor Kinkogakure【👷】" not in roles:
        await ctx.send("🚫 Solo los **productores de Kinkōgakure** pueden usar este comando.")
        return

    # Cargar inventarios
    with open(archivo_inventario, 'r', encoding='utf-8') as f:
        inventario = json.load(f)

    with open(archivo_armas, 'r', encoding='utf-8') as f:
        armas = json.load(f)

    # Validar que Kinkōgakure tenga minerales
    if inventario["kinkogakure"]["minerales"] < 3:
        await ctx.send("⚠️ No hay suficientes minerales para crear un arma. Se necesitan al menos **3**.")
        return

    # Descontar minerales
    inventario["kinkogakure"]["minerales"] -= 3

    # Buscar si ya existe un arma con ese nombre (ignorando mayúsculas)
    armas_kinko = armas["kinkogakure"]
    nombre_normalizado = nombre_arma.strip().lower()
    id_existente = None
    for arma_id, data in armas_kinko.items():
        if data["nombre"].strip().lower() == nombre_normalizado:
            id_existente = arma_id
            break

    # Crear nueva o actualizar existente
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    if id_existente:
        armas_kinko[id_existente]["cantidad"] += 1
    else:
        nuevo_id = str(max([int(k) for k in armas_kinko.keys()] + [0]) + 1)
        armas_kinko[nuevo_id] = {
            "nombre": nombre_arma.strip(),
            "cantidad": 1,
            "fecha_creacion": fecha_actual
        }

    # Guardar archivos actualizados
    with open(archivo_inventario, 'w', encoding='utf-8') as f:
        json.dump(inventario, f, indent=2, ensure_ascii=False)

    with open(archivo_armas, 'w', encoding='utf-8') as f:
        json.dump(armas, f, indent=2, ensure_ascii=False)

    await ctx.send(f"✅ Se ha creado una unidad del arma **{nombre_arma}** y fue registrada exitosamente.")

#___________________________________________________________________________________________________________________
# VENTA DE ARMAS Y ENTREGA DE ARMAS:
# Archivos de armas
def obtener_aldea_usuario(user):
    roles_usuario = [role.name for role in user.roles]

    mapeo_roles = {
        "【🍃】Konohagakure【🍃】": "konoha",
        "【☁️】Kumogakure【☁️】": "kumogakure",
        "【💧】Kirigakure【💧】": "kirigakure",
        "【⚒️】Kinkōgakure【⚒️】": "kinkogakure",
        "【⏳】Sunagakure【⏳】": "sunagakure",
        "【🗻】Iwagakure【🗻】": "iwagakure"
    }

    for rol in roles_usuario:
        if rol in mapeo_roles:
            return mapeo_roles[rol]

    return None
@bot.command()
async def armasaldea(ctx):
    import json
    import os

    archivo_armas = 'armas_aldeas.json'

    aldea = obtener_aldea_usuario(ctx.author)

    if not aldea:
        return await ctx.send("🚫 No perteneces a ninguna aldea reconocida.")

    if not os.path.exists(archivo_armas):
        return await ctx.send("❌ Archivo de armas no encontrado.")

    with open(archivo_armas, 'r', encoding='utf-8') as f:
        armas = json.load(f)

    armas_aldea = armas.get(aldea, {})

    if not armas_aldea:
        return await ctx.send(f"🔒 Tu aldea ({aldea}) no tiene armas registradas aún.")

    mensaje = f"🛡️ **Inventario de armas de `{aldea.capitalize()}`**:\n"
    for arma_id, arma in armas_aldea.items():
        mensaje += (
            f"🔸 ID `{arma_id}` - {arma['nombre']} | Cantidad: **{arma['cantidad']}** | "
            f"Fecha: `{arma['fecha_creacion']}`\n"
        )

    await ctx.send(mensaje)
#ARMAS DE USUARIOS >:D
@bot.command()
async def misarmas(ctx):
    import json
    import os

    archivo_usuarios = 'armas_usuarios.json'
    user_id = str(ctx.author.id)

    # Verificar existencia del archivo
    if not os.path.exists(archivo_usuarios):
        return await ctx.send("📦 No tienes armas registradas.")

    with open(archivo_usuarios, 'r', encoding='utf-8') as f:
        data = json.load(f)

    inventario = data.get(user_id, [])

    if not inventario:
        return await ctx.send("📭 No tienes armas en tu inventario personal.")

    # Crear mensaje con las armas
    mensaje = f"🗡️ **Tus armas personales:**\n"
    for arma in inventario:
        mensaje += f"🔹 `{arma['nombre']}` (ID: `{arma['id']}`) – Fecha: `{arma['fecha_creacion']}`\n"

    await ctx.send(mensaje)


# VENDER ARMAS
@bot.command()
async def venderarma(ctx, miembro: discord.Member, *, nombre_arma: str):
    import json
    import os
    from datetime import datetime

    archivo_armas = 'armas_aldeas.json'
    archivo_usuarios = 'armas_usuarios.json'

    # Función para identificar la aldea según los roles personales
    def obtener_aldea_usuario(user):
        roles_usuario = [role.name for role in user.roles]

        mapeo_roles = {
            "【🍃】Konohagakure【🍃】": "konoha",
            "【☁️】Kumogakure【☁️】": "kumogakure",
            "【💧】Kirigakure【💧】": "kirigakure",
            "【⚒️】Kinkōgakure【⚒️】": "kinkogakure",
            "【⏳】Sunagakure【⏳】": "sunagakure",
            "【🗻】Iwagakure【🗻】": "iwagakure",
            "【🌳】Hokage【🌳】": "konoha",
            "【☁️】Raikage【☁️】": "kumogakure",
            "【🌊】Mizukage【🌊】": "kirigakure",
            "【⚒️】MAESTRO HERRERO【⚒️】": "kinkogakure",
            "【⌛】Kazekage【⌛】": "sunagakure",
            "【⛰️】Tsuchikage【⛰️】": "iwagakure"
        }

        for rol in roles_usuario:
            if rol in mapeo_roles:
                return mapeo_roles[rol]
        return None

    roles_usuario = {r.name for r in ctx.author.roles}
    aldea = obtener_aldea_usuario(ctx.author)

    if not aldea:
        return await ctx.send("🚫 No se pudo determinar a qué aldea perteneces.")

    # Verificación de autoridad (rol de kage general o maestro herrero)
    es_kage = "【👑】kage【👑】" in roles_usuario
    es_herrero = "【⚒️】MAESTRO HERRERO【⚒️】" in roles_usuario
    es_vendedor = "【⚔️ 】Vendedor de Armas【💰 】" in roles_usuario

    if not (es_kage or es_herrero or es_vendedor):
        return await ctx.send("🚫 Solo un **Kage**, **Maestro Herrero** o **Vendedor de Armas** puede vender armas.")

    # Validar archivos
    if not os.path.exists(archivo_armas) or not os.path.exists(archivo_usuarios):
        return await ctx.send("❌ Archivos de armas no encontrados.")

    with open(archivo_armas, 'r', encoding='utf-8') as f:
        armas = json.load(f)

    armas_aldea = armas.get(aldea, {})

    nombre_normalizado = nombre_arma.strip().lower()
    arma_encontrada = None
    arma_id = None

    for i, arma in armas_aldea.items():
        if arma["nombre"].strip().lower() == nombre_normalizado:
            arma_encontrada = arma
            arma_id = i
            break

    if not arma_encontrada:
        return await ctx.send("⚠️ Esa arma no existe en el inventario de tu aldea.")

    if arma_encontrada["cantidad"] <= 0:
        return await ctx.send("⚠️ No hay unidades disponibles de esa arma para vender.")

    # Descontar del inventario de la aldea
    arma_encontrada["cantidad"] -= 1
    if arma_encontrada["cantidad"] == 0:
        del armas_aldea[arma_id]

    # Registrar en el inventario personal del usuario
    with open(archivo_usuarios, 'r', encoding='utf-8') as f:
        armas_usuarios = json.load(f)

    id_objetivo = str(miembro.id)
    if id_objetivo not in armas_usuarios:
        armas_usuarios[id_objetivo] = []

    armas_usuarios[id_objetivo].append({
        "id": arma_id,
        "nombre": arma_encontrada["nombre"],
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d")
    })

    # Guardar los cambios
    with open(archivo_armas, 'w', encoding='utf-8') as f:
        json.dump(armas, f, indent=2, ensure_ascii=False)

    with open(archivo_usuarios, 'w', encoding='utf-8') as f:
        json.dump(armas_usuarios, f, indent=2, ensure_ascii=False)

    await ctx.send(f"✅ Se ha vendido el arma **{arma_encontrada['nombre']}** a {miembro.mention}.")

# DAR ARMAS >:D
@bot.command()
async def dararma(ctx, *args):
    import json
    import os
    from datetime import datetime

    archivo_usuarios = 'armas_usuarios.json'
    archivo_armas = 'armas_aldeas.json'
    autor_id = str(ctx.author.id)

    # ⚠️ Validación básica de entrada
    if len(args) < 2:
        return await ctx.send("❗ Uso correcto:\n`!dararma aldea <nombre del arma>`\n`!dararma @usuario <nombre del arma>`")

    # Interpretar argumentos
    destino_raw = args[0]
    nombre_arma = " ".join(args[1:]).strip().lower()

    # Cargar archivos
    if not os.path.exists(archivo_usuarios) or not os.path.exists(archivo_armas):
        return await ctx.send("❌ Archivos de armas no encontrados.")

    with open(archivo_usuarios, 'r', encoding='utf-8') as f:
        data_usuarios = json.load(f)

    with open(archivo_armas, 'r', encoding='utf-8') as f:
        data_aldeas = json.load(f)

    inventario_autor = data_usuarios.get(autor_id, [])

    # Buscar arma en inventario del autor
    arma_transferida = None
    for arma in inventario_autor:
        if arma["nombre"].strip().lower() == nombre_arma:
            arma_transferida = arma
            break

    if not arma_transferida:
        return await ctx.send("⚠️ No tienes esa arma en tu inventario.")

    # 🏯 Dar arma a la aldea
    if destino_raw.lower() in ["aldea", "alaldea", "aldea-ninja"]:
        def obtener_aldea_usuario(user):
            roles_usuario = [role.name for role in user.roles]
            mapeo_roles = {
                "【🍃】Konohagakure【🍃】": "konoha",
                "【☁️】Kumogakure【☁️】": "kumogakure",
                "【💧】Kirigakure【💧】": "kirigakure",
                "【⚒️】Kinkōgakure【⚒️】": "kinkogakure",
                "【⏳】Sunagakure【⏳】": "sunagakure",
                "【🗻】Iwagakure【🗻】": "iwagakure",
                "【🌳】Hokage【🌳】": "konoha",
                "【☁️】Raikage【☁️】": "kumogakure",
                "【🌊】Mizukage【🌊】": "kirigakure",
                "【⚒️】MAESTRO HERRERO【⚒️】": "kinkogakure",
                "【⌛】Kazekage【⌛】": "sunagakure",
                "【⛰️】Tsuchikage【⛰️】": "iwagakure"
            }
            for rol in roles_usuario:
                if rol in mapeo_roles:
                    return mapeo_roles[rol]
            return None

        aldea = obtener_aldea_usuario(ctx.author)
        if not aldea:
            return await ctx.send("❌ No se pudo determinar tu aldea para devolver el arma.")

        armas_aldea = data_aldeas.get(aldea, {})

        # Ver si ya existe el arma
        id_existente = None
        for i, arma in armas_aldea.items():
            if arma["nombre"].strip().lower() == nombre_arma:
                id_existente = i
                break

        if id_existente:
            armas_aldea[id_existente]["cantidad"] += 1
        else:
            nuevo_id = str(max([int(k) for k in armas_aldea.keys()] + [0]) + 1)
            armas_aldea[nuevo_id] = {
                "nombre": arma_transferida["nombre"],
                "cantidad": 1,
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d")
            }

        # Quitar arma del usuario
        inventario_autor.remove(arma_transferida)
        data_usuarios[autor_id] = inventario_autor
        data_aldeas[aldea] = armas_aldea

        # Guardar
        with open(archivo_usuarios, 'w', encoding='utf-8') as f:
            json.dump(data_usuarios, f, indent=2, ensure_ascii=False)
        with open(archivo_armas, 'w', encoding='utf-8') as f:
            json.dump(data_aldeas, f, indent=2, ensure_ascii=False)

        return await ctx.send(f"✅ Has devuelto el arma **{arma_transferida['nombre']}** al inventario de tu aldea (**{aldea}**).")

    # 🧍 Transferencia a otro usuario
    try:
        miembro = await commands.MemberConverter().convert(ctx, destino_raw)
    except:
        return await ctx.send("❌ Usuario no válido o no mencionado correctamente.")

    receptor_id = str(miembro.id)
    roles_destino = {r.name for r in miembro.roles}

    if "【👑】kage【👑】" not in roles_destino and "【⚔️ 】Vendedor de Armas【💰 】" not in roles_destino:
        return await ctx.send("🚫 Solo puedes entregar armas a un **Kage**, un **Vendedor de Armas** o tu **aldea**.")

    # Agregar arma al receptor
    inventario_receptor = data_usuarios.get(receptor_id, [])
    inventario_receptor.append(arma_transferida)
    data_usuarios[receptor_id] = inventario_receptor

    # Quitar arma del autor
    inventario_autor.remove(arma_transferida)
    data_usuarios[autor_id] = inventario_autor

    # Guardar cambios
    with open(archivo_usuarios, 'w', encoding='utf-8') as f:
        json.dump(data_usuarios, f, indent=2, ensure_ascii=False)

    await ctx.send(f"✅ Has entregado el arma **{arma_transferida['nombre']}** a {miembro.mention}.")
# BORRAR ARMAS (STAFF)

# VERSION 2
@bot.command()
async def borrararma(ctx, destino, *, nombre_arma: str):
    import json
    import os

    archivo_usuarios = 'armas_usuarios.json'
    archivo_aldeas = 'armas_aldeas.json'

    # Roles con permiso global
    roles_permiso_global = {
        "【⛔️】ADMIN【🚫】",
        "【🥏】MODERADOR【🧶】",
        "【❌️】OWNER【❌️】"
    }

    # Roles por aldea autorizados
    roles_autorizados_aldeas = {
        "【⚒️】MAESTRO HERRERO【⚒️】",
        "【👑】kage【👑】"
    }

    roles_usuario = {r.name for r in ctx.author.roles}
    if not (roles_permiso_global & roles_usuario or roles_autorizados_aldeas & roles_usuario):
        return await ctx.send("🚫 No tienes permiso para borrar armas. Solo Staff, Kages o ciertos rangos de aldea pueden hacerlo.")

    nombre_normalizado = nombre_arma.strip().lower()

    # 💥 BORRAR ARMA DE ALDEA
    if destino.lower() in ["aldea", "a-la-aldea", "aldeaninja"]:
        if not os.path.exists(archivo_aldeas):
            return await ctx.send("❌ El archivo de armas de aldeas no existe.")

        def obtener_aldea_usuario(user):
            roles_usuario = [role.name for role in user.roles]
            mapeo_roles = {
                "【🍃】Konohagakure【🍃】": "konoha",
                "【☁️】Kumogakure【☁️】": "kumogakure",
                "【💧】Kirigakure【💧】": "kirigakure",
                "【⚒️】Kinkōgakure【⚒️】": "kinkogakure",
                "【⏳】Sunagakure【⏳】": "sunagakure",
                "【🗻】Iwagakure【🗻】": "iwagakure",
                "【🌳】Hokage【🌳】": "konoha",
                "【☁️】Raikage【☁️】": "kumogakure",
                "【🌊】Mizukage【🌊】": "kirigakure",
                "【⌛】Kazekage【⌛】": "sunagakure",
                "【⛰️】Tsuchikage【⛰️】": "iwagakure",
                "【⚒️】MAESTRO HERRERO【⚒️】": "kinkogakure"
            }
            for rol in roles_usuario:
                if rol in mapeo_roles:
                    return mapeo_roles[rol]
            return None

        aldea = obtener_aldea_usuario(ctx.author)
        if not aldea:
            return await ctx.send("❌ No se pudo identificar tu aldea.")

        with open(archivo_aldeas, 'r', encoding='utf-8') as f:
            data = json.load(f)

        armas = data.get(aldea, {})
        arma_id_encontrada = None

        for id_arma, info in armas.items():
            if info["nombre"].strip().lower() == nombre_normalizado:
                arma_id_encontrada = id_arma
                break

        if not arma_id_encontrada:
            return await ctx.send(f"⚠️ No se encontró esa arma en el inventario de **{aldea}**.")

        # Disminuir cantidad o eliminar
        armas[arma_id_encontrada]["cantidad"] -= 1
        if armas[arma_id_encontrada]["cantidad"] <= 0:
            del armas[arma_id_encontrada]

        data[aldea] = armas

        with open(archivo_aldeas, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return await ctx.send(f"🗑️ Se ha eliminado **1 unidad** de `{nombre_arma}` del inventario de **{aldea}**.")

    # 🧍 BORRAR ARMA DE USUARIO
    if not os.path.exists(archivo_usuarios):
        return await ctx.send("❌ El archivo de armas de usuarios no existe.")

    try:
        miembro = await commands.MemberConverter().convert(ctx, destino)
    except:
        return await ctx.send("❌ Usuario no válido o no mencionado correctamente.")

    with open(archivo_usuarios, 'r', encoding='utf-8') as f:
        data = json.load(f)

    user_id = str(miembro.id)
    inventario = data.get(user_id, [])

    if not inventario:
        return await ctx.send("📭 El usuario no tiene armas registradas.")

    arma_encontrada = None
    for arma in inventario:
        if arma["nombre"].strip().lower() == nombre_normalizado:
            arma_encontrada = arma
            break

    if not arma_encontrada:
        return await ctx.send("⚠️ El usuario no tiene esa arma en su inventario.")

    inventario.remove(arma_encontrada)
    data[user_id] = inventario

    with open(archivo_usuarios, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    await ctx.send(f"🗑️ Se ha eliminado **{arma_encontrada['nombre']}** del inventario de {miembro.mention}.")

# BORRAR INVENTARIO DE ARMAS DE CADA PERSONA

@bot.command()
async def borrararmasusuario(ctx, miembro: discord.Member):
    import json
    import os

    archivo_usuarios = 'armas_usuarios.json'

    # Roles con permiso global
    roles_permiso_global = {
        "【⛔️】ADMIN【🚫】",
        "【🥏】MODERADOR【🧶】",
        "【❌️】OWNER【❌️】"
    }

    # Roles por aldea autorizados
    roles_autorizados_aldeas = {
    }

    roles_usuario = {r.name for r in ctx.author.roles}
    if not (roles_permiso_global & roles_usuario or roles_autorizados_aldeas & roles_usuario):
        return await ctx.send("🚫 No tienes permiso para borrar inventarios completos. Solo Staff, Kages o ciertos rangos de aldea pueden hacerlo.")

    if not os.path.exists(archivo_usuarios):
        return await ctx.send("❌ El archivo de armas de usuarios no existe.")

    with open(archivo_usuarios, 'r', encoding='utf-8') as f:
        data = json.load(f)

    user_id = str(miembro.id)

    if user_id not in data or not data[user_id]:
        return await ctx.send("📭 El usuario no tiene armas que borrar.")

    cantidad = len(data[user_id])
    data[user_id] = []

    with open(archivo_usuarios, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    await ctx.send(f"🧨 Se han borrado **{cantidad} armas** del inventario de {miembro.mention}.")

# RULETAS! >:D
@bot.command(name="kenjutsu")
async def gacha_kenjutsu(ctx):
    import random
    import discord

    elementos = [
        "💧 Agua",
        "⚡ Relámpago",
        "🔥 Fuego",
        "🌪️ Viento",
        "💨 neblina"
    ]

    random.shuffle(elementos)
    resultado = elementos[0]

    embed = discord.Embed(
        title="🎴 Resultado Gacha - Kenjutsu",
        description=f"🗡️ Has obtenido el estilo: **{resultado}**",
        color=discord.Color.blue()
    )
    embed.set_footer(text="¡Usa este resultado con sabiduría, shinobi!")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)

@bot.command(name="RUTAS")
async def gacha_kenjutsu(ctx):
    import random
    import discord

    opcion = [
        "RUTA 2",
        "RUTA 1"
    ]

    random.shuffle(opcion)
    resultado = opcion[0]
    embed = discord.Embed(
        title="🎴 Resultado Gacha - RUTAS",
        description=f"🗡️ LA RUTA POR LA QUE DEBES IR ES: **{resultado}**",
        color=discord.Color.blue()
    )
    embed.set_footer(text="¡Usa este resultado con sabiduría, shinobi!, RECUERDA MIRAR EL MAPA")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)

@bot.command(name="familiaclan")
async def gacha_kenjutsu(ctx):
    import random
    import discord

    opcion = [
        "familia principal",
        "familia secundaria"
    ]

    random.shuffle(opcion)
    resultado = opcion[0]
    embed = discord.Embed(
        title="🎴 Resultado Gacha - FAMILIAS",
        description=f"🗡️ TU FAMILIA DE CLAN ES: **{resultado}**",
        color=discord.Color.blue()
    )
    embed.set_footer(text="¡Usa este resultado con sabiduría, shinobi!, recuerda que esto debes de tenerlo en cuenta para tu clan")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)

@bot.command(name="mangekyu")
async def gacha_kenjutsu(ctx):
    import random
    import discord

    opcion = [
        "【🔥】Bankai  【🔥】",
        "【👁️】Riser 【👁️】",
        "【⚡】Raion 【⚡】",
        "【☀️】Shindai 【☀️】",
        "【🍃】Satori【🍃】",
        "【🌌】Shiver【🌌】",
        "【🌸】Sarachia【🌸】",
        "NINGUNO",
        "NINGUNO.",
        "NINGUNO.."
    ]

    random.shuffle(opcion)
    resultado = opcion[0]
    embed = discord.Embed(
        title="🎴 Resultado Gacha - MANGEKYU SHARINGAN",
        description=f"🗡️ TU SHARINGAN PERSONAL ES: **{resultado}**",
        color=discord.Color.blue()
    )
    embed.set_footer(text="¡Usa este resultado con sabiduría, shinobi!, recuerda que esto debes de tenerlo en cuenta para tu clan")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)

#______________________RULETA ESPECIALIDADES_____________________________________
@bot.command(name="tener_especialidad")
async def gacha_kenjutsu(ctx):
    import random
    import discord

    opcion = [
        "【⛔️】NO【⛔️】",
        "【🔥】SI【🔥】"
    ]

    random.shuffle(opcion)
    resultado = opcion[0]
    embed = discord.Embed(
        title="🎴 Resultado Gacha - ¿TENDRAS ESPECIALIDAD?",
        description=f"🗡️ VAS A TENER ESPECIALIDAD EN ESTE MOMENTO?: **{resultado}**",
        color=discord.Color.blue()
    )
    embed.set_footer(text="¡Usa este resultado con sabiduría, shinobi!, RECUERDA TENERLO EN CUENTA A FUTURO")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)

@bot.command(name="especialidad")
async def gacha_kenjutsu(ctx):
    import random
    import discord

    opcion = [
        "【🗡️ 】Bukijutsu【🏹】",
        "【🧬 】Medicina【🫀】",
        "【📜 】Sellado【⛓️‍💥】",
        "【📃 】Invocacion【🐸】",
        "【👥 】Clones【👤】",
        "【🧠 】Genjutsu【🌀 ",
        "【🛡️ 】Barrera【🧱】",
        "【👀 】Sensorial【👃🏻】"
    ]

    random.shuffle(opcion)
    resultado = opcion[0]
    embed = discord.Embed(
        title="🎴 Resultado Gacha - ESPECIALIDADES",
        description=f"🗡️ LA ESPECIALIDAD QUE TENDRAS ES DE: **{resultado}**",
        color=discord.Color.blue()
    )
    embed.set_footer(text="¡Usa este resultado con sabiduría, shinobi!, recuerda que esto debes de tenerlo en para tus entrenamientos")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)

# ___________ACTUALIZAR ECONOMIA COMPLETA CADA DOMINGO______________________________
@bot.command(name="actualizareconomia")
@commands.has_any_role("【⛔️】ADMIN【🚫】", "【❌️】OWNER【❌️】", "【🥏】MODERADOR【🧶】")
async def actualizar_economia(ctx, aldea_objetivo: str = None):
    import json
    import os
    import random

    archivo_recursos = 'recursos_generales_aldeas.json'
    archivo_misiones = 'misiones_aldeas.json'
    archivo_armas = 'armas_aldeas.json'
    archivo_roles = {
        "genin": ["【🎓】Genin【🎓】"],
        "chunin": ["【🍁】Chunin【🍁】"],
        "jonin": ["【🥀】Jounin【🥀】"],
        "anbu": ["【🔗】Anbu【🔗】"]
    }
    rol_vendedor = "【⚔️ 】Vendedor de Armas【💰 】"

    if not os.path.exists(archivo_recursos) or not os.path.exists(archivo_misiones) or not os.path.exists(archivo_armas):
        await ctx.send("❌ Faltan archivos requeridos para ejecutar la actualización.")
        return

    with open(archivo_recursos, 'r', encoding='utf-8') as f:
        recursos = json.load(f)

    with open(archivo_misiones, 'r', encoding='utf-8') as f:
        misiones_aldeas = json.load(f)

    with open(archivo_armas, 'r', encoding='utf-8') as f:
        armas_data = json.load(f)

    if not aldea_objetivo or aldea_objetivo.lower() not in recursos:
        await ctx.send("❌ Debes especificar una aldea válida. Ejemplo: `!actualizareconomia konoha`")
        return

    aldea = aldea_objetivo.lower()
    datos = recursos[aldea]
    habitantes = datos.get("habitantes", 0)
    usos_restantes = datos.get("usos_productores_restantes", 4)
    usos_realizados = max(0, 4 - usos_restantes)
    produccion_pasiva = datos.get("produccion_pasiva", {})

    consumo_total = {
        "agua": 2 * habitantes,
        "comida": 4 * habitantes,
        "medicamentos": 1 * habitantes,
        "ropas": 2 * habitantes
    }

    enfermos_set = set()
    miembros_aldea = [m for m in ctx.guild.members if any(aldea in r.name.lower() for r in m.roles)]

    for recurso, cantidad in consumo_total.items():
        recursos[aldea][recurso] -= cantidad
        if recursos[aldea][recurso] < 0:
            faltante = abs(recursos[aldea][recurso])
            por_habitante = cantidad // habitantes if habitantes > 0 else 1
            cantidad_enfermos = (faltante + por_habitante - 1) // por_habitante

            seleccionables = [m for m in miembros_aldea if m not in enfermos_set]
            seleccionados = random.sample(seleccionables, min(cantidad_enfermos, len(seleccionables)))
            enfermos_set.update(seleccionados)

            recursos[aldea][recurso] = 0

    enfermos = list(enfermos_set)

    for recurso, cantidad in produccion_pasiva.items():
        recursos[aldea][recurso] += cantidad

    pago_productores = usos_realizados * 500
    misiones = misiones_aldeas.get(aldea, {}).get("misiones", {})
    pagos_misiones = {
        "genin": 750,
        "chunin": 1000,
        "jonin": 1500
    }
    total_pago_misiones = sum(misiones.get(rango, 0) * pagos_misiones[rango] for rango in pagos_misiones)

    rangos_aldea = {"genin": 0, "chunin": 0, "jonin": 0, "anbu": 0}
    vendedores_armas = 0
    for miembro in ctx.guild.members:
        if any(aldea in r.name.lower() for r in miembro.roles):
            for rango in rangos_aldea:
                if any(r.name in archivo_roles[rango] for r in miembro.roles):
                    rangos_aldea[rango] += 1
            if any(r.name == rol_vendedor for r in miembro.roles):
                vendedores_armas += 1

    max_productores = habitantes // 5

    armas_aldea = armas_data.get(aldea, {})
    resumen_armas = "\n".join([
        f"🗡️ ID {k} - {v['nombre']} | Cantidad: {v['cantidad']} | Fecha: {v['fecha_creacion']}"
        for k, v in armas_aldea.items()
    ]) or "⚠️ No hay armas registradas en esta aldea."

    resumen = f"""
╔══════════════════════════════════════════════╗
║          📊 RESUMEN ECONÓMICO - {aldea.capitalize()}          ║
╚══════════════════════════════════════════════╝

👥 Habitantes totales: {habitantes}
🎯 Máx. Productores permitidos: {max_productores}
🛒 Vendedores de Armas: {vendedores_armas}

📦 Consumo semanal aplicado:
  💧 Agua: {consumo_total['agua']}
  🍱 Comida: {consumo_total['comida']}
  💊 Medicamentos: {consumo_total['medicamentos']}
  👘 Ropas: {consumo_total['ropas']}

🛠️ Producción pasiva recibida:
  {json.dumps(produccion_pasiva, indent=2, ensure_ascii=False)}

💸 Pago a productores: ${pago_productores}
🎖️ Misiones realizadas: {misiones}
🪙 Pago total por misiones: ${total_pago_misiones}

🏷️ Rangos activos:
  🎓 Genin: {rangos_aldea['genin']}
  🍁 Chunin: {rangos_aldea['chunin']}
  🥀 Jounin: {rangos_aldea['jonin']}
  🔗 Anbu: {rangos_aldea['anbu']}

🔐 Inventario de armas:
{resumen_armas}

🤒 Habitantes enfermos esta semana:
{', '.join(m.display_name for m in enfermos) if enfermos else '✅ Nadie enfermó, todo en orden.'}
"""

    recursos[aldea]["usos_productores_restantes"] = 4
    recursos[aldea]["robos_almacen"] = 0
    recursos[aldea]["produccion_robada"] = 0
    recursos[aldea]["robos_productores"] = 0

    if aldea in misiones_aldeas:
        misiones_aldeas[aldea]["misiones"] = {
            "genin": 0,
            "chunin": 0,
            "jonin": 0
        }

    with open(archivo_recursos, 'w', encoding='utf-8') as f:
        json.dump(recursos, f, indent=2, ensure_ascii=False)

    with open(archivo_misiones, 'w', encoding='utf-8') as f:
        json.dump(misiones_aldeas, f, indent=2, ensure_ascii=False)

    await ctx.send(f"```{resumen}```")

# Reemplaza 'AQUI_VA_TU_TOKEN' con el token que guardaste
import os
bot.run(os.getenv("DISCORD_TOKEN"))



