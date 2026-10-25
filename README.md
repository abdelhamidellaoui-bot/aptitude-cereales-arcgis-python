# Aptitude des terres aux céréales : ArcGIS Pro et Python

Cartographie de l'aptitude des terres à la culture des céréales avec **ArcGIS Pro** et **Python (ArcPy, Spatial Analyst)**. Le script reproduit automatiquement toute l'analyse : traitement des rasters, classification en 4 classes d'aptitude, lissage, calcul des surfaces par classe, export de tableaux CSV et de graphiques.

## Résultats

Surfaces par classe d'aptitude, après lissage (zone d'étude d'environ 2 868 km²) :

| Classe d'aptitude | Surface (km²) |
|---|---|
| Peu apte | 56,75 |
| Moyennement apte | 506,62 |
| Apte | 1 502,30 |
| Très apte | 802,05 |

## Méthodologie

1. Lecture et préparation des rasters d'entrée (tuiles du dossier `data/`).
2. Découpage sur la zone d'étude.
3. Reclassification des critères en classes d'aptitude.
4. Combinaison des critères en une carte d'aptitude à 4 classes.
5. Lissage du raster classé pour supprimer le bruit.
6. Calcul des surfaces par classe (en hectares et en km²), avant et après lissage.
7. Export des tableaux au format CSV.
8. Export des graphiques au format PNG.

## Structure du dépôt

```
aptitude_cereales.py     Script principal (étapes 1 à 8)
test_arcpy.py            Test de l'installation d'ArcPy et de Spatial Analyst
resultats/               Tableaux CSV et graphiques PNG produits par le script
```

Les rasters (`data/`) et la géodatabase (`Projet_Aptitude.gdb`) ne sont pas versionnés à cause de leur taille.

## Prérequis

- ArcGIS Pro avec l'extension **Spatial Analyst** activée
- L'interpréteur Python d'ArcGIS Pro (environnement `arcgispro-py3`)
- Visual Studio Code (conseillé)

## Utilisation

1. Placer les tuiles raster dans un dossier `data/` à la racine du projet.
2. Fermer ou retirer de la carte les couches de la géodatabase, pour éviter une erreur de verrou.
3. Lancer `aptitude_cereales.py` avec l'interpréteur d'ArcGIS Pro.
4. Récupérer les fichiers générés dans `resultats/`.

## Auteur

Ellaoui Abdelhamid, étudiant en ingénierie de data science appliquée en agriculture, IAV Hassan II (Rabat).
