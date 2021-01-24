import string

from pattern.en import conjugate, PAST, PRESENT, INFINITIVE, SINGULAR, PLURAL
import spacy
from spacy.symbols import NOUN


PLURAL_MAP = {"we": "they", "us": "them", "ourselves": "themselves", "our": "their", "ours": "theirs"}
MASC_MAP   = {"i": "he",    "me": "him",  "myself": "himself",       "my": "his",    "mine": "his"}
FEM_MAP    = {"i": "she",   "me": "her",  "myself": "herself",       "my": "her",    "mine": "hers"}
THEY_MAP   = {"i": "they",  "me": "them", "myself": "theirself",     "my": "their",  "mine": "theirs"}

CONTRACT_MAP = {"has": "'s", "is": "'s"}


nlp = spacy.load('en_core_web_sm')


SUBJ_DEPS = {'agent', 'csubj', 'csubjpass', 'expl', 'nsubj', 'nsubjpass'}


def _get_conjuncts(tok):
    """
    Return conjunct dependents of the leftmost conjunct in a coordinated phrase,
    e.g. "Burton, [Dan], and [Josh] ...".
    """
    return [right for right in tok.rights
            if right.dep_ == 'conj']

def get_subjects_of_verb(verb):
    """Return all subjects of a verb according to the dependency parse."""
    if verb.dep_ == "aux" and list(verb.ancestors):
        return get_subjects_of_verb(list(verb.ancestors)[0])
    subjs = [tok for tok in verb.lefts
             if tok.dep_ in SUBJ_DEPS]
    # get additional conjunct subjects
    subjs.extend(tok for subj in subjs for tok in _get_conjuncts(subj))
    if not len(subjs):
        ancestors = list(verb.ancestors)
        if len(ancestors) > 0:
            return get_subjects_of_verb(ancestors[0])
    return subjs

def is_me(word):
    """Is this word 'I' or 'me'?"""
    return word.norm_ == "i"

def is_convertible_verb(word):
    """Is this word a verb that might need changing?"""
    if word.tag_ in ['VBG', 'VBN']:             # No infinitives or past participles
        return False
    elif word.tag_ == 'VB' and word.pos_ != 'AUX' and word.dep_ != 'conj': # and word.dep_ in ['advcl', relcl', 'xcomp', 'ROOT']:
        return False                            # Don't convert these infinitives
    elif word.pos_ == 'VERB':
        return True
    elif word.tag_ in ['VB', 'VBP', 'VBZ']:
        return True                             # Auxiliary verbs
    else:
        return False

def verb_to_third(verb):
    """Returns the 3rd-person form of a verg."""
    tense = PRESENT
    if verb.tag_ in ['VBD', 'VBN']:
        tense = PAST
    result = conjugate(verb.text, person=3, tense=tense)
    if result == None:
        # TODO: Log a warning
        return verb.text
    if verb.text[0] == "'":
        result = CONTRACT_MAP.get(result, result)   # Preserve contraction form
    return result


def change_to_third(input_text, to_pronoun, nlp=nlp, debug=0):
    """Change first person to third person.

    Args:
        text (str): text to change.
        to_pronoun (str): 'he', 'she', 'they'
        npl (SpaCy model, optional):

    Returns:
        str: changed text.

    """
    if to_pronoun == "he": 
        gender_map = MASC_MAP 
    elif to_pronoun == "she": 
        gender_map = FEM_MAP
    else:
        gender_map = THEY_MAP

    doc = nlp(input_text)

    out = list()
    quoted = False
    for word in doc:
        text = word.text
        text0 = text

        logWord = (debug > 1 and word.pos_ not in ['SPACE', 'PUNCT'])
        if logWord:
            print("\t'" + text + "', POS = " + word.pos_ + "', TAG = " + word.tag_ + ", DEP =" + word.dep_, end="")
        
        if word.tag_ == "``":
            # The tokenizer often thinks a closing straight-quote is opening:
            if quoted and word.text_with_ws == '" ':
                quoted = False
            else:
                quoted = True
        elif word.tag_ == "''":
            quoted = False

        if not quoted:
            if is_convertible_verb(word):
                # Check if verb's subject is "I":
                subjects = get_subjects_of_verb(word)
                if logWord: print(", SUBJECTS = ", subjects, end="")
                for subj in subjects:
                    if is_me(subj):
                        # OK, convert verb to 3rd person:
                        if logWord: print(", LEFTS =", list(word.lefts), end="")
                        text = verb_to_third(word)
                        break
            elif word.pos_ in ['DET', 'PRON']:
                # Convert 1st to 3rd person pronoun:
                text = PLURAL_MAP.get(word.norm_)
                if not text:
                    text = gender_map.get(word.norm_, text0)

            if word.is_sent_start and word.text[0].isupper():
                text = text.capitalize()

        if logWord:
            print("")
        if debug > 0 and text != text0:
            print("    ", text0, " --> ", text)

        out.append(text)

    text_out = ' '.join(out)

    # Remove spaces before/after punctuation:
    for char in string.punctuation:
        if char in """(<['""":
            text_out = text_out.replace(char+' ', char)
        else:
            text_out = text_out.replace(' '+char, char)

    for char in ["-", "“", "‘"]:
        text_out = text_out.replace(char+' ', char)
    for char in ["…", "”", "'s", "n't", "’"]:
        text_out = text_out.replace(' '+char, char)

    return text_out
