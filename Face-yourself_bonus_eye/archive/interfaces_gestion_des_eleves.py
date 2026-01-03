#interfaces tkinter pour la gestion des crédits de cantine des élèves
import tkinter as tk
from tkinter import messagebox
import sqlite3
from tkinter import simpledialog
import cv2
import os
from datetime import datetime
# Connexion à la base de données SQLite (ou création si elle n'existe pas)
conn = sqlite3.connect('eleves.db')
c = conn.cursor()
# Création de la table des élèves si elle n'existe pas déjà
c.execute('''CREATE TABLE IF NOT EXISTS eleves
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    nom TEXT NOT NULL, 
                    prenom TEXT NOT NULL, 
                    credit REAL DEFAULT 0.0)''')
conn.commit()

# Fonction pour ajouter un élève
def ajouter_eleve():
    nom = simpledialog.askstring("Nom", "Entrez le nom de l'élève:")
    prenom = simpledialog.askstring("Prénom", "Entrez le prénom de l'élève:")
    if nom and prenom:
        c.execute("INSERT INTO eleves (nom, prenom) VALUES (?, ?)", (nom, prenom))
        conn.commit()
        messagebox.showinfo("Succès", f"Élève {prenom} {nom} ajouté avec succès!")
    else:
        messagebox.showwarning("Erreur", "Le nom et le prénom ne peuvent pas être vides.")
# Fonction pour ajouter du crédit à un élève
def ajouter_credit():
    eleve_id = simpledialog.askinteger("ID Élève", "Entrez l'ID de l'élève:")
    montant = simpledialog.askfloat("Montant", "Entrez le montant à ajouter:")
    if eleve_id and montant:
        c.execute("UPDATE eleves SET credit = credit + ? WHERE id = ?", (montant, eleve_id))
        conn.commit()
        messagebox.showinfo("Succès", f"{montant} ajouté au crédit de l'élève ID {eleve_id}.")
    else:
        messagebox.showwarning("Erreur", "L'ID de l'élève et le montant ne peuvent pas être vides.")
# Fonction pour afficher le crédit d'un élève
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
# Création de la fenêtre principale
root = tk.Tk()
root.title("Gestion des Crédits de Cantine des Élèves")
# Boutons pour les différentes actions
btn_ajouter_eleve = tk.Button(root, text="Ajouter un Élève", command=ajouter_eleve)
btn_ajouter_eleve.pack(pady=10)
btn_ajouter_credit = tk.Button(root, text="Ajouter du Crédit", command=ajouter_credit)
btn_ajouter_credit.pack(pady=10)
btn_afficher_credit = tk.Button(root, text="Afficher le Crédit", command=afficher_credit)
btn_afficher_credit.pack(pady=10)
# Lancer la boucle principale de l'interface
root.mainloop()
# Fermer la connexion à la base de données lors de la fermeture de l'application
conn.close()
