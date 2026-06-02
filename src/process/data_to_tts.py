from TTS import base_wave_func as bwf
import numpy as np
from src.process import text_process as p
fre = 44100

# fonctions pour simplfier l'écriture

def o(i):
    if i >= 4 :
        return 2
    if i < 100 or i == 0:
        return 4
    if i == 100 :
        return 1
    else :
        return 0
def e(i):
    if i == 5 or i == 19 :
        return 3
    if i == 3 or i == 4 or i == 15 or i == 18 :
        return 4
    return 0

# paramètres des formants (inchangés)

params_A = [
    *[
    (30-(i/2), [105*i]) for i in range(10)
    ]
]
params_O = [
    *[
        (o(i) ,[125*i + o(100*i)])for i in range(1,6) 
    ],

]
params_E = [
    *[
        (e(i), [132*i]) for i in range(20)
    ]
]
params_I = [
    ( 3, [1, 160,310,2070]),
    (0.5, [480] + [2030 + 190*i for i in range(9)])
]

params_U = []
params_Y = []


# CHANGEMENT : f0 ajouté en paramètre (fréquence de la note chantée)
def write_mltp_harmo(freq, f0=440):
    """
    freq : liste de tuples (k, freqs)
        - k : facteur de pondération (amplitude)
        - freqs : liste de fréquences (en Hz)
    f0 : fréquence fondamentale de la note chantée (Hz)
         défaut = 440 Hz (La4)
    Retourne une fonction f(t) = somme pondérée de sinusoïdes.
    """
    def func(t):
        val = 0
        count = 0
        for k, freqs_list in freq:
            for w in freqs_list:
                count += 1
                harmonique = round(w / f0)  # CHANGEMENT : on cherche l'harmonique de f0 la plus proche de w
                harmonique = max(harmonique, 1)  # CHANGEMENT : minimum harmonique 1 pour éviter le silence
                val += k * np.sin(2 * np.pi * (harmonique * f0) * t)  # CHANGEMENT : on joue harmonique*f0 au lieu de w
        if count != 0:
            val /= count
        return val

    return func


NOTE = {  # CHANGEMENT : dictionnaire des notes pour plus de lisibilité
    'Do4': 261.63, 'Re4': 293.66, 'Mi4': 329.63,
    'Fa4': 349.23, 'Sol4': 392.00, 'La4': 440.00,
    'Si4': 493.88, 'Do5': 523.25
}

fa = write_mltp_harmo(params_A, f0=261.63)  # CHANGEMENT : f0=Sol4 (392 Hz) au lieu de fréquences absolues
fo = write_mltp_harmo(params_O, f0=261.63)  
fe = write_mltp_harmo(params_E, f0=261.63)  
fi = write_mltp_harmo(params_I, f0=261.63)  
fu = write_mltp_harmo(params_U, f0=261.63)
fy = write_mltp_harmo(params_Y, f0=261.63)


def voyeller(fil,pas):
    '''
    permet de transformer un string de voyelle en sons
    
    :param fil: string de caractères
    :param pas: durée arbitraire de l'unité dans le tableau émincé
    '''

    def formant(chr):
        match chr:
            case '-':
                return lambda x : 0
            case 'a' :
                return fa
            case 'o' : 
                return fo
            case 'i' :
                return fi
            case 'e' :
                return fe
            case _ : 
                print( "caractère incorrect passsé : ",chr)
                return lambda x : 2/0

    u = p.emincer(p.decouper(fil,2))
    print("bb", u)
    tab  = []
    for vnb in u :
        v,nb = vnb 
        tab = tab + [[[pas*nb,1,formant(v)]]]
    return tab

def chanter(frequences, mots, pas):
    """
    frequences : liste de fréquences en Hz   ex: [440, 392, 523]
    mots       : liste de strings de voyelles ex: ['a', 'oe', 'i']
    pas        : durée unitaire par caractère

    chaque mot[i] est chanté sur frequences[i]
    """
    assert len(frequences) == len(mots), "il faut autant de fréquences que de mots"

    tab = []
    for freq, mot in zip(frequences, mots):

        # NOUVEAU : on recrée les fonctions de formants pour chaque fréquence
        fa = write_mltp_harmo(params_A, f0=freq)
        fo = write_mltp_harmo(params_O, f0=freq)
        fe = write_mltp_harmo(params_E, f0=freq)
        fi = write_mltp_harmo(params_I, f0=freq)

        def formant(chr, fa=fa, fo=fo, fe=fe, fi=fi):  # capture locale des variables
            match chr:
                case '-': return lambda x: 0
                case 'a': return fa
                case 'o': return fo
                case 'i': return fi
                case 'e': return fe
                case _:
                    print("caractère incorrect passé :", chr)
                    return lambda x: 2/0

        # on découpe le mot et on construit le tableau
        u = p.emincer(p.decouper(mot, 2))
        for v, nb in u:
            tab.append([[pas * nb, 1, formant(v)]])

    return tab

frequences = [261.63, 261.63, 392.00, 392.00, 440.00, 440.00,392.00]   
mots       = ['o', 'o', 'i', 'i', 'a', 'a', 'o']  
pas        = 0.3

tab   = chanter(frequences, mots, pas)
audio = bwf.write_audio(tab, fre)
bwf.write_file(audio, "voyelle/little", fre)


#tab = voyeller("o-i-i-a-i-a-o-i-i-i-a-o-i",0.2)

#audio = bwf.write_audio(tab, fre)
#bwf.write_file(audio, "voyelles/oo", fre)