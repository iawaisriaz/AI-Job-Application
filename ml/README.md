# Local CV / Job Matching ML Pipeline

## 1. Install dependencies

From the Django project root:

```bash
pip install -r requirements-ml.txt
```

## 2. Create your real labelled dataset

File:

```text
dataset/job_match_dataset.csv
```

Required columns:

```text
cv_text,job_description,match_score
```

`match_score` must be a human-labelled value from 0 to 100.

Do not rely on the small CSV included here for a portfolio claim. It is only a development example. For a serious model, create a substantially larger, consistently labelled dataset.

## 3. Train

From the Django project root:

```bash
python ml/train_model.py
```

This creates:

```text
models/job_match_xgb.joblib
models/tfidf_vectorizer.joblib
```

## 4. Django

Replace your analysis app `views.py` with the supplied `views.py`.

The existing URLs can remain unchanged.

The new backend flow is:

CV file
-> text extraction
-> TF-IDF similarity
-> Sentence Transformer semantic similarity
-> skill matching
-> feature vector
-> XGBoost
-> result saved in JobAnalysis
-> result page

## 5. API removal

The old OpenAI/OpenRouter imports, client, API key and `run_ai_analysis()` function are removed from the supplied views.py.

No OpenAI/OpenRouter API key is required by this pipeline.

## Important

The Sentence Transformer model is a pretrained local model. It may download once when first used, then it is cached locally. It is not an API-key-based call.

The XGBoost model is your supervised model. Its quality depends on the quality, size and consistency of your labelled training dataset.
