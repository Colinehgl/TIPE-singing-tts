import wave
import numpy as np

import src.process.combinaison_son as cs
import src.process.extraction_liste as el 
import src.frontend.piano_page as pp
import src.tts.vowel as v 
import src.process as p

""" 
Ce programme est le support principal du logiciel
il devra mettre en lien les différents autres fichiers pour faire fonctionner le tout
"""

def main (parole, melodie, intrumental, nom_sortie ) : 

    m_tkinter = int(input("Avez-vous déjà un fichier .wav avec la mélodie prête (entrez 1) ou souhaitez-vous la composer sur placer (entrez 2)?"))

    if (m_tkinter != 1) or ( m_tkinter != 2) : 
        print("Vous n'avez pas saisie 1 ou 2. Veuillez réessayer.")

    elif m_tkinter == 1 :   
        sortie = wave.open(nom_sortie,"wr")
        freq_melodie = el.liste_hz(melodie)
        lyricsdecoupe = p.decouper(parole, 2) # a modfifier


        for i in range ( len(freq_melodie) ) :
            freq_notee = freq_melodie[i]
            

