import math

class City:
    def __init__(self, idd, time):
        self.id = idd
        self.time = time
        self.lignes = []
        #self.gares = []
        self.allTimes = []



def search_for_cities(original, current, villes, time=0):
    for l in current.lignes:
        if l["arrivee"]-1 != original.id:
            goHere = True
            for aT in original.allTimes:
                if aT[0] == l["arrivee"]:
                    if time >= aT[1]:
                        goHere = False
                        break
                    else:
                        original.allTimes.remove(aT)
            if goHere:
                ttime = time + current.time + l["temps"]
                original.allTimes.append((l["arrivee"], ttime))

                #print("Going from " + str(l["depart"]) + " to " + str(l["arrivee"]) + " in " + str(ttime))
                search_for_cities(original, villes[l["arrivee"]-1], villes, time=ttime)
        


def la_meilleure_ville0(villes):
    for v in villes:
        if len(v.lignes) == 0:
            print("-1")
            continue
        
        search_for_cities(v, v, villes)

        total = 0.0
        for t in v.allTimes :
            total += t[1]
        total /= float(len(v.allTimes))
        print(math.floor(total))


(n, m, g) = list(map(int, input().split()))
villes = [None] * n

for i in range(0, n):
    villes[i] = City(i, int(input()))

lignes = [None] * m

for j in range(0, m):
    (depart, arrivee, temps) = list(map(int, input().split()))
    trajet = {"depart":depart, "arrivee":arrivee, "temps":temps}
    lignes[j] = trajet

    villes[depart-1].lignes.append(trajet)

gares = [None] * g

for k in range(0, g):
    (dep, arr, tmp) = list(map(int, input().split()))
    traj = {"depart":dep, "arrivee":arr, "temps":tmp}
    gares[k] = traj

    #villes[dep-1].gares.append(traj)

#Destroy the 'gare' problem by saying that if there's a 'gare' then there is a 'ligne' whith:
#   time = gare + otherLigne

for g in gares:
    for l in villes[g["arrivee"]-1].lignes: # biais pour les gares après des gares
        gare = {"depart":g["depart"], "arrivee":l["arrivee"], "temps":g["temps"]+l["temps"]}
        villes[g["depart"]-1].lignes.append(gare)


la_meilleure_ville0(villes)