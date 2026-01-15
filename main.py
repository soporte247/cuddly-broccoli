import os
import time
import logging
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, create_engine, Session, select
from passlib.context import CryptContext
from jose import JWTError, jwt

import openai
import json
from .policies import check_content_policy, save_report, REPORTS_FILE

ADMIN_USERS = [u.strip() for u in os.getenv("ADMIN_USERS", "admin").split(",") if u.strip()]

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})

app = FastAPI(title="Chatbot técnico - backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("chatbot_backend")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    hashed_password: str


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user: str
    reason: Optional[str]
    message: str
    category: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Token(BaseModel):
    access_token: str
    token_type: str


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user(username: str):
    with Session(engine) as session:
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()
        return user


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.post("/auth/register", status_code=201)
def register(username: str, password: str):
    if get_user(username):
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    user = User(username=username, hashed_password=get_password_hash(password))
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
    logger.info(f"Usuario creado: {username}")
    return {"msg": "Usuario creado"}


@app.post("/auth/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"Token generado para: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


class ChatIn(BaseModel):
    message: str


# Simple in-memory rate limiter per username
rate_limits = {}


def is_rate_limited(username: str) -> bool:
    now = time.time()
    window = RATE_LIMIT_WINDOW
    max_req = RATE_LIMIT_MAX
    times: List[float] = rate_limits.get(username, [])
    # keep timestamps within window
    times = [t for t in times if now - t < window]
    if len(times) >= max_req:
        rate_limits[username] = times
        return True
    times.append(now)
    rate_limits[username] = times
    return False


def save_message(username: str, role: str, content: str):
    with Session(engine) as session:
        msg = Message(username=username, role=role, content=content)
        session.add(msg)
        session.commit()


def save_report_db(username: str, message: str, reason: str = "user_report", category: Optional[str] = None):
    try:
        with Session(engine) as session:
            rpt = Report(user=username, reason=reason, message=message, category=category)
            session.add(rpt)
            session.commit()
        logger.info(f"Reporte guardado en DB: {reason} por {username}")
        return True
    except Exception as e:
        logger.exception(f"No se pudo guardar el reporte en DB: {e}")
        return False


@app.post("/chat")
def chat(payload: ChatIn, current_user=Depends(get_current_user)):
    username = current_user.username
    if is_rate_limited(username):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    user_text = payload.message
    save_message(username, "user", user_text)

    # Comprobación local rápida (denylist)
    local = check_content_policy(user_text)
    if local.get("flagged"):
        logger.warning(f"Mensaje localmente bloqueado ({local.get('category')}) por: {username}")
        raise HTTPException(status_code=403, detail="Contenido prohibido por las políticas de moderación (local)")

    # Moderación básica usando la API de OpenAI (si está disponible)
    if openai.api_key:
        try:
            mod = openai.Moderation.create(model="omni-moderation-latest", input=user_text)
            results = mod.get("results") or []
            if results and results[0].get("flagged"):
                logger.warning(f"Mensaje moderado (bloqueado) por: {username}")
                raise HTTPException(status_code=403, detail="Contenido prohibido por las políticas de moderación")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error en moderación: {e}")

    system_prompt = (
        "Eres un asistente técnico que responde en español a profesionales de programación y ciberseguridad. "
        "Proporciona explicaciones precisas, ejemplos de código cuando apliquen y advertencias de seguridad cuando sea necesario. "
        "No des instrucciones para actividades ilegales o dañinas."
    )

    try:
        resp = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            max_tokens=800,
        )
        text = resp["choices"][0]["message"]["content"]
    except Exception as e:
        logger.exception(f"Error en OpenAI: {e}")
        raise HTTPException(status_code=500, detail=f"Error en OpenAI: {e}")

    # Comprobación local de la respuesta del asistente
    assistant_check = check_content_policy(text)
    if assistant_check.get("flagged"):
        cat = assistant_check.get('category')
        logger.warning(f"Respuesta bloqueada por política local (categoria: {cat}) para {username}")
        # Guardar incidente en log y en DB, devolver mensaje genérico
        save_report(username, text, reason=f"assistant_blocked:{cat}")
        save_report_db(username, text, reason=f"assistant_blocked:{cat}", category=cat)
        return {"reply": "La respuesta ha sido bloqueada por las políticas de seguridad."}

    save_message(username, "assistant", text)
    logger.info(f"Respuesta enviada a {username} ({len(text)} chars)")
    return {"reply": text}


@app.get("/history")
def get_history(current_user=Depends(get_current_user), limit: int = 100):
    username = current_user.username
    with Session(engine) as session:
        statement = select(Message).where(Message.username == username).order_by(Message.timestamp.desc()).limit(limit)
        msgs = session.exec(statement).all()
        # return in chronological order
        msgs = list(reversed(msgs))
        return [{"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()} for m in msgs]


@app.post("/history/clear")
def clear_history(current_user=Depends(get_current_user)):
    username = current_user.username
    with Session(engine) as session:
        statement = select(Message).where(Message.username == username)
        msgs = session.exec(statement).all()
        for m in msgs:
            session.delete(m)
        session.commit()
    logger.info(f"Historial borrado por {username}")
    return {"msg": "Historial borrado"}


@app.post("/report")
def report(payload: dict, current_user=Depends(get_current_user)):
    """Endpoint para que usuarios reporten mensajes problemáticos.

    Payload esperado: { "message": "...", "reason": "opcional" }
    """
    username = current_user.username
    message = payload.get("message", "")
    reason = payload.get("reason", "user_report")
    ok = save_report(username, message, reason)
    if not ok:
        raise HTTPException(status_code=500, detail="No se pudo guardar el reporte")
    return {"msg": "Reporte recibido"}


@app.get("/auth/me")
def me(current_user=Depends(get_current_user)):
    return {"username": current_user.username, "is_admin": current_user.username in ADMIN_USERS}


@app.get("/admin/reports")
def admin_reports(current_user=Depends(get_current_user), page: int = 1, size: int = 20, q: Optional[str] = None, user: Optional[str] = None, reason: Optional[str] = None, category: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    if current_user.username not in ADMIN_USERS:
        raise HTTPException(status_code=403, detail="Acceso de administrador requerido")
    try:
        with Session(engine) as session:
            statement = select(Report)
            # filters
            if q:
                statement = statement.where(Report.message.contains(q))
            if user:
                statement = statement.where(Report.user == user)
            if reason:
                statement = statement.where(Report.reason == reason)
            if category:
                statement = statement.where(Report.category == category)
            if start_date:
                try:
                    sd = datetime.fromisoformat(start_date)
                    statement = statement.where(Report.timestamp >= sd)
                except Exception:
                    pass
            if end_date:
                try:
                    ed = datetime.fromisoformat(end_date)
                    statement = statement.where(Report.timestamp <= ed)
                except Exception:
                    pass

            total = session.exec(select([Report.id]).where(statement._whereclause)).count() if statement._whereclause is not None else session.exec(select([Report.id])).count()
            # ordering and pagination
            statement = statement.order_by(Report.timestamp.desc()).offset((page-1)*size).limit(size)
            results = session.exec(statement).all()
            items = [{"id": r.id, "user": r.user, "reason": r.reason, "message": r.message, "category": r.category, "timestamp": r.timestamp.isoformat()} for r in results]
            return {"page": page, "size": size, "total": total, "items": items}
    except Exception as e:
        logger.exception(f"Error consultando reportes en BD: {e}")
        # fallback: read file
        try:
            path = REPORTS_FILE
            entries = []
            if not os.path.exists(path):
                return {"page": page, "size": size, "total": 0, "items": []}
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        continue
            # simple paging on file results
            total = len(entries)
            start = (page-1)*size
            items = entries[start:start+size]
            return {"page": page, "size": size, "total": total, "items": items}
        except Exception as e2:
            logger.exception(f"Error leyendo reportes fallback: {e2}")
            raise HTTPException(status_code=500, detail="No se pueden leer los reportes")


@app.post("/admin/reports/clear")
def admin_reports_clear(current_user=Depends(get_current_user)):
    if current_user.username not in ADMIN_USERS:
        raise HTTPException(status_code=403, detail="Acceso de administrador requerido")
    try:
        # clear DB table
        with Session(engine) as session:
            statement = select(Report)
            rows = session.exec(statement).all()
            for r in rows:
                session.delete(r)
            session.commit()
        # clear file
        path = REPORTS_FILE
        open(path, "w", encoding="utf-8").close()
        logger.info(f"Reportes limpiados por {current_user.username}")
        return {"msg": "Reportes eliminados"}
    except Exception as e:
        logger.exception(f"Error limpiando reportes: {e}")
        raise HTTPException(status_code=500, detail="No se pudieron borrar los reportes")
