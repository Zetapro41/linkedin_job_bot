import logging
import sys
import asyncio
import urllib.parse
import json
import re
from datetime import datetime, timezone
import requests

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from ai_client import chat_completion, resolve_ai_provider
from config import load_config
from database import Database

# Configuración de Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# JobSpy Imports
import pandas as pd
from jobspy import scrape_jobs

def scrape_all_boards(keyword, location="Worldwide", limit=10):
    """Realiza la búsqueda de empleo usando la librería python-jobspy en múltiples portales de forma independiente y segura."""
    logger.info(f"Iniciando scrapeo multi-portal para: '{keyword}' en '{location}' usando JobSpy...")
    
    portales = ["linkedin", "indeed", "glassdoor"]
    jobs = []
    
    for portal in portales:
        try:
            logger.info(f"Buscando en {portal}...")
            # Si la ubicación es 'Worldwide', Glassdoor e Indeed pueden fallar, así que dejamos el campo vacío para búsqueda global
            loc = location
            if location.lower() == "worldwide" and portal in ["glassdoor", "indeed"]:
                loc = ""
                
            jobs_df = scrape_jobs(
                site_name=[portal],
                search_term=keyword,
                location=loc,
                results_wanted=max(5, limit // 2),
                hours_old=72,
            )
            
            if jobs_df is not None and not jobs_df.empty:
                for _, row in jobs_df.iterrows():
                    title = str(row.get('title', '')).strip()
                    company = str(row.get('company', '')).strip()
                    loc_val = str(row.get('location', '')).strip()
                    link = str(row.get('job_url', '')).strip()
                    date_posted = str(row.get('date_posted', 'N/A')).strip()
                    desc = str(row.get('description', '')).strip()
                    site_name = str(row.get('site', portal)).strip().capitalize()
                    
                    if title and link:
                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": loc_val if loc_val else "Remoto",
                            "date_posted": date_posted,
                            "link": link,
                            "description": desc,
                            "site": site_name
                        })
        except Exception as e:
            logger.warning(f"No se pudieron obtener resultados del portal {portal} debido a un error: {e}")
            continue
            
    logger.info(f"Búsqueda finalizada. Total de ofertas combinadas: {len(jobs)}")
    return jobs

def analyze_job_with_ai(config, job_title, company, description=""):
    """Evalúa la compatibilidad de una vacante con el proveedor de IA configurado."""
    if not resolve_ai_provider(config):
        logger.warning("No hay API keys de IA configuradas en .env. Saltando análisis de IA.")
        return (
            "📊 *Compatibilidad:* No disponible\n"
            "💡 Configura una API en `.env` (ChatGPT, Gemini, Grok u otra compatible)."
        )

    max_desc_len = 1500
    trimmed_desc = description[:max_desc_len] + "..." if len(description) > max_desc_len else description

    user_profile = (
        "El candidato tiene conocimientos básicos de Inteligencia Artificial (diseño de Prompts, uso y automatización "
        "con herramientas de IA), diseño en Canva (diseño de plantillas, imágenes, piezas para redes sociales y "
        "presentaciones profesionales) y bases en programación general (Python básico, scripts, HTML/CSS)."
    )

    system_prompt = (
        "Eres un analista de talento especializado en empleo tecnológico y diseño. Tu tarea es evaluar la compatibilidad "
        "de una oferta de trabajo con el perfil del candidato. Debes ser realista y directo.\n\n"
        f"Perfil del Candidato:\n{user_profile}\n\n"
        "Devuelve tu respuesta EXACTAMENTE en este formato (usa markdown):\n"
        "🎯 *Compatibilidad:* [XX]%\n"
        "📝 *Resumen:* [Breve resumen de la vacante en 2 líneas enfatizando qué debe hacer el candidato y qué tecnologías requiere.]\n"
        "💡 *Veredicto:* [Una breve frase explicando por qué encaja o qué reto tendrá el candidato en este puesto.]"
    )

    user_message = (
        f"Oferta de Empleo:\n"
        f"Título: {job_title}\n"
        f"Empresa: {company}\n"
        f"Descripción: {trimmed_desc if trimmed_desc else 'No disponible'}"
    )

    content, error = chat_completion(config, system_prompt, user_message, temperature=0.3)
    if content:
        return content
    return f"📊 *Compatibilidad:* {error or 'Error en la consulta de IA.'}"

def generate_cover_letter_with_ai(config, job_title, company):
    """Genera una carta de presentación utilizando la API de IA configurada."""
    if not resolve_ai_provider(config):
        return (
            "⚠️ No hay API de IA configurada.\n"
            "Agrega una key en `.env`: ChatGPT, Gemini, Grok u otra API compatible."
        )

    user_profile = (
        "El candidato tiene conocimientos básicos de Inteligencia Artificial (Prompting efectivo, automatizaciones, "
        "interacción con LLMs), habilidades en diseño utilizando Canva (creación de plantillas, imágenes y material visual "
        "para marketing) y conocimientos fundamentales de programación (desarrollo de scripts sencillos en Python, bases "
        "de desarrollo web con HTML y CSS)."
    )

    system_prompt = (
        "Eres un redactor profesional de cartas de presentación laboral. Redacta una carta de presentación (cover letter) "
        f"en español que sea profesional, directa y moderna para postular al puesto de '{job_title}' en la empresa '{company}'.\n\n"
        f"Perfil del Candidato:\n{user_profile}\n\n"
        "Instrucciones de Redacción:\n"
        "1. Mantén la carta en unos 3 párrafos cortos (concisa pero impactante).\n"
        "2. Sonar motivado, honesto y muy profesional.\n"
        "3. Destaca cómo su combinación de Canva, herramientas de IA y programación básica le permite acelerar procesos "
        "y aportar valor visual y técnico de inmediato.\n"
        "4. No uses placeholders vacíos (como [Tu Nombre] o [Fecha]), inventa datos ficticios realistas si es indispensable, o simplemente deja la estructura lista para firmar."
    )

    content, error = chat_completion(
        config,
        system_prompt,
        f"Redactar carta para {job_title} en {company}.",
        temperature=0.7,
    )
    if content:
        return content
    return f"❌ {error or 'Error al generar la carta.'}"

# --- Manejadores de Comandos del Bot ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra al usuario y le presenta los comandos disponibles."""
    user = update.effective_user
    db: Database = context.bot_data["db"]
    
    db.register_user(user.id, user.username, user.first_name)
    user_data = db.get_user(user.id)
    tracks = db.get_tracks(user.id)
    
    track_list_str = "\n".join([f"• ID {t['id']}: `{t['keywords']}`" for t in tracks])
    
    welcome_text = (
        f"¡Hola {user.first_name}! 👋\n\n"
        f"Bienvenido a tu *LinkedIn & Multi-Portal Job Tracker Bot (Versión Pro)*.\n"
        f"Te ayudaré a monitorear vacantes 100% remotas automáticamente y analizarlas con Inteligencia Artificial.\n\n"
        f"📋 *Tu Configuración Actual:*\n"
        f"📍 Región/País: `{user_data['location']}`\n"
        f"⏱️ Frecuencia automática: `Cada {user_data['check_interval_hours']} horas`\n\n"
        f"🔍 *Puestos que estás rastreando actualmente:*\n"
        f"{track_list_str if track_list_str else '• Ninguno (Agrega uno con /track)'}\n\n"
        f"💻 *Comandos Pro:*\n"
        f"🔹 `/track [puesto]` - Agrega un puesto de trabajo a tu lista de rastreo.\n"
        f"🔹 `/tracks` - Muestra tu lista de puestos rastreados.\n"
        f"🔹 `/untrack [id]` - Deja de rastrear un puesto usando su ID.\n"
        f"🔹 `/location [país]` - Cambia el país o región del monitoreo automático.\n"
        f"🔹 `/frecuencia [horas]` - Cambia la frecuencia del monitoreo automático (1-24h).\n"
        f"🔹 `/buscar` - Realiza una búsqueda manual de todos tus puestos ahora.\n"
        f"🔹 `/status` - Muestra tu configuración actual de monitoreo.\n\n"
        f"¡Usa el menú de botones persistentes abajo para controlar el bot rápidamente!"
    )
    
    # Crear teclado con botones persistentes
    keyboard = [
        ["/buscar", "/status"],
        ["/tracks", "/track"],
        ["/untrack", "/location"],
        ["/frecuencia", "/start"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el estado de la configuración actual."""
    user_id = update.effective_user.id
    db: Database = context.bot_data["db"]
    user_data = db.get_user(user_id)
    
    if not user_data:
        await update.message.reply_text("Por favor, inicia con el comando /start primero.")
        return
        
    tracks = db.get_tracks(user_id)
    track_list_str = "\n".join([f"• ID {t['id']}: `{t['keywords']}`" for t in tracks])
    
    status_text = (
        f"⚙️ *Configuración de Monitoreo Actual (Pro):*\n\n"
        f"📍 *Región / País:* `{user_data['location']}`\n"
        f"⏱️ *Frecuencia de monitoreo:* `Cada {user_data['check_interval_hours']} horas`\n"
        f"📅 *Último chequeo:* `{user_data['last_search_at'] if user_data['last_search_at'] else 'Nunca'}`\n\n"
        f"🔍 *Puestos en tu lista de rastreo:*\n"
        f"{track_list_str if track_list_str else '• Ninguno (Usa /track para agregar)'}"
    )
    await update.message.reply_text(status_text, parse_mode="Markdown")

async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Agrega un nuevo puesto a rastrear."""
    user_id = update.effective_user.id
    db: Database = context.bot_data["db"]
    
    keywords = " ".join(context.args).strip()
    if not keywords:
        await update.message.reply_text("Uso correcto: `/track [nombre del puesto]`\nEjemplo: `/track Prompt Engineer`", parse_mode="Markdown")
        return
        
    db.add_track(user_id, keywords)
    await update.message.reply_text(f"✅ Puesto agregado a tu lista: `{keywords}`.\nEl bot ahora buscará ofertas para este puesto.", parse_mode="Markdown")

async def untrack_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Elimina un puesto de la lista de rastreo."""
    user_id = update.effective_user.id
    db: Database = context.bot_data["db"]
    
    if not context.args:
        await update.message.reply_text("Uso correcto: `/untrack [ID del puesto]`\nPara ver tus IDs de puestos, usa el botón o comando `/tracks`.", parse_mode="Markdown")
        return
        
    try:
        track_id = int(context.args[0])
        success = db.remove_track(user_id, track_id)
        if success:
            await update.message.reply_text(f"✅ Se ha dejado de rastrear el puesto con ID `{track_id}`.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ No se encontró ningún puesto con ID `{track_id}` en tu cuenta.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("El ID debe ser un número entero.", parse_mode="Markdown")

async def tracks_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra la lista de puestos rastreados."""
    user_id = update.effective_user.id
    db: Database = context.bot_data["db"]
    tracks = db.get_tracks(user_id)
    
    if not tracks:
        await update.message.reply_text("No tienes ningún puesto en tu lista de rastreo. Agrega uno enviando `/track [puesto]`.", parse_mode="Markdown")
        return
        
    track_list_str = "\n".join([f"📌 *ID {t['id']}*: `{t['keywords']}`" for t in tracks])
    await update.message.reply_text(f"🔍 *Tus puestos rastreados:*\n\n{track_list_str}\n\nSi deseas eliminar alguno de ellos, escribe:\n`/untrack [ID]`", parse_mode="Markdown")

async def location_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cambia la ubicación global de búsqueda."""
    user_id = update.effective_user.id
    db: Database = context.bot_data["db"]
    
    loc = " ".join(context.args).strip()
    if not loc:
        await update.message.reply_text("Uso correcto: `/location [país o región]`\nEjemplo: `/location Worldwide` o `/location Spain`", parse_mode="Markdown")
        return
        
    db.update_user_location(user_id, loc)
    await update.message.reply_text(f"✅ Ubicación de búsqueda actualizada a: `{loc}`", parse_mode="Markdown")

async def frecuencia_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cambia la frecuencia de búsqueda automática."""
    user_id = update.effective_user.id
    db: Database = context.bot_data["db"]
    
    if not context.args:
        await update.message.reply_text("Uso correcto: `/frecuencia [horas]`\nEjemplo: `/frecuencia 6` (para escanear cada 6 horas)", parse_mode="Markdown")
        return
        
    try:
        hours = int(context.args[0])
        if hours < 1 or hours > 24:
            await update.message.reply_text("La frecuencia debe estar entre 1 y 24 horas.")
            return
            
        db.update_user_frequency(user_id, hours)
        await update.message.reply_text(f"✅ Monitoreo automático configurado: `Cada {hours} horas`.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("Por favor, ingresa un número entero válido para las horas.")

async def buscar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Realiza una búsqueda manual inmediata de todos los puestos rastreados."""
    user_id = update.effective_user.id
    db: Database = context.bot_data["db"]
    config = context.bot_data["config"]
    user_data = db.get_user(user_id)
    
    if not user_data:
        db.register_user(user_id, update.effective_user.username, update.effective_user.first_name)
        user_data = db.get_user(user_id)
        
    tracks = db.get_tracks(user_id)
    if not tracks:
        await update.message.reply_text("No tienes ningún puesto en tu lista de monitoreo. Agrega uno con `/track [puesto]` para poder buscar.")
        return

    await update.message.reply_text(f"Iniciando búsqueda multi-portal para tus {len(tracks)} puestos en `{user_data['location']}`... Esto puede tomar cerca de un minuto. 🔍")

    # Almacenaremos los resultados temporalmente en memoria de sesión de Telegram
    # para poder generar cartas de presentación (cover letters) dinámicamente si pulsan el botón
    context.user_data["last_searched_jobs"] = []
    
    all_found_jobs = []
    for track in tracks:
        puesto = track["keywords"]
        # Realizamos scraping sin navegador (ligero)
        jobs = await asyncio.to_thread(scrape_all_boards, puesto, user_data["location"], 5)
        all_found_jobs.extend(jobs)
        
    if not all_found_jobs:
        await update.message.reply_text("No se encontraron nuevas ofertas en este momento. Intenta de nuevo más tarde.")
        return

    # Limitar para no saturar al usuario en una búsqueda manual
    all_found_jobs = all_found_jobs[:10]
    context.user_data["last_searched_jobs"] = all_found_jobs
    db.update_last_search_time(user_id)

    await update.message.reply_text(f"Encontrados {len(all_found_jobs)} ofertas recientes. Analizándolas con Inteligencia Artificial... 🤖")

    for index, job in enumerate(all_found_jobs):
        is_new = not db.is_job_seen(job["link"])
        db.mark_job_seen(job["link"], user_id)
        
        # Realizar análisis de compatibilidad por IA en un hilo secundario
        ai_analysis = await asyncio.to_thread(
            analyze_job_with_ai, 
            config, 
            job["title"], 
            job["company"], 
            job["description"]
        )
        
        tag_nuevo = "🆕 " if is_new else ""
        msg = (
            f"{tag_nuevo}💼 *{job['title']}*\n"
            f"🏢 *Empresa:* {job['company']}\n"
            f"📍 *Ubicación:* {job['location']}\n"
            f"📡 *Portal:* {job['site']}\n"
            f"📅 *Publicado:* {job['date_posted']}\n\n"
            f"{ai_analysis}"
        )
        
        # Crear botones interactivos Inline
        keyboard = [
            [
                InlineKeyboardButton("🔗 Ver Oferta", url=job["link"]),
                InlineKeyboardButton("📝 Generar Carta", callback_data=f"cover_letter_{index}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)
        await asyncio.sleep(0.5)

    await update.message.reply_text("Búsqueda completada. Si deseas que te redacte una carta de presentación para alguna vacante, pulsa su respectivo botón.")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja las interacciones con los botones inline de las tarjetas de empleo."""
    query = update.callback_query
    await query.answer()
    
    config = context.bot_data["config"]
    data = query.data
    
    if data.startswith("cover_letter_"):
        index = int(data.split("_")[-1])
        jobs = context.user_data.get("last_searched_jobs", [])
        
        if index >= len(jobs):
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("⚠️ No se pudieron recuperar los detalles de esta vacante. Por favor, realiza otra búsqueda con el botón '🔍 Buscar Ahora'.")
            return
            
        job = jobs[index]
        await query.message.reply_text(f"✍️ Redactando carta de presentación personalizada para `{job['title']}` en `{job['company']}` usando IA... espera por favor...")
        
        # Generar cover letter con IA en hilo secundario
        cover_letter = await asyncio.to_thread(generate_cover_letter_with_ai, config, job["title"], job["company"])
        
        await query.message.reply_text(
            f"📝 *Carta de Presentación Generada:*\n\n{cover_letter}",
            parse_mode="Markdown"
        )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Procesa las interacciones desde el teclado de menú persistente."""
    text = update.message.text
    if text == "🔍 Buscar Ahora":
        await buscar_command(update, context)
    elif text == "⚙️ Ver Estado":
        await status(update, context)
    elif text == "📋 Mis Puestos Rastreados":
        await tracks_list_command(update, context)
    elif text == "💻 Comandos PRO":
        comandos_pro_text = (
            "💻 *Comandos Avanzados (PRO):*\n\n"
            "Escribe estos comandos directamente en el chat para configurar tu bot:\n\n"
            "📍 *Ubicación de búsqueda:*\n"
            "🔹 `/location [país]` - Cambia el país o región de búsqueda.\n"
            "Ejemplo: `/location Spain` o `/location Worldwide`\n\n"
            "⏱️ *Frecuencia de monitoreo:*\n"
            "🔹 `/frecuencia [horas]` - Ajusta cada cuánto tiempo el bot busca ofertas automáticamente.\n"
            "Ejemplo: `/frecuencia 6`\n\n"
            "🔍 *Rastreo de puestos:*\n"
            "🔹 `/track [puesto]` - Agrega un nuevo puesto a tu lista de monitoreo.\n"
            "Ejemplo: `/track Prompt Engineer`\n"
            "🔹 `/untrack [ID]` - Deja de rastrear un puesto usando su ID.\n"
            "Ejemplo: `/untrack 2`"
        )
        await update.message.reply_text(comandos_pro_text, parse_mode="Markdown")
    elif text == "ℹ️ Ayuda":
        await start(update, context)
    else:
        await update.message.reply_text("Utiliza el menú de botones o los comandos válidos para interactuar conmigo.")

# --- Tareas Automáticas en Segundo Plano (Cron) ---

async def check_jobs_automatic_scheduler(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Escanea periódicamente empleos en segundo plano respetando las horas y frecuencias individuales de cada usuario."""
    db: Database = context.bot_data["db"]
    config = context.bot_data["config"]
    users = db.get_all_users()
    
    logger.info("Iniciando escaneo automático programado...")
    
    for u in users:
        telegram_id = u["telegram_id"]
        location = u["location"]
        interval = u["check_interval_hours"]
        last_search_str = u["last_search_at"]
        
        # Evaluar si ha pasado suficiente tiempo para este usuario individual
        should_search = True
        if last_search_str:
            try:
                last_search = datetime.fromisoformat(last_search_str)
                diff = datetime.now(timezone.utc) - last_search
                hours_passed = diff.total_seconds() / 3600
                if hours_passed < interval:
                    should_search = False
            except Exception as e:
                logger.error(f"Error parseando fecha de búsqueda: {e}")
                
        if not should_search:
            continue
            
        tracks = db.get_tracks(telegram_id)
        if not tracks:
            continue
            
        logger.info(f"Escaneando en segundo plano para el usuario {telegram_id} ({len(tracks)} puestos)...")
        db.update_last_search_time(telegram_id)
        
        # Almacenar en una lista de sesión simulada en bot_data por si interactúa más tarde
        # (Aunque los callbacks interactivos prefieren leer de context.user_data, en el automático
        # enviamos una carta de presentación directa o informamos del botón. Para simplificar,
        # guardamos los últimos trabajos del automático en el user_data del usuario)
        user_jobs_memory = []
        
        for t in tracks:
            puesto = t["keywords"]
            jobs = await asyncio.to_thread(scrape_all_boards, puesto, location, 5)
            
            # Filtrar solo los nuevos
            new_jobs = [j for j in jobs if not db.is_job_seen(j["link"])]
            
            for job in new_jobs:
                db.mark_job_seen(job["link"], telegram_id)
                user_jobs_memory.append(job)
                
                # Análisis de compatibilidad con IA
                ai_analysis = await asyncio.to_thread(
                    analyze_job_with_ai, 
                    config, 
                    job["title"], 
                    job["company"], 
                    job["description"]
                )
                
                msg = (
                    f"🆕 💼 *¡Nuevo Empleo Encontrado!*\n\n"
                    f"📌 *{job['title']}*\n"
                    f"🏢 *Empresa:* {job['company']}\n"
                    f"📍 *Ubicación:* {job['location']}\n"
                    f"📡 *Portal:* {job['site']}\n"
                    f"📅 *Publicado:* {job['date_posted']}\n\n"
                    f"{ai_analysis}"
                )
                
                # Asignamos un índice en la memoria del usuario por si desea generar cover letter
                job_idx = len(user_jobs_memory) - 1
                
                keyboard = [
                    [
                        InlineKeyboardButton("🔗 Ver Oferta", url=job["link"]),
                        InlineKeyboardButton("📝 Generar Carta", callback_data=f"cover_letter_auto_{job_idx}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                try:
                    await context.bot.send_message(chat_id=telegram_id, text=msg, parse_mode="Markdown", reply_markup=reply_markup)
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error notificando al usuario {telegram_id}: {e}")
                    
        # Guardar en memoria de sesión de este usuario para permitir generar cartas
        # Para que funcione con los jobs automáticos, interceptamos el callback 'cover_letter_auto_'
        context.application.user_data[telegram_id]["last_searched_jobs"] = user_jobs_memory

async def handle_callback_query_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja interacciones de cartas de presentación generadas por búsquedas automáticas."""
    query = update.callback_query
    await query.answer()
    
    config = context.bot_data["config"]
    data = query.data
    
    if data.startswith("cover_letter_auto_"):
        index = int(data.split("_")[-1])
        jobs = context.user_data.get("last_searched_jobs", [])
        
        if index >= len(jobs):
            await query.message.reply_text("⚠️ Oferta antigua. Por favor, haz una búsqueda manual pulsando '🔍 Buscar Ahora' para generar cartas nuevas.")
            return
            
        job = jobs[index]
        await query.message.reply_text(f"✍️ Redactando carta de presentación personalizada para `{job['title']}` en `{job['company']}` usando IA... espera por favor...")
        
        cover_letter = await asyncio.to_thread(generate_cover_letter_with_ai, config, job["title"], job["company"])
        await query.message.reply_text(
            f"📝 *Carta de Presentación Generada:*\n\n{cover_letter}",
            parse_mode="Markdown"
        )

# --- Inicialización y Registro de Handlers ---

def main() -> None:
    config = load_config()
    if not config.bot_token:
        logger.error("BOT_TOKEN no configurado en el archivo .env. Agrega el token de tu bot de Telegram.")
        sys.exit(1)

    db = Database(config.database_path)

    # Inicializar la aplicación de Telegram
    application = Application.builder().token(config.bot_token).build()

    # Pasar datos globales al bot
    application.bot_data["db"] = db
    application.bot_data["config"] = config

    # Registrar comandos del bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("track", track_command))
    application.add_handler(CommandHandler("untrack", untrack_command))
    application.add_handler(CommandHandler("tracks", tracks_list_command))
    application.add_handler(CommandHandler("location", location_command))
    application.add_handler(CommandHandler("frecuencia", frecuencia_command))
    application.add_handler(CommandHandler("buscar", buscar_command))
    
    # Manejar clics de cartas de presentación
    application.add_handler(CallbackQueryHandler(handle_callback_query, pattern="^cover_letter_\\d+$"))
    application.add_handler(CallbackQueryHandler(handle_callback_query_auto, pattern="^cover_letter_auto_\\d+$"))

    # Manejar clics de botones del menú inferior (Texto normal)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Configurar el cron automático: revisa cada 30 minutos (1800 segundos) quién necesita búsqueda
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(
            check_jobs_automatic_scheduler,
            interval=1800,
            first=30,
            name="check_jobs_scheduler_pro"
        )
        logger.info("Monitoreo automático inteligente en segundo plano programado cada 30 minutos.")

    # Iniciar el bot en modo polling
    logger.info("Bot de LinkedIn PRO iniciado. Presiona Ctrl+C para detener.")
    application.run_polling()

if __name__ == "__main__":
    main()