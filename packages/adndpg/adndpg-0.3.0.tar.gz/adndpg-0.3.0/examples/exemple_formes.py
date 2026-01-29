

from adndpg import *
import math


# Ouvrir la fenêtre
ouvrir_fenetre("Formes de Base")

# Créer des formes
carre = Carre(x=100, y=100, taille=80, couleur=ROUGE)
rectangle = Rectangle(x=250, y=100, largeur=150, hauteur=80, couleur=BLEU)
cercle = Cercle(x=500, y=140, rayon=50, couleur=VERT)
triangle = Triangle(x1=600, y1=200, x2=700, y2=100, x3=750, y3=200, couleur=JAUNE)
ligne = Ligne(x1=100, y1=300, x2=700, y2=300, couleur=NOIR, epaisseur=3)

# Boucle principale
while fenetre_est_ouverte():
    effacer_ecran(BLANC)
    
    # Animation simple: rotation et pulsation
    rectangle.orienter(obtenir_temps() * 50)
    triangle.orienter(obtenir_temps() * 30)
    carre.orienter(-obtenir_temps() * 40)
    
    # Pulsation du cercle
    nouveau_rayon = 50 + math.sin(obtenir_temps() * 5) * 20
    cercle.redimensionner(nouveau_rayon)

    # Dessiner toutes les formes
    carre.dessiner()
    rectangle.dessiner()
    cercle.dessiner()
    triangle.dessiner()
    ligne.dessiner()
    
    # Texte d'aide
    titre = Texte(contenu="Cliquez sur une forme!", x=250, y=450, taille=30, couleur=NOIR)
    titre.dessiner()
    
    # Interactivité: changer la couleur au clic
    if carre.est_clique():
        carre.couleur = couleur_aleatoire()
    
    if cercle.est_clique():
        cercle.couleur = couleur_aleatoire()
    
    if rectangle.est_clique():
        rectangle.couleur = couleur_aleatoire()

    if triangle.est_clique():
        triangle.couleur = couleur_aleatoire()

    if ligne.est_clique():
        ligne.couleur = couleur_aleatoire()

fermer_fenetre()
