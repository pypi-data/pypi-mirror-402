

from adndpg import *
import random


ouvrir_fenetre("Attrape les Carrés!")

# Score
score = 0
temps_restant = 30.0  # 30 secondes

# Créer la cible (un carré à attraper)
def nouvelle_cible():
    x = random.randint(50, 700)
    y = random.randint(100, 500)
    taille = random.randint(30, 80)
    return Carre(x=x, y=y, taille=taille, couleur=couleur_aleatoire())

cible = nouvelle_cible()

# Boucle de jeu
while fenetre_est_ouverte():
    # Calculer le temps restant
    temps_restant -= obtenir_delta()
    
    if temps_restant <= 0:
        # Fin du jeu!
        effacer_ecran(NOIR)
        
        texte_fin = Texte(contenu="TEMPS ÉCOULÉ!", x=250, y=200, taille=40, couleur=ROUGE)
        texte_fin.dessiner()
        
        texte_score = Texte(contenu=f"Score final: {score}", x=280, y=300, taille=30, couleur=BLANC)
        texte_score.dessiner()
        
        texte_quitter = Texte(contenu="Appuyez sur ECHAP pour quitter", x=220, y=450, taille=20, couleur=GRIS)
        texte_quitter.dessiner()
        
        if touche_appuyee(ECHAP):
            break
        continue
    
    effacer_ecran(BLANC)
    
    # Vérifier si on clique sur la cible
    if cible.est_clique():
        score += 1
        cible = nouvelle_cible()
    
    # Dessiner la cible
    cible.dessiner()
    
    # Effet de survol
    if cible.est_survole():
        # Dessiner un contour
        contour = Carre(x=cible.x - 3, y=cible.y - 3, 
                       taille=cible.taille + 6, couleur=NOIR)
        contour.dessiner()
        cible.dessiner()  # Redessiner par-dessus
    
    # Interface
    texte_score = Texte(contenu=f"Score: {score}", x=10, y=10, taille=24, couleur=NOIR)
    texte_score.dessiner()
    
    texte_temps = Texte(contenu=f"Temps: {int(temps_restant)}s", x=650, y=10, taille=24, couleur=ROUGE)
    texte_temps.dessiner()
    
    instruction = Texte(contenu="Cliquez sur les carrés!", x=280, y=560, taille=18, couleur=GRIS)
    instruction.dessiner()

fermer_fenetre()
