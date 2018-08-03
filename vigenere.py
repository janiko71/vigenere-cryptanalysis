import pprint
import string
import operator

from collections import Counter
import re

"""
  --------------------------------
    Useful CONSTANTS
  --------------------------------
"""
FREQUENCY = {
    'fra': [9.42,1.02,2.64,3.39,15.87,0.95,1.04,0.77,8.41,0.89,0.0,5.34,3.24,7.15,5.14,2.86,1.06,6.46,7.90,7.26,6.24,2.15,0.0,0.30,0.24,0.32],
    'eng': [8.08,1.67,3.18,3.99,12.56,2.17,1.80,5.27,7.24,0.14,0.63,4.04,2.60,7.38,7.47,1.91,0.09,6.42,6.59,9.15,2.79,1.00,1.89,0.21,1.65,0.07]
}

USUAL_IC = {
    'fra' : 0.0778,
    'eng' : 0.0667
}


"""
  --------------------------------
    Useful functions
  --------------------------------
"""

def caesar(chain, key):
    """
        Caesar deciphering
    """

    # You can specify a letter or an int
    if (not isinstance(key, int)):
        key = 65 - ord(key) # A verifier

    alph=string.ascii_uppercase
    res = chain.translate(str.maketrans(alph,alph[key:]+alph[:key]))
    
    return res


def vigenere(chain, key):
    """
        Vigenere deciphering
    """
    # Key is a word (letters)
    result = [""] * 21
    lg = len(key)
    for i in range(lg):
        tested_chain = chain[i::lg]
        result[i] = caesar(tested_chain, key[i])
    # Re-assembling sub-chains
    seq = ""
    try:
        for i in range(0, len(result[0])):
            for j in range(0, lg):
                seq = seq + result[j][i]
    except:
        print('Fin')
   
    return seq


def IC_calculation(chain):
    """
        Index of Coincidence calculation, in order to estimate (later) Vigenere key length
    """
    app = list_to_array(letters_apparition(chain))
    s = sum (n*(n-1) for n in app)
    total = sum(app)
    res = (s/(total*(total-1)))

    return res


def caesar_key_guess(chain):
    """
        Caesar key searching, based on letters frequencies analysis
        To find the best match, we can use either :
        - correlation (the highest is the better)
        - difference (the lowest is the better)
    """
    correlation_list = {}
    diff_list = {}

    for dec in range(26):

        tested_chain = caesar(chain, -dec)
        freq_tbl = list_to_array(freq_analyse(tested_chain))

        # Correlation is (letter frequency * usual frequency), summed for every letter
        correl = sum(a * b for a, b in zip(freq_tbl,FREQUENCY[LANG]))
        correlation_list[dec] = correl

        # Difference is the distance between letter frequency and usual frequency, for each letter.
        lg = float(len(tested_chain))
        diff = sum(abs(b - FREQUENCY[LANG][a]) for a, b in enumerate([100 * lettre / lg for lettre in map(tested_chain.count, string.ascii_uppercase)]))

        diff_list[dec] = diff
 
    sorted_list = sorted(correlation_list.items(), key=operator.itemgetter(1), reverse=True)

    # Small trick : we have to "reverse" the offset to construct the right key
    #offset = (26 - sorted_list[0][0]) % 26
    offset = sorted_list[0][0]

    return offset


def vigenere_key_guess(chain):
    """
        Estimation of Vigenere's key length
    
        We try lengthes between 2 and 20. For each length, we calculate IC for every sub-chains, and then the mean.
        If the mean IC for one length is greater than the usual IC for target language, this length is a probable one.
        Source : https://fr.wikipedia.org/wiki/Indice_de_coïncidence
                 https://en.wikipedia.org/wiki/Index_of_coincidence 
    """
    IC = [0] * 21
    lg = 0
    for l in range(1, 21):
        ic_tmp = 0.0
        for c in range(0, l):
            t = IC_calculation(chain[c::l])
            ic_tmp += t
        IC[l] = ic_tmp / l
        if (IC[l] > USUAL_IC['fra']):
            lg = l
            break

    return lg


def freq_analyse(chain, tri = False):
    """
        Analyse frequentielle d'une chaîne
    """
    liste_freq = Counter(chain)
    del liste_freq['\r']
    del liste_freq['\n']
    del liste_freq[' ']    

    # On cherche le nombre total de caractères 
    tc = sum(liste_freq.values())
    # On remplace le nombre d'occurrences par leur fréquence
    for letter in liste_freq:
        freq = float(liste_freq[letter] / tc * 100)
        liste_freq[letter] = freq
    # On retrie
    if (tri):
        sorted_liste = sorted(liste_freq.items(), key=operator.itemgetter(1), reverse=True)
    else:
        sorted_liste = sorted(liste_freq.items(), key=operator.itemgetter(0))

    return sorted_liste


def letters_apparition(chain):
    """
        Comptage simple des occurrences des lettres d'une chaîne
    """
    l = Counter(chain)
    del l['\r']
    del l['\n']
    del l[' ']
    
    return sorted(l.items())


def search_vigenere_key(chain,lg) :
    """
        Searching for Vigenere's most probable key, for a given length
    """
    key = "".join(chr(65+caesar_key_guess(chain[i::lg])) for i in range(lg))
        
    return key


def list_to_array(liste):
    """
        Transform from a list (issued from Counter class) to an easier format
    """
    ret = [0] * 26
    for k,v in liste:
        ret[ord(k)-65] = v

    return ret


def substitution(chain, translate):
    """
        Monoalphabetic substitution

        :param chain: text to translate
        :param translate: dict containing all known substitution (can be partial)
        :type arg1: string
        :type arg1: dict
        :return: translated text
        :rtype: string

        :Example:

        >>> substitution("abcd", {"b": "0", "d": "1"})
        a0c1
    """
    keys   = "".join(key   for key, value in translate.items())
    values = "".join(value for key, value in translate.items())

    return chain.translate(str.maketrans(keys,values))


def clean(chain):
    """
        Text cleaning (no CR, no space, only uppercases). Convention : ciphered text should be in uppercase.

        :param chain: text to translate
        :param translate: dict containing all known substitution (can be partial)
        :return: cleaned text
        :rtype: string

        :Example:

        >>> clean("abcd\refgh.ijkl mn")
        ABCDEFGHIJKLMN
    """
    chain = chain.replace('\r','')
    chain = chain.replace('\n','')
    chain = chain.replace(' ','')
    chain = chain.replace(".",'')
    chain = chain.replace(',','')
    chain = chain.upper()

    return chain

        
"""
  ------------------------------------------------------
    AUTOMATIC VIGENERE TEXT DECIPHERING (Main part)
    
    Input     : ciphered text (file)
    Output    : deciphered text (display)
  ------------------------------------------------------
"""

LANG = 'fra'

# Text reading and cleaning
# Text must be uppercased, no space
text = ""
with open("vig.txt", 'r', encoding='utf-8') as f:
    text = text + f.read()

text = clean(text)
print()

# First we need to estimate the key length
lg = vigenere_key_guess(text)
print('Probable key length : {}'.format(lg))

# Then we try to guess the key
key = search_vigenere_key(text, lg)
print('Probable key        : {}'.format(key))

# And the we decipher the text
print()
original = vigenere(text, key)
print(original)


