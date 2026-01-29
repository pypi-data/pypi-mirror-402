__version__ = "0.2.1"

from adndpg.fenetre import (
    ouvrir_fenetre,
    fermer_fenetre,
    fenetre_est_ouverte,
    effacer_ecran,
    redimensionner_fenetre,
    definir_images_par_seconde,
    obtenir_temps,
    obtenir_delta,
)

from adndpg.couleurs import (
    Couleur,
    ROUGE,
    BLEU,
    VERT,
    JAUNE,
    ORANGE,
    VIOLET,
    ROSE,
    NOIR,
    BLANC,
    GRIS,
    MARRON,
    CYAN,
    TRANSPARENT,
    couleur_aleatoire,
)

from adndpg.formes import (
    Carre,
    Rectangle,
    Cercle,
    Triangle,
    Ligne,
)

from adndpg.texte import Texte

from adndpg.images import Image

from adndpg.sons import Son, Musique

from adndpg.clavier import (
    touche_appuyee,
    touche_enfoncee,
    touche_relachee,
    HAUT,
    BAS,
    GAUCHE,
    DROITE,
    ESPACE,
    ENTREE,
    ECHAP,
    A, B, C, D, E, F, G, H, I, J, K, L, M,
    N, O, P, Q, R, S, T, U, V, W, X, Y, Z,
)

from adndpg.souris import (
    position_souris,
    clic,
    bouton_enfonce,
    CLIQUE_GAUCHE as BOUTON_GAUCHE,
    CLIQUE_DROITE as BOUTON_DROIT,
    CLIQUE_MILIEU as BOUTON_MILIEU,
)
