[![Built with uv](https://img.shields.io/badge/Built%20with-uv-blueviolet?logo=python&logoColor=white)](https://docs.astral.sh/uv/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/edb-noumea)](https://pypistats.org/packages/edb-noumea)
[![Open in Kaggle](https://img.shields.io/badge/Kaggle-Open%20Notebook-blue?logo=kaggle)](https://www.kaggle.com/code/adriensales/qualit-eaux-de-baignade-noum-a)
[![Dataset](https://img.shields.io/badge/Kaggle-Dataset-blue?logo=kaggle)](https://www.kaggle.com/datasets/adriensales/qualit-des-eaux-de-baignade-nouma)
[![Live CSV Data](https://img.shields.io/badge/GitHub-Live%20CSV%20Data-black?logo=github)](https://github.com/adriens/edb-noumea-data)
[![Go BubbleTea TUI](https://img.shields.io/badge/Go-BubbleTea%20TUI-00ADD8?logo=go)](https://github.com/adriens/edb-noumea-tui)
[![Site officiel Ville de Nouméa](https://img.shields.io/badge/Nouméa-Site%20officiel%20Ville%20de%20Nouméa-0A74DA)](https://www.noumea.nc/noumea-pratique/salubrite-publique/qualite-eaux-baignade)



# Qualité des Eaux de Baignade à Nouméa

Ce projet Python fournit un outil simple pour scraper les données sur la qualité des eaux de baignade à Nouméa depuis le site officiel de la ville (`noumea.nc`). Il extrait les informations et les présente sous forme de tableau dans le terminal.

Il se base sur les données de https://www.noumea.nc/noumea-pratique/salubrite-publique/qualite-eaux-baignade

## Prérequis

Avant de commencer, assurez-vous d'avoir installé `uv`, le gestionnaire de paquets et d'environnements virtuels Python.




## Installation

Suivez ces étapes pour configurer l'environnement et installer les dépendances.

1.  **Accédez au répertoire du projet :**
    ```bash
    cd edb-noumea
    ```

2.  **Créez un environnement virtuel avec `uv` :**
    ```bash
    uv venv
    ```

3.  **Activez l'environnement virtuel :**
    ```bash
    source .venv/bin/activate
    ```
    *(Sur Windows, utilisez `.venv\Scripts\activate`)*

4.  **Installez les dépendances du projet :**
    ```bash
    uv pip install -e .
    ```
    *(L'option `-e .` installe le projet en mode "éditable", ce qui vous permet de modifier le code sans avoir à le réinstaller.)*

## Utilisation

Ce package peut être utilisé de deux manières : soit pour obtenir un résumé de l'état des plages, soit pour obtenir les résultats détaillés des derniers prélèvements.

### Obtenir le résumé de l'état sanitaire

Pour obtenir le tableau de résumé simple depuis la page web principale, exécutez :
```bash
python -m edb_noumea.main
```

### Obtenir les résultats détaillés (depuis PDF)

Pour obtenir le tableau détaillé des derniers relevés (extrait automatiquement du dernier fichier PDF disponible), exécutez :
```bash
python -m edb_noumea.details
```


## Générer des graphiques PNG des analyses détaillées

Vous pouvez générer automatiquement deux graphiques au format PNG (niveaux d'E. coli et d'Entérocoques par point de prélèvement) à partir des derniers résultats d'analyses, grâce au script fourni.

### Étapes

1. Assurez-vous que l'environnement virtuel est activé et que les dépendances sont installées.
2. Exécutez le script suivant depuis le répertoire du projet :

```bash
source .venv/bin/activate
/home/adriens/Github/edb-noumea/noumea_water_quality/.venv/bin/python generer_graphique_analyses.py
```

Deux fichiers PNG seront générés dans le dossier courant :


Vous pouvez ouvrir ces fichiers pour visualiser les résultats détaillés des analyses.

## Utilisation en tant que Bibliothèque

Vous pouvez également importer les fonctions dans vos propres scripts Python pour une intégration plus poussée.

Installer 

### Obtenir le résumé

```python
# exemple_resume.py
from edb_noumea.main import get_water_quality

df_resume = get_water_quality()

if df_resume is not None:
    print("Résumé de l'état des plages :")
    print(df_resume.to_string())
```

### Obtenir les résultats détaillés

```python
# exemple_details.py
from edb_noumea.details import get_detailed_results

df_details = get_detailed_results()

if df_details is not None:
    print("Détails des derniers relevés :")
    print(df_details.to_string())
```

### Exemple de Visualisation

Voici un exemple montrant comment récupérer les données détaillées et créer un graphique simple avec `matplotlib` pour visualiser les niveaux d'E. coli par point de prélèvement.

```python
# exemple_visualisation.py
import pandas as pd
import matplotlib.pyplot as plt
from edb_noumea.details import get_detailed_results

# Obtenir les données détaillées
df = get_detailed_results()

if df is not None and not df.empty:
    print("Création du graphique...")

    # S'assurer que les données sont triées pour une meilleure lisibilité
    df_sorted = df.sort_values(by='e_coli_npp_100ml', ascending=False)

    # Créer le graphique à barres horizontales
    plt.figure(figsize=(12, 8))
    plt.barh(df_sorted['point_de_prelevement'], df_sorted['e_coli_npp_100ml'], color='skyblue')
    
    # Ajouter les titres et les étiquettes
    plt.xlabel('E. coli (NPP/100ml)')
    plt.ylabel('Point de prélèvement')
    plt.title("Niveaux d'E. coli par Point de Prélèvement")
    plt.gca().invert_yaxis() # Afficher le plus élevé en haut
    plt.tight_layout() # Ajuster le layout pour que tout soit visible

    # Sauvegarder le graphique dans un fichier
    plt.savefig('ecoli_levels.png')
    print("Graphique sauvegardé sous 'ecoli_levels.png'")

    # Afficher le graphique
    plt.show()
else:
    print("Aucune donnée à afficher.")

```

*Assurez-vous que votre script est exécuté dans le même environnement virtuel où le package `edb-noumea` a été installé.*

## Sortie Attendue

### Résumé de l'état sanitaire (`main`)
```
📊 État sanitaire des eaux de baignade à Nouméa 📊
                                  Plage      État sanitaire
0          Plage de la baie des Citrons  Baignade autorisée
1  Plage de la promenade Pierre-Vernier  Baignade autorisée
...
```

### Détails des relevés (`details`)
```
📋 Voici les détails des derniers relevés :
                                   Site                       Point de prélèvement        Date  Heure E. coli (NPP/100ml) Entérocoques (NPP/100ml)
0          PLAGE DE LA BAIE DES CITRONS               P18049, Face The Beach House  04/09/2025  07:29                    10                         20
1          PLAGE DE LA BAIE DES CITRONS   P18050, Face allée centrale Mirage plaza  04/09/2025  07:33                    62                         75
...
```


