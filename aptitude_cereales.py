# -*- coding: utf-8 -*-
"""
Carte d'aptitude topographique pour les cereales - plaine du Sais (Meknes-Fes)
=============================================================================
Chaine complete ArcPy : MNT SRTM -> pente -> reclassification -> score pondere
-> classes d'aptitude -> surfaces (CSV + graphique).

A lancer dans VS Code avec l'interpreteur Python d'ArcGIS Pro (arcgispro-py3).
Prerequis : ArcGIS Pro installe, connecte (licence) et extension Spatial Analyst.
"""

import csv
import os
import sys
import glob

import arcpy
from arcpy.sa import (ExtractByMask, Slope, Reclassify, RemapRange)

# ---------------------------------------------------------------------------
# 1. PARAMETRES A ADAPTER (seule partie a modifier)
# ---------------------------------------------------------------------------
BASE = r"C:\Projet_Aptitude"                 # dossier du projet
DATA = os.path.join(BASE, "data")            # dossier contenant les tuiles SRTM (.tif)
GDB = os.path.join(BASE, "Projet_Aptitude.gdb")
RESULTATS = os.path.join(BASE, "resultats")

# Zone d'etude en degres (WGS 84) : ouest, sud, est, nord
OUEST, SUD, EST, NORD = -5.9, 33.7, -5.2, 34.1

# Systeme de coordonnees de travail : WGS 1984 UTM zone 30N (WKID 32630)
WKID_UTM = 32630
TAILLE_PIXEL = 30                            # metres

# Poids des criteres (la somme doit faire 1)
POIDS_PENTE = 0.6
POIDS_ALTITUDE = 0.4

# Seuils de reclassification : [debut, fin, note]  (5 = tres favorable)
REMAP_PENTE = [[0, 3, 5], [3, 8, 4], [8, 15, 3], [15, 25, 2], [25, 1000, 1]]
REMAP_ALTITUDE = [[-100, 400, 5], [400, 700, 4], [700, 1000, 3],
                  [1000, 1400, 2], [1400, 5000, 1]]
# Classes finales du score (1 = peu apte ... 4 = tres apte)
REMAP_FINAL = [[0, 2, 1], [2, 3, 2], [3, 4, 3], [4, 5.01, 4]]
LIBELLES = {1: "Peu apte", 2: "Moyennement apte", 3: "Apte", 4: "Tres apte"}


def msg(texte):
    """Affiche un message dans la console (et dans ArcGIS Pro si outil de script)."""
    print(texte)
    arcpy.AddMessage(texte)


def main():
    # -- Verifications de depart ------------------------------------------
    if abs(POIDS_PENTE + POIDS_ALTITUDE - 1) > 1e-9:
        sys.exit("Erreur : la somme des poids doit etre egale a 1.")

    if arcpy.CheckExtension("Spatial") != "Available":
        sys.exit("Erreur : l'extension Spatial Analyst n'est pas disponible.")
    arcpy.CheckOutExtension("Spatial")

    tuiles = glob.glob(os.path.join(DATA, "*.tif"))
    if not tuiles:
        sys.exit("Erreur : aucun fichier .tif trouve dans " + DATA)
    msg("Tuiles SRTM trouvees : %d" % len(tuiles))

    os.makedirs(RESULTATS, exist_ok=True)
    if not arcpy.Exists(GDB):
        arcpy.management.CreateFileGDB(BASE, os.path.basename(GDB))
        msg("Geodatabase creee : " + GDB)

    arcpy.env.workspace = GDB
    arcpy.env.overwriteOutput = True
    sr_wgs = arcpy.SpatialReference(4326)
    sr_utm = arcpy.SpatialReference(WKID_UTM)
    

    # -- 2. Zone d'etude (rectangle) --------------------------------------
    msg("Etape 1/7 : creation de la zone d'etude")
    sommets = [arcpy.Point(OUEST, SUD), arcpy.Point(EST, SUD),
               arcpy.Point(EST, NORD), arcpy.Point(OUEST, NORD),
               arcpy.Point(OUEST, SUD)]
    polygone = arcpy.Polygon(arcpy.Array(sommets), sr_wgs)
    arcpy.management.CopyFeatures([polygone], "Zone_etude_wgs")
    arcpy.management.Project("Zone_etude_wgs", "Zone_etude_utm", sr_utm)

    # -- 3. Mosaique, reprojection, decoupage -----------------------------
    msg("Etape 2/7 : mosaique des tuiles SRTM")
    arcpy.management.MosaicToNewRaster(
        ";".join(tuiles), GDB, "srtm_brut", None, "16_BIT_SIGNED", None, 1, "FIRST")

    msg("Etape 3/7 : reprojection (UTM 30N, pixel %d m) et decoupage" % TAILLE_PIXEL)
    arcpy.management.ProjectRaster(
        "srtm_brut", "mnt_utm", sr_utm, "BILINEAR", str(TAILLE_PIXEL))
    ExtractByMask("mnt_utm", "Zone_etude_utm").save("mnt_zone")

    # -- 4. Pente en % -----------------------------------------------------
    msg("Etape 4/7 : calcul de la pente (%)")
    Slope("mnt_zone", "PERCENT_RISE").save("pente_pct")

    # -- 5. Reclassification des criteres ---------------------------------
    msg("Etape 5/7 : reclassification pente et altitude (1 a 5)")
    pente_cl = Reclassify("pente_pct", "VALUE", RemapRange(REMAP_PENTE))
    alt_cl = Reclassify("mnt_zone", "VALUE", RemapRange(REMAP_ALTITUDE))
    pente_cl.save("pente_cl")
    alt_cl.save("alt_cl")

    # -- 6. Score pondere et classes d'aptitude ---------------------------
    msg("Etape 6/7 : score pondere et classes d'aptitude")
    score = POIDS_PENTE * pente_cl + POIDS_ALTITUDE * alt_cl
    score.save("score_aptitude")
    Reclassify(score, "VALUE", RemapRange(REMAP_FINAL)).save("aptitude_classes")

    # -- 7. Surfaces par classe -------------------------------------------
    msg("Etape 7/7 : calcul des surfaces")
    desc = arcpy.Describe("aptitude_classes")
    surface_pixel_ha = (desc.meanCellWidth * desc.meanCellHeight) / 10000.0
    lignes = [(r[0], r[1]) for r in
              arcpy.da.SearchCursor("aptitude_classes", ["Value", "Count"])]
    total_pixels = sum(c for _, c in lignes)

    chemin_csv = os.path.join(RESULTATS, "surfaces_par_classe.csv")
    surfaces = []
    with open(chemin_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Classe", "Libelle", "Pixels", "Surface_ha", "Part_%"])
        for valeur, nb in sorted(lignes):
            ha = nb * surface_pixel_ha
            pct = 100.0 * nb / total_pixels
            surfaces.append((valeur, ha, pct))
            w.writerow([valeur, LIBELLES.get(valeur, "?"), nb,
                        round(ha, 1), round(pct, 1)])
            msg("Classe %s (%s) : %.0f ha (%.1f %%)"
                % (valeur, LIBELLES.get(valeur, "?"), ha, pct))
    msg("Tableau enregistre : " + chemin_csv)

    # -- Graphique des surfaces (facultatif : ignore si matplotlib absent) -
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        couleurs = {1: "#d7191c", 2: "#fdae61", 3: "#a6d96a", 4: "#1a9641"}
        fig, ax = plt.subplots(figsize=(7, 4))
        etiquettes = [LIBELLES.get(v, str(v)) for v, _, _ in surfaces]
        valeurs = [ha for _, ha, _ in surfaces]
        ax.bar(etiquettes, valeurs, color=[couleurs.get(v, "grey") for v, _, _ in surfaces])
        ax.set_ylim(0, max(valeurs) * 1.2)
        ax.set_ylabel("Surface (ha)")
        ax.set_title("Surface par classe d'aptitude")
        for i, (_, ha, pct) in enumerate(surfaces):
            ax.text(i, ha, "%.0f ha\n%.1f %%" % (ha, pct), ha="center", va="bottom")
        fig.tight_layout()
        chemin_png = os.path.join(RESULTATS, "surfaces_par_classe.png")
        fig.savefig(chemin_png, dpi=200)
        msg("Graphique enregistre : " + chemin_png)
    except ImportError:
        msg("matplotlib absent : graphique ignore.")

    arcpy.CheckInExtension("Spatial")
    msg("Termine. Ajoute 'aptitude_classes' a ta carte dans ArcGIS Pro.")


if __name__ == "__main__":
    main()
