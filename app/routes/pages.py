from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app import templates
import logging

router = APIRouter(prefix="")  # Explicitly set empty prefix

@router.get("/aboutus", response_class=HTMLResponse)
async def about_us(request: Request):
    print("Accessing /aboutus route")  # Debug print
    return templates.TemplateResponse("aboutus.html", {"request": request}) 