# adndpg

Bibliothèque graphique simplifiée pour apprendre la programmation d'application et de jeux en Python.

## Installation

```bash
pip install adndpg
```

---

## Fenêtre

| Fonction / Membre | Description |
|-------------------|-------------|
| `ouvrir_fenetre(titre)` | Ouvre la fenêtre de jeu |
| `fermer_fenetre()` | Ferme définitivement la fenêtre |
| `fenetre_est_ouverte()` | `True` tant que la fenêtre n'est pas fermée |
| `effacer_ecran(couleur)`| Nettoie l'écran avec une couleur de fond |
| `redimensionner_fenetre(l, h)`| Change la taille de la fenêtre |
| `definir_images_par_seconde(fps)` | Change la vitesse de rafraîchissement |
| `obtenir_temps()` | Donne le nombre de secondes depuis le début |
| `obtenir_delta()` | Donne le temps écoulé depuis la dernière image |
| `obtenir_largeur_fenetre()` | Donne la largeur actuelle de l'écran |
| `obtenir_hauteur_fenetre()` | Donne la hauteur actuelle de l'écran |

### Exemple
```python
from adndpg import *

ouvrir_fenetre("Ma Super App")

while fenetre_est_ouverte():
    effacer_ecran(BLEU)
    # Ton code ici...

fermer_fenetre()
```

---

## Couleurs

| Fonction / Membre | Description |
|-------------------|-------------|
| `ROUGE`, `BLEU`, `VERT`, `JAUNE`, `NOIR`, `BLANC`, `GRIS`, `ORANGE`, `VIOLET`, `ROSE`, `MARRON`, `CYAN`, `TRANSPARENT` | Couleurs prédéfinies |
| `couleur_aleatoire()` | Choisit une couleur au hasard parmi la liste |
| `Couleur(r, v, b, a)` | Crée une couleur personnalisée (Rouge, Vert, Bleu, Alpha) de 0 à 255 |

### Exemple
```python
from adndpg import *

ma_couleur = Couleur(100, 200, 50, 255)
couleur_du_fond = couleur_aleatoire()
```

---

## Le Carré

| Fonction / Membre | Description |
|-------------------|-------------|
| `Carre(x, y, taille, couleur)` | Crée un nouveau carré |
| `x`, `y` | Position du coin haut-gauche |
| `taille` | Longueur des côtés |
| `couleur` | Couleur du carré |
| `rotation` | Angle de rotation en degrés |
| `visible` | `True` pour l'afficher, `False` pour le cacher |
| `dessiner()` | Affiche le carré à l'écran |
| `deplacer(dx, dy)` | Fait bouger le carré |
| `aller_a(x, y)` | Déplace le carré à une position précise |
| `redimensionner(taille)`| Change la taille |
| `orienter(degres)` | Change l'angle de rotation |
| `est_survole()` | `True` si la souris est sur le carré |
| `est_clique()` | `True` si on clique sur le carré |
| `touche(autre)` | `True` si le carré touche un autre objet |

### Exemple
```python
from adndpg import *

ouvrir_fenetre()
joueur = Carre(100, 100, 40, ROUGE)

while fenetre_est_ouverte():
    effacer_ecran(BLANC)
    
    joueur.deplacer(2, 0) # Le carré avance
    joueur.rotation += 1  # Le carré tourne sur lui-même
    
    joueur.dessiner()
```

---

## Le Rectangle

| Fonction / Membre | Description |
|-------------------|-------------|
| `Rectangle(x, y, l, h, couleur)` | Crée un nouveau rectangle |
| `x`, `y` | Position du coin haut-gauche |
| `largeur`, `hauteur` | Dimensions du rectangle |
| `couleur`, `rotation`, `visible` | Style et visibilité |
| `dessiner()`, `deplacer()`, `aller_a()` | Fonctions d'affichage et mouvement |
| `redimensionner(l, h)` | Change la largeur et la hauteur |
| `orienter(degres)` | Change l'angle |
| `est_survole()`, `est_clique()` | Interactions avec la souris |
| `touche(autre)` | Détection de collision |

### Exemple
```python
from adndpg import *

plateforme = Rectangle(200, 400, 400, 20, GRIS)

while fenetre_est_ouverte():
    effacer_ecran(BLANC)
    plateforme.dessiner()
    
    if plateforme.est_clique():
        plateforme.couleur = VERT
```

---

## Le Cercle

| Fonction / Membre | Description |
|-------------------|-------------|
| `Cercle(x, y, rayon, couleur)` | Crée un nouveau cercle |
| `x`, `y` | Position du **centre** du cercle |
| `rayon` | Taille du cercle |
| `couleur`, `visible` | Style et visibilité |
| `dessiner()`, `deplacer()`, `aller_a()` | Fonctions d'affichage et mouvement |
| `redimensionner(rayon)` | Change le rayon |
| `est_survole()`, `est_clique()` | Interactions avec la souris |
| `touche(autre)` | Détection de collision |

### Exemple
```python
from adndpg import *

balle = Cercle(400, 300, 20, JAUNE)

while fenetre_est_ouverte():
    effacer_ecran(NOIR)
    
    balle.aller_a(position_souris()[0], position_souris()[1])
    balle.dessiner()
```

---

## Le Texte

| Fonction / Membre | Description |
|-------------------|-------------|
| `Texte(message, x, y, taille, couleur)` | Crée un texte |
| `contenu` | Le message à afficher (doit être une chaîne de caractères) |
| `x`, `y` | Position |
| `taille` | Taille de la police |
| `largeur` | (Lecture seule) Largeur du texte en pixels |
| `dessiner()`, `deplacer()`, `aller_a()` | Fonctions d'affichage et mouvement |

### Exemple
```python
from adndpg import *

score = 0
ma_bulle = Texte("Score: 0", 20, 20, 30, NOIR)

# Pour changer le texte plus tard :
score += 10
ma_bulle.contenu = "Score: " + str(score)
```

---

## L'Image

| Fonction / Membre | Description |
|-------------------|-------------|
| `Image(chemin, x, y)` | Charge une image depuis ton ordinateur |
| `x`, `y` | Position |
| `largeur`, `hauteur` | (Lecture seule) Taille originale de l'image |
| `echelle` | Zoom de l'image (1.0 = normal, 2.0 = double) |
| `rotation`, `visible` | Style et visibilité |
| `dessiner()`, `deplacer()`, `aller_a()`, `orienter()` | Fonctions d'affichage et mouvement |
| `redimensionner(echelle)` | Change l'échelle de l'image |
| `est_survole()`, `est_clique()`, `touche()` | Interactions et collisions |

### Exemple
```python
from adndpg import *

image = Image("assets/image.png", 400, 300)
image.redimensionner(0.5) # Image deux fois plus petite

while fenetre_est_ouverte():
    effacer_ecran(BLANC)
    image.dessiner()
```

---

## Clavier et Souris

| Fonction | Description |
|----------|-------------|
| `touche_appuyee(T)` | `True` une seule fois quand on appuie sur la touche |
| `touche_enfoncee(T)` | `True` tout le temps où la touche est maintenue |
| `touche_relachee(T)` | `True` une seule fois quand on relâche la touche |
| `position_souris()` | Donne les coordonnées `(x, y)` de la souris |
| `clic()` | `True` une seule fois quand on clique (gauche) |
| `bouton_enfonce(B)` | `True` tant qu'on maintient le bouton (`BOUTON_GAUCHE`, `BOUTON_DROIT`) |
| `bouton_relache(B)` | `True` quand on relâche le bouton |
| `molette()` | Donne le mouvement de la molette (positif ou négatif) |

### Exemple
```python
from adndpg import *

while fenetre_est_ouverte():
    if touche_enfoncee(DROITE):
        print("Tu vas à droite !")
    
    x, y = position_souris()
    if clic():
        print("Clic en", x, y)
```

---

## Audio

| Fonction / Membre | Description |
|----------|-------------|
| `Son(chemin)` | Charge un bruitage court |
| `Musique(chemin)` | Charge une musique longue |
| `jouer()` | Démarre la lecture |
| `arreter()` | Arrête la lecture |
| `mettre_en_pause()` | (Musique) Suspend la lecture |
| `reprendre()` | (Musique) Relance après une pause |
| `continue_a_jouer()` | (**Musique**) Indispensable dans la boucle `while` |
| `est_en_boucle(v)` | (Musique) `True` pour répéter indéfiniment |
| `changer_volume(v)` | Change le volume (de 0.0 à 1.0) |
| `est_en_lecture()` | `True` si l'audio est en train de jouer |

### Exemple
```python
from adndpg import *

bruit = Son("saut.wav")
musique = Musique("fond.mp3")
musique.jouer()

while fenetre_est_ouverte():
    musique.continue_a_jouer()
    
    if touche_appuyee(ESPACE):
        bruit.jouer()
```

---

Tu as tous les outils pour commencer ton programme. La section ci-dessous ne te concerne pas.

# Guide de maintenance du paquet

### Installation
```bash
pip install -e .
```

### Lancer les tests visuels
```bash
python tests/lancer_tests.py
```
`ESPACE` = continuer | `ECHAP` = quitter

### Pour publier une nouvelle version

Mettre à jour la version dans `src/adndpg/__init__.py`

```bash
__version__ = "X.X.X"
```

Sur Github, penser à faire une release manuellement pour lancer la CI qui publiera la veersion sur [PyPi](https://pypi.org/project/adndpg/).