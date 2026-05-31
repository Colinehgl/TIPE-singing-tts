import wave
import numpy as np
import os
from pathlib import Path

### FONCTION ECRITURE SON FLUIDE

def est_nulle(func):
    """
    teste si une fonction est la fonction nulle pour une fonction audio 
    en pratique n'est pas correcte, mais pour de telles fonctions de son,
    ça convient assez bien  

    :param func: la fonction a tester
    """
    return func(1)==0 and func(2) == 0


def crossfade_blocs(blocs, N=64):
    """
    Applique un fondu enchaîné entre chaque bloc successif.
    
    :param blocs: list de np.ndarray, chaque bloc étant de forme (T, 2)
    :param N: taille de la zone de fondu
    """
    if not blocs:
        return np.zeros((0, 2))

    # Commence avec le premier bloc
    audio = blocs[0]

    for next_bloc in blocs[1:]:
        # Si l'un des blocs est trop court, on skip le fondu
        if len(audio) < N or len(next_bloc) < N:
            audio = np.concatenate((audio, next_bloc), axis=0)
            continue

        # Fondu enchaîné entre la fin de `audio` et le début de `next_bloc`
        w = np.hanning(2 * N)
        fade_out, fade_in = w[:N], w[N:]

        A_end = audio[-N:] * fade_out[:, None]
        B_start = next_bloc[:N] * fade_in[:, None]
        crossfaded = A_end + B_start

        # Recomposer audio complet : tout sauf fin de A + fondu + reste de B
        audio = np.concatenate((
            audio[:-N],
            crossfaded,
            next_bloc[N:]
        ), axis=0)

    return audio


def fenetre_cos(dt, tab, fe):
    """
    écriture d'une fonction d'amortissage sonore pour la fonction suivante

    :param dt: durée de l'amoritssage
    :param tab: tableau de l'audio
    :param fe: fréquence d'échantillonage

    """
    duree_fenetre = dt / 8
    taille_fenetre = int(duree_fenetre * fe)

    if taille_fenetre > len(tab) // 2:
        taille_fenetre = len(tab) // 2

    hanning = 0.5 * (1 - np.cos(2 * np.pi * np.arange(taille_fenetre) / taille_fenetre))
    tab[:taille_fenetre] *= hanning
    tab[-taille_fenetre:] *= hanning[::-1]


def sinusoidal(freq):
    return lambda t: np.sin(2 * np.pi * freq * t)

# Ajouts de Bruits de fond
def add_bdf(audio, level_db=-85):
    """
    # Ajoute un bruit blanc très faible au signal audio.
    # level_db = niveau du bruit en dB par rapport au RMS du signal
    """
    # amplitude de référence fixe
    ref = 1.0
    noise_amp = ref * 10**(level_db / 20)

    noise = np.random.normal(0, noise_amp, size=audio.shape)
    return audio + noise

def add_realism(audio, fe, depth=0.002, rate=1.2):
    """
    # Applique une micro-modulation d'amplitude lente.
    # depth = profondeur de modulation (≈ 0.1–0.5 %)
    # rate  = fréquence de la modulation (Hz)
    """
    n = audio.shape[0]
    t = np.arange(n) / fe

    # LFO lent
    mod = 1 + depth * np.sin(2 * np.pi * rate * t)

    # Application identique sur les deux canaux
    if audio.ndim == 2:
        mod = mod[:, None]

    return audio * mod


### FONCTION ECRITURE TABLEAU AUDIO

def set_piste_audio(d,fe,func,vol,precedent,montant):
    """
    # écriture d'une piste audio contenant un signal asimilé à une fonction quelconque
    # d = durée
    # fe = fréquence d'échantillonage
    # f = function 
    # v = volume
    # precedent =  fréquence précédente,
    # montant = booléen répondant à " prédemment montant ?"
    """
    # décalage à effectuer pour aligner les sinusoïdales
    # offset = aligner_phases(func, fe, d, precedent, montant)
    offset = 0
    # crée axe temporel de fe points par seconde
    template = np.linspace(0, d, int(d*fe)) 
    # renvoie l'image par la fonction de cet axe
    try:
        signal = func(template + offset).astype(np.float32)
    except:
        # fallback si func n'est pas vectorisée
        signal = np.array([func(t + offset) for t in template], dtype=np.float32)
    # fenêtrage pour lisser les bords du son
    # fenetre_cos(d,signal,fe)

    # pour pas casser les oreilles
    if np.max(np.abs(signal)) > 1:
        signal = signal / np.max(np.abs(signal))

    precedent = signal[-1]
    montant = (signal[-1] >= signal[-2])
    return vol * signal, precedent, montant

def set_empty(d,fe): 
    """
    # écriture d'une piste audio ne contenant rien
    # d = durée
    # f = fréquence d'échantillonage
    """
    return np.array(np.linspace( 0,d, int(d*fe) ) )

def create_audio(piste_g,piste_d): 
    """
    # écriture tableau de valeurs sons exploitable
    # piste_d = piste oreille droite
    # piste_g = piste oreille gauche    
    """ 
    # pour mettre les pistes gauche et droite identiques       
    if piste_d is None or np.size(piste_d) == 0: # si [[...]] ou [[...],[]]
        return np.array([piste_g,piste_g]).T     # on renvoie le même à droite et gauche
    else :              
        return np.array([piste_g,piste_d]).T
    # .T = Transposition, pour passer de matrice (N,2) à (2,N) 

def write_audio(tab, fe):
    """
    > Prend un tableau de tableau de forme :
        [ [[d1g,volg1,fun1g],[d1d,vold1,fun1d]], ... ]
    - d1g = durée du son à l'oreille gauche
    - f1g = fréquence ou fonction pour gauche
    - func_g1 = fonction du son gauche
    - vold1 = volume (constante entre 0 et 1)
    
    > et le transforme en tableau de son exploitable
    > fe = fréquence d'échantillonnage
    """
    tab = list(tab)  # pour ne pas altérer le tableau original
    card_tab = len(tab)
    written = 0
    idx = 0

    # Initialisation
    tab.reverse()
    audio_blocks = []
    precedentd = precedentg = 0
    montantd = montantg = True

    while tab:
        # Affichage de la progression
        print(int(written / card_tab * 100), "%")

        tab_dg = tab.pop()  # [[dg,volg,fung],[dd,vold,fund]]
        tab_g = tab_dg.pop()  # [dg, volg, fung]
        dg = tab_g.pop(0)
        volg = tab_g.pop(0)
        fung = tab_g.pop(0)
        if isinstance(fung, (int, float)):
            fung = sinusoidal(fung)

        if not tab_dg:
            dd, vold, fund = dg, volg, fung
        else:
            tab_d = tab_dg.pop()
            dd = tab_d.pop(0)
            vold = tab_d.pop(0)
            fund = tab_d.pop(0)
            if isinstance(fund, (int, float)):
                fund = sinusoidal(fund)

        assert dg == dd

        # Création des signaux gauche et droite
        signal_g, precedentg, montantg = set_piste_audio(dg, fe, fung, volg, precedentg, montantg)
        signal_d, precedentd, montantd = set_piste_audio(dd, fe, fund, vold, precedentd, montantd)

        # Fusion stéréo
        bloc = create_audio(signal_g, signal_d)

        # Ajout du bloc à la liste
        audio_blocks.append(bloc)
        idx += len(bloc)
        written += 1

    print("100%\n")

    # Applique crossfade à la fin, sur tous les blocs
    audio = crossfade_blocs(audio_blocks)

    # On rend l'audio plus réalise
    audio = add_bdf(audio, level_db=-85)
    audio = add_realism(audio, fe, depth=0.002, rate=1.2)

    return audio


#écris l'entête de fichier wav et le rempli avec l'audio
def write_file(audio,filename,fe):
    max_val = np.max(np.abs(audio))
    if max_val > 1:
        audio = audio / max_val  # normalise globalement sans écraser les volumes relatifs
    audio = audio * 0.5
    audio = (audio * (2 ** 15 - 1)).astype("<h")
    # conversion en 16 bits (H = 16 bits)
    chemin = Path(__file__).parent.parent / "TESTS" / "SONS" / (filename + ".wav")
    chemin.parent.mkdir(parents=True, exist_ok=True)  # crée le dossier si absent
    with wave.open(str(chemin), "w") as f:
        f.setnchannels(2)
        # 2 octets par secondes
        f.setsampwidth(2)
        f.setframerate(fe)
        f.writeframes(audio.tobytes())
    """
    with open('new.txt', 'w') as fp:
        for item in audio:
            fp.write("%s\n" % item)
    """
    print(f"Fichier créé : {os.path.abspath(filename)}")  

print("bwf correctement importé")