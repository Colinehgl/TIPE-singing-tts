from pathlib import Path
import src.process.combinaison_son as cs
import src.process.extraction_liste as el 
import src.tts.base_wave_func as bwf
import src.process.text_process as tp

""" 
Ce programme est le support principal du logiciel
il devra mettre en lien les différents autres fichiers pour faire fonctionner le tout
"""

#           >>> PARAMÈTRES GLOBAUX <<<


FE      = 44100          # fréquence d'échantillonnage (Hz)
PAS_V   = 0.15           # durée unitaire de la voyelle par syllabe (s)
NOM_TMP = "_tmp_parole"  # nom du fichier wav temporaire (sans extension)


#           >>> FONCTIONS AUXILIAIRES <<<


def blocs_vers_partition(blocs):
    """
    Convertit la liste de blocs produite par syllaber() en une Partition.

    Chaque élément de blocs est de la forme [[duree, volume, func]],
    une liste à un seul triplet sonore. On crée une Note par triplet
    et on les empile dans une Partition mono (même signal gauche/droite).

    :param blocs: liste de blocs [[duree, volume, func]] issue de syllaber()
    """
    part = bwf.Partition()

    for bloc in blocs:
        for dur, vol, func in bloc:
            note = bwf.Note(dur, vol, func)
            part.ajouter(note)              # piste gauche = piste droite par défaut

    return part


def chanter(texte, melodie):
    """
    Synthétise les paroles japonaises (romaji) en un tableau audio stéréo.

    À terme, cette fonction adaptera la hauteur de chaque voyelle synthétisée
    pour suivre pas à pas les fréquences extraites du fichier mélodie,
    produisant ainsi un vrai chant. Pour l'instant, elle se contente de prononcer
    le texte normalement via le moteur TTS :

    chaque syllabe romaji est décomposée en une consonne suivie d'une voyelle à 
    durée fixe PAS_V.

    :param texte:   texte japonais en romaji à prononcer 
    :param melodie: chemin vers le .wav de la mélodie de référence
                    (non utilisé pour l'instant, réservé pour la version chantée)
    """
    syllabes = tp.decouper(texte, 2)
    blocs = tp.syllaber(syllabes, PAS_V)
    partition = blocs_vers_partition(blocs)
    audio = bwf.writeAudio(partition)
    return audio


#           >>> PROGRAMME PRINCIPAL <<<


def main(parole, melodie, instrumental, nom_sortie):
    """
    Point d'entrée principal du synthétiseur vocal.

    Prend un texte japonais en romaji, une mélodie de référence et un
    accompagnement instrumental, et produit un fichier .wav final résultant
    de la combinaison de la voix synthétisée et de l'instrumental.

    :param parole:       texte japonais en romaji à prononcer ou chanter
    :param melodie:      chemin vers le .wav de la mélodie de référence
    :param instrumental: chemin vers le .wav de l'accompagnement instrumental
    :param nom_sortie:   nom du fichier de sortie, sans extension (posé dans SONS/)
    """
    racine = Path(__file__).parent
    print("Synthèse vocale en cours...")
    audio_parole = chanter(parole, melodie)
    bwf.writeFile(audio_parole, NOM_TMP)
    chemin_tmp = racine / "SONS" / f"{NOM_TMP}.wav"
    print("Combinaison voix + instrumental...")
    chemin_sortie = racine / "SONS" / f"{nom_sortie}.wav"
    cs.combiner(str(chemin_tmp), str(instrumental), str(chemin_sortie))
    # 4. Suppression du fichier temporaire de voix
    chemin_tmp.unlink(missing_ok=True)

    print(f"Rendu final enregistré sous '{chemin_sortie}'.")
