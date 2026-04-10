import wave
import numpy as np
import os

### FONCTION ECRITURE SON FLUIDE


def crossfade_blocs(stereo, idx):
    """
    > Applique un fondu enchaîne de N echantillons a l'indice idx
    > stereo : np.ndarray de forme (T,2)
    > idx    : position de fin du bloc A (avant concatenation)
    > N      : taille de la zone de transition

    """
    N = 64 #arbitraire

    if idx < N or idx + N > len(stereo):
        # Trop court pour un fondu : on ne fait rien
        return stereo


    # on travaille canal par canal
    for ch in (0, 1):
        chan = stereo[:, ch] # renvoie un tableau de forme (T,1)
        # Hann de longueur 2N
        w = np.hanning(2 * N)
        fade_debut, fade_fin = w[:N], w[N:]
        # calcul des extremites
        A_end = chan[idx - N: idx] * fade_debut
        B_start = chan[idx: idx + N] * fade_fin
        # recouvrement + addition
        chan[idx - N: idx] = A_end + B_start
        stereo[:, ch] = chan

    return stereo



def fenetre_cos(dt, tab, fe):
    """
    # ecriture d'une fonction d'amortissage sonore pour la fonction suivante
    # dt = duree de l'amoritssage
    # tab = tableau de l'audio
    #fe = frequence d'echantillonage

    """
    duree_fenetre = dt / 8
    taille_fenetre = int(duree_fenetre * fe)

    if taille_fenetre > len(tab) // 2:
        taille_fenetre = len(tab) // 2

    hanning = 0.5 * (1 - np.cos(2 * np.pi * np.arange(taille_fenetre) / taille_fenetre))
    tab[:taille_fenetre] *= hanning
    tab[-taille_fenetre:] *= hanning[::-1]


def aligner_phases(func, f, fe, d, precedent, montant):
    """
    # ecriture d'une fonction qui aligne les phases sinusoïdales, pour eviter les coupures  
    # func = fonction du son
    # f = frequence du son
    # fe = frequence d'echantillonage
    # d = duree de l'audio
    # montant = booleen de "le signal est finalement montant ?"

    """

    if f == 0:
        return 0  # pas besoin d'alignement pour un silence
    
    
    t = np.linspace(0, d, int(d * fe)) # cree un tableau comme template d'ecriture (fonction suivante)
    offset = 0
    pas = 1 / fe  # resolution temporelle

    # Balaye pour trouver une valeur proche de `precedent`
    for k in range(int(fe/f)):
        test = func(offset, f)
        if abs(test - precedent) < 0.0000001:  # seuil de tolerance
            return offset
        offset += pas
    return 0


### FONCTION ECRITURE TABLEAU AUDIO

def set_piste_audio(d,f,fe,func,vol,precedent,montant):
    """
    # ecriture d'une piste audio contenant un signal asimile a une fonction quelconque
    # d = duree
    # f = frequence
    # fe = frequence d'echantillonage
    # f = function 
    # v = volume
    # precedent =  frequence precedente,
    # montant = booleen repondant a " predemment montant ?"
    """
    # decalage a effectuer pour aligner les sinusoïdales
    offset = aligner_phases(func, f, fe, d, precedent, montant)
    # cree axe temporel de fe points par seconde
    template = np.linspace(0, d, int(d*fe)) 
    # renvoie l'image par la fonction de cet axe
    signal = np.array( [ func(i+offset,f) for i in template] , dtype = np.float32)
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
    # ecriture d'une piste audio ne contenant rien
    # d = duree
    # f = frequence d'echantillonage
    """
    return np.array(np.linspace( 0,d, int(d*fe) ) )

def create_audio(piste_g,piste_d): 
    """
    # ecriture tableau de valeurs sons exploitable
    # piste_d = piste oreille droite
    # piste_g = piste oreille gauche    
    """ 
    # pour mettre les pistes gauche et droite identiques       
    if piste_d is None or np.size(piste_d) == 0: # si [[...]] ou [[...],[]]
        return np.array([piste_g,piste_g]).T     # on renvoie le meme a droite et gauche
    else :              
        return np.array([piste_g,piste_d]).T
    # .T = Transposition, pour passer de matrice (N,2) a (2,N) 

def write_audio(tab,fe) :
    """
    > prends un tableau de tableau de forme [ [[d1g,f1g,func_g1,vold1],[d1d,f1d,func_g2,vold2]], ... ]
    ****d1g = duree du son a l'oreille gauche
        f1g = frequence n*1 gauche
        func_g1 = fonction du song
        vold1 = volume (constante entre 0 et 1 )

    > et le transforme en tableau de son exploitable
    > fe = frequence d'echantillonage
    """
    tab = list(tab) # pour ne pas alterer le tableau original

    #pour le rajout d'un compteur d'avancement de la creation 
    card_tab = len(tab)
    written = 0 

    #ecriture du tableau son
    tab.reverse()
    audio = None  #tableau vide
    precedentd = precedentg = 0
    montantd = montantg = True  

    while tab :
        # update compteur
        print(int(written / card_tab * 100), "%")        

        # creation de la piste
        tab_dg = tab.pop()                          # [[dg,fg,volg],[dd,fd,vold]]
        tab_g = tab_dg.pop()                        # on recupère les g
        dg,fg,vol_g,func_g = tab_g                  # on enregistre la première parite
        if tab_dg == [] :
            dd,fd,vol_d,func_d = dg,fg,vol_g,func_g # si partie droite absente, même que gauche
        else :
            tab_d = tab_dg.pop()
            dd,fd,vol_d,func_d = tab_d              # sinon on prends le reste
        assert(dg==dd)

        # on ecrit 

        # Appels separes pour recuperer les trois valeurs
        signal_g, precedentg, montantg = set_piste_audio(dg, fg, fe, func_g, vol_g, precedentg, montantg)
        signal_d, precedentd, montantd = set_piste_audio(dd, fd, fe, func_d, vol_d, precedentd, montantd)

        # Creation de l'audio formate
        bloc = create_audio(signal_g, signal_d)

        # On fusionne la piste cree avec tout ce qui a ete ecrit precedemment
        if audio is None :
            audio = bloc
        else :
            # position de fin du bloc
            idx = len(audio)
            # concatenation de tout ce qui a ete ecrit et du nouveau bloc
            audio = np.concatenate((audio, bloc))
            # applique le crossfade autour de idx
            audio = crossfade_blocs(audio, idx)
            


        # On rajoute une petite fraction de son vide
        # vide_sep = create_audio(set_empty(0.005,fe), [])
        # audio = np.concatenate((audio, vide_sep))

        # update du compteur
        written += 1 
    print("100%\n")
    return audio



#ecris l'entête de fichier wav et le rempli avec l'audio
def write_file(audio,filename,fe):
    max_val = np.max(np.abs(audio))
    if max_val > 1:
        audio = audio / max_val  # normalise globalement sans ecraser les volumes relatifs
    audio = audio * 0.5
    audio = (audio * (2 ** 15 - 1)).astype("<h")
 # conversion en 16 bits (H = 16 bits)

    with wave.open( "sons/" + filename + ".wav", "w") as f:
        # 2 pistes.
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
    print(f"Fichier cre : {os.path.abspath(filename)}")  


