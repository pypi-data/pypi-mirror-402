

from adndpg import *


ouvrir_fenetre("Animation")

# Notre personnage (un cercle)
joueur = Cercle(x=400, y=300, rayon=30, couleur=BLEU)
vitesse = 5

# Score
score = 0

# Boucle de jeu
while fenetre_est_ouverte():
    effacer_ecran(BLANC)
    
    # Déplacement avec les flèches
    if touche_enfoncee(GAUCHE):
        joueur.deplacer(-vitesse, 0)
    if touche_enfoncee(DROITE):
        joueur.deplacer(vitesse, 0)
    if touche_enfoncee(HAUT):
        joueur.deplacer(0, -vitesse)
    if touche_enfoncee(BAS):
        joueur.deplacer(0, vitesse)
    
    # Changer de couleur avec espace
    if touche_appuyee(ESPACE):
        joueur.couleur = couleur_aleatoire()
        score += 1
    
    # Dessiner
    joueur.dessiner()
    
    # Afficher le score
    texte_score = Texte(contenu=f"Score: {score}", x=10, y=10, taille=20, couleur=NOIR)
    texte_score.dessiner()
    
    # Instructions
    aide = Texte(contenu="Flèches = bouger, Espace = couleur", x=10, y=560, taille=16, couleur=GRIS)
    aide.dessiner()

fermer_fenetre()
