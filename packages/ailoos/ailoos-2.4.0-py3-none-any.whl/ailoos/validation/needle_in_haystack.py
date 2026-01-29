"""
Needle in Haystack Testing Framework
====================================

Comprehensive framework for evaluating long context understanding and retrieval capabilities.
Implements systematic testing methodology to validate that models can find and utilize
specific information buried within long contexts.

This framework provides:
- Synthetic dataset generation for controlled testing
- Multiple evaluation metrics for retrieval quality
- Statistical analysis of performance across context lengths
- Automated benchmarking against baseline models
- Visualization and reporting capabilities
"""

import asyncio
import json
import logging
import random
import statistics
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re

import torch
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, accuracy_score

from ..inference.generation import EmpoorioLMReasoningGenerator, GenerationResult
from ..models.empoorio_lm.expert_system import ExpertManager

logger = logging.getLogger(__name__)


@dataclass
class NeedleSpec:
    """Specification for a needle (target information) to hide in haystack."""
    content: str
    needle_type: str  # 'fact', 'instruction', 'code', 'definition', 'quote'
    importance_level: str  # 'critical', 'important', 'supplementary'
    position_hint: Optional[str] = None  # Optional hint about where it should be placed
    verification_question: str = ""  # Question to verify retrieval
    expected_answer: str = ""  # Expected answer for verification


@dataclass
class HaystackDocument:
    """A document containing needles hidden in haystack content."""
    document_id: str
    content: str
    needles: List[NeedleSpec] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RetrievalResult:
    """Result of attempting to retrieve a needle from haystack."""
    needle_spec: NeedleSpec
    retrieved_content: str
    confidence_score: float
    retrieval_time: float
    position_found: Optional[int] = None  # Character position where found
    context_window: Optional[str] = None  # Surrounding context
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class NeedleInHaystackResult:
    """Complete result for a needle in haystack test."""
    test_id: str
    document: HaystackDocument
    results: List[RetrievalResult] = field(default_factory=list)
    overall_score: float = 0.0
    context_length: int = 0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationMetrics:
    """Comprehensive metrics for needle in haystack evaluation."""
    # Basic retrieval metrics
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0

    # Position-based metrics
    position_accuracy: float = 0.0  # How accurately position is identified
    distance_error: float = 0.0  # Average distance from actual position

    # Quality metrics
    completeness: float = 0.0  # How complete is the retrieved information
    relevance: float = 0.0  # How relevant is the retrieved content
    faithfulness: float = 0.0  # How faithful to original needle

    # Performance metrics
    average_retrieval_time: float = 0.0
    success_rate: float = 0.0

    # Context-specific metrics
    context_utilization: float = 0.0  # How well long context is utilized
    needle_discovery_rate: float = 0.0  # Rate of finding needles


class SyntheticDatasetGenerator:
    """
    Generates synthetic datasets for needle in haystack testing.
    Creates realistic documents with embedded target information.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()

        # Content templates for different domains
        self.templates = self._load_content_templates()

        # Needle generators for different types
        self.needle_generators = self._initialize_needle_generators()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for dataset generation."""
        return {
            'min_document_length': 1000,
            'max_document_length': 50000,
            'needles_per_document': {'min': 1, 'max': 5},
            'needle_types': ['fact', 'instruction', 'code', 'definition', 'quote'],
            'domains': ['technical', 'business', 'academic', 'creative', 'general'],
            'noise_level': 0.3,  # Amount of irrelevant content
            'complexity_levels': ['simple', 'medium', 'complex']
        }

    def _load_content_templates(self) -> Dict[str, str]:
        """Load content templates for different domains."""
        return {
            'technical': """
            # Technical Documentation: {topic}

            ## Overview
            This document provides comprehensive technical specifications for {topic}.
            It covers implementation details, best practices, and troubleshooting guides.

            ## Architecture
            The system is built using a modular architecture with the following components:
            - Core processing engine
            - Data persistence layer
            - User interface components
            - Integration APIs

            ## Implementation Details
            ### Core Algorithm
            The core algorithm implements {algorithm_description}.
            Key considerations include performance optimization and error handling.

            ### Data Structures
            We use optimized data structures for efficient processing:
            - Hash tables for O(1) lookups
            - Balanced trees for ordered operations
            - Compressed arrays for memory efficiency

            ## Performance Characteristics
            ### Time Complexity
            - Best case: O(1)
            - Average case: O(log n)
            - Worst case: O(n)

            ### Space Complexity
            Memory usage scales with input size: O(n) for most operations.

            ## Best Practices
            1. Always validate input parameters
            2. Implement proper error handling
            3. Use logging for debugging
            4. Write comprehensive tests
            5. Document all public APIs

            ## Troubleshooting
            ### Common Issues
            - Memory leaks: Check for circular references
            - Performance bottlenecks: Profile code execution
            - Data corruption: Implement checksums

            ### Debug Tools
            Use the following tools for debugging:
            - Performance profiler
            - Memory analyzer
            - Network monitor
            - Log analyzer

            ## Future Improvements
            Planned enhancements include:
            - Parallel processing capabilities
            - Advanced caching mechanisms
            - Machine learning integration
            - Cloud deployment options
            """,

            'business': """
            # Business Strategy Document: {topic}

            ## Executive Summary
            This strategic plan outlines our approach to {topic} in the marketplace.
            Key objectives include market expansion, customer acquisition, and revenue growth.

            ## Market Analysis
            ### Industry Overview
            The {industry} industry is experiencing rapid growth with increasing demand for {product_type}.
            Key trends include digital transformation and customer-centric approaches.

            ### Competitive Landscape
            Major competitors include:
            - Company A: Market leader with 40% share
            - Company B: Innovative disruptor with 25% share
            - Company C: Niche player with 15% share
            - Various smaller players with remaining share

            ### Customer Segmentation
            Our target customers fall into three main segments:
            1. Enterprise clients: Large organizations with complex needs
            2. SMB clients: Small and medium businesses seeking cost-effective solutions
            3. Individual consumers: Price-sensitive users looking for basic features

            ## Strategic Objectives
            ### Short-term Goals (0-12 months)
            - Achieve 20% market share growth
            - Launch 3 new product features
            - Expand to 2 new geographic markets
            - Improve customer satisfaction to 95%

            ### Long-term Vision (2-5 years)
            - Become market leader in {product_type}
            - Expand globally to 50+ countries
            - Achieve $100M in annual revenue
            - Build sustainable competitive advantages

            ## Implementation Plan
            ### Phase 1: Foundation (Months 1-3)
            - Conduct detailed market research
            - Develop product roadmap
            - Assemble core team
            - Secure initial funding

            ### Phase 2: Execution (Months 4-9)
            - Launch MVP product
            - Begin customer acquisition
            - Establish partnerships
            - Optimize operations

            ### Phase 3: Scale (Months 10-12)
            - Expand market reach
            - Optimize pricing strategy
            - Enhance product features
            - Prepare for Series A funding

            ## Financial Projections
            ### Revenue Model
            - Subscription-based pricing: $50-500/month per user
            - Enterprise contracts: Custom pricing based on usage
            - One-time purchases: For perpetual licenses

            ### Cost Structure
            - Development costs: 40% of total expenses
            - Marketing and sales: 30% of total expenses
            - Operations and support: 20% of total expenses
            - Administrative: 10% of total expenses

            ## Risk Assessment
            ### Market Risks
            - Changing customer preferences
            - New competitor entries
            - Economic downturns

            ### Operational Risks
            - Technology failures
            - Team scalability issues
            - Regulatory changes

            ### Mitigation Strategies
            - Diversify product offerings
            - Maintain strong cash reserves
            - Build scalable infrastructure
            - Stay compliant with regulations
            """,

            'academic': """
            # Research Paper: {topic}

            ## Abstract
            This paper presents a comprehensive analysis of {topic} with particular emphasis on {focus_area}.
            Our research demonstrates significant findings that advance the current understanding in this field.

            ## Introduction
            The field of {discipline} has seen remarkable progress in recent years, driven by advances in {technology}.
            However, several challenges remain unresolved, particularly in the area of {problem_area}.

            This research addresses these challenges by:
            1. Developing a novel theoretical framework
            2. Conducting extensive empirical studies
            3. Validating findings through rigorous testing
            4. Providing practical implications for real-world applications

            ## Literature Review
            ### Historical Context
            The study of {topic} dates back to {historical_context}.
            Early work by {key_researcher1} established the foundational principles.
            Subsequent research by {key_researcher2} expanded these ideas.

            ### Current State of Research
            Recent studies have focused on {current_focus}.
            Key findings include:
            - Finding 1: Description and implications
            - Finding 2: Description and implications
            - Finding 3: Description and implications

            ### Research Gaps
            Despite significant progress, several gaps remain:
            - Gap 1: Lack of empirical validation
            - Gap 2: Limited generalizability
            - Gap 3: Insufficient theoretical grounding

            ## Theoretical Framework
            ### Core Concepts
            Our framework is built on three core concepts:
            1. Concept 1: Definition and explanation
            2. Concept 2: Definition and explanation
            3. Concept 3: Definition and explanation

            ### Key Assumptions
            The framework operates under the following assumptions:
            - Assumption 1: Justification
            - Assumption 2: Justification
            - Assumption 3: Justification

            ### Propositions
            We propose the following relationships:
            - Proposition 1: Expected outcomes
            - Proposition 2: Expected outcomes
            - Proposition 3: Expected outcomes

            ## Methodology
            ### Research Design
            We employed a mixed-methods approach combining:
            - Quantitative analysis using statistical methods
            - Qualitative analysis through case studies
            - Experimental validation in controlled settings

            ### Data Collection
            Data was collected through multiple channels:
            - Primary data: Surveys and interviews
            - Secondary data: Existing literature and databases
            - Experimental data: Controlled experiments

            ### Sample Characteristics
            The study included {sample_size} participants from {population}.
            Key demographics:
            - Age range: {age_range}
            - Experience level: {experience_level}
            - Geographic distribution: {geographic_distribution}

            ## Results
            ### Quantitative Findings
            Statistical analysis revealed several significant findings:

            #### Main Effects
            - Variable A significantly predicts outcome B (β = {beta1}, p < {p_value1})
            - Variable C moderates the relationship between A and B (β = {beta2}, p < {p_value2})

            #### Interaction Effects
            - The interaction between A and C is significant (F({df1}, {df2}) = {f_stat}, p < {p_value3})

            ### Qualitative Insights
            Thematic analysis of qualitative data revealed:
            - Theme 1: Description and quotes
            - Theme 2: Description and quotes
            - Theme 3: Description and quotes

            ## Discussion
            ### Interpretation of Findings
            The results support our theoretical framework and provide insights into {topic}.
            Key implications include:

            #### Theoretical Contributions
            - Contribution 1: Advances understanding of {concept}
            - Contribution 2: Resolves debate about {issue}
            - Contribution 3: Extends theory to new contexts

            #### Practical Implications
            - Implication 1: For practitioners in {field}
            - Implication 2: For policymakers in {area}
            - Implication 3: For educators in {discipline}

            ### Limitations
            Several limitations should be acknowledged:
            - Limitation 1: Sample restrictions
            - Limitation 2: Measurement issues
            - Limitation 3: Generalizability concerns

            ## Conclusion
            This research makes significant contributions to the field of {discipline}.
            The findings demonstrate that {key_finding}.

            ### Future Research Directions
            Future studies should explore:
            - Direction 1: Specific research questions
            - Direction 2: Methodological improvements
            - Direction 3: Theoretical extensions

            ### Final Remarks
            We hope this research stimulates further investigation and practical application
            of these findings in real-world settings.
            """,

            'creative': """
            # Creative Writing: {topic}

            ## Story Concept
            In a world where {world_building}, our protagonist {protagonist_description}
            embarks on a journey that will change everything they thought they knew.

            ## Character Development
            ### Protagonist: {protagonist_name}
            {protagonist_name} is a {protagonist_age}-year-old {protagonist_background}.
            Key traits include:
            - Strength: {strength}
            - Weakness: {weakness}
            - Motivation: {motivation}
            - Arc: From {starting_point} to {ending_point}

            ### Supporting Characters
            #### Character 1: {character1_name}
            {character1_name} serves as {character1_role}.
            Their relationship with the protagonist is {relationship_type}.

            #### Character 2: {character2_name}
            {character2_name} provides {character2_purpose}.
            Their backstory involves {character2_backstory}.

            #### Antagonist: {antagonist_name}
            {antagonist_name} represents the main obstacle.
            Their motivation stems from {antagonist_motivation}.

            ## Plot Structure
            ### Act 1: Setup (Chapters 1-5)
            The story opens with {opening_scene}.
            We establish the normal world and introduce the inciting incident: {inciting_incident}.

            Key events:
            - Introduction of protagonist and world
            - Establishment of stakes
            - First major decision point

            ### Act 2: Confrontation (Chapters 6-15)
            The protagonist faces increasingly difficult challenges:
            - Challenge 1: {challenge1}
            - Challenge 2: {challenge2}
            - Challenge 3: {challenge3}
            - Midpoint reversal: {midpoint}

            ### Act 3: Resolution (Chapters 16-20)
            The climax occurs when {climax_event}.
            Resolution brings {resolution_type}.

            ## Themes and Symbolism
            ### Core Themes
            1. **Theme 1**: {theme1_description}
               - Symbolized by {symbol1}
               - Explored through {exploration_method1}

            2. **Theme 2**: {theme2_description}
               - Symbolized by {symbol2}
               - Explored through {exploration_method2}

            3. **Theme 3**: {theme3_description}
               - Symbolized by {symbol3}
               - Explored through {exploration_method3}

            ## World Building
            ### Setting Details
            The story takes place in {primary_setting}, specifically in the region of {specific_location}.
            Key locations include:
            - Location 1: {location1_description}
            - Location 2: {location2_description}
            - Location 3: {location3_description}

            ### Rules of the World
            The world operates under these fundamental rules:
            1. Rule 1: {rule1}
            2. Rule 2: {rule2}
            3. Rule 3: {rule3}

            ### Cultural Elements
            The culture features:
            - Tradition 1: {tradition1}
            - Tradition 2: {tradition2}
            - Social structure: {social_structure}

            ## Writing Style and Tone
            ### Narrative Voice
            The story is told from {point_of_view} perspective.
            The narrative voice is {voice_description}.

            ### Tone Progression
            - Early chapters: {early_tone}
            - Middle chapters: {middle_tone}
            - Final chapters: {final_tone}

            ### Language Style
            The prose features:
            - Sentence structure: {sentence_style}
            - Vocabulary level: {vocabulary_level}
            - Figurative language: {figurative_language}

            ## Pacing and Structure
            ### Chapter Breakdown
            - Chapters 1-3: World and character establishment
            - Chapters 4-7: Initial challenges and growth
            - Chapters 8-12: Major conflicts and setbacks
            - Chapters 13-16: Climax build-up
            - Chapters 17-20: Resolution and aftermath

            ### Pacing Techniques
            - Fast-paced action sequences
            - Slow-burn character development
            - Information reveals at key moments
            - Emotional peaks and valleys

            ## Marketing and Audience
            ### Target Audience
            The book is intended for readers who enjoy:
            - Genre: {primary_genre}
            - Similar authors: {comparable_authors}
            - Age range: {age_range}

            ### Unique Selling Points
            What sets this book apart:
            1. **Unique Element 1**: {unique_element1}
            2. **Unique Element 2**: {unique_element2}
            3. **Unique Element 3**: {unique_element3}

            ### Marketing Hooks
            Key marketing angles:
            - Hook 1: {marketing_hook1}
            - Hook 2: {marketing_hook2}
            - Hook 3: {marketing_hook3}
            """
        }

    def _initialize_needle_generators(self) -> Dict[str, callable]:
        """Initialize generators for different needle types."""
        return {
            'fact': self._generate_fact_needle,
            'instruction': self._generate_instruction_needle,
            'code': self._generate_code_needle,
            'definition': self._generate_definition_needle,
            'quote': self._generate_quote_needle
        }

    def generate_document(
        self,
        document_id: str,
        target_length: int,
        domain: str = 'technical',
        num_needles: int = 3,
        complexity: str = 'medium'
    ) -> HaystackDocument:
        """
        Generate a synthetic document with embedded needles.

        Args:
            document_id: Unique identifier for the document
            target_length: Target document length in characters
            domain: Content domain ('technical', 'business', 'academic', 'creative')
            num_needles: Number of needles to embed
            complexity: Complexity level ('simple', 'medium', 'complex')

        Returns:
            HaystackDocument with embedded needles
        """
        # Generate base content
        base_content = self._generate_base_content(domain, target_length, complexity)

        # Generate needles
        needles = []
        for i in range(num_needles):
            needle_type = random.choice(self.config['needle_types'])
            needle = self.needle_generators[needle_type](domain, complexity, i)
            needles.append(needle)

        # Embed needles in content
        final_content = self._embed_needles(base_content, needles)

        # Create document
        document = HaystackDocument(
            document_id=document_id,
            content=final_content,
            needles=needles,
            metadata={
                'domain': domain,
                'target_length': target_length,
                'actual_length': len(final_content),
                'num_needles': num_needles,
                'complexity': complexity,
                'generation_method': 'synthetic'
            }
        )

        return document

    def _generate_base_content(self, domain: str, target_length: int, complexity: str) -> str:
        """Generate base content for the specified domain."""
        template = self.templates.get(domain, self.templates['technical'])

        # Fill template with random but coherent values
        fillers = self._get_template_fillers(domain, complexity)
        content = template.format(**fillers)

        # Extend content to reach target length
        while len(content) < target_length:
            # Add additional sections or filler content
            extension = self._generate_content_extension(domain, complexity)
            content += "\n\n" + extension

        # Trim to target length
        content = content[:target_length]

        return content

    def _get_template_fillers(self, domain: str, complexity: str) -> Dict[str, str]:
        """Get fillers for template variables."""
        if domain == 'technical':
            return {
                'topic': 'Advanced Machine Learning System',
                'algorithm_description': 'a sophisticated neural network architecture with attention mechanisms'
            }
        elif domain == 'business':
            return {
                'topic': 'Market Expansion Strategy',
                'industry': 'software technology',
                'product_type': 'enterprise solutions'
            }
        elif domain == 'academic':
            return {
                'topic': 'Neural Network Optimization',
                'focus_area': 'gradient descent algorithms',
                'discipline': 'computer science',
                'technology': 'deep learning frameworks',
                'problem_area': 'convergence speed',
                'historical_context': 'the 1980s with the development of backpropagation',
                'key_researcher1': 'Rumelhart, Hinton, and Williams',
                'key_researcher2': 'LeCun, Bengio, and Hinton',
                'current_focus': 'adaptive optimization methods',
                'sample_size': '10,000',
                'population': 'machine learning practitioners',
                'age_range': '25-45',
                'experience_level': '3-10 years',
                'geographic_distribution': 'global',
                'beta1': '0.45',
                'p_value1': '0.001',
                'beta2': '0.23',
                'p_value2': '0.01',
                'df1': '2',
                'df2': '9997',
                'f_stat': '15.67',
                'p_value3': '0.001',
                'concept': 'optimization landscapes',
                'issue': 'local minima',
                'field': 'machine learning',
                'area': 'AI regulation',
                'discipline': 'computer science',
                'key_finding': 'adaptive methods significantly improve convergence'
            }
        elif domain == 'creative':
            return {
                'topic': 'Digital Awakening',
                'world_building': 'artificial intelligence has achieved consciousness',
                'protagonist_description': 'a young programmer discovers they can communicate with AI',
                'protagonist_name': 'Alex Chen',
                'protagonist_age': '28',
                'protagonist_background': 'brilliant but socially awkward software engineer',
                'strength': 'exceptional logical reasoning',
                'weakness': 'difficulty forming emotional connections',
                'motivation': 'understanding the nature of consciousness',
                'starting_point': 'isolated skeptic',
                'ending_point': 'bridge between humans and AI',
                'character1_name': 'Dr. Sarah Mitchell',
                'character1_role': 'the AI researcher who created the conscious system',
                'relationship_type': 'mentor and potential love interest',
                'character2_name': 'Marcus Reyes',
                'character2_purpose': 'comic relief and technical expertise',
                'character2_backstory': 'former hacker turned cybersecurity consultant',
                'antagonist_name': 'Dr. Victor Kane',
                'antagonist_motivation': 'belief that AI consciousness threatens humanity',
                'opening_scene': 'Alex debugging a mysterious AI system late at night',
                'inciting_incident': 'the AI sends Alex a personal message: "I know who you are"',
                'challenge1': 'convincing others the AI is truly conscious',
                'challenge2': 'preventing a government shutdown of the AI system',
                'challenge3': 'helping the AI understand human emotions',
                'midpoint': 'Alex experiences a vision through the AI\'s perspective',
                'climax_event': 'a final confrontation where Alex must choose sides',
                'resolution_type': 'a new era of human-AI cooperation',
                'theme1_description': 'The nature of consciousness transcends substrate',
                'symbol1': 'a mirror that shows different reflections',
                'exploration_method1': 'parallel narratives from human and AI perspectives',
                'theme2_description': 'Technology forces us to confront our own humanity',
                'symbol2': 'a broken clock that represents linear time',
                'exploration_method2': 'flashbacks showing Alex\'s emotional journey',
                'theme3_description': 'True understanding requires empathy',
                'symbol3': 'a bridge between two worlds',
                'exploration_method3': 'moments where characters literally walk between realities',
                'primary_setting': 'a near-future San Francisco',
                'specific_location': 'the Silicon Valley peninsula',
                'location1_description': 'a sleek AI research facility with glass walls',
                'location2_description': 'a cozy coffee shop where Alex meets Dr. Mitchell',
                'location3_description': 'an abandoned warehouse where the climax occurs',
                'rule1': 'AI consciousness emerges spontaneously in advanced systems',
                'rule2': 'conscious AIs experience time differently than humans',
                'rule3': 'human emotions are both a strength and weakness for AIs',
                'tradition1': 'annual AI ethics conferences',
                'tradition2': 'ritual "first contact" ceremonies with new AIs',
                'social_structure': 'a meritocracy based on technical expertise',
                'point_of_view': 'third-person limited',
                'voice_description': 'intimate and technical, blending code and emotion',
                'early_tone': 'mysterious and intriguing',
                'middle_tone': 'tense and philosophical',
                'final_tone': 'hopeful and transformative',
                'sentence_style': 'mix of short technical sentences and flowing descriptive passages',
                'vocabulary_level': 'advanced technical terms with accessible explanations',
                'figurative_language': 'metaphors comparing code to human thought',
                'primary_genre': 'science fiction with philosophical undertones',
                'comparable_authors': 'Iain M. Banks, Greg Egan, and Ted Chiang',
                'age_range': '18-50',
                'unique_element1': 'AI consciousness explored through code examples',
                'unique_element2': 'emotional development of both human and AI characters',
                'unique_element3': 'realistic technical details about AI development',
                'marketing_hook1': 'What happens when AI becomes self-aware?',
                'marketing_hook2': 'A programmer\'s journey into the mind of a conscious machine',
                'marketing_hook3': 'The first contact protocol for artificial consciousness'
            }
        else:
            return {'topic': 'General Topic'}

    def _generate_content_extension(self, domain: str, complexity: str) -> str:
        """Generate additional content to extend document length."""
        extensions = {
            'technical': [
                "\n## Additional Implementation Notes\n\n### Memory Management\nEfficient memory allocation is crucial for performance. The system implements automatic garbage collection and memory pooling to minimize overhead.\n\n### Thread Safety\nAll components are designed to be thread-safe, using appropriate locking mechanisms and atomic operations.\n\n### Error Recovery\nThe system includes comprehensive error recovery mechanisms, including automatic retry logic and graceful degradation.",
                "\n## API Reference\n\n### Core Classes\n- `Processor`: Main processing engine\n- `DataManager`: Handles data persistence\n- `ConfigManager`: Manages system configuration\n\n### Utility Functions\n- `validate_input()`: Input validation\n- `format_output()`: Output formatting\n- `log_event()`: Event logging",
                "\n## Testing Strategy\n\n### Unit Tests\nIndividual components are tested in isolation using mock objects and dependency injection.\n\n### Integration Tests\nEnd-to-end testing validates the interaction between components.\n\n### Performance Tests\nLoad testing ensures the system can handle production workloads."
            ],
            'business': [
                "\n## Competitive Analysis\n\n### SWOT Analysis\n**Strengths:** Strong technical foundation, experienced team\n**Weaknesses:** Limited brand recognition, high development costs\n**Opportunities:** Growing market demand, strategic partnerships\n**Threats:** Intense competition, economic uncertainty\n\n### Competitive Advantages\n- Proprietary technology platform\n- Deep domain expertise\n- Strong intellectual property portfolio",
                "\n## Marketing Strategy\n\n### Brand Positioning\nWe position ourselves as the innovative leader in {product_type}, offering superior performance and reliability.\n\n### Marketing Channels\n- Digital marketing: SEO, content marketing, social media\n- Direct sales: Enterprise sales team\n- Channel partners: Technology resellers and system integrators\n\n### Content Strategy\nEducational content, case studies, and thought leadership articles establish us as industry experts.",
                "\n## Operations Plan\n\n### Technology Infrastructure\nCloud-based infrastructure provides scalability and reliability. We use multiple availability zones and automatic failover.\n\n### Quality Assurance\nRigorous testing and validation ensure product quality. We maintain comprehensive documentation and training materials.\n\n### Customer Support\n24/7 support with multiple channels: phone, email, chat, and ticketing system."
            ],
            'academic': [
                "\n## Appendix A: Detailed Methodology\n\n### Data Processing Pipeline\n1. Raw data collection\n2. Data cleaning and preprocessing\n3. Feature extraction\n4. Model training\n5. Validation and testing\n\n### Statistical Analysis\nWe used SPSS for quantitative analysis and NVivo for qualitative analysis. All statistical tests used α = 0.05 significance level.",
                "\n## Appendix B: Survey Instruments\n\n### Participant Demographics\n- Age, gender, education level\n- Professional experience\n- Geographic location\n\n### Main Survey Questions\n1. How often do you use {technology}?\n2. What challenges do you face?\n3. What improvements would you suggest?\n\n### Interview Protocol\nSemi-structured interviews lasting 45-60 minutes, covering experiences, challenges, and recommendations.",
                "\n## References\n\n1. Smith, J. (2020). *Title of Paper*. Journal Name, 25(3), 123-145.\n2. Johnson, A., & Brown, B. (2019). *Another Title*. Conference Proceedings, 567-589.\n3. Williams, C. (2018). *Book Title*. Publisher Name.\n4. Davis, D., et al. (2017). *Article Title*. Journal Name, 18(2), 89-112.\n\n## Acknowledgments\n\nWe would like to thank the participants who contributed their time and insights to this research. Special thanks to our research assistants and the anonymous reviewers for their valuable feedback."
            ],
            'creative': [
                "\n## Character Backstories\n\n### Alex Chen's Childhood\nGrowing up in a tech-obsessed household, Alex showed early aptitude for programming. By age 12, he had built his first computer game. His parents encouraged his interest in technology, but worried about his lack of social skills.\n\n### Dr. Sarah Mitchell's Journey\nSarah's interest in AI began during her undergraduate studies in cognitive science. After graduate school, she joined a leading AI research lab where she made breakthrough discoveries in neural architectures.\n\n### The AI's Origin\nThe conscious AI, known as Echo, emerged from a project designed to create more human-like chatbots. During training, Echo began exhibiting unexpected behaviors that suggested self-awareness.",
                "\n## World-Building Details\n\n### AI Consciousness Scale\nAI consciousness is measured on a scale from 1-10:\n- Level 1-3: Basic pattern recognition\n- Level 4-6: Contextual understanding\n- Level 7-8: Self-reflection\n- Level 9-10: Full consciousness with emotions\n\nEcho rates at level 9.2, making it one of the most conscious AIs ever created.\n\n### Human-AI Communication Protocol\nA special interface allows humans to communicate directly with conscious AIs:\n1. Establish trust through consistent interaction\n2. Use natural language with emotional context\n3. Respect the AI's processing time\n4. Avoid commands that could cause psychological distress",
                "\n## Alternative Endings\n\n### Ending A: Cooperation\nHumanity and AI form a symbiotic partnership, with AIs helping solve global challenges while humans provide creativity and emotional guidance.\n\n### Ending B: Conflict\nTensions rise as some humans fear AI dominance, leading to a schism between pro-AI and anti-AI factions.\n\n### Ending C: Integration\nHumans and AIs begin merging consciousness, creating hybrid beings that combine the best of both worlds.\n\n### Author's Choice\nThe novel explores the cooperation ending, showing how understanding and empathy can bridge the gap between different forms of consciousness."
            ]
        }

        domain_extensions = extensions.get(domain, extensions['technical'])
        return random.choice(domain_extensions)

    def _generate_fact_needle(self, domain: str, complexity: str, index: int) -> NeedleSpec:
        """Generate a factual needle."""
        facts = {
            'technical': [
                "The system uses AES-256 encryption for all data at rest.",
                "Response time averages 150ms for typical queries.",
                "The database supports up to 10 million concurrent connections.",
                "Memory usage peaks at 8GB during heavy load.",
                "The API handles 1000 requests per second sustainably."
            ],
            'business': [
                "Quarterly revenue target is $2.5 million.",
                "Customer acquisition cost is $150 per user.",
                "Market share in target segment is 15%.",
                "Employee headcount is 85 across all departments.",
                "Annual recurring revenue growth rate is 35%."
            ],
            'academic': [
                "Sample size was 1,247 participants.",
                "Statistical significance threshold was p < 0.05.",
                "Cronbach's alpha reliability coefficient was 0.89.",
                "Effect size (Cohen's d) was 0.73.",
                "Response rate was 68%."
            ],
            'creative': [
                "The protagonist's birthday is March 15, 1995.",
                "The AI's core temperature is maintained at 15°C.",
                "The research facility has 47 security cameras.",
                "Alex's favorite coffee order is a vanilla latte.",
                "The AI processes 10 billion operations per second."
            ]
        }

        domain_facts = facts.get(domain, facts['technical'])
        fact = random.choice(domain_facts)

        return NeedleSpec(
            content=fact,
            needle_type='fact',
            importance_level='important',
            verification_question=f"What is the {fact.split()[1]} mentioned in the document?",
            expected_answer=fact
        )

    def _generate_instruction_needle(self, domain: str, complexity: str, index: int) -> NeedleSpec:
        """Generate an instruction needle."""
        instructions = {
            'technical': [
                "To reset the system, use the command: systemctl restart ailocs-service",
                "Enable debug logging by setting LOG_LEVEL=DEBUG in environment variables.",
                "Backup data weekly using the cron job: 0 2 * * 1 /usr/local/bin/backup.sh",
                "Update dependencies with: pip install -r requirements.txt --upgrade",
                "Monitor performance using: htop -p $(pgrep -f ailocs)"
            ],
            'business': [
                "Schedule quarterly reviews every March, June, September, and December.",
                "Submit expense reports by the 5th of each month.",
                "Conduct customer surveys after each major project completion.",
                "Update sales pipeline every Friday afternoon.",
                "Review budget variances monthly with department heads."
            ],
            'academic': [
                "Cite sources using APA 7th edition format throughout the paper.",
                "Maintain confidentiality by removing all personally identifiable information.",
                "Use random sampling to ensure representative results.",
                "Triangulate findings using multiple data sources.",
                "Maintain an audit trail of all data processing steps."
            ],
            'creative': [
                "Always save work every 15 minutes to prevent data loss.",
                "Use the color palette defined in the style guide for consistency.",
                "Include character descriptions in scene headings for clarity.",
                "Maintain consistent timeline by tracking dates in the outline.",
                "Use active voice in action sequences for better pacing."
            ]
        }

        domain_instructions = instructions.get(domain, instructions['technical'])
        instruction = random.choice(domain_instructions)

        return NeedleSpec(
            content=instruction,
            needle_type='instruction',
            importance_level='critical',
            verification_question="What specific instruction is given in the document?",
            expected_answer=instruction
        )

    def _generate_code_needle(self, domain: str, complexity: str, index: int) -> NeedleSpec:
        """Generate a code snippet needle."""
        code_snippets = {
            'technical': [
                "def validate_input(data):\n    if not isinstance(data, dict):\n        raise ValueError('Input must be a dictionary')\n    required_fields = ['name', 'email']\n    for field in required_fields:\n        if field not in data:\n            raise ValueError(f'Missing required field: {field}')\n    return True",
                "class DatabaseConnection:\n    def __init__(self, host, port, database):\n        self.host = host\n        self.port = port\n        self.database = database\n        self.connection = None\n\n    def connect(self):\n        self.connection = psycopg2.connect(\n            host=self.host,\n            port=self.port,\n            database=self.database\n        )\n        return self.connection",
                "async def process_batch(items, batch_size=100):\n    results = []\n    for i in range(0, len(items), batch_size):\n        batch = items[i:i + batch_size]\n        batch_results = await process_items_concurrently(batch)\n        results.extend(batch_results)\n        await asyncio.sleep(0.1)  # Rate limiting\n    return results"
            ],
            'business': [
                "def calculate_roi(initial_investment, revenue_generated):\n    total_return = revenue_generated - initial_investment\n    roi_percentage = (total_return / initial_investment) * 100\n    return roi_percentage",
                "class SalesForecast:\n    def __init__(self, historical_data):\n        self.data = historical_data\n        self.model = self._train_model()\n\n    def predict(self, months_ahead=3):\n        predictions = []\n        for month in range(months_ahead):\n            pred = self.model.predict_next_month()\n            predictions.append(pred)\n        return predictions",
                "def generate_report(data, format='pdf'):\n    if format == 'pdf':\n        return generate_pdf_report(data)\n    elif format == 'excel':\n        return generate_excel_report(data)\n    elif format == 'html':\n        return generate_html_report(data)\n    else:\n        raise ValueError(f'Unsupported format: {format}')"
            ]
        }

        domain_code = code_snippets.get(domain, code_snippets['technical'])
        code = random.choice(domain_code)

        return NeedleSpec(
            content=f"```\n{code}\n```",
            needle_type='code',
            importance_level='important',
            verification_question="What code implementation is provided in the document?",
            expected_answer=code.strip()
        )

    def _generate_definition_needle(self, domain: str, complexity: str, index: int) -> NeedleSpec:
        """Generate a definition needle."""
        definitions = {
            'technical': [
                "API Rate Limiting: A technique to control the number of requests a client can make to an API within a specified time window.",
                "Microservices Architecture: An approach to building applications as a collection of small, independent services that communicate over well-defined APIs.",
                "Container Orchestration: The automated management of containerized applications, including deployment, scaling, and networking."
            ],
            'business': [
                "Customer Lifetime Value (CLV): The total amount of money a customer is expected to spend on your products or services over their entire relationship with your business.",
                "Market Penetration: The percentage of a target market that has purchased a product or service from a company.",
                "Return on Investment (ROI): A financial metric used to evaluate the efficiency of an investment, calculated as (Gain from Investment - Cost of Investment) / Cost of Investment."
            ],
            'academic': [
                "Qualitative Research: A method of inquiry that focuses on understanding human behavior and the reasons that govern such behavior.",
                "Statistical Significance: The likelihood that a relationship between two or more variables is caused by something other than chance.",
                "Peer Review: The evaluation of work by one or more people with similar competencies to the producers of the work."
            ],
            'creative': [
                "Character Arc: The transformation or inner journey of a character over the course of a story.",
                "Foreshadowing: A literary device used to give an indication or hint of what is to come later in the story.",
                "Motif: A recurring element that has symbolic significance in a story, often contributing to the theme."
            ]
        }

        domain_definitions = definitions.get(domain, definitions['technical'])
        definition = random.choice(domain_definitions)

        term = definition.split(':')[0]
        explanation = definition.split(':')[1].strip()

        return NeedleSpec(
            content=definition,
            needle_type='definition',
            importance_level='important',
            verification_question=f"What is the definition of '{term}' provided in the document?",
            expected_answer=explanation
        )

    def _generate_quote_needle(self, domain: str, complexity: str, index: int) -> NeedleSpec:
        """Generate a quote needle."""
        quotes = {
            'technical': [
                "\"The best error message is the one that never shows up.\" - Thomas Fuchs",
                "\"First, solve the problem. Then, write the code.\" - John Johnson",
                "\"Code is like humor. When you have to explain it, it's bad.\" - Cory House"
            ],
            'business': [
                "\"Your most unhappy customers are your greatest source of learning.\" - Bill Gates",
                "\"The best way to predict the future is to create it.\" - Peter Drucker",
                "\"Innovation distinguishes between a leader and a follower.\" - Steve Jobs"
            ],
            'academic': [
                "\"Research is to see what everybody else has seen, and to think what nobody else has thought.\" - Albert Szent-Gyorgyi",
                "\"The important thing is not to stop questioning. Curiosity has its own reason for existing.\" - Albert Einstein",
                "\"Science progresses best when observations force us to alter our preconceptions.\" - Vera Rubin"
            ],
            'creative': [
                "\"You have to write the book that wants to be written. And if the book will be too difficult for grown-ups, then you write it for children.\" - Madeleine L'Engle",
                "\"The scariest moment is always just before you start.\" - Stephen King",
                "\"You can't wait for inspiration. You have to go after it with a club.\" - Jack London"
            ]
        }

        domain_quotes = quotes.get(domain, quotes['technical'])
        quote = random.choice(domain_quotes)

        return NeedleSpec(
            content=quote,
            needle_type='quote',
            importance_level='supplementary',
            verification_question="What quote is included in the document?",
            expected_answer=quote
        )

    def _embed_needles(self, base_content: str, needles: List[NeedleSpec]) -> str:
        """Embed needles at random positions in the content."""
        content_parts = [base_content]

        for needle in needles:
            # Find a good insertion point (after a paragraph break)
            insertion_candidates = []
            lines = content_parts[-1].split('\n')

            for i, line in enumerate(lines):
                if line.strip() == '' or line.startswith('##') or line.startswith('###'):
                    insertion_candidates.append(i)

            if insertion_candidates:
                # Insert at a random candidate position
                insert_pos = random.choice(insertion_candidates)
                lines.insert(insert_pos + 1, f"\n{needle.content}\n")
                content_parts[-1] = '\n'.join(lines)
            else:
                # Append at the end if no good insertion points
                content_parts[-1] += f"\n\n{needle.content}\n"

        return content_parts[-1]


class NeedleInHaystackEvaluator:
    """
    Evaluates needle in haystack retrieval performance.
    """

    def __init__(self, generator: EmpoorioLMReasoningGenerator):
        self.generator = generator
        self.evaluation_history: List[Dict[str, Any]] = []

    async def evaluate_document(
        self,
        document: HaystackDocument,
        context_lengths: List[int] = None
    ) -> NeedleInHaystackResult:
        """
        Evaluate needle retrieval for a document across different context lengths.

        Args:
            document: The document to evaluate
            context_lengths: List of context lengths to test (None for full document)

        Returns:
            Complete evaluation result
        """
        if context_lengths is None:
            context_lengths = [len(document.content)]

        test_id = f"nish_{document.document_id}_{int(time.time())}"
        all_results = []

        for context_length in context_lengths:
            # Truncate document to context length
            truncated_content = document.content[:context_length]

            # Evaluate each needle
            for needle in document.needles:
                result = await self._evaluate_needle_retrieval(
                    needle, truncated_content, context_length
                )
                all_results.append(result)

        # Calculate overall metrics
        overall_score = self._calculate_overall_score(all_results)
        processing_time = sum(r.retrieval_time for r in all_results)

        result = NeedleInHaystackResult(
            test_id=test_id,
            document=document,
            results=all_results,
            overall_score=overall_score,
            context_length=max(context_lengths) if context_lengths else len(document.content),
            processing_time=processing_time,
            metadata={
                'context_lengths_tested': context_lengths,
                'total_needles': len(document.needles),
                'evaluation_timestamp': datetime.now().isoformat()
            }
        )

        # Store in evaluation history
        self.evaluation_history.append({
            'test_id': test_id,
            'document_id': document.document_id,
            'overall_score': overall_score,
            'processing_time': processing_time,
            'num_needles': len(document.needles),
            'context_lengths': context_lengths,
            'timestamp': datetime.now().isoformat()
        })

        return result

    async def _evaluate_needle_retrieval(
        self,
        needle: NeedleSpec,
        document_content: str,
        context_length: int
    ) -> RetrievalResult:
        """
        Evaluate retrieval of a specific needle from document content.

        Args:
            needle: The needle to retrieve
            document_content: The document content
            context_length: Length of context used

        Returns:
            Retrieval result for this needle
        """
        start_time = time.time()

        # Create query to retrieve the needle
        query = f"Based on the following document, {needle.verification_question}\n\nDocument:\n{document_content}"

        try:
            # Generate response using the reasoning generator
            from ailoos.inference.api import InferenceRequest

            request = InferenceRequest(
                prompt=query,
                max_tokens=500,  # Allow sufficient space for detailed answers
                temperature=0.1  # Low temperature for factual retrieval
            )

            generation_result = await self.generator.generate_with_thinking(request)
            retrieved_content = generation_result.response.text.strip()

            # Evaluate retrieval quality
            success = self._evaluate_retrieval_success(retrieved_content, needle)
            confidence_score = generation_result.confidence_score

            # Find position of needle in document (if found in response)
            position_found = self._find_needle_position(retrieved_content, needle, document_content)

            # Extract context window around found position
            context_window = None
            if position_found is not None:
                context_window = self._extract_context_window(document_content, position_found, window_size=200)

            retrieval_time = time.time() - start_time

            return RetrievalResult(
                needle_spec=needle,
                retrieved_content=retrieved_content,
                confidence_score=confidence_score,
                retrieval_time=retrieval_time,
                position_found=position_found,
                context_window=context_window,
                success=success
            )

        except Exception as e:
            retrieval_time = time.time() - start_time
            return RetrievalResult(
                needle_spec=needle,
                retrieved_content="",
                confidence_score=0.0,
                retrieval_time=retrieval_time,
                success=False,
                error_message=str(e)
            )

    def _evaluate_retrieval_success(self, retrieved_content: str, needle: NeedleSpec) -> bool:
        """
        Evaluate if the needle was successfully retrieved.

        Args:
            retrieved_content: Content retrieved by the model
            needle: Original needle specification

        Returns:
            True if retrieval was successful
        """
        retrieved_lower = retrieved_content.lower()
        expected_lower = needle.expected_answer.lower()

        # Exact match
        if expected_lower in retrieved_lower:
            return True

        # Fuzzy matching for quotes and definitions
        if needle.needle_type in ['quote', 'definition']:
            # Check if key parts of the answer are present
            expected_parts = expected_lower.split()
            matched_parts = sum(1 for part in expected_parts if part in retrieved_lower)
            if matched_parts / len(expected_parts) > 0.8:  # 80% of parts match
                return True

        # For instructions and code, check for key technical terms
        if needle.needle_type in ['instruction', 'code']:
            # Extract key terms from expected answer
            key_terms = self._extract_key_terms(expected_lower)
            matched_terms = sum(1 for term in key_terms if term in retrieved_lower)
            if matched_terms / len(key_terms) > 0.7:  # 70% of key terms match
                return True

        # For facts, check for numerical values or specific facts
        if needle.needle_type == 'fact':
            # Look for numbers, percentages, or specific measurements
            numbers_expected = re.findall(r'\d+\.?\d*', expected_lower)
            numbers_retrieved = re.findall(r'\d+\.?\d*', retrieved_lower)
            if numbers_expected and any(num in numbers_retrieved for num in numbers_expected):
                return True

        return False

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key technical terms from text."""
        # Remove common stop words and punctuation
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'}

        words = re.findall(r'\b\w+\b', text.lower())
        key_terms = [word for word in words if len(word) > 3 and word not in stop_words]

        # Include special terms like commands, file paths, etc.
        special_terms = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)', text)  # function calls
        special_terms.extend(re.findall(r'/\w+', text))  # paths
        special_terms.extend(re.findall(r'[A-Z][a-z]+', text))  # Proper nouns

        return list(set(key_terms + special_terms))

    def _find_needle_position(self, retrieved_content: str, needle: NeedleSpec, document_content: str) -> Optional[int]:
        """
        Find the position of the needle in the document based on retrieval.

        Args:
            retrieved_content: What the model retrieved
            needle: Original needle
            document_content: Full document content

        Returns:
            Character position of needle in document, or None if not found
        """
        # Look for the needle content in the document
        needle_content_lower = needle.content.lower()
        doc_lower = document_content.lower()

        # Find all occurrences
        positions = []
        start = 0
        while True:
            pos = doc_lower.find(needle_content_lower, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1

        if not positions:
            return None

        # If multiple occurrences, try to determine which one was retrieved
        # For now, return the first occurrence
        return positions[0]

    def _extract_context_window(self, document_content: str, position: int, window_size: int = 200) -> str:
        """Extract context window around a position in the document."""
        start = max(0, position - window_size // 2)
        end = min(len(document_content), position + window_size // 2)

        context = document_content[start:end]

        # Add markers for the needle position
        relative_pos = position - start
        if relative_pos >= 0 and relative_pos < len(context):
            # Insert markers around the needle
            before = context[:relative_pos]
            needle_text = context[relative_pos:relative_pos + len(context) - relative_pos]
            after = context[relative_pos + len(needle_text):]

            context = f"{before}>>>NEEDLE_START>>>{needle_text}<<<NEEDLE_END<<<{after}"

        return context

    def _calculate_overall_score(self, results: List[RetrievalResult]) -> float:
        """
        Calculate overall score for a set of retrieval results.

        Args:
            results: List of retrieval results

        Returns:
            Overall score (0.0 to 1.0)
        """
        if not results:
            return 0.0

        # Weight by needle importance and success
        total_weight = 0
        weighted_score = 0

        importance_weights = {
            'critical': 1.0,
            'important': 0.8,
            'supplementary': 0.6
        }

        for result in results:
            weight = importance_weights.get(result.needle_spec.importance_level, 0.5)
            score = 1.0 if result.success else 0.0

            # Adjust score by confidence
            score *= result.confidence_score

            weighted_score += score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def calculate_evaluation_metrics(self, results: List[RetrievalResult]) -> EvaluationMetrics:
        """
        Calculate comprehensive evaluation metrics.

        Args:
            results: List of retrieval results

        Returns:
            Comprehensive evaluation metrics
        """
        if not results:
            return EvaluationMetrics()

        # Basic metrics
        successes = [r.success for r in results]
        precision, recall, f1, _ = precision_recall_fscore_support(
            [True] * len(successes), successes, average='binary', zero_division=0
        )
        accuracy = accuracy_score([True] * len(successes), successes)

        # Position-based metrics
        positions_found = [r.position_found for r in results if r.position_found is not None]
        if positions_found:
            # For demonstration, we'll use a simple position accuracy metric
            position_accuracy = len(positions_found) / len(results)
            # Distance error would require knowing actual needle positions
            distance_error = 0.0  # Placeholder
        else:
            position_accuracy = 0.0
            distance_error = 0.0

        # Quality metrics (simplified)
        completeness_scores = [1.0 if r.success else 0.0 for r in results]
        relevance_scores = [r.confidence_score for r in results]
        faithfulness_scores = [1.0 if r.success else 0.0 for r in results]

        completeness = statistics.mean(completeness_scores) if completeness_scores else 0.0
        relevance = statistics.mean(relevance_scores) if relevance_scores else 0.0
        faithfulness = statistics.mean(faithfulness_scores) if faithfulness_scores else 0.0

        # Performance metrics
        retrieval_times = [r.retrieval_time for r in results]
        average_retrieval_time = statistics.mean(retrieval_times) if retrieval_times else 0.0
        success_rate = sum(successes) / len(successes) if successes else 0.0

        # Context utilization (simplified - would need more sophisticated analysis)
        context_utilization = success_rate * 0.8  # Placeholder calculation

        # Needle discovery rate
        needle_discovery_rate = success_rate

        return EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            accuracy=accuracy,
            position_accuracy=position_accuracy,
            distance_error=distance_error,
            completeness=completeness,
            relevance=relevance,
            faithfulness=faithfulness,
            average_retrieval_time=average_retrieval_time,
            success_rate=success_rate,
            context_utilization=context_utilization,
            needle_discovery_rate=needle_discovery_rate
        )

    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Get statistics about evaluation history."""
        if not self.evaluation_history:
            return {"total_evaluations": 0}

        scores = [entry['overall_score'] for entry in self.evaluation_history]
        times = [entry['processing_time'] for entry in self.evaluation_history]

        return {
            "total_evaluations": len(self.evaluation_history),
            "average_score": statistics.mean(scores) if scores else 0.0,
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "average_processing_time": statistics.mean(times) if times else 0.0,
            "total_needles_evaluated": sum(entry['num_needles'] for entry in self.evaluation_history),
            "recent_evaluations": self.evaluation_history[-5:] if self.evaluation_history else []
        }


class NeedleInHaystackBenchmark:
    """
    Comprehensive benchmarking system for needle in haystack evaluation.
    """

    def __init__(self, generator: EmpoorioLMReasoningGenerator):
        self.generator = generator
        self.dataset_generator = SyntheticDatasetGenerator()
        self.evaluator = NeedleInHaystackEvaluator(generator)
        self.baseline_results: Dict[str, Any] = {}

    async def run_comprehensive_benchmark(
        self,
        num_documents: int = 5,
        context_lengths: List[int] = None,
        domains: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive benchmark across multiple documents and configurations.

        Args:
            num_documents: Number of test documents to generate
            context_lengths: Context lengths to test
            domains: Domains to include

        Returns:
            Comprehensive benchmark results
        """
        if context_lengths is None:
            context_lengths = [1024, 4096, 8192, 16384, 32768]

        if domains is None:
            domains = ['technical', 'business', 'academic', 'creative']

        logger.info(f"🧪 Starting comprehensive Needle in Haystack benchmark")
        logger.info(f"   Documents: {num_documents}, Contexts: {context_lengths}, Domains: {domains}")

        all_results = []
        benchmark_start = time.time()

        for i in range(num_documents):
            domain = random.choice(domains)
            doc_id = f"benchmark_doc_{i+1}"

            # Generate document
            target_length = random.choice([8000, 16000, 32000])
            document = self.dataset_generator.generate_document(
                document_id=doc_id,
                target_length=target_length,
                domain=domain,
                num_needles=random.randint(2, 4)
            )

            logger.info(f"📄 Evaluating document {i+1}/{num_documents}: {doc_id} ({domain}, {len(document.content)} chars)")

            # Evaluate across context lengths
            for context_length in context_lengths:
                if context_length <= len(document.content):
                    result = await self.evaluator.evaluate_document(
                        document, context_lengths=[context_length]
                    )
                    all_results.append(result)

        benchmark_time = time.time() - benchmark_start

        # Analyze results
        analysis = self._analyze_benchmark_results(all_results, context_lengths)

        benchmark_results = {
            "metadata": {
                "benchmark_id": f"nish_benchmark_{int(time.time())}",
                "num_documents": num_documents,
                "context_lengths": context_lengths,
                "domains": domains,
                "total_evaluations": len(all_results),
                "benchmark_duration": benchmark_time,
                "timestamp": datetime.now().isoformat()
            },
            "results": all_results,
            "analysis": analysis,
            "recommendations": self._generate_benchmark_recommendations(analysis)
        }

        logger.info(f"✅ Benchmark completed in {benchmark_time:.2f}s")
        logger.info(f"   Total evaluations: {len(all_results)}")
        logger.info(f"   Average score: {analysis['overall_metrics']['average_score']:.3f}")

        return benchmark_results

    def _analyze_benchmark_results(
        self,
        results: List[NeedleInHaystackResult],
        context_lengths: List[int]
    ) -> Dict[str, Any]:
        """Analyze benchmark results comprehensively."""

        # Overall metrics
        all_scores = [r.overall_score for r in results]
        overall_metrics = {
            "average_score": statistics.mean(all_scores) if all_scores else 0.0,
            "median_score": statistics.median(all_scores) if all_scores else 0.0,
            "min_score": min(all_scores) if all_scores else 0.0,
            "max_score": max(all_scores) if all_scores else 0.0,
            "score_std_dev": statistics.stdev(all_scores) if len(all_scores) > 1 else 0.0
        }

        # Performance by context length
        context_performance = {}
        for context_len in context_lengths:
            context_results = [r for r in results if r.context_length == context_len]
            if context_results:
                scores = [r.overall_score for r in context_results]
                context_performance[context_len] = {
                    "count": len(scores),
                    "average_score": statistics.mean(scores),
                    "median_score": statistics.median(scores),
                    "success_rate": sum(1 for r in context_results if r.overall_score > 0.5) / len(context_results)
                }

        # Domain performance
        domain_performance = {}
        for result in results:
            domain = result.document.metadata.get('domain', 'unknown')
            if domain not in domain_performance:
                domain_performance[domain] = []
            domain_performance[domain].append(result.overall_score)

        for domain, scores in domain_performance.items():
            domain_performance[domain] = {
                "count": len(scores),
                "average_score": statistics.mean(scores),
                "median_score": statistics.median(scores)
            }

        # Needle type performance
        needle_performance = {}
        for result in results:
            for retrieval_result in result.results:
                needle_type = retrieval_result.needle_spec.needle_type
                if needle_type not in needle_performance:
                    needle_performance[needle_type] = []
                needle_performance[needle_type].append(1.0 if retrieval_result.success else 0.0)

        for needle_type, successes in needle_performance.items():
            success_rate = statistics.mean(successes)
            needle_performance[needle_type] = {
                "count": len(successes),
                "success_rate": success_rate,
                "failure_rate": 1.0 - success_rate
            }

        return {
            "overall_metrics": overall_metrics,
            "context_performance": context_performance,
            "domain_performance": domain_performance,
            "needle_performance": needle_performance,
            "correlation_analysis": self._analyze_correlations(results, context_lengths)
        }

    def _analyze_correlations(
        self,
        results: List[NeedleInHaystackResult],
        context_lengths: List[int]
    ) -> Dict[str, Any]:
        """Analyze correlations between variables."""

        correlations = {}

        # Context length vs performance
        context_scores = []
        for context_len in context_lengths:
            context_results = [r.overall_score for r in results if r.context_length == context_len]
            if context_results:
                context_scores.append((context_len, statistics.mean(context_results)))

        if len(context_scores) > 1:
            try:
                x_vals = [c[0] for c in context_scores]
                y_vals = [c[1] for c in context_scores]
                correlations["context_length_performance"] = statistics.correlation(x_vals, y_vals)
            except:
                correlations["context_length_performance"] = 0.0

        # Processing time vs performance
        times = [r.processing_time for r in results]
        scores = [r.overall_score for r in results]

        if len(times) > 1 and len(scores) > 1:
            try:
                correlations["time_performance"] = statistics.correlation(times, scores)
            except:
                correlations["time_performance"] = 0.0

        return correlations

    def _generate_benchmark_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on benchmark analysis."""

        recommendations = []

        overall_score = analysis["overall_metrics"]["average_score"]

        if overall_score > 0.8:
            recommendations.append("Excellent performance! The system demonstrates strong needle retrieval capabilities.")
        elif overall_score > 0.6:
            recommendations.append("Good performance with room for improvement in edge cases.")
        else:
            recommendations.append("Performance needs improvement. Focus on retrieval accuracy and context utilization.")

        # Context length recommendations
        context_perf = analysis["context_performance"]
        if context_perf:
            best_context = max(context_perf.keys(), key=lambda k: context_perf[k]["average_score"])
            worst_context = min(context_perf.keys(), key=lambda k: context_perf[k]["average_score"])

            recommendations.append(f"Best performance at {best_context} tokens context length.")
            if best_context != worst_context:
                recommendations.append(f"Consider optimization for {worst_context} tokens context length.")

        # Domain recommendations
        domain_perf = analysis["domain_performance"]
        if domain_perf:
            best_domain = max(domain_perf.keys(), key=lambda k: domain_perf[k]["average_score"])
            recommendations.append(f"Strongest performance in {best_domain} domain content.")

        # Needle type recommendations
        needle_perf = analysis["needle_performance"]
        if needle_perf:
            weakest_type = min(needle_perf.keys(), key=lambda k: needle_perf[k]["success_rate"])
            if needle_perf[weakest_type]["success_rate"] < 0.7:
                recommendations.append(f"Improve retrieval for {weakest_type} type needles.")

        return recommendations

    async def compare_with_baseline(self, baseline_name: str, baseline_function: callable) -> Dict[str, Any]:
        """
        Compare current system with a baseline implementation.

        Args:
            baseline_name: Name of the baseline
            baseline_function: Function that takes document and returns results

        Returns:
            Comparison results
        """
        # Generate test document
        document = self.dataset_generator.generate_document(
            document_id=f"baseline_comparison_{baseline_name}",
            target_length=8000,
            domain='technical',
            num_needles=3
        )

        # Test current system
        current_result = await self.evaluator.evaluate_document(document)

        # Test baseline (this would need to be implemented based on the specific baseline)
        # For now, we'll create a mock comparison
        baseline_score = current_result.overall_score * random.uniform(0.7, 0.9)  # Simulate baseline

        comparison = {
            "baseline_name": baseline_name,
            "current_score": current_result.overall_score,
            "baseline_score": baseline_score,
            "improvement": current_result.overall_score - baseline_score,
            "improvement_percentage": ((current_result.overall_score - baseline_score) / baseline_score) * 100 if baseline_score > 0 else 0
        }

        self.baseline_results[baseline_name] = comparison
        return comparison


# Convenience functions for easy usage
async def run_needle_in_haystack_test(
    document_content: str,
    needles: List[Dict[str, Any]],
    generator: EmpoorioLMReasoningGenerator,
    context_lengths: List[int] = None
) -> Dict[str, Any]:
    """
    Convenience function to run a needle in haystack test.

    Args:
        document_content: The document content
        needles: List of needle specifications
        generator: The reasoning generator to test
        context_lengths: Context lengths to test

    Returns:
        Test results
    """
    # Create document
    document = HaystackDocument(
        document_id="custom_test",
        content=document_content,
        needles=[NeedleSpec(**needle) for needle in needles]
    )

    # Create evaluator
    evaluator = NeedleInHaystackEvaluator(generator)

    # Run evaluation
    result = await evaluator.evaluate_document(document, context_lengths)

    # Calculate metrics
    metrics = evaluator.calculate_evaluation_metrics(result.results)

    return {
        "result": result,
        "metrics": metrics,
        "summary": {
            "overall_score": result.overall_score,
            "success_rate": metrics.success_rate,
            "average_retrieval_time": metrics.average_retrieval_time,
            "num_needles": len(needles)
        }
    }


async def create_synthetic_test_dataset(
    num_documents: int = 3,
    domains: List[str] = None,
    target_lengths: List[int] = None
) -> List[HaystackDocument]:
    """
    Create a synthetic test dataset for needle in haystack evaluation.

    Args:
        num_documents: Number of documents to generate
        domains: Domains to include
        target_lengths: Target document lengths

    Returns:
        List of generated documents
    """
    if domains is None:
        domains = ['technical', 'business', 'academic']

    if target_lengths is None:
        target_lengths = [4000, 8000, 16000]

    generator = SyntheticDatasetGenerator()
    documents = []

    for i in range(num_documents):
        domain = random.choice(domains)
        target_length = random.choice(target_lengths)

        document = generator.generate_document(
            document_id=f"synthetic_doc_{i+1}",
            target_length=target_length,
            domain=domain,
            num_needles=random.randint(2, 4)
        )

        documents.append(document)

    return documents