# =============================================================================
# gunicorn.conf.py – Production Gunicorn configuration for SafeSight AI
# Applied automatically when Gunicorn is started from the project root.
# render.yaml's startCommand overrides --bind and --workers via CLI flags.
# =============================================================================
import os
import multiprocessing

# Bind is set by Render via --bind "0.0.0.0:$PORT" in the startCommand.
# This file provides sensible defaults for local production testing:
bind = f"0.0.0.0:{os.getenv('PORT', os.getenv('API_PORT', '5000'))}"

# Workers: 1 on Render free/starter (RAM constrained).
# Formula for larger plans: (2 × CPU cores) + 1
workers = int(os.getenv("WEB_CONCURRENCY", 1))

# Threads per worker (good for I/O-bound Flask routes)
threads = int(os.getenv("GUNICORN_THREADS", 4))

# Worker class
worker_class = "gthread"

# Timeout (seconds) – generous for inference requests
timeout = 300
keepalive = 5

# Logging
accesslog = "-"   # stdout
errorlog  = "-"   # stderr
loglevel  = os.getenv("LOG_LEVEL", "info")

# Graceful shutdown
graceful_timeout = 30
