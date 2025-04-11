# 🔐 Projet FPGA - Sécurité & Cryptographie ECG

*Ce projet a pour but de concevoir et compléter des outils de cryptage utilisant l’algorithme **ASCON-128** pour chiffrer, déchiffrer et analyser une trace ECG (électrocardiogramme). L’implémentation est réalisée sur une carte **FPGA PYNQ-Z2**, et une **API Python** permet de piloter l’ensemble du système.*

---

## 👥 Collaborateurs

- Hugo **CELARIE**  
- Pablo **COLIN**

---

## 🗂️ Organisation

L'API est composée de **trois programmes Python** et d’un fichier **`.log`** :

- Le fichier **`.log`** contient un historique des actions menées.
- **`ascon_pcsn.py`** contient des fonctions permettant de **crypter** et **décrypter** une trace ECG avec **ASCON-128**.
- **`fpga.py`** contient une classe `FPGA` avec des fonctions associées, ainsi qu’une fonction pour lire les fichiers `.csv` et stocker les données de manière exploitable.
- **`main.py`** contient les fonctions pour **afficher** et **détecter les pics PQRST** sur la trace ECG.

---

## ⚙️ Manuel d'Utilisation

### ✅ Prérequis

Avant de démarrer, vous devez disposer des éléments suivants :

- **Python ≥ 3.13** (utilisation d’un environnement virtuel recommandée)
- **Carte FPGA PYNQ-Z2**
- **Outil de synthèse et de programmation** compatible, tel que **Xilinx Vivado 2024.1**
- **Module UART** recommandé : `Digilent Pmod USBUART`
- Une trace ECG :
  - En **hexadécimal**
  - Placée dans la **première colonne** d’un fichier `.csv`
  - D’une longueur maximale de **362 caractères hexadécimaux** (soit 181 octets)
  - Si la trace est plus longue, poursuivre sur la **ligne suivante**, dans la même colonne, en complétant avec des `0` si nécessaire

---

### 🔧 Mise en Place

1. **Branchement matériel :**
   - Connecter le **Pmod USBUART** à la carte FPGA sur les broches **PMODA (1 à 6)**
   - Brancher la carte FPGA et le module UART à votre ordinateur

2. **Implémentation FPGA :**
   - Ouvrir le projet dans **Vivado 2024.1**
   - Importer les fichiers `.sv` et `.xdc`
   - Synthétiser le projet et programmer la carte PYNQ-Z2 :
     - Dans Vivado :
       1. Pour générer un bitstream : cliquez sur `Generate Bitstream` → `Open Target` → `Auto Connect`
       2. Cliquez sur `Program Device` → **Sélectionner la carte**

3. **Vérification du baud rate :**
   - L’UART communique à un baud rate de `115200 bit/s`. Vérifiez que les 3 LED vertes (LED0, LED1 et LED2) sont bien **allumées**.  
     Si ce n’est pas le cas, mettez les 2 switchs (SW0 et SW1) à l’état **bas**.

4. **Lancement de l’environnement Python :**
   - Assurez-vous que toutes les dépendances sont installées
   - Lancez le script principal

5. **En cas d'erreur :**
   - Lancez les autres fichiers `.py` manuellement pour identifier l'origine du problème
   - Vérifiez les versions des bibliothèques installées

---

## 🌐 Utilisation de l’API

L’API est accessible directement en exécutant le fichier `main.py`.

✅ **Avant de lancer le programme**, assurez-vous que :
- L’implémentation matérielle sur la carte **FPGA PYNQ-Z2** est correctement programmée
- Le module **USB-UART** est bien connecté à la carte et à l’ordinateur

---

### ⚙️ Fonctionnement Général

Le script principal exécute deux fonctions :

- `init_ascon()` : initialise les paramètres de cryptage (clé, nonce, données associées)
- `init_graph()` : récupère, chiffre, déchiffre et affiche dynamiquement les signaux ECG

---

### 📊 Affichage Graphique

La fonction `init_graph()` lit les traces ECG à partir d’un fichier `.csv` et les affiche dynamiquement **en temps réel** sous forme de **deux courbes côte à côte** (reliées entre elles) :

- **ECG original** (non chiffré)
- **ECG déchiffré** (après chiffrement et déchiffrement ASCON)

Des points colorés indiquent les différentes ondes **PQRST** du signal :

| Onde | Couleur   |
|------|-----------|
| P    | 🔵 Bleu    |
| Q    | 🟦 Cyan    |
| R    | 🟢 Vert    |
| S    | 🟣 Magenta |
| T    | 🟡 Jaune   |

---

### 🖥️ Affichage Terminal

Dans le terminal, vous verrez les échanges entre le programme Python et la carte FPGA :

- Après chaque envoi d’un paramètre, la carte renvoie **`OK\n`**
- Les données envoyées sont affichées :
  - En **hexadécimal** : après `Sent:`
  - En **commande brute** : après `message: b'...'`

---

### 🔧 Modifier les Paramètres de Cryptage

Les paramètres de cryptage sont configurés dans la fonction `init_ascon()` :

| Paramètre        | Type  | Description |
|------------------|-------|-------------|
| `key_hexa`       | `str` | Clé de chiffrement (16 octets en hexadécimal) |
| `nonce_hexa`     | `str` | Nonce ASCON (16 octets en hexadécimal) |
| `associateddata` | `str` | Données associées (6 octets en hexadécimal) |
| `chemin_fichier` | `str` | Chemin relatif vers le fichier `.csv` contenant les traces ECG |
| `nom_colonne`    | `str` | Nom de la colonne contenant les données ECG dans le fichier |
| `port`           | `str` | Port UART utilisé (ex. : `"COM5"` ou `"ttyUSB0"`). Si `None`, le port est détecté automatiquement. Si le port est marqué comme occupé, débranchez et rebranchez l’UART. |

---

## 🧾 Log


---

## 📚 Références

1. [Manuel utilisateur de la PYNQ-Z2](https://www.mouser.com/datasheet/2/744/pynqz2_user_manual_v1_0-1525725.pdf)  
2. [Fiche technique - Digilent Pmod USBUART](https://digilent.com/reference/_media/pmod:pmod:pmodusbuart_rm.pdf)  
3. [Article sur l’algorithme ASCON - J3EA](https://www.j3ea.org/articles/j3ea/pdf/2022/01/j3ea221004.pdf)  
4. [Xilinx Vivado Design Suite](https://www.amd.com/fr/products/software/adaptive-socs-and-fpgas/vivado.html)

---