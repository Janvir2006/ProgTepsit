import mysql.connector
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime, timedelta


app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="ciao")
template = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def connessione():
    
    conn = mysql.connector.connect(
        
        host='192.168.3.92',
        user='admquintaainfo',
        password='admquintaainfo',
        database='supermercato'
        
        
    )
    
    return conn
    


def PassHash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def confrontoPass(DbPass, InputPass):
    return DbPass == PassHash(InputPass)

def invia_email(destinatario, codice):
    sender_email = "patadmpatberna@gmail.com"
    password = "rmem vklz zcrp lxsy"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    subject = "Codice di verifica per cambio password"
    body = f"Il tuo codice di verifica per cambiare la password è: {codice}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = destinatario
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, destinatario, text)
        server.quit()
    except Exception as e:
        print(f"Errore nell'invio dell'email: {e}")

@app.get("/")
def root():
    return RedirectResponse(url="/loginRegister")

"""
@app.get("/login", response_class=HTMLResponse)
def loginPage(request: Request):
    return template.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def RegPage(request: Request):
    return template.TemplateResponse("register.html", {"request": request})
"""

@app.get("/inviaCodice", response_class=HTMLResponse)
def IcPage(request: Request):
    return template.TemplateResponse("inviaCodice.html", {"request": request})

@app.get("/cambiaPass", response_class=HTMLResponse)
def CpPage(request: Request):
    return template.TemplateResponse("cambiaPass.html", {"request": request})

@app.get("/admin_dashboard", response_class=HTMLResponse)
def Dash_Page(request: Request):
    return template.TemplateResponse("admin_dashboard.html", {"request": request})



@app.get("/loginRegister", response_class=HTMLResponse)
def loginPage(request: Request):
    return template.TemplateResponse("loginRegister.html", {"request": request})

@app.post("/loginRegister")
def login_register(request: Request, 
                          username: str = Form(...), 
                          password: str = Form(...), 
                          email: str = Form(None)):
    conn = connessione()
    cursor = conn.cursor()

    if email is None:  # Se l'email non è presente, è un tentativo di login
        try:
            query = "SELECT * FROM utenti WHERE username = %s"
            cursor.execute(query, (username,))
            tupla = cursor.fetchone()
            print("CIAOOOOOOOOOOOO",tupla)
            if tupla is None or not confrontoPass(tupla[3], password):
                return template.TemplateResponse("loginRegister.html", {"request": request, "error": "Credenziali non valide"})
            
            role_redirects = ["cliente", "dipendente", "fornitore", "admin"]
            page_redirect =  ["/user_dashboard.html", "/dipendente_dashboard.html", "/fornitore_dashboard.html", "/admin_dashboard.html"]

            role = tupla[4]
            pos = -1
            for i in range(len(role_redirects)):
                if role_redirects[i] == role:
                    pos = i
            
            if pos != -1:
                redirect_page = page_redirect[pos] 
                return template.TemplateResponse(redirect_page, {"request": request})
            

            return template.TemplateResponse("loginRegister.html", {"request": request, "error": "Ruolo non valido"})

        finally:
            cursor.close()
            conn.close()
            
    else:  # Se l'email è presente, è un tentativo di registrazione
        try:
            cursor.execute("SELECT * FROM utenti WHERE email = %s", (email,))
            if cursor.fetchone():
                return template.TemplateResponse("loginRegister.html", {"request": request, "error": "Email già registrata"})

            cursor.execute("SELECT * FROM utenti WHERE username = %s", (username,))
            if cursor.fetchone():
                return template.TemplateResponse("loginRegister.html", {"request": request, "error": "Username già esistente"})

            hashed_password = PassHash(password)
            cursor.execute("INSERT INTO utenti (username, email, password, ruolo) VALUES (%s, %s, %s, %s)", (username, email, hashed_password, 'cliente'))
            conn.commit()

            return template.TemplateResponse("loginRegister.html", {"request": request, "success": f"{username} registrato con successo"})

        except Exception as e:
            conn.rollback()
            return template.TemplateResponse("loginRegister.html", {"request": request, "error": f"Errore durante la registrazione: {str(e)}"})

        finally:
            cursor.close()
            conn.close()


@app.post("/inviaCodice")
def invia_codice(request: Request, email: str = Form(...)):
    conn = connessione()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM utenti WHERE email = %s", (email,))
        utente = cursor.fetchone()
        if utente is None:
            return template.TemplateResponse("inviaCodice.html", {"request": request, "error": "Email non trovata"})

        codice = str(random.randint(100000, 999999))
        scadenza = datetime.now() + timedelta(minutes=10)

        request.session['codice'] = codice
        request.session['scadenza'] = scadenza.isoformat()

        invia_email(email, codice)
        return template.TemplateResponse("/cambiaPass", {"request": request})

    finally:
        cursor.close()
        conn.close()

@app.post("/cambiaPass")
def cambia_password(request: Request, email: str = Form(...), codice: str = Form(...), new_password: str = Form(...)):
    conn = connessione()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM utenti WHERE email = %s", (email,))
        utente = cursor.fetchone()
        if utente is None:
            return template.TemplateResponse("cambiaPass.html", {"request": request, "error": "Email non trovata"})

        codice_salvato = request.session.get('codice')
        scadenza_str = request.session.get('scadenza')

        if not codice_salvato or not scadenza_str:
            return template.TemplateResponse("cambiaPass.html", {"request": request, "error": "Codice non inviato o sessione scaduta."})

        scadenza = datetime.fromisoformat(scadenza_str)

        if codice != codice_salvato:
            return template.TemplateResponse("cambiaPass.html", {"request": request, "error": "Codice errato"})
        if datetime.now() > scadenza:
            return template.TemplateResponse("cambiaPass.html", {"request": request, "error": "Il codice è scaduto"})

        hashed_password = PassHash(new_password)
        cursor.execute("UPDATE utenti SET password = %s WHERE email = %s", (hashed_password, email))
        conn.commit()

        del request.session['codice']
        del request.session['scadenza']

        return template.TemplateResponse("cambiaPass.html", {"request": request, "success": "Password cambiata con successo"})

    finally:
        cursor.close()
        conn.close()


@app.post("/admin_dashboard")
def aggiungi_utente(request: Request, 
                    new_username: str = Form(...), 
                    new_email: str = Form(...), 
                    new_password: str = Form(...), 
                    new_role: str = Form(...)):
    conn = connessione()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM utenti WHERE username = %s", (new_username,))
        if cursor.fetchone():
            return template.TemplateResponse("admin_dashboard.html", {"request": request, "error": "Username già esistente"})

        cursor.execute("SELECT * FROM utenti WHERE email = %s", (new_email,))
        if cursor.fetchone():
            return template.TemplateResponse("admin_dashboard.html", {"request": request, "error": "Email già registrata"})

        hashed_password = PassHash(new_password)

        cursor.execute("INSERT INTO utenti (username, email, password, ruolo) VALUES (%s, %s, %s, %s)", 
                       (new_username, new_email, hashed_password, new_role))
        conn.commit()

        return RedirectResponse(url="/admin_dashboard", status_code=303)

    except Exception as e:
        conn.rollback()
        return template.TemplateResponse("admin_dashboard.html", {"request": request, "error": f"Errore durante l'aggiunta dell'utente: {str(e)}"})

    finally:
        cursor.close()
        conn.close()

