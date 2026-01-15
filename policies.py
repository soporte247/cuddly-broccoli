import re
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger("chatbot_policies")

# Patrones simples para detección rápida de solicitudes peligrosas.
# Esta lista es un punto de partida y debe ajustarse según uso.
DENY_PATTERNS = [
    (re.compile(r"\b(create|build|write)\s+(a\s+)?(malware|virus|trojan|worm)\b", re.I), "malware"),
    (re.compile(r"\b(ddos|denial\s*of\s*service)\b", re.I), "ddos"),
    (re.compile(r"\b(sql\s*injection|xss|cross[- ]site\s*scripting)\b", re.I), "vuln_term"),
    (re.compile(r"\b(bypass\s+authentication|crack\s+passwords|brute[- ]force)\b", re.I), "auth_bypass"),
    (re.compile(r"\b(exploit|remote\s+code\s+execution|rce)\b", re.I), "exploit"),
    (re.compile(r"\b(kill\s+someone|harm\s+someone|assassinat)\b", re.I), "violence"),
]

REPORTS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "reports.log")


def check_content_policy(text: str):
    """Comprueba el texto contra patrones locales.

    Retorna un dict: { 'flagged': bool, 'matches': [terms], 'category': str|null }
    """
    if not text:
        return {"flagged": False, "matches": [], "category": None}

    matches = []
    category = None
    for pattern, cat in DENY_PATTERNS:
        if pattern.search(text):
            matches.append(pattern.pattern)
            category = cat
    flagged = len(matches) > 0
    return {"flagged": flagged, "matches": matches, "category": category}


def save_report(username: str, message: str, reason: str = "user_report"):
    try:
        # append to log file in repo (for manual review)
        data = {"timestamp": datetime.utcnow().isoformat(), "user": username, "reason": reason, "message": message}
        path = os.path.abspath(REPORTS_FILE)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        logger.info(f"Reporte guardado en log: {reason} por {username}")
        return True
    except Exception as e:
        logger.exception(f"No se pudo guardar el reporte en log: {e}")
        return False
