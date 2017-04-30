import string
from pattern.en import conjugate, PAST, PRESENT, SINGULAR, PLURAL
from spacy.en import English
from spacy.symbols import NOUN

from utils import pairwise


SUBJ_DEPS = {'agent', 'csubj', 'csubjpass', 'expl', 'nsubj', 'nsubjpass'}

nlp = English()


def _get_conjuncts(tok):
    """
    Return conjunct dependents of the leftmost conjunct in a coordinated phrase,
    e.g. "Burton, [Dan], and [Josh] ...".
    """
    return [right for right in tok.rights
            if right.dep_ == 'conj']


def is_plural_noun(token):
    """
    Returns True if token is a plural noun, False otherwise.

    Args:
        token (``spacy.Token``): parent document must have POS information

    Returns:
        bool
    """
    if token.doc.is_tagged is False:
        raise ValueError('token is not POS-tagged')
    return True if token.pos == NOUN and token.lemma != token.lower else False


def get_subjects_of_verb(verb):
    if verb.dep_ == "aux" and list(verb.ancestors):
        return get_subjects_of_verb(list(verb.ancestors)[0])
    """Return all subjects of a verb according to the dependency parse."""
    subjs = [tok for tok in verb.lefts
             if tok.dep_ in SUBJ_DEPS]
    # get additional conjunct subjects
    subjs.extend(tok for subj in subjs for tok in _get_conjuncts(subj))
    if not len(subjs):
        return get_subjects_of_verb(list(verb.ancestors)[0])
    return subjs


def is_plural_verb(token):
    if token.doc.is_tagged is False:
        raise ValueError('token is not POS-tagged')
    subjects = get_subjects_of_verb(token)
    if not len(subjects):
        return False
    plural_score = sum([is_plural_noun(x) for x in subjects])/len(subjects)

    return plural_score > .5


def change_tense(text, to_tense, nlp=nlp):

    tense_lookup = {'future': 'inf', 'present': PRESENT, 'past': PAST}
    tense = tense_lookup[to_tense]

    doc = nlp(unicode(text))

    out = list()
    out.append(doc[0].text)
    for word_pair in pairwise(doc):
        if (word_pair[0].text == 'will' and word_pair[0].tag_ == 'MD' and word_pair[1].tag_ == 'VB') or \
                        word_pair[1].tag_ in ('VBD', 'VBP', 'VBZ', 'VBN') or \
                (not word_pair[0].text in ('to', 'not') and word_pair[1].tag_ == 'VB'):
            subjects = [x.text for x in get_subjects_of_verb(word_pair[1])]
            if ('I' in subjects) or ('we' in subjects) or ('We' in subjects):
                person = 1
            elif ('you' in subjects) or ('You' in subjects):
                person = 2
            else:
                person = 3
            if is_plural_verb(word_pair[1]):
                number = PLURAL
            else:
                number = SINGULAR
            if (word_pair[0].text == 'will' and word_pair[0].tag_ == 'MD') or word_pair[0].text == 'had':
                out.pop(-1)
            if to_tense == 'future' and out[-1] is not 'will':
                out.append('will')
            #if word_pair[0].dep_ == 'auxpass':
            out.append(conjugate(word_pair[1].text, tense=tense, person=person, number=number))
        else:
            out.append(word_pair[1].text)

        # negation
        if word_pair[0].text+word_pair[1].text in ('didnot', 'donot', 'willnot'):
            if tense == PAST:
                out[-2] = 'did'
            elif tense == PRESENT:
                out[-2] = 'do'
            else:
                out.pop(-2)

        # future perfect, and progressives, but ignore for "I will have cookies"
        if word_pair[1].text in ('have', 'has') and len(list(word_pair[1].ancestors)) and word_pair[1].dep_ == 'aux':
            out.pop(-1)

    text_out = ' '.join(out)

    for char in string.punctuation:
        if char in """(<['""":
            text_out = text_out.replace(char+' ', char)
        else:
            text_out = text_out.replace(' '+char, char)

    text_out = text_out.replace(" 's", "'s")  # fix posessive 's

    return text_out