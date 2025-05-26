from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.database import get_connection
from app import templates

router = APIRouter()

@router.get("/dipendente_dashboard", response_class=HTMLResponse)
def employee_dashboard(request: Request):
    if 'user_id' not in request.session or request.session.get('role') != 'dipendente':
        return RedirectResponse(url="/loginRegister")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                id_prodotto,
                nome,
                prezzo,
                quantita_disponibile as quantita,
                immagine_url
            FROM prodotti 
            WHERE quantita_disponibile > 0
            ORDER BY id_prodotto DESC
        """)
        products = cursor.fetchall()
        
        # Log per debug
        print(f"Numero di prodotti trovati: {len(products)}")
        if products:
            print("Primo prodotto trovato:", products[0])
        
        return templates.TemplateResponse("dipendente_dashboard.html", {
            "request": request,
            "products": products,
            "user_role": request.session.get('role'),
            "debug": True
        })
    except Exception as e:
        print(f"Errore nel recupero dei prodotti: {str(e)}")
        return templates.TemplateResponse("dipendente_dashboard.html", {
            "request": request,
            "error": f"Errore nel recupero dei prodotti: {str(e)}",
            "products": [],
            "user_role": request.session.get('role'),
            "debug": True
        })
    finally:
        cursor.close()
        conn.close()

@router.get("/aggiungi_prodotto", response_class=HTMLResponse)
def add_product_page(request: Request):
    if 'user_id' not in request.session or request.session.get('role') != 'dipendente':
        return RedirectResponse(url="/loginRegister")
    return templates.TemplateResponse("aggiungi_prodotto.html", {"request": request})

@router.post("/aggiungi_prodotto")
async def add_product(
    request: Request,
    nome: str = Form(...),
    descrizione: str = Form(...),
    prezzo: float = Form(...),
    quantita: int = Form(...),
    immagine_url: str = Form(...)
):
    if 'user_id' not in request.session or request.session.get('role') != 'dipendente':
        raise HTTPException(status_code=403, detail="Non autorizzato")
    
    # Verifica che il nome file sia valido
    if not immagine_url or not any(immagine_url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
        return templates.TemplateResponse("aggiungi_prodotto.html", {
            "request": request,
            "error": "Il nome del file immagine non è valido. Usa un'estensione .png, .jpg, .jpeg o .gif"
        })

    # Costruisci il percorso completo dell'immagine
    immagine_path = f"../static/images/{immagine_url}"
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO prodotti (nome, descrizione, prezzo, quantita_disponibile, immagine_url) "
            "VALUES (%s, %s, %s, %s, %s)",
            (nome, descrizione, prezzo, quantita, immagine_path)
        )
        conn.commit()
        return templates.TemplateResponse("aggiungi_prodotto.html", {
            "request": request,
            "success": "Prodotto aggiunto con successo!"
        })
    except Exception as e:
        conn.rollback()
        return templates.TemplateResponse("aggiungi_prodotto.html", {
            "request": request,
            "error": f"Errore durante l'aggiunta del prodotto: {str(e)}"
        })
    finally:
        cursor.close()
        conn.close() 