from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from xgboost import XGBRegressor

from feature_engineering import build_features


BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    BASE_DIR
    / "dataset"
    / "job_match_dataset.csv"
)

MODEL_DIR = BASE_DIR / "models"

MODEL_DIR.mkdir(
    exist_ok=True
)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def main():

    print("\nLoading dataset...")

    if not DATASET_PATH.exists():

        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    df = pd.read_csv(
        DATASET_PATH
    )

    required = {
        "cv_text",
        "job_description",
        "match_score",
    }

    missing = required.difference(
        df.columns
    )

    if missing:

        raise ValueError(
            "Missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    df = df.dropna(
        subset=[
            "cv_text",
            "job_description",
            "match_score",
        ]
    ).copy()

    df["match_score"] = pd.to_numeric(
        df["match_score"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["match_score"]
    )

    df["match_score"] = df[
        "match_score"
    ].clip(0, 100)

    print(
        f"Training examples: {len(df)}"
    )

    # --------------------------------------------------------
    # TF-IDF
    # --------------------------------------------------------

    corpus = (
        df["cv_text"]
        .astype(str)
        .tolist()
        +
        df["job_description"]
        .astype(str)
        .tolist()
    )

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=8000,
    )

    vectorizer.fit(
        corpus
    )

    print(
        "Loading embedding model..."
    )

    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )

    # --------------------------------------------------------
    # FEATURE CREATION
    # --------------------------------------------------------

    X = []
    y = []

    total = len(df)

    for counter, (_, row) in enumerate(
        df.iterrows(),
        start=1
    ):

        if counter % 500 == 0:

            print(
                f"Processed {counter}/{total}"
            )

        features, _ = build_features(
            str(row["cv_text"]),
            str(row["job_description"]),
            vectorizer,
            embedding_model,
        )

        X.append(
            features[0]
        )

        y.append(
            float(row["match_score"])
        )

    X = np.asarray(
        X,
        dtype=np.float32
    )

    y = np.asarray(
        y,
        dtype=np.float32
    )

    print(
        "\nFeature matrix:",
        X.shape
    )

    # --------------------------------------------------------
    # TRAIN / TEST
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
    )

    model = XGBRegressor(

        n_estimators=400,

        max_depth=5,

        learning_rate=0.04,

        subsample=0.85,

        colsample_bytree=0.90,

        min_child_weight=3,

        objective="reg:squarederror",

        random_state=42,
    )

    print(
        "\nTraining XGBoost..."
    )

    model.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------------
    # EVALUATION
    # --------------------------------------------------------

    predictions = np.clip(
        model.predict(X_test),
        0,
        100,
    )

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    r2 = r2_score(
        y_test,
        predictions
    )

    print(
        "\n=============================="
    )

    print(
        "MODEL EVALUATION"
    )

    print(
        "=============================="
    )

    print(
        f"MAE  : {mae:.2f}"
    )

    print(
        f"RMSE : {rmse:.2f}"
    )

    print(
        f"R2   : {r2:.3f}"
    )

    # --------------------------------------------------------
    # FEATURE IMPORTANCE
    # --------------------------------------------------------

    feature_names = [

        "tfidf_similarity",

        "semantic_similarity",

        "skill_match_ratio",

        "missing_skill_ratio",

        "text_coverage",

        "role_match_score",

        "skill_quality",
    ]

    print(
        "\nFeature importance:"
    )

    for name, importance in zip(
        feature_names,
        model.feature_importances_
    ):

        print(
            f"{name:25s}: "
            f"{importance:.4f}"
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    joblib.dump(
        model,
        MODEL_DIR
        / "job_match_xgb.joblib"
    )

    joblib.dump(
        vectorizer,
        MODEL_DIR
        / "tfidf_vectorizer.joblib"
    )

    print(
        "\nModels saved successfully."
    )

    print(
        MODEL_DIR
        / "job_match_xgb.joblib"
    )

    print(
        MODEL_DIR
        / "tfidf_vectorizer.joblib"
    )


if __name__ == "__main__":
    main()