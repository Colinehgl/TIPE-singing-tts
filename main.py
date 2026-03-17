import wave
import numpy as np

import combinaison_son as cs
import extraction_liste as el 
import piano_page as pp

#Cette fonction est la fonction principale qui fait la plus grand boucle


def main_desu (parole, melodie, intrumental, nom_sortie ) : 

    m_tkinter = int(input("Avez-vous déjà un fichier .wav avec la mélodie prête (entrez 1) ou souhaitez-vous la composer sur placer (entrez 2)?"))

    if (m_tkinter != 1) or ( m_tkinter != 2) : 
        print("Vous n'avez pas saisie 1 ou 2. Veuillez réessayer.")

    elif m_tkinter == 1 :   
        sortie = wave.open(nom_sortie,"wr")
        freq_melodie = el.liste_hz(melodie)

        for i in range (len(freq_melodie)) :
            freq_notee = freq_melodie[i]
            # 

