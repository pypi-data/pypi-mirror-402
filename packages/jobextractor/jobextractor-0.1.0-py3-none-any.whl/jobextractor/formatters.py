"""File formatting utilities for job extraction results."""
from datetime import datetime
from typing import List, Optional
import json

from .models import JobInformation


def format_output_text(job_info: JobInformation, extraction_date: Optional[str] = None) -> str:
    """Format extracted information as a well-formatted text file.
    
    Args:
        job_info: Extracted job information
        extraction_date: Date string when extraction was performed (defaults to now)
        
    Returns:
        Formatted text string
    """
    if extraction_date is None:
        extraction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output = []
    output.append("=" * 80)
    output.append("JOB INFORMATION EXTRACTION")
    output.append("=" * 80)
    output.append(f"\nExtraction Date: {extraction_date}\n")
    output.append("-" * 80)
    
    # Basic Information
    output.append("\nBASIC INFORMATION")
    output.append("-" * 80)
    if job_info.job_title:
        output.append(f"Job Title: {job_info.job_title}")
    if job_info.company_name:
        output.append(f"Company: {job_info.company_name}")
    if job_info.department:
        output.append(f"Department: {job_info.department}")
    if job_info.seniority_level:
        output.append(f"Seniority Level: {job_info.seniority_level}")
    if job_info.years_of_experience:
        output.append(f"Years of Experience: {job_info.years_of_experience}")
    
    # Work Arrangement
    output.append("\nWORK ARRANGEMENT")
    output.append("-" * 80)
    if job_info.work_type:
        output.append(f"Work Type: {job_info.work_type}")
    if job_info.location:
        output.append(f"Location: {job_info.location}")
    
    # Compensation
    if job_info.salary:
        output.append("\nCOMPENSATION")
        output.append("-" * 80)
        output.append(f"Salary: {job_info.salary}")
    
    # Education
    if job_info.education_requirements:
        output.append("\nEDUCATION REQUIREMENTS")
        output.append("-" * 80)
        output.append(job_info.education_requirements)
    
    # Required Criteria
    if job_info.required_criteria:
        output.append("\nREQUIRED CRITERIA")
        output.append("-" * 80)
        for i, criterion in enumerate(job_info.required_criteria, 1):
            output.append(f"{i}. {criterion}")
    
    # Preferred Qualifications
    if job_info.preferred_qualifications:
        output.append("\nPREFERRED QUALIFICATIONS")
        output.append("-" * 80)
        for i, qual in enumerate(job_info.preferred_qualifications, 1):
            output.append(f"{i}. {qual}")
    
    # Skills
    if job_info.skills:
        output.append("\nSKILLS & TECHNOLOGIES")
        output.append("-" * 80)
        for i, skill in enumerate(job_info.skills, 1):
            output.append(f"{i}. {skill}")
    
    # Scope of Responsibilities
    if job_info.scope_of_responsibilities:
        output.append("\nSCOPE OF RESPONSIBILITIES")
        output.append("-" * 80)
        for i, responsibility in enumerate(job_info.scope_of_responsibilities, 1):
            output.append(f"{i}. {responsibility}")
    
    # Benefits
    if job_info.benefits:
        output.append("\nBENEFITS & PERKS")
        output.append("-" * 80)
        for i, benefit in enumerate(job_info.benefits, 1):
            output.append(f"{i}. {benefit}")
    
    # Additional Information
    if job_info.additional_info:
        output.append("\nADDITIONAL INFORMATION")
        output.append("-" * 80)
        output.append(job_info.additional_info)
    
    output.append("\n" + "=" * 80)
    return "\n".join(output)


def generate_txt_file(job_info: JobInformation, extraction_date: Optional[str] = None) -> str:
    """Generate formatted TXT file content.
    
    Args:
        job_info: Extracted job information
        extraction_date: Date string when extraction was performed (defaults to now)
        
    Returns:
        Formatted text string
    """
    return format_output_text(job_info, extraction_date)


def generate_json_file(job_info: JobInformation, indent: int = 2) -> str:
    """Generate JSON file content.
    
    Args:
        job_info: Extracted job information
        indent: JSON indentation level (default: 2)
        
    Returns:
        JSON string with indentation
    """
    return job_info.model_dump_json(indent=indent, exclude_none=True)


def format_batch_results(
    results: List[Optional[JobInformation]],
    format_type: str = "json"
) -> str:
    """Format batch extraction results.
    
    Args:
        results: List of JobInformation objects (may include None for failures)
        format_type: Output format ('json' or 'txt')
        
    Returns:
        Formatted string with all results
    """
    # Filter out None values
    valid_results = [r for r in results if r is not None]
    
    if format_type.lower() == "json":
        results_dict = {
            "total": len(results),
            "successful": len(valid_results),
            "failed": len(results) - len(valid_results),
            "results": [r.model_dump(exclude_none=True) for r in valid_results]
        }
        return json.dumps(results_dict, indent=2, default=str)
    else:
        # TXT format
        output = []
        output.append("=" * 80)
        output.append("BATCH JOB INFORMATION EXTRACTION")
        output.append("=" * 80)
        output.append(f"\nTotal: {len(results)}")
        output.append(f"Successful: {len(valid_results)}")
        output.append(f"Failed: {len(results) - len(valid_results)}")
        output.append("=" * 80)
        
        for idx, result in enumerate(valid_results, 1):
            output.append(f"\n\n{'=' * 80}")
            output.append(f"JOB #{idx}")
            output.append("=" * 80)
            output.append(format_output_text(result))
        
        return "\n".join(output)
