import itertools
import logging
import math
import multiprocessing
import re
from typing import Optional, List, Tuple

from iso639.exceptions import InvalidLanguageValue
from pydantic import BaseModel, ConfigDict, Field

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, AnalysisExplanation, \
    EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts, NlpEngineProvider
from presidio_analyzer.predefined_recognizers import SpacyRecognizer, PhoneRecognizer
import streamlit as st
import nltk
from flair.data import Sentence
from flair.models import SequenceTagger

from .custom_recognizers import PhonePatternRecognizer, ModernUrlRecognizer

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.nlp.stemmers import Stemmer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.utils import get_stop_words

from .language import to_name, SPACY_MODELS

# Suppress Presidio's verbose logging
logging.getLogger("presidio_analyzer").setLevel(logging.ERROR)

BASE_ALLOWED_LABELS = ["PERSON", "ORG", "LOC", "DATE", "PHONE", "IP_ADDRESS", "EMAIL", "URL",
                       "CRYPTO", "IBAN", "CREDIT_CARD", "US_SSN", "US_DRIVER_LICENSE", "US_PASSPORT", "MEDICAL_LICENSE"]

LABELS_PRIORITY = {
    "PERSON": 100,
    "LOC": 50,
    "ORG": 25,
    "DATE": 10,
    "EMAIL": 10,
    "PHONE": 10,
    "URL": 10,
    "IBAN": 10,
    "CREDIT_CARD": 10,
    "US_SSN": 10,
    "US_DRIVER_LICENSE": 10,
    "US_PASSPORT": 10,
    "MEDICAL_LICENSE": 10,
    "CRYPTO": 10,
    "IP_ADDRESS": 10,
}

NAME_LIKE_LABELS = ["PERSON", "ORG", "LOC"]
CASE_INSENSITIVE_LABELS = ["EMAIL", "PERSON", "ORG", "LOC"]
UPPERCASE_LABELS = ["IBAN", "CREDIT_CARD", "US_SSN", "US_DRIVER_LICENSE", "US_PASSPORT", "CRYPTO"]

PRESIDIO_TO_BASE_ALIASES = {
    "PHONE_NUMBER": "PHONE",
    "EMAIL_ADDRESS": "EMAIL",
    "IBAN_CODE": "IBAN",
    "DRIVER_LICENSE": "US_DRIVER_LICENSE",
    "US_DRIVER_LICENSE": "US_DRIVER_LICENSE",
    "US_DRIVERS_LICENSE": "US_DRIVER_LICENSE",
    "PASSPORT": "US_PASSPORT",
    "CREDIT_CARD": "CREDIT_CARD",
    "URL": "URL",
    "IP_ADDRESS": "IP_ADDRESS",
    "CRYPTO": "CRYPTO",
    "CRYPTO_WALLET": "CRYPTO",
    "CRYPTO_WALLET_ADDRESS": "CRYPTO",
    "DATE_TIME": "DATE",
    "LOCATION": "LOC",
    "ORGANIZATION": "ORG",
    "GPE": "LOC",
    "NORP": "ORG",
}

BASE_TO_RECOGNIZER_EXPANSIONS = {
    "ORG": ["ORG", "ORGANIZATION", "NORP"],
    "LOC": ["LOC", "LOCATION", "GPE"],
    "PHONE": ["PHONE", "PHONE_NUMBER"],
    "EMAIL": ["EMAIL", "EMAIL_ADDRESS"],
    "IBAN": ["IBAN", "IBAN_CODE"],
    "US_DRIVER_LICENSE": ["US_DRIVER_LICENSE", "US_DRIVERS_LICENSE", "DRIVER_LICENSE"],
    "US_PASSPORT": ["US_PASSPORT", "PASSPORT"],
    "DATE": ["DATE", "DATE_TIME"],
    "PERSON": ["PERSON"],
    "URL": ["URL"],
    "IP_ADDRESS": ["IP_ADDRESS"],
    "CRYPTO": ["CRYPTO", "CRYPTO_WALLET", "CRYPTO_WALLET_ADDRESS"],
    "CREDIT_CARD": ["CREDIT_CARD"],
    "US_SSN": ["US_SSN"],
    "MEDICAL_LICENSE": ["MEDICAL_LICENSE"],
}

REGEX_RECOGNIZER_NAMES = [
    "EmailRecognizer",
    "IbanRecognizer", 
    "CreditCardRecognizer",
    "PhoneRecognizer",
    "IpRecognizer",
    "UrlRecognizer",
    "CryptoRecognizer",
    "UsSsnRecognizer",
    "UsLicenseRecognizer",
    "UsPassportRecognizer",
    "MedicalLicenseRecognizer",
    "DateRecognizer",
    "UsItinRecognizer",
    "SgFinRecognizer",
    "AuAbnRecognizer",
    "AuAcnRecognizer",
    "AuTfnRecognizer",
    "AuMedicareRecognizer",
    "InPanRecognizer",
]


class FlairRecognizer(EntityRecognizer):
    ENTITIES = [
        "LOC",
        "PERSON",
        "ORG",
    ]

    DEFAULT_EXPLANATION = "Identified as {} by Flair's Named Entity Recognition"

    CHECK_LABEL_GROUPS = [
        ({"LOC"}, {"LOC", "LOCATION"}),
        ({"PERSON"}, {"PER", "PERSON"}),
        ({"ORG"}, {"ORG", "ORGANIZATION"}),
    ]

    PRESIDIO_EQUIVALENCES = {
        "PER": "PERSON",
        "LOC": "LOC",
        "ORG": "ORG"
    }

    def __init__(
            self,
            model: SequenceTagger = None,
            supported_language: str = "en",
            supported_entities: Optional[List[str]] = None,
            check_label_groups: Optional[Tuple[set, set]] = None,
    ):
        self.check_label_groups = (
            check_label_groups if check_label_groups else self.CHECK_LABEL_GROUPS
        )

        supported_entities = supported_entities if supported_entities else self.ENTITIES
        self.model = model

        super().__init__(
            supported_entities=supported_entities,
            supported_language=supported_language,
            name="Flair Analytics",
        )

    def load(self) -> None:
        pass

    def get_supported_entities(self) -> List[str]:
        return self.supported_entities

    def analyze(self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None) -> List[RecognizerResult]:
        results = []

        sentences = Sentence(text)
        self.model.predict(sentences)

        if not entities:
            entities = self.supported_entities

        for entity in entities:
            if entity not in self.supported_entities:
                continue

            for ent in sentences.get_spans("ner"):
                if not self.__check_label(
                        entity, ent.labels[0].value, self.check_label_groups
                ):
                    continue
                textual_explanation = self.DEFAULT_EXPLANATION.format(
                    ent.labels[0].value
                )
                explanation = self.build_flair_explanation(
                    round(ent.score, 2), textual_explanation
                )
                flair_result = self._convert_to_recognizer_result(ent, explanation)

                results.append(flair_result)

        return results

    def build_flair_explanation(self, original_score: float, explanation: str) -> AnalysisExplanation:
        explanation = AnalysisExplanation(
            recognizer=self.__class__.__name__,
            original_score=original_score,
            textual_explanation=explanation,
        )
        return explanation

    def _convert_to_recognizer_result(self, entity, explanation) -> RecognizerResult:
        entity_type = self.PRESIDIO_EQUIVALENCES.get(entity.tag, entity.tag)
        flair_score = round(entity.score, 2)

        flair_results = RecognizerResult(
            entity_type=entity_type,
            start=entity.start_position,
            end=entity.end_position,
            score=flair_score,
            analysis_explanation=explanation,
        )

        return flair_results

    @staticmethod
    def __check_label(
            entity: str, label: str, check_label_groups: Tuple[set, set]
    ) -> bool:
        return any(
            [entity in egrp and label in lgrp for egrp, lgrp in check_label_groups]
        )


class CustomCallableRecognizer(EntityRecognizer):
    """
    Custom recognizer that wraps any callable NER function.
    
    The callable should accept (text: str, language: str) and return a list of dicts with these exact keys:
    - label: entity type (e.g., "PERSON", "LOC", "ORG")
    - text: the entity text
    - score: confidence score (0-1)
    - start: start character position in text
    - end: end character position in text
    
    The user's lambda/function is responsible for transforming their model's output 
    to this format, giving them full control over the mapping.
    
    Example:
        def my_ner(text: str, language: str):
            results = some_model(text)
            return [
                {
                    "label": "PERSON",
                    "text": "John Doe", 
                    "score": 0.95,
                    "start": 0,
                    "end": 8
                }
            ]
    """
    
    ENTITIES = ["LOC", "PERSON", "ORG"]
    
    DEFAULT_EXPLANATION = "Identified as {} by Custom NER Model"
    
    def __init__(
            self,
            ner_callable,
            supported_language: str = "en",
            supported_entities: Optional[List[str]] = None,
    ):
        """
        Args:
            ner_callable: Function that takes (text: str, language: str) and returns NER results
            supported_language: Language code
            supported_entities: List of entity types to detect
        """
        supported_entities = supported_entities if supported_entities else self.ENTITIES
        self.ner_callable = ner_callable
        self.language = supported_language
        
        super().__init__(
            supported_entities=supported_entities,
            supported_language=supported_language,
            name="Custom Callable NER",
        )
    
    def load(self) -> None:
        pass
    
    def get_supported_entities(self) -> List[str]:
        return self.supported_entities
    
    def analyze(self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None) -> List[RecognizerResult]:
        results = []
        
        if not entities:
            entities = self.supported_entities
        
        try:
            ner_results = self.ner_callable(text, self.language)
            
            for ner_item in ner_results:
                # Expect exact keys: label, text, score, start, end
                # The user's lambda is responsible for mapping their model's output to this format
                
                entity_type = ner_item.get("label")
                entity_text = ner_item.get("text")
                score = ner_item.get("score", 1.0)
                start = ner_item.get("start")
                end = ner_item.get("end")
                
                # Validate required fields
                if not entity_type or entity_text is None or start is None or end is None:
                    logging.warning(
                        f"Custom NER callable returned incomplete result. "
                        f"Expected keys: label, text, score, start, end. Got: {ner_item.keys()}"
                    )
                    continue
                
                # Skip if not in requested entities
                if entity_type not in entities:
                    continue
                
                # Create explanation
                textual_explanation = self.DEFAULT_EXPLANATION.format(entity_type)
                explanation = AnalysisExplanation(
                    recognizer=self.__class__.__name__,
                    original_score=score,
                    textual_explanation=textual_explanation,
                )
                
                # Create RecognizerResult
                result = RecognizerResult(
                    entity_type=entity_type,
                    start=start,
                    end=end,
                    score=score,
                    analysis_explanation=explanation,
                )
                
                results.append(result)
        
        except Exception as e:
            logging.error(f"Error in custom NER callable: {e}")
            import traceback
            traceback.print_exc()
        
        return results


def normalize_presidio_label(label: str) -> str:
    return PRESIDIO_TO_BASE_ALIASES.get(label, label)


def normalize_entity_name(name: str, label: str) -> str:
    """
    Normalize entity names for consistency and better deduplication.
    
    Different normalization strategies based on entity type:
    - Name-like entities (PERSON, ORG, LOC): full normalization
    - Technical entities (URL, EMAIL, PHONE, etc.): only strip whitespace
    
    Args:
        name: The entity name to normalize
        label: The entity label/type
        
    Returns:
        Normalized entity name
    """
    normalized = name.strip()

    if label in NAME_LIKE_LABELS:
        normalized = re.sub(r'[^\w\s\-\'.]+', '', normalized)
        normalized = re.sub(r'\s*-\s*', '-', normalized)
        normalized = re.sub(r"\s*'\s*", "'", normalized)
        normalized = re.sub(r'\s*\.\s*', '.', normalized)
        normalized = re.sub(r'\.(?=[a-zA-Z])', '. ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.strip()

    if label in UPPERCASE_LABELS:
        normalized = normalized.upper()
    elif label in CASE_INSENSITIVE_LABELS:
        normalized = normalized.lower()

    return normalized



def expand_entities_for_analyzer(entities_list):
    expanded = set()
    for e in entities_list:
        vals = BASE_TO_RECOGNIZER_EXPANSIONS.get(e, [e])
        for v in vals:
            expanded.add(v)
    return list(expanded)


def _sumy__get_best_sentences(sentences, rating, *args, **kwargs):
    from operator import attrgetter
    from sumy.summarizers._summarizer import SentenceInfo

    rate = rating
    if isinstance(rating, dict):
        assert not args and not kwargs
        rate = lambda s: rating[s]
    infos = (SentenceInfo(s, o, rate(s, *args, **kwargs)) for o, s in enumerate(sentences))
    infos = sorted(infos, key=attrgetter("rating"), reverse=True)
    return tuple((i.sentence, i.rating, i.order) for i in infos)


def _sumy__lsa_call(summarizer, document):
    summarizer._ensure_dependecies_installed()
    dictionary = summarizer._create_dictionary(document)
    if not dictionary:
        return ()
    matrix = summarizer._create_matrix(document, dictionary)
    matrix = summarizer._compute_term_frequency(matrix)
    from numpy.linalg import svd as singular_value_decomposition

    u, sigma, v = singular_value_decomposition(matrix, full_matrices=False)
    ranks = iter(summarizer._compute_ranks(sigma, v))
    return _sumy__get_best_sentences(document.sentences, lambda s: next(ranks))


def _sumy__luhn_call(summarizer, document):
    words = summarizer._get_significant_words(document.words)
    return _sumy__get_best_sentences(document.sentences, summarizer.rate_sentence, words)


def get_nltk_tokenizer(language: str) -> Tokenizer:
    try:
        nltk_lang = to_name(language).lower()

    except InvalidLanguageValue:
        nltk_lang = language

    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")

    return Tokenizer(nltk_lang)


class NERObject(BaseModel):
    name: str
    label: str
    score: float = 0.0
    start: int
    count: int
    context: str | None = None
    comentions: list[str] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")

    def __repr__(self):
        return f"NERObject(label={self.label},name={self.name})"


def postprocess_ner(entities: list[NERObject], whitelisted_labels=None, max_entities=None, prioritize_entity_types=True):
    """
    Post-process NER entities: normalize, deduplicate, and merge.
    
    Args:
        entities: List of NER entities to process
        whitelisted_labels: Optional list of entity types to keep
        max_entities: Maximum number of entities to return
        prioritize_entity_types: If True, when multiple entities have the same name,
                                prioritize PERSON > LOC > ORG > technical entities
    
    Returns:
        List of processed and deduplicated NER entities
    """
    # Entity type priority (higher = more important)
    # Used when multiple models detect the same text as different entity types
    
    
    if whitelisted_labels is not None:
        entities = [e for e in entities if e.label in whitelisted_labels]
    
    # Normalize entity names
    for entity in entities:
        entity.name = normalize_entity_name(entity.name, entity.label)
    
    # Filter out empty names
    entities = [e for e in entities if e.name]
    
    # Sort by normalized name for grouping
    entities = sorted(entities, key=lambda x: x.name)
    
    final_entities = []
    for _, group in itertools.groupby(entities, key=lambda x: x.name):
        group = list(group)
        
        # Select best entity based on priority and confidence
        if prioritize_entity_types and len(group) > 1:
            def entity_rank(e):
                priority = LABELS_PRIORITY.get(e.label, 0)
                confidence = e.score * e.count
                # Combine priority (weighted heavily) with confidence
                return priority * 10 + confidence
            
            best_entity = max(group, key=entity_rank)
        else:
            # Original behavior: select by score * count only
            best_entity = max(group, key=lambda x: x.score * x.count)
        
        # Merge data from all entities with the same name
        merged_data = {
            "name": best_entity.name,
            "label": best_entity.label,
            "score": best_entity.score,
            "context": best_entity.context,
            "count": sum(e.count for e in group),
            "start": best_entity.start,
        }
        
        # Merge additional fields
        all_fields = type(best_entity).model_fields.keys()
        for field in all_fields:
            if field in merged_data:
                continue
            values = [getattr(e, field, None) for e in group if getattr(e, field, None) is not None]
            if not values:
                continue
            if isinstance(values[0], list):
                merged_data[field] = list(set(itertools.chain.from_iterable(values or [])))
            else:
                merged_data[field] = getattr(best_entity, field, None)
        
        final_entities.append(NERObject(**merged_data))
    
    # Sort by relevance (score * count)
    final_entities = sorted(final_entities, key=lambda x: x.score * x.count, reverse=True)
    
    if max_entities and len(final_entities) > max_entities:
        final_entities = final_entities[:max_entities]
    
    return final_entities


def build_presidio_analyzer(language: str, engine_type: str = "spacy", model=None) -> AnalyzerEngine:
    """
    Build a Presidio analyzer with EXCLUSIVE engine types.
    
    Args:
        language: Language code (e.g., "en", "de", "fr", "it")
        engine_type: One of:
            - "regex": Only pattern-based recognizers (phones, emails, IBANs, etc.)
            - "flair": Only Flair NER (PERSON, ORG, LOC)
            - "spacy": Only spaCy NER (PERSON, ORG, LOC, etc.)
            - "custom": Custom NER model or callable
        model: For "flair" - Flair SequenceTagger or model name
               For "spacy" - spaCy model name
               For "custom" - Either:
                   * Callable (lambda/function) that takes (text: str, language: str)
                     and returns list of dicts with EXACT keys:
                     {"label": str, "text": str, "score": float, "start": int, "end": int}
                   * Pre-loaded Flair SequenceTagger instance
               For "regex" - ignored (can be None)
    
    Returns:
        AnalyzerEngine configured for the specified engine type only
    """
    registry = RecognizerRegistry()
    
    if engine_type == "regex":
        default_registry = RecognizerRegistry()
        default_registry.load_predefined_recognizers(languages=["en"])
        for recognizer in default_registry.recognizers:
            if recognizer.name in REGEX_RECOGNIZER_NAMES:
                if recognizer.name == "UrlRecognizer":
                    continue
                elif recognizer.name == "PhoneRecognizer":
                    phone_recognizer = PhoneRecognizer(
                        supported_language=language,
                        leniency=0
                    )
                    registry.add_recognizer(phone_recognizer)
                else:
                    recognizer.supported_language = language
                    if hasattr(recognizer, 'supported_languages'):
                        recognizer.supported_languages = [language]
                    registry.add_recognizer(recognizer)
        phone_pattern_recognizer = PhonePatternRecognizer(
            supported_language=language
        )
        registry.add_recognizer(phone_pattern_recognizer)
        modern_url_recognizer = ModernUrlRecognizer(
            supported_language=language
        )
        registry.add_recognizer(modern_url_recognizer)
        registry.supported_languages = [language]
        spacy_model = SPACY_MODELS.get(language)
        if spacy_model is None:
            spacy_model = SPACY_MODELS.get("en", "en_core_web_sm")
            nlp_lang = "en"
        else:
            nlp_lang = language
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": nlp_lang, "model_name": spacy_model}],
        }
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        return AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=[language])
    
    elif engine_type == "flair":
        if model is None:
            raise ValueError("Flair model must be provided")
        if isinstance(model, str):
            flair_model = SequenceTagger.load(model)
        else:
            flair_model = model
        
        flair_recognizer = FlairRecognizer(
            model=flair_model,
            supported_language=language
        )
        registry.add_recognizer(flair_recognizer)
        registry.supported_languages = [language]
        spacy_model = SPACY_MODELS.get(language, SPACY_MODELS.get("en", "en_core_web_sm"))
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": language, "model_name": spacy_model}],
        }
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        return AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=[language])
    
    elif engine_type == "spacy":
        if model is None:
            raise ValueError("SpaCy model name must be provided")
        spacy_recognizer = SpacyRecognizer(supported_language=language)
        registry.add_recognizer(spacy_recognizer)
        registry.supported_languages = [language]
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": language, "model_name": model}],
        }
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        return AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=[language])
    
    elif engine_type == "custom":
        if model is None:
            raise ValueError("Custom model must be provided")
        
        # Check if model is a callable (lambda, function, etc.)
        if callable(model):
            custom_recognizer = CustomCallableRecognizer(
                ner_callable=model,
                supported_language=language
            )
        # Check if model is a Flair SequenceTagger
        elif isinstance(model, SequenceTagger):
            custom_recognizer = FlairRecognizer(
                model=model,
                supported_language=language
            )
        else:
            raise ValueError(
                "Custom model must be either a callable (function/lambda) "
                "that takes (text: str, language: str) and returns NER results, "
                "or a Flair SequenceTagger instance"
            )
        
        registry.add_recognizer(custom_recognizer)
        registry.supported_languages = [language]
        spacy_model = SPACY_MODELS.get(language, SPACY_MODELS.get("en", "en_core_web_sm"))
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": language, "model_name": spacy_model}],
        }
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        return AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=[language])
    
    else:
        raise ValueError(f"Unknown engine_type: {engine_type}. Must be 'regex', 'flair', 'spacy', or 'custom'")


def compute_ner_presidio(
        text,
        language,
        analyzer,
        engine_type="spacy",
        entities=None,
        score_threshold=0.5,
        context_width=150,
        with_comentions=True,
        with_context=True,
        batch_size=32,
        n_process=None
):
    if n_process is None:
        if engine_type in ["flair", "custom"]:
            n_process = 1
        else:
            n_process = multiprocessing.cpu_count()
    # Prevent CUDA fork issues
    if engine_type in ["flair", "custom"] and n_process > 1:
        raise ValueError("n_process must be 1 for Flair and custom models")
    
    # Single text string processing
    results = analyzer.analyze(
        text=text,
        language=language,
        entities=(expand_entities_for_analyzer(entities) if entities else None)
    )
    ner_objects = []
    for result in results:
        if result.score >= score_threshold:
            context_start = max(0, result.start - math.floor(context_width / 2))
            context_end = min(len(text), result.end + math.ceil(context_width / 2))
            context = text[context_start:context_end] if with_context else None
            ner_objects.append(NERObject(
                name=text[result.start:result.end],
                label=normalize_presidio_label(result.entity_type),
                score=float(result.score),
                start=int(result.start),
                count=1,
                context=context
            ))
    if with_comentions:
        for i in range(len(ner_objects)):
            entity = ner_objects[i]
            comentions = [
                ner_objects[j].name
                for j in range(len(ner_objects))
                if j != i and abs(ner_objects[j].start - entity.start) < math.ceil(context_width / 2)
            ]
            ner_objects[i].comentions = comentions
    return ner_objects


def get_extractive_summary(text, language, max_chars, fast=False, with_scores=False):
    tokenizer = get_nltk_tokenizer(language)
    stemmer = Stemmer(language)
    parser = PlaintextParser.from_string(text, tokenizer)
    if fast:
        summarizer = LuhnSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(language)
        scored_sentences = iter(_sumy__luhn_call(summarizer, parser.document))
    else:
        summarizer = LsaSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(language)
        scored_sentences = iter(_sumy__lsa_call(summarizer, parser.document))
    summary = []
    summary_chars = 0
    summary_chars_penultimate = 0
    while summary_chars < max_chars:
        try:
            next_sentence = next(scored_sentences)
            summary.append(next_sentence)
            summary_chars_penultimate = summary_chars
            summary_chars += len(" " + next_sentence[0]._text)
        except StopIteration:
            break
    summary = sorted(summary, key=lambda x: x[2])
    summary = [(sentence[0]._text, sentence[1]) for sentence in summary]
    if summary_chars > max_chars:
        summary[-1] = (
            summary[-1][0][: max_chars - summary_chars_penultimate],
            summary[-1][1],
        )
    if not with_scores:
        summary = " ".join([s[0] for s in summary])
    else:
        min_score = min([s[1] for s in summary]) if summary else 0
        max_score = max([min_score] + [s[1] for s in summary])
        score_range = 1 if min_score == max_score else (max_score - min_score)
        summary = [(s[0], (s[1] - min_score) / score_range) for s in summary]
    return summary


def _preprocess_newlines_for_ner(text: str) -> str:
    """
    Replace newline-containing whitespace sequences with ' — — ' (space + em dashes + space).
    
    This helps NER models treat text on separate lines as distinct entities,
    preventing merging of e.g. "Jennifer Williams\\nMegaCorp" into a single entity.
    
    Handles:
    - Single newlines: \\n
    - Carriage returns: \\r\\n, \\r
    - Mixed whitespace with newlines: '  \\n  ', '\\n\\n', etc.
    
    All are collapsed into a single ' — — ' separator.
    """
    pattern = r'[ \t]*[\r\n]+[ \t\r\n]*'
    return re.sub(pattern, ' — — ', text)


def _strip_honorifics_for_ner(text: str) -> str:
    """
    Remove abbreviated honorifics/titles from text to prevent them from interfering with NER.
    
    Returns:
        Text with honorifics removed, preserving the rest of the content
    """
    honorifics = [
        # English
        r'Dr', r'Mr', r'Mrs', r'Ms', r'Miss', r'Prof', r'Rev', r'Revd',
        r'Hon', r'Sr', r'Jr', r'Esq',
        
        # Italian
        r'Dott', r'Dott\.ssa', r'Dott\.re',
        r'Prof', r'Prof\.ssa',
        r'Sig', r'Sig\.ra', r'Sig\.na',
        r'Avv', r'Ing', r'Arch', r'Geom',
        r'Rag',

        # German
        r'Herr', r'Frau', r'Frl', r'Fräulein',
        r'Dipl\.-Ing', r'Dipl\.-Kfm', r'Dipl',
        
        # French
        r'M', r'Mme', r'Mlle', r'Mgr', r'Me',
        
        # Spanish
        r'D', r'Dª', r'Doña', r'Don',
        r'Dra', r'Sra', r'Srta',
        
        # General academic/professional
        r'Ph\.D', r'M\.D', r'B\.Sc', r'M\.Sc', r'B\.A', r'M\.A',
    ]
    pattern = r'\b(' + '|'.join(honorifics) + r')\.?\s+'
    result = re.sub(pattern, '', text, flags=re.IGNORECASE)
    result = re.sub(r'\s{2,}', ' ', result)
    return result


def ner_pipe(
        text,
        language,
        model,
        engine_type="spacy",
        fast=False,
        compression_ratio="auto",
        with_scores=False,
        with_comentions=True,
        with_context=True,
        entities=None,
        score_threshold=0.5,
        batch_size=32,
        n_process=None,
        preprocess_newlines=True
):
    """
    Run NER pipeline on text.
    
    Args:
        text: Input text (str). For multiple texts, iterate and call this function for each.
        language: Language code (e.g., 'en', 'de', 'fr')
        model: Model name for spacy/flair engine
        engine_type: 'regex', 'flair', or 'spacy'
        fast: Use fast summarization for long texts
        compression_ratio: Compression ratio for long texts ('auto' or float)
        with_scores: Include confidence scores (not implemented)
        with_comentions: Include co-mentioned entities
        with_context: Include surrounding context
        entities: List of entity types to detect (None = all)
        score_threshold: Minimum confidence score
        batch_size: Batch size for processing
        n_process: Number of parallel processes
        preprocess_newlines: Replace newlines with ' — ' to prevent entity merging
    """
    if with_scores:
        raise NotImplementedError("with_scores functionality is not implemented yet")
    
    if not isinstance(text, str):
        raise TypeError(f"text must be str, not {type(text).__name__}")

    analyzer = build_presidio_analyzer(
        language=language,
        engine_type=engine_type,
        model=model,
    )

    if preprocess_newlines:
        text = _preprocess_newlines_for_ner(text)
    text = _strip_honorifics_for_ner(text)

    if compression_ratio == "auto":
        compression_ratio = max(1.0, len(text) / 15000) if fast else 1.0

    if compression_ratio > 1.0:
        sentences = get_extractive_summary(text, language, int(len(text) / compression_ratio), fast=fast,
                                           with_scores=True)
        text = " ".join([s[0] for s in sentences])

    ner = compute_ner_presidio(
        text,
        language,
        analyzer,
        engine_type,
        entities,
        score_threshold,
        with_comentions=with_comentions,
        with_context=with_context,
        batch_size=batch_size,
        n_process=n_process
    )

    return ner


def get_ner_handler(
        language,
        model,
        engine_type="spacy",
        fast=False,
        entities=None,
        score_threshold=0.5,
        batch_size=32,
        n_process=None,
        preprocess_newlines=True
):
    try:
        get_nltk_tokenizer(language)
    except LookupError:
        language = "en"

    return lambda text, compression_ratio="auto", with_scores=False, with_comentions=True, with_context=True: ner_pipe(
        text,
        language,
        model,
        engine_type,
        fast,
        compression_ratio,
        with_scores,
        with_comentions,
        with_context,
        entities,
        score_threshold,
        batch_size,
        n_process,
        preprocess_newlines
    )


@st.cache_resource
def get_cached_ner_handler(language, model):
    return get_ner_handler(language, model)
