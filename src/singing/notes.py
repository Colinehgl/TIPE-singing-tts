do   = [32.703,  65.406, 130.813, 261.626, 523.251, 1046.502]   # C1 .. C6
reb  = [34.648,  69.295, 138.591, 277.183, 554.365, 1108.731]   # D♭ / C#
re   = [36.708,  73.416, 146.832, 293.665, 587.330, 1174.659]   # D
mib  = [38.891,  77.782, 155.563, 311.127, 622.254, 1244.508]   # E♭ / D#
mi   = [41.203,  82.407, 164.814, 329.628, 659.255, 1318.510]   # E
fa   = [43.654,  87.307, 174.614, 349.228, 698.456, 1396.913]   # F
solb = [46.249,  92.499, 184.997, 369.994, 739.989, 1479.979]   # F# / G♭ (SOL♭ ajouté)
sol  = [49.000,  98.000, 196.000, 392.000, 783.991, 1567.982]   # G
lab  = [51.913, 103.826, 207.652, 415.305, 830.609, 1661.219]   # A♭ / G#
la   = [55.000, 110.000, 220.000, 440.000, 880.000, 1760.000]   # A
sib  = [58.270, 116.541, 233.082, 466.164, 932.328, 1864.655]   # B♭ / A#
si   = [61.735, 123.471, 246.942, 493.883, 987.767, 1975.533]   # B

def tabliser():
    t = []
    for i in range(5) : 
        t.append(do[i])
        t.append(reb[i])
        t.append(re[i])
        t.append(mib[i])
        t.append(mi[i])
        t.append(fa[i])
        t.append(sol[i])
        t.append(lab[i])
        t.append(la[i])
        t.append(sib[i])
        t.append(si[i])
    return t 
full = tabliser()


def part_to_bwf(partition):
    tab = []
    assert( (partition is not None))
    while(partition != []):
        son = partition.pop()
        note,duree = son
        tab.append([[duree,1,note]])
    tab.reverse()
    return tab


