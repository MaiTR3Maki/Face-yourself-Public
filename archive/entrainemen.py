import cv2
import numpy as np
from PIL import Image
import os

# --- Configuration ---
# Le chemin vers le dossier contenant les sous-dossiers numériques (1, 2, etc.)
path = 'dataset'

# Le classifieur pour la détection de visage (Haar Cascade)
face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Le modèle de reconnaissance à entraîner (LBPH)
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Fonction pour obtenir les images et les IDs
def getImagesAndLabels(path):
    # Liste de tous les chemins d'images dans le dossier 'dataset' et ses sous-dossiers
    imagePaths = [os.path.join(root, file)
                  for root, dirs, files in os.walk(path)
                  for file in files if file.endswith(('jpg', 'png'))]
    
    faceSamples = []  # Pour stocker les échantillons de visage (ROI)
    ids = []          # Pour stocker les IDs (labels numériques)

    print("Début du traitement des images...")

    for imagePath in imagePaths:
        # Lire l'image en niveaux de gris
        PIL_img = Image.open(imagePath).convert('L')
        # Convertir en tableau numpy
        img_numpy = np.array(PIL_img, 'uint8')

        # L'ID est le nom du dossier parent (ID numérique)
        # os.path.split(imagePath)[0] donne le chemin du dossier
        # os.path.basename(...) donne le nom final du dossier (l'ID)
        id = int(os.path.basename(os.path.split(imagePath)[0]))

        # Détecter les visages sur cette image
        faces = face_classifier.detectMultiScale(img_numpy, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        # Pour chaque visage détecté :
        for (x, y, w, h) in faces:
            # Extraire la région d'intérêt (ROI)
            faceSamples.append(img_numpy[y:y + h, x:x + w])
            ids.append(id)
            
            # (Optionnel) Afficher le visage détecté pour vérifier
            # cv2.imshow("Processing Face", img_numpy[y:y + h, x:x + w])
            # cv2.waitKey(1)

    print(f"Fin du traitement. {len(faceSamples)} échantillons de visage trouvés.")
    # cv2.destroyAllWindows()
    return faceSamples, ids

# --- Processus d'Entraînement ---
print("\n[INFO] Entraînement du modèle. Veuillez patienter...")
faces, ids = getImagesAndLabels(path)

# Entraîner le modèle LBPH
recognizer.train(faces, np.array(ids))

# Sauvegarder le modèle entraîné dans le fichier trainer.yml
recognizer.write('trainer.yml')

print(f"\n[INFO] {len(np.unique(ids))} identités uniques entraînées.")
print("[INFO] Modèle sauvegardé avec succès sous 'trainer.yml'")