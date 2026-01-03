import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import sqlite3
import cv2
import numpy as np
import os

# --- 1. CONFIGURATION DE LA BASE DE DONNÉES ET DES CONSTANTES ---

# Connexion à la base de données SQLite
conn = sqlite3.connect('eleves.db')
c = conn.cursor()

# Création de la table des élèves
c.execute('''CREATE TABLE IF NOT EXISTS eleves
                (id INTEGER PRIMARY KEY, 
                 nom TEXT NOT NULL, 
                 prenom TEXT NOT NULL, 
                 credit REAL DEFAULT 0.0)''')
conn.commit()

# Coût du repas (à ajuster)
COUT_REPAS = 5.00

# --- 2. CONFIGURATION DE LA RECONNAISSANCE FACIALE (LBPH) ---

face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Initialisation du reconnaisseur LBPH
recognizer = cv2.face.LBPHFaceRecognizer_create()
MODEL_FILE = "trainer.yml"

try:
    recognizer.read(MODEL_FILE)
    print(f"[INFO] Modèle de reconnaissance '{MODEL_FILE}' chargé.")
except cv2.error:
    # Le programme continuera, mais la reconnaissance ne fonctionnera pas
    # Il faudra ajouter un message d'erreur plus visible dans la fonction
    print(f"[ERREUR] Le fichier '{MODEL_FILE}' n'a pas été trouvé. Lancez l'entraînement !")
    # On désactive la reconnaissance si le modèle n'est pas là
    recognizer = None 


ID_TO_NAME = {} 
ID_TO_DB_ID = {} # Un mapping direct si l'ID du modèle est l'ID de la DB

def load_names_from_db():
    global ID_TO_NAME, ID_TO_DB_ID
    c.execute("SELECT id, prenom, nom FROM eleves")
    results = c.fetchall()
    
    # On suppose que l'ID du modèle LBPH est le même que l'ID de la DB.
    # Si ce n'est pas le cas, ce mapping doit être ajusté.
    ID_TO_NAME = {row[0]: f"{row[1]} {row[2]}" for row in results}
    ID_TO_DB_ID = {row[0]: row[0] for row in results} # ID modèle -> ID DB
    ID_TO_NAME[0] = "INCONNU" # ID 0 pour les non-reconnus

load_names_from_db()

# --- 3. FONCTIONS DE GESTION DE LA BASE DE DONNÉES (TKINTER) ---

def ajouter_eleve():
    nom = simpledialog.askstring("Nom", "Entrez le nom de l'élève:")
    prenom = simpledialog.askstring("Prénom", "Entrez le prénom de l'élève:")
    if nom and prenom:
        c.execute("INSERT INTO eleves (nom, prenom) VALUES (?, ?)", (nom, prenom))
        conn.commit()
        # Rechargez les noms après l'ajout
        load_names_from_db()
        messagebox.showinfo("Succès", f"Élève {prenom} {nom} ajouté avec succès! ID: {c.lastrowid}")
    else:
        messagebox.showwarning("Erreur", "Le nom et le prénom ne peuvent pas être vides.")

def ajouter_credit():
    eleve_id = simpledialog.askinteger("ID Élève", "Entrez l'ID de l'élève:")
    montant = simpledialog.askfloat("Montant", "Entrez le montant à ajouter:")
    if eleve_id and montant is not None and montant > 0:
        c.execute("UPDATE eleves SET credit = credit + ? WHERE id = ?", (montant, eleve_id))
        conn.commit()
        if c.rowcount > 0:
            messagebox.showinfo("Succès", f"{montant:.2f} € ajouté au crédit de l'élève ID {eleve_id}.")
        else:
            messagebox.showwarning("Erreur", "Élève non trouvé.")
    else:
        messagebox.showwarning("Erreur", "ID et montant valides requis.")

def afficher_credit():
    eleve_id = simpledialog.askinteger("ID Élève", "Entrez l'ID de l'élève:")
    if eleve_id:
        c.execute("SELECT nom, prenom, credit FROM eleves WHERE id = ?", (eleve_id,))
        result = c.fetchone()
        if result:
            nom, prenom, credit = result
            messagebox.showinfo("Crédit Élève", f"Élève: {prenom} {nom}\nCrédit: {credit:.2f} €")
        else:
            messagebox.showwarning("Erreur", "Élève non trouvé.")
    else:
        messagebox.showwarning("Erreur", "L'ID de l'élève ne peut pas être vide.")

def debiter_credit(db_id, montant):
    c.execute("SELECT nom, prenom, credit FROM eleves WHERE id = ?", (db_id,))
    result = c.fetchone()
    
    if result:
        nom, prenom, credit = result
        if credit >= montant:
            c.execute("UPDATE eleves SET credit = credit - ? WHERE id = ?", (montant, db_id))
            conn.commit()
            messagebox.showinfo("Transaction Réussie", 
                                f"{prenom} {nom} identifié(e) et débité(e) de {montant:.2f} €.\nNouveau Crédit: {credit - montant:.2f} €")
            return True
        else:
            messagebox.showerror("Crédit Insuffisant", 
                                 f"{prenom} {nom} n'a pas assez de crédit.\nCrédit actuel: {credit:.2f} €.")
            return False
    else:
        messagebox.showwarning("Erreur", f"Élève ID {db_id} non trouvé dans la base de données.")
        return False

# --- 4. FONCTION DE RECONNAISSANCE FACIALE ET DÉBIT (COEUR DU PROJET) ---

def scanner_et_debiter():
    if recognizer is None:
        messagebox.showerror("Erreur Modèle", "Le modèle de reconnaissance (trainer.yml) n'a pas été chargé.")
        return

    video_capture = cv2.VideoCapture(0)
    identified_id = None
    
    # Le message qui s'affiche à l'écran
    status_text = "Veuillez vous positionner devant la caméra..."
    
    # Boucle de détection/reconnaissance
    while True:
        result, video_frame = video_capture.read()
        if not result:
            break

        gray_image = cv2.cvtColor(video_frame, cv2.COLOR_BGR2GRAY)
        
        # Détection (avec des paramètres plus stricts pour éviter les doubles détections)
        faces = face_classifier.detectMultiScale(
            gray_image, 
            scaleFactor=1.1, 
            minNeighbors=8, 
            minSize=(80, 80)
        )

        for (x, y, w, h) in faces:
            roi_gray = gray_image[y:y + h, x:x + w]
            
            # Prédiction
            id_model, confidence = recognizer.predict(roi_gray)
            threshold = 75 # Seuil d'acceptation légèrement ajusté
            
            # --- Décision ---
            if confidence < threshold and id_model in ID_TO_DB_ID:
                identified_name = ID_TO_NAME[id_model]
                identified_id = ID_TO_DB_ID[id_model]
                color = (0, 255, 0) # Vert
                status_text = f"Identifié: {identified_name}. Conf: {round(confidence, 2)}"
                
                # Option : Arrêter la boucle après une identification réussie
                # break 
            else:
                identified_name = ID_TO_NAME.get(id_model, "INCONNU")
                identified_id = None
                color = (0, 0, 255) # Rouge
                status_text = f"NON AUTORISÉ (Inconnu) - Conf: {round(confidence, 2)}"
            
            # Affichage dans la fenêtre OpenCV
            cv2.rectangle(video_frame, (x, y), (x + w, y + h), color, 4)
            cv2.putText(video_frame, status_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Affichage du statut en bas
        cv2.putText(video_frame, status_text, (10, video_frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("Scanner de Cantine (Q pour Debiter ou Echap)", video_frame)

        key = cv2.waitKey(1)
        
        # dès qu'une personne est identifiée sans bouton a presser
        if identified_id is not None:
            # Tenter de débiter le crédit
            debiter_credit(identified_id, COUT_REPAS)
            break

        # Si 'Esc' est pressé ou que l'élève n'est pas identifié mais on veut sortir
        if key & 0xFF == 27: # 27 est la touche Echap (Escape)
            video_capture.release()
            cv2.destroyAllWindows()
            messagebox.showinfo("Annulation", "Scan annulé.")
            return


# --- 5. INTERFACE TKINTER ---

# Création de la fenêtre principale
root = tk.Tk()
root.title("Gestion des Crédits Cantine & Reconnaissance Faciale")

# Titre
tk.Label(root, text="Système de Gestion de Cantine", font=("Arial", 16, "bold")).pack(pady=10)

# Cadre pour les actions d'administration
frame_admin = tk.LabelFrame(root, text="Administration DB", padx=10, pady=10)
frame_admin.pack(pady=10, padx=10, fill="x")

btn_ajouter_eleve = tk.Button(frame_admin, text="1. Ajouter un Élève (Nouvel ID)", command=ajouter_eleve)
btn_ajouter_eleve.pack(pady=5, fill="x")

btn_ajouter_credit = tk.Button(frame_admin, text="2. Ajouter du Crédit", command=ajouter_credit)
btn_ajouter_credit.pack(pady=5, fill="x")

btn_afficher_credit = tk.Button(frame_admin, text="3. Afficher le Crédit", command=afficher_credit)
btn_afficher_credit.pack(pady=5, fill="x")

# Cadre pour l'action principale de cantine
frame_cantine = tk.LabelFrame(root, text="Action Cantine (Coût: 5.00 €)", padx=10, pady=10)
frame_cantine.pack(pady=10, padx=10, fill="x")

btn_scanner_debiter = tk.Button(frame_cantine, text="Scanner le Visage & Débiter", command=scanner_et_debiter, bg="light green", font=("Arial", 12, "bold"))
btn_scanner_debiter.pack(pady=15, fill="x")


# Lancer la boucle principale de l'interface
root.mainloop()

# Fermer la connexion à la base de données lors de la fermeture de l'application
conn.close()