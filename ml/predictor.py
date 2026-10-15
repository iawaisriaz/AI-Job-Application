"""Local, explainable IT CV matcher. Keeps predict_match() contract used by Django views.

This is a heuristic portfolio score, NOT a calibrated hiring probability.
It deliberately does not load the previously trained IT-specific XGBoost model,
because changing its feature definitions without retraining invalidates it.
"""
from functools import lru_cache
import re

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .feature_engineering import clean_text, detect_roles, extract_skills, skill_match_features

MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'


@lru_cache(maxsize=1)
def _model():
    return SentenceTransformer(MODEL_NAME, device='cpu')


def _chunks(text: str, max_words: int = 160, max_chunks: int = 16):
    """Use several shorter passages so long CVs are not silently truncated."""
    words = clean_text(text).split()
    if not words:
        return []
    return [' '.join(words[i:i + max_words]) for i in range(0, min(len(words), max_words * max_chunks), max_words)]


def _semantic_score(cv_text: str, job_text: str) -> float:
    cv_parts, job_parts = _chunks(cv_text), _chunks(job_text, max_chunks=8)
    if not cv_parts or not job_parts:
        return 0.0
    model = _model()
    cv_vectors = model.encode(cv_parts, normalize_embeddings=True, show_progress_bar=False)
    job_vectors = model.encode(job_parts, normalize_embeddings=True, show_progress_bar=False)
    sims = np.asarray(cv_vectors) @ np.asarray(job_vectors).T
    # Each job passage is compared to the most relevant CV passage.
    return float(np.clip(np.mean(np.max(sims, axis=0)), 0, 1))


def _tfidf_score(cv_text: str, job_text: str) -> float:
    try:
        matrix = TfidfVectorizer(stop_words='english', ngram_range=(1, 2)).fit_transform([cv_text, job_text])
        return float(cosine_similarity(matrix[0:1], matrix[1:2])[0, 0])
    except ValueError:
        return 0.0


def _label_for_score(score: int) -> str:
    if score >= 80:
        return 'Strong Match'
    if score >= 65:
        return 'Good Match'
    if score >= 50:
        return 'Moderate Match'
    return 'Low Match'


def predict_match(cv_text: str, job_text: str) -> dict:
    cv_text, job_text = clean_text(cv_text), clean_text(job_text)
    if not cv_text or not job_text:
        raise ValueError('CV text and job description are required for analysis.')

    cv_skills = extract_skills(cv_text)
    job_skills = extract_skills(job_text)
    skill_ratio, missing_ratio, _, matched, missing = skill_match_features(cv_text, job_text)
    semantic = _semantic_score(cv_text, job_text)
    tfidf = _tfidf_score(cv_text, job_text)
    cv_roles, job_roles = detect_roles(cv_text), detect_roles(job_text)

    # 60% semantic relevance, 30% evidence of listed technical skills, 10% terms.
    # When job skills cannot be extracted, avoid treating zero detections as zero fit.
    if job_skills:
        raw_score = 100 * (0.60 * semantic + 0.30 * skill_ratio + 0.10 * tfidf)
    else:
        raw_score = 100 * (0.85 * semantic + 0.15 * tfidf)
    score = int(round(min(95, max(0, raw_score))))

    strengths = []
    if matched:
        strengths.append('CV mentions these job-related skills: ' + ', '.join(matched[:8]) + '.')
    if semantic >= 0.65:
        strengths.append('CV experience is semantically relevant to the job description.')
    if tfidf >= 0.35:
        strengths.append('CV uses several terms also found in the job description.')
    if not strengths:
        strengths.append('Limited direct evidence of alignment was found in the supplied CV text.')

    weak_areas = []
    if missing:
        weak_areas.append('Not evidenced in the CV text: ' + ', '.join(missing[:8]) + '.')
        weak_areas.append('If you have these skills, add specific projects or experience demonstrating them.')
    elif job_skills:
        weak_areas.append('All detected job skills appear in the CV; experience level and other requirements still need review.')
    else:
        weak_areas.append('No skills from the current IT vocabulary were detected in the job description; review requirements manually.')
    if semantic < 0.55:
        weak_areas.append('Explain relevant responsibilities, outcomes and projects more clearly in your CV.')

    detailed = (
        f'Estimated CV/job alignment: {score}% ({_label_for_score(score)}). '
        f'Semantic similarity: {semantic:.0%}; keyword similarity: {tfidf:.0%}. '
        + (f'Detected job skills: {len(job_skills)}; matched: {len(matched)}; '
           f'not evidenced: {len(missing)}. ' if job_skills else 'No known job skills detected. ')
        + 'This is an explainable portfolio heuristic, not a hiring probability. '
          'A missing skill means it was not found in the CV text, not that the candidate lacks it.'
    )
    meta = {
        'semantic_similarity': round(semantic, 4),
        'tfidf_similarity': round(tfidf, 4),
        'skill_match_ratio': round(skill_ratio, 4) if job_skills else None,
        'missing_skill_ratio': round(missing_ratio, 4) if job_skills else None,
        'matched_skills': matched,
        'missing_skills': missing,
        'cv_roles': cv_roles,
        'job_roles': job_roles,
        'scoring_method': 'heuristic_v2',
    }
    return {
        'match_score': score,
        'match_label': _label_for_score(score),
        'matched_skills': matched,
        'missing_skills': missing,
        'strengths': strengths[:5],
        'weak_areas': weak_areas[:5],
        'detailed_analysis': detailed,
        'features': meta,
    }
