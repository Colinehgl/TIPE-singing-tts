import wave
import struct


#           >>> COMBINAISON DE FICHIERS WAVE <<<


def combiner(son1, son2, son_sortie):
    """
    Superpose deux fichiers .wav en additionnant leurs échantillons.
    Les deux fichiers doivent avoir les mêmes paramètres (canaux, largeur, fréquence).
    La sortie est écrêtée entre -32768 et 32767 pour rester en 16 bits.

    :param son1:      chemin vers le premier fichier .wav
    :param son2:      chemin vers le deuxième fichier .wav
    :param son_sortie: chemin du fichier .wav de sortie
    """
    with wave.open(son1, 'rb') as wf1, wave.open(son2, 'rb') as wf2:

        # Vérification de la compatibilité des fichiers
        if wf1.getparams()[:3] != wf2.getparams()[:3]:
            raise ValueError("Les fichiers n'ont pas les mêmes paramètres (canaux, largeur, fréquence).")

        frames1 = wf1.readframes(wf1.getnframes())
        frames2 = wf2.readframes(wf2.getnframes())

        n_samples1 = len(frames1) // 2
        n_samples2 = len(frames2) // 2
        samples1   = struct.unpack("<" + str(n_samples1) + "h", frames1)
        samples2   = struct.unpack("<" + str(n_samples2) + "h", frames2)

        min_len  = min(len(samples1), len(samples2))
        combined = [
            max(-32768, min(32767, samples1[i] + samples2[i]))
            for i in range(min_len)
        ]

        # Écriture du fichier de sortie
        with wave.open(son_sortie, 'wb') as output:
            output.setparams(wf1.getparams())
            output.writeframes(struct.pack("<" + str(len(combined)) + "h", *combined))

    print(f"Fichier combiné enregistré sous '{son_sortie}' ({len(combined)} échantillons).")


print("csn correctement importé")