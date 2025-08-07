"""Main entry point for data processing and translation."""

import argparse
from pathlib import Path
from loguru import logger

from .translator import DigimonTranslator
from ..utils.config import config


def main():
    """Process and translate Digimon data."""
    parser = argparse.ArgumentParser(description="Process and translate Digimon data")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/processed/digimon",
        help="Directory containing parsed Digimon JSON files"
    )
    parser.add_argument(
        "--output-dir", 
        type=str,
        default="data/translated",
        help="Directory to save translated files"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode - only process first 5 files"
    )
    args = parser.parse_args()
    
    logger.info("Starting Digimon data translation")
    logger.info(f"Input directory: {args.input_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    
    # Initialize translator
    translator = DigimonTranslator()
    
    # Get input files
    input_path = Path(args.input_dir)
    if not input_path.exists():
        logger.error(f"Input directory not found: {input_path}")
        return
        
    if args.test:
        # In test mode, create a small test set
        all_files = list(input_path.glob("*.json"))
        all_files = [f for f in all_files if not f.name.startswith("_")][:5]
        
        # Create test directory
        test_input = Path("data/test_translation")
        test_input.mkdir(exist_ok=True)
        
        # Copy test files
        import shutil
        for f in all_files:
            shutil.copy(f, test_input / f.name)
            
        logger.info(f"Test mode: Processing {len(all_files)} files")
        stats = translator.process_all_digimon(test_input, Path(args.output_dir) / "test")
    else:
        # Process all files
        stats = translator.process_all_digimon(Path(args.input_dir), Path(args.output_dir))
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Translation complete!")
    logger.info(f"Total files: {stats['total']}")
    logger.info(f"Successfully translated: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Skipped (already translated): {stats['skipped']}")
    logger.info("=" * 60)
    

if __name__ == "__main__":
    main()