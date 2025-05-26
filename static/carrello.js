// Funzione per aggiornare il contatore del carrello nella navbar
async function updateCartCounter() {
    try {
        const response = await fetch('/api/carrello');
        if (!response.ok) throw new Error("Errore nel caricamento del carrello");
        const carrello = await response.json();
        const counter = document.querySelector(".nav-cart span");
        if (counter) {
            counter.textContent = carrello.length;
        }
    } catch (error) {
        console.error("Impossibile aggiornare il contatore del carrello:", error);
    }
}

// Funzione per mostrare il contenuto del carrello nella pagina carrello.html
async function mostraCarrello() {
    const container = document.getElementById("carrello-container");
    if (!container) return;

    try {
        const response = await fetch('/api/carrello');
        if (!response.ok) throw new Error("Errore nel caricamento del carrello");
        const carrello = await response.json();

        if (carrello.length === 0) {
            container.innerHTML = "<p>Il carrello è vuoto.</p>";
            return;
        }

        let html = `
            <div class="carrello-header">
                <span>Prodotto</span>
                <span>Prezzo</span>
                <span>Quantità</span>
                <span>Totale</span>
                <span>Azioni</span>
            </div>
        `;

        let totaleGenerale = 0;

        carrello.forEach(item => {
            const totaleProdotto = (item.prezzo * item.quantita).toFixed(2);
            totaleGenerale += parseFloat(totaleProdotto);
            html += `
                <div class="carrello-item" data-id="${item.id}">
                    <div class="carrello-item-img">
                        <img src="${item.immagine_url}" alt="${item.nome}" />
                        <span>${item.nome}</span>
                    </div>
                    <div class="carrello-item-prezzo">€${item.prezzo.toFixed(2)}</div>
                    <div class="carrello-item-quantita">
                        <input type="number" min="1" value="${item.quantita}" class="quantita-input" />
                    </div>
                    <div class="carrello-item-totale">€${totaleProdotto}</div>
                    <div class="carrello-item-azioni">
                        <button class="btn-rimuovi">Rimuovi</button>
                    </div>
                </div>
            `;
        });

        html += `
            <div class="carrello-totale">
                <strong>Totale: €${totaleGenerale.toFixed(2)}</strong>
            </div>
            <form action="/checkout" method="get">
                <button type="submit" class="btn-checkout">
                    Vai al checkout
                </button>
            </form>
            <button id="btn-svuota-carrello">Svuota Carrello</button>
        `;

        container.innerHTML = html;

        // Aggiungi event listener per aggiornare quantità
        document.querySelectorAll('.quantita-input').forEach(input => {
            input.addEventListener('change', async (e) => {
                const newQuantita = parseInt(e.target.value);
                if (isNaN(newQuantita) || newQuantita < 1) {
                    alert("La quantità deve essere maggiore di 0");
                    mostraCarrello(); // Ricarica il carrello per ripristinare i valori corretti
                    return;
                }
                const prodottoId = e.target.closest('.carrello-item').dataset.id;
                await aggiornaQuantita(prodottoId, newQuantita);
            });
        });

        // Event listener per rimuovere prodotto
        document.querySelectorAll('.btn-rimuovi').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const prodottoId = e.target.closest('.carrello-item').dataset.id;
                await rimuoviProdotto(prodottoId);
                mostraCarrello();
                updateCartCounter();
            });
        });

        // Event listener per svuotare carrello
        const svuotaBtn = document.getElementById('btn-svuota-carrello');
        if (svuotaBtn) {
            svuotaBtn.addEventListener('click', async () => {
                if (confirm("Sei sicuro di voler svuotare il carrello?")) {
                    await svuotaCarrello();
                    mostraCarrello();
                    updateCartCounter();
                }
            });
        }

    } catch (error) {
        container.innerHTML = `<p>Errore nel caricamento del carrello: ${error.message}</p>`;
        console.error(error);
    }
}

// Funzione per aggiungere un prodotto al carrello (da usare ad esempio nelle pagine prodotto)
async function aggiungiAlCarrello(prodottoId) {
    try {
        const formData = new FormData();
        formData.append("quantita", 1);

        const response = await fetch(`/carrello/aggiungi/${prodottoId}`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) throw new Error("Errore durante l'aggiunta al carrello");

        alert("Articolo aggiunto al carrello!");
        updateCartCounter();

    } catch (error) {
        alert("Impossibile aggiungere l'articolo: " + error.message);
    }
}

// Funzione per aggiornare la quantità di un prodotto nel carrello
async function aggiornaQuantita(prodottoId, quantita) {
    try {
        if (quantita <= 0) {
            alert("La quantità deve essere maggiore di 0");
            mostraCarrello(); // Ricarica il carrello per ripristinare i valori corretti
            return;
        }

        const response = await fetch(`/carrello/aggiorna/${prodottoId}`, {
            method: "POST",
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `quantita=${quantita}`
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: "Errore sconosciuto" }));
            throw new Error(errorData.detail || "Errore durante l'aggiornamento della quantità");
        }

        // Se l'aggiornamento ha successo, aggiorna l'interfaccia
        await mostraCarrello();
        await updateCartCounter();
    } catch (error) {
        console.error("Errore nell'aggiornamento della quantità:", error);
        alert(error.message || "Impossibile aggiornare la quantità");
        mostraCarrello(); // Ricarica il carrello per ripristinare i valori corretti
    }
}

// Funzione per rimuovere un prodotto dal carrello
async function rimuoviProdotto(prodottoId) {
    try {
        const response = await fetch(`/carrello/rimuovi/${prodottoId}`, {
            method: "POST"
        });

        if (!response.ok) throw new Error("Errore durante la rimozione del prodotto");
    } catch (error) {
        alert("Impossibile rimuovere il prodotto: " + error.message);
    }
}

// Funzione per svuotare il carrello
async function svuotaCarrello() {
    try {
        const response = await fetch(`/carrello/svuota`, {
            method: "POST"
        });

        if (!response.ok) throw new Error("Errore durante lo svuotamento del carrello");
    } catch (error) {
        alert("Impossibile svuotare il carrello: " + error.message);
    }
}


// Esegui all'avvio solo se siamo nella pagina carrello
document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("carrello-container")) {
        mostraCarrello();
    }
    updateCartCounter();
});
