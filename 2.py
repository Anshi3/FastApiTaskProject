from fastapi import FastAPI,HTTPException,Depends
from pydantic import BaseModel
from typing import Optional,List
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,Session

# DB SETUP

SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"
engine=create_engine(SQLALCHEMY_DATABASE_URL,connect_args={"check_same_thread": False})
SessionLocal=sessionmaker(autocommit=False,autoflush=True,bind=engine)
Base=declarative_base()


# DB MOdel

class TaskTable(Base):
    __tablename__="tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    is_completed = Column(Boolean, default=False)
    
# Tables create
Base.metadata.create_all(bind=engine)


class TaskSchema(BaseModel):
    title:str
    description:Optional[str]=None
    is_completed: bool = False
    
    class Config:
        from_attributes=True # SQLAlchemy object ko JSON mein badalne ke liye
    

app=FastAPI(title="Anshika Task Manager")


# Dependency Injection-# Dependency: Ye har request ke liye naya DB session kholega aur kaam khatam hote hi band kar dega

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

    
    
# Welcome message
@app.get("/")
def home():
    return {"message": "Anshika, you are on track! Server is running."}

# ROUTES

# Post 
@app.post("/tasks",response_model=TaskSchema)
def create_task(task: TaskSchema, db: Session = Depends(get_db)):
    db_task=TaskTable(
        title=task.title,
        description=task.description,
        is_completed=task.is_completed
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)# ID generate hone ke baad update karta hai
    return db_task
        
    
# Get List all task with query params

@app.get("/tasks/ response_model=List[TaskSchema]")
async def read_tasks(skip:int=0,limit:int=10,db:Session=Depends(get_db)):
    tasks = db.query(TaskTable).offset(skip).limit(limit).all()
    return tasks
   

# GET: Get single task using Path Parameter (Q2)
@app.get("/tasks/{task_id}", response_model=TaskSchema)
def read_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskTable).filter(TaskTable.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task nahi mila!")
    return task



    