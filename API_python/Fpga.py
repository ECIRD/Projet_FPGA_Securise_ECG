import serial
import serial.tools.list_ports
import time
from ascon_pcsn import ascon_decrypt
import csv
import matplotlib.pyplot as plt


#Classe afin de se conneter au FPGA et d'intéragir avec
class FPGA:
    def __init__(self, port=None, baudrate=115200, timeout=1):
        """
        Initialise la connexion UART avec le FPGA.
        Si aucun port n'est spécifié, tente de détecter automatiquement le premier disponible.
        """
        if(port == None):
            port = self.find_available_port()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.tag_bytes = 0
        self.cipher_bytes = 0
        self.ser = self.configure_uart()

    @staticmethod
    def find_available_port():
        """Détecte automatiquement le premier port série disponible."""
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            raise RuntimeError("Aucun port série disponible.")
        return ports[0].device  # Ex: 'COM3' ou '/dev/ttyUSB0'

    def configure_uart(self):
        """Configure et retourne un objet série pour la communication UART."""
        return serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=self.timeout
        )

    #Fonction de base pour envoyer un message via UART au FPGA
    def send_message(self, message):
        """Envoie un message au FPGA via UART."""
        self.ser.write(message.encode())
        print(f"Sent: {message} (message: {message.encode('utf-8')})")

    #Fonction de base pour recevoir un message via UART au FPGA
    def receive_message(self):
        """Reçoit un message du FPGA via UART."""
        # Lire la réponse jusqu'à 'OK' et essayer de décoder en UTF-8
        #self.ser.timeout = 1
        response = self.ser.readall()#.decode('utf-8', errors='ignore').strip()

        if response:
            print(f"OK")

        return response
    
    #Fonction de base pour recevoir un message via UART au FPGA
    def receive_message_hexa(self, n):
        """Reçoit un message en hexadécimal du FPGA via UART."""
        #self.ser.timeout = 2
        data = self.ser.readall()
        if data:
            hex_data = data.hex().upper()
            print(f"Données reçues en hexadécimal : {hex_data}")
        return data

    def write_add(self, add):
        """Écrit une adresse sur le FPGA."""
        message = "A" + str(add)
        self.ser.write(message.encode())
        self.receive_message()

    #Fonction pour envoyer la clé
    def key(self, key):
        """Send a message over UART with 4C prepended in hexadecimal format."""
        # Convert the key to its hexadecimal representation
        #hex_message = key.encode('utf-8').hex()
        
        # Prepend '4C' (hexadecimal representation of 'L') to the message
        hex_message_with_prefix = '4B' + key
        
        # Send the message over UART
        ser = self
        self.ser.write(bytes.fromhex(hex_message_with_prefix))
        
        # Print the message for confirmation
        print(f"Sent: {hex_message_with_prefix}", f"message: {bytes.fromhex(hex_message_with_prefix)}")
        
        # Receive the message after sending
        self.receive_message()

    #Fonction pour envoyer le nounce
    def nonce(self, nonce):
        """Send a message over UART with 4C prepended in hexadecimal format."""
        # Convert the key to its hexadecimal representation
        #hex_message = nonce.encode('utf-8').hex()
        
        # Prepend '4C' (hexadecimal representation of 'L') to the message
        hex_message_with_prefix = '4E' + nonce
        
        # Send the message over UART
        ser = self
        self.ser.write(bytes.fromhex(hex_message_with_prefix))
        
        # Print the message for confirmation
        print(f"Sent: {hex_message_with_prefix}", f"message: {bytes.fromhex(hex_message_with_prefix)}")
        
        # Receive the message after sending
        self.receive_message()

    #Fonction pour envoyer la donnée associée
    def associated_data(self, ad):
        """Send a message over UART with 4C prepended in hexadecimal format."""
        # Convert the key to its hexadecimal representation
        #hex_message = ad.encode('utf-8').hex()
        
        # Prepend '4C' (hexadecimal representation of 'L') to the message
        hex_message_with_prefix = '41' + ad
        
        # Send the message over UART
        ser = self
        self.ser.write(bytes.fromhex(hex_message_with_prefix))
        
        # Print the message for confirmation
        print(f"Sent: {hex_message_with_prefix}", f"message: {bytes.fromhex(hex_message_with_prefix)}")
        
        # Receive the message after sending
        self.receive_message()

    #Fonction pour envoyer la trace ECG
    def waveform(self, wave):
        """Send a message over UART with 4C prepended in hexadecimal format."""
        # Convert the key to its hexadecimal representation
        #hex_message = wave.encode('utf-8').hex()
        
        # Prepend '4C' (hexadecimal representation of 'L') to the message
        hex_message_with_prefix = '57' + wave
        
        # Send the message over UART
        ser = self
        self.ser.write(bytes.fromhex(hex_message_with_prefix))
        
        # Print the message for confirmation
        print(f"Sent: {hex_message_with_prefix}")
        
        # Receive the message after sending
        self.receive_message()

    #Lancer le cryptage ascon
    def go(self):
        """Send a message over UART with 4C prepended in hexadecimal format."""
        
        # Prepend '4C' (hexadecimal representation of 'L') to the message
        hex_message_with_prefix = '47'
        
        # Send the message over UART
        ser = self
        self.ser.write(bytes.fromhex(hex_message_with_prefix))
        
        # Print the message for confirmation
        print(f"Sent: {hex_message_with_prefix}", f"message: {bytes.fromhex(hex_message_with_prefix)}")
        
        # Receive the message after sending
        self.receive_message()

    def write_data(self, data):
        """Écrit des données sur le FPGA."""
        message = "W" + str(data)
        self.ser.write(message.encode())
        self.receive_message()
    '''
    def go(self):
        """Envoie la commande de démarrage au FPGA."""
        message = str("G")
        self.ser.write(message.encode())
        self.receive_message()
    '''

    def read_data(self):
        """Lit les données du FPGA."""
        message = "R"
        self.ser.write(message.encode())
        self.receive_message_hexa()
        self.receive_message()

    #Fonction pour recevoir le tag
    def tag(self):
        """Send a message over UART with 4C prepended in hexadecimal format."""
        
        # Prepend '4C' (hexadecimal representation of 'L') to the message
        hex_message_with_prefix = "54"
        
        # Send the message over UART
        ser = self
        self.ser.write(bytes.fromhex(hex_message_with_prefix))
        
        # Print the message for confirmation
        print(f"Sent: {hex_message_with_prefix}", f"message: {bytes.fromhex(hex_message_with_prefix)}")
        
        # Receive the message after sending
        self.tag_bytes = self.receive_message_hexa(160)
        #self.receive_message()

    #Fonction pour recevoir le cipher
    def cipher(self):
        """Send a message over UART with 4C prepended in hexadecimal format."""
        
        # Prepend '4C' (hexadecimal representation of 'L') to the message
        hex_message_with_prefix = "43"
        
        # Send the message over UART
        ser = self
        self.ser.write(bytes.fromhex(hex_message_with_prefix))
        
        # Print the message for confirmation
        print(f"Sent: {hex_message_with_prefix}", f"message: {bytes.fromhex(hex_message_with_prefix)}")
        
        # Receive the message after sending
        self.cipher_bytes = self.receive_message_hexa(184)
        #self.receive_message()

    def close(self):
        """Ferme la connexion UART proprement."""
        self.ser.close()
        print("Connexion UART fermée.")

#Fonction pour lire le fichier csv avec la trace
def lire_colonne_csv(chemin_fichier):
    valeurs = []
    with open(chemin_fichier, mode='r', encoding='utf-8') as fichier:
        lecteur_csv = csv.reader(fichier)
        for ligne in lecteur_csv:
            if ligne:
                valeurs.append(str(ligne[0]))  # Lire la première colonne
    return valeurs
