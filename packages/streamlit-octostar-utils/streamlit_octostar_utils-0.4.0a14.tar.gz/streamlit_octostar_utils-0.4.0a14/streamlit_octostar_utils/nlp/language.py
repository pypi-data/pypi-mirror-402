import re
from typing import Optional

import py3langid as langid

from iso639 import Lang
from iso639.exceptions import InvalidLanguageValue

FLAIR_MODELS = {
    "en": "flair/ner-english-fast",
    "es": "flair/ner-multi",
    "de": "flair/ner-multi",
    "nl": "flair/ner-multi",
    "fr": "flair/ner-multi",
    "it": "flair/ner-multi",
    "pt": "flair/ner-multi",
    "pl": "flair/ner-multi",
    "ru": "flair/ner-multi",
    "sv": "flair/ner-multi",
    "no": "flair/ner-multi",
    "da": "flair/ner-multi",
}

SPACY_MODELS = {
    "en": "en_core_web_sm",
    "es": "es_core_news_sm",
    "fr": "fr_core_news_sm",
    "de": "de_core_news_sm",
    "it": "it_core_news_sm",
    "pt": "pt_core_news_sm",
    "nl": "nl_core_news_sm",
    "pl": "pl_core_news_sm",
    "ru": "ru_core_news_sm",
    "sv": "sv_core_news_sm",
    "no": "nb_core_news_sm",
    "da": "da_core_news_sm",
    "fi": "fi_core_news_sm",
    "el": "el_core_news_sm",
    "zh": "zh_core_web_sm",
    "ja": "ja_core_news_sm",
    "ko": "ko_core_news_sm",
    "ar": "ar_core_news_sm",
    "ca": "ca_core_news_sm",
}


def to_name(language: str) -> str:
    """Convert a language code or name to its full name.
    
    Args:
        language: Language name or alpha2 code (e.g., 'en' or 'English')
    
    Returns:
        Full language name (e.g., 'English')
    
    Raises:
        ValueError: If language is empty or invalid
    """
    if not language:
        raise ValueError("Language must be a non-empty string.")
    
    try:
        return Lang(language).name
    except InvalidLanguageValue:
        name = re.sub(r'\b\w+', lambda m: m.group(0).capitalize(), language)
        try:
            return Lang(name).name
        except InvalidLanguageValue:
            raise ValueError(f"Invalid language: {language}")


def to_alpha2(language: str) -> str:
    """Convert a language name or code to its alpha2 code.
    
    Args:
        language: Language name or alpha2 code (e.g., 'English' or 'en')
    
    Returns:
        Alpha2 language code (e.g., 'en')
    
    Raises:
        ValueError: If language is empty or invalid
    """
    if not language:
        raise ValueError("Language must be a non-empty string.")
    
    try:
        lang_obj = Lang(language)
        return lang_obj.pt1
    except InvalidLanguageValue:
        name = re.sub(r'\b\w+', lambda m: m.group(0).capitalize(), language)
        try:
            return Lang(name).pt1
        except InvalidLanguageValue:
            raise ValueError(f"Invalid language: {language}")


def detect_language(text, min_confidence=None):
    """Detect the language of a text string.
    
    Args:
        text: Text to detect language for
        min_confidence: Minimum confidence threshold (0-1). If set and confidence is below
                       this threshold, returns None for language
    
    Returns:
        Tuple of (language_name, confidence) where language_name is the full name
        (e.g., 'English') or None if confidence is below threshold
    """
    detector = langid.langid.LanguageIdentifier.from_pickled_model(
        langid.langid.MODEL_FILE, norm_probs=True
    )
    detected_lang, confidence = detector.classify(text)
    if min_confidence and confidence < min_confidence:
        return None, confidence
    detected_lang = to_name(detected_lang)
    return detected_lang, confidence


def is_language_available(language: Optional[str], type: str) -> bool:
    """Check if a language model is available for the given language.
    
    Args:
        language: Language name or alpha2 code (e.g., 'English' or 'en')
        type: Model type ('spacy' or 'flair')
    
    Returns:
        True if a model is available for the language, False otherwise
    """
    if not language:
        return False

    try:
        lang_code = to_alpha2(language)
    except (InvalidLanguageValue, ValueError):
        return False

    match type:
        case "spacy":
            return lang_code in SPACY_MODELS

        case "flair":
            return lang_code in FLAIR_MODELS
        
        case _:
            return False


def load_language_model(languages, type):
    """Load language models for the specified languages.
    
    Args:
        languages: Single language string or list of languages (names or alpha2 codes)
        type: Model type ('spacy' or 'flair')
    
    Returns:
        Dictionary mapping language to loaded model, or single model if input was a string
    
    Raises:
        Exception: If a model for the specified language is not available
    """
    from flair.models import SequenceTagger
    from spacy_download import load_spacy
    
    return_as_one = False
    original_input = None
    if isinstance(languages, str):
        original_input = languages
        languages = [languages]
        return_as_one = True
    
    models_dict = {}
    model_to_langs = {}
    
    match type:
        case "spacy":
            for lang in languages:
                if is_language_available(lang, "spacy"):
                    lang_code = to_alpha2(lang)
                    model_name = SPACY_MODELS.get(lang_code, SPACY_MODELS["en"])
                    if model_name not in model_to_langs:
                        model_to_langs[model_name] = []
                    model_to_langs[model_name].append(lang)
                else:
                    raise Exception(f"SpaCy model for language '{lang}' is not available.")
            
            loaded_models = {}
            for model_name, langs in model_to_langs.items():
                loaded_models[model_name] = load_spacy(model_name)
            
            for model_name, langs in model_to_langs.items():
                for lang in langs:
                    models_dict[lang] = loaded_models[model_name]
        
        case "flair":
            for lang in languages:
                if is_language_available(lang, "flair"):
                    lang_code = to_alpha2(lang)
                    model_name = FLAIR_MODELS.get(lang_code)
                    if model_name not in model_to_langs:
                        model_to_langs[model_name] = []
                    model_to_langs[model_name].append(lang)
                else:
                    raise Exception(f"Flair model for language '{lang}' is not available.")
            
            loaded_models = {}
            for model_name, langs in model_to_langs.items():
                loaded_models[model_name] = SequenceTagger.load(model_name)
            
            for model_name, langs in model_to_langs.items():
                for lang in langs:
                    models_dict[lang] = loaded_models[model_name]
        
        case _:
            raise ValueError(f"Unsupported model type: {type}")
    
    if return_as_one:
        return models_dict[original_input]
    return models_dict