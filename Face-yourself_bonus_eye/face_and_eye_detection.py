import time
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk 
import sqlite3
import cv2
import numpy as np
import os
from PIL import Image

import cvzone
from cvzone.FaceMeshModule import FaceMeshDetector
from cvzone.PlotModule import LivePlot


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

COUT_REPAS = 5.00
DATASET_PATH = 'dataset'
MODEL_FILE = "trainer.yml"

# Classifieur Haar Cascade pour la détection
face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

recognizer = None 

ID_TO_NAME = {0: "INCONNU"} 
ID_TO_DB_ID = {}

def load_names_from_db():
    global ID_TO_NAME, ID_TO_DB_ID
    c.execute("SELECT id, prenom, nom FROM eleves")
    results = c.fetchall()
    
    ID_TO_NAME = {row[0]: f"{row[1]} {row[2]}" for row in results}
    ID_TO_DB_ID = {row[0]: row[0] for row in results}
    ID_TO_NAME[0] = "INCONNU" 

load_names_from_db()

def load_recognizer_model():
    global recognizer
    try:
        if recognizer is None:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(MODEL_FILE)
        print(f"[INFO] Modèle de reconnaissance '{MODEL_FILE}' chargé.")
        return recognizer
    except cv2.error:
        print(f"[ERREUR] Le fichier '{MODEL_FILE}' n'a pas été trouvé ou est corrompu.")
        return None

def ajouter_eleve():
    nom = simpledialog.askstring("Nom", "Entrez le nom de l'élève:")
    prenom = simpledialog.askstring("Prénom", "Entrez le prénom de l'élève:")
    if nom and prenom:
        c.execute("INSERT INTO eleves (nom, prenom) VALUES (?, ?)", (nom, prenom))
        conn.commit()
        last_id = c.lastrowid
        load_names_from_db()
        messagebox.showinfo("Succès", f"Élève {prenom} {nom} ajouté avec succès! ID: {last_id}")
        
        if messagebox.askyesno("Capture d'images", "Voulez-vous lancer la capture d'images pour cet élève (ID : {}) maintenant ?".format(last_id)):
             lancer_capture_images(predefined_id=last_id)
    else:
        messagebox.showwarning("Erreur", "Le nom et le prénom ne peuvent pas être vides.")

def supprimer_eleve():
    id_eleve = simpledialog.askinteger("ID Élève", "Entrez l'ID de l'élève à supprimer:")
    if id_eleve:
        c.execute("SELECT nom, prenom FROM eleves WHERE id = ?", (id_eleve,))
        result = c.fetchone()
        if result:
            nom, prenom = result
            if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer l'élève {prenom} {nom} (ID: {id_eleve}) ?"):
                c.execute("DELETE FROM eleves WHERE id = ?", (id_eleve,))
                conn.commit()
                load_names_from_db()
                messagebox.showinfo("Succès", f"Élève {prenom} {nom} supprimé avec succès.")
        else:
            messagebox.showwarning("Erreur", "Élève non trouvé.")

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


def scanner_et_debiter():
    global recognizer
    if load_recognizer_model() is None:
        messagebox.showerror("Erreur Modèle", "Le modèle de reconnaissance (trainer.yml) est manquant.")
        return

    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        messagebox.showerror("Erreur Caméra", "Impossible d'ouvrir la caméra.")
        return

    # --- CONFIGURATION FACEMESH (Clignement) ---
    detector = FaceMeshDetector(maxFaces=1)
    
    # Points des yeux (MediaPipe)
    idListleft = [22, 23, 24, 26, 110, 157, 158, 159, 160, 161, 130, 243] 
    idListRight = [362, 385, 387, 263, 249, 466, 467, 468, 469, 470, 359, 454]
    
    # Graphique pour visualiser le clignement (optionnel, utile pour le debug)
    plotY = LivePlot(640, 360, [20, 50], invert=True)    
    ratioList = [] # Liste unique pour la moyenne des deux yeux

    blinkCounter = 0
    counter = 0 # Compteur de frames pour le 'debounce' (anti-rebond)
        
    identified_id = None
    status_text = "Positionnez-vous..."
    
    # Stabilisation au démarrage
    STABILIZATION_FRAMES = 100
    frame_loop = 0
    
    while True:
        # Gestion boucle vidéo (sécurité)
        if video_capture.get(cv2.CAP_PROP_POS_FRAMES) == video_capture.get(cv2.CAP_PROP_FRAME_COUNT):
            video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        success, frame = video_capture.read()
        if not success:
            break
            
        frame_loop += 1
        
        img_display = frame.copy()
        
        # --- A. LOGIQUE DE CLIGNEMENT (FACEMESH) ---
        frame, face = detector.findFaceMesh(frame, draw=False)
        
        if face:
            face = face[0]

            pointLeftTemp = face[454]
            pointRightTemp = face[234]
            # w_face est la largeur du visage en pixels
            w_face, _ = detector.findDistance(pointLeftTemp, pointRightTemp)
            
        
            dynamic_threshold = 35 - (w_face / 20)
            
            # Bornes de sécurité pour éviter des valeurs absurdes
            if dynamic_threshold < 28: dynamic_threshold = 28
            if dynamic_threshold > 40: dynamic_threshold = 40
            

            # --- Oeil Gauche ---
            leftUp = face[159]
            leftDown = face[23]
            leftLeft = face[130]
            leftRight = face[243]
            lenghtverL, _ = detector.findDistance(leftUp, leftDown)
            lenghthorL, _ = detector.findDistance(leftLeft, leftRight)
            ratioL = int((lenghtverL / lenghthorL) * 100)

            # --- Oeil Droit ---
            rightUp = face[386]
            rightDown = face[253]
            rightLeft = face[362]
            rightRight = face[454]
            lenghtverR, _ = detector.findDistance(rightUp, rightDown)
            lenghthorR, _ = detector.findDistance(rightLeft, rightRight)
            ratioR = int((lenghtverR / lenghthorR) * 100)

            ratioAvg = (ratioL + ratioR) / 2
            
            ratioList.append(ratioAvg)
            if len(ratioList) > 3:
                ratioList.pop(0)
            ratioSmooth = sum(ratioList) / len(ratioList)

            # --- CONDITION DE CLIGNEMENT AVEC SEUIL DYNAMIQUE ---
            if ratioSmooth < dynamic_threshold and counter == 0:
                blinkCounter += 1
                counter = 1
            
            if counter != 0:
                counter += 1
                if counter > 10:
                    counter = 0    

            cv2.line(img_display, leftUp, leftDown, (0, 200, 0), 2)
            cv2.line(img_display, rightUp, rightDown, (0, 200, 0), 2)

            # Mise à jour graphique...
            imgPlot = plotY.update(ratioSmooth)
            imgPlot = cv2.resize(imgPlot, (300, 200))
            img_display[0:200, 0:300] = imgPlot        # On utilise une conversion propre depuis l'image brute
        gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces_haar = face_classifier.detectMultiScale(
            gray_image, scaleFactor=1.1, minNeighbors=8, minSize=(80, 80)
        )
        
        identified_id = None
        current_color = (255, 255, 255)
        
        for (x, y, w, h) in faces_haar:
            # Ignorer les premières frames pour stabiliser
            if frame_loop < STABILIZATION_FRAMES:
                cv2.rectangle(img_display, (x, y), (x + w, y + h), (0, 165, 255), 2)
                status_text = "Initialisation..."
                continue

            roi_gray = gray_image[y:y + h, x:x + w]
            
            # Prédiction ID 
            id_model, confidence = recognizer.predict(roi_gray)
            threshold = 50
            
            if confidence < threshold and id_model in ID_TO_DB_ID:
                identified_name = ID_TO_NAME[id_model]
                identified_id = ID_TO_DB_ID[id_model]
                current_color = (0, 255, 0) # Vert
                status_text = f"Identifie: {identified_name}. Clignez pour valider."
            else:
                identified_name = "INCONNU"
                current_color = (0, 0, 255) # Rouge
                status_text = "Inconnu"
            
            # Dessin sur l'image finale
            cv2.rectangle(img_display, (x, y), (x + w, y + h), current_color, 4)
            cv2.putText(img_display, identified_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, current_color, 2)

        # Affichage du statut en bas
        cv2.putText(img_display, status_text, (10, img_display.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, current_color, 1)
        
        # Feedback visuel "CLIGNEMENT"
        if counter > 0 and counter < 5: # Affiche pendant quelques frames
             cv2.putText(img_display, "CLIGNEMENT DETECTE !", (320, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

        # Affichage FINAL dans une SEULE fenêtre
        cv2.imshow("Scanner Cantine", img_display)
        
        # --- C. ACTION FINALE : DÉBIT ---
        # Condition : ID reconnu + Clignement actif (counter > 0)
        if identified_id is not None and counter >= 1:
            # Petit délai pour voir le feedback visuel
            cv2.waitKey(500) 
            video_capture.release()
            cv2.destroyAllWindows()
            debiter_credit(identified_id, COUT_REPAS)
            return

        # Quitter avec Echap
        if cv2.waitKey(1) & 0xFF == 27:
            break

    video_capture.release()
    cv2.destroyAllWindows()
    messagebox.showinfo("Annulation", "Scan annulé.")

def getImagesAndLabels(path):
    imagePaths = [os.path.join(root, file)
                  for root, dirs, files in os.walk(path)
                  for file in files if file.endswith(('jpg', 'png'))]
    
    faceSamples = []
    ids = []         

    print("Début du traitement des images...")

    for imagePath in imagePaths:
        try:
            PIL_img = Image.open(imagePath).convert('L')
            img_numpy = np.array(PIL_img, 'uint8')

            id = int(os.path.basename(os.path.split(imagePath)[0]))

            faces = face_classifier.detectMultiScale(img_numpy, scaleFactor=1.1, minNeighbors=8, minSize=(60, 60))

            for (x, y, w, h) in faces:
                faceSamples.append(img_numpy[y:y + h, x:x + w])
                ids.append(id)
        except Exception as e:
            print(f"Erreur lors du traitement de l'image {imagePath}: {e}")

    print(f"Fin du traitement. {len(faceSamples)} échantillons de visage trouvés.")
    return faceSamples, ids

def lancer_entrainement():
    faces, ids = getImagesAndLabels(DATASET_PATH)

    if len(faces) == 0:
        messagebox.showwarning("Entraînement", "Aucune image de visage trouvée dans le dossier 'dataset'.")
        return

    recognizer_trainer = cv2.face.LBPHFaceRecognizer_create()
    recognizer_trainer.train(faces, np.array(ids))

    recognizer_trainer.write(MODEL_FILE)
    
    load_recognizer_model()

    messagebox.showinfo("Entraînement", 
                        f"Entraînement terminé avec {len(np.unique(ids))} identités uniques. Modèle sauvegardé sous '{MODEL_FILE}'")

def lancer_capture_images(predefined_id=None):
    if predefined_id is None:
        eleve_id = simpledialog.askinteger("ID Élève", "Entrez l'ID de l'élève pour la capture d'images :")
        if eleve_id is None or eleve_id == 0:
            return
    else:
        eleve_id = predefined_id

    c.execute("SELECT nom, prenom FROM eleves WHERE id = ?", (eleve_id,))
    if c.fetchone() is None:
        messagebox.showwarning("Erreur ID", f"L'élève avec l'ID {eleve_id} n'existe pas dans la base de données.")
        return
        
    path = os.path.join(DATASET_PATH, str(eleve_id))
    if not os.path.exists(path):
        os.makedirs(path)

    video_capture = cv2.VideoCapture(0)
    image_count = 0 
    frame_count = 0 

    messagebox.showinfo("Capture d'images", f"La capture pour l'ID {eleve_id} va commencer. Placez-vous devant la caméra. Appuyez sur 'q' pour arrêter.")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = face_classifier.detectMultiScale(
            gray_frame, 
            scaleFactor=1.1, 
            minNeighbors=8, 
            minSize=(60, 60)
        )

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
            if frame_count % 5 == 0:
                image_count += 1
                face_img = gray_frame[y:y + h, x:x + w]
                
                file_name = f"{eleve_id}_{image_count}.jpg"
                cv2.imwrite(os.path.join(path, file_name), face_img)
                
                print(f"Image enregistrée : {file_name}")
        
        frame_count += 1 

        cv2.putText(frame, f"ID: {eleve_id} - Captures: {image_count}/30", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow(f'Capture ID: {eleve_id}', frame)

        if cv2.waitKey(1) & 0xFF == ord('q') or image_count >= 30:
            break

    video_capture.release()
    cv2.destroyAllWindows()
    
    if image_count > 0:
         messagebox.showinfo("Capture terminée", f"Capture terminée. {image_count} images sauvegardées pour l'ID {eleve_id}.")
    else:
        messagebox.showwarning("Capture terminée", "Aucune image capturée. Vérifiez la caméra et l'éclairage.")

def afficher_tous_les_eleves():

    liste_window = tk.Toplevel(root)
    liste_window.title("Liste de Tous les Élèves et Crédits")
    liste_window.geometry("500x400") 

    tree = ttk.Treeview(liste_window, columns=("ID", "Prénom", "Nom", "Crédit"), show="headings")
    
    tree.heading("ID", text="ID", anchor=tk.W)
    tree.heading("Prénom", text="Prénom", anchor=tk.W)
    tree.heading("Nom", text="Nom", anchor=tk.W)
    tree.heading("Crédit", text="Crédit (€)", anchor=tk.E)

    tree.column("ID", width=60, stretch=tk.NO) 
    tree.column("Prénom", width=150, anchor=tk.W)
    tree.column("Nom", width=150, anchor=tk.W)
    tree.column("Crédit", width=90, anchor=tk.E)

    c.execute("SELECT id, prenom, nom, credit FROM eleves ORDER BY id ASC")
    eleves = c.fetchall()

    if eleves:
        for row in eleves:
            eleve_id, prenom, nom, credit = row
            formatted_credit = f"{credit:.2f}"
            tree.insert("", tk.END, values=(eleve_id, prenom, nom, formatted_credit))
    else:
        tk.Label(liste_window, text="Aucun élève trouvé dans la base de données.", font=("Arial", 12)).pack(pady=50)

    scrollbar = ttk.Scrollbar(liste_window, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill="both", expand=True, padx=10, pady=10)


# --- 8. INTERFACE TKINTER ---

root = tk.Tk()
root.title("Système de Cantine: DB, Entraînement et Reconnaissance")

tk.Label(root, text="Gestion de Cantine par Reconnaissance Faciale", font=("Arial", 16, "bold")).pack(pady=10)

frame_cantine = tk.LabelFrame(root, text="ACTION CANTINE (Coût: 5.00 €)", padx=10, pady=10)
frame_cantine.pack(pady=10, padx=10, fill="x")

btn_scanner_debiter = tk.Button(frame_cantine, text="SCANNER LE VISAGE & DÉBITER", command=scanner_et_debiter, bg="light green", font=("Arial", 14, "bold"))
btn_scanner_debiter.pack(pady=15, fill="x")

frame_admin = tk.LabelFrame(root, text="Administration & Entraînement", padx=10, pady=10)
frame_admin.pack(pady=10, padx=10, fill="x")

frame_actions = tk.Frame(frame_admin)
frame_actions.pack(fill="x")

col1 = tk.LabelFrame(frame_actions, text="Gestion DB", padx=10, pady=10)
col1.pack(side="left", fill="both", expand=True, padx=10)
btn_ajouter_eleve = tk.Button(col1, text="1. Ajouter un Élève", command=ajouter_eleve)
btn_ajouter_eleve.pack(pady=10, fill="x")
btn_supprimer_eleve = tk.Button(col1, text="2. Supprimer un Élève", command=supprimer_eleve)
btn_supprimer_eleve.pack(pady=10, fill="x")
btn_ajouter_credit = tk.Button(col1, text="3. Ajouter du Crédit", command=ajouter_credit)
btn_ajouter_credit.pack(pady=10, fill="x")
btn_afficher_credit = tk.Button(col1, text="3. Afficher le Crédit", command=afficher_credit)
btn_afficher_credit.pack(pady=10, fill="x")
btn_afficher_eleves = tk.Button(col1, text="Afficher Tous les Élèves", command=afficher_tous_les_eleves)
btn_afficher_eleves.pack(pady=10, fill="x")

col2 = tk.LabelFrame(frame_actions, text="Préparation IA", padx=10, pady=10)
col2.pack(side="left", fill="both", expand=True, padx=10)
btn_capture_images = tk.Button(col2, text="4. Capturer Images Élève", command=lambda: lancer_capture_images())
btn_capture_images.pack(pady=10, fill="x")
btn_entrainer = tk.Button(col2, text="5. Entraîner le Modèle (Créer trainer.yml)", command=lancer_entrainement)
btn_entrainer.pack(pady=10, fill="x")

root.protocol("WM_DELETE_WINDOW", lambda: (conn.close(), root.destroy()))
root.mainloop()

conn.close()