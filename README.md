![ebloc](https://github.com/user-attachments/assets/cf86528b-b474-4d4a-a068-f539d2c7d7fb)

# 🏠 Integrarea E-bloc.ro pentru Home Assistant

Integrarea **E-bloc.ro** permite utilizatorilor să afișeze și să monitorizeze informații despre apartamentul lor direct din platforma [E-bloc.ro](https://www.e-bloc.ro) în Home Assistant. Aceasta oferă senzori pentru detalii despre client, indexurile de consum și plățile efectuate.

---

## 📋 Funcționalități

### 🧑‍💻 **Senzor Detalii Client (`Date client`)**
- Afișează informații despre client și apartament.
- **Atribute disponibile:**
  - `Cod client` – Codul unic al clientului.
  - `Apartament` – Numărul apartamentului asociat.
  - `Persoane declarate` – Numărul de persoane declarate în apartament.
  - `Datorie` – Suma restantă de plată (în RON).
  - `Ultima zi de plată` – Termenul limită pentru plata datoriei.
  - `Contor trimis` – Starea trimiterii indexului de consum (Da/Nu).
  - `Începere citire contoare` – Data de început pentru citirea contoarelor.
  - `Încheiere citire contoare` – Data de final pentru citirea contoarelor.
  - `Luna cu datoria cea mai veche` – Luna celei mai vechi datorii.
  - `Luna afișată` – Luna curentă afișată în interfață.
  - `Nivel restanță` – Gradul acumulării datoriilor.

### 📊 **Senzor Index Contor (`Index contor`)**
- Afișează informațiile despre consumul de utilități.
- **Atribute disponibile:**
  - `Index vechi` – Indexul precedent (în mc).
  - `Index nou` – Indexul curent (în mc).

### 💳 **Senzor Plăți și Chitanțe (`Plăți și chitanțe`)**
- Afișează informațiile despre plățile efectuate.
- **Atribute disponibile:**
  - `Număr total de chitanțe` – Numărul total de plăți înregistrate.
  - Detalii pentru fiecare chitanță:
    - `Chitanță` – Numărul chitanței.
    - `Data` – Data plății.
    - `Sumă plătită` – Suma achitată (în RON).

---

## 🛠️ Configurare

### 1️⃣ Instalare
### 💡 Instalare prin HACS:
1. Adaugă [depozitul personalizat](https://github.com/cnecrea/e-bloc) în HACS. 🛠️
2. Caută integrarea **Integrare pentru e-bloc.ro** și instaleaz-o. ✅
3. Repornește Home Assistant și configurează integrarea. 🔄

### ✋ Instalare manuală:
1. Clonează sau descarcă [depozitul GitHub](https://github.com/cnecrea/e-bloc). 📂
2. Copiază folderul `custom_components/e-bloc` în directorul `custom_components` al Home Assistant. 🗂️
3. Repornește Home Assistant și configurează integrarea. 🔧

---



### 2️⃣ Adăugare în Home Assistant
1. Mergeți la **Settings** > **Devices & Services** > **Add Integration**.
2. Căutați `E-bloc.ro` și completați datele de autentificare:
   - **Utilizator**: Email-ul asociat contului E-bloc.ro.
   - **Parolă**: Parola contului.
   - **ID Asociație**: ID-ul asociației de locatari (găsit în contul E-bloc.ro).
   - **ID Apartament**: ID-ul apartamentului (disponibil în contul E-bloc.ro).

---

## 🖼️ Prezentare

### Exemplu senzori:

**Detalii Client:**
```yaml
Cod client: AXXXXF
Apartament: 22
Persoane declarate: 2
Datorie: 221.75 RON
Ultima zi de plată: 2025-01-12
Contor trimis: Nu
```

**Index Contor:**
```yaml
Index vechi: 169 mc
Index nou: 172 mc
```

**Plăți și Chitanțe:**
```yaml
Număr total de chitanțe: 2

Chitanță: 43XXXXXXXXXX
Data: 2024-11-27
Sumă plătită: 262.51 RON

Chitanță: 43XXXXXXXXXX
Data: 2024-10-30
Sumă plătită: 213.60 RON
```

---

## 🔄 Actualizări
Integrarea se actualizează automat la fiecare 5 minute pentru a sincroniza cele mai recente date de pe platforma E-bloc.ro.

---

## ✍️ Autor
Această integrare a fost creată pentru utilizarea personală a datelor din platforma E-bloc.ro în Home Assistant. 

---

## 🧑‍💻 Contribuții
Contribuțiile sunt binevenite! Simte-te liber să trimiți un pull request sau să raportezi probleme [aici](https://github.com/cnecrea/e-bloc/issues).

---

## 🌟 Suport
Dacă îți place această integrare, oferă-i un ⭐ pe [GitHub](https://github.com/cnecrea/e-bloc/)! 😊

---

## 📜 Licență
Distribuit sub licența [MIT](LICENSE).
