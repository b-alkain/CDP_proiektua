from multiprocessing import Pool

import collections
import random
import time

# Graph
import community
import networkx as nx
# Combinations
import itertools

#import matplotlib.pyplot as plt
#import networkx as nx
import numpy as np
import sqlite3
import pandas as pd

def sortu_grafoa():

    # Datuak irakurri
    # BETE HEMEN 8 lerro
    
    # Get data
    connect = sqlite3.connect('./database.sqlite')
    query = """
    SELECT pa.paper_id, pa.author_id, a.name
    FROM paper_authors AS pa JOIN papers AS p ON pa.paper_id = p.id
    JOIN authors as a ON pa.author_id = a.id
    WHERE p.Year BETWEEN '2014' AND '2015'
    """
    df = pd.read_sql(query, connect)

    
    # Sortu grafoa
    # BETE HEMEN 7-10 lerro
    
    # Initialize graph
    G = nx.Graph()

    # Transform
    # Autorearen IDa erabili beharrean erabili izena.
    for p, a in df.groupby('paper_id')['name']: 
        for u, v in itertools.combinations(a, 2):
            if u != v:
                if G.has_edge(u, v):
                    G[u][v]['weight'] +=1
                else:
                    G.add_edge(u, v, weight=1)
    
    return G


def eraikitzailea(G, komunitate_kop):
    kom_lista = len(G) * [-1]
    soluzioa = dict(zip(G.nodes, kom_lista))
    ilara = collections.deque()
    komunitatea = 0
    min_kop = len(G) // komunitate_kop
    hondarra = len(G) % komunitate_kop
    sartzeko_kop = min_kop + int(komunitatea < hondarra)
    sartu_kop = 0
    izenak = list(G.nodes)
    random.shuffle(izenak)
    for izena in izenak:
        ilara.append(izena)
        while ilara:
            unekoa = ilara.popleft()
            if soluzioa[unekoa] == -1:
                soluzioa[unekoa] = komunitatea
                sartu_kop += 1
                if sartu_kop == sartzeko_kop:
                    komunitatea += 1
                    sartzeko_kop = min_kop + int(komunitatea < hondarra)
                    sartu_kop = 0
                for auzokoa in G[unekoa]:
                    ilara.append(auzokoa)
    return soluzioa

def crossover(parent1, parent2):
    s1 = [0]*len(parent1)
    s2 = [0]*len(parent2)
    
    crossover_point = np.random.choice(list(range(len(parent1))))
    s1[0:crossover_point] = parent1[0:crossover_point]
    s2[0:crossover_point] = parent2[0:crossover_point]
    s1[crossover_point:] = parent2[crossover_point:]
    s2[crossover_point:] = parent1[crossover_point:]

    return s1,s2   

# Aurretik SArako dagoen funtzioaren antzekoa, baina honek soluzioa zenbaki lista bezala hartzen du,
# eta aurrekoak izen-zenbaki hiztegi bezala
def lortu_kom_auzokideak(izena, soluzioa, G):
    komunitateak = set()
    for auzokidea in list(G.adj[izena]):
        komunitatea = soluzioa[list(G.nodes).index(auzokidea)]
        if komunitatea != soluzioa[list(G.nodes).index(izena)]:
            komunitateak.add(soluzioa[list(G.nodes).index(auzokidea)])
    return list(komunitateak)


def mutate(G,s,k):
    komunitateak = []
    nodoak = list(G.nodes).copy()
    random.shuffle(nodoak)
    for n in nodoak:
        nodoa = n
        komunitateak = lortu_kom_auzokideak(nodoa, s, G)
        if komunitateak != []:
            break

    if komunitateak != []:
        komunitatea = random.choice(komunitateak)
    # Beste komunitate bateko auzokideren bat daukan erpinik ez dagoenean, ausaz erpin bat hartu 
    # eta bere auzokideekin batera beste komunitate batera mugitzen dira 
    # (komunitate kopurua oso txikia denean batzuetan gertatzen da)
    else:
        nodoa = random.choice(list(G.nodes))
        lista = list(range(k))
        lista.remove(s[list(G.nodes).index(nodoa)])
        komunitatea = random.choice(lista)

    s[list(G.nodes).index(nodoa)] = komunitatea
    for bizilagunak in list(G.adj[nodoa]):
        s[list(G.nodes).index(bizilagunak)] = komunitatea
    return s

def update(P1,P2,f1,f2):
    P = P1 + P2
    f = f1 + f2
    while len(P) > len(P1):
        i = f.index(min(f))
        P.pop(i)
        f.pop(i)
        
    return P,f

def GACD_paralelo(G, k, max_evals, size, pc, max_g):
    
    P = []
    f = []
    # size max_evals baino txiiagoa izan behar da
    for i in range(size):
        s = list(np.random.randint(k, size=len(G)))
        f.append(community.modularity(dict(zip(G.nodes, s)), G))
        P.append(s)
        
    best_P = P[f.index(max(f))]
    best_fitness = max(f)    
    evals = size
    g = 0
    
    while max_evals >= evals + size:
        i = 0
        P2 = []
        while i < size :
            index =  np.random.choice(list(range(len(P))),2)
            s1 = P[index[0]]
            s2 = P[index[1]]
            if random.random() < pc:
                s1, s2 = crossover(s1,s2)
            else:
                s1 = mutate(G,s1,k)
                s2 = mutate(G,s2,k)
            i += 2
            P2.append(s1)
            P2.append(s2)
        parametroak = [(dict(zip(G.nodes, sol)), G) for sol in P2]
        
        with Pool() as pool:
            f2 = pool.starmap(community.modularity, parametroak)
            
        P,f = update(P,P2,f,f2)
        if best_fitness == max(f):
            g+=1
        else:
            best_P = P[f.index(max(f))]
            best_fitness = max(f)
            g = 0
        
        evals += size
        
        if g == max_g:
            break

    return (best_fitness, best_P, max_evals-evals)

def main():
    G = sortu_grafoa()
    
    budget = 10_000
    g = 10

    rep = 10
    pc = 0.7
    population_size = 100
    # Proba paraleloarekin
    ##file1 = open("GA5.txt","w") 
    ##for k in range(2,101):
    k=20
    
    modularitatea = []
    for _ in range(rep):
        m, soluzioa, remaining = GACD_paralelo(G, k, budget, population_size, pc,g)
        modularitatea.append(m)
        print(m)
    ##file1.writelines(modularitatea)
    print(k, (np.sum(modularitatea)/rep))
    ##file1.close()



if __name__ == '__main__':
    main()