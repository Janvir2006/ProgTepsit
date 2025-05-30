from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.database import get_connection
from app import templates
from decimal import Decimal

router = APIRouter()

@router.get("/user_dashboard", response_class=HTMLResponse)
def user_dashboard(request: Request, search_query: str = None):
    if 'user_id' not in request.session:
        return RedirectResponse(url="/loginRegister", status_code=303)
        
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if search_query:
            # Se c'è una query di ricerca, mostra solo i risultati della ricerca
            search_param = f"%{search_query}%"
            cursor.execute("""
                SELECT * FROM prodotti 
                WHERE quantita_disponibile > 0
                AND (nome LIKE %s OR descrizione LIKE %s)
                ORDER BY id_prodotto DESC
            """, (search_param, search_param))
            products = cursor.fetchall()
            
            show_search_results = True
        else:
            # Altrimenti mostra i prodotti normali
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
            show_search_results = False

        for product in products:
            product['id'] = product['id_prodotto']
            for key, value in product.items():
                if isinstance(value, Decimal):
                    product[key] = float(value)
        
        return templates.TemplateResponse("user_dashboard.html", {
            "request": request,
            "prodotti_lista": products if show_search_results else recent_products,
            "prodotti_popolari": low_quantity_products if not show_search_results else [],
            "username": request.session.get('username', 'tester'),
            "search_query": search_query,
            "show_search_results": show_search_results
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
