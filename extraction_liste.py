import wave
import numpy as np


# Une fonction qui prend en entre un fichier audio et qui renvoie une liste :
#[ ( position du trame audio, la frequence a cette position ) ]


def liste_hz(nom_audio, taille_fenetre=1024):
    frequence = nom_audio.getframerate()    #frequence d'echantillionage
    nb_trames = nom_audio.getnframes()      #Le nombre de trame audio
    nb_canaux = nom_audio.getnchannels()    #Le nombre de canaux audio
    sample_width = nom_audio.getsampwidth() #La largeur de l'echantillon en octet

    
    signal = nom_audio.readframes(nb_trames) #lit et renvoie nb_trames audios

  
    if sample_width == 2: #On verifie si la largeur de l'echantillon est de 2 octets (ou 16 bits)
        data = np.frombuffer(signal, dtype=np.int16) 
    else:
        raise ValueError("Format audio (pas 16 bits)") 

    
    if nb_canaux == 2:
        data = data[::2]

    resultats = []

    for i in range(0, len(data) - taille_fenetre, taille_fenetre):
        segment = data[i:i + taille_fenetre]
        fft = np.fft.fft(segment) # 
        freqs = np.fft.fftfreq(len(segment), d=1/frequence) #renvoie les frequences du signal calcule dans la DFT

        amplitudes = np.abs(fft[:len(fft)//2])
        freqs = freqs[:len(freqs)//2]

        frequence_max = freqs[np.argmax(amplitudes)]
        resultats.append((i, frequence_max))

    return resultats

#A changer 
    xingxing = wave.open("little_star.wav", "rb")
    liste = liste_hz(xingxing)
    xingxing.close()

#print("Liste des frequences  :", liste)



# Une fonction qui filtre la liste des frequences 

def filtre (liste) : 
    
    (_,y)=liste[0]
    i = 1
    l = len(liste)
    
    while(i!=(l)) :
        
        (_,y2) = liste[i]       
        
        if y==y2 :              
            _ = liste.pop(i)    
            l += -1             
            i += -1             
            
        y = y2
        i +=1                   
    return liste




#print("la liste filtree est : ", filtre(liste) )

















