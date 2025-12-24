import time
import bcrypt  # Direct bcrypt use karenge error se bachne ke liye
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from fastapi import FastAPI, HTTPException, Depends, Request, status
from pydantic import BaseModel 
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

# --- 1. CONFIGS ---
SECRET_KEY = "197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3"
ALGORITHM = "HS256"
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

# --- 2. DB SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserTable(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)

Base.metadata.create_all(bind=engine)

# --- 3. MODELS ---
class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

app = FastAPI(title="Anshika Task Manager Final")

# --- 4. MIDDLEWARE ---
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    response.headers["X-Process-Time"] = str(duration)
    return response

# --- 5. HASHING HELPERS (Manual Bcrypt to avoid ValueError) ---
def hash_password(password: str):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- 6. DEPENDENCIES ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# --- 7. ROUTES ---

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(db: db_dependency, user_req: CreateUserRequest):
    # Manual hash call
    hashed_pwd = hash_password(user_req.password)
    new_user = UserTable(
        username=user_req.username,
        hashed_password=hashed_pwd,
        role=user_req.role
    )
    db.add(new_user)
    db.commit()
    return {"message": "User Created Successfully"}

@app.post("/auth/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = db.query(UserTable).filter(UserTable.username == form_data.username).first()
    
    # Manual verify call
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Invalid Credentials')
    
    token = jwt.encode(
        {'sub': user.username, 'id': user.id, 'role': user.role, 
         'exp': datetime.now(timezone.utc) + timedelta(minutes=20)},
        SECRET_KEY, algorithm=ALGORITHM
    )
    return {'access_token': token, 'token_type': 'bearer'}