import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from adndpg._testeur import lancer_tests
from test_clavier import TestsClavier
from test_couleurs import TestsCouleurs
from test_fenetre import TestsFenetre
from test_formes import TestsFormes
from test_souris import TestsSouris
from test_texte import TestsTexte
from test_images import TestsImages
from test_sons import TestsSons

def main():
    print("Lancement des tests visuels adndpg...")
    print("=" * 50)
    
    succes = lancer_tests(
        TestsFormes, TestsCouleurs, TestsFenetre, 
        TestsSouris, TestsTexte, TestsClavier,
        TestsImages, TestsSons
    )
    
    if succes:
        print("\n✓ Tous les tests sont passés!")
        return 0
    else:
        print("\n✗ Certains tests ont échoué.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
