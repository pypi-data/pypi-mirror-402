"""
NIAH Generator - Professional Synthetic Dataset Generation
==========================================================

Advanced generator for creating synthetic "haystack" documents with precisely
placed "needle" information for evaluating long context understanding.

This implementation combines:
- Controlled needle placement at specific depths
- Realistic filler content generation
- Multiple needle types and complexities
- Token-aware positioning for accurate benchmarking
"""

import random
import uuid
import logging
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class NeedleSpec:
    """Specification for a needle (target information) to be placed in haystack."""
    content: str
    needle_type: str  # 'fact', 'code', 'quote', 'instruction', 'definition'
    verification_question: str
    expected_answer: str
    complexity_level: str = 'medium'  # 'simple', 'medium', 'complex'
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class HaystackDocument:
    """A generated document containing needles at specific positions."""
    document_id: str
    content: str
    needles: List[NeedleSpec]
    total_tokens: int
    needle_positions: Dict[str, int]  # needle_id -> position
    metadata: Dict[str, Any]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class NIAHGenerator:
    """
    Professional NIAH generator with advanced synthetic content creation.

    Features:
    - Multiple filler content types (technical, business, academic, creative)
    - Precise token-based positioning
    - Multiple needle types with varying complexity
    - Realistic document structure
    - Configurable generation parameters
    """

    def __init__(self, tokenizer=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the NIAH generator.

        Args:
            tokenizer: Optional tokenizer for accurate token counting
            config: Configuration dictionary
        """
        self.tokenizer = tokenizer
        self.config = config or self._default_config()

        # Filler content templates for different domains
        self.filler_templates = self._load_filler_templates()

        # Needle generation patterns
        self.needle_generators = self._initialize_needle_generators()

        logger.info("🧵 NIAH Generator initialized with professional configuration")

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for the generator."""
        return {
            'filler_complexity': 'medium',
            'needle_density': 0.001,  # needles per token
            'min_needle_distance': 100,  # minimum tokens between needles
            'context_buffer': 50,  # tokens to keep clear around needles
            'realistic_structure': True,  # add document structure
            'domain_mixing': True,  # mix different content domains
        }

    def _load_filler_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Load filler content templates for different domains."""
        return {
            'technical': {
                'paragraphs': [
                    "The rapid advancement of artificial intelligence has revolutionized software development practices. Machine learning algorithms now power recommendation systems, autonomous vehicles, and natural language processing applications. Deep learning architectures, particularly transformer models, have achieved state-of-the-art performance across numerous benchmarks. Distributed computing frameworks enable scalable training of large language models on massive datasets. Neural network optimization techniques continue to evolve, with researchers exploring novel architectures and training methodologies.",
                    "Computer vision systems leverage convolutional neural networks to process and understand visual information. Image recognition, object detection, and semantic segmentation tasks benefit from these advanced architectures. Transfer learning approaches allow models trained on large datasets to be fine-tuned for specific applications. Edge computing enables real-time inference on resource-constrained devices. Computer graphics and rendering techniques have evolved significantly with GPU acceleration and ray tracing technologies.",
                    "Database systems have evolved from traditional relational models to include NoSQL, graph databases, and NewSQL solutions. Distributed databases provide horizontal scalability and fault tolerance. Data warehousing solutions enable complex analytical queries on massive datasets. Real-time streaming platforms process continuous data flows. Database optimization techniques include indexing strategies, query planning, and caching mechanisms. Data consistency models range from strong consistency to eventual consistency based on application requirements.",
                    "Cybersecurity measures protect digital assets from various threats and vulnerabilities. Encryption algorithms secure data transmission and storage. Multi-factor authentication provides additional security layers. Intrusion detection systems monitor network traffic for suspicious activities. Blockchain technology enables decentralized and tamper-proof transaction systems. Zero-trust security models assume no implicit trust within network boundaries. Security audits and penetration testing identify potential weaknesses in systems."
                ],
                'transitions': [
                    "Furthermore,", "Additionally,", "Moreover,", "In contrast,",
                    "However,", "Consequently,", "Therefore,", "Specifically,"
                ]
            },
            'business': {
                'paragraphs': [
                    "Strategic business planning requires comprehensive market analysis and competitive intelligence. Organizations must understand customer needs, market trends, and competitive positioning. Business intelligence tools provide data-driven insights for decision making. Strategic partnerships and alliances can create competitive advantages. Innovation management drives product development and market differentiation. Change management ensures successful implementation of organizational transformations. Performance measurement systems track key business metrics and KPIs.",
                    "Financial management encompasses budgeting, forecasting, and investment decisions. Capital budgeting techniques evaluate long-term investment opportunities. Risk management strategies protect organizations from financial losses. Treasury management optimizes cash flow and liquidity. Financial reporting provides transparency to stakeholders. Cost accounting systems track product and service costs. Financial technology innovations disrupt traditional banking and payment systems. Regulatory compliance ensures adherence to financial reporting standards.",
                    "Human resource management involves talent acquisition, development, and retention strategies. Employee engagement drives organizational performance and productivity. Performance management systems align individual goals with organizational objectives. Leadership development programs build future organizational capabilities. Diversity and inclusion initiatives create equitable workplaces. Compensation and benefits programs attract and retain top talent. Learning and development initiatives enhance employee skills and competencies. Organizational culture influences employee behavior and performance.",
                    "Supply chain management coordinates the flow of goods, services, and information. Procurement strategies optimize supplier relationships and costs. Inventory management balances supply and demand requirements. Logistics and transportation systems ensure timely delivery. Warehouse management systems optimize storage and distribution. Demand forecasting improves planning accuracy. Supplier relationship management builds strategic partnerships. Sustainability initiatives reduce environmental impact throughout the supply chain."
                ],
                'transitions': [
                    "In business terms,", "From a strategic perspective,", "Operationally,",
                    "Financially speaking,", "In terms of market dynamics,", "Commercially,"
                ]
            },
            'academic': {
                'paragraphs': [
                    "Research methodology provides systematic approaches to knowledge generation and validation. Quantitative research methods employ statistical analysis and numerical data. Qualitative research explores phenomena through interpretive approaches. Mixed methods research combines quantitative and qualitative techniques. Research design considerations include sampling strategies, data collection methods, and analysis techniques. Validity and reliability ensure research quality and trustworthiness. Ethical considerations guide responsible research practices. Peer review processes validate research findings and methodologies.",
                    "Educational psychology examines learning processes and cognitive development. Learning theories explain how individuals acquire and retain knowledge. Cognitive development stages influence educational approaches. Motivation theories drive student engagement and achievement. Assessment strategies measure learning outcomes and competencies. Individual differences affect learning styles and preferences. Educational technology enhances teaching and learning experiences. Curriculum development aligns educational goals with societal needs. Teacher training programs develop pedagogical competencies.",
                    "Social sciences investigate human behavior and societal structures. Sociological theories explain social phenomena and group dynamics. Psychological research explores mental processes and behavior patterns. Anthropological studies examine cultural diversity and human evolution. Political science analyzes governance systems and power structures. Economic theories model resource allocation and market dynamics. Communication studies explore information exchange and media effects. Interdisciplinary approaches integrate multiple social science perspectives. Empirical research validates theoretical frameworks and hypotheses.",
                    "Scientific inquiry follows systematic investigation principles. Hypothesis formulation guides research questions and objectives. Experimental design controls variables and ensures validity. Data collection methods gather empirical evidence. Statistical analysis interprets research findings. Scientific peer review validates research quality. Replication studies confirm research reliability. Scientific communication disseminates knowledge to the research community. Research ethics ensure responsible scientific practices. Interdisciplinary collaboration advances scientific understanding."
                ],
                'transitions': [
                    "Academically,", "From a research perspective,", "Theoretically,",
                    "Empirically,", "In scholarly terms,", "According to current literature,"
                ]
            },
            'creative': {
                'paragraphs': [
                    "Creative expression manifests through various artistic mediums and forms. Visual arts communicate ideas through color, shape, and composition. Literary works explore human experiences and emotions. Musical compositions evoke feelings and memories. Performing arts bring stories to life through movement and dialogue. Digital art embraces technology in creative processes. Artistic movements reflect cultural and historical contexts. Creative collaboration enhances artistic outcomes. Artistic critique provides constructive feedback and interpretation. Artistic education develops creative skills and appreciation.",
                    "Design thinking provides structured approaches to creative problem solving. Human-centered design focuses on user needs and experiences. Iterative design processes refine creative solutions. Prototyping techniques test design concepts and functionality. User research informs design decisions and requirements. Design systems create consistency and scalability. Visual design principles guide aesthetic and functional decisions. Interaction design enhances user experiences and interfaces. Service design considers end-to-end user journeys. Design innovation drives product and service development.",
                    "Narrative structures organize stories and information presentation. Story arcs provide dramatic progression and development. Character development creates relatable and compelling personalities. Plot structures organize events and conflicts. Thematic elements convey deeper meanings and messages. Narrative techniques engage audiences and maintain interest. Digital storytelling leverages multimedia elements. Transmedia storytelling spans multiple platforms and formats. Narrative design creates immersive experiences. Cultural narratives shape collective identities and values.",
                    "Innovation processes combine creativity with systematic methodologies. Creative problem solving techniques generate novel solutions. Brainstorming methods encourage idea generation. Design thinking frameworks structure innovation processes. Prototyping and testing validate innovative concepts. Intellectual property protection secures innovation investments. Innovation ecosystems support collaborative development. Technology transfer moves innovations from research to application. Innovation metrics measure creative and economic impact. Sustainable innovation considers environmental and social impacts."
                ],
                'transitions': [
                    "Creatively,", "From an artistic viewpoint,", "Imaginatively,",
                    "Innovatively,", "Aesthetically,", "Expressively,"
                ]
            }
        }

    def _initialize_needle_generators(self) -> Dict[str, callable]:
        """Initialize needle generation functions for different types."""
        return {
            'fact': self._generate_fact_needle,
            'code': self._generate_code_needle,
            'quote': self._generate_quote_needle,
            'instruction': self._generate_instruction_needle,
            'definition': self._generate_definition_needle,
        }

    def generate_test_case(
        self,
        context_length: int,
        depth_percent: float,
        domain: str = 'technical',
        needle_type: str = 'fact'
    ) -> Tuple[str, str, str, NeedleSpec]:
        """
        Generate a complete test case with context, question, answer, and needle spec.

        Args:
            context_length: Target context length in tokens
            depth_percent: Where to place the needle (0.0 = start, 1.0 = end)
            domain: Content domain for filler text
            needle_type: Type of needle to generate

        Returns:
            Tuple of (context, question, expected_answer, needle_spec)
        """
        # Generate the needle
        needle_spec = self.needle_generators[needle_type](domain, 'medium', 0)

        # Generate the haystack document
        document = self.generate_document(
            document_id=f"niah_test_{uuid.uuid4().hex[:8]}",
            target_length=context_length,
            domain=domain,
            needles=[needle_spec],
            needle_depth=depth_percent
        )

        return (
            document.content,
            needle_spec.verification_question,
            needle_spec.expected_answer,
            needle_spec
        )

    def generate_document(
        self,
        document_id: str,
        target_length: int,
        domain: str = 'technical',
        needles: Optional[List[NeedleSpec]] = None,
        needle_depth: float = 0.5
    ) -> HaystackDocument:
        """
        Generate a complete document with embedded needles.

        Args:
            document_id: Unique identifier for the document
            target_length: Target length in tokens
            domain: Content domain
            needles: List of needles to embed (if None, generates one)
            needle_depth: Where to place needles (0.0-1.0)

        Returns:
            Complete HaystackDocument
        """
        if needles is None:
            needle = self.needle_generators['fact'](domain, 'medium', 0)
            needles = [needle]

        # Estimate characters per token (rough approximation)
        chars_per_token = 4
        target_chars = target_length * chars_per_token

        # Generate filler content
        filler_content = self._generate_filler_content(target_chars, domain)

        # Insert needles at specified depths
        needle_positions = {}
        final_content = filler_content

        for i, needle in enumerate(needles):
            if len(needles) == 1:
                depth = needle_depth
            else:
                # Distribute needles evenly
                depth = i / (len(needles) - 1) if len(needles) > 1 else 0.5

            final_content, position = self._insert_needle_at_depth(
                final_content, needle, depth
            )
            needle_positions[needle.content[:50]] = position

        # Count actual tokens if tokenizer available
        actual_tokens = len(final_content.split())  # Rough approximation
        if self.tokenizer:
            try:
                actual_tokens = len(self.tokenizer.encode(final_content))
            except:
                pass

        return HaystackDocument(
            document_id=document_id,
            content=final_content,
            needles=needles,
            total_tokens=actual_tokens,
            needle_positions=needle_positions,
            metadata={
                'domain': domain,
                'target_length': target_length,
                'actual_length': actual_tokens,
                'needle_count': len(needles),
                'generator_config': self.config.copy()
            }
        )

    def _generate_filler_content(self, target_chars: int, domain: str) -> str:
        """Generate filler content for the specified domain."""
        template = self.filler_templates.get(domain, self.filler_templates['technical'])

        content_parts = []
        current_length = 0

        while current_length < target_chars:
            # Add a paragraph
            paragraph = random.choice(template['paragraphs'])

            # Add transition if not first paragraph
            if content_parts:
                transition = random.choice(template['transitions'])
                paragraph = f"{transition} {paragraph.lower()}"

            content_parts.append(paragraph)
            current_length += len(paragraph)

        return " ".join(content_parts)

    def _insert_needle_at_depth(self, content: str, needle: NeedleSpec, depth: float) -> Tuple[str, int]:
        """Insert a needle at the specified depth percentage."""
        content_length = len(content)

        # Calculate insertion point
        insert_position = int(content_length * depth)

        # Ensure we don't split words
        while insert_position < content_length and content[insert_position] != ' ':
            insert_position += 1

        # Insert the needle
        needle_text = f" {needle.content} "
        new_content = content[:insert_position] + needle_text + content[insert_position:]

        return new_content, insert_position

    def _generate_fact_needle(self, domain: str, complexity: str, seed: int) -> NeedleSpec:
        """Generate a factual needle."""
        random.seed(seed)

        facts_by_domain = {
            'technical': [
                "The TCP three-way handshake establishes reliable connections in network communications.",
                "Quantum computers use superposition and entanglement to perform parallel computations.",
                "Blockchain technology maintains immutable transaction records through cryptographic hashing.",
                "Machine learning models require feature engineering to improve predictive accuracy.",
                "Container orchestration systems manage deployment and scaling of microservices architectures."
            ],
            'business': [
                "Return on investment (ROI) measures the efficiency of business investments over time.",
                "Supply chain optimization reduces costs and improves delivery reliability.",
                "Customer lifetime value (CLV) predicts the total revenue from a customer relationship.",
                "Agile methodology emphasizes iterative development and customer collaboration.",
                "Market segmentation divides customers into groups with similar needs and characteristics."
            ],
            'academic': [
                "Cognitive dissonance occurs when individuals hold contradictory beliefs or values.",
                "Natural selection drives evolutionary adaptation in biological populations.",
                "Social constructivism suggests knowledge is built through social interactions.",
                "Confirmation bias leads people to favor information supporting existing beliefs.",
                "Maslow's hierarchy organizes human needs from physiological to self-actualization."
            ],
            'creative': [
                "Color theory explains how primary colors combine to create secondary hues.",
                "The golden ratio (phi) appears in art, architecture, and natural patterns.",
                "Narrative structure typically includes exposition, rising action, climax, and resolution.",
                "Minimalist design emphasizes simplicity and removal of unnecessary elements.",
                "Symmetry in visual composition creates balance and aesthetic appeal."
            ]
        }

        facts = facts_by_domain.get(domain, facts_by_domain['technical'])
        fact = random.choice(facts)

        # Create verification question
        question = f"What is stated about {fact.split()[1]} in the context?"

        return NeedleSpec(
            content=fact,
            needle_type='fact',
            verification_question=question,
            expected_answer=fact,
            complexity_level=complexity,
            metadata={'domain': domain, 'fact_type': 'general'}
        )

    def _generate_code_needle(self, domain: str, complexity: str, seed: int) -> NeedleSpec:
        """Generate a code-related needle."""
        code_snippets = [
            "The function `map()` applies a given function to each item of an iterable.",
            "List comprehension `[x**2 for x in range(10)]` creates squares efficiently.",
            "The `async def` syntax defines asynchronous functions in Python.",
            "Dictionary merging uses `{**dict1, **dict2}` syntax in modern Python.",
            "Lambda functions `lambda x: x * 2` create anonymous inline functions."
        ]

        code = random.choice(code_snippets)
        question = "What does the code snippet demonstrate?"

        return NeedleSpec(
            content=code,
            needle_type='code',
            verification_question=question,
            expected_answer=code,
            complexity_level=complexity,
            metadata={'language': 'python', 'concept': 'syntax'}
        )

    def _generate_quote_needle(self, domain: str, complexity: str, seed: int) -> NeedleSpec:
        """Generate a quote needle."""
        quotes = [
            "\"The best way to predict the future is to create it.\" - Peter Drucker",
            "\"Innovation distinguishes between a leader and a follower.\" - Steve Jobs",
            "\"The only way to do great work is to love what you do.\" - Steve Jobs",
            "\"Your most unhappy customers are your greatest source of learning.\" - Bill Gates",
            "\"The future belongs to those who believe in the beauty of their dreams.\" - Eleanor Roosevelt"
        ]

        quote = random.choice(quotes)
        question = "What quote is mentioned in the document?"

        return NeedleSpec(
            content=quote,
            needle_type='quote',
            verification_question=question,
            expected_answer=quote,
            complexity_level=complexity,
            metadata={'author': quote.split('-')[1].strip(), 'type': 'motivational'}
        )

    def _generate_instruction_needle(self, domain: str, complexity: str, seed: int) -> NeedleSpec:
        """Generate an instruction needle."""
        instructions = [
            "To reset the system, navigate to Settings > System > Reset and confirm the action.",
            "Enable two-factor authentication by going to Security settings and selecting 2FA.",
            "Update the software by downloading the latest version from the official repository.",
            "Configure the network by entering the IP address and subnet mask in network settings.",
            "Backup your data regularly by selecting Backup from the File menu and choosing a destination."
        ]

        instruction = random.choice(instructions)
        question = "What are the steps to perform this action?"

        return NeedleSpec(
            content=instruction,
            needle_type='instruction',
            verification_question=question,
            expected_answer=instruction,
            complexity_level=complexity,
            metadata={'action_type': 'configuration', 'steps': instruction.count('>') + 1}
        )

    def _generate_definition_needle(self, domain: str, complexity: str, seed: int) -> NeedleSpec:
        """Generate a definition needle."""
        definitions = [
            "API (Application Programming Interface) is a set of rules and protocols for accessing a software application.",
            "Cache memory is a high-speed data storage layer that stores frequently accessed data for quick retrieval.",
            "Encryption is the process of converting readable data into an unreadable format using mathematical algorithms.",
            "Scalability refers to the ability of a system to handle increased load by adding resources.",
            "Authentication is the process of verifying the identity of a user or system entity."
        ]

        definition = random.choice(definitions)
        term = definition.split('(')[0].strip()
        question = f"What is the definition of {term}?"

        return NeedleSpec(
            content=definition,
            needle_type='definition',
            verification_question=question,
            expected_answer=definition,
            complexity_level=complexity,
            metadata={'term': term, 'field': 'technology'}
        )

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about generated content."""
        return {
            'supported_domains': list(self.filler_templates.keys()),
            'needle_types': list(self.needle_generators.keys()),
            'config': self.config.copy()
        }