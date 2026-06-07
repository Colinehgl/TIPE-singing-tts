import numpy as np
import src.tts.base_wave_func as bwf
import src.tts.vowel as v

#           >>> PARAMÈTRES GLOBAUX <<<

FE  = 44100   # fréquence d'échantillonnage 
F0  = 130     # fréquence fondamentale glottale


#           >>> FONCTION GENERATRICE CONSONNES <<<


def occlusiveSourde(duree, f_low=0, f_high=8000):
    """
    OCCLUSIVES SOURDES : k, t, p 

    Occlusive sourde : silence (fermeture) + burst de bruit à décroissance
    exponentielle, filtré en bande selon le lieu d'articulation.

    Modèle temporel :
        [silence : 60 %]  [burst décroissant : 40 %]

    Points d'articulation :
        k  →  vélaire  (0–6000 Hz)
        t  →  alvéolaire (0–8000 Hz)
        p  →  bilabiale (0–10000 Hz)

    :param duree:  durée totale de la consonne (s)
    :param f_low:  fréquence basse du bruit de burst (Hz)
    :param f_high: fréquence haute du bruit de burst (Hz)
    """
    n     = int(duree * FE)
    n_sil = int(n * 0.60)
    n_bur = n - n_sil

    bruit = bwf.bandeBruit(f_low, f_high, n_bur)
    decay = np.exp(-5 * np.linspace(0, 1, n_bur))   # décroissance rapide
    signal = np.concatenate([np.zeros(n_sil), bruit * decay])
    return bwf.versFunc(signal, duree), duree

def occlusiveSonore(duree, f_low=0, f_high=4000):
    """
    OCCLUSIVES SONORES : g, d, b

    Occlusive sonore : pré-voisement harmonique + burst court + voix montante.
    La transition vers le voisement complet simule le VOT (Voice Onset Time) négatif.

    Modèle temporel :
        [pré-voix : 30 %]  [burst : 20 %]  [voix montante : 50 %]

    :param duree:  durée totale de la consonne (s)
    :param f_low:  fréquence basse du bruit de burst (Hz)
    :param f_high: fréquence haute du bruit de burst (Hz)
    """
    n     = int(duree * FE)
    n_pre = int(n * 0.30)
    n_bur = int(n * 0.20)
    n_voi = n - n_pre - n_bur

    pre  = bwf.harmBase(n_pre, nb_harm=5) * 0.30
    bur  = bwf.bandeBruit(f_low, f_high, n_bur) * np.exp(-3 * np.linspace(0, 1, n_bur))
    voi  = bwf.harmBase(n_voi, nb_harm=8) * np.linspace(0.3, 0.8, n_voi)

    signal = np.concatenate([pre, bur, voi])
    return bwf.versFunc(signal, duree), duree

def fricativeSourde(duree, f_low, f_high):
    """
    FRICATIVES SOURDES : s, sh, h, f

    Fricative sourde : bruit blanc filtré en bande avec enveloppe douce.
    La bande fréquentielle est caractéristique du lieu d'articulation :

        s   →  alvéolaire stridente   (4000–8000 Hz)
        sh  →  palatale               (2000–5000 Hz)
        h   →  glottale aspirée       (500–3000 Hz)
        f   →  labiodentale           (5000–9000 Hz)

    :param duree:  durée de la fricative (s)
    :param f_low:  fréquence basse de la bande (Hz)
    :param f_high: fréquence haute de la bande (Hz)
    """
    n      = int(duree * FE)
    signal = bwf.bandeBruit(f_low, f_high, n) * bwf.enveloppe(n, 0.10, 0.20)
    return bwf.versFunc(signal, duree), duree

def fricativeSonore(duree, f_low, f_high):
    """
    FRICATIVES SONORES : z, j

    Fricative sonore : bruit filtré + composante harmonique de voisement.
    Le "buzzing" grave (F0) s'ajoute au bruit filtré, caractéristique
    des fricatives sonores.

    :param duree:  durée de la fricative (s)
    :param f_low:  fréquence basse de la bande de bruit (Hz)
    :param f_high: fréquence haute de la bande de bruit (Hz)
    """
    n      = int(duree * FE)
    bruit  = bwf.bandeBruit(f_low, f_high, n) * 0.65
    vois   = bwf.harmBase(n, nb_harm=4) * 0.35
    signal = (bruit + vois) * bwf.enveloppe(n, 0.10, 0.20)
    return bwf.versFunc(signal, duree), duree

def affriquees(duree, f_low, f_high):
    """
    AFFRIQUÉES : ts, ch 

    Affriquée : occlusion brève + burst d'attaque + fricative.
    Combinaison séquentielle d'une occlusive et d'une fricative :

        ch (ち)  →  t + sh  (2000–5000 Hz)
        ts (つ)  →  t + s   (4000–8000 Hz)

    Modèle temporel :
        [silence : 30 %]  [burst : 15 %]  [fricative : 55 %]

    :param duree:  durée totale (s)
    :param f_low:  fréquence basse de la fricative (Hz)
    :param f_high: fréquence haute de la fricative (Hz)
    """
    n     = int(duree * FE)
    n_sil = int(n * 0.30)
    n_bur = int(n * 0.15)
    n_fri = n - n_sil - n_bur

    bur = bwf.bandeBruit(0, 8000, n_bur) * np.exp(-4 * np.linspace(0, 1, n_bur))
    fri = bwf.bandeBruit(f_low, f_high, n_fri) * bwf.enveloppe(n_fri, 0.05, 0.30)

    signal = np.concatenate([np.zeros(n_sil), bur, fri])
    return bwf.versFunc(signal, duree), duree

def nasale(duree, f_anti=1000):
    """
    NASALES : n, m

    Nasale : excitation harmonique filtrée avec anti-formant nasal.

    Modèle source-filtre :
        1. Excitation glottale (harmoniques 1/k)
        2. Filtre passe-bas doux à ~800 Hz   → absorption de la cavité nasale
        3. Anti-formant (notch gaussien)      → caractéristique des nasales

    Points d'articulation :
        n  →  alvéolaire  (f_anti ≈ 1000 Hz)
        m  →  bilabiale   (f_anti ≈  800 Hz)
        nn →  syllabique  (durée étendue)

    :param duree:  durée de la nasale (s)
    :param f_anti: fréquence de l'anti-formant (Hz)
    """
    n   = int(duree * FE)
    sig = bwf.harmBase(n, nb_harm=20)

    spectre = np.fft.rfft(sig)
    freqs   = np.fft.rfftfreq(n, 1 / FE)

    # Passe-bas doux : atténue les aigus (absorption nasale)
    lp    = np.where(freqs < 800, 1.0, np.exp(-(freqs - 800) / 400))
    # Anti-formant : filtre gaussien centré sur f_anti
    notch = 1 - 0.85 * np.exp(-((freqs - f_anti) ** 2) / (2 * 120 ** 2))

    spectre *= lp * notch
    sig_f = np.fft.irfft(spectre, n)
    mx    = np.max(np.abs(sig_f))
    sig_f = sig_f / mx if mx > 0 else sig_f

    signal = sig_f * bwf.enveloppe(n, 0.10, 0.20)
    return bwf.versFunc(signal, duree), duree

# >>> PPROXIMANTES : y, w, r 

def approx_y(duree):
    """
    Approximante palatale /y/ :
    Synthèse additive avec formants proches de /i/ (F1 ≈ 270 Hz, F2 ≈ 2300 Hz),
    à durée courte et décroissance rapide vers la voyelle suivante.

    :param duree: durée en s de la consonne
    """
    n   = int(duree * FE)
    t   = np.arange(n) / FE
    sig = np.zeros(n)
    for k in range(1, 15):
        f   = k * F0
        amp = (
            np.exp(-((f -  270) ** 2) / (2 *  80 ** 2))
          + 0.5 * np.exp(-((f - 2300) ** 2) / (2 * 180 ** 2))
        )
        if amp > 0.05:
            sig += amp * np.sin(2 * np.pi * f * t)
    mx     = np.max(np.abs(sig))
    sig    = sig / mx if mx > 0 else sig
    signal = sig * bwf.enveloppe(n, 0.15, 0.60)
    return bwf.versFunc(signal, duree), duree

def approx_w(duree):
    """
    Approximante labio-vélaire /w/ :
    Synthèse additive avec formants proches de /u/ (F1 ≈ 300 Hz, F2 ≈ 700 Hz),
    à durée courte et décroissance rapide.

    :param duree: durée en s de la consonne
    """
    n   = int(duree * FE)
    t   = np.arange(n) / FE
    sig = np.zeros(n)
    for k in range(1, 15):
        f   = k * F0
        amp = (
            np.exp(-((f - 300) ** 2) / (2 *  60 ** 2))
          + 0.3 * np.exp(-((f - 700) ** 2) / (2 *  80 ** 2))
        )
        if amp > 0.05:
            sig += amp * np.sin(2 * np.pi * f * t)
    mx     = np.max(np.abs(sig))
    sig    = sig / mx if mx > 0 else sig
    signal = sig * bwf.enveloppe(n, 0.15, 0.60)
    return bwf.versFunc(signal, duree), duree

def approx_r(duree):
    """
    Battement /r/ japonais (tap / flap alvéolaire) :
    Très court silence (occlusion) suivi d'une transition voisée montante.

    :param duree: durée en s de la consonne
    """
    n     = int(duree * FE)
    n_sil = int(n * 0.35)
    n_voi = n - n_sil
    voi   = bwf.harmBase(n_voi, nb_harm=10) * np.linspace(0, 0.85, n_voi)
    signal = np.concatenate([np.zeros(n_sil), voi])
    return bwf.versFunc(signal, duree), duree


print("cst correctement importé")