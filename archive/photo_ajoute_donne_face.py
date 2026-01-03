import cv2
import os

# ... (Configuration, face_classifier, etc. reste inchangé) ...

face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
# ATTENTION : Changez cet ID pour chaque personne que vous enregistrez !
face_id = 2
dataset_path = 'dataset'

# Créer le dossier s'il n'existe pas
path = os.path.join(dataset_path, str(face_id))
if not os.path.exists(path):
    os.makedirs(path)

video_capture = cv2.VideoCapture(0)
image_count = 0  # Compteur pour le nombre d'images ENREGISTRÉES (doit aller jusqu'à 30)
frame_count = 0  # Compteur pour le nombre de frames passées (pour la temporisation)

print(f"\n[INFO] Commencez à capturer les images pour l'ID {face_id}. Regardez la caméra...")

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Détecter les visages
    faces = face_classifier.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        # On sauvegarde une image toutes les 5 frames passées
        if frame_count % 5 == 0:
            image_count += 1 # ⬅️ On incrémente le compteur d'images seulement ICI
            # Recadrer la région d'intérêt
            face_img = gray_frame[y:y + h, x:x + w]
            
            # Nom de fichier : ID_Numéro.jpg
            file_name = f"{face_id}_{image_count}.jpg"
            cv2.imwrite(os.path.join(path, file_name), face_img)
            
            print(f"Image enregistrée : {file_name}")
    
    # Incrémenter le compteur de frames à chaque passage dans la boucle principale
    frame_count += 1 

    cv2.putText(frame, f"ID: {face_id} - Captures: {image_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.imshow('Face Capturing', frame)

    # Sortir si 'q' est pressé ou si on a assez d'images (ex: 30)
    if cv2.waitKey(1) & 0xFF == ord('q') or image_count >= 30:
        break

print(f"\n[INFO] Fin de la capture. {image_count} images capturées pour l'ID {face_id}.")
video_capture.release()
cv2.destroyAllWindows()