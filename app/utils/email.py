import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import EMAIL_CONFIG

def send_verification_code(recipient: str, code: str) -> None:
    subject = "Codice di verifica per cambio password"
    body = f"Il tuo codice di verifica per cambiare la password è: {code}"
    _send_email(recipient, subject, body)

def send_order_confirmation(recipient: str, products: list, total: float) -> None:
    subject = "Dettagli del tuo ordine"
    body = "Grazie per il tuo ordine! Ecco i dettagli:\n\n"
    body += "{:<30} {:<10} {:<15} {:<10}\n".format("Prodotto", "Quantità", "Prezzo unitario", "Totale")
    body += "-"*70 + "\n"
    
    for product in products:
        nome = product['nome']
        quantita = product['quantita']
        prezzo_unitario = product['prezzo']
        totale_prodotto = quantita * prezzo_unitario
        body += f"{nome:<30} {quantita:<10} {prezzo_unitario:<15.2f} {totale_prodotto:<10.2f}\n"
    
    body += "\nPrezzo totale ordine: {:.2f} €".format(total)
    _send_email(recipient, subject, body)

def _send_email(recipient: str, subject: str, body: str) -> None:
    msg = MIMEMultipart()
    msg["From"] = EMAIL_CONFIG['sender_email']
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['password'])
        server.sendmail(EMAIL_CONFIG['sender_email'], recipient, msg.as_string())
        server.quit()
        print("Email inviata correttamente a", recipient)
    except Exception as e:
        print(f"Errore nell'invio dell'email: {e}")
        raise e 