from tkinter import *
import notes as n
import base_wave_func as bwf

fenetre = Tk()
fenetre.title("Piano")
fenetre.minsize(800, 400)
fenetre.eval('tk::PlaceWindow . center')


# Ce fichier est une page tkinter qui genere une surface ou tu peux entrer ta propre melodie

def tab():  # génère tb de freq
    note_hz = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, -1, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0]

    for i in range(5):
        note_hz.append(n.do[i])
        note_hz.append(n.reb[i])
        note_hz.append(n.re[i])
        note_hz.append(n.mib[i])
        note_hz.append(n.mi[i])
        note_hz.append(n.fa[i])
        note_hz.append(n.solb[i])
        note_hz.append(n.sol[i])
        note_hz.append(n.lab[i])
        note_hz.append(n.la[i])
        note_hz.append(n.sib[i])
        note_hz.append(n.si[i])

    note_hz.append(n.do[5])
    return note_hz


liste_frequence = tab()
print(len(liste_frequence))


def traduction_note():  # mettre les mots en fréquences
    note_frequence = []
    texte = entree.get()
    liste_texte = list(texte)

    for i in range(len(liste_texte)):
        indice = ord(liste_texte[i])
        if indice < len(liste_frequence):
            note_frequence.append(liste_frequence[indice])

    print(note_frequence)


# --- Titre ---
titre = Label(
    fenetre,
    text="Veuillez entrer une mélodie \n Espace = Soupire          ! = prolongement d'un temps",
    font=("Arial", 14)
)
titre.pack(pady=10)


photo = PhotoImage(file="piano.png")
label_image = Label(fenetre, image=photo)
label_image.pack(pady=10)


# --- Cadre pour l'entrée ---
cadre = Frame(fenetre)
cadre.pack(pady=10)

expression = StringVar()
expression.set("")

entree = Entry(cadre, textvariable=expression, width=60)
entree.pack()


# --- Centrage fenêtre ---
largeur = 1500
hauteur = 500
ecran_largeur = fenetre.winfo_screenwidth()
ecran_hauteur = fenetre.winfo_screenheight()
x = (ecran_largeur // 2) - (largeur // 2)
y = (ecran_hauteur // 2) - (hauteur // 2)
fenetre.geometry(f"{largeur}x{hauteur}+{x}+{y}")


# --- Bouton ---
bouton = Button(cadre, text="Émettre", command=traduction_note)
bouton.pack()


fenetre.mainloop()