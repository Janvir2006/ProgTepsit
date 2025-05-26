import mysql.connector
from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="ciao")
template = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")



# Funzioni di connessione al database e altre funzioni di utilità (come prima)
def connessione():
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='jan',
            password='Janvir2006',
            database='supermercato'
        )
        print("Database connection successful")  # Debug print
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")  # Debug print
        raise e


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


@app.get("/aboutus", response_class=HTMLResponse)
def IcPage(request: Request):
    return template.TemplateResponse("aboutus.html", {"request": request})

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
    print(f"Login attempt - username: {username}, email: {email}")  # Debug print
    conn = connessione()
    cursor = conn.cursor()

    if email is None:  # Login
        try:
            query = "SELECT * FROM utenti WHERE username = %s"
            cursor.execute(query, (username,))
            tupla = cursor.fetchone()
            
            print(f"Login query result: {tupla}")  # Debug print
            
            if tupla is None or not confrontoPass(tupla[3], password):
                return template.TemplateResponse("loginRegister.html", 
                    {"request": request, "error": "Credenziali non valide"})

            # Memorizza l'utente in sessione
            request.session['user_id'] = tupla[0]
            request.session['username'] = tupla[1]
            request.session['role'] = tupla[4]
            
            print(f"Session after login: {dict(request.session)}")  # Debug print

            # Reindirizzamento basato sul ruolo
            role_redirects = {
                "cliente": "/user_dashboard",
                "dipendente": "/dipendente_dashboard",
                "fornitore": "/fornitore_dashboard",
                "admin": "/admin_dashboard"
            }

            if tupla[4] in role_redirects:
                response = RedirectResponse(
                    url=role_redirects[tupla[4]], 
                    status_code=303)
                return response
            
            return template.TemplateResponse("loginRegister.html", 
                {"request": request, "error": "Ruolo non valido"})

        except Exception as e:
            print(f"Login error: {str(e)}")  # Debug print
            return template.TemplateResponse("loginRegister.html", 
                {"request": request, "error": f"Errore durante il login: {str(e)}"})
        finally:
            cursor.close()
            conn.close()

    else:
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
        return RedirectResponse("/cambiaPass", status_code=303)

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

@app.get("/admin_dashboard/{role}")
def get_users_by_role(role: str):
    conn = connessione()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT username, email, password, ruolo as ruolo FROM utenti WHERE ruolo = %s", (role,))
        users = cursor.fetchall()
        return {"users": users}
    finally:
        cursor.close()
        conn.close()

@app.get("/admin_dashboard/edit/{username}")
def edit_user_page(request: Request, username: str):
    conn = connessione()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM utenti WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return RedirectResponse(url="/admin_dashboard")
        return template.TemplateResponse("admin_dashboard.html", {"request": request, "user": user})
    finally:
        cursor.close()
        conn.close()

@app.post("/admin_dashboard/update/{username}")
def update_user(request: Request, username: str,
                new_username: str = Form(...),
                new_email: str = Form(...),
                new_role: str = Form(...)):
    conn = connessione()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE utenti SET username = %s, email = %s, ruolo = %s WHERE username = %s",
                       (new_username, new_email, new_role, username))
        conn.commit()
        return RedirectResponse(url="/admin_dashboard", status_code=303)
    except Exception as e:
        conn.rollback()
        return template.TemplateResponse("admin_dashboard.html", {"request": request, "error": f"Errore durante l'aggiornamento: {str(e)}"})
    finally:
        cursor.close()
        conn.close()

@app.get("/admin_dashboard/delete/{username}")
def delete_user(username: str):
    conn = connessione()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM utenti WHERE username = %s", (username,))
        conn.commit()
        return RedirectResponse(url="/admin_dashboard", status_code=303)
    except Exception as e:
        conn.rollback()
        return template.TemplateResponse("admin_dashboard.html", {"request": request, "error": f"Errore durante l'aggiunta dell'utente: {str(e)}"})
    finally:
        cursor.close()
        conn.close()




@app.get("/user_dashboard", response_class=HTMLResponse)
def user_dashboard(request: Request):
    
    fake_products = [
        {
            'id_prodotto': 1,
            'nome': 'test prodotto',
            'descrizione': 'descrizione test',
            'prezzo': 20.5,
            'immagine_url': '../static/images/download.jpg',
            'prezzo_scontato': 25.0,
            'id': 1
        }
    ]   
    
    print("Session data:", dict(request.session))  # Debug print
    if 'user_id' not in request.session:
        print("User not logged in, redirecting to login")  # Debug print
        return RedirectResponse(url="/loginRegister", status_code=303)
        
    conn = connessione()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM prodotti")
        products = cursor.fetchall()

        # Qui aggiungi la chiave id uguale a id_prodotto per comodità nel template
        for prodotto in products:
            prodotto['id'] = prodotto['id_prodotto']
            for key, value in prodotto.items():
                if isinstance(value, Decimal):
                    prodotto[key] = float(value)
        
        
        print("Products from DB:", products)  # Debug print
        print(f"Passing to template {len(products)} products")
        return template.TemplateResponse("user_dashboard.html", {
            "request": request,
            "prodotti_lista": products,
            "username": request.session.get('username', 'tester')
        })
    except Exception as e:
        print(f"Error in user_dashboard: {str(e)}")  # Debug print
        return template.TemplateResponse("user_dashboard.html", {
            "request": request,
            "products": [],
            "error": f"Errore nel caricamento dei prodotti: {str(e)}",
            "username": request.session.get('username')
        })
    finally:
        cursor.close()
        conn.close()





# -------------------------------------------------------------------------------------
# Dipendente
# -------------------------------------------------------------------------------------

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/loginRegister")

@app.get("/dipendente_dashboard", response_class=HTMLResponse)
def dipendente_dashboard_page(request: Request):
    # Verifica che l'utente sia loggato e sia un dipendente
    if 'user_id' not in request.session or request.session.get('role') != 'dipendente':
        return RedirectResponse(url="/loginRegister")
    
    return template.TemplateResponse("dipendente_dashboard.html", {"request": request})

@app.get("/aggiungi_prodotto", response_class=HTMLResponse)
def aggiungi_prodotto_page(request: Request):
    # Verifica che l'utente sia loggato e sia un dipendente
    if 'user_id' not in request.session or request.session.get('role') != 'dipendente':
        return RedirectResponse(url="/loginRegister")
    
    return template.TemplateResponse("aggiungi_prodotto.html", {"request": request})

@app.post("/aggiungi_prodotto")
async def aggiungi_prodotto(
    request: Request,
    nome: str = Form(...),
    descrizione: str = Form(...),
    prezzo: float = Form(...),
    quantita: int = Form(...),
    immagine_url: str = Form(...)
):
    # Verifica che l'utente sia loggato e sia un dipendente
    if 'user_id' not in request.session or request.session.get('role') != 'dipendente':
        return RedirectResponse(url="/loginRegister")
    
    conn = connessione()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO prodotti (nome, descrizione, prezzo, quantita_disponibile, immagine_url) VALUES (%s, %s, %s, %s, %s)",
            (nome, descrizione, prezzo, quantita, immagine_url)
        )
        conn.commit()
        return template.TemplateResponse("aggiungi_prodotto.html", {
            "request": request,
            "success": "Prodotto aggiunto con successo!"
        })
    except Exception as e:
        conn.rollback()
        return template.TemplateResponse("aggiungi_prodotto.html", {
            "request": request,
            "error": f"Errore durante l'aggiunta del prodotto: {str(e)}"
        })
    finally:
        cursor.close()
        conn.close()

@app.get("/api/products")
def get_products():
    conn = connessione()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM prodotti")
        products = cursor.fetchall()
        return {"products": products}
    finally:
        cursor.close()
        conn.close()

@app.get("/hot_products", response_class=HTMLResponse)
def hot_products(request: Request):
    conn = connessione()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM prodotti")
        products = cursor.fetchall()

        # Qui aggiungi la chiave id uguale a id_prodotto per comodità nel template
        for prodotto in products:
            prodotto['id'] = prodotto['id_prodotto']
            for key, value in prodotto.items():
                if isinstance(value, Decimal):
                    prodotto[key] = float(value)
        
        
        print("Products from DB:", products)  # Debug print
        print(f"Passing to template {len(products)} products")
        return template.TemplateResponse("hot_products.html", {
            "request": request,
            "prodotti_lista": products,
            "username": request.session.get('username', 'tester')
        })
    except Exception as e:
        print(f"Error in user_dashboard: {str(e)}")  # Debug print
        return template.TemplateResponse("hot_products.html", {
            "request": request,
            "products": [],
            "error": f"Errore nel caricamento dei prodotti: {str(e)}",
            "username": request.session.get('username')
        })
    finally:
        cursor.close()
        conn.close()
        

########################
#CARRELLO              #
########################

def get_carrello_db(utente_id: int) -> list:
    conn = connessione()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.id_prodotto as id, p.nome, p.prezzo, p.immagine_url, c.quantita 
            FROM carrello c
            JOIN prodotti p ON c.id_prodotto = p.id_prodotto
            WHERE c.id_utente = %s
        """, (utente_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def aggiungi_al_carrello_db(utente_id: int, prodotto_id: int, quantita: int = 1):
    conn = connessione()
    cursor = conn.cursor()
    try:
        print(f"Aggiungendo al carrello - utente_id: {utente_id}, prodotto_id: {prodotto_id}, quantita: {quantita}")  # Debug print
        # Verifica se il prodotto è già nel carrello
        cursor.execute("SELECT quantita FROM carrello WHERE id_utente = %s AND id_prodotto = %s", 
                      (utente_id, prodotto_id))
        existing = cursor.fetchone()
        
        if existing:
            # Aggiorna la quantità
            new_quantita = existing[0] + quantita
            print(f"Prodotto esistente - aggiornando quantità a: {new_quantita}")  # Debug print
            cursor.execute("UPDATE carrello SET quantita = %s WHERE id_utente = %s AND id_prodotto = %s",
                          (new_quantita, utente_id, prodotto_id))
        else:
            # Aggiungi nuovo prodotto
            print(f"Nuovo prodotto - inserendo nel carrello")  # Debug print
            cursor.execute("INSERT INTO carrello (id_utente, id_prodotto, quantita) VALUES (%s, %s, %s)",
                          (utente_id, prodotto_id, quantita))
        conn.commit()
        print("Operazione completata con successo")  # Debug print
    except Exception as e:
        conn.rollback()
        print(f"Errore nell'aggiunta al carrello: {str(e)}")  # Debug print
        raise e
    finally:
        cursor.close()
        conn.close()

def rimuovi_dal_carrello_db(utente_id: int, prodotto_id: int):
    conn = connessione()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM carrello WHERE id_utente = %s AND id_prodotto = %s", 
                      (utente_id, prodotto_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def svuota_carrello_db(utente_id: int):
    conn = connessione()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM carrello WHERE id_utente = %s", (utente_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
        
@app.get("/api/carrello")
async def api_carrello(request: Request):
    if 'user_id' not in request.session:
        return JSONResponse(content={"error": "Non autorizzato"}, status_code=401)
    
    utente_id = request.session['user_id']
    carrello_items = get_carrello_db(utente_id)

    # Converti i Decimal in float per JSON serializzabile
    for item in carrello_items:
        for key, value in item.items():
            if isinstance(value, Decimal):
                item[key] = float(value)

    return JSONResponse(content=carrello_items)


@app.get("/carrello", response_class=HTMLResponse)
def carrello(request: Request):
    if 'user_id' not in request.session:
        return RedirectResponse(url="/loginRegister")

    user_id = request.session['user_id']
    carrello_items = get_carrello_db(user_id)

    # Calcola il totale: prezzo * quantità
    totale = sum(item['prezzo'] * item['quantita'] for item in carrello_items)

    context = {
        "request": request,
        "carrello_items": carrello_items,
        "totale": totale
    }
    return template.TemplateResponse("carrello.html", context)

@app.post("/carrello/aggiungi/{prodotto_id}")
async def aggiungi_al_carrello(request: Request, prodotto_id: int, quantita: int = Form(1)):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=401, detail="Non autorizzato")
    
    user_id = request.session['user_id']
    aggiungi_al_carrello_db(user_id, prodotto_id, quantita)
    return RedirectResponse(url="/carrello", status_code=303)

@app.post("/carrello/aggiorna/{prodotto_id}")
async def aggiorna_quantita_carrello(request: Request, prodotto_id: int, quantita: int = Form(...)):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=401, detail="Non autorizzato")
    
    user_id = request.session['user_id']
    if quantita <= 0:
        rimuovi_dal_carrello_db(user_id, prodotto_id)
    else:
        conn = connessione()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE carrello SET quantita = %s WHERE id_utente = %s AND id_prodotto = %s",
                          (quantita, user_id, prodotto_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    return RedirectResponse(url="/carrello", status_code=303)

@app.post("/carrello/rimuovi/{prodotto_id}")
async def rimuovi_dal_carrello(request: Request, prodotto_id: int):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=401, detail="Non autorizzato")
    
    user_id = request.session['user_id']
    rimuovi_dal_carrello_db(user_id, prodotto_id)
    return RedirectResponse(url="/carrello", status_code=303)

@app.post("/carrello/svuota")
async def svuota_carrello(request: Request):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=401, detail="Non autorizzato")
    
    user_id = request.session['user_id']
    svuota_carrello_db(user_id)
    return RedirectResponse(url="/carrello", status_code=303)


########################
#ORDINE                #
########################
@app.get("/checkout", response_class=HTMLResponse)
def mostra_checkout(request: Request):
    if 'user_id' not in request.session:
        return RedirectResponse("/loginRegister")
    
    user_id = request.session['user_id']
    carrello_items = get_carrello_db(user_id)
    totale = sum(item['prezzo'] * item['quantita'] for item in carrello_items)
    
    return template.TemplateResponse("checkout.html", {
        "request": request,
        "carrello_items": carrello_items,
        "totale": round(totale, 2)
    })


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def invia_emailCheckOut(destinatario, prodotti, totale):
    sender_email = "patadmpatberna@gmail.com"
    password = "rmem vklz zcrp lxsy"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    subject = "Dettagli del tuo ordine"

    # Costruiamo il corpo della mail con i dettagli dell'ordine
    body = "Grazie per il tuo ordine! Ecco i dettagli:\n\n"
    body += "{:<30} {:<10} {:<15} {:<10}\n".format("Prodotto", "Quantità", "Prezzo unitario", "Totale")
    body += "-"*70 + "\n"
    
    for prodotto in prodotti:
        nome = prodotto['nome']
        quantita = prodotto['quantita']
        prezzo_unitario = prodotto['prezzo']
        totale_prodotto = quantita * prezzo_unitario
        body += f"{nome:<30} {quantita:<10} {prezzo_unitario:<15.2f} {totale_prodotto:<10.2f}\n"
    
    body += "\nPrezzo totale ordine: {:.2f} €".format(totale)

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = destinatario
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, destinatario, msg.as_string())
        server.quit()
        print("Email inviata correttamente a", destinatario)
    except Exception as e:
        print(f"Errore nell'invio dell'email: {e}")

@app.post("/checkout/confirm")
def conferma_ordine(request: Request):
    if 'user_id' not in request.session:
        return RedirectResponse("/loginRegister")
    
    user_id = request.session['user_id']
    carrello_items = get_carrello_db(user_id)

    if not carrello_items:
        return RedirectResponse("/carrello")  # Carrello vuoto

    conn = connessione()
    cursor = conn.cursor()
    try:
        totale = sum(item['prezzo'] * item['quantita'] for item in carrello_items)
        cursor.execute("INSERT INTO ordini (id_utente, totale) VALUES (%s, %s)", (user_id, totale))
        ordine_id = cursor.lastrowid

        for item in carrello_items:
            cursor.execute(
                "INSERT INTO dettagli_ordine (id_ordine, id_prodotto, quantita, prezzo_unitario) VALUES (%s, %s, %s, %s)",
                (ordine_id, item['id'], item['quantita'], item['prezzo'])
            )
            cursor.execute(
                "UPDATE prodotti SET quantita_disponibile = quantita_disponibile - %s WHERE id_prodotto = %s",
                (item['quantita'], item['id'])
            )

        # Recupera email utente dal DB (aggiusta la query in base alla tua tabella utenti)
        cursor.execute("SELECT email FROM utenti WHERE id_utente = %s", (user_id,))
        user_data = cursor.fetchone()
        email_utente = user_data[0] if user_data else None

        svuota_carrello_db(user_id)
        conn.commit()

        # Invia email se abbiamo l'indirizzo
        if email_utente:
            invia_emailCheckOut(email_utente, carrello_items, totale)
            print("CIIAAAAAOOOOOOOOOO, mail inviata con succeso")
        return RedirectResponse("/user_dashboard", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nel completare l'ordine: {e}")
    finally:
        cursor.close()
        conn.close()




def crea_ordine_db(utente_id: int):
    conn = connessione()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Recupera il carrello
        cursor.execute("""
            SELECT c.id_prodotto, c.quantita, p.prezzo
            FROM carrello c
            JOIN prodotti p ON c.id_prodotto = p.id_prodotto
            WHERE c.id_utente = %s
        """, (utente_id,))
        carrello = cursor.fetchall()

        if not carrello:
            raise Exception("Il carrello è vuoto.")

        # 2. Calcola il totale ordine
        totale = sum(item['prezzo'] * item['quantita'] for item in carrello)

        # 3. Inserisci l’ordine
        cursor.execute("""
            INSERT INTO ordini (id_utente, data_ordine, totale) 
            VALUES (%s, %s, %s)
        """, (utente_id, datetime.now(), totale))
        id_ordine = cursor.lastrowid

        # 4. Inserisci ogni prodotto nei dettagli ordine
        for item in carrello:
            cursor.execute("""
                INSERT INTO dettagli_ordine (id_ordine, id_prodotto, quantita, prezzo_unitario)
                VALUES (%s, %s, %s, %s)
            """, (id_ordine, item['id_prodotto'], item['quantita'], item['prezzo']))

        # 5. Svuota il carrello
        cursor.execute("DELETE FROM carrello WHERE id_utente = %s", (utente_id,))

        conn.commit()
        return id_ordine
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

@app.post("/carrello/conferma_ordine")
async def conferma_ordine(request: Request):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=401, detail="Non autorizzato")

    user_id = request.session['user_id']
    try:
        ordine_id = crea_ordine_db(user_id)
        return RedirectResponse(url=f"/ordine_confermato/{ordine_id}", status_code=303)
    except Exception as e:
        return template.TemplateResponse("carrello.html", {
            "request": request,
            "carrello_items": get_carrello_db(user_id),
            "totale": sum(item['prezzo'] * item['quantita'] for item in get_carrello_db(user_id)),
            "error": f"Errore durante la conferma dell’ordine: {str(e)}"
        })


@app.get("/ordine_confermato/{ordine_id}", response_class=HTMLResponse)
def ordine_confermato(request: Request, ordine_id: int):
    return template.TemplateResponse("ordine_confermato.html", {
        "request": request,
        "ordine_id": ordine_id
    })


@app.get("/i_miei_ordini", response_class=HTMLResponse)
def i_miei_ordini(request: Request):
    if 'user_id' not in request.session:
        return RedirectResponse(url="/loginRegister")

    user_id = request.session['user_id']
    conn = connessione()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM ordini WHERE id_utente = %s ORDER BY data_ordine DESC
        """, (user_id,))
        ordini = cursor.fetchall()
        return template.TemplateResponse("i_miei_ordini.html", {
            "request": request,
            "ordini": ordini
        })
    finally:
        cursor.close()
        conn.close()


@app.get("/ordine/{ordine_id}", response_class=HTMLResponse)
def dettaglio_ordine(request: Request, ordine_id: int):
    if 'user_id' not in request.session:
        return RedirectResponse(url="/loginRegister")

    conn = connessione()
    cursor = conn.cursor(dictionary=True)
    try:
        # Recupera info ordine
        cursor.execute("SELECT * FROM ordini WHERE id_ordine = %s", (ordine_id,))
        ordine = cursor.fetchone()

        # Recupera dettagli
        cursor.execute("""
            SELECT d.*, p.nome, p.immagine_url
            FROM dettagli_ordine d
            JOIN prodotti p ON d.id_prodotto = p.id_prodotto
            WHERE d.id_ordine = %s
        """, (ordine_id,))
        dettagli = cursor.fetchall()

        return template.TemplateResponse("dettaglio_ordine.html", {
            "request": request,
            "ordine": ordine,
            "dettagli": dettagli
        })
    finally:
        cursor.close()
        conn.close()
