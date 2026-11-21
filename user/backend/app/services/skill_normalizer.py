"""Taxonomy, normalization, and relationship mapping for technical and professional skills."""

import re
from typing import Any

# Canonical skill metadata: canonical_name -> (category, default_importance)
SKILL_TAXONOMY: dict[str, tuple[str, str]] = {
    # Programming Languages
    "Python": ("Programming Languages", "high"),
    "JavaScript": ("Programming Languages", "high"),
    "TypeScript": ("Programming Languages", "high"),
    "Java": ("Programming Languages", "high"),
    "C++": ("Programming Languages", "high"),
    "C#": ("Programming Languages", "high"),
    "Go": ("Programming Languages", "high"),
    "Rust": ("Programming Languages", "high"),
    "Ruby": ("Programming Languages", "medium"),
    "PHP": ("Programming Languages", "medium"),
    "SQL": ("Programming Languages", "high"),
    "HTML": ("Programming Languages", "medium"),
    "CSS": ("Programming Languages", "medium"),
    "Bash": ("Programming Languages", "medium"),
    "Shell": ("Programming Languages", "medium"),
    "Scala": ("Programming Languages", "medium"),
    "Kotlin": ("Programming Languages", "high"),
    "Swift": ("Programming Languages", "high"),
    "R": ("Programming Languages", "medium"),
    # AI & Machine Learning
    "Scikit-learn": ("AI & Machine Learning", "high"),
    "XGBoost": ("AI & Machine Learning", "high"),
    "Pandas": ("AI & Machine Learning", "high"),
    "NumPy": ("AI & Machine Learning", "high"),
    "OpenCV": ("AI & Machine Learning", "high"),
    "YOLOv8": ("AI & Machine Learning", "high"),
    "YOLO": ("AI & Machine Learning", "high"),
    "Tesseract OCR": ("AI & Machine Learning", "medium"),
    "PyTorch": ("AI & Machine Learning", "high"),
    "TensorFlow": ("AI & Machine Learning", "high"),
    "Machine Learning": ("AI & Machine Learning", "high"),
    "Deep Learning": ("AI & Machine Learning", "high"),
    "NLP": ("AI & Machine Learning", "high"),
    "Feature Engineering": ("AI & Machine Learning", "medium"),
    "Model Evaluation": ("AI & Machine Learning", "medium"),
    "Data Engineering": ("AI & Machine Learning", "high"),
    "Apache Spark": ("AI & Machine Learning", "high"),
    "Apache Kafka": ("AI & Machine Learning", "high"),
    # LLMs & Retrieval
    "RAG": ("LLMs & Retrieval", "high"),
    "Embeddings": ("LLMs & Retrieval", "high"),
    "Sentence-BERT": ("LLMs & Retrieval", "high"),
    "FAISS": ("LLMs & Retrieval", "high"),
    "ChromaDB": ("LLMs & Retrieval", "high"),
    "LangGraph": ("LLMs & Retrieval", "high"),
    "Ollama": ("LLMs & Retrieval", "high"),
    "Semantic Search": ("LLMs & Retrieval", "high"),
    "SQLite FTS5": ("LLMs & Retrieval", "medium"),
    "FastMCP": ("LLMs & Retrieval", "medium"),
    "Vector Search": ("LLMs & Retrieval", "high"),
    # Backend & APIs
    "FastAPI": ("Backend & APIs", "high"),
    "ASP.NET Core": ("Backend & APIs", "high"),
    "ASP.NET": ("Backend & APIs", "high"),
    "Django": ("Backend & APIs", "high"),
    "Flask": ("Backend & APIs", "medium"),
    "Node.js": ("Backend & APIs", "high"),
    "Express.js": ("Backend & APIs", "high"),
    "Spring Boot": ("Backend & APIs", "high"),
    "REST APIs": ("Backend & APIs", "high"),
    "Pydantic": ("Backend & APIs", "high"),
    "WebSockets": ("Backend & APIs", "medium"),
    "GraphQL": ("Backend & APIs", "medium"),
    "Microservices": ("Backend & APIs", "high"),
    "React": ("Backend & APIs", "high"),
    "Vue.js": ("Backend & APIs", "high"),
    "Angular": ("Backend & APIs", "high"),
    "Next.js": ("Backend & APIs", "high"),
    "CQRS": ("Backend & APIs", "medium"),
    "Clean Architecture": ("Backend & APIs", "medium"),
    # Databases & Storage
    "PostgreSQL": ("Databases & Storage", "high"),
    "SQL Server": ("Databases & Storage", "high"),
    "SQLite": ("Databases & Storage", "medium"),
    "MongoDB": ("Databases & Storage", "high"),
    "MySQL": ("Databases & Storage", "high"),
    "Redis": ("Databases & Storage", "high"),
    "Cassandra": ("Databases & Storage", "medium"),
    "Elasticsearch": ("Databases & Storage", "medium"),
    "DynamoDB": ("Databases & Storage", "medium"),
    # Tools & Infrastructure
    "Git": ("Tools & Infrastructure", "high"),
    "Docker": ("Tools & Infrastructure", "high"),
    "Kubernetes": ("Tools & Infrastructure", "high"),
    "GitHub Actions": ("Tools & Infrastructure", "high"),
    "Linux": ("Tools & Infrastructure", "high"),
    "CI/CD": ("Tools & Infrastructure", "high"),
    "Unit Testing": ("Tools & Infrastructure", "medium"),
    "TDD": ("Tools & Infrastructure", "medium"),
    "AWS": ("Tools & Infrastructure", "high"),
    "Azure": ("Tools & Infrastructure", "high"),
    "GCP": ("Tools & Infrastructure", "high"),
    "Terraform": ("Tools & Infrastructure", "high"),
    "Jenkins": ("Tools & Infrastructure", "medium"),
    "Jira": ("Tools & Infrastructure", "low"),
    "Agile": ("Tools & Infrastructure", "medium"),
    "Scrum": ("Tools & Infrastructure", "medium"),
}

# Alias mapping: lowercase normalized variant -> Canonical Name
ALIAS_TO_CANONICAL: dict[str, str] = {
    # Languages
    "py": "Python",
    "python3": "Python",
    "python 3": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "golang": "Go",
    "go": "Go",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "c sharp": "C#",
    "sql": "SQL",
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "bash": "Bash",
    "shell": "Shell",
    # Frontend
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "react native": "React Native",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "angularjs": "Angular",
    "next": "Next.js",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "redux": "Redux",
    # Backend
    "fastapi": "FastAPI",
    "fast-api": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "express": "Express.js",
    "expressjs": "Express.js",
    "express.js": "Express.js",
    "spring": "Spring Boot",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "asp.net": "ASP.NET",
    "dotnet": "ASP.NET",
    ".net": "ASP.NET",
    "rails": "Ruby on Rails",
    "ruby on rails": "Ruby on Rails",
    "graphql": "GraphQL",
    "graph-ql": "GraphQL",
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "restful": "REST APIs",
    "rest apis": "REST APIs",
    "restful apis": "REST APIs",
    "restful api": "REST APIs",
    "microservices": "Microservices",
    "micro-services": "Microservices",
    # Databases
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "postgre sql": "PostgreSQL",
    "postgre-sql": "PostgreSQL",
    "psql": "PostgreSQL",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "sqlite3": "SQLite",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "dynamodb": "DynamoDB",
    # Cloud & DevOps
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform",
    "cicd": "CI/CD",
    "ci/cd": "CI/CD",
    "ci-cd": "CI/CD",
    "github actions": "GitHub Actions",
    "jenkins": "Jenkins",
    "linux": "Linux",
    # AI & Data
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "machine-learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "deep-learning": "Deep Learning",
    "dl": "Deep Learning",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "pytorch": "PyTorch",
    "tf": "TensorFlow",
    "tensorflow": "TensorFlow",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit-learn": "Scikit-learn",
    "scikit learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "xgboost": "XGBoost",
    "opencv": "OpenCV",
    "yolov8": "YOLOv8",
    "yolo": "YOLO",
    "tesseract": "Tesseract OCR",
    "tesseract ocr": "Tesseract OCR",
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "kafka": "Apache Kafka",
    "apache kafka": "Apache Kafka",
    # LLMs & Retrieval
    "rag": "RAG",
    "faiss": "FAISS",
    "chromadb": "ChromaDB",
    "chroma": "ChromaDB",
    "sentence-bert": "Sentence-BERT",
    "sbert": "Sentence-BERT",
    "langgraph": "LangGraph",
    "ollama": "Ollama",
    "fastmcp": "FastMCP",
    "sqlite fts5": "SQLite FTS5",
    "fts5": "SQLite FTS5",
    "semantic search": "Semantic Search",
    "vector search": "Vector Search",
    # Backend & Architecture
    "asp.net core": "ASP.NET Core",
    "pydantic": "Pydantic",
    "websockets": "WebSockets",
    "cqrs": "CQRS",
    "clean architecture": "Clean Architecture",
    # Databases
    "sql server": "SQL Server",
    "mssql": "SQL Server",
    # Tools & Practices
    "git": "Git",
    "jira": "Jira",
    "agile": "Agile",
    "scrum": "Scrum",
    "tdd": "TDD",
    "unit test": "Unit Testing",
    "unit testing": "Unit Testing",
}

# Ensure all canonical skills in taxonomy are registered in lowercase
for _canonical in SKILL_TAXONOMY:
    if _canonical.lower() not in ALIAS_TO_CANONICAL:
        ALIAS_TO_CANONICAL[_canonical.lower()] = _canonical

# Skill Transferability & Relationship Mapping
# Each relation defines: related_skill, relation_type, strength (0.0 to 1.0)
SKILL_RELATIONSHIPS: dict[str, list[dict[str, Any]]] = {
    # Backend Frameworks -> Languages & Architecture
    "FastAPI": [
        {"related_skill": "Python", "relation_type": "framework_language", "strength": 0.85},
        {"related_skill": "REST APIs", "relation_type": "implements_domain", "strength": 0.80},
        {"related_skill": "Flask", "relation_type": "sibling_framework", "strength": 0.70},
        {"related_skill": "Django", "relation_type": "sibling_framework", "strength": 0.65},
    ],
    "Django": [
        {"related_skill": "Python", "relation_type": "framework_language", "strength": 0.85},
        {"related_skill": "REST APIs", "relation_type": "implements_domain", "strength": 0.75},
        {"related_skill": "Flask", "relation_type": "sibling_framework", "strength": 0.70},
        {"related_skill": "FastAPI", "relation_type": "sibling_framework", "strength": 0.65},
    ],
    "Flask": [
        {"related_skill": "Python", "relation_type": "framework_language", "strength": 0.85},
        {"related_skill": "FastAPI", "relation_type": "sibling_framework", "strength": 0.70},
        {"related_skill": "Django", "relation_type": "sibling_framework", "strength": 0.65},
    ],
    "Express.js": [
        {"related_skill": "Node.js", "relation_type": "framework_runtime", "strength": 0.85},
        {"related_skill": "JavaScript", "relation_type": "framework_language", "strength": 0.80},
        {"related_skill": "REST APIs", "relation_type": "implements_domain", "strength": 0.75},
    ],
    "Spring Boot": [
        {"related_skill": "Java", "relation_type": "framework_language", "strength": 0.85},
        {"related_skill": "REST APIs", "relation_type": "implements_domain", "strength": 0.75},
        {"related_skill": "Microservices", "relation_type": "architecture_pattern", "strength": 0.70},
    ],
    # Frontend Frameworks -> Ecosystem
    "React": [
        {"related_skill": "JavaScript", "relation_type": "framework_language", "strength": 0.85},
        {"related_skill": "TypeScript", "relation_type": "commonly_paired", "strength": 0.75},
        {"related_skill": "Next.js", "relation_type": "parent_ecosystem", "strength": 0.80},
        {"related_skill": "Vue.js", "relation_type": "sibling_framework", "strength": 0.60},
    ],
    "Next.js": [
        {"related_skill": "React", "relation_type": "underlying_framework", "strength": 0.90},
        {"related_skill": "JavaScript", "relation_type": "framework_language", "strength": 0.80},
        {"related_skill": "TypeScript", "relation_type": "commonly_paired", "strength": 0.75},
    ],
    "Vue.js": [
        {"related_skill": "JavaScript", "relation_type": "framework_language", "strength": 0.85},
        {"related_skill": "React", "relation_type": "sibling_framework", "strength": 0.60},
    ],
    "Angular": [
        {"related_skill": "TypeScript", "relation_type": "framework_language", "strength": 0.85},
        {"related_skill": "JavaScript", "relation_type": "underlying_language", "strength": 0.75},
    ],
    # Databases -> SQL & Relational
    "PostgreSQL": [
        {"related_skill": "SQL", "relation_type": "underlying_language", "strength": 0.85},
        {"related_skill": "MySQL", "relation_type": "sibling_database", "strength": 0.70},
        {"related_skill": "SQLite", "relation_type": "sibling_database", "strength": 0.65},
    ],
    "MySQL": [
        {"related_skill": "SQL", "relation_type": "underlying_language", "strength": 0.85},
        {"related_skill": "PostgreSQL", "relation_type": "sibling_database", "strength": 0.70},
    ],
    "SQLite": [
        {"related_skill": "SQL", "relation_type": "underlying_language", "strength": 0.80},
        {"related_skill": "PostgreSQL", "relation_type": "sibling_database", "strength": 0.60},
    ],
    # Cloud & Containers
    "Kubernetes": [
        {"related_skill": "Docker", "relation_type": "underlying_container", "strength": 0.80},
        {"related_skill": "CI/CD", "relation_type": "domain_alignment", "strength": 0.65},
    ],
    "Docker": [
        {"related_skill": "Kubernetes", "relation_type": "ecosystem_tool", "strength": 0.70},
        {"related_skill": "Linux", "relation_type": "operating_environment", "strength": 0.65},
    ],
    "Terraform": [
        {"related_skill": "AWS", "relation_type": "target_cloud", "strength": 0.70},
        {"related_skill": "CI/CD", "relation_type": "domain_alignment", "strength": 0.65},
    ],
    # AI & ML
    "PyTorch": [
        {"related_skill": "Deep Learning", "relation_type": "subfield", "strength": 0.85},
        {"related_skill": "Machine Learning", "relation_type": "parent_domain", "strength": 0.80},
        {"related_skill": "Python", "relation_type": "implementation_language", "strength": 0.85},
        {"related_skill": "TensorFlow", "relation_type": "sibling_framework", "strength": 0.70},
    ],
    "TensorFlow": [
        {"related_skill": "Deep Learning", "relation_type": "subfield", "strength": 0.85},
        {"related_skill": "Machine Learning", "relation_type": "parent_domain", "strength": 0.80},
        {"related_skill": "Python", "relation_type": "implementation_language", "strength": 0.85},
        {"related_skill": "PyTorch", "relation_type": "sibling_framework", "strength": 0.70},
    ],
    "Deep Learning": [
        {"related_skill": "Machine Learning", "relation_type": "parent_domain", "strength": 0.85},
    ],
}


def normalize_skill(raw_name: str) -> dict[str, str]:
    """Normalize a raw skill string to canonical form and category.

    Preserves case-insensitivity, whitespace trimming, and alias resolution.
    If no alias is found, sanitizes whitespace and infers a title-cased name.
    """
    cleaned = re.sub(r"\s+", " ", raw_name.strip())
    lower_key = cleaned.lower()

    if lower_key in ALIAS_TO_CANONICAL:
        canonical = ALIAS_TO_CANONICAL[lower_key]
        category, _ = SKILL_TAXONOMY.get(canonical, ("General", "medium"))
        return {
            "canonical_name": canonical,
            "category": category,
            "raw_name": raw_name,
        }

    # Check direct canonical match ignoring case
    for canonical, (category, _) in SKILL_TAXONOMY.items():
        if canonical.lower() == lower_key:
            return {
                "canonical_name": canonical,
                "category": category,
                "raw_name": raw_name,
            }

    # Unknown / unaliased skill: return cleaned title-cased name
    return {
        "canonical_name": cleaned.title() if len(cleaned) > 3 else cleaned.upper(),
        "category": "General",
        "raw_name": raw_name,
    }


def get_skill_category(name: str) -> str:
    """Return the category for a given skill name."""
    norm = normalize_skill(name)
    return norm["category"]


def get_related_skills(canonical_name: str) -> list[dict[str, Any]]:
    """Return list of transferable/related skills with relationship type and strength.

    Preserves strict distinctions: Java is not JavaScript, React is not Angular,
    AWS is not Azure, SQL is not PostgreSQL.
    """
    # Direct mappings from SKILL_RELATIONSHIPS
    relations = list(SKILL_RELATIONSHIPS.get(canonical_name, []))

    # Also check reverse mappings (if A has B as parent/underlying, B might have weak relation to A)
    for other_skill, other_relations in SKILL_RELATIONSHIPS.items():
        if other_skill == canonical_name:
            continue
        for rel in other_relations:
            if rel["related_skill"] == canonical_name:
                # Add with slightly discounted strength if not already present
                existing = any(r["related_skill"] == other_skill for r in relations)
                if not existing:
                    discounted_strength = round(rel["strength"] * 0.8, 2)
                    relations.append({
                        "related_skill": other_skill,
                        "relation_type": f"inverse_{rel['relation_type']}",
                        "strength": discounted_strength,
                    })

    return relations


def are_skills_related(skill_a: str, skill_b: str) -> tuple[bool, str | None, float]:
    """Check if two skills have a defined transferable relationship.

    Returns: (is_related, relation_note, relationship_strength)
    """
    norm_a = normalize_skill(skill_a)["canonical_name"]
    norm_b = normalize_skill(skill_b)["canonical_name"]

    if norm_a.lower() == norm_b.lower():
        return True, "Identical skill", 1.0

    # Explicit boundaries: Never consider Java and JavaScript related
    incompatible_pairs = {
        ("Java", "JavaScript"),
        ("JavaScript", "Java"),
        ("React", "Angular"),
        ("Angular", "React"),
        ("AWS", "Azure"),
        ("Azure", "AWS"),
        ("AWS", "GCP"),
        ("GCP", "AWS"),
    }
    if (norm_a, norm_b) in incompatible_pairs:
        return False, None, 0.0

    for rel in get_related_skills(norm_a):
        if rel["related_skill"].lower() == norm_b.lower():
            note = f"Related via {rel['relation_type'].replace('_', ' ')} ({norm_a} -> {norm_b})"
            return True, note, rel["strength"]

    return False, None, 0.0


def extract_known_skills_from_text(text: str) -> list[dict[str, str]]:
    """Scan arbitrary text and return detected canonical skills, sorted and deduplicated."""
    found: dict[str, dict[str, str]] = {}

    # Sort aliases by length descending so longer phrases match before substrings
    # (e.g. "machine learning" before "ml", "spring boot" before "spring")
    sorted_aliases = sorted(ALIAS_TO_CANONICAL.keys(), key=len, reverse=True)

    text_lower = f" {text.lower()} "
    matched_spans: list[tuple[int, int]] = []

    for alias in sorted_aliases:
        # Require word boundaries; handle special symbols like c++, c#, .net
        pattern = r"(?<![A-Za-z0-9_])" + re.escape(alias) + r"(?![A-Za-z0-9_])"
        for m in re.finditer(pattern, text_lower):
            start, end = m.span()
            # If this match is contained within an already accepted longer alias span, suppress it
            if any(s_start <= start and end <= s_end for s_start, s_end in matched_spans):
                continue
            matched_spans.append((start, end))
            canonical = ALIAS_TO_CANONICAL[alias]
            if canonical not in found:
                category, _ = SKILL_TAXONOMY.get(canonical, ("General", "medium"))
                found[canonical] = {
                    "name": canonical,
                    "category": category,
                    "raw_mention": alias,
                }

    return list(found.values())
