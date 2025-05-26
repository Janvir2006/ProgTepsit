from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.database import get_connection
from app.utils.email import send_order_confirmation
from app import templates
from datetime import datetime
from decimal import Decimal

router = APIRouter()

def get_cart_from_db(user_id: int) -> list:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.id_prodotto as id, p.nome, p.prezzo, p.immagine_url, c.quantita 
            FROM carrello c
            JOIN prodotti p ON c.id_prodotto = p.id_prodotto
            WHERE c.id_utente = %s
        """, (user_id,))
        items = cursor.fetchall()
        # Converti i valori Decimal in float
        for item in items:
            for key, value in item.items():
                if isinstance(value, Decimal):
                    item[key] = float(value)
        return items
    finally:
        cursor.close()
        conn.close()

def add_to_cart_db(user_id: int, product_id: int, quantity: int = 1):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT quantita FROM carrello WHERE id_utente = %s AND id_prodotto = %s", 
            (user_id, product_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            new_quantity = existing[0] + quantity
            cursor.execute(
                "UPDATE carrello SET quantita = %s WHERE id_utente = %s AND id_prodotto = %s",
                (new_quantity, user_id, product_id)
            )
        else:
            cursor.execute(
                "INSERT INTO carrello (id_utente, id_prodotto, quantita) VALUES (%s, %s, %s)",
                (user_id, product_id, quantity)
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def remove_from_cart_db(user_id: int, product_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM carrello WHERE id_utente = %s AND id_prodotto = %s", 
            (user_id, product_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def empty_cart_db(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM carrello WHERE id_utente = %s", (user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

@router.get("/api/carrello")
async def api_cart(request: Request):
    if 'user_id' not in request.session:
        return JSONResponse(content={"error": "Non autorizzato"}, status_code=401)
    
    user_id = request.session['user_id']
    cart_items = get_cart_from_db(user_id)
    return JSONResponse(content=cart_items)

@router.get("/carrello", response_class=HTMLResponse)
def cart(request: Request):
    if 'user_id' not in request.session:
        return RedirectResponse(url="/loginRegister")

    user_id = request.session['user_id']
    cart_items = get_cart_from_db(user_id)
    total = sum(item['prezzo'] * item['quantita'] for item in cart_items)

    return templates.TemplateResponse("carrello.html", {
        "request": request,
        "carrello_items": cart_items,
        "totale": total
    })

@router.post("/carrello/aggiungi/{product_id}")
async def add_to_cart(request: Request, product_id: int, quantity: int = Form(1)):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=401, detail="Non autorizzato")
    
    user_id = request.session['user_id']
    add_to_cart_db(user_id, product_id, quantity)
    return RedirectResponse(url="/carrello", status_code=303)

@router.post("/carrello/aggiorna/{product_id}")
async def update_cart_quantity(request: Request, product_id: int, quantity: int = Form(...)):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=401, detail="Non autorizzato")
    
    try:
        if quantity <= 0:
            # Se la quantità è 0 o negativa, rimuovi il prodotto dal carrello
            user_id = request.session['user_id']
            remove_from_cart_db(user_id, product_id)
            return RedirectResponse(url="/carrello", status_code=303)
        
        user_id = request.session['user_id']
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Prima verifichiamo la quantità disponibile
            cursor.execute(
                "SELECT quantita_disponibile FROM prodotti WHERE id_prodotto = %s",
                (product_id,)
            )
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Prodotto non trovato")
            
            quantita_disponibile = result[0]
            if quantity > quantita_disponibile:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Quantità richiesta non disponibile. Disponibili: {quantita_disponibile}"
                )

            cursor.execute(
                "UPDATE carrello SET quantita = %s WHERE id_utente = %s AND id_prodotto = %s",
                (quantity, user_id, product_id)
            )
            conn.commit()
            return RedirectResponse(url="/carrello", status_code=303)
        finally:
            cursor.close()
            conn.close()
    except ValueError:
        raise HTTPException(status_code=400, detail="Quantità non valida")

@router.post("/carrello/rimuovi/{product_id}")
async def remove_from_cart(request: Request, product_id: int):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=401, detail="Non autorizzato")
    
    user_id = request.session['user_id']
    remove_from_cart_db(user_id, product_id)
    return RedirectResponse(url="/carrello", status_code=303)

@router.post("/carrello/svuota")
async def empty_cart(request: Request):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=401, detail="Non autorizzato")
    
    user_id = request.session['user_id']
    empty_cart_db(user_id)
    return RedirectResponse(url="/carrello", status_code=303)

@router.get("/checkout", response_class=HTMLResponse)
def show_checkout(request: Request):
    if 'user_id' not in request.session:
        return RedirectResponse("/loginRegister")
    
    user_id = request.session['user_id']
    cart_items = get_cart_from_db(user_id)
    total = sum(item['prezzo'] * item['quantita'] for item in cart_items)
    
    return templates.TemplateResponse("checkout.html", {
        "request": request,
        "carrello_items": cart_items,
        "totale": round(total, 2)
    })

@router.post("/checkout/confirm")
def confirm_order(request: Request):
    if 'user_id' not in request.session:
        return RedirectResponse("/loginRegister")
    
    user_id = request.session['user_id']
    cart_items = get_cart_from_db(user_id)

    if not cart_items:
        return RedirectResponse("/carrello")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        total = sum(item['prezzo'] * item['quantita'] for item in cart_items)
        cursor.execute(
            "INSERT INTO ordini (id_utente, totale) VALUES (%s, %s)", 
            (user_id, total)
        )
        order_id = cursor.lastrowid

        for item in cart_items:
            cursor.execute(
                "INSERT INTO dettagli_ordine (id_ordine, id_prodotto, quantita, prezzo_unitario) "
                "VALUES (%s, %s, %s, %s)",
                (order_id, item['id'], item['quantita'], item['prezzo'])
            )
            cursor.execute(
                "UPDATE prodotti SET quantita_disponibile = quantita_disponibile - %s "
                "WHERE id_prodotto = %s",
                (item['quantita'], item['id'])
            )

        cursor.execute("SELECT email FROM utenti WHERE id_utente = %s", (user_id,))
        user_data = cursor.fetchone()
        user_email = user_data[0] if user_data else None

        empty_cart_db(user_id)
        conn.commit()

        if user_email:
            send_order_confirmation(user_email, cart_items, total)
        return RedirectResponse("/user_dashboard", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nel completare l'ordine: {e}")
    finally:
        cursor.close()
        conn.close() 