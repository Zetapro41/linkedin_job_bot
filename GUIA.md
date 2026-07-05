# Guía paso a paso — LinkedIn Job Bot PRO

Bot de Telegram que busca empleos remotos en **LinkedIn, Indeed y Glassdoor**, analiza compatibilidad con **IA** y genera cartas de presentación.

Repositorio: https://github.com/Zetapro41/linkedin_job_bot

---

## Tabla de contenidos

1. [Requisitos](#1-requisitos)
2. [Crear tu bot de Telegram](#2-crear-tu-bot-de-telegram)
3. [Obtener una API de IA](#3-obtener-una-api-de-ia)
4. [Instalar en tu PC](#4-instalar-en-tu-pc)
5. [Configurar el archivo .env](#5-configurar-el-archivo-env)
6. [Ejecutar el bot localmente](#6-ejecutar-el-bot-localmente)
7. [Usar el bot en Telegram](#7-usar-el-bot-en-telegram)
8. [Desplegar en Railway (24/7)](#8-desplegar-en-railway-247)
9. [Desplegar con GitHub automático](#9-desplegar-con-github-automático)
10. [Solución de problemas](#10-solución-de-problemas)

---

## 1. Requisitos

| Requisito | Versión mínima |
|-----------|----------------|
| Python | 3.11 o superior |
| Git | Cualquier versión reciente |
| Cuenta de Telegram | Para crear y usar el bot |
| API de IA (opcional) | ChatGPT, Gemini, Grok u otra |

**No necesitas Chrome ni Selenium.** El bot usa la librería JobSpy.

---

## 2. Crear tu bot de Telegram

Cada persona que instale el repo debe crear **su propio bot**. No uses el token de otra persona.

### Paso 2.1 — Abrir BotFather

1. Abre Telegram y busca **@BotFather**
2. Envía el comando:

```
/newbot
```

### Paso 2.2 — Nombrar el bot

1. BotFather pedirá un **nombre visible** (ej: `Mi Buscador de Empleo`)
2. Luego pedirá un **username** que termine en `bot` (ej: `mi_empleo_bot`)

### Paso 2.3 — Guardar el token

BotFather te dará un token como:

```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

Guárdalo. Lo usarás en el archivo `.env` como `BOT_TOKEN`.

### Paso 2.4 — Probar el enlace

Tu bot estará disponible en:

```
https://t.me/TU_USERNAME_BOT
```

---

## 3. Obtener una API de IA

La IA sirve para:
- Analizar compatibilidad de cada empleo (%)
- Generar cartas de presentación

**El bot funciona sin IA**, pero esas funciones mostrarán "No disponible".

Puedes usar **cualquiera** de estas APIs (o una compatible con OpenAI):

### Opción A — ChatGPT (OpenAI)

1. Entra a https://platform.openai.com/api-keys
2. Crea una API key
3. En `.env`:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-tu-key-aqui
OPENAI_MODEL=gpt-4o-mini
```

Modelos recomendados: `gpt-4o-mini` (económico), `gpt-4o` (más potente).

---

### Opción B — Gemini (Google)

1. Entra a https://aistudio.google.com/apikey
2. Crea una API key
3. En `.env`:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=tu-key-aqui
GEMINI_MODEL=gemini-2.0-flash
```

---

### Opción C — Grok (xAI)

1. Entra a https://console.x.ai/
2. Crea una API key
3. En `.env`:

```env
AI_PROVIDER=grok
XAI_API_KEY=tu-key-aqui
XAI_MODEL=grok-3-mini
```

---

### Opción D — Venice AI

1. Entra a https://venice.ai/settings/api
2. Crea una API key
3. En `.env`:

```env
AI_PROVIDER=venice
VENICE_API_KEY=tu-key-aqui
VENICE_MODEL=llama-3.3-70b
```

---

### Opción E — Cualquier API compatible con OpenAI

Funciona con proveedores que usen el formato estándar de chat completions:

- **DeepSeek** → `https://api.deepseek.com/v1`
- **OpenRouter** → `https://openrouter.ai/api/v1`
- **Mistral** → `https://api.mistral.ai/v1`
- **Ollama local** → `http://localhost:11434/v1`

En `.env`:

```env
AI_PROVIDER=custom
AI_API_BASE_URL=https://api.deepseek.com/v1
AI_API_KEY=tu-key-aqui
AI_MODEL=deepseek-chat
```

---

### Modo automático (recomendado)

Si pones `AI_PROVIDER=auto`, el bot usa la **primera API key** que encuentre en este orden:

1. OpenAI (ChatGPT)
2. Gemini
3. Grok
4. Venice
5. API personalizada

```env
AI_PROVIDER=auto
OPENAI_API_KEY=sk-...
```

Solo necesitas configurar **una** API.

---

## 4. Instalar en tu PC

### Paso 4.1 — Clonar el repositorio

**Windows (PowerShell):**

```powershell
git clone https://github.com/Zetapro41/linkedin_job_bot.git
cd linkedin_job_bot
```

**Linux / macOS:**

```bash
git clone https://github.com/Zetapro41/linkedin_job_bot.git
cd linkedin_job_bot
```

### Paso 4.2 — Crear entorno virtual

**Windows:**

```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 4.3 — Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 5. Configurar el archivo .env

### Paso 5.1 — Crear el archivo

**Windows:**

```powershell
copy .env.example .env
notepad .env
```

**Linux / macOS:**

```bash
cp .env.example .env
nano .env
```

### Paso 5.2 — Configuración mínima

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_PATH=linkedin_bot.db
AI_PROVIDER=auto
OPENAI_API_KEY=sk-tu-key-aqui
```

### Paso 5.3 — Configuración completa (ejemplo)

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_PATH=linkedin_bot.db
CHECK_INTERVAL_HOURS=12
LIMIT_RESULTS=25

AI_PROVIDER=gemini
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-2.0-flash
```

> **Importante:** Nunca subas el archivo `.env` a GitHub. Ya está en `.gitignore`.

---

## 6. Ejecutar el bot localmente

Con el entorno virtual activado:

```bash
python bot.py
```

Deberías ver en consola:

```
Bot de LinkedIn PRO iniciado. Presiona Ctrl+C para detener.
Monitoreo automático inteligente en segundo plano programado cada 30 minutos.
```

Abre Telegram, busca tu bot y envía `/start`.

Para detener el bot: `Ctrl + C` en la terminal.

---

## 7. Usar el bot en Telegram

### Primer uso

| Comando | Qué hace |
|---------|----------|
| `/start` | Te registra y muestra la ayuda |
| `/track Python Developer` | Agrega un puesto a rastrear |
| `/location Latin America` | Cambia la región de búsqueda |
| `/frecuencia 6` | Busca automáticamente cada 6 horas |
| `/buscar` | Búsqueda manual inmediata |
| `/status` | Muestra tu configuración |
| `/tracks` | Lista tus puestos rastreados |
| `/untrack 2` | Elimina el puesto con ID 2 |

### Ejemplo de flujo completo

```
/start
/track Data Analyst
/track Prompt Engineer
/location Spain
/frecuencia 8
/buscar
```

### Qué recibirás

Cada empleo llega con:
- Título, empresa, ubicación y portal
- Análisis de compatibilidad con IA (%)
- Botón **Ver Oferta** (enlace directo)
- Botón **Generar Carta** (carta de presentación con IA)

### Monitoreo automático

Sin hacer nada más, el bot:
- Revisa cada 30 minutos si te toca buscar
- Respeta tu frecuencia configurada (`/frecuencia`)
- Solo envía empleos **nuevos** (no repite los ya vistos)

---

## 8. Desplegar en Railway (24/7)

Para que el bot funcione con la PC apagada.

### Paso 8.1 — Crear cuenta en Railway

1. Entra a https://railway.app
2. Regístrate con GitHub

### Paso 8.2 — Desplegar desde GitHub

1. **New Project** → **Deploy from GitHub repo**
2. Selecciona `Zetapro41/linkedin_job_bot` (o tu fork)
3. Railway detectará Python automáticamente

### Paso 8.3 — Variables de entorno

En Railway → tu servicio → **Variables**, agrega:

| Variable | Valor |
|----------|-------|
| `BOT_TOKEN` | Tu token de @BotFather |
| `DATABASE_PATH` | `/data/linkedin_bot.db` |
| `AI_PROVIDER` | `auto` (o `openai`, `gemini`, `grok`) |
| `OPENAI_API_KEY` | Tu key (si usas ChatGPT) |
| `GEMINI_API_KEY` | Tu key (si usas Gemini) |
| `XAI_API_KEY` | Tu key (si usas Grok) |

### Paso 8.4 — Volumen persistente

1. Service → **Settings** → **Volumes**
2. **Add Volume** montado en `/data`
3. Esto guarda usuarios y empleos vistos aunque Railway reinicie

### Paso 8.5 — Verificar

En **Deployments** → **Logs**, busca:

```
Bot de LinkedIn PRO iniciado.
```

---

## 9. Desplegar con GitHub automático

Cada vez que hagas `git push`, Railway redeploya solo.

### Con Railway CLI (alternativa)

```powershell
npx @railway/cli login
.\deploy-railway.ps1
```

El script:
1. Vincula el proyecto local con Railway
2. Sube las variables de tu `.env`
3. Despliega el bot

### Actualizar el bot

```bash
git pull origin main
```

Si usas Railway con GitHub conectado, el redeploy es automático al hacer push.

---

## 10. Solución de problemas

### Error: `BOT_TOKEN no configurado`

- Verifica que `.env` existe y tiene `BOT_TOKEN=...`
- En Railway, revisa que la variable esté en **Variables**

### Error 409 de Telegram

```
Conflict: terminated by other getUpdates request
```

**Causa:** El mismo `BOT_TOKEN` corre en dos sitios (PC + Railway).

**Solución:** Detén una instancia. Solo una puede estar activa.

### `Compatibilidad: No disponible`

- No configuraste ninguna API de IA en `.env`
- Agrega al menos una: `OPENAI_API_KEY`, `GEMINI_API_KEY` o `XAI_API_KEY`

### Error HTTP 401 / 403 en IA

- API key incorrecta o expirada
- Verifica la key en el panel del proveedor
- Confirma que `AI_PROVIDER` coincide con la key que configuraste

### El bot no encuentra empleos

- Prueba `/buscar` manualmente
- Cambia la ubicación: `/location Worldwide`
- Agrega otro puesto: `/track Remote Developer`
- LinkedIn/Indeed pueden limitar resultados temporalmente

### Se pierden usuarios al reiniciar Railway

- Falta el volumen en `/data`
- Agrega Volume y `DATABASE_PATH=/data/linkedin_bot.db`

### `pip install` falla

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Resumen rápido

```text
1. git clone el repo
2. Crear bot en @BotFather → copiar BOT_TOKEN
3. Elegir API de IA (ChatGPT, Gemini, Grok u otra)
4. copy .env.example .env → pegar tokens
5. pip install -r requirements.txt
6. python bot.py
7. En Telegram: /start → /track → /buscar
```

---

## Licencia y uso

Este proyecto es de código abierto. Cada usuario:
- Crea su propio bot de Telegram
- Usa su propia API de IA
- Despliega en su PC o su cuenta de Railway

No compartas tokens ni archivos `.env` con nadie.