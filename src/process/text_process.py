import src.tts.vowel as v
import src.tts.consonant as cst
import numpy as np


#           >>> fonctions de découpage <<<


def decouper(fil,langue):
    '''
    Prends en argument un texte et une langue et
    decoupe de manière appropriée en sons
    Pour langue : 0=en 1=fr 2=jp

    :param fil: texte à découper
    :param langue: langue utilisée pour le découpage
    '''
    if langue > 2 or langue < 0 :
        raise ValueError("paramètre langue incorrect : ", langue, " non reconnu.\n")

    l = len(fil)
    warned = False

    if langue == 0 :
        return decoupe_en(fil,l,warned)

    elif langue == 2 :
        return decoupe_jap(fil,l,warned)

    return []


def emincer(d):
    '''
    efface les doublons et fusionne ce qui va ensemble

    :param d: liste des sons découpés
    '''
    i = 1
    n = len(d)
    e = []

    if d == '' or n == 0 :
        return []

    cact = d[0]
    nact = 1

    while i < n :

        if d[i] == cact :

            nact += 1
            i += 1

        elif d[i] == '-' :

            e.append((cact,nact))
            e.append(('-',0.2))

            if i + 1 < n :
                cact = d[i+1]
                nact = 1
                i += 2
            else :
                i += 1

        else :

            e.append((cact,nact))
            cact = d[i]
            nact = 1
            i += 1

    e.append((cact,nact))

    return e


#           >>> découpage japonais <<<

# Durées typiques des consonnes en japonais (en secondes)
DUR_OCC_S  = 0.055   # occlusives sourdes  : k, t, p
DUR_OCC_V  = 0.060   # occlusives sonores  : g, d, b
DUR_FRIC_S = 0.075   # fricatives sourdes  : s, sh, h, f
DUR_FRIC_V = 0.080   # fricatives sonores  : z, j
DUR_AFFR   = 0.080   # affriquées          : ts (つ), ch (ち)
DUR_NAS    = 0.065   # nasales             : n, m
DUR_APPR   = 0.040   # approximantes       : y, w, r



def decoupe_jap(fil,l,warned):
    """
    découpe selon langue japonaise

    :param fil: texte à découper
    :param l: longueur du texte
    :param warned: indique si un avertissement a déjà été affiché
    """
    decoupe = []

    filtre = [81,86,88,113,118,120]
    voyelles = ["a","e","i","o","u","A","E","I","O","U","-"]

    precedent_consonne = False
    prem_char = True
    prec = ""

    for i in range(0,l) :

        val = ord(fil[i])

        if (val == 32 or 64 < val < 91 or 95 < val < 123 or val == 45) and val not in filtre :

            char = fil[i]

            if char in voyelles :

                if precedent_consonne and len(decoupe) > 0 :

                    decoupe[-1] = prec + char
                    precedent_consonne = False

                else :

                    decoupe.append(char)

            else :

                if char == " " :

                    if prec != char :
                        decoupe.append(char)

                    precedent_consonne = False

                elif not prem_char :

                    if char == "h" and (prec == "s" or prec == "c") :

                        decoupe[-1] = prec + char

                    else :

                        decoupe.append(char)
                        precedent_consonne = True

                else :

                    decoupe.append(char)
                    precedent_consonne = True

            if len(decoupe) > 0 :
                prec = decoupe[-1]

            prem_char = False

        elif not warned :

            print("\n /!\\ Des caracères non acceptés sont apparus dans la soumission, ils seront automatiquement ignorés (Cf :", fil[i],")\n")
            warned = True

    return decoupe

#           >>> TABLE DE DISPATCH : syllabe romaji → fabrique <<<


# Chaque valeur est soit None (voyelle pure, pas de consonne)
# soit un callable sans argument qui génère (func, duree).
# Le bruit est re-généré à chaque appel pour une légère variation naturelle.

_DISPATCH = {
    # Voyelles pures : pas de consonne
    'a': None, 'i': None, 'u': None, 'e': None, 'o': None,

    # か行 — occlusive vélaire sourde
    'ka': lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 6000),
    'ki': lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 6000),
    'ku': lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 6000),
    'ke': lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 6000),
    'ko': lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 6000),

    # さ行 — fricative alvéolaire sourde ; sh (し) palatale
    'sa':  lambda: cst.fricativeSourde(DUR_FRIC_S, 4000, 8000),
    'shi': lambda: cst.fricativeSourde(DUR_FRIC_S, 2000, 5000),
    'su':  lambda: cst.fricativeSourde(DUR_FRIC_S, 4000, 8000),
    'se':  lambda: cst.fricativeSourde(DUR_FRIC_S, 4000, 8000),
    'so':  lambda: cst.fricativeSourde(DUR_FRIC_S, 4000, 8000),
    # た行 — t alvéolaire ; ch (ち) affriquée palatale ; ts (つ) affriquée
    'ta':  lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 8000),
    'chi': lambda: cst.affriquees(DUR_AFFR, 2000, 5000),
    'tsu': lambda: cst.affriquees(DUR_AFFR, 4000, 8000),
    'te':  lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 8000),
    'to':  lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 8000),

    # な行 — nasale alvéolaire
    'na': lambda: cst.nasale(DUR_NAS, f_anti=1000),
    'ni': lambda: cst.nasale(DUR_NAS, f_anti=1000),
    'nu': lambda: cst.nasale(DUR_NAS, f_anti=1000),
    'ne': lambda: cst.nasale(DUR_NAS, f_anti=1000),
    'no': lambda: cst.nasale(DUR_NAS, f_anti=1000),

    # は行 — h glottale aspirée ; f (ふ) labiodentale
    'ha': lambda: cst.fricativeSourde(DUR_FRIC_S,  500, 3000),
    'hi': lambda: cst.fricativeSourde(DUR_FRIC_S,  500, 3000),
    'fu': lambda: cst.fricativeSourde(DUR_FRIC_S, 5000, 9000),
    'he': lambda: cst.fricativeSourde(DUR_FRIC_S,  500, 3000),
    'ho': lambda: cst.fricativeSourde(DUR_FRIC_S,  500, 3000),

    # ま行 — nasale bilabiale
    'ma': lambda: cst.nasale(DUR_NAS, f_anti=800),
    'mi': lambda: cst.nasale(DUR_NAS, f_anti=800),
    'mu': lambda: cst.nasale(DUR_NAS, f_anti=800),
    'me': lambda: cst.nasale(DUR_NAS, f_anti=800),
    'mo': lambda: cst.nasale(DUR_NAS, f_anti=800),

    # や行 — approximante palatale
    'ya': lambda: cst.approx_y(DUR_APPR),
    'yu': lambda: cst.approx_y(DUR_APPR),
    'yo': lambda: cst.approx_y(DUR_APPR),

    # ら行 — tap/flap alvéolaire
    'ra': lambda: cst.approx_r(DUR_APPR),
    'ri': lambda: cst.approx_r(DUR_APPR),
    'ru': lambda: cst.approx_r(DUR_APPR),
    're': lambda: cst.approx_r(DUR_APPR),
    'ro': lambda: cst.approx_r(DUR_APPR),

    # わ行 — approximante labio-vélaire
    'wa': lambda: cst.approx_w(DUR_APPR),

    # が行 — occlusive vélaire sonore
    'ga': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 4000),
    'gi': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 4000),
    'gu': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 4000),
    'ge': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 4000),
    'go': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 4000),

    # ざ行 — fricative alvéolaire sonore ; j (じ) sonore palatale
    'za': lambda: cst.fricativeSonore(DUR_FRIC_V, 4000, 8000),
    'ji': lambda: cst.fricativeSonore(DUR_FRIC_V, 2000, 5000),
    'zu': lambda: cst.fricativeSonore(DUR_FRIC_V, 4000, 8000),
    'ze': lambda: cst.fricativeSonore(DUR_FRIC_V, 4000, 8000),
    'zo': lambda: cst.fricativeSonore(DUR_FRIC_V, 4000, 8000),

    # だ行 — occlusive alvéolaire sonore (di/du → ji/zu en japonais moderne)
    'da': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 5000),
    'de': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 5000),
    'do': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 5000),

    # ば行 — occlusive bilabiale sonore
    'ba': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 3000),
    'bi': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 3000),
    'bu': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 3000),
    'be': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 3000),
    'bo': lambda: cst.occlusiveSonore(DUR_OCC_V, 0, 3000),

    # ぱ行 — occlusive bilabiale sourde (aspiration plus large)
    'pa': lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 10000),
    'pi': lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 10000),
    'pu': lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 10000),
    'pe': lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 10000),
    'po': lambda: cst.occlusiveSourde(DUR_OCC_S, 0, 10000),

    # ん — nasale syllabique (durée étendue, pas de voyelle suivante)
    'nn': lambda: cst.nasale(DUR_NAS * 1.5, f_anti=900),
}


# Mapping : syllabe romaji → voyelle correspondante
_VOYELLE = {
    'a':'a',  'i':'i',  'u':'u',  'e':'e',  'o':'o',
    'ka':'a', 'ki':'i', 'ku':'u', 'ke':'e', 'ko':'o',
    'sa':'a', 'shi':'i','su':'u', 'se':'e', 'so':'o',
    'ta':'a', 'chi':'i','tsu':'u','te':'e', 'to':'o',
    'na':'a', 'ni':'i', 'nu':'u', 'ne':'e', 'no':'o',
    'ha':'a', 'hi':'i', 'fu':'u', 'he':'e', 'ho':'o',
    'ma':'a', 'mi':'i', 'mu':'u', 'me':'e', 'mo':'o',
    'ya':'a', 'yu':'u', 'yo':'o',
    'ra':'a', 'ri':'i', 'ru':'u', 're':'e', 'ro':'o',
    'wa':'a',
    'ga':'a', 'gi':'i', 'gu':'u', 'ge':'e', 'go':'o',
    'za':'a', 'ji':'i', 'zu':'u', 'ze':'e', 'zo':'o',
    'da':'a', 'de':'e', 'do':'o',
    'ba':'a', 'bi':'i', 'bu':'u', 'be':'e', 'bo':'o',
    'pa':'a', 'pi':'i', 'pu':'u', 'pe':'e', 'po':'o',
    'nn': '-',
}


#           >>> FONCTIONS EN LIEN AVEC PROCESS <<<


def cth(syl):
    """
    Consonant to Harmonic  (analogue de vth() dans vowel.py)
    Prend une syllabe romaji et retourne (func, duree) de sa consonne.
    Retourne (fonction nulle, 0.0) pour une voyelle pure.
    Le bruit est re-généré à chaque appel : légère variation naturelle.

    :param syl: syllabe en romaji (ex: 'ka', 'shi', 'tsu', 'nn')
    :return: tuple (func, duree)
        - func   : f(t) → amplitude, compatible avec Note/createSignal
        - duree  : durée de la consonne en secondes (0.0 si aucune)
    """
    syl_lower = syl.lower()
    if syl_lower not in _DISPATCH:
        print("syllabe inconnue passée :", syl)
        return lambda t: np.zeros_like(np.asarray(t, dtype=float)), 0.0
    fabrique = _DISPATCH[syl_lower]
    if fabrique is None:   # voyelle pure
        return lambda t: np.zeros_like(np.asarray(t, dtype=float)), 0.0
    return fabrique()


def voyelle_de(syl):
    """
    Retourne la voyelle (caractère) correspondant à une syllabe romaji.

    :param syl: syllabe en romaji
    :return: caractère voyelle ('a','i','u','e','o') ou '-'
    """
    return _VOYELLE.get(syl.lower(), '-')


def syllaber(romajis, pas):
    """
    Transforme une liste de syllabes romaji en blocs partition
    (consonne + voyelle pour chaque syllabe).
    Analogue de voyeller() dans vowel.py.

    :param romajis: liste de syllabes en romaji (ex: ['ka', 'ta', 'na'])
    :param pas:     durée arbitraire de la voyelle (unité temporelle, en secondes)
    :return: liste de blocs [[[duree, volume, func]]]
    """
    tab = []
    for syl in romajis:
        func_c, dur_c = cth(syl)
        func_v = v.vth(voyelle_de(syl))
        if dur_c > 0:
            tab = tab + [[[dur_c, 1, func_c]]]
        tab = tab + [[[pas, 1, func_v]]]
    return tab

#           >>> découpage anglais <<<


def decoupe_en(fil,l,warned):
    """
    découpe selon langue anglaise

    :param fil: texte à découper
    :param l: longueur du texte
    :param warned: indique si un avertissement a déjà été affiché
    """
    decoupe = []

    voyelles = ['a','e','i','o','u','A','E','I','O','U']
    ponct = [' ',',','-','\'']

    if fil == "" :
        return decoupe

    prec = fil[0]
    precedent_consonne = True

    if prec in voyelles :
        precedent_consonne = False

    for i in range(1,l) :

        val = ord(fil[i])

        if (val == 32 or val == 36 or val == 45 or 64 < val < 91 or 96 < val < 123) :

            char = fil[i]

            if char in voyelles :

                if precedent_consonne :
                    decoupe.append(prec + char)

                else :
                    decoupe.append(char)

                precedent_consonne = False

            elif char in ponct :

                if precedent_consonne :
                    decoupe.append(prec)

                decoupe.append(char)
                precedent_consonne = False

            else :

                if precedent_consonne :
                    decoupe.append(prec)

                precedent_consonne = True

            prec = char

        elif not warned :

            print("\n /!\\ Des caracères non acceptés sont apparus dans la soumission, ils seront automatiquement ignorés (Cf :", fil[i],")\n")
            warned = True

    if len(fil) == 1 :

        decoupe.append(fil[0])

    elif prec not in decoupe :

        decoupe.append(prec)

    return decoupe