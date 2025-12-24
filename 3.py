from fastapi import FastAPI,HTTPException,Depends
from pydantic import BaseModel
from typing import Optional,List
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime,timedelta


# Configurations
SECRET_KEY="anshika_ka_super_secret_key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Password Hashing Tool
pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
# CryptContext is used to manage password hashing algorithms securely, commonly with bcrypt in FastAPI applications.

# DB SETUP

SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"
engine=create_engine(SQLALCHEMY_DATABASE_URL,connect_args={"check_same_thread": False})
SessionLocal=sessionmaker(autocommit=False,autoflush=True,bind=engine)
Base=declarative_base()


# DB MOdel

class UserTable(Base):
    __tablename__="users"
    id=Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class TaskTable(Base):
    __tablename__="tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    # is_completed = Column(Boolean, default=False)
    owner_id = Column(Integer) # User se connect karne ke liye
    
# Tables create
Base.metadata.create_all(bind=engine)



# Pydantic Models
class UserCreate(BaseModel):
    username:str
    password:str

class TaskSchema(BaseModel):
    title:str
    description:Optional[str]=None
    # is_completed: bool = False
    
    class Config:
        from_attributes=True # SQLAlchemy object ko JSON mein badalne ke liye
        
class Token(BaseModel):
    access_token: str
    token_type: str
    

app=FastAPI(title="Anshika Task Manager")


# Dependency Injection-# Dependency: Ye har request ke liye naya DB session kholega aur kaam khatam hote hi band kar dega

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()


# AUTH FUNCTIONS
# This function generates a JWT access token by adding an expiration time and signing the payload with a secret key.
def create_access_token(data:dict):
    to_encode=data.copy()
    expire=datetime.utcnow()+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    
    
# Welcome message
@app.get("/")
def home():
    return {"message": "Anshika, you are on track! Server is running."}

# ROUTES

# Signup
@app.post("/signup")
def signup(user:UserCreate,db:Session=Depends(get_db)):
    hashed_pwd=pwd_context.hash(user.password)
    new_user=UserTable(username=user.username,hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    return {"message": "User created! Ab login karo."}


        
        
# Login JWT Authentication

@app.post("/login",response_model=Token)
def login(user_credentials:UserCreate,db:Session=Depends(get_db)):
    user=db.query(UserTable).filter(UserTable.username==user_credentials.username).first()
    if not user or not pwd_context.verify(user_credentials.password,user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    access_token=create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}




# 3. CREATE TASK (Abhi ye bina token ke chal raha hai, next step mein protect karenge)
@app.post("/tasks/")
def create_task(task: TaskSchema, db: Session = Depends(get_db)):
    new_task = TaskTable(title=task.title, description=task.description)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task
    