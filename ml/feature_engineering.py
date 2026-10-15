"""IT-focused CV/job skill extraction and matching (no retraining required)."""
import re
from typing import Dict, List, Tuple

# Canonical skill => aliases. Add aliases here without changing Django code.
SKILL_ALIASES: Dict[str, List[str]] = {
    # Languages
    'Python': ['python'], 'Java': ['java'], 'JavaScript': ['javascript', 'java script', 'js'],
    'TypeScript': ['typescript', 'ts'], 'Dart': ['dart'], 'PHP': ['php'],
    'C++': ['c++', 'cpp'], 'C#': ['c#', 'c sharp', 'csharp'], 'C': ['c language', 'ansi c'],
    'Go': ['golang', 'go language'], 'Rust': ['rust'], 'Ruby': ['ruby'],
    'Kotlin': ['kotlin'], 'Swift': ['swift'], 'Objective-C': ['objective-c'],
    'R': ['r language', 'r programming'], 'Scala': ['scala'], 'SQL': ['sql'],
    'Bash': ['bash', 'shell scripting'], 'PowerShell': ['powershell'],
    # Mobile
    'Flutter': ['flutter', 'flutter sdk'], 'React Native': ['react native', 'react-native'],
    'Android SDK': ['android sdk', 'android development'], 'iOS Development': ['ios development', 'ios developer'],
    'Jetpack Compose': ['jetpack compose'], 'SwiftUI': ['swiftui'],
    'Firebase': ['firebase', 'cloud firestore', 'firebase authentication'],
    'BLoC': ['bloc', 'flutter bloc', 'bloc pattern'], 'Provider': ['provider state management', 'flutter provider'],
    'Riverpod': ['riverpod'], 'GetX': ['getx'], 'State Management': ['state management'],
    # Backend
    'Django': ['django'], 'Django REST Framework': ['django rest framework', 'drf'],
    'Flask': ['flask'], 'FastAPI': ['fastapi'], 'Laravel': ['laravel'],
    'Symfony': ['symfony'], 'CodeIgniter': ['codeigniter'], 'Spring Boot': ['spring boot'],
    'Spring': ['spring framework', 'spring mvc'], 'ASP.NET Core': ['asp.net core', 'asp net core'],
    '.NET': ['.net', 'dotnet'], 'Node.js': ['node.js', 'nodejs', 'node js'],
    'Express.js': ['express.js', 'expressjs', 'express js'], 'NestJS': ['nestjs', 'nest.js'],
    'Ruby on Rails': ['ruby on rails', 'rails framework'], 'GraphQL': ['graphql'],
    'REST APIs': ['rest api', 'restful api', 'restful services', 'rest apis'],
    'Microservices': ['microservices', 'microservice architecture'],
    # Frontend
    'React': ['react', 'reactjs', 'react.js'], 'Next.js': ['next.js', 'nextjs'],
    'Angular': ['angular', 'angularjs'], 'Vue.js': ['vue.js', 'vuejs', 'vue'],
    'Nuxt': ['nuxt', 'nuxtjs'], 'Svelte': ['svelte'],
    'HTML': ['html', 'html5'], 'CSS': ['css', 'css3'], 'Tailwind CSS': ['tailwind', 'tailwindcss', 'tailwind css'],
    'Bootstrap': ['bootstrap'], 'Sass': ['sass', 'scss'], 'Redux': ['redux'],
    # Data stores
    'MySQL': ['mysql'], 'PostgreSQL': ['postgresql', 'postgres'],
    'Oracle Database': ['oracle database', 'oracle db', 'oracle sql', 'oracle 19c', 'oracle 21c'],
    'Oracle PL/SQL': ['pl/sql', 'plsql'], 'SQL Server': ['sql server', 'mssql', 'microsoft sql server'],
    'SQLite': ['sqlite', 'sqlite3'], 'MongoDB': ['mongodb', 'mongo db'],
    'Redis': ['redis'], 'Elasticsearch': ['elasticsearch', 'elastic search'],
    'MariaDB': ['mariadb'], 'DynamoDB': ['dynamodb'], 'Firestore': ['firestore'],
    # DevOps/cloud
    'AWS': ['aws', 'amazon web services'], 'Azure': ['azure', 'microsoft azure'],
    'Google Cloud': ['gcp', 'google cloud', 'google cloud platform'],
    'Docker': ['docker'], 'Kubernetes': ['kubernetes', 'k8s'],
    'Terraform': ['terraform'], 'Jenkins': ['jenkins'], 'GitHub Actions': ['github actions'],
    'CI/CD': ['ci/cd', 'continuous integration', 'continuous delivery'],
    'Git': ['git', 'git version control'], 'GitHub': ['github'], 'GitLab': ['gitlab'],
    'Linux': ['linux'], 'Nginx': ['nginx'], 'Apache Kafka': ['kafka', 'apache kafka'],
    'RabbitMQ': ['rabbitmq'],
    # Testing and methods
    'Unit Testing': ['unit testing', 'unit tests', 'unittest'],
    'Integration Testing': ['integration testing', 'integration tests'],
    'Pytest': ['pytest'], 'Selenium': ['selenium'], 'Cypress': ['cypress'],
    'Playwright': ['playwright'], 'JUnit': ['junit'], 'Postman': ['postman'],
    'Test-Driven Development': ['tdd', 'test driven development', 'test-driven development'],
    'Agile': ['agile'], 'Scrum': ['scrum'], 'Jira': ['jira'],
    'Object-Oriented Programming': ['oop', 'object oriented programming', 'object-oriented programming'],
    'Data Structures': ['data structures', 'dsa'], 'System Design': ['system design'],
    'Design Patterns': ['design patterns'], 'Clean Architecture': ['clean architecture'],
    # ML/data/security
    'Machine Learning': ['machine learning'], 'Deep Learning': ['deep learning'],
    'NLP': ['nlp', 'natural language processing'], 'Computer Vision': ['computer vision'],
    'PyTorch': ['pytorch'], 'TensorFlow': ['tensorflow'], 'Scikit-learn': ['scikit-learn', 'sklearn'],
    'XGBoost': ['xgboost'], 'Pandas': ['pandas'], 'NumPy': ['numpy'],
    'Power BI': ['power bi'], 'Tableau': ['tableau'], 'Apache Spark': ['apache spark', 'pyspark'],
    'Cybersecurity': ['cybersecurity', 'cyber security'], 'Penetration Testing': ['penetration testing', 'pentesting'],
    'OWASP': ['owasp'], 'OAuth': ['oauth', 'oauth2'], 'JWT': ['jwt', 'json web token'],
    # Common workplace skills
    'Communication': ['communication skills', 'communication'],
    'Teamwork': ['teamwork', 'team working', 'collaboration'],
    'Problem Solving': ['problem solving', 'problem-solving'],
    'Leadership': ['leadership'], 'Time Management': ['time management'],
}

ROLE_ALIASES: Dict[str, List[str]] = {
    'mobile_development': ['flutter developer', 'dart developer', 'mobile app developer', 'mobile developer',
                           'android developer', 'ios developer', 'react native developer'],
    'frontend_development': ['frontend developer', 'front end developer', 'frontend engineer', 'react developer',
                             'angular developer', 'vue developer', 'ui developer'],
    'backend_development': ['backend developer', 'back end developer', 'backend engineer', 'django developer',
                            'laravel developer', 'php developer', 'python developer', 'node developer',
                            'java developer', 'spring boot developer', '.net developer'],
    'fullstack_development': ['full stack developer', 'full-stack developer', 'fullstack developer', 'web developer'],
    'software_engineering': ['software engineer', 'software developer', 'software engineering'],
    'database_development': ['database developer', 'database administrator', 'dba', 'oracle developer', 'sql developer'],
    'data_analysis': ['data analyst', 'business intelligence analyst', 'bi developer'],
    'data_science': ['data scientist'],
    'machine_learning': ['machine learning engineer', 'ml engineer', 'ai engineer', 'nlp engineer'],
    'devops': ['devops engineer', 'site reliability engineer', 'sre', 'platform engineer'],
    'cloud': ['cloud engineer', 'cloud architect'],
    'qa': ['qa engineer', 'qa tester', 'test automation engineer', 'software tester'],
    'security': ['cybersecurity analyst', 'security engineer', 'penetration tester'],
}

# Role is not a mandatory exact match: 'software engineer' and 'Flutter developer' may both be relevant.

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').replace('\x00', ' ')).strip()


def _contains(text: str, alias: str) -> bool:
    """Match complete terms, not substrings: 'java' must not match 'javascript'."""
    return bool(re.search(r'(?<![\w])' + re.escape(alias.lower()) + r'(?![\w])', text))


def extract_skills(text: str) -> List[str]:
    normalized = clean_text(text).lower()
    return sorted([name for name, aliases in SKILL_ALIASES.items()
                   if any(_contains(normalized, a) for a in aliases)], key=str.casefold)


def detect_roles(text: str) -> List[str]:
    normalized = clean_text(text).lower()
    return sorted([role for role, aliases in ROLE_ALIASES.items()
                   if any(_contains(normalized, a) for a in aliases)])


def skill_match_features(cv_text: str, job_text: str) -> Tuple[float, float, float, List[str], List[str]]:
    cv_skills, job_skills = set(extract_skills(cv_text)), set(extract_skills(job_text))
    if not job_skills:
        return 0.0, 0.0, 0.0, [], []
    matched, missing = sorted(cv_skills & job_skills), sorted(job_skills - cv_skills)
    ratio = len(matched) / len(job_skills)
    return ratio, len(missing) / len(job_skills), ratio, matched, missing


def role_match_score(cv_text: str, job_text: str) -> float:
    cv_roles, job_roles = set(detect_roles(cv_text)), set(detect_roles(job_text))
    if not job_roles or not cv_roles:
        return 0.5  # unknown, not a confirmed mismatch
    if cv_roles & job_roles:
        return 1.0
    # Different but related software roles are not necessarily incompatible.
    return 0.5
