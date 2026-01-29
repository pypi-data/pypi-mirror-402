# 👨‍🏫 adndpg

Bibliothèque graphique extrêmement simplifliée en français à des fins éducative, basée sur [pyray](https://electronstudio.github.io/raylib-python-cffi/pyray.html), un wrapper de [raylib](https://www.raylib.com/).

---

## 📦 Installation (pour les élèves)

```bash
pip install adndpg
```

---

## 🔧 Maintenance du Package

### Prérequis

```bash
pip install build twine hatchling
```

### Installation en mode développement

```bash
git clone https://github.com/your-username/adndpg.git
cd adndpg
pip install -e .
```

### Lancer les tests visuels

Tous les tests s'exécutent dans une unique fenêtre graphique:

```bash
python tests/lancer_tests.py
```

En cas d'échec, la fenêtre se met en pause et affiche l'erreur.  
`ESPACE` = continuer | `ECHAP` = quitter

### Lancer un exemple

```bash
python examples/exemple_jeu_simple.py
```

### Build du package

```bash
python -m build
```

Génère:

- `dist/adndpg-X.X.X-py3-none-any.whl`
- `dist/adndpg-X.X.X.tar.gz`

### Mise à jour de la version

Modifier `__version__` dans `src/adndpg/__init__.py`:

```python
__version__ = "X.X.X"
```

### Publication sur PyPI

La publication s'effectue lors de la création d'une nouvelle release sur le dépôt Github.