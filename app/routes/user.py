from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.database import get_connection
from app import templates
from decimal import Decimal

router = APIRouter()

@router.get("/user_dashboard", response_class=HTMLResponse)
def user_dashboard(request: Request):
    if 'user_id' not in request.session:
        return RedirectResponse(url="/loginRegister", status_code=303)
        
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get recent products ordered by id_prodotto DESC
        cursor.execute("""
            SELECT * FROM prodotti 
            WHERE quantita_disponibile > 0
            ORDER BY id_prodotto DESC
        """)
        recent_products = cursor.fetchall()

        # Get products with lowest quantity
        cursor.execute("""
            SELECT * FROM prodotti 
            WHERE quantita_disponibile > 0
            ORDER BY quantita_disponibile ASC
            LIMIT 5
        """)
        low_quantity_products = cursor.fetchall()

        # Combine the products
        products = recent_products + low_quantity_products

        for product in products:
            product['id'] = product['id_prodotto']
            for key, value in product.items():
                if isinstance(value, Decimal):
                    product[key] = float(value)
        
        return templates.TemplateResponse("user_dashboard.html", {
            "request": request,
            "prodotti_lista": recent_products,
            "prodotti_popolari": low_quantity_products,
            "username": request.session.get('username', 'tester')
        })
    except Exception as e:
        print(f"Error in user_dashboard: {str(e)}")
        return templates.TemplateResponse("user_dashboard.html", {
            "request": request,
            "products": [],
            "error": f"Errore nel caricamento dei prodotti: {str(e)}",
            "username": request.session.get('username')
        })
    finally:
        cursor.close()
        conn.close()

@router.get("/hot_products", response_class=HTMLResponse)
def hot_products(request: Request):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM prodotti 
            WHERE quantita_disponibile > 0 
            ORDER BY id_prodotto DESC
        """)
        products = cursor.fetchall()

        for product in products:
            product['id'] = product['id_prodotto']
            for key, value in product.items():
                if isinstance(value, Decimal):
                    product[key] = float(value)
        
        return templates.TemplateResponse("hot_products.html", {
            "request": request,
            "prodotti_lista": products,
            "username": request.session.get('username', 'tester')
        })
    except Exception as e:
        print(f"Error in hot_products: {str(e)}")
        return templates.TemplateResponse("hot_products.html", {
            "request": request,
            "products": [],
            "error": f"Errore nel caricamento dei prodotti: {str(e)}",
            "username": request.session.get('username')
        })
    finally:
        cursor.close()
        conn.close()

@router.get("/api/products")
def get_products():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM prodotti 
            WHERE quantita_disponibile > 0 
            ORDER BY id_prodotto DESC
        """)
        products = cursor.fetchall()
        # Converti i valori Decimal in float
        for product in products:
            for key, value in product.items():
                if isinstance(value, Decimal):
                    product[key] = float(value)
        return {"products": products}
    finally:
        cursor.close()
        conn.close() 