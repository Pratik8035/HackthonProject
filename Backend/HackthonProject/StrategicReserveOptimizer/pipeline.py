"""
Strategic Reserve Optimization Agent
Master Pipeline

Orchestrates the complete end-to-end workflow:
1. Data generation
2. Preprocessing
3. Feature engineering
4. Model training
5. Scenario optimization
6. Report generation

Usage:
  python pipeline.py                  # Full pipeline
  python pipeline.py --skip-lstm      # Skip LSTM training
  python pipeline.py --skip-training  # Skip ML training, run optimization only
  python pipeline.py --data-only      # Only generate data

Author: Strategic Reserve Optimization Team
Date: 2025
"""

import argparse
import logging
import sys
import json
import time
from pathlib import Path

import io

# Force UTF-8 encoding for stdout on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log", mode="w", encoding="utf-8"),
    ]
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


def run_pipeline(
    skip_lstm: bool = False,
    skip_prophet: bool = False,
    skip_training: bool = False,
    data_only: bool = False,
):
    """Run the complete Strategic Reserve Optimization pipeline."""
    
    start_time = time.time()
    
    logger.info("+==============================================================+")
    logger.info("|    STRATEGIC RESERVE OPTIMIZATION AGENT - FULL PIPELINE     |")
    logger.info("|    India Energy Security | AI-Powered SPR Management        |")
    logger.info("+==============================================================+")
    
    pipeline_status = {}
    
    # --- PHASE 1: Data Generation -----------------------------------------
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1: Data Generation")
    logger.info("=" * 60)
    
    try:
        from src.data.data_generator import run_all_generators
        run_all_generators()
        pipeline_status["data_generation"] = "OK SUCCESS"
        logger.info("Phase 1 COMPLETE OK")
    except Exception as e:
        logger.error(f"Phase 1 FAILED: {e}")
        pipeline_status["data_generation"] = f"X FAILED: {e}"
        raise
    
    if data_only:
        logger.info("\nData-only mode: stopping after data generation.")
        return pipeline_status
    
    # --- PHASE 2: Preprocessing -------------------------------------------
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: Data Preprocessing")
    logger.info("=" * 60)
    
    try:
        from src.data.preprocessor import preprocess_pipeline
        master_df = preprocess_pipeline()
        pipeline_status["preprocessing"] = "OK SUCCESS"
        logger.info("Phase 2 COMPLETE OK")
    except Exception as e:
        logger.error(f"Phase 2 FAILED: {e}")
        pipeline_status["preprocessing"] = f"X FAILED: {e}"
        raise
    
    # --- PHASE 3: Feature Engineering ------------------------------------
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 3: Feature Engineering")
    logger.info("=" * 60)
    
    try:
        from src.features.feature_engineering import run_feature_engineering
        features_df = run_feature_engineering()
        pipeline_status["feature_engineering"] = "OK SUCCESS"
        logger.info("Phase 3 COMPLETE OK")
    except Exception as e:
        logger.error(f"Phase 3 FAILED: {e}")
        pipeline_status["feature_engineering"] = f"X FAILED: {e}"
        raise
    
    # --- PHASE 4: Model Training ------------------------------------------
    if not skip_training:
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 4: ML Model Training (6 Models)")
        logger.info("=" * 60)
        
        try:
            from src.models.model_trainer import run_all_models
            model_results = run_all_models(
                skip_lstm=skip_lstm,
                skip_prophet=skip_prophet
            )
            pipeline_status["model_training"] = "OK SUCCESS"
            logger.info("Phase 4 COMPLETE OK")
        except Exception as e:
            logger.error(f"Phase 4 FAILED: {e}")
            pipeline_status["model_training"] = f"X FAILED: {e}"
            logger.warning("Continuing with optimization despite training failure...")
    else:
        logger.info("\nPhase 4: ML Training SKIPPED (--skip-training flag)")
        pipeline_status["model_training"] = "SKIPPED"
    
    # --- PHASE 5: Optimization & Scenarios -------------------------------
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 5: Strategic Reserve Optimization (4 Scenarios)")
    logger.info("=" * 60)
    
    try:
        from src.scenarios.scenario_engine import run_all_scenarios
        scenario_results = run_all_scenarios()
        pipeline_status["optimization"] = "OK SUCCESS"
        logger.info("Phase 5 COMPLETE OK")
    except Exception as e:
        logger.error(f"Phase 5 FAILED: {e}")
        pipeline_status["optimization"] = f"X FAILED: {e}"
        raise
    
    # --- PHASE 6: Summary Report ------------------------------------------
    elapsed = time.time() - start_time
    
    logger.info("\n+==============================================================+")
    logger.info("|                    PIPELINE COMPLETE                        |")
    logger.info(f"|    Total time: {elapsed/60:.1f} minutes                            |")
    logger.info("+==============================================================+")
    
    logger.info("\nPIPELINE STATUS:")
    for step, status in pipeline_status.items():
        logger.info(f"  {step:30s} {status}")
    
    logger.info("\nOUTPUT LOCATIONS:")
    logger.info(f"  Data (raw):          {BASE_DIR}/data/raw/")
    logger.info(f"  Data (processed):    {BASE_DIR}/data/processed/")
    logger.info(f"  Trained models:      {BASE_DIR}/models/")
    logger.info(f"  Scenario results:    {BASE_DIR}/outputs/scenarios/")
    logger.info(f"  Model metrics:       {BASE_DIR}/outputs/metrics/")
    
    logger.info("\nNEXT STEPS:")
    logger.info("  Launch dashboard:  streamlit run app/streamlit_app.py")
    
    # Save pipeline summary
    summary = {
        "pipeline_status": pipeline_status,
        "elapsed_seconds": round(elapsed, 1),
        "datasets_generated": 12,
        "models_trained": 6 - (1 if skip_lstm else 0) - (1 if skip_prophet else 0),
        "scenarios_tested": 4,
    }
    
    with open(BASE_DIR / "outputs" / "pipeline_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    return pipeline_status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Strategic Reserve Optimization Agent - Master Pipeline"
    )
    parser.add_argument("--skip-lstm", action="store_true",
                        help="Skip LSTM model training (faster)")
    parser.add_argument("--skip-prophet", action="store_true",
                        help="Skip Prophet model training")
    parser.add_argument("--skip-training", action="store_true",
                        help="Skip all ML training")
    parser.add_argument("--data-only", action="store_true",
                        help="Only generate data, skip everything else")
    
    args = parser.parse_args()
    
    try:
        run_pipeline(
            skip_lstm=args.skip_lstm,
            skip_prophet=args.skip_prophet,
            skip_training=args.skip_training,
            data_only=args.data_only,
        )
    except Exception as e:
        logger.critical(f"Pipeline failed with error: {e}")
        sys.exit(1)
