import wave
import numpy as np
import os
from pathlib import Path


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

def fenetre_cos(dt, tab, fe=44100):
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

def add_bdf(audio, level_db=-85):
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

def add_realism(audio, fe=44100, depth=0.002, rate=1.2):
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
        return self.dtot != 0
    
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


def setEmpty(d,fe=44100): 
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

def writeAudio(p: Partition, fe=44100):
    """
    fonction de traduction d'un tableau audio exploitable vers l'audio qui sera dans le fichier wav

    On notera, en remplaçant g par d pour la droite
    (d1g : durée du son à l'oreille gauche) 
    (f1g = fréquence ou fonction pour gauche) 
    (func_g1 = fonction du son gauche) 
    (vold1 = volume (constante entre 0 et 1))
    
    :param tab: Prend un tableau de tableau de forme [ [[d1g,volg1,fun1g],[d1d,vold1,fun1d]], ... ]
    :param fe: = fréquence d'échantillonnage
    """
    card_tab = len(p.cpg)
    written = 0
    idx = 0

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
    audio = add_bdf(audio, level_db=-85)
    audio = add_realism(audio, fe, depth=0.002, rate=1.2)

    return audio

def writeFile(audio,filename,fe=44100):
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

print("bwf correctement importé")