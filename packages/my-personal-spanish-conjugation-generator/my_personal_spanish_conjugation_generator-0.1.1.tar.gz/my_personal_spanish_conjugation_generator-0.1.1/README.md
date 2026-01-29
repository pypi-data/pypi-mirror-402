# Spanish Verb Conjugator

A lightweight Python library for conjugating Spanish verbs across a comprehensive range of tenses and moods. This tool is designed for developers, language learners, and anyone in need of a quick and reliable way to get Spanish verb conjugations.

## Features

-   **Wide Tense Coverage**: Supports indicative, subjunctive, and imperative moods, including simple and perfect tenses.
-   **Irregular Verbs**: Includes a built-in list of common irregular verbs and their special conjugations.
-   **Vosotros Support**: Provides conjugations for the `vosotros/vosotras` pronoun, commonly used in Spain. This can be disabled for a Latin American Spanish focus.
-   **Easy to Use**: A simple and intuitive API for getting the conjugations you need.

## Installation

You can install the library using `pip`:

```bash
pip install spanish-conjugator
```

## Usage

The library is easy to use. Simply import the `Conjugator`, `Tense`, and `Pronoun` classes, and you're ready to start conjugating.

### Basic Example

Here's how to get a specific conjugation for a verb:

```python
from spanish_conjugator import Conjugator, Tense, Pronoun

# Initialize the conjugator
conjugator = Conjugator()

# Get the 'yo' form of 'hablar' in the present tense
verb = "hablar"
tense = Tense.PRESENT
pronoun = Pronoun.YO

conjugation = conjugator.get_specific_conjugation(verb, tense, pronoun)
print(f"The conjugation of '{verb}' for '{pronoun.value}' in the {tense.value} tense is: {conjugation}")
# Output: The conjugation of 'hablar' for 'yo' in the present tense is: hablo
```

### Getting All Conjugations for a Tense

You can also get all pronoun conjugations for a specific tense:

```python
# Get all present tense conjugations for 'comer'
conjugations = conjugator.get_tense_conjugations("comer", Tense.PRESENT)
for pronoun, form in conjugations.items():
    print(f"{pronoun}: {form}")
```

### Getting All Conjugations for a Verb

To get a complete dictionary of all supported tenses for a verb:

```python
all_conjugations = conjugator.get_all_conjugations("vivir")

# Print the future tense conjugations
future_tense = all_conjugations.get(Tense.FUTURE)
if future_tense:
    for pronoun, form in future_tense.items():
        print(f"{pronoun}: {form}")
```

### Disabling 'Vosotros'

If you want to exclude the `vosotros/vosotras` pronoun, initialize the `Conjugator` with `use_vosotros=False`:

```python
# Conjugator for Latin American Spanish (without vosotros)
la_conjugator = Conjugator(use_vosotros=False)

conjugations = la_conjugator.get_tense_conjugations("ser", Tense.PRESENT)
print("vosotros/vosotras" in conjugations)
# Output: False
```

## Supported Tenses

The library supports the following tenses:

-   **Indicative**: Present, Preterite, Imperfect, Conditional, Future, Present Perfect, Pluperfect, Conditional Perfect, Future Perfect
-   **Subjunctive**: Present, Imperfect, Present Perfect, Pluperfect
-   **Imperative**: Affirmative

## Supported Irregular Verbs

A list of common irregular verbs is included. Some examples are:

-   `acertar`
-   `agradecer`
-   `aparecer`
-   `atraer`
-   `decir`
-   `hacer`
-   `ir`
-   `oler`
-   `pedir`
-   `perder`
-   `poder`
-   `poner`
-   `reir`
-   `ser`
-   `sonreir`
-   `tener`
-   `volar`
-   `volver`

And many more.
