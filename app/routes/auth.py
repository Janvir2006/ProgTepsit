from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.database import get_connection
from app.utils.security import hash_password, verify_password
from app.utils.email import send_verification_code
from app import templates
import random
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/")
def root():
    return RedirectResponse(url="/loginRegister")

@router.get("/loginRegister", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("loginRegister.html", {"request": request})

@router.post("/loginRegister")
def login_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(None)
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if email is None:  # Login
            query = "SELECT * FROM utenti WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            
            if user is None or not verify_password(user[3], password):
                return templates.TemplateResponse("loginRegister.html", 
                    {"request": request, "error": "Credenziali non valide"})

            request.session['user_id'] = user[0]
            request.session['username'] = user[1]
            request.session['role'] = user[4]

            role_redirects = {
                "cliente": "/user_dashboard",
                "dipendente": "/dipendente_dashboard",
                "admin": "/admin_dashboard"
            }

            if user[4] in role_redirects:
                return RedirectResponse(url=role_redirects[user[4]], status_code=303)
            
            return templates.TemplateResponse("loginRegister.html", 
                {"request": request, "error": "Ruolo non valido"})

        else:  # Register
            cursor.execute("SELECT * FROM utenti WHERE email = %s", (email,))
            if cursor.fetchone():
                return templates.TemplateResponse("loginRegister.html", 
                    {"request": request, "error": "Email già registrata"})

            cursor.execute("SELECT * FROM utenti WHERE username = %s", (username,))
            if cursor.fetchone():
                return templates.TemplateResponse("loginRegister.html", 
                    {"request": request, "error": "Username già esistente"})

            hashed_password = hash_password(password)
            cursor.execute(
                "INSERT INTO utenti (username, email, password, ruolo) VALUES (%s, %s, %s, %s)", 
                (username, email, hashed_password, 'cliente')
            )
            conn.commit()

            return templates.TemplateResponse("loginRegister.html", 
                {"request": request, "success": f"{username} registrato con successo"})

    except Exception as e:
        conn.rollback()
        return templates.TemplateResponse("loginRegister.html", 
            {"request": request, "error": f"Errore: {str(e)}"})
    finally:
        cursor.close()
        conn.close()

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/loginRegister")

@router.get("/inviaCodice", response_class=HTMLResponse)
def send_code_page(request: Request):
    return templates.TemplateResponse("inviaCodice.html", {"request": request})

@router.post("/inviaCodice")
def send_code(request: Request, email: str = Form(...)):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM utenti WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user is None:
            return templates.TemplateResponse("inviaCodice.html", 
                {"request": request, "error": "Email non trovata"})

        code = str(random.randint(100000, 999999))
        expiry = datetime.now() + timedelta(minutes=10)

        request.session['code'] = code
        request.session['expiry'] = expiry.isoformat()

        send_verification_code(email, code)
        return RedirectResponse("/cambiaPass", status_code=303)

    finally:
        cursor.close()
        conn.close()

@router.get("/cambiaPass", response_class=HTMLResponse)
def change_password_page(request: Request):
    return templates.TemplateResponse("cambiaPass.html", {"request": request})

@router.post("/cambiaPass")
def change_password(
    request: Request,
    email: str = Form(...),
    code: str = Form(...),
    new_password: str = Form(...)
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM utenti WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user is None:
            return templates.TemplateResponse("cambiaPass.html", 
                {"request": request, "error": "Email non trovata"})

        saved_code = request.session.get('code')
        expiry_str = request.session.get('expiry')

        if not saved_code or not expiry_str:
            return templates.TemplateResponse("cambiaPass.html", 
                {"request": request, "error": "Codice non inviato o sessione scaduta."})

        expiry = datetime.fromisoformat(expiry_str)

        if code != saved_code:
            return templates.TemplateResponse("cambiaPass.html", 
                {"request": request, "error": "Codice errato"})
        if datetime.now() > expiry:
            return templates.TemplateResponse("cambiaPass.html", 
                {"request": request, "error": "Il codice è scaduto"})

        hashed_password = hash_password(new_password)
        cursor.execute("UPDATE utenti SET password = %s WHERE email = %s", 
            (hashed_password, email))
        conn.commit()

        del request.session['code']
        del request.session['expiry']

        return templates.TemplateResponse("cambiaPass.html", 
            {"request": request, "success": "Password cambiata con successo"})

    finally:
        cursor.close()
        conn.close() 