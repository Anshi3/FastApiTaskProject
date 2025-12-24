from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from typing import Optional,List

app=FastAPI(title="Anshika Task Manager")

class Task(BaseModel):
    id:int
    title:str
    description:Optional[str]=None
    status:str="pending"
    
    
# In mem DB

fake_tasks_db = [
    {"id": 1, "title": "Learn FastAPI", "description": "Basics clear karne hain", "status": "completed"},
    {"id": 2, "title": "Build Project", "description": "End-to-end coding", "status": "pending"},
]

# Welcome message
@app.get("/")
def home():
    return {"message": "Anshika, you are on track! Server is running."}


# Get List all task with query params

@app.get("/tasks/ response_model=List[Task]")
async def read_tasks(status:Optional[str]=None,limit:int=10):
    results=fake_tasks_db
    if status:
        results = [task for task in fake_tasks_db if task["status"] == status]
    return results[:limit]

# GET: Get single task using Path Parameter (Q2)
@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    for task in fake_tasks_db:
        if task["id"] == task_id:
            return task    
        
    raise HTTPException(status_code=404, detail="Task not found")


# Post 
@app.post("/tasks")
async def create_task(new_task:Task):
    # check if id exists
    for task in fake_tasks_db:
        if task["id"]==new_task.id:
            raise HTTPException(status_code=400, detail="Task ID already exists")
        
    fake_tasks_db.append(new_task.model_dump())
    return {"message": "Task created successfully", "task": new_task}
    