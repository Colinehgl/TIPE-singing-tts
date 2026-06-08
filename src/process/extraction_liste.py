import numpy as np


#           >>> EXTRACTION DE FRÉQUENCES <<<


def liste_hz(nom_audio, taille_fenetre=1024):
    """
    Prend un fichier audio ouvert et renvoie la liste des fréquences dominantes
    relevées fenêtre par fenêtre sur toute la durée du signal.
    Seuls les fichiers 16 bits sont acceptés.
    Pour les fichiers stéréo, seul le canal gauche est analysé.

    :param nom_audio:      objet wave.Wave_read déjà ouvert
    :param taille_fenetre: nombre d'échantillons par fenêtre d'analyse FFT
    """
    frequence   = nom_audio.getframerate()
    nb_trames   = nom_audio.getnframes()
    nb_canaux   = nom_audio.getnchannels()
    sample_width = nom_audio.getsampwidth()

    signal = nom_audio.readframes(nb_trames)

    if sample_width != 2:
        raise ValueError("Format audio non supporté (attendu : 16 bits).")

    data = np.frombuffer(signal, dtype=np.int16)

    if nb_canaux == 2:
        data = data[::2]

    resultats = []

    for i in range(0, len(data) - taille_fenetre, taille_fenetre):
        segment  = data[i:i + taille_fenetre]
        fft      = np.fft.fft(segment)
        freqs    = np.fft.fftfreq(len(segment), d=1 / frequence)

        amplitudes    = np.abs(fft[:len(fft) // 2])
        freqs         = freqs[:len(freqs) // 2]
        frequence_max = freqs[np.argmax(amplitudes)]

        resultats.append((i, frequence_max))

    return resultats


#           >>> FILTRAGE DE LA LISTE <<<


def filtre(liste):
    """
    Supprime les doublons consécutifs dans une liste de tuples (position, fréquence).
    Deux entrées adjacentes ayant la même fréquence sont fusionnées en une seule.

    :param liste: liste de tuples (position, frequence)
    """
    if not liste:
        return liste

    (_, y) = liste[0]
    i = 1
    l = len(liste)

    while i != l:
        (_, y2) = liste[i]

        if y == y2:
            liste.pop(i)
            l -= 1
        else:
            y = y2
            i += 1

    return liste


print("el correctement importé")