-- phpMyAdmin SQL Dump
-- version 5.1.2
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Creato il: Mag 25, 2025 alle 17:53
-- Versione del server: 5.7.24
-- Versione PHP: 8.3.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `supermercato`
--

-- --------------------------------------------------------

--
-- Struttura della tabella `carrello`
--

CREATE TABLE `carrello` (
  `id_carrello` int(11) NOT NULL,
  `id_utente` int(11) NOT NULL,
  `id_prodotto` int(11) NOT NULL,
  `quantita` int(11) NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dump dei dati per la tabella `carrello`
--

INSERT INTO `carrello` (`id_carrello`, `id_utente`, `id_prodotto`, `quantita`) VALUES
(12, 2, 1, 1),
(14, 4, 1, 1);

-- --------------------------------------------------------

--
-- Struttura della tabella `dettagli_ordine`
--

CREATE TABLE `dettagli_ordine` (
  `id_dettaglio` int(11) NOT NULL,
  `id_ordine` int(11) NOT NULL,
  `id_prodotto` int(11) NOT NULL,
  `quantita` int(11) NOT NULL,
  `prezzo_unitario` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dump dei dati per la tabella `dettagli_ordine`
--

INSERT INTO `dettagli_ordine` (`id_dettaglio`, `id_ordine`, `id_prodotto`, `quantita`, `prezzo_unitario`) VALUES
(1, 1, 2, 2, '250.00'),
(2, 1, 6, 1, '5.00'),
(3, 1, 10, 1, '500.00'),
(4, 1, 8, 1, '450.00'),
(5, 2, 10, 1, '500.00'),
(6, 2, 11, 1, '500.00'),
(7, 3, 9, 2, '80.00'),
(8, 3, 10, 1, '500.00'),
(9, 4, 11, 2, '500.00'),
(10, 4, 10, 1, '500.00'),
(11, 4, 9, 1, '80.00'),
(12, 5, 11, 1, '500.00'),
(13, 5, 10, 1, '500.00'),
(14, 5, 9, 1, '80.00'),
(15, 6, 11, 2, '500.00'),
(16, 6, 8, 1, '450.00'),
(17, 6, 7, 1, '30.00'),
(18, 6, 9, 1, '80.00'),
(19, 6, 10, 1, '500.00'),
(20, 6, 6, 1, '5.00'),
(21, 6, 2, 1, '250.00');

-- --------------------------------------------------------

--
-- Struttura della tabella `ordini`
--

CREATE TABLE `ordini` (
  `id_ordine` int(11) NOT NULL,
  `id_utente` int(11) NOT NULL,
  `data_ordine` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `totale` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dump dei dati per la tabella `ordini`
--

INSERT INTO `ordini` (`id_ordine`, `id_utente`, `data_ordine`, `totale`) VALUES
(1, 5, '2025-05-25 15:59:12', '1455.00'),
(2, 5, '2025-05-25 15:59:46', '1000.00'),
(3, 5, '2025-05-25 16:15:32', '660.00'),
(4, 6, '2025-05-25 16:50:34', '1580.00'),
(5, 7, '2025-05-25 16:56:52', '1080.00'),
(6, 8, '2025-05-25 17:11:19', '2315.00');

-- --------------------------------------------------------

--
-- Struttura della tabella `prodotti`
--

CREATE TABLE `prodotti` (
  `id_prodotto` int(11) NOT NULL,
  `nome` varchar(200) NOT NULL,
  `descrizione` text,
  `prezzo` decimal(10,2) NOT NULL,
  `quantita_disponibile` int(11) DEFAULT '0',
  `immagine_url` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dump dei dati per la tabella `prodotti`
--

INSERT INTO `prodotti` (`id_prodotto`, `nome`, `descrizione`, `prezzo`, `quantita_disponibile`, `immagine_url`) VALUES
(1, 'cuffia', 'cuffia multi uso', '50.00', 10, '../static/images/download.jpg'),
(2, 'watch', 'apple watch', '250.00', 17, '../static/images/h3.png'),
(3, 'portatile', 'hp', '600.00', 20, '../static/images/h2.png'),
(4, 'webcam', 'webcam', '20.00', 50, '../static/images/h5.png'),
(6, 'cuffie', 'con cavo', '5.00', 18, '../static/images/h4.jpg'),
(7, 'mouse', 'wireless', '30.00', 9, '../static/images/p2.png'),
(8, 'portatile', 'hp', '450.00', 8, '../static/images/p3.png'),
(9, 'cuffie', 'sony', '80.00', 5, '../static/images/p4.png'),
(10, 'fotocamera', 'canon', '500.00', 4, '../static/images/p5.png'),
(11, 'ps5', 'console', '500.00', 4, '../static/images/p6.png');

-- --------------------------------------------------------

--
-- Struttura della tabella `utenti`
--

CREATE TABLE `utenti` (
  `id_utente` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `ruolo` enum('cliente','dipendente','admin','fornitore') DEFAULT 'cliente'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dump dei dati per la tabella `utenti`
--

INSERT INTO `utenti` (`id_utente`, `username`, `email`, `password`, `ruolo`) VALUES
(1, 'admin', 'admin@supermercato.com', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin'),
(2, 'cliente1', 'cliente@test.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'cliente'),
(4, 'dipend', 'dip@dip', 'b133a0c0e9bee3be20163d2ad31d6248db292aa6dcb1ee087a2aa50e0fc75ae2', 'dipendente'),
(5, 'jan', 'jan@jan', 'b133a0c0e9bee3be20163d2ad31d6248db292aa6dcb1ee087a2aa50e0fc75ae2', 'cliente'),
(6, 'pat', 'bernaciak.patryk@einaudicorreggio.it', '598df83951da3ed6984fcb3129042c8c6fabfb7bbca6cf02fd2df15c05e71138', 'cliente'),
(7, 'pat2', 'bernaciakpatryk0@gmail.com', '0414530a84a89ce3f1d693f0376570be8cc1177bee503027cbf15d4a79d9a9f5', 'cliente'),
(8, 'luca', 'canovi.luca@einaudicorreggio.it', 'b04e95d0b09d1c3846dc2c1df871b44c780a47844534e36cfee5212f181660ae', 'cliente');

--
-- Indici per le tabelle scaricate
--

--
-- Indici per le tabelle `carrello`
--
ALTER TABLE `carrello`
  ADD PRIMARY KEY (`id_carrello`),
  ADD UNIQUE KEY `unique_user_product` (`id_utente`,`id_prodotto`),
  ADD KEY `id_prodotto` (`id_prodotto`);

--
-- Indici per le tabelle `dettagli_ordine`
--
ALTER TABLE `dettagli_ordine`
  ADD PRIMARY KEY (`id_dettaglio`),
  ADD KEY `id_ordine` (`id_ordine`),
  ADD KEY `id_prodotto` (`id_prodotto`);

--
-- Indici per le tabelle `ordini`
--
ALTER TABLE `ordini`
  ADD PRIMARY KEY (`id_ordine`),
  ADD KEY `id_utente` (`id_utente`);

--
-- Indici per le tabelle `prodotti`
--
ALTER TABLE `prodotti`
  ADD PRIMARY KEY (`id_prodotto`);

--
-- Indici per le tabelle `utenti`
--
ALTER TABLE `utenti`
  ADD PRIMARY KEY (`id_utente`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT per le tabelle scaricate
--

--
-- AUTO_INCREMENT per la tabella `carrello`
--
ALTER TABLE `carrello`
  MODIFY `id_carrello` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=35;

--
-- AUTO_INCREMENT per la tabella `dettagli_ordine`
--
ALTER TABLE `dettagli_ordine`
  MODIFY `id_dettaglio` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- AUTO_INCREMENT per la tabella `ordini`
--
ALTER TABLE `ordini`
  MODIFY `id_ordine` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT per la tabella `prodotti`
--
ALTER TABLE `prodotti`
  MODIFY `id_prodotto` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT per la tabella `utenti`
--
ALTER TABLE `utenti`
  MODIFY `id_utente` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- Limiti per le tabelle scaricate
--

--
-- Limiti per la tabella `carrello`
--
ALTER TABLE `carrello`
  ADD CONSTRAINT `carrello_ibfk_1` FOREIGN KEY (`id_utente`) REFERENCES `utenti` (`id_utente`) ON DELETE CASCADE,
  ADD CONSTRAINT `carrello_ibfk_2` FOREIGN KEY (`id_prodotto`) REFERENCES `prodotti` (`id_prodotto`) ON DELETE CASCADE;

--
-- Limiti per la tabella `dettagli_ordine`
--
ALTER TABLE `dettagli_ordine`
  ADD CONSTRAINT `dettagli_ordine_ibfk_1` FOREIGN KEY (`id_ordine`) REFERENCES `ordini` (`id_ordine`) ON DELETE CASCADE,
  ADD CONSTRAINT `dettagli_ordine_ibfk_2` FOREIGN KEY (`id_prodotto`) REFERENCES `prodotti` (`id_prodotto`);

--
-- Limiti per la tabella `ordini`
--
ALTER TABLE `ordini`
  ADD CONSTRAINT `ordini_ibfk_1` FOREIGN KEY (`id_utente`) REFERENCES `utenti` (`id_utente`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
