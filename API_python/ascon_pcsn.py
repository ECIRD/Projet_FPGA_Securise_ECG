#!/usr/bin/env python3
import matplotlib.pyplot as plt

"""
Implementation of Ascon v1.2, an authenticated cipher and hash function
http://ascon.iaik.tugraz.at/
"""

debug = True
debugpermutation = True
debugtransformation = True
debugFull = False

# === Ascon hash/xof ===

def ascon_hash(message, variant="Ascon-Hash", hashlength=32): 
    """
    Ascon hash function and extendable-output function.
    message: a bytes object of arbitrary length
    variant: "Ascon-Hash", "Ascon-Hasha" (both with 256-bit output for 128-bit security), "Ascon-Xof", or "Ascon-Xofa" (both with arbitrary output length, security=min(128, bitlen/2))
    hashlength: the requested output bytelength (must be 32 for variant "Ascon-Hash"; can be arbitrary for Ascon-Xof, but should be >= 32 for 128-bit security)
    returns a bytes object containing the hash tag
    """
    assert variant in ["Ascon-Hash", "Ascon-Hasha", "Ascon-Xof", "Ascon-Xofa"]
    if variant in ["Ascon-Hash", "Ascon-Hasha"]: assert(hashlength == 32)
    a = 12   # rounds
    b = 8 if variant in ["Ascon-Hasha", "Ascon-Xofa"] else 12
    rate = 8 # bytes

    # Initialization
    tagspec = int_to_bytes(256 if variant in ["Ascon-Hash", "Ascon-Hasha"] else 0, 4)
    S = bytes_to_state(to_bytes([0, rate * 8, a, a-b]) + tagspec + zero_bytes(32))
    #if debug: printstate(S, "initial value:")

    ascon_permutation(S, a)
    #if debug: printstate(S, "initialization:")

    # Message Processing (Absorbing)
    m_padding = to_bytes([0x80]) + zero_bytes(rate - (len(message) % rate) - 1)
    m_padded = message + m_padding

    # first s-1 blocks
    for block in range(0, len(m_padded) - rate, rate):
        S[0] ^= bytes_to_int(m_padded[block:block+8])  # rate=8
        ascon_permutation(S, b)
    # last block
    block = len(m_padded) - rate
    S[0] ^= bytes_to_int(m_padded[block:block+8])  # rate=8
    #if debug: printstate(S, "process message:")

    # Finalization (Squeezing)
    H = b""
    ascon_permutation(S, a)
    while len(H) < hashlength:
        H += int_to_bytes(S[0], 8)  # rate=8
        ascon_permutation(S, b)
    #if debug: printstate(S, "finalization:")
    return H[:hashlength]


# === Ascon AEAD encryption and decryption ===

def ascon_encrypt(key, nonce, associateddata, plaintext, variant="Ascon-128"): 
    """
    Ascon encryption.
    key: a bytes object of size 16 (for Ascon-128, Ascon-128a; 128-bit security) or 20 (for Ascon-80pq; 128-bit security)
    nonce: a bytes object of size 16 (must not repeat for the same key!)
    associateddata: a bytes object of arbitrary length
    plaintext: a bytes object of arbitrary length
    variant: "Ascon-128", "Ascon-128a", or "Ascon-80pq" (specifies key size, rate and number of rounds)
    returns a bytes object of length len(plaintext)+16 containing the ciphertext and tag
    """
    assert variant in ["Ascon-128", "Ascon-128a", "Ascon-80pq"]
    assert(len(nonce) == 16 and (len(key) == 16 or (len(key) == 20 and variant == "Ascon-80pq")))
    S = [0, 0, 0, 0, 0]
    k = len(key) * 8   # bits
    a = 12   # rounds
    b = 8 if variant == "Ascon-128a" else 6   # rounds
    rate = 16 if variant == "Ascon-128a" else 8   # bytes

    ascon_initialize(S, k, rate, a, b, key, nonce)
    ascon_process_associated_data(S, b, rate, associateddata)
    ciphertext = ascon_process_plaintext(S, b, rate, plaintext)
    tag = ascon_finalize(S, rate, a, key)
    return ciphertext + tag


def ascon_decrypt(key, nonce, associateddata, ciphertext, variant="Ascon-128"):
    """
    Ascon decryption.
    key: a bytes object of size 16 (for Ascon-128, Ascon-128a; 128-bit security) or 20 (for Ascon-80pq; 128-bit security)
    nonce: a bytes object of size 16 (must not repeat for the same key!)
    associateddata: a bytes object of arbitrary length
    ciphertext: a bytes object of arbitrary length (also contains tag)
    variant: "Ascon-128", "Ascon-128a", or "Ascon-80pq" (specifies key size, rate and number of rounds)
    returns a bytes object containing the plaintext or None if verification fails
    """
    assert variant in ["Ascon-128", "Ascon-128a", "Ascon-80pq"]
    assert(len(nonce) == 16 and (len(key) == 16 or (len(key) == 20 and variant == "Ascon-80pq")))
    assert(len(ciphertext) >= 16)
    S = [0, 0, 0, 0, 0]
    k = len(key) * 8 # bits
    a = 12 # rounds
    b = 8 if variant == "Ascon-128a" else 6   # rounds
    rate = 16 if variant == "Ascon-128a" else 8   # bytes

    ascon_initialize(S, k, rate, a, b, key, nonce)
    ascon_process_associated_data(S, b, rate, associateddata)
    plaintext = ascon_process_ciphertext(S, b, rate, ciphertext[:-16])
    tag = ascon_finalize(S, rate, a, key)
    if tag == ciphertext[-16:]:
        return plaintext
    else:
        return None


# === Ascon AEAD building blocks ===

def ascon_initialize(S, k, rate, a, b, key, nonce):
    """
    Ascon initialization phase - internal helper function.
    S: Ascon state, a list of 5 64-bit integers
    k: key size in bits
    rate: block size in bytes (8 for Ascon-128, Ascon-80pq; 16 for Ascon-128a)
    a: number of initialization/finalization rounds for permutation
    b: number of intermediate rounds for permutation
    key: a bytes object of size 16 (for Ascon-128, Ascon-128a; 128-bit security) or 20 (for Ascon-80pq; 128-bit security)
    nonce: a bytes object of size 16
    returns nothing, updates S
    """
    
    global debugtransformation
    
    iv_zero_key_nonce = to_bytes([k, rate * 8, a, b] + (20-len(key))*[0]) + key + nonce
    S[0], S[1], S[2], S[3], S[4] = bytes_to_state(iv_zero_key_nonce)
    #if debug: printstate(S, "initial value:")
    #if debug: printstate(S, "Valeur initiale    : ")

    debugtransformation = True
    ascon_permutation(S, a)
    debugtransformation = False
    
    zero_key = bytes_to_state(zero_bytes(40-len(key)) + key)
    S[0] ^= zero_key[0]
    S[1] ^= zero_key[1]
    S[2] ^= zero_key[2]
    S[3] ^= zero_key[3]
    S[4] ^= zero_key[4]
    #if debugpermutation : myprintstate(S, "État ^ (0...0 & K) : ")

    #if debug: printstate(S, "initialization:")
    #if debug: printstate(S, "Initialisation     : ")

def ascon_process_associated_data(S, b, rate, associateddata):
    """
    Ascon associated data processing phase - internal helper function.
    S: Ascon state, a list of 5 64-bit integers
    b: number of intermediate rounds for permutation
    rate: block size in bytes (8 for Ascon-128, 16 for Ascon-128a)
    associateddata: a bytes object of arbitrary length
    returns nothing, updates S
    """
    if len(associateddata) > 0:
        a_zeros = rate - (len(associateddata) % rate) - 1
        a_padding = to_bytes([0x80] + [0 for i in range(a_zeros)])
        a_padded = associateddata + a_padding
        #if debug: print("Donnée associée A paddée  : ", a_padded)
        
        for block in range(0, len(a_padded), rate):
            S[0] ^= bytes_to_int(a_padded[block:block+8])
            #if debugpermutation : myprintstate(S, "État ^ donnée A" + str(block+1) + "   : ")
            if rate == 16:
                S[1] ^= bytes_to_int(a_padded[block+8:block+16])

            ascon_permutation(S, b)

    S[4] ^= 1
    #if debugpermutation : myprintstate(S, "État ^ (0...0 & 1) : ")
    #if debug: printstate(S, "process associated data:")
    #if debug: printstate(S, "Donnée associée A  : ")
    

def ascon_process_plaintext(S, b, rate, plaintext):
    """
    Ascon plaintext processing phase (during encryption) - internal helper function.
    S: Ascon state, a list of 5 64-bit integers
    b: number of intermediate rounds for permutation
    rate: block size in bytes (8 for Ascon-128, Ascon-80pq; 16 for Ascon-128a)
    plaintext: a bytes object of arbitrary length
    returns the ciphertext (without tag), updates S
    """
    p_lastlen = len(plaintext) % rate
    p_padding = to_bytes([0x80] + (rate-p_lastlen-1)*[0x00])
    p_padded = plaintext + p_padding

    # first t-1 blocks
    ciphertext = to_bytes([])
    for block in range(0, len(p_padded) - rate, rate):
        if rate == 8:
            S[0] ^= bytes_to_int(p_padded[block:block+8])
            #if debugpermutation : myprintstate(S, "État ^ Texte P" + str(int(block/rate)+1) + "    : ")
            ciphertext += int_to_bytes(S[0], 8)
            #print("-- Texte chiffré C" + str(int(block/rate)+1) + " = 0x " + bytes_to_hex(int_to_bytes(S[0], 8)))
        elif rate == 16:
            S[0] ^= bytes_to_int(p_padded[block:block+8])
            S[1] ^= bytes_to_int(p_padded[block+8:block+16])
            ciphertext += (int_to_bytes(S[0], 8) + int_to_bytes(S[1], 8))
            
        ascon_permutation(S, b)

    # last block t
    block = len(p_padded) - rate
    if rate == 8:
        #if debugpermutation : myprintstate(S, "État ^ Texte P" + str(int(block/rate)+1) + "    : ")
        S[0] ^= bytes_to_int(p_padded[block:block+8])
        ciphertext += int_to_bytes(S[0], 8)[:p_lastlen]
        #print("-- Texte chiffré C" + str(int(block/rate)+1) + " = 0x " + bytes_to_hex(int_to_bytes(S[0], 8)[:p_lastlen]))
    elif rate == 16:
        S[0] ^= bytes_to_int(p_padded[block:block+8])
        S[1] ^= bytes_to_int(p_padded[block+8:block+16])
        ciphertext += (int_to_bytes(S[0], 8)[:min(8,p_lastlen)] + int_to_bytes(S[1], 8)[:max(0,p_lastlen-8)])
    #if debug: printstate(S, "process plaintext:")
    #if debug: printstate(S, "Texte clair P      : ")
    return ciphertext


def ascon_process_ciphertext(S, b, rate, ciphertext):
    """
    Ascon ciphertext processing phase (during decryption) - internal helper function. 
    S: Ascon state, a list of 5 64-bit integers
    b: number of intermediate rounds for permutation
    rate: block size in bytes (8 for Ascon-128, Ascon-80pq; 16 for Ascon-128a)
    ciphertext: a bytes object of arbitrary length
    returns the plaintext, updates S
    """
    c_lastlen = len(ciphertext) % rate
    c_padded = ciphertext + zero_bytes(rate - c_lastlen)

    # first t-1 blocks
    plaintext = to_bytes([])
    for block in range(0, len(c_padded) - rate, rate):
        if rate == 8:
            Ci = bytes_to_int(c_padded[block:block+8])
            plaintext += int_to_bytes(S[0] ^ Ci, 8)
            S[0] = Ci
        elif rate == 16:
            Ci = (bytes_to_int(c_padded[block:block+8]), bytes_to_int(c_padded[block+8:block+16]))
            plaintext += (int_to_bytes(S[0] ^ Ci[0], 8) + int_to_bytes(S[1] ^ Ci[1], 8))
            S[0] = Ci[0]
            S[1] = Ci[1]

        ascon_permutation(S, b)

    # last block t
    block = len(c_padded) - rate
    if rate == 8:
        c_padding1 = (0x80 << (rate-c_lastlen-1)*8)
        c_mask = (0xFFFFFFFFFFFFFFFF >> (c_lastlen*8))
        Ci = bytes_to_int(c_padded[block:block+8])
        plaintext += int_to_bytes(Ci ^ S[0], 8)[:c_lastlen]
        S[0] = Ci ^ (S[0] & c_mask) ^ c_padding1
    elif rate == 16:
        c_lastlen_word = c_lastlen % 8
        c_padding1 = (0x80 << (8-c_lastlen_word-1)*8)
        c_mask = (0xFFFFFFFFFFFFFFFF >> (c_lastlen_word*8))
        Ci = (bytes_to_int(c_padded[block:block+8]), bytes_to_int(c_padded[block+8:block+16]))
        plaintext += (int_to_bytes(S[0] ^ Ci[0], 8) + int_to_bytes(S[1] ^ Ci[1], 8))[:c_lastlen]
        if c_lastlen < 8:
            S[0] = Ci[0] ^ (S[0] & c_mask) ^ c_padding1
        else:
            S[0] = Ci[0]
            S[1] = Ci[1] ^ (S[1] & c_mask) ^ c_padding1
    #if debug: printstate(S, "process ciphertext:")
    return plaintext


def ascon_finalize(S, rate, a, key):
    """
    Ascon finalization phase - internal helper function.
    S: Ascon state, a list of 5 64-bit integers
    rate: block size in bytes (8 for Ascon-128, Ascon-80pq; 16 for Ascon-128a)
    a: number of initialization/finalization rounds for permutation
    key: a bytes object of size 16 (for Ascon-128, Ascon-128a; 128-bit security) or 20 (for Ascon-80pq; 128-bit security)
    returns the tag, updates S
    """
    assert(len(key) in [16,20])
    S[rate//8+0] ^= bytes_to_int(key[0:8])
    S[rate//8+1] ^= bytes_to_int(key[8:16])
    S[rate//8+2] ^= bytes_to_int(key[16:])

    #if debugpermutation : myprintstate(S, "État ^ (K & 0...0) : ")

    ascon_permutation(S, a)

    S[3] ^= bytes_to_int(key[-16:-8])
    S[4] ^= bytes_to_int(key[-8:])
    tag = int_to_bytes(S[3], 8) + int_to_bytes(S[4], 8)
    #if debug: printstate(S, "finalization:")
    #if debug: printstate(S, "Finalisation       : ")
    return tag


# === Ascon permutation ===

def ascon_permutation(S, rounds=1):
    """
    Ascon core permutation for the sponge construction - internal helper function.
    S: Ascon state, a list of 5 64-bit integers
    rounds: number of rounds to perform
    returns nothing, updates S
    """
    assert(rounds <= 12)
    #if debugtransformation: myprintstate(S, "permutation input:")
    for r in range(12-rounds, 12):
        # --- add round constants ---
        S[2] ^= (0xf0 - r*0x10 + r*0x1)
        #if (debugtransformation or debugFull): 
            #print("-- Permutation (r=" + "{:02d}".format(r) + ")")
            #myprintstate(S, "Addition constante : ")
        # --- substitution layer ---
        S[0] ^= S[4]
        S[4] ^= S[3]
        S[2] ^= S[1]
        T = [(S[i] ^ 0xFFFFFFFFFFFFFFFF) & S[(i+1)%5] for i in range(5)]
        for i in range(5):
            S[i] ^= T[(i+1)%5]
        S[1] ^= S[0]
        S[0] ^= S[4]
        S[3] ^= S[2]
        S[2] ^= 0XFFFFFFFFFFFFFFFF
        #if (debugtransformation or debugFull): myprintstate(S, "Substitution S-box : ")
        # --- linear diffusion layer ---
        S[0] ^= rotr(S[0], 19) ^ rotr(S[0], 28)
        S[1] ^= rotr(S[1], 61) ^ rotr(S[1], 39)
        S[2] ^= rotr(S[2],  1) ^ rotr(S[2],  6)
        S[3] ^= rotr(S[3], 10) ^ rotr(S[3], 17)
        S[4] ^= rotr(S[4],  7) ^ rotr(S[4], 41)
        #if (debugtransformation or debugFull): myprintstate(S, "Diffusion linéaire : ")
        #if (debugpermutation and not((debugtransformation or debugFull))): myprintstate(S, "Permutation (r=" + "{:02d}".format(r) + ") : ")
    

# === helper functions ===

def get_random_bytes(num):
    import os
    return to_bytes(os.urandom(num))

def zero_bytes(n):
    return n * b"\x00"

def to_bytes(l): # where l is a list or bytearray or bytes
    return bytes(bytearray(l))

def bytes_to_int(bytes):
    return sum([bi << ((len(bytes) - 1 - i)*8) for i, bi in enumerate(to_bytes(bytes))])

def bytes_to_state(bytes):
    return [bytes_to_int(bytes[8*w:8*(w+1)]) for w in range(5)]

def int_to_bytes(integer, nbytes):
    return to_bytes([(integer >> ((nbytes - 1 - i) * 8)) % 256 for i in range(nbytes)])

def rotr(val, r):
    return (val >> r) | ((val & (1<<r)-1) << (64-r))

def bytes_to_hex(b):
    #return b.hex()
    #return " ".join(hex(x) for x in b)
    #return " ".join(format(x, 'x') for x in b)
    return " ".join('{:02X}'.format(x) for x in b)
'''  
def printstate(S, description=""):
    #print("*"*(16*5+5+20))
    #print(" " + description)
    #print(description + " ".join(["{s:016x}".format(s=s) for s in S]))
    #print("*"*(16*5+5+20))

def myprintstate(S, description=""):
    #print(description + " ".join(["{s:016x}".format(s=s) for s in S]))
    
def printwords(S, description=""):
    #print(" " + description)
    #print("\n".join(["  x{i}={s:016x}".format(**locals()) for i, s in enumerate(S)]))

'''
# === some demo if called directly ===

def demo_print(data):
    maxlen = max([len(text) for (text, val) in data])
    #for text, val in data:
        #print("{text}:{align} 0x{val} ({length} octets)".format(text=text, align=((maxlen - len(text)) * " "), val=bytes_to_hex(val), length=len(val)))

def demo_aead(variant):
    assert variant in ["Ascon-128", "Ascon-128a", "Ascon-80pq"]
    keysize = 20 if variant == "Ascon-80pq" else 16
    # print("=== demo encryption using {variant} ===".format(variant=variant))

    # choose a cryptographically strong random key and a nonce that never repeats for the same key:
    # key   = get_random_bytes(keysize) # zero_bytes(keysize)
    # nonce = get_random_bytes(16)      # zero_bytes(16)
    
    # New random key
    key_hexa="8A55114D1CB6A9A2BE263D4D7AECAAFF"
    # New random nonce
    nonce_hexa="4ED0EC0B98C529B7C8CDDF37BCD0284A"
    # New message une courbe de 121 octet normalisée et points entre 0 et 255
    plaintext_hexa="5A5B5B5A5A5A5A5A59554E4A4C4F545553515354565758575A5A595756595B5A5554545252504F4F4C4C4D4D4A49444447474644424341403B36383E4449494747464644434243454745444546474A494745484F58697C92AECEEDFFFFE3B47C471600041729363C3F3E40414141403F3F403F3E3B3A3B3E3D3E3C393C41464646454447464A4C4F4C505555524F5155595C5A595A5C5C5B5959575351504F4F53575A5C5A5B5D5E6060615F605F5E5A5857545252"
    
    key = bytes.fromhex(key_hexa)
    nonce = bytes.fromhex(nonce_hexa)
    plaintext= bytes.fromhex(plaintext_hexa)
    
    # associateddata = b"ASCON"
    # associateddata = bytes.fromhex(key_hexa)
    associateddata = b"A to B"

    #plaintext      = b"RDV au Ti'bar ce soir ?"

    ciphertext        = ascon_encrypt(key, nonce, associateddata, plaintext,  variant)
    print("chien")
    print(ciphertext)
    decrypt = ascon_decrypt(key,nonce, associateddata, ciphertext, variant)
    print("oui")
    print(decrypt)
    print(' '.join(f"{byte:02x}" for byte in decrypt))#, f"message: {bytes.fromhex(str(ciphertext))}")
    hex_string = ' '.join(f"{byte:02x}" for byte in decrypt)
    hex_values = hex_string.split()  # Divise la chaîne en une liste de valeurs hexadécimales

    # Afficher chaque "point" (octet) avec sa valeur hexadécimale et décimale
    '''for i, value in enumerate(hex_values):
        decimal_value = int(value, 16)  # Conversion de l'hexadécimal en décimal
        print(f"Point {i + 1}: Hex = {value}, Decimal = {decimal_value}")
        hex_values = hex_string.split()  # Divise la chaîne en une liste de valeurs hexadécimales

    # Convertir chaque valeur hexadécimale en décimal
    decimal_values = [int(value, 16) for value in hex_values]

    # Créer un graphique avec les valeurs décimales
    plt.figure(figsize=(10, 5))  # Optionnel : pour un graphique plus large
    plt.plot(decimal_values, marker='o', linestyle='-', color='b')  # Afficher les points

    # Ajouter des titres et des étiquettes
    plt.title("Graphique des Points (Valeurs Hexadécimales Converties)")
    plt.xlabel("Index des Points")
    plt.ylabel("Valeur du Point (en Décimal)")
    plt.grid(True)

    # Afficher le graphique
    plt.show()'''
    #file.close()
    debug = True #False
    debugpermutation = True #False
    debugtransformation = True #False
    
    #receivedplaintext = ascon_decrypt(key, nonce, associateddata, ciphertext, variant)
    
    
    #if receivedplaintext == None: print("verification failed!")
        
    demo_print([("key", key), 
                ("nonce", nonce), 
                ("plaintext", plaintext), 
                ("ass.data", associateddata), 
                ("ciphertext", ciphertext[:-16]), 
                ("tag", ciphertext[-16:]), 
                #("received", receivedplaintext), 
               ])

def demo_hash(variant="Ascon-Hash", hashlength=32):
    assert variant in ["Ascon-Xof", "Ascon-Hash", "Ascon-Xofa", "Ascon-Hasha"]
    print("=== demo hash using {variant} ===".format(variant=variant))

    message = b"ascon"
    tag = ascon_hash(message, variant, hashlength)

    demo_print([("message", message), ("tag", tag)])


if __name__ == "__main__":
    demo_aead("Ascon-128")
    demo_hash("Ascon-Hash")
