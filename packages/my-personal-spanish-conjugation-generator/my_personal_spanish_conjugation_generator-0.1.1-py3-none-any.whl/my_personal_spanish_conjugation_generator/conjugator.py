import json
from pathlib import Path
from typing import Dict

from .constants import Pronoun, Tense

COMPOUND_TENSES_MAPPING = {
    Tense.PRESENT_PERFECT: Tense.PRESENT,
    Tense.PLUPERFECT: Tense.IMPERFECT,
    Tense.CONDITIONAL_PERFECT: Tense.CONDITIONAL,
    Tense.FUTURE_PERFECT: Tense.FUTURE,
    Tense.PRESENT_PERFECT_SUBJUNCTIVE: Tense.PRESENT_SUBJUNCTIVE,
    Tense.PLUPERFECT_SUBJUNCTIVE: Tense.IMPERFECT_SUBJUNCTIVE,
}


class Conjugator:
    """
    A class to conjugate Spanish verbs.
    """

    def __init__(self, use_vosotros: bool = True):
        """
        Initializes the Conjugator by loading verb data from the JSON file.

        :param use_vosotros: Whether to include 'vosotros/vosotras' conjugations.
        """
        self.use_vosotros = use_vosotros
        data_path = Path(__file__).parent / "data" / "verbs.json"
        with open(data_path, "r", encoding="utf-8") as f:
            self.verb_data = json.load(f)

    def _get_past_participle(self, verb: str) -> str:
        """
        Returns the past participle of a verb.

        :param verb: The verb to get the past participle for.
        :return: The past participle of the verb.
        """
        if verb in self.verb_data["irregular_past_participles"]:
            return self.verb_data["irregular_past_participles"][verb]

        verb_ending = verb[-2:]
        stem = verb[:-2]
        if verb_ending == "ar":
            return stem + "ado"
        elif verb_ending in ["er", "ir"]:
            return stem + "ido"

        raise ValueError(f"Could not determine past participle for verb '{verb}'.")

    def get_all_conjugations(self, verb: str) -> Dict[str, Dict[str, str]]:
        """
        Returns all tenses and their conjugations for a given verb.

        :param verb: The verb to conjugate.
        :return: A dictionary of all tenses and their conjugations for the verb.
        :raises ValueError: If the verb is not found in the data.
        """
        all_conjugations = {}

        # Simple tenses
        if verb in self.verb_data["irregular_verbs"]:
            all_conjugations.update(self.verb_data["irregular_verbs"][verb])
        else:
            verb_ending = verb[-2:]
            if verb_ending in self.verb_data["regular_endings"]:
                stem = verb[:-2]
                for tense, endings in self.verb_data["regular_endings"][
                    verb_ending
                ].items():
                    all_conjugations[tense] = {
                        pronoun: stem + ending for pronoun, ending in endings.items()
                    }
            else:
                raise ValueError(f"Verb '{verb}' not found in the conjugation data.")

        # Compound tenses
        past_participle = self._get_past_participle(verb)
        for compound_tense, aux_tense in COMPOUND_TENSES_MAPPING.items():
            haber_conjugations = self.get_tense_conjugations("haber", aux_tense)
            all_conjugations[compound_tense] = {
                pronoun: f"{haber_form} {past_participle}"
                for pronoun, haber_form in haber_conjugations.items()
            }

        if not self.use_vosotros:
            for tense in all_conjugations:
                all_conjugations[tense].pop(Pronoun.VOSOTROS, None)

        return all_conjugations

    def get_tense_conjugations(self, verb: str, tense: Tense) -> Dict[str, str]:
        """
        Returns the pronoun-conjugation map for a specific tense.

        :param verb: The verb to conjugate.
        :param tense: The tense to conjugate the verb in.
        :return: A dictionary of pronouns and their conjugations for the verb in the given tense.
        :raises ValueError: If the verb or tense is not found in the data.
        """
        if tense in COMPOUND_TENSES_MAPPING:
            aux_tense = COMPOUND_TENSES_MAPPING[tense]
            haber_conjugations = self.get_tense_conjugations("haber", aux_tense)
            past_participle = self._get_past_participle(verb)
            conjugations = {
                pronoun: f"{haber_form} {past_participle}"
                for pronoun, haber_form in haber_conjugations.items()
            }
        else:
            # Logic for simple tenses
            if (
                verb in self.verb_data["irregular_verbs"]
                and tense in self.verb_data["irregular_verbs"][verb]
            ):
                conjugations = self.verb_data["irregular_verbs"][verb][tense]
            else:
                verb_ending = verb[-2:]
                if (
                    verb_ending in self.verb_data["regular_endings"]
                    and tense in self.verb_data["regular_endings"][verb_ending]
                ):
                    stem = verb[:-2]
                    endings = self.verb_data["regular_endings"][verb_ending][tense]
                    conjugations = {
                        pronoun: stem + ending for pronoun, ending in endings.items()
                    }
                else:
                    raise ValueError(f"Tense '{tense}' not found for verb '{verb}'.")

        if not self.use_vosotros:
            conjugations.pop(Pronoun.VOSOTROS, None)

        return conjugations

    def get_specific_conjugation(
        self, verb: str, tense: Tense, pronoun: Pronoun
    ) -> str:
        """
        Returns a single conjugated verb string.

        :param verb: The verb to conjugate.
        :param tense: The tense to conjugate the verb in.
        :param pronoun: The pronoun to conjugate the verb for.
        :return: The conjugated verb string.
        :raises ValueError: If the verb, tense, or pronoun is not found in the data.
        """
        if not self.use_vosotros and pronoun == Pronoun.VOSOTROS:
            raise ValueError("'vosotros/vosotras' pronoun is disabled.")

        if tense in COMPOUND_TENSES_MAPPING:
            aux_tense = COMPOUND_TENSES_MAPPING[tense]
            haber_form = self.get_specific_conjugation("haber", aux_tense, pronoun)
            past_participle = self._get_past_participle(verb)
            return f"{haber_form} {past_participle}"

        tense_conjugations = self.get_tense_conjugations(verb, tense)
        if pronoun in tense_conjugations:
            return tense_conjugations[pronoun]
        raise ValueError(
            f"Pronoun '{pronoun}' not found for verb '{verb}' in tense '{tense}'."
        )
