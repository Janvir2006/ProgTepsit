from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Configure middleware
app.add_middleware(SessionMiddleware, secret_key="ciao")

# Configure templates
templates = Jinja2Templates(directory="templates")

# Configure static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Import routes
from app.routes import auth, admin, user, employee, cart, pages

# Include routers - putting pages first
app.include_router(pages.router)  # Static pages should be first
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(user.router)
app.include_router(employee.router)
app.include_router(cart.router) 