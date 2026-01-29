# This is generated and should not be edited manually
from typing import Literal

ScriptListType = Literal["Devanagari", "Telugu", "Tamil", "Tamil-Extended", "Bengali", "Kannada", "Gujarati", "Malayalam", "Odia", "Sinhala", "Normal", "Romanized", "Gurumukhi", "Assamese", "Purna-Devanagari", "Brahmi", "Granth", "Modi", "Sharada", "Siddham"]
"""List of all supported script names"""

LangListType = Literal["English", "Sanskrit", "Hindi", "Telugu", "Tamil", "Bengali", "Kannada", "Gujarati", "Malayalam", "Odia", "Sinhala", "Marathi", "Nepali", "Punjabi", "Assamese"]
"""List of all supported language names which are mapped to a script"""

ScriptAndLangListType = Literal["English", "Sanskrit", "Hindi", "Telugu", "Tamil", "Bengali", "Kannada", "Gujarati", "Malayalam", "Odia", "Sinhala", "Marathi", "Nepali", "Punjabi", "Assamese", "Devanagari", "Tamil-Extended", "Normal", "Romanized", "Gurumukhi", "Purna-Devanagari", "Brahmi", "Granth", "Modi", "Sharada", "Siddham"]
"""List of all Supported Script/Language"""

ScriptLangType = ScriptAndLangListType | Literal["de", "dev", "te", "tel", "tam", "tam-ext", "ta-ext", "ben", "be", "ka", "kan", "gu", "guj", "mal", "or", "od", "oriya", "si", "sinh", "sin", "en", "eng", "la", "lat", "nor", "norm", "rom", "gur", "as", "sa", "san", "hin", "hi", "mar", "ne", "nep", "pun"]
"""Supported script/language identifier types (aliases allowed)"""

TransliterationOptionsType = Literal["all_to_normal:replace_pancham_varga_varna_with_n", "brahmic_to_brahmic:replace_pancham_varga_varna_with_anusvAra", "all_to_sinhala:use_conjunct_enabling_halant", "all_to_normal:remove_virAma_and_double_virAma", "all_to_normal:replace_avagraha_with_a", "normal_to_all:use_typing_chars", "all_to_normal:preserve_specific_chars"]
