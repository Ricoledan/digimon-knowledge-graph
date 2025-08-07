"""Parse Digimon HTML pages to extract structured data."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from ..utils.config import config
from ..utils.file_utils import ensure_directory


class DigimonParser:
    """Parser for Digimon detail pages."""
    
    def __init__(self):
        """Initialize parser."""
        self.html_dir = Path(config.get("paths.raw_html"))
        self.output_dir = Path(config.get("paths.processed_data"))
        ensure_directory(self.output_dir)
        
        # Field mappings (Japanese to English keys)
        self.field_mappings = {
            "レベル": "level",
            "タイプ": "type",
            "属性": "attribute",
            "必殺技": "special_moves",
            "プロフィール": "profile"
        }
        
    def parse_html_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single HTML file and extract Digimon data.
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            Dictionary with extracted data or None if parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extract directory name from filename
            directory_name = file_path.stem
            
            # Initialize data structure
            data = {
                "directory_name": directory_name,
                "source_file": file_path.name,
                "names": {},
                "info": {},
                "profile": {},
                "special_moves": [],
                "related_digimon": [],
                "images": {}
            }
            
            # 1. Extract names
            japanese_name_elem = soup.select_one('.c-titleSet__main')
            if japanese_name_elem:
                data["names"]["japanese"] = japanese_name_elem.text.strip()
                
            english_name_elem = soup.select_one('.c-titleSet__sub')
            if english_name_elem:
                data["names"]["english"] = english_name_elem.text.strip()
                
            # 2. Extract main image
            main_img = soup.select_one('.p-ref__picitem img')
            if main_img and main_img.get('src'):
                data["images"]["main"] = main_img['src']
                
            # 3. Extract info fields (level, type, attribute, moves)
            info_section = soup.select('.p-ref__info dl')
            
            for dl in info_section:
                dt = dl.find('dt', class_='c-txtStrong_A')
                dd = dl.find('dd')
                
                if dt and dd:
                    field_name = dt.text.strip()
                    field_value = dd.text.strip()
                    
                    # Special handling for moves
                    if field_name == "必殺技":
                        # Split moves by line breaks or bullets
                        moves_html = str(dd)
                        # Replace <br> tags with newlines
                        moves_text = moves_html.replace('<br/>', '\n').replace('<br>', '\n')
                        # Parse again to get text
                        moves_soup = BeautifulSoup(moves_text, 'html.parser')
                        moves = moves_soup.text.strip().split('\n')
                        
                        # Clean up moves
                        cleaned_moves = []
                        for move in moves:
                            move = move.strip()
                            # Remove bullet points
                            if move.startswith('・'):
                                move = move[1:].strip()
                            if move:
                                cleaned_moves.append(move)
                                
                        data["special_moves"] = cleaned_moves
                    else:
                        # Map to English key if available
                        english_key = self.field_mappings.get(field_name, field_name)
                        data["info"][english_key] = field_value
                        # Also keep Japanese key
                        data["info"][f"{english_key}_jp"] = field_name
                        
            # 4. Extract profile
            profile_elem = soup.select_one('.p-ref__txt.-txtProfile')
            if profile_elem:
                data["profile"]["japanese"] = profile_elem.text.strip()
                
            # 5. Extract related Digimon
            related_section = soup.select('.p-refRelationList')
            
            for item in related_section:
                link = item.select_one('.p-refRelationList__content')
                name_elem = item.select_one('.p-refRelationList__name')
                type_elem = item.select_one('.p-refRelationList__type')
                
                if link and name_elem:
                    href = link.get('href', '')
                    # Extract directory_name from href
                    if 'directory_name=' in href:
                        related_dir_name = href.split('directory_name=')[-1]
                    else:
                        related_dir_name = None
                        
                    related_data = {
                        "name": name_elem.text.strip(),
                        "directory_name": related_dir_name,
                        "type_info": type_elem.text.strip() if type_elem else None
                    }
                    
                    data["related_digimon"].append(related_data)
                    
            # 6. Add metadata
            data["metadata"] = {
                "parsed_at": str(Path(file_path).stat().st_mtime),
                "parser_version": "1.0"
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None
            
    def parse_all_files(self) -> Dict[str, Any]:
        """Parse all HTML files in the raw HTML directory.
        
        Returns:
            Summary of parsing results
        """
        # Find all HTML files (excluding special files starting with _)
        html_files = list(self.html_dir.glob("*.html"))
        html_files = [f for f in html_files if not f.name.startswith("_")]
        
        logger.info(f"Found {len(html_files)} HTML files to parse")
        
        if not html_files:
            logger.error("No HTML files found to parse!")
            return {"total": 0, "success": 0, "failed": 0}
            
        successful = 0
        failed = 0
        failed_files = []
        
        # Parse each file with progress bar
        with tqdm(total=len(html_files), desc="Parsing HTML files", unit="files") as pbar:
            for html_file in html_files:
                # Update progress bar with current file
                pbar.set_postfix({"current": html_file.stem[:20]})
                
                # Parse the file
                data = self.parse_html_file(html_file)
                
                if data:
                    # Save to JSON file
                    output_file = self.output_dir / f"{data['directory_name']}.json"
                    
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        successful += 1
                    except Exception as e:
                        logger.error(f"Error saving {output_file}: {e}")
                        failed += 1
                        failed_files.append((str(html_file), str(e)))
                else:
                    failed += 1
                    failed_files.append((str(html_file), "Parsing returned None"))
                    
                pbar.update(1)
                
        # Create summary
        summary = {
            "total": len(html_files),
            "successful": successful,
            "failed": failed,
            "failed_files": failed_files,
            "output_directory": str(self.output_dir)
        }
        
        # Save summary
        summary_file = self.output_dir / "_parsing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
            
        # Log results
        logger.info("="*60)
        logger.info(f"Parsing complete!")
        logger.info(f"Total files: {summary['total']}")
        logger.info(f"Successfully parsed: {summary['successful']} ({summary['successful']/summary['total']*100:.1f}%)")
        logger.info(f"Failed: {summary['failed']}")
        
        if failed > 0:
            logger.warning("Failed files:")
            for file_path, error in failed_files[:10]:  # Show first 10
                logger.warning(f"  - {Path(file_path).name}: {error}")
                
        logger.info(f"Output saved to: {self.output_dir}")
        logger.info("="*60)
        
        return summary
        
    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate extracted data for completeness.
        
        Args:
            data: Extracted Digimon data
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        # Check required fields
        if not data.get("names", {}).get("japanese"):
            warnings.append("Missing Japanese name")
            
        if not data.get("info", {}).get("level"):
            warnings.append("Missing level information")
            
        if not data.get("info", {}).get("type"):
            warnings.append("Missing type information")
            
        if not data.get("special_moves"):
            warnings.append("No special moves found")
            
        if not data.get("profile", {}).get("japanese"):
            warnings.append("Missing profile text")
            
        return warnings