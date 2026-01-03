import cv2
import numpy as np

# --- 1. CONFIGURATION ET CHARGEMENT DU CLASSIFIEUR ---

face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# --- 2. CHARGEMENT DU MODÈLE DE RECONNAISSANCE (LBPH) ---
# Vous devez entraîner ce modèle (trainer.yml) au préalable
recognizer = cv2.face.LBPHFaceRecognizer_create()
try:
    # Assurez-vous que ce fichier existe après votre phase d'entraînement
    recognizer.read("trainer.yml")
except cv2.error:
    print("Erreur: Le fichier 'trainer.yml' n'a pas été trouvé. Veuillez l'entraîner d'abord.")
    exit()

# Dictionnaire pour mapper les IDs numériques aux noms (ou statut)
# Exemple: {1: "Jean (AUTORISÉ)", 2: "Marie (AUTORISÉE)"}
names = {
    0: "INCONNU",  # ID 0 est souvent utilisé pour les visages non entraînés
    1: "Lucas Rauzy",
    2: "Stagiaire (AUTORISÉ)",
    # Ajoutez d'autres noms/IDs ici
}

video_capture = cv2.VideoCapture(0)

# --- 3. FONCTION DE DÉTECTION ET D'IDENTIFICATION ---
def recognize_face(vid):
    gray_image = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)
    faces = face_classifier.detectMultiScale(
        gray_image, 1.1, 5, minSize=(40, 40)
    )

    for (x, y, w, h) in faces:
        # Dessiner le rectangle de détection
        cv2.rectangle(vid, (x, y), (x + w, y + h), (0, 255, 0), 4)

        # Région d'intérêt pour la reconnaissance
        roi_gray = gray_image[y:y + h, x:x + w]
        
        # Reconnaissance : prédire l'ID et le niveau de confiance
        # confidence est un score: plus il est bas, plus la confiance est haute
        id_, confidence = recognizer.predict(roi_gray)

        # Définir le seuil d'autorisation (par exemple, un score de confiance inférieur à 70)
        threshold = 70 

        if confidence < threshold:
            name = names[id_]
            color = (0, 255, 0) # Vert pour Autorisé
            status = "AUTORISÉ"
        else:
            name = "Inconnu"
            color = (0, 0, 255) # Rouge pour Non Autorisé
            status = "NON AUTORISÉ"
            
        # Mettre à jour l'affichage
        cv2.rectangle(vid, (x, y), (x + w, y + h), color, 4)
        
        # Afficher le nom et le statut
        label = f"{name} ({status}) - Confiance: {round(confidence, 2)}"
        cv2.putText(vid, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    return faces

# --- 4. BOUCLE PRINCIPALE ---
while True:
    result, video_frame = video_capture.read()
    if result is False:
        break

    recognize_face(video_frame)

    cv2.imshow("Authentification Faciale", video_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video_capture.release()
cv2.destroyAllWindows()