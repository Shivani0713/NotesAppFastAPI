import os
from .db import Base
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from . import models, db, auth, schemas
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse,HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Depends, HTTPException, Form, status, File, UploadFile, Response

Base.metadata.create_all(bind =  db.engine)
app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR,"templates"))

origins = ["*"] 
app.add_middleware( CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"],)

@app.get("/logout")
def logout(response: Response, request: Request):
    response.delete_cookie(key="token")
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse("reg_login.html", {"request": request})

@app.post("/signup", response_class=HTMLResponse)
def signup(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), hash_password: str = Form(...), db: Session = Depends(db.get_db)):
    exist_user = db.query(models.User).filter(models.User.email == email).first()
    if exist_user:
        return templates.TemplateResponse("reg_login.html", {"request": request, "error": "Email already exists!"}, status_code=status.HTTP_400_BAD_REQUEST)
    if password != hash_password:
        return templates.TemplateResponse("reg_login.html", {"request": request, "error": "Passwords do not match!"}, status_code=status.HTTP_400_BAD_REQUEST)
    hashed_password = auth.hash_password(password)
    new_user = models.User(email=email, password=hashed_password, username=username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return templates.TemplateResponse("reg_login.html", {"request": request, "message": "Signup successful! Please login."})

@app.post("/login")
def login(email:str = Form(...), password: str = Form(...), db:Session = Depends(db.get_db)):
    exist_user = db.query(models.User).filter(models.User.email == email).first()
    if not exist_user or not auth.verify_password(password, exist_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token({"sub": exist_user.email})
    response = RedirectResponse(url="/notes/0", status_code=303)
    response.set_cookie("token",token)
    return response

@app.get("/notes/{notes_id}", response_class=HTMLResponse)
def get_notes_page(notes_id: int, request: Request, user=Depends(auth.get_current_user), db: Session = Depends(db.get_db)):
    all_notes = db.query(models.Note).filter(models.Note.user_id == user.id).all()

    if notes_id != 0:
        note = db.query(models.Note).filter(models.Note.user_id == user.id, models.Note.id == notes_id).first()
        if not note:
            note = {"id": 0, "title": "", "description": "", "image_path": ""}
    else:
        note = {"id": 0, "title": "", "description": "", "image_path": ""}

    return templates.TemplateResponse("index.html", {
        "request": request,
        "notes": all_notes,
        "note": note,
        "user": user
    })


@app.post("/new_note/{notes_id}/")
def add_or_update_note(
    request: Request,
    notes_id: int,
    title: str = Form(...),
    description: str = Form(...),
    file_data: UploadFile = File(None),
    db: Session = Depends(db.get_db)
):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        user_email = payload.get("sub")
        user = db.query(models.User).filter_by(email=user_email).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if notes_id  not in [0 ,'']:
            note = db.query(models.Note).filter(models.Note.id == int(notes_id), models.Note.user_id == user.id).first()
            if not note:
                raise HTTPException(status_code=404, detail="Note not found or unauthorized")
            note.title = title
            note.description = description

            if file_data and file_data.filename:
                image_dir = os.path.join(BASE_DIR, "static", "images")
                os.makedirs(image_dir, exist_ok=True)
                file_location = os.path.join(image_dir, file_data.filename)
                with open(file_location, "wb") as f:
                    f.write(file_data.file.read())
                note.image_path = f"static/images/{file_data.filename}"

            db.commit()
            db.refresh(note)

        else:
            note = models.Note(
                title=title,
                description=description,
                user_id=user.id,
                create_date=date.today()
            )
            if file_data and file_data.filename:
                image_dir = os.path.join(BASE_DIR, "static", "images")
                os.makedirs(image_dir, exist_ok=True)
                file_location = os.path.join(image_dir, file_data.filename)
                with open(file_location, "wb") as f:
                    f.write(file_data.file.read())
                note.image_path = f"static/images/{file_data.filename}"

            db.add(note)
            db.commit()
            db.refresh(note)

        return RedirectResponse(url="/notes/0/", status_code=303)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
  
@app.get("/del_notes/{notes_id}/", response_model=schemas.NoteDelete)
def delete_note(notes_id :int, user_id : Session = Depends(auth.get_current_user), db : Session = Depends(db.get_db)):
    notes_del  = db.query(models.Note).filter(models.Note.id == notes_id).first()
    db.delete(notes_del)
    db.commit()
    return RedirectResponse(url="/notes/0/", status_code=303)