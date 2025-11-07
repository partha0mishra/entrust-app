"""
Knowledge Base Setup Script for RAG Integration
Downloads and organizes curated documents for data governance dimensions.
"""

import os
import requests
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base directory for knowledge
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "Knowledge"

# Knowledge source configuration
# Format: (url, filename, description)
KNOWLEDGE_SOURCES: Dict[str, List[Tuple[str, str, str]]] = {
    "maturity": [
        (
            "https://raw.githubusercontent.com/DAMA-UPC/DataQualityManagement/main/DAMA-DMBOK-Framework.md",
            "dama_dmbok_maturity.txt",
            "DAMA-DMBOK Maturity Levels (1-5: Initial, Repeatable, Defined, Managed, Optimized)"
        ),
        (
            "https://www.lightsondata.com/data-governance-maturity-models-gartner/",
            "gartner_eim_maturity.txt",
            "Gartner EIM Maturity Model"
        ),
        (
            "https://www.lightsondata.com/data-governance-maturity-models-ibm/",
            "ibm_maturity.txt",
            "IBM Data Governance Maturity Model"
        ),
    ],
    "privacy_compliance": [
        (
            "https://raw.githubusercontent.com/ansipunk/awesome-gdpr/master/README.md",
            "gdpr_overview.txt",
            "GDPR Best Practices and Guidelines"
        ),
        (
            "https://raw.githubusercontent.com/wbh1/ccpa-compliance/master/README.md",
            "ccpa_overview.txt",
            "CCPA Compliance Guidelines"
        ),
    ],
    "ethics_bias": [
        (
            "https://raw.githubusercontent.com/MichiganNLP/fairness-datasets/main/README.md",
            "ai_ethics_bias.txt",
            "AI Ethics and Bias Mitigation"
        ),
    ],
    "lineage_traceability": [
        (
            "https://raw.githubusercontent.com/finos/tracdap/main/doc/architecture/data-lineage.md",
            "data_lineage_standards.txt",
            "Data Lineage and Traceability Standards"
        ),
    ],
    "value_lifecycle": [
        (
            "https://raw.githubusercontent.com/DAMA-UPC/DataLifeCycle/main/README.md",
            "data_lifecycle_management.txt",
            "Data Lifecycle Management Framework"
        ),
    ],
    "governance_management": [
        (
            "https://raw.githubusercontent.com/DAMA-UPC/DataGovernance/main/README.md",
            "data_governance_framework.txt",
            "DAMA-DMBOK Data Governance Framework"
        ),
    ],
    "security_access": [
        (
            "https://raw.githubusercontent.com/0xsp-SRD/NIST-Cybersecurity-Framework/master/README.md",
            "nist_security_framework.txt",
            "NIST Cybersecurity Framework"
        ),
        (
            "https://raw.githubusercontent.com/wiiisdom/awesome-security-architecture/master/README.md",
            "iso27001_overview.txt",
            "ISO 27001 Security Standards"
        ),
    ],
    "metadata_documentation": [
        (
            "https://raw.githubusercontent.com/opendatadiscovery/opendatadiscovery-specification/main/specification/specification.md",
            "metadata_standards.txt",
            "Metadata and Documentation Standards"
        ),
    ],
    "quality": [
        (
            "https://raw.githubusercontent.com/whylabs/whylogs/mainline/README.md",
            "data_quality_frameworks.txt",
            "Data Quality Frameworks and Standards"
        ),
    ],
}

# Fallback content for when downloads fail
FALLBACK_CONTENT: Dict[str, str] = {
    "maturity": """# Data Governance Maturity Models

## DAMA-DMBOK Maturity Levels

### Level 1: Initial (Ad Hoc)
- Processes are unpredictable, poorly controlled, and reactive
- Work gets completed but is often delayed and over budget
- Success depends on individual heroics

### Level 2: Repeatable (Managed)
- Basic project management processes established
- Repeatable practices for similar types of projects
- Success can be repeated for projects with similar applications

### Level 3: Defined (Standardized)
- Processes well characterized and understood
- Documented in standards, procedures, tools, and methods
- Organization-wide standards provide guidance across projects

### Level 4: Managed (Quantitatively Managed)
- Detailed measures of process and product quality collected
- Processes and products are quantitatively understood and controlled
- Performance is predictable

### Level 5: Optimized (Continuous Improvement)
- Focus on continually improving process performance
- Continuous process improvement is enabled by quantitative feedback
- Piloting innovative ideas and technologies

## Gartner EIM Maturity Stages

### Stage 1: Awareness
- Recognizing the need for data governance
- Ad hoc data management practices

### Stage 2: Reactive
- Responding to data issues as they arise
- Basic policies beginning to emerge

### Stage 3: Intentional
- Proactive data governance initiatives
- Defined roles and responsibilities

### Stage 4: Managed
- Systematic approach to data management
- Metrics and KPIs in place

### Stage 5: Effective
- Optimized data governance
- Data treated as strategic asset
""",
    "privacy_compliance": """# Privacy and Compliance Best Practices

## GDPR Key Principles (Article 5)

1. **Lawfulness, Fairness, and Transparency**
   - Process data lawfully, fairly, and transparently
   - Clear communication with data subjects

2. **Purpose Limitation**
   - Collect data for specified, explicit, and legitimate purposes
   - No further processing incompatible with original purpose

3. **Data Minimization**
   - Adequate, relevant, and limited to what's necessary
   - Avoid collecting excessive data

4. **Accuracy**
   - Keep personal data accurate and up to date
   - Erase or rectify inaccurate data

5. **Storage Limitation**
   - Keep data only as long as necessary
   - Implement data retention policies

6. **Integrity and Confidentiality**
   - Ensure appropriate security
   - Protect against unauthorized processing

## CCPA Requirements

- **Right to Know**: What personal information is collected
- **Right to Delete**: Request deletion of personal information
- **Right to Opt-Out**: Opt out of sale of personal information
- **Right to Non-Discrimination**: Equal service regardless of privacy choices

## ISO 27701 Privacy Controls

- Privacy impact assessments
- Consent management
- Data subject rights management
- Privacy by design and by default
""",
    "ethics_bias": """# Data Ethics and Bias Mitigation

## Ethical AI Principles

1. **Fairness and Non-Discrimination**
   - Ensure AI systems don't discriminate
   - Regular bias audits and testing

2. **Transparency and Explainability**
   - Make AI decisions understandable
   - Document model logic and data sources

3. **Privacy and Data Protection**
   - Respect user privacy
   - Implement data minimization

4. **Accountability**
   - Clear ownership of AI systems
   - Mechanisms for redress

## Bias Mitigation Strategies

### Pre-processing
- Balanced dataset collection
- Bias detection in training data
- Reweighting or resampling techniques

### In-processing
- Fair learning algorithms
- Adversarial debiasing
- Regularization techniques

### Post-processing
- Threshold optimization
- Calibration
- Output transformation

## Fairness Metrics
- Demographic Parity
- Equal Opportunity
- Equalized Odds
- Individual Fairness
""",
    "lineage_traceability": """# Data Lineage and Traceability

## DAMA-DMBOK Lineage Principles

### Business Lineage
- End-to-end business process view
- Maps business terms to data elements
- Supports regulatory compliance

### Technical Lineage
- System-to-system data flows
- Transformation logic documentation
- Source-to-target mappings

### Operational Lineage
- Runtime execution tracking
- Actual data flow capture
- Performance monitoring

## Key Capabilities

1. **Impact Analysis**
   - Upstream dependency identification
   - Downstream impact assessment
   - Change propagation analysis

2. **Root Cause Analysis**
   - Data quality issue tracing
   - Error source identification
   - Issue resolution tracking

3. **Compliance Support**
   - Audit trail maintenance
   - Regulatory reporting
   - Data sovereignty tracking

## Best Practices

- Automate lineage capture where possible
- Maintain metadata in central repository
- Document transformation rules
- Regular lineage validation
- Integration with data catalogs
""",
    "value_lifecycle": """# Data Value and Lifecycle Management

## Data Lifecycle Stages

### 1. Planning and Design
- Requirements gathering
- Data modeling
- Architecture design

### 2. Creation and Acquisition
- Data generation
- Data collection
- Data integration

### 3. Storage and Maintenance
- Database management
- Data warehousing
- Backup and recovery

### 4. Usage and Enhancement
- Data access
- Data analysis
- Data sharing

### 5. Archival
- Long-term storage
- Compliance retention
- Cost optimization

### 6. Disposal
- Secure deletion
- Regulatory compliance
- Audit trail

## Value Assessment

### Business Value Metrics
- Revenue impact
- Cost reduction
- Risk mitigation
- Decision improvement

### Data Quality Dimensions
- Accuracy
- Completeness
- Consistency
- Timeliness
- Validity

## Lifecycle Governance

- Data classification policies
- Retention schedules
- Access controls by stage
- Quality requirements by stage
""",
    "governance_management": """# Data Governance and Management

## DAMA-DMBOK Governance Framework

### Core Principles

1. **Data is an Asset**
   - Strategic organizational resource
   - Requires active management
   - Generates value

2. **Accountability**
   - Clear ownership and stewardship
   - Defined roles and responsibilities
   - Decision rights framework

3. **Quality**
   - Fitness for purpose
   - Continuous improvement
   - Measurable standards

## Governance Operating Model

### Organizational Structure
- Data Governance Council
- Data Owners
- Data Stewards
- Data Custodians

### Policies and Standards
- Data policies
- Data standards
- Procedures and guidelines
- Compliance requirements

### Processes
- Issue management
- Change management
- Compliance monitoring
- Metrics and reporting

## Key Activities

1. **Strategy Development**
   - Vision and business case
   - Roadmap creation
   - Success metrics

2. **Policy Management**
   - Policy definition
   - Communication
   - Enforcement

3. **Stewardship**
   - Data quality oversight
   - Issue resolution
   - Metadata management

4. **Compliance**
   - Regulatory adherence
   - Audit support
   - Risk management
""",
    "security_access": """# Data Security and Access Control

## NIST Cybersecurity Framework

### Core Functions

1. **Identify**
   - Asset management
   - Risk assessment
   - Governance

2. **Protect**
   - Access control
   - Data security
   - Protective technology

3. **Detect**
   - Anomaly detection
   - Security monitoring
   - Detection processes

4. **Respond**
   - Response planning
   - Communications
   - Analysis and mitigation

5. **Recover**
   - Recovery planning
   - Improvements
   - Communications

## ISO 27001 Controls

### Access Control (A.9)
- Access control policy
- User access management
- User responsibilities
- System and application access control

### Cryptography (A.10)
- Cryptographic controls
- Key management

### Physical Security (A.11)
- Secure areas
- Equipment security

### Operations Security (A.12)
- Operational procedures
- Protection from malware
- Backup
- Logging and monitoring

## Best Practices

- Principle of least privilege
- Multi-factor authentication
- Regular access reviews
- Encryption at rest and in transit
- Security monitoring and logging
- Incident response procedures
""",
    "metadata_documentation": """# Metadata and Documentation

## DAMA-DMBOK Metadata Management

### Metadata Types

1. **Business Metadata**
   - Business definitions
   - Business rules
   - Data ownership
   - Data lineage

2. **Technical Metadata**
   - Database schemas
   - Data models
   - Data types and formats
   - System specifications

3. **Operational Metadata**
   - Processing logs
   - Data quality metrics
   - Access statistics
   - Job schedules

## Metadata Standards

### Dublin Core
- Title, Creator, Subject
- Description, Publisher
- Contributor, Date, Type
- Format, Identifier, Source
- Language, Relation, Coverage, Rights

### ISO/IEC 11179
- Data element naming
- Definition standards
- Classification schemes
- Registration procedures

## Best Practices

1. **Centralized Repository**
   - Single source of truth
   - Accessible to all stakeholders
   - Version controlled

2. **Automated Capture**
   - Reduce manual effort
   - Improve accuracy
   - Real-time updates

3. **Business Glossary**
   - Standard terminology
   - Clear definitions
   - Usage examples

4. **Data Catalog**
   - Data discovery
   - Usage tracking
   - Quality metrics
   - Lineage visualization
""",
    "quality": """# Data Quality Management

## ISO 8000 Data Quality Dimensions

### Accuracy
- Data correctly represents reality
- Validation against authoritative sources
- Error detection and correction

### Completeness
- All required data present
- No missing values where needed
- Coverage of entire domain

### Consistency
- Data uniform across systems
- No contradictions
- Adherence to standards

### Timeliness
- Data available when needed
- Up-to-date information
- Appropriate refresh rates

### Validity
- Conformance to defined formats
- Business rule compliance
- Domain constraint adherence

### Uniqueness
- No unwanted duplicates
- Proper entity resolution
- Single source of truth

## Total Data Quality Management (TDQM)

### Define
- Quality requirements
- Measurement criteria
- Stakeholder needs

### Measure
- Quality metrics
- Profiling and assessment
- Issue identification

### Analyze
- Root cause analysis
- Impact assessment
- Trend analysis

### Improve
- Data cleansing
- Process improvements
- Preventive measures

## Best Practices

- Establish data quality KPIs
- Implement automated quality checks
- Regular data profiling
- Quality scorecards and dashboards
- Continuous improvement culture
- Data quality tools (Great Expectations, Deequ, etc.)
"""
}


def create_directory_structure():
    """Create the Knowledge directory structure"""
    logger.info("Creating Knowledge directory structure...")

    for dimension in KNOWLEDGE_SOURCES.keys():
        dim_path = KNOWLEDGE_BASE_DIR / dimension
        dim_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dim_path}")


def download_with_retry(url: str, max_retries: int = 3, timeout: int = 30) -> str:
    """
    Download content from URL with retry logic

    Args:
        url: URL to download from
        max_retries: Maximum number of retry attempts
        timeout: Timeout in seconds for each request

    Returns:
        Downloaded text content or None if failed
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading from {url} (attempt {attempt + 1}/{max_retries})...")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            # Try to decode as text
            content = response.text
            if len(content) > 100:  # Sanity check
                logger.info(f"Successfully downloaded {len(content)} characters")
                return content
            else:
                logger.warning(f"Downloaded content too short: {len(content)} characters")

        except requests.RequestException as e:
            logger.warning(f"Download attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

    return None


def save_document(content: str, filepath: Path):
    """Save document content to file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved document to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save document to {filepath}: {e}")


def download_knowledge_documents():
    """Download all knowledge documents"""
    logger.info("Starting knowledge document downloads...")

    stats = {
        'total': 0,
        'downloaded': 0,
        'fallback': 0,
        'failed': 0
    }

    for dimension, sources in KNOWLEDGE_SOURCES.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing dimension: {dimension}")
        logger.info(f"{'='*60}")

        dim_path = KNOWLEDGE_BASE_DIR / dimension

        for url, filename, description in sources:
            stats['total'] += 1
            logger.info(f"\n{description}")

            filepath = dim_path / filename

            # Try to download
            content = download_with_retry(url)

            if content:
                save_document(content, filepath)
                stats['downloaded'] += 1
            else:
                # Use fallback content if download failed
                logger.warning(f"Using fallback content for {dimension}")
                if dimension in FALLBACK_CONTENT:
                    save_document(FALLBACK_CONTENT[dimension], filepath)
                    stats['fallback'] += 1
                else:
                    logger.error(f"No fallback content available for {dimension}")
                    stats['failed'] += 1

    # Save fallback content for all dimensions
    logger.info(f"\n{'='*60}")
    logger.info("Saving fallback content for all dimensions")
    logger.info(f"{'='*60}")

    for dimension, content in FALLBACK_CONTENT.items():
        dim_path = KNOWLEDGE_BASE_DIR / dimension
        fallback_file = dim_path / f"{dimension}_fallback.txt"
        save_document(content, fallback_file)

    # Print statistics
    logger.info(f"\n{'='*60}")
    logger.info("Download Summary")
    logger.info(f"{'='*60}")
    logger.info(f"Total sources: {stats['total']}")
    logger.info(f"Successfully downloaded: {stats['downloaded']}")
    logger.info(f"Used fallback: {stats['fallback']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"\nKnowledge base location: {KNOWLEDGE_BASE_DIR}")


def main():
    """Main execution function"""
    logger.info("="*60)
    logger.info("Knowledge Base Setup for RAG Integration")
    logger.info("="*60)

    # Create directory structure
    create_directory_structure()

    # Download documents
    download_knowledge_documents()

    logger.info("\n" + "="*60)
    logger.info("Knowledge base setup complete!")
    logger.info("="*60)
    logger.info(f"Knowledge base location: {KNOWLEDGE_BASE_DIR.absolute()}")
    logger.info("\nNext steps:")
    logger.info("1. Review downloaded documents")
    logger.info("2. Run 'python -m app.rag' to ingest documents into vector store")
    logger.info("3. Restart the application to use RAG-enhanced analysis")


if __name__ == "__main__":
    main()
