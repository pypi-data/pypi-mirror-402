"""Main extractor class supporting multiple LLM providers via LiteLLM."""
import json
import logging
from typing import List, Optional, Union, Dict, Any
from datetime import datetime

from pydantic import ValidationError

try:
    import litellm
    from litellm import completion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    litellm = None
    completion = None

from .models import JobInformation

# Configure logging
logger = logging.getLogger(__name__)


class JobExtractor:
    """Extracts structured information from job descriptions using various LLM providers.
    
    This class supports multiple LLM providers through LiteLLM, including:
    - OpenAI (GPT-4o, GPT-4o-mini, GPT-4.1, GPT-5, GPT-5.2)
    - Anthropic (Claude Sonnet 4.5, Claude Opus 4.5, Claude Sonnet 4)
    - Google (Gemini 3 Flash, Gemini 3 Pro, Gemini 2.0 Flash)
    - Local models via Ollama (Llama 3.3, Llama 3.2, Mistral, etc.)
    - And 100+ other providers supported by LiteLLM
    
    Examples:
        Basic usage with OpenAI:
        >>> extractor = JobExtractor(provider="openai", api_key="sk-...")
        >>> result = extractor.extract("We are looking for a Senior Python Developer...")
        
        Using Ollama (local):
        >>> extractor = JobExtractor(provider="ollama", model="llama3.2")
        >>> result = extractor.extract("Job description text...")
        
        Batch processing:
        >>> descriptions = ["Job 1...", "Job 2...", "Job 3..."]
        >>> results = extractor.extract_batch(descriptions)
    """
    
    # Default models for each provider (latest stable models as of January 2026)
    DEFAULT_MODELS = {
        "openai": "gpt-4o",  # Latest stable flagship (GPT-5.2 available but may need explicit selection)
        "anthropic": "claude-sonnet-4.5-20250929",  # Latest Claude Sonnet 4.5 (Sep 2025)
        "google": "gemini/gemini-2.0-flash",  # Latest stable Gemini Flash model
        "ollama": "llama3.3",  # Latest Llama 3.3 (70B, 128K context)
        "groq": "llama-3.3-70b-versatile",  # Latest Groq-supported Llama model
        "cohere": "command-a-03-2025",  # Latest Command A (most performant, Mar 2025)
    }
    
    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs
    ):
        """Initialize the job extractor.
        
        Args:
            provider: LLM provider name (e.g., 'openai', 'anthropic', 'google', 'ollama')
            api_key: API key for the provider (not needed for local models like Ollama)
            model: Model name to use (defaults to provider's default model)
            base_url: Custom base URL (useful for local deployments or proxies)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
            **kwargs: Additional provider-specific parameters
        
        Raises:
            ImportError: If LiteLLM is not installed
            ValueError: If provider is not supported
        """
        if not LITELLM_AVAILABLE:
            raise ImportError(
                "LiteLLM is required. Install it with: pip install litellm"
            )
        
        self.provider = provider.lower()
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.kwargs = kwargs
        
        # Set default model if not provided
        if model is None:
            if self.provider in self.DEFAULT_MODELS:
                self.model = self.DEFAULT_MODELS[self.provider]
            else:
                # For Ollama, default to llama3.2
                if self.provider == "ollama":
                    self.model = "llama3.2"
                else:
                    raise ValueError(
                        f"Unknown provider '{provider}'. "
                        f"Supported providers: {', '.join(self.DEFAULT_MODELS.keys())}"
                    )
        else:
            self.model = model
        
        # Configure LiteLLM
        self._configure_litellm()
        
        logger.info(f"JobExtractor initialized with provider: {self.provider}, model: {self.model}")
    
    def _configure_litellm(self):
        """Configure LiteLLM with provider settings."""
        # Set API key if provided
        if self.api_key:
            if self.provider == "openai":
                litellm.api_key = self.api_key
            elif self.provider == "anthropic":
                litellm.anthropic_key = self.api_key
            elif self.provider == "google":
                litellm.google_api_key = self.api_key
            elif self.provider == "groq":
                litellm.groq_api_key = self.api_key
            elif self.provider == "cohere":
                litellm.cohere_api_key = self.api_key
            # For Ollama, base_url is typically http://localhost:11434
            elif self.provider == "ollama":
                if self.base_url is None:
                    self.base_url = "http://localhost:11434"
        
        # Set base URL if provided
        if self.base_url:
            litellm.api_base = self.base_url
    
    def _build_prompt(self, job_description: str) -> str:
        """Build the extraction prompt.
        
        Args:
            job_description: Raw job description text
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze the following job description and extract all relevant structured information.

Extract information about:
- Job title, company name, and department
- Seniority level and years of experience required
- Work arrangement (Remote, Hybrid, or On-site) and location
- Salary or compensation information
- Required criteria and qualifications
- Preferred qualifications
- Scope of responsibilities and duties
- Technical skills and technologies
- Education requirements
- Benefits and perks
- Any additional relevant information

Job Description:
{job_description}

Extract all relevant information. If a field is not mentioned in the job description, use null for optional string fields or an empty array for list fields.

Return the response as a valid JSON object matching this schema:
{json.dumps(JobInformation.model_json_schema(), indent=2)}"""
    
    def extract(
        self,
        job_description: str,
        model: Optional[str] = None,
        **kwargs
    ) -> Optional[JobInformation]:
        """Extract structured information from a single job description.
        
        Args:
            job_description: Raw job description text
            model: Override the default model for this extraction
            **kwargs: Additional parameters to pass to the LLM call
        
        Returns:
            JobInformation object with extracted data, or None if extraction fails
        """
        if not job_description or not job_description.strip():
            logger.warning("Empty job description provided")
            return None
        
        model_to_use = model or self.model
        prompt = self._build_prompt(job_description)
        
        # Build model string for LiteLLM
        if self.provider == "ollama":
            model_string = f"ollama/{model_to_use}"
        elif self.provider == "google":
            model_string = f"gemini/{model_to_use}" if not model_to_use.startswith("gemini/") else model_to_use
        else:
            model_string = model_to_use
        
        try:
            logger.info(f"Extracting information using {model_string}")
            
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            
            # Prepare additional parameters
            completion_kwargs = {**self.kwargs, **kwargs}
            
            # For Google/Gemini, ensure API key is passed explicitly
            if self.provider == "google" and self.api_key:
                completion_kwargs["api_key"] = self.api_key
            
            # Call LLM with structured output
            response = completion(
                model=model_string,
                messages=messages,
                response_format={"type": "json_object"},
                timeout=self.timeout,
                max_retries=self.max_retries,
                **completion_kwargs
            )
            
            # Extract JSON from response
            content = response.choices[0].message.content
            
            # Parse JSON
            try:
                json_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response content: {content[:500]}")
                return None
            
            # Validate and create JobInformation object
            job_info = JobInformation.model_validate(json_data)
            logger.info(f"Successfully extracted information for job: {job_info.job_title}")
            return job_info
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting information: {e}", exc_info=True)
            return None
    
    def extract_batch(
        self,
        job_descriptions: Union[List[str], List[Dict[str, Any]]],
        model: Optional[str] = None,
        show_progress: bool = True,
        **kwargs
    ) -> List[Optional[JobInformation]]:
        """Extract structured information from multiple job descriptions.
        
        Args:
            job_descriptions: List of job description strings or dicts with 'text' key
            model: Override the default model for this batch
            show_progress: Whether to log progress (default: True)
            **kwargs: Additional parameters to pass to each LLM call
        
        Returns:
            List of JobInformation objects (None for failed extractions)
        
        Examples:
            >>> extractor = JobExtractor(provider="openai", api_key="sk-...")
            >>> descriptions = ["Job 1...", "Job 2...", "Job 3..."]
            >>> results = extractor.extract_batch(descriptions)
            >>> # Filter out None values
            >>> successful = [r for r in results if r is not None]
        """
        results = []
        total = len(job_descriptions)
        
        for idx, item in enumerate(job_descriptions, 1):
            # Handle both string and dict inputs
            if isinstance(item, dict):
                job_text = item.get("text", item.get("description", ""))
            else:
                job_text = item
            
            if show_progress:
                logger.info(f"Processing {idx}/{total}...")
            
            result = self.extract(job_text, model=model, **kwargs)
            results.append(result)
        
        successful = sum(1 for r in results if r is not None)
        logger.info(f"Batch extraction complete: {successful}/{total} successful")
        
        return results
    
    def extract_with_metadata(
        self,
        job_description: str,
        metadata: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Extract information and include metadata in the result.
        
        Args:
            job_description: Raw job description text
            metadata: Additional metadata to include (e.g., source, date, etc.)
            model: Override the default model for this extraction
            **kwargs: Additional parameters to pass to the LLM call
        
        Returns:
            Dictionary with 'job_info' and 'metadata' keys, or None if extraction fails
        """
        job_info = self.extract(job_description, model=model, **kwargs)
        
        if job_info is None:
            return None
        
        result = {
            "job_info": job_info,
            "metadata": {
                "extraction_date": datetime.now().isoformat(),
                "provider": self.provider,
                "model": model or self.model,
                **(metadata or {})
            }
        }
        
        return result
