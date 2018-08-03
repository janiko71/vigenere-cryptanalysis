"""
  ------------------------------------------------------
  
    AUTOMATIC VIGENERE TEXT DECIPHERING IN PYTHON
    
  ------------------------------------------------------
"""

import pprint
import string
import operator

"""
  --------------------------------
    Useful CONSTANTS
  --------------------------------
"""
# Usual frequencies for some languages
USUAL_FREQUENCIES = {
    'fra': [9.42,1.02,2.64,3.39,15.87,0.95,1.04,0.77,8.41,0.89,0.0,5.34,3.24,7.15,5.14,2.86,1.06,6.46,7.90,7.26,6.24,2.15,0.0,0.30,0.24,0.32],
    'eng': [8.08,1.67,3.18,3.99,12.56,2.17,1.80,5.27,7.24,0.14,0.63,4.04,2.60,7.38,7.47,1.91,0.09,6.42,6.59,9.15,2.79,1.00,1.89,0.21,1.65,0.07]
}

# Usual index of correlation for some languages
USUAL_IC = {
    'fra' : 0.0778,
    'eng' : 0.0667
}

# Default file name (why not?)
DEFAULT_FILE_NAME = "vig.txt"


"""
  ------------------------------------
    Useful cryptographic functions
  ------------------------------------
"""

def caesar(chain, key):
    """
        Caesar deciphering

        :param chain: ciphered text
        :param key: letter of offset
        :type chain: string
        :type key: int or char
        :return: deciohered text
        :rtype: string
    """

    # You can specify a letter or an int
    if (not isinstance(key, int)):
        key = 65 - ord(key) # we are deciohering, so the key (offset) should be negative

    alph=string.ascii_uppercase
    res = chain.translate(str.maketrans(alph,alph[key:]+alph[:key]))
    
    return res


def vigenere(chain, key):
    """
        Vigenere deciphering, by deciohering subchains with Caesar's method

        :param chain: ciphered text
        :param key: letter of offset
        :type chain: string
        :type key: string
        :return: deciohered text
        :rtype: string

        ..to do:: code optimizing 
    """
    # Key is a word (letters)
    result = [""] * 21
    lg = len(key)
    for i in range(lg):
        tested_chain = chain[i::lg]
        result[i] = caesar(tested_chain, key[i])
        
    # Re-assembling subchains
    seq = ""
    try:
        for i in range(0, len(result[0])):
            for j in range(0, lg):
                seq = seq + result[j][i]
    except:
        print('Fin')
   
    return seq


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


"""
  ------------------------------------
    Useful cryptanalysis functions
  ------------------------------------
"""
def IC_calculation(chain):
    """
        Index of Coincidence calculation, in order to estimate (later) Vigenere key length

        :param chain: ciphered text
        :type chain: string
        :return: index of coincidence for the text
        :rtype: float
    """
    app = letters_apparitions(chain)
    s = sum (n*(n-1) for n in app)
    total = sum(app)
    res = (s/(total*(total-1)))

    return res


def caesar_key_guess(chain):
    """
        Caesar key searching, based on letters frequencies analysis. The best guess is when the 
        frequencies of the ciphered text is "close" to the usual fequencies (for one language).

        To find the best match between frequencies, we can use either :
        - correlation (the highest score is the better)
        - difference (the lowest score is the better)

        :param chain: ciphered text
        :type chain: string
        :return: probable Caesar's key offset
        :rtype: int
    """
    correlation_list = {}
    diff_list = {}

    for dec in range(26):

        tested_chain = caesar(chain, -dec)
        freq_tbl = frequencies_analysis(tested_chain)

        # Correlation is (letter USUAL_FREQUENCIES * usual USUAL_FREQUENCIES), summed for every letter
        correl = sum(a * b for a, b in zip(freq_tbl,USUAL_FREQUENCIES[LANG]))
        correlation_list[dec] = correl

        # Difference is the distance between letter USUAL_FREQUENCIES and usual USUAL_FREQUENCIES, for each letter.
        lg = float(len(tested_chain))
        diff = sum(abs(b - USUAL_FREQUENCIES[LANG][a]) for a, b in enumerate([100 * letter / lg for letter in map(tested_chain.count, string.ascii_uppercase)]))

        diff_list[dec] = diff

    # Let's return the key og the highest value (correlation)
    sorted_list = sorted(correlation_list.items(), key=operator.itemgetter(1), reverse=True)
    offset = sorted_list[0][0]

    return offset


def vigenere_keylength_guess(chain):
    """
        Estimation of Vigenere's key length
    
        We try lengthes between 2 and 20. For each length, we calculate IC for every subchains, and then the mean.
        If the mean IC for one length is greater than the usual IC for target language, this length is a probable one.
        We can't be sure to find an eligible value.
        
        Source : https://fr.wikipedia.org/wiki/Indice_de_coïncidence
                 https://en.wikipedia.org/wiki/Index_of_coincidence 


        :param chain: ciphered text
        :type chain: string
        :return: probable Vigenere's key length (returns 0 if not found)
        :rtype: int
    """
    lg = 0
    while (True):
        lg = lg + 1
        if (lg == 21):
            break
        else:
            ic = sum(IC_calculation(chain[c::lg]) for c in range(0, lg)) / lg
            if (ic > USUAL_IC['fra']):
                return lg

    return 0


def frequencies_analysis(chain):
    """
        Text frequency analysis
        
        :param chain: any text
        :type chain: string
        :return: frequency of apparition for each letter
        :rtype: float[]
    """
    app = letters_apparitions(chain)
    total_length = len(chain)
    # Frequency calculation, for each letter 
    freq = [0.0] * 26
    for i in range(26):
        freq[i] = float(app[i] / total_length * 100)

    return freq


def vigenere_key_search(chain, lg) :
    """
        Searching for Vigenere's most probable key, for a given length, by guessing
        the Caesar's offset for each subchain

        :param chain: ciphered text
        :param lg: key length (must be calculated before)
        :type chain: string
        :type lg: int
        :return: Probable Vigenere's key
        :rtype: string
    """
    key = "".join(chr(65+caesar_key_guess(chain[i::lg])) for i in range(lg))
        
    return key

"""
  ------------------------------------
    Other useful functions
  ------------------------------------
"""
def letters_apparitions(chain):
    """
        Apparition count

        :param chain: chain
        :return: array of integer
        :rtype: int[]
    """
    res = []
    for fq in map(chain.count, string.ascii_uppercase):
        res.append(fq)

    return res


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

file_name = input("Please enter the file name (containing Vigenere's ciphered text) [{}]: ".format(DEFAULT_FILE_NAME))

# Defaut value, if you want...
if (len(file_name) == 0):
    file_name = str(DEFAULT_FILE_NAME)
    
# Text reading and cleaning
# Text must be uppercased, no space
original = ""
with open(file_name, 'r', encoding='utf-8') as f:
    original = original + f.read()

text = clean(original)
print()

# First we need to estimate the key length
lg = vigenere_keylength_guess(text)
print('Probable key length : {}'.format(lg))

# Then we try to guess the key
key = vigenere_key_search(text, lg)
print('Probable key        : {}'.format(key))

# And the we decipher the text
print()
deciphered = vigenere(original, key)
print(deciphered)


