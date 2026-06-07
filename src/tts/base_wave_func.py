import wave
import numpy as np
import os
from pathlib import Path

#           >>> PARAMÈTRES GLOBAUX <<<

FE  = 44100   # fréquence d'échantillonnage (Hz)
F0  = 130     # fréquence fondamentale glottale


#           >>> fonction, fluidité et réalisme du son <<<


def est_nulle(func):
    """
    teste si une fonction est la fonction nulle pour une fonction audio 
    en pratique n'est pas correcte, mais pour de telles fonctions de son,
    ça convient assez bien  

    :param func: la fonction a tester
    """
    return func(1) > 0.05 and func(2) > 0.05

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

def fenetre_cos(dt, tab, fe=FE):
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

def sinusoidale(freq):
    """
    dans le cas où l'on souhaiterai une fonction sinusoidale simple
    
    :param freq: fréquence de la sinusoidale
    """
    return lambda t: np.sin(2 * np.pi * freq * t)

def addBdf(audio, level_db=-85):
    """
    Ajoute un bruit blanc très faible au signal audio.

    :param audio: audio à modifier
    :param level_db: niveau du bruit en dB par rapport au RMS du signal
    """
    # amplitude de référence fixe
    ref = 1.0
    noise_amp = ref * 10**(level_db / 20)

    noise = np.random.normal(0, noise_amp, size=audio.shape)
    return audio + noise

def addRealism(audio, fe=FE, depth=0.002, rate=1.2):
    """
    Applique une micro-modulation d'amplitude lente.

    :param audio: audio à modifier
    :param fe: fréquence d'échantillonage
    :param depth: profondeur de modulation (0.1 -> 0.5 %)
    :param rate: fréquence de la modulation (Hz)
    """
    n = audio.shape[0]
    t = np.arange(n) / fe

    # LFO lent
    mod = 1 + depth * np.sin(2 * np.pi * rate * t)

    # Application identique sur les deux canaux
    if audio.ndim == 2:
        mod = mod[:, None]

    return audio * mod

def bandeBruit(f_low, f_high, n, fe=FE):
    """
    Génère un bruit blanc filtré entre f_low et f_high par FFT.
    Retourne un tableau normalisé de longueur n.

    :param f_low:  fréquence basse de la bande passante (Hz)
    :param f_high: fréquence haute de la bande passante (Hz)
    :param n:      nombre d'échantillons
    :param fe:     fréquence d'échantillonnage
    """
    bruit   = np.random.randn(n)
    spectre = np.fft.rfft(bruit)
    freqs   = np.fft.rfftfreq(n, 1 / fe)
    spectre[(freqs < f_low) | (freqs > f_high)] = 0
    filtre  = np.fft.irfft(spectre, n)
    mx = np.max(np.abs(filtre))
    return filtre / mx if mx > 0 else filtre

def enveloppe(n, attaque=0.15, declin=0.25):
    """
    Enveloppe d'amplitude linéaire : montée → tenue → descente.

    :param n:       taille du signal
    :param attaque: fraction de n pour la montée
    :param declin:  fraction de n pour la descente
    """
    env = np.ones(n)
    na  = max(1, int(n * attaque))
    nd  = max(1, int(n * declin))
    env[:na]  = np.linspace(0, 1, na)
    env[-nd:] = np.linspace(1, 0, nd)
    return env

def versFunc(signal, duree):
    """
    Encapsule un tableau numpy pré-calculé en fonction f(t)

    :param signal: tableau numpy 1D du signal
    :param duree:  durée correspondante en secondes
    """
    t_ref = np.linspace(0, duree, len(signal))
    def f(t):
        tc = np.clip(np.asarray(t, dtype=float), 0, duree * (1 - 1e-9))
        return np.interp(tc, t_ref, signal)
    return f

def harmBase(n, f0=F0, nb_harm=12, fe=FE):
    """
    Excitation glottale simplifiée : somme d'harmoniques pondérés en 1/k
    surtout utilisée dans consonant.py

    :param n:       nombre d'échantillons
    :param f0:      fondamentale (Hz)
    :param nb_harm: nombre d'harmoniques
    :param fe:      fréquence d'échantillonnage
    """
    t   = np.arange(n) / fe
    sig = sum((1 / k) * np.sin(2 * np.pi * k * f0 * t) for k in range(1, nb_harm + 1))
    mx  = np.max(np.abs(sig))
    return sig / mx if mx > 0 else sig


#           >>> definition de la classe de notes et paritions <<<


class Note:
    """
    une note comme encodée dans la partition
    """
    def __init__(self,d: int,v: float , func=None , freq = 0):
        """
        initialise la note de durée d à un volume v avec la fonction f
        
        :param d: durée (int)
        :param v: volume (int dans [0;1])
        :param func: fonction (int->int) à remplacer on veut une sinusoidale simple
        :param freq: fréquence de la sinusoidale simple
        """
        self.duration = d
        self.volume = v
        if func is None :
            if freq == 0 :
                self.function = lambda t: 0
            else:
                f = sinusoidale(freq)
                self.function = f
        else :
            self.function = func
    
    def afficher_n(self,retour_ligne : bool = True):
        """
        affiche la note

        :param RetourLigne: True si on souhaite un retour à la ligne après le print
        """
        if retour_ligne :
            print("(", self.duration, ", ", self.volume, ", ", self.function, ") ")
        else :
            print("(", self.duration, ", ", self.volume, ", ", self.function, ") ", end=" ")
    
    def open_n(self):
        """
        renvoie un 3-uplets des 3 éléments de la Note
        """
        return self.duration, self.volume, self.function

class Partition:
    """
    classe représentant les étapes de sons à écrire, initialement vide
    """
    def __init__(self):
        self.cpd: list[Note] = []   # contenu piste droite
        self.cpg: list[Note] = []   # contenu piste gauche
        self.dtot = 0               # durée totale de la parition

    def ajouter(self, ng: Note, nd: Note = None):
        """
        rajoute un élément de piste à la suite du reste
        :param npd: Note qui sera dans la piste gauche

        :param npd: Note qui sera dans la piste droite
        """
        if nd == None :
            nd = ng
        if ng.duration != nd.duration:
            raise ValueError("Les notes ajoutées pistes droite et gauche doivent avoir la même durée\n")
        self.cpd.append(ng)
        self.cpg.append(nd)
        self.dtot = self.dtot + ng.duration

    def fusionner(self, nlg: list[Note], nld: list[Note] = None):
        """
        fusionne un tableau de triplet de piste oute un élément de piste à la suite du reste

        :param npd: (durée (int), volume (int dans [0;1]), fonction (int->int))
        :param npd: de même
        """
        if nld == None :
            nld = nlg

        lg = 0    #longeur piste gauche
        ld = 0    #longeur piste droite
        for ng in nlg :
            lg = lg + ng.duration
        for nd in nld : 
            ld = ld + nd.duration
        
        if ld != lg :
            raise ValueError("Les listes de note doivent avoir la même longueur temporelle")

        self.cpg = self.cpg + nlg
        self.cpd = self.cpd + nld
        self.dtot = self.dtot + lg
        
    def renverser(self):
        """
        équivalent d'un list.reverse() sur les deux pistes contenues dans la partition
        """
        self.cpg.reverse()
        self.cpd.reverse()

    def afficher(self):
        """
        fonction pour debug, affiche simplement la parition
        """
        print("\nPiste gauche : ") 
        for n in self.cpg :
            n.afficher_n()
        print("Piste droite : ") 
        for n in self.cpd :
            n.afficher_n()
        print("taille = ", self.dtot, "\n")

    def nonVide(self):
        """
        renvoie vrai si la partition est vide
        """
        return len(self.cpg) > 0 and len(self.cpd) > 0
    
    def pop_in_2(self):
        """
        unpack une valeur temporelle et renvoie les R valeurs suivantes : 

        le volume et la fonction du son de la piste gauche
        puis de même pour la piste droite, puis la durée de la note popped
        """
        dg,vg,fg = self.cpg.pop().open_n()   
        dd,vd,fd = self.cpd.pop().open_n()
        d = min(dg,dd)

        if dg < dd: #on va couper la partie de la piste droite qui ne sera pas pop
            dr = dd - dg # durée restante
            nnd = Note(dr,vd,fd) # nouvelle note droite
            self.cpd.append(nnd)
            self.dtot = self.dtot - dg 
        elif dg > dd: # de même si la partie droite est plus courte
            dr = dg - dd 
            nng = Note(dr,vg,fg) # nouvelle note gauche
            self.cpg.append(nng)
            self.dtot = self.dtot - dd
        else :
            self.dtot = self.dtot - d
        return vg,fg,vd,fd,d


#           >>> fonction ecriture tableau audio <<<


def setEmpty(d,fe=FE): 
    """
    écriture d'une piste audio ne contenant rien

    :param d: durée
    :param fe: fréquence d'échantillonage
    """
    return np.array(np.linspace( 0,d, int(d*fe) ) )

def createSignal(d,fe,func,vol,precedent,montant):
    """
    écriture d'un signal audio asimilé à une fonction quelconque.
    renvoie de plus des données utiles à la concaténation de pistes 

    :param d: durée
    :param fe: fréquence d'échantillonage
    :param f: function 
    :param v: volume
    :param precedent: fréquence du son précédente
    :param montant: booléen répondant à " prédemment montant ?"
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

def signalToAudio(piste_g,piste_d): 
    """
    fusionne deux pistes dans le format sonore contenu dans le fichier wav

    :param piste_d: piste oreille droite
    :param piste_g: piste oreille gauche    
    """ 
    # pour mettre les pistes gauche et droite identiques       
    if piste_d is None or np.size(piste_d) == 0: # si [[...]] ou [[...],[]]
        return np.array([piste_g,piste_g]).T     # on renvoie le même à droite et gauche
    else :              
        return np.array([piste_g,piste_d]).T
    # .T = Transposition, pour passer de matrice (N,2) à (2,N) 

def writeAudio(p: Partition, fe=FE):
    """
    fonction de traduction d'une partition vers le tableau réprésentant l'audio qui sera dans le fichier wav

    :param p: partition du son à écrire
    :param fe: = fréquence d'échantillonnage
    """
    card_tab = len(p.cpg)
    written = 0
    idx = 0
    p.renverser()
    # Initialisation
    audio_blocks = []
    precedentd = precedentg = 0
    montantd = montantg = True
    while p.nonVide() :

        # Affichage de la progression
        print(int(written / card_tab * 100), "%")

        volg,fung,vold,fund,d = p.pop_in_2()
        # Création des signaux gauche et droite
        signal_g, precedentg, montantg = createSignal(d, fe, fung, volg, precedentg, montantg)
        signal_d, precedentd, montantd = createSignal(d, fe, fund, vold, precedentd, montantd)

        # Fusion stéréo
        bloc = signalToAudio(signal_g, signal_d)

        # Ajout du bloc à la liste
        audio_blocks.append(bloc)
        idx += len(bloc)
        written += 1

    # Applique crossfade à la fin, sur tous les blocs
    audio = crossfade_blocs(audio_blocks)

    # On rend l'audio plus réalise
    audio = addBdf(audio, level_db=-85)
    audio = addRealism(audio, fe, depth=0.002, rate=1.2)

    return audio

def writeFile(audio,filename,fe=FE):
    """
    écris l'entête de fichier wav et le rempli avec l'audio

    :param audio: tableau audio produit par write_audio
    :param filename: nom du fichier audio créé
    :param fe: fréquence d'échantillonage
    """
    max_val = np.max(np.abs(audio))
    if max_val > 1:
        audio = audio / max_val  # normalise globalement sans écraser les volumes relatifs
    audio = audio * 0.5
    audio = (audio * (2 ** 15 - 1)).astype("<h")
    # conversion en 16 bits (H = 16 bits)
    chemin = Path(__file__).parent.parent.parent / "SONS" / (filename + ".wav")
    chemin.parent.mkdir(parents=True, exist_ok=True)  # crée le dossier si absent
    with wave.open(str(chemin), "w") as f:
        f.setnchannels(2)
        # 2 octets par secondes
        f.setsampwidth(2)
        f.setframerate(fe)
        f.writeframes(audio.tobytes())

    print(f"Fichier créé : {os.path.abspath(filename)}")  

def partitionToFile(p: Partition, filename, fe=FE):
    """
    Crée un fichier audio contenant le son correspondant à la partition donnée en entrée
    
    :param p: partition représentant le son à créer
    :param filename: nom du ficheir qui sera créé
    :param fe: fréquence d'échantillonage
    """
    audio = writeAudio(p,fe)
    writeFile(audio,filename)


#       >>> fonction ecriture tableau audio - version cyclique <<<


def generer_morceaux(p: Partition, fe: int):
    """
    prends une partition en renvoie, un par un, les fragments de son comme 
    ce sera encondé dans le fichier

    :param p: patition du son à écrire
    :param fe: fréquence d'échantillonage

    """
    precedent_d, precedent_g = 0, 0
    montant_d, montant_g = True, True

    while p.nonVide():
        vg,fg,vd,fd,d = p.pop_in_2()

        signal_g, precedent_g, montant_g = createSignal(d, fe, fg, vg, precedent_g, montant_g)
        signal_d, precedent_d, montant_d = createSignal(d, fe, fd, vd, precedent_d, montant_d)

        stereo = np.column_stack((signal_g, signal_d))
        yield stereo,d

def partitionToFileCyclique(p: Partition, filename, fe=FE):
    """
    Crée un fichier audio contenant le son correspondant à la partition donnée en entrée
    cette fois, ne calcule pas tout le son d'un coup, mais l'ajoute progressivement
    
    :param p: partition représentant le son à créer
    :param filename: nom du ficheir qui sera créé
    :param fe: fréquence d'échantillonage
    """
    p.renverser()
    d_tot = p.dtot  #durée totale audio
    d_ecrite = 0    #durée écrite audio
    chemin = Path(__file__).parent.parent.parent / "SONS" / (filename + ".wav")
    chemin.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(chemin), "w") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(fe)


        for morceau,d in generer_morceaux(p, fe):  # ton itérateur/générateur
            d_ecrite += d 
            # normalisation locale du morceau
            max_val = np.max(np.abs(morceau))
            if max_val > 1:
                morceau = morceau / max_val
            morceau = morceau * 0.5
            morceau = (morceau * (2**15 - 1)).astype("<h")

            f.writeframes(morceau.tobytes())  # écriture immédiate
            print(int(d_ecrite / d_tot * 100), "%")


    print(f"Fichier créé : {chemin}")


print("bwf correctement importé")