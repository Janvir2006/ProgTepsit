from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.database import get_connection
from app.utils.security import hash_password
from app import templates
import logging

router = APIRouter()

@router.get("/admin_dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    if 'user_id' not in request.session or request.session.get('role') != 'admin':
        return RedirectResponse(url="/loginRegister")
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@router.get("/admin_dashboard/cliente", response_class=HTMLResponse)
def admin_customer_view(request: Request):
    if 'user_id' not in request.session or request.session.get('role') != 'admin':
        return RedirectResponse(url="/loginRegister")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Query modificata per usare solo le colonne esistenti
        cursor.execute("""
            SELECT 
                id_utente,
                username,
                email,
                ruolo
            FROM utenti 
            WHERE ruolo = 'cliente'
            ORDER BY id_utente DESC
        """)
        customers = cursor.fetchall()
        
        # Log per debug
        print(f"Numero di clienti trovati: {len(customers)}")
        if customers:
            print("Primo cliente trovato:", customers[0])
        
        return templates.TemplateResponse("admin_customers.html", {
            "request": request,
            "customers": customers,
            "user_role": request.session.get('role'),
            "debug": True  # Abilitiamo il debug per vedere più informazioni
        })
    except Exception as e:
        print(f"Errore nel recupero dei clienti: {str(e)}")
        return templates.TemplateResponse("admin_customers.html", {
            "request": request,
            "error": f"Errore nel recupero dei clienti: {str(e)}",
            "customers": [],
            "user_role": request.session.get('role'),
            "debug": True
        })
    finally:
        cursor.close()
        conn.close()

@router.get("/admin_dashboard/dipendente", response_class=HTMLResponse)
def admin_employee_view(request: Request):
    if 'user_id' not in request.session or request.session.get('role') != 'admin':
        return RedirectResponse(url="/loginRegister")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                id_utente,
                username,
                email,
                ruolo
            FROM utenti 
            WHERE ruolo = 'dipendente'
            ORDER BY id_utente DESC
        """)
        employees = cursor.fetchall()
        
        # Log per debug
        print(f"Numero di dipendenti trovati: {len(employees)}")
        if employees:
            print("Primo dipendente trovato:", employees[0])
        
        return templates.TemplateResponse("admin_employees.html", {
            "request": request,
            "employees": employees,
            "user_role": request.session.get('role'),
            "debug": True
        })
    except Exception as e:
        print(f"Errore nel recupero dei dipendenti: {str(e)}")
        return templates.TemplateResponse("admin_employees.html", {
            "request": request,
            "error": f"Errore nel recupero dei dipendenti: {str(e)}",
            "employees": [],
            "user_role": request.session.get('role'),
            "debug": True
        })
    finally:
        cursor.close()
        conn.close()

@router.post("/admin_dashboard")
def add_user(
    request: Request,
    new_username: str = Form(...),
    new_email: str = Form(...),
    new_password: str = Form(...),
    new_role: str = Form(...)
):
    if 'user_id' not in request.session or request.session.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Non autorizzato")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM utenti WHERE username = %s", (new_username,))
        if cursor.fetchone():
            return templates.TemplateResponse("admin_dashboard.html", 
                {"request": request, "error": "Username già esistente"})

        cursor.execute("SELECT * FROM utenti WHERE email = %s", (new_email,))
        if cursor.fetchone():
            return templates.TemplateResponse("admin_dashboard.html", 
                {"request": request, "error": "Email già registrata"})

        hashed_password = hash_password(new_password)

        cursor.execute(
            "INSERT INTO utenti (username, email, password, ruolo) VALUES (%s, %s, %s, %s)",
            (new_username, new_email, hashed_password, new_role)
        )
        conn.commit()

        return RedirectResponse(url="/admin_dashboard", status_code=303)

    except Exception as e:
        conn.rollback()
        return templates.TemplateResponse("admin_dashboard.html", 
            {"request": request, "error": f"Errore durante l'aggiunta dell'utente: {str(e)}"})

    finally:
        cursor.close()
        conn.close() 