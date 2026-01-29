from enum import Enum


class Tense(str, Enum):
    """
    An enumeration of Spanish verb tenses.
    """

    PRESENT = "present"
    PRETERITE = "preterite"
    IMPERFECT = "imperfect"
    CONDITIONAL = "conditional"
    FUTURE = "future"
    PRESENT_SUBJUNCTIVE = "present_subjunctive"
    IMPERFECT_SUBJUNCTIVE = "imperfect_subjunctive"
    IMPERATIVE = "imperative"
    PRESENT_PERFECT = "present_perfect"
    PLUPERFECT = "pluperfect"
    CONDITIONAL_PERFECT = "conditional_perfect"
    FUTURE_PERFECT = "future_perfect"
    PRESENT_PERFECT_SUBJUNCTIVE = "present_perfect_subjunctive"
    PLUPERFECT_SUBJUNCTIVE = "pluperfect_subjunctive"


class Pronoun(str, Enum):
    """
    An enumeration of Spanish subject pronouns.
    """

    YO = "yo"
    TU = "tú"
    EL = "él/ella/usted"
    NOSOTROS = "nosotros/nosotras"
    VOSOTROS = "vosotros/vosotras"
    ELLOS = "ellos/ellas/ustedes"
