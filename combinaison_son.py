import wave
import struct

#Cette fonction combine deux fichier wave , les superpose

def combiner(son1, son2, son_sortie):

    with wave.open(son1, 'rb') as wf1, wave.open(son2, 'rb') as wf2:
         # Verifier compatibilite des fichiers
        if wf1.getparams()[:3] != wf2.getparams()[:3]:
            raise ValueError("Les fichiers n'ont pas les memes parametres (canaux, taille, frequence).")


        # Lire les frames
        frames1 = wf1.readframes(wf1.getnframes())
        frames2 = wf2.readframes(wf2.getnframes())

        # Determiner le format
        n_samples1 = len(frames1) // 2 
        n_samples2 = len(frames2) // 2

        # Convertir en entiers 
        samples1 = struct.unpack("<" + str(n_samples1) + "h", frames1)
        samples2 = struct.unpack("<" + str(n_samples2) + "h", frames2)

        # Combinaison 
        min_len = min(len(samples1), len(samples2))
        combined = [
            max(-32768, min(32767, samples1[i] + samples2[i]))
            for i in range(min_len)
        ]

        # ecrire le son de sortie
        with wave.open(son_sortie, 'wb') as output:
            output.setparams(wf1.getparams())
            output.writeframes(struct.pack("<" + str(len(combined)) + "h", *combined))

    print(f" Fichier combine enregistre sous '{son_sortie}' ({len(combined)} echantillons).")



combiner ("sonyi.wav", "soner.wav","son_s.wav") 