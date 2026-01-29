"""
jps-controlled-vocabularies-utils

A standalone Python package for loading, managing, and validating controlled vocabularies
stored in YAML files.
"""

from jps_controlled_vocabularies_utils.exceptions import (
    ControlledVocabularyError,
    NotFoundError,
    ParseError,
    SchemaError,
    ValidationError,
)
from jps_controlled_vocabularies_utils.parser import Parser
from jps_controlled_vocabularies_utils.record import Record
from jps_controlled_vocabularies_utils.registry import Registry
from jps_controlled_vocabularies_utils.results import ValidationReport, ValueValidationResult
from jps_controlled_vocabularies_utils.validator import Validator
from jps_controlled_vocabularies_utils.vocabulary import Vocabulary

__version__ = "0.1.0"

__all__ = [
    "ControlledVocabularyError",
    "NotFoundError",
    "ParseError",
    "Parser",
    "Record",
    "Registry",
    "SchemaError",
    "ValidationError",
    "ValidationReport",
    "Validator",
    "ValueValidationResult",
    "Vocabulary",
]
