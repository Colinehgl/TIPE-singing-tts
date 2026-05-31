import TTS.base_wave_func as bwf
import numpy as np
import PROCESS.text_process as p

fre = 44100

def gaussian_formant(f_center, delta, fondamentale=130, nb_harm=30, amp_dft=3):
    """
    Génère des tableaux partiels avec amplitude pondérée par une gaussienne
    centrée sur f_center, de largeur delta.
    """
    tab = []
    for i in range(1, nb_harm + 1):
        f = i * fondamentale
        amp = amp_dft * np.exp(-((f - f_center)**2) / (2 * delta**2))   # gausienne
        if amp > 0.05:                                                  # seuil pour ne pas additionner du bruit irrélévant
            tab.append((amp, [f]))
    return tab

def write_mltp_harmo(freq):
    """
    freq : liste de tuples (k, freqs)
        - k : facteur de pondération (amplitude)
        - freqs : liste de fréquences (en Hz)
    Retourne une fonction f(t) = somme pondérée de sinusoïdes.
    """
    def func(t):
        val = 0
        count = 0
        for k, freqs_list in freq:
            for w in freqs_list:
                count += 1
                # Somme pondérée des sinusoïdes
                val += k * np.sin(2 * np.pi * w * t)
        if count != 0:
            val /= count  # normalisation
        return val

    return func

def voyeller(fil,pas):
    '''
    permet de transformer un string de voyelle en sons
    
    :param fil: string de caractères
    :param pas: durée arbitraire de l'unité dans le tableau émincé
    '''

    def formant(chr):
        match chr:
            case '-':
                return lambda x : 0
            case 'a' :
                return fa
            case 'o' : 
                return fo
            case 'i' :
                return fi
            case 'e' :
                return fe
            case _ : 
                print( "caractère incorrect passsé : ",chr)
                return lambda x : 2/0

    u = p.emincer(p.decouper(fil,2))
    print("bb", u)
    tab  = []
    for vnb in u :
        v,nb = vnb 
        tab = tab + [[[pas*nb,1,formant(v)]]]
    return tab

params_A = (
    gaussian_formant(800,  150, amp_dft=4)
  + gaussian_formant(1200, 200, amp_dft=2)
  + gaussian_formant(2700, 300, amp_dft=0.8)
)

params_O = (
    gaussian_formant(450, 80,  amp_dft=4)   
  + gaussian_formant(750, 90,  amp_dft=2)  
  + gaussian_formant(2500, 250, amp_dft=0.4)
)

params_E = (
    gaussian_formant(380,  100)             
  + gaussian_formant(2200, 180)
  + gaussian_formant(2900, 220)
)

params_I = (
    gaussian_formant(270,  80)
  + gaussian_formant(2300, 180)  
  + gaussian_formant(3000, 250, amp_dft=1)
)

params_U = (
    gaussian_formant(300, 60,  amp_dft=4)   
  + gaussian_formant(700, 80,  amp_dft=2.5) 
  + gaussian_formant(2200, 200, amp_dft=0.4)
)

params_Y = (
    gaussian_formant(250, 60,   amp_dft=4)  
  + gaussian_formant(1800, 150, amp_dft=3) 
  + gaussian_formant(2100, 200, amp_dft=1.5)
)

fha = write_mltp_harmo( params_A ) 
fho = write_mltp_harmo( params_O ) 
fhe = write_mltp_harmo( params_E ) 
fhi = write_mltp_harmo( params_I ) 
fhu = write_mltp_harmo( params_U )
fhy = write_mltp_harmo( params_Y )

# tableau fonctions voyelles
tfv = [fac,foc,fec,fic,fuc,fyc] 