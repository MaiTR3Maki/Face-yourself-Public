# Face-yourself
## 🍽️ Système de Gestion de Cantine par Reconnaissance Faciale

<p align="center">
    <img src="/Documentation/logo-Face-yourself.png" alt="Logo Face Yourself" width="250"/>
</p>

Ce projet combine une interface de gestion des crédits de cantine (via Tkinter et SQLite) avec un système d'authentification par reconnaissance faciale (via OpenCV et l'algorithme LBPH) pour automatiser le débit des repas.

## ✨ Fonctionnalités Principales

- **Gestion des Élèves :** Ajout, consultation du crédit et affichage de la liste complète des élèves (Base de données SQLite).

- **Gestion des Crédits :** Fonctionnalités d'ajout de crédit par un administrateur.

- **Capture d'Images :** Outil intégré pour collecter des échantillons de visages nécessaires à l'entraînement de l'IA.

- **Entraînement du Modèle :** Génération du fichier de modèle (trainer.yml) à partir des images capturées.

- **Débit Automatisé :** Utilisation de la caméra pour identifier un élève et débiter le coût du repas de son compte si le crédit est suffisant.

<p align="center">
  <a href="/Documentation/Maquette.pdf" target="_blank">
    <img src="/Documentation/page_principal.png" alt="Interface Graphique" width="250"/>
  </a>
</p>

## ⚙️ Prérequis

Assurez-vous que les dépendances suivantes sont installées sur votre système :

    Python 3.x

    OpenCV (avec les contributions pour la reconnaissance faciale)

    NumPy

    Pillow (PIL)

Vous pouvez installer les bibliothèques requises via pip :
Bash

    pip install opencv-contrib-python numpy Pillow

## 🚀 Guide de Démarrage Rapide

Pour que le système fonctionne, il est crucial de suivre ces étapes dans l'ordre pour configurer la base de données et entraîner le modèle d'IA.

### Étape 1 : Lancement de l'Application

Lancez le script Python principal :
Bash

    python Cantine_reconnaissance.py

### Étape 2 : Enregistrement des Élèves

Utilisez la section **"Administration & Entraînement"** dans l'interface Tkinter :

Cliquez sur **"1. Ajouter un Élève".**

Entrez le nom et le prénom. **L'ID de l'élève sera affiché dans la boîte de dialogue de succès.** Cet ID est l'identifiant unique utilisé par la DB et le modèle d'IA.

### Étape 3 : Capture des Images du Visage

L'IA a besoin d'images pour apprendre. Utilisez l'ID obtenu à l'étape précédente.

Cliquez sur **"4. Capturer Images Élève".**

Entrez l'ID de l'élève créé à l'étape 2.

La caméra s'ouvrira. Positionnez l'élève devant la caméra et faites-lui effectuer quelques légers mouvements de tête et expressions.

Le système capturera 30 images et les enregistrera dans le dossier dataset/ID_ÉLÈVE/.

### Étape 4 : Entraînement du Modèle d'IA

Une fois que vous avez capturé les images pour tous les élèves à reconnaître, vous devez entraîner l'IA :

Cliquez sur **"5. Entraîner le Modèle (Créer trainer.yml)".**

Le processus de calcul commence. Une fois terminé, le fichier trainer.yml sera créé ou mis à jour dans le répertoire racine du projet. Ce fichier est le cerveau de la reconnaissance faciale.

### Étape 5 : Gestion des Crédits

Avant le premier débit, assurez-vous que les élèves ont des fonds :

Cliquez sur **"2. Ajouter du Crédit".**

Entrez l'ID de l'élève et le montant à créditer.

## 🚀 Utilisation du Système de Débit

Cette fonctionnalité est le cœur du projet, utilisée pour le service de cantine.

Cliquez sur **"SCANNER LE VISAGE & DÉBITER"**.

La caméra s'ouvrira après une brève phase de stabilisation (quelques secondes) pour éviter les plantages.

Positionnez l'élève devant la caméra.

Une fois l'élève identifié (boîte verte), le programme valide la transaction.

Le coût du repas (5.00 € par défaut) sera débité du compte, et une boîte de dialogue Tkinter confirmera la transaction et affichera le nouveau solde.

Pour annuler et fermer la caméra sans débiter, appuyez sur Échap (Esc).

## 📚 Structure du Projet

| Fichier/Dossier  | Rôle         | 
| :---------------|:---------------:|
| ``` Cantine_reconnaissance.py ``` | Contient le code principal, l'interface Tkinter et la logique d'exécution.|
| ``` eleves.db ``` | Base de données SQLite contenant les informations des élèves (ID, nom, prénom, crédit).|
| ``` dataset/ ```| Dossier de travail pour stocker les images capturées (classées par sous-dossiers ID).|
| ``` trainer.yml ```| Modèle de reconnaissance faciale LBPH généré après l'entraînement.|


## 🛠️ Dépannage et Maintenance


| Problème  | Cause         | Solution        | 
| :---------------|:---------------:|:---------------:|
| **Écran de caméra noir** | Mauvais index de caméra ou caméra déjà utilisée.| Modifiez l'index de cv2.VideoCapture(0) à 1 ou 2. Fermez les autres applications de caméra.| 
| **Détection trop rapide/plantage** | Conflit entre OpenCV et Tkinter lors de la fermeture. | Le script intègre un délai de stabilisation (10 frames) qui devrait résoudre ce problème. | 
| **Élève non reconnu (Inconnu)**| Confiance trop faible ou manque de données. | Augmentez la luminosité, capturez plus d'images pour cet ID, puis relancez l'entraînement (Étape 4).| 
| ``` trainer.yml ``` **manquant**| Le modèle n'a jamais été entraîné. | Suivez l'Étape 4 : Entraînement du Modèle d'IA.| 

___

 ## 🔍 Explication: Comment j'ai réalisé ce projet ?

Je me suis renseigné sur comment détecter un visage, et j'ai trouvé ce lien qui m'a énormément aidé : 
[Face Detection Python (opencv)](https://www.datacamp.com/fr/tutorial/face-detection-python-opencv)

J'ai pu faire en sorte qu'il détecte les visages sans savoir qui c'est pour le moment. Cette première étape s'est basée sur l'utilisation de l'algorithme **Haar Cascade**, chargé via : ```cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml") ```

## 💡 Le Défi de la Reconnaissance Faciale

C'est donc là qu'est venue la deuxième étape : trouver comment passer de la **détection** (savoir où est le visage) à la **reconnaissance** (savoir à qui appartient ce visage). J'ai défini les objectifs suivants :

1. **Enregistrer des photos :** Collecter des images de référence pour chaque personne.

2. **Créer une empreinte du visage (ou embedding) :** Extraire des caractéristiques numériques uniques du visage pour l'identification.

3. **Reconnaître grâce à la caméra :** Comparer l'empreinte en direct avec celles enregistrées.

1. **La Création de l'Empreinte (Embedding)**

Pour la création de l'empreinte, je me suis rendu sur la documentation officielle de Python et d'OpenCV pour espérer trouver mon bonheur. Malheureusement, ce ne fut pas le cas, du moins pas complètement. J'ai trouvé quelques bouts de code intéressants mais pas suffisants (la documentation est vraiment immense, avec des formules mathématiques et des termes que je ne connaissais même pas).

J'ai compris qu'il fallait utiliser un modèle de machine learning entraîné à convertir une image de visage en un **vecteur de nombres** (l'empreinte). C'est ce vecteur, et non l'image elle-même, qui est stocké.

J'ai dû demander à l'IA comment utiliser ces bouts de code, notamment pour la partie cruciale de la reconnaissance elle-même. Pour cela, j'ai finalement opté pour l'algorithme Local Binary Patterns Histograms (LBPH), un algorithme d'OpenCV bien adapté pour cette tâche et relativement simple à mettre en œuvre par rapport aux solutions basées sur le Deep Learning.

L'entraînement du modèle LBPH (méthode ```cv2.face.LBPHFaceRecognizer_create()```) se résume à :

- **Récupérer** toutes les images de référence.

- **Convertir** chaque visage en son empreinte (ensemble de patterns binaires).

- **Stocker** ces empreintes avec l'ID de la personne correspondante.

2. Reconnaissance en Temps Réel

Une fois l'étape d'entraînement terminée, la reconnaissance en temps réel est devenue plus simple. À chaque nouvelle image capturée par la caméra :

1. Le **Haar Cascade** détecte un visage (trouve les coordonnées du rectangle).

2. Le visage détecté est transmis au modèle **LBPH**.

3. Le modèle compare l'empreinte du visage actuel avec toutes celles enregistrées et renvoie l'ID de la personne la plus proche, ainsi qu'un **niveau de confiance** (plus il est bas, plus la correspondance est bonne).

C'est cette valeur de confiance (``` threshold = 75 ```)  qui permet de décider si l'on affiche le nom de la personne ou le libellé "Inconnu".