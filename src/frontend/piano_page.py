import os
from tkinter import *
from tkinter import messagebox
from src.singing import notes as n


#           >>> forme de la fenêtre <<<


fenetre = Tk()
fenetre.title("Piano")
fenetre.minsize(800, 400)

largeur = 1500
hauteur = 650
ecran_largeur = fenetre.winfo_screenwidth()
ecran_hauteur = fenetre.winfo_screenheight()
x = (ecran_largeur // 2) - (largeur // 2)
y = (ecran_hauteur // 2) - (hauteur // 2)
fenetre.geometry(f"{largeur}x{hauteur}+{x}+{y}")


#           >>> utilité pour la fenêtre <<<


def tab():
    """
    renvoie le tableau utilisé pour associer au string rentré pour la mélodie en suite de fréquence
    """
    note_hz = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

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

def ecrire(a, b):
    print("a=", a, "b=", b)

def action_bouton():
    a = expressionSon.get().strip()
    b = expressionNomF.get().strip()
    
    if not a or not b:
        messagebox.showerror("Erreur", "Champs incomplets : veuillez remplir la mélodie et le nom du fichier.")
        label_statut.config(text="")
        return

    print(f"Mélodie : {a}")
    print(f"Nom du fichier : {b}")
    
    ecrire(a, b)
    
    chemin_actuel = os.path.dirname(os.path.abspath(__file__))
    chemin_complet = os.path.join(chemin_actuel, "SONS", b)
    label_statut.config(text=f"fichier créé : {chemin_complet}", fg="green")


#           >>> éléments fenêtre <<<


titre = Label(
    fenetre,
    text="Veuillez entrer une mélodie \n Espace = Soupire          ! = prolongement d'un temps",
    font=("Arial", 14),
)
titre.pack(pady=10)

photo = PhotoImage(file="src/frontend/piano.png")
label_image = Label(fenetre, image=photo)
label_image.pack(pady=10)

cadreSon = Frame(fenetre)
cadreSon.pack(pady=5)

labelSon = Label(cadreSon, text="Mélodie", font=("Arial", 11))
labelSon.pack()

expressionSon = StringVar()
entreeSon = Entry(cadreSon, textvariable=expressionSon, width=60)
entreeSon.pack()

cadreNomF = Frame(fenetre)
cadreNomF.pack(pady=5)

labelNomF = Label(cadreNomF, text="Nom du fichier", font=("Arial", 11))
labelNomF.pack()

expressionNomF = StringVar()
entreeNomF = Entry(cadreNomF, textvariable=expressionNomF, width=60)
entreeNomF.pack()

bouton = Button(fenetre, text="Émettre", command=action_bouton)
bouton.pack(pady=15)

label_statut = Label(fenetre, text="", font=("Arial", 11, "bold"))
label_statut.pack(pady=5)

fenetre.mainloop()