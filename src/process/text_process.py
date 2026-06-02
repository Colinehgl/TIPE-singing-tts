
def decouper(fil,langue):
    '''
    Prends en argument un texte et une langue et
    decoupe de manière appropriée en sons
    Pour langue : 0=en 1=fr 2=jp
    '''
    if langue > 2 or langue < 0 :
        raise ValueError("paramètre langue incorrect : ", langue, " non reconnu.\n")

    l = len(fil)
    warned = False

    if langue == 0 :
        return decoupe_en(fil,l,warned)
    elif langue == 2 : 
        return decoupe_jap(fil,l,warned)
    return ""


def emincer(d):
    '''
    efface les doublons et fusionne ce qui va ensemble
    
    :param decoupe: Description
    '''
    i = 1
    n = len(d)
    e = []

    if d == '' :
        return ('',0)


    print("aa",d)
    cact = d[0] #caractère actuel        
    nact = 1  #nombre actuel de ce caratcère
    while( i < n ): #pour l'instant, fusionne 'a' et 'a' en ('a',2)
        if d[i] == cact :
            nact += 1
            i += 1
        elif d[i] == '-' :
            e.append((cact,nact))
            e.append(('-', 0.2))
            nact = 1
            cact = d[i+1]
            i += 2
        else :
            e.append((cact,nact))
            nact = 0
            cact = d[i]
    e.append((cact,nact))
    return e





def decoupe_jap(fil,l,warned):
    """
    découpe selon langue japonaise
    """
    decoupe = []
    filtre = [81,86,88,113,118,120]
    voyelles = ["a","e","i","o","u","A","E","I","O","U","-"]
    precedent_consonne = False
    prem_char = True

    for i in range(0,l):
        val = ord(fil[i])
        # vérification si caractère adapté
        if (val == 32 or 64 < val < 91 or 95 < val < 123 or val == 45) and val not in filtre:
            # traitement du caractère accepté
            char = fil[i]

            if char in voyelles:
                if precedent_consonne:
                    decoupe[-1] = prec +  char
                    precedent_consonne = False
                else:
                    decoupe.append(char)
            else:
                if char == " ":
                    if not prec == char:
                        decoupe.append(char)
                        precedent_consonne = False
                elif not prem_char :
                    if (char == "h" and (prec == "s" or prec == "c")) :
                        decoupe[-1] = prec +  char
                    else :
                        decoupe.append(char)
                        precedent_consonne = True 
                else :
                    decoupe.append(char)
                    precedent_consonne = True 
            prec = decoupe[-1]
            prem_char = False
        elif not warned :
            print("\n /!\\ Des caracères non acceptés sont apparus dans la soumission, ils seront automatiquement ignorés (Cf :", fil[i],")\n")
            warned = True


    return decoupe     

def decoupe_en(fil,l,warned): 
    decoupe = []
    voyelles = ['a','e','i','o','u','A','E','I','O','U']
    ponct = [' ',',','-','\'']
    precedent_consonne = True
    prec = ''
    if fil == "":
        return decoupe
    else:
        prec = fil[0]
        if prec in voyelles :
            precedent_consonne = False

    for i in range(1,l):
        val = ord(fil[i])
        # vérification si caractère adapté
        if (val == 32 or val == 36 or val == 45 or 64 < val < 91 or 96 < val < 123 ) :
            # traitement du caractère accepté
            char = fil[i]
            if (char in voyelles) :
                #print("voyelle")
                if precedent_consonne :
                    char = prec + char
                decoupe.append(char)
                precedent_consonne = False
            elif (char in ponct):
                #print("ponct")
                if precedent_consonne :
                    decoupe.append(prec)
                decoupe.append(char)
                precedent_consonne = False
            else :
                #print("cons")
                if precedent_consonne :
                    decoupe.append(prec)
                else:
                    precedent_consonne = True
        elif not warned :
            print("\n /!\\ Des caracères non acceptés sont apparus dans la soumission, ils seront automatiquement ignorés (Cf :", fil[i],")\n")
            warned = True
        prec = char
    decoupe.append(prec)

    return decoupe     

