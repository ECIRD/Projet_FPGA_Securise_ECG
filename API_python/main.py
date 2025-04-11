import numpy as np
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtCore
from Fpga import lire_colonne_csv
from ascon_pcsn import ascon_decrypt
from collections import deque
import pyqtgraph as pg
from scipy.signal import find_peaks
from Fpga import FPGA
from log import *
import time

#Detection de pique PQRST
def detect_pqrst(signal):
    signal = np.array(signal)

    # Détection du pic R (le plus facile : c'est le max global)
    r_peaks, _ = find_peaks(signal, distance=20, height=np.max(signal)*0.9)

    p_peaks = []
    q_peaks = []
    s_peaks = []
    t_peaks = []

    for r in r_peaks:
        # Zone avant R pour chercher Q et P
        q_range = signal[max(0, r-20):r]
        q_index = np.argmin(q_range) + max(0, r-20)
        q_peaks.append(q_index)

        p_range = signal[max(0, q_index-30):q_index]
        if len(p_range) > 0:
            p_index = np.argmax(p_range) + max(0, q_index-30)
            p_peaks.append(p_index)

        # Zone après R pour chercher S et T
        s_range = signal[r:min(len(signal), r+20)]
        s_index = np.argmin(s_range) + r
        s_peaks.append(s_index)

        t_range = signal[s_index:min(len(signal), s_index+40)]
        if len(t_range) > 0:
            t_index = np.argmax(t_range) + s_index
            t_peaks.append(t_index)

    return p_peaks, q_peaks, r_peaks.tolist(), s_peaks, t_peaks

# Fonction pour récupérer l'ECG d'ascon cryptage et decryptage
def ecg_take():
    global counter
    ligne = wave[counter]
    if(len(ligne)>362):
        print("ERREUR CHAINE TROP LONGUE")
        print('Taille', len(ligne))
        print('Ligne', ligne)
        while(1):
            time.sleep(100.0)
            
    if(len(ligne)<368):
        ligne+="8"
        while(len(ligne)<368):
            ligne+="0"
            
    fpga.waveform(ligne)
    fpga.go()
    fpga.tag()
    fpga.cipher()
    ciphertext = fpga.cipher_bytes[:-6] + fpga.tag_bytes[:-3] #le ciphertext utile après le cryptage
    print(ciphertext)
    if (ciphertext == None):
        user.debug("Ciphertext vide : problème dans le cryptage")
    if (len(ciphertext) > 197):
        user.warning("Problème de taille")
        ciphertext = ciphertext[:197]
    decrypt = ascon_decrypt(bytes.fromhex(key_hexa), bytes.fromhex(nonce_hexa), bytes.fromhex(associateddata[:-4]), ciphertext, "Ascon-128") #Le ciphertext décrypté
    print(decrypt)
    # Convertir les valeurs décryptées en hexadécimal en valeurs décimales
    hex_string = ' '.join(f"{byte:02x}" for byte in decrypt) #On sépare en octet donc en faisant des groupes de deux caractères en hexadécimal
    hex_values = hex_string.split()
    decimal_values = [int(value, 16) for value in hex_values]
    ecg_data.extend(decimal_values)
    counter += 1
    return decimal_values

def ecg_before_ascon():
    ligne = wave[counter]
    hex_val = [ligne[i:i+2] for i in range(0, len(ligne), 2)]

    # Convertir chaque groupe hexadécimal en valeur décimale

    # Convertir chaque valeur hexadécimale en décimal
    val_deci = [int(value, 16) for value in hex_val]
    val = val_deci
    return val

# Fonction de mise à jour des données
def update():
    global data
    global data_b
    # Décaler les anciennes courbes vers la gauche
    data = np.roll(data, shift=-1, axis=0)
    data_b = np.roll(data_b, shift=-1, axis=0)
    # Générer de nouvelles données ECG pour la dernière courbe

    new_data_b = ecg_before_ascon()

    new_data = ecg_take()

    ecg_stock.append(new_data)

    # Mettre à jour la dernière courbe avec les nouvelles données
    data[4] = new_data

    data_b[4] = new_data_b
    # Concaténer toutes les courbes en une seule série continue
    all_data = np.concatenate(data)

    all_data_b = np.concatenate(data_b)

    # Mettre à jour la courbe principale
    curve.setData(np.arange(len(all_data)), all_data)

    bottom_curve.setData(np.arange(len(all_data_b)), all_data_b)

    # Détection PQRST
    p_peaks, q_peaks, r_peaks, s_peaks, t_peaks = detect_pqrst(all_data)

    # Mise à jour des courbes de pics
    p_curve.setData(p_peaks, all_data[p_peaks])
    q_curve.setData(q_peaks, all_data[q_peaks])
    r_curve.setData(r_peaks, all_data[r_peaks])
    s_curve.setData(s_peaks, all_data[s_peaks])
    t_curve.setData(t_peaks, all_data[t_peaks])

    user.info("Actualisation réussie")


def init_graph():
    global p_curve,q_curve,r_curve,s_curve,t_curve, data, curve, bottom_curve, data_b
    ### Génération du graphe qui s'actualise tous les X secondes
    # Initialisation de l'application Qt
    app = QApplication(sys.argv)

    # Création de la fenêtre principale
    win = QMainWindow()
    win.setWindowTitle("Affichage en Temps Réel")
    win.resize(1000, 600)

    # Création d'un widget pour afficher les graphiques
    plot_widget = pg.GraphicsLayoutWidget()
    win.setCentralWidget(plot_widget)

    # Créer un graphique
    plot = plot_widget.addPlot(title="ECG en temps réel", labels={'left': 'Amplitude', 'bottom': 'Index'})
    plot.setYRange(-100, 300)

    # Créer une courbe unique pour afficher toutes les données reliées
    curve = plot.plot(pen=pg.mkPen(color='r'))

    # Créer un deuxième graphique (subplot principal en bas)
    bottom_plot = plot_widget.addPlot(title="ECG en temps réel, avant cryptage et decryptage", labels={'left': 'Amplitude', 'bottom': 'Index'})
    bottom_plot.setYRange(-100, 300)

    # Créer une courbe pour le graphique du bas
    bottom_curve = bottom_plot.plot(pen=pg.mkPen(color='r'))

    # Courbes pour les pics P, Q, R, S, T (avec des symboles distincts)
    p_curve = plot.plot(pen=None, symbol='o', symbolBrush='b', symbolSize=8)  # bleu
    q_curve = plot.plot(pen=None, symbol='t', symbolBrush='c', symbolSize=8)  # cyan
    r_curve = plot.plot(pen=None, symbol='s', symbolBrush='g', symbolSize=10) # vert
    s_curve = plot.plot(pen=None, symbol='d', symbolBrush='m', symbolSize=8)  # magenta
    t_curve = plot.plot(pen=None, symbol='x', symbolBrush='y', symbolSize=8)  # jaune

    # Créer un tableau pour stocker les données des courbes
    data = np.zeros((5, 181))  # 5 courbes, chaque courbe contient 181 points
    data_b = np.zeros((5, 181))
    # Ajuster la largeur de l'axe X pour afficher toutes les courbes combinées
    plot.setXRange(0, 181 * 5)

    # Timer pour mettre à jour toutes les 100 ms
    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(3000)

    # Afficher la fenêtre
    win.show()

    # Lancer l'application Qt
    sys.exit(app.exec_())

def init_ascon():
    # Paramètres
    global ecg_data, counter, nom_colonne, fpga, curve, key_hexa, nonce_hexa, associateddata, wave, ecg_stock
    key_hexa = "8A55114D1CB6A9A2BE263D4D7AECAAFF"
    ecg_data = deque(maxlen=181)
    ecg_stock = []
    nonce_hexa = "4ED0EC0B98C529B7C8CDDF37BCD0284A"
    counter = 0
    associateddata = "4120746F2042"
    port = None
    fpga = FPGA(port)
    chemin_fichier = "waveform_example_ecg.csv"  # Remplace par le chemin réel du fichier
    nom_colonne = ""  # Remplace par le nom réel de la colonne
    wave = lire_colonne_csv(chemin_fichier)
    # Envoie du nonce, key et donnée associées à la base.
    fpga.nonce(nonce_hexa)
    fpga.key(key_hexa)
    if(len(associateddata)>16):
        print("ERREUR CHAINE TROP LONGUE")
        print('Taille', len(associateddata))
        print('Ligne', associateddata)
        while(1):
            time.sleep(100.0)
    if(len(associateddata)<16):
        associateddata+="8"
        while(len(associateddata)<16):
            associateddata+="0"
    fpga.associated_data(associateddata)


def main():
    if (user.authenticate("admin", "password123") == False):
        print("Authentification fail")
        return 0
    init_ascon()
    init_graph()
    return 0

main()