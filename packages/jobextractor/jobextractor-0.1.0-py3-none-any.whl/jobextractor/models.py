"""Pydantic models for structured job information extraction."""
from typing import List, Optional
from pydantic import BaseModel, Field


class JobInformation(BaseModel):
    """Structured model for extracted job information.
    
    This model represents all the structured information that can be
    extracted from a job description using LLM-based extraction.
    
    Attributes:
        job_title: The job title or position name (required)
        seniority_level: Seniority level (e.g., Junior, Mid-level, Senior)
        years_of_experience: Required years of experience
        work_type: Work arrangement (Remote, Hybrid, or On-site)
        location: Job location (city, state, country, or 'Remote')
        salary: Salary range or compensation information
        required_criteria: Required qualifications, skills, or criteria
        preferred_qualifications: Preferred but not required qualifications
        scope_of_responsibilities: Key responsibilities and duties
        company_name: Company or organization name
        department: Department or team name
        benefits: Benefits and perks mentioned
        skills: Technical skills, tools, or technologies required
        education_requirements: Education requirements (degree, certifications, etc.)
        additional_info: Any additional relevant information
    """
    
    job_title: str = Field(description="The job title or position name")
    seniority_level: Optional[str] = Field(
        default=None, 
        description="Seniority level (e.g., Junior, Mid-level, Senior, Lead, Principal)"
    )
    years_of_experience: Optional[str] = Field(
        default=None,
        description="Required years of experience (e.g., '3-5 years', '5+ years')"
    )
    work_type: Optional[str] = Field(
        default=None,
        description="Work arrangement: Remote, Hybrid, or On-site"
    )
    location: Optional[str] = Field(
        default=None,
        description="Job location (city, state, country, or 'Remote')"
    )
    salary: Optional[str] = Field(
        default=None,
        description="Salary range or compensation information"
    )
    required_criteria: List[str] = Field(
        default_factory=list,
        description="Required qualifications, skills, or criteria"
    )
    preferred_qualifications: List[str] = Field(
        default_factory=list,
        description="Preferred but not required qualifications"
    )
    scope_of_responsibilities: List[str] = Field(
        default_factory=list,
        description="Key responsibilities and duties"
    )
    company_name: Optional[str] = Field(
        default=None,
        description="Company or organization name"
    )
    department: Optional[str] = Field(
        default=None,
        description="Department or team name"
    )
    benefits: List[str] = Field(
        default_factory=list,
        description="Benefits and perks mentioned"
    )
    skills: List[str] = Field(
        default_factory=list,
        description="Technical skills, tools, or technologies required"
    )
    education_requirements: Optional[str] = Field(
        default=None,
        description="Education requirements (degree, certifications, etc.)"
    )
    additional_info: Optional[str] = Field(
        default=None,
        description="Any additional relevant information"
    )
