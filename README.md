# LinkedIn Job Bot PRO

Bot de Telegram que busca empleos remotos en **LinkedIn, Indeed y Glassdoor**, analiza compatibilidad con **IA** y genera cartas de presentación.

## Características

- Búsqueda multi-portal sin navegador (JobSpy)
- Monitoreo automático configurable por usuario
- Análisis de compatibilidad con IA
- Generación de cartas de presentación
- Soporte para **ChatGPT, Gemini, Grok** y cualquier API compatible con OpenAI
- Despliegue en Railway 24/7

## Inicio rápido

```bash
git clone https://github.com/Zetapro41/linkedin_job_bot.git
cd linkedin_job_bot
python -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
# Edita .env con tu BOT_TOKEN y API de IA
python bot.py
```

## Documentación completa

**[GUIA.md](./GUIA.md)** — Guía paso a paso con instalación, APIs de IA, Railway y solución de problemas.

## Comandos del bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Registro e instrucciones |
| `/track [puesto]` | Agregar puesto a rastrear |
| `/buscar` | Búsqueda manual |
| `/location [país]` | Cambiar región |
| `/frecuencia [horas]` | Intervalo automático |
| `/status` | Ver configuración |

## APIs de IA soportadas

| Proveedor | Variable |
|-----------|----------|
| ChatGPT (OpenAI) | `OPENAI_API_KEY` |
| Gemini (Google) | `GEMINI_API_KEY` |
| Grok (xAI) | `XAI_API_KEY` |
| Venice AI | `VENICE_API_KEY` |
| Cualquier API OpenAI-compatible | `AI_API_BASE_URL` + `AI_API_KEY` |

Configura `AI_PROVIDER=auto` para usar la primera key disponible.