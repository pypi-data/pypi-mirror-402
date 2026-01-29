"""
JobExtractor - Professional job description extraction package.

A production-ready Python package for extracting structured information
from job descriptions using various LLM providers.
"""

__version__ = "0.1.0"
__author__ = "Otmane El Bourki"
__email__ = "otmane.elbourki@gmail.com"

from .models import JobInformation
from .extractor import JobExtractor
from .formatters import (
    format_output_text,
    generate_txt_file,
    generate_json_file,
    format_batch_results,
)

__all__ = [
    "JobInformation",
    "JobExtractor",
    "format_output_text",
    "generate_txt_file",
    "generate_json_file",
    "format_batch_results",
]
