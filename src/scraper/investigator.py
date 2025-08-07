"""Investigate HTML structure of Digimon pages to determine selectors."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
from collections import Counter
from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from loguru import logger

from ..utils.config import config


class StructureInvestigator:
    """Investigate and analyze HTML structure of Digimon pages."""
    
    def __init__(self):
        """Initialize investigator."""
        self.base_url = config.get("scraping.base_url")
        self.index_url = "https://digimon.net/reference/index.php"
        self.headers = {
            "User-Agent": config.get("scraping.user_agent"),
            "Accept-Language": "ja,en;q=0.9"
        }
        
    def fetch_sample_page(self, url: Optional[str] = None) -> Optional[BeautifulSoup]:
        """Fetch a sample page for investigation."""
        if not url:
            # Try to fetch index first to get a sample URL
            url = self.index_url
            
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'lxml')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
            
    def find_digimon_links(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Find all possible Digimon detail page links."""
        found_links = {}
        
        # Try various selectors - prioritize Digimon-specific patterns
        selectors = [
            ('a[href*="detail.php?directory_name="]', 'Direct Digimon detail links'),
            ('.c-digimonList a[href]', 'Links in .c-digimonList'),
            ('a[href*="/reference/detail"]', 'Links containing /reference/detail'),
            ('.digimon-list a', 'Links inside .digimon-list'),
            ('.l-content a[href]', 'Links in .l-content'),
            ('main a[href]', 'All links in main content'),
            ('.content a[href]', 'All links in .content'),
            ('article a[href]', 'Links in article'),
            ('ul li a[href]', 'Links in list items'),
        ]
        
        for selector, description in selectors:
            links = soup.select(selector)
            if links:
                # Filter out navigation and non-digimon links
                digimon_links = []
                for link in links:
                    href = link.get('href', '')
                    # Skip common navigation patterns and external sites
                    if any(skip in href.lower() for skip in ['#', 'javascript:', '.css', '.js', '/news/', '/about/', 'privacy', 'bandai.co.jp', 'policy', '/history/', '/product/', '/anime']):
                        continue
                    # Look for potential digimon detail patterns
                    if 'detail.php?directory_name=' in href:
                        digimon_links.append(self._normalize_url(href))
                    elif any(pattern in href.lower() for pattern in ['/detail/', 'digimon']) and 'digimon.net' in self._normalize_url(href):
                        digimon_links.append(self._normalize_url(href))
                        
                if digimon_links:
                    found_links[description] = digimon_links[:10]  # First 10 as examples
                    logger.info(f"Found {len(digimon_links)} potential Digimon links with selector '{selector}'")
                
        return found_links
        
    def analyze_detail_page(self, url: str) -> Dict[str, Any]:
        """Analyze a Digimon detail page structure in detail."""
        soup = self.fetch_sample_page(url)
        if not soup:
            return {}
            
        analysis = {
            "url": url,
            "page_structure": self._analyze_page_structure(soup),
            "title_elements": self._analyze_titles(soup),
            "data_sections": self._analyze_data_sections(soup),
            "image_elements": self._analyze_images(soup),
            "evolution_info": self._analyze_evolution_sections(soup),
            "move_info": self._analyze_moves(soup),
            "profile_info": self._analyze_profile(soup),
            "metadata": self._extract_metadata(soup, url)
        }
        
        return analysis
    
    def _analyze_page_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze overall page structure."""
        structure = {
            "has_main_tag": bool(soup.find('main')),
            "has_article_tag": bool(soup.find('article')),
            "main_containers": [],
            "content_hierarchy": []
        }
        
        # Find main content containers
        container_selectors = [
            '.l-content', '.content', '.main-content', 
            '.c-content', 'main', 'article', '#content'
        ]
        
        for selector in container_selectors:
            containers = soup.select(selector)
            if containers:
                structure["main_containers"].append({
                    "selector": selector,
                    "count": len(containers),
                    "classes": containers[0].get('class', []) if containers else []
                })
                
        # Analyze heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        for h in headings[:10]:  # First 10 headings
            structure["content_hierarchy"].append({
                "tag": h.name,
                "text": h.get_text(strip=True),
                "classes": h.get('class', []),
                "parent_classes": h.parent.get('class', []) if h.parent else []
            })
            
        return structure
    
    def _analyze_titles(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze title and name elements."""
        titles = {}
        
        # Extended title selectors
        title_selectors = [
            ('.c-titleSet__main', 'Main title (Japanese)'),
            ('.c-titleSet__sub', 'Subtitle (possibly English)'),
            ('h1', 'H1 heading'),
            ('h2', 'H2 heading'),
            ('.digimon-name', 'Digimon name class'),
            ('.title', 'Generic title class'),
            ('.name', 'Generic name class'),
            ('.c-digimon__name', 'Specific digimon name'),
            ('[class*="name"]', 'Any class containing "name"'),
            ('[class*="title"]', 'Any class containing "title"'),
        ]
        
        for selector, description in title_selectors:
            elements = soup.select(selector)
            if elements:
                elem = elements[0]
                text = elem.get_text(strip=True)
                titles[selector] = {
                    "description": description,
                    "text": text,
                    "is_english": self._is_english(text),
                    "contains_katakana": self._contains_katakana(text),
                    "parent_tag": elem.parent.name if elem.parent else None,
                    "siblings_count": len(list(elem.parent.children)) if elem.parent else 0
                }
                
        return titles
    
    def _analyze_data_sections(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze structured data sections."""
        data = {
            "definition_lists": [],
            "tables": [],
            "key_value_pairs": [],
            "info_boxes": []
        }
        
        # Analyze definition lists
        for dl in soup.find_all('dl'):
            dl_data = {
                "classes": dl.get('class', []),
                "items": []
            }
            for dt, dd in zip(dl.find_all('dt'), dl.find_all('dd')):
                key = dt.get_text(strip=True)
                value = dd.get_text(strip=True)
                dl_data["items"].append({
                    "key": key,
                    "value": value,
                    "key_translation": self._translate_common_terms(key)
                })
            if dl_data["items"]:
                data["definition_lists"].append(dl_data)
                
        # Analyze tables
        for table in soup.find_all('table'):
            table_data = {
                "classes": table.get('class', []),
                "headers": [],
                "sample_rows": []
            }
            # Get headers
            headers = table.find_all('th')
            table_data["headers"] = [h.get_text(strip=True) for h in headers]
            
            # Get sample rows
            rows = table.find_all('tr')[:3]  # First 3 rows
            for row in rows:
                cells = row.find_all(['td', 'th'])
                table_data["sample_rows"].append([cell.get_text(strip=True) for cell in cells])
                
            if table_data["headers"] or table_data["sample_rows"]:
                data["tables"].append(table_data)
                
        # Look for info boxes or data containers
        info_selectors = [
            '.infobox', '.info-box', '.data-box',
            '.c-digimon__info', '.digimon-info',
            '[class*="info"]', '[class*="data"]'
        ]
        
        for selector in info_selectors:
            boxes = soup.select(selector)
            for box in boxes[:2]:  # First 2 of each type
                box_data = {
                    "selector": selector,
                    "classes": box.get('class', []),
                    "text_preview": box.get_text(strip=True)[:200],
                    "child_elements": [child.name for child in box.children if hasattr(child, 'name')]
                }
                data["info_boxes"].append(box_data)
                
        return data
    
    def _analyze_evolution_sections(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Look for evolution-related sections."""
        evolution = {
            "found_sections": [],
            "evolution_keywords": []
        }
        
        # Japanese evolution terms
        evolution_terms = [
            '進化', 'しんか', 'evolution', 'evolve',
            '究極体', '完全体', '成熟期', '成長期', '幼年期'
        ]
        
        # Search for sections containing evolution terms
        for term in evolution_terms:
            # Search in text
            elements = soup.find_all(string=lambda text: term in text if text else False)
            for elem in elements[:3]:
                parent = elem.parent
                if parent:
                    evolution["evolution_keywords"].append({
                        "term": term,
                        "context": elem.strip()[:100],
                        "parent_tag": parent.name,
                        "parent_classes": parent.get('class', [])
                    })
                    
        # Look for evolution-specific containers
        evo_selectors = [
            '[class*="evolution"]', '[class*="evo"]',
            '[id*="evolution"]', '[id*="evo"]'
        ]
        
        for selector in evo_selectors:
            elements = soup.select(selector)
            for elem in elements:
                evolution["found_sections"].append({
                    "selector": selector,
                    "tag": elem.name,
                    "classes": elem.get('class', []),
                    "text_preview": elem.get_text(strip=True)[:200]
                })
                
        return evolution
    
    def _analyze_moves(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Look for move/technique sections."""
        moves = {
            "found_sections": [],
            "move_keywords": []
        }
        
        # Move-related terms
        move_terms = [
            '必殺技', 'わざ', '技', 'technique', 'move', 'attack',
            'skill', 'special', '必殺'
        ]
        
        for term in move_terms:
            elements = soup.find_all(string=lambda text: term in text if text else False)
            for elem in elements[:3]:
                parent = elem.parent
                if parent:
                    moves["move_keywords"].append({
                        "term": term,
                        "context": elem.strip()[:100],
                        "parent_tag": parent.name,
                        "parent_classes": parent.get('class', [])
                    })
                    
        return moves
    
    def _analyze_profile(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Look for profile/description sections."""
        profile = {
            "found_sections": [],
            "long_text_blocks": []
        }
        
        # Find paragraphs or text blocks
        text_containers = soup.find_all(['p', 'div'])
        for container in text_containers:
            text = container.get_text(strip=True)
            if len(text) > 100:  # Long text blocks
                profile["long_text_blocks"].append({
                    "tag": container.name,
                    "classes": container.get('class', []),
                    "text_length": len(text),
                    "text_preview": text[:200],
                    "parent_classes": container.parent.get('class', []) if container.parent else []
                })
                
        # Look for profile-specific selectors
        profile_selectors = [
            '[class*="profile"]', '[class*="description"]',
            '[class*="detail"]', '.c-digimon__profile'
        ]
        
        for selector in profile_selectors:
            elements = soup.select(selector)
            for elem in elements:
                profile["found_sections"].append({
                    "selector": selector,
                    "tag": elem.name,
                    "classes": elem.get('class', []),
                    "text_preview": elem.get_text(strip=True)[:200]
                })
                
        return profile
    
    def _analyze_images(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze image elements in detail."""
        images = {
            "all_images": [],
            "main_image_candidates": [],
            "image_patterns": {}
        }
        
        # Get all images
        all_imgs = soup.find_all('img')
        for img in all_imgs:
            src = img.get('src', '')
            if src and not any(skip in src for skip in ['icon', 'logo', 'button', 'arrow']):
                img_data = {
                    "src": src,
                    "alt": img.get('alt', ''),
                    "title": img.get('title', ''),
                    "width": img.get('width', 'auto'),
                    "height": img.get('height', 'auto'),
                    "classes": img.get('class', []),
                    "parent_classes": img.parent.get('class', []) if img.parent else [],
                    "is_likely_main": self._is_likely_main_image(img)
                }
                images["all_images"].append(img_data)
                
                if img_data["is_likely_main"]:
                    images["main_image_candidates"].append(img_data)
                    
        # Analyze image patterns
        src_patterns = Counter()
        for img in images["all_images"]:
            src = img["src"]
            # Extract pattern from src
            if '/digimon/' in src:
                src_patterns['contains_/digimon/'] += 1
            if src.endswith('.jpg') or src.endswith('.png'):
                src_patterns['static_image'] += 1
            if 'detail' in src:
                src_patterns['contains_detail'] += 1
                
        images["image_patterns"] = dict(src_patterns)
        
        return images
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from the page."""
        metadata = {
            "url_info": self._extract_url_info(url),
            "meta_tags": {},
            "json_ld": None,
            "open_graph": {}
        }
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            if name and content:
                metadata["meta_tags"][name] = content
                if name.startswith('og:'):
                    metadata["open_graph"][name] = content
                    
        # Look for JSON-LD
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                metadata["json_ld"] = json.loads(json_ld.string)
            except:
                metadata["json_ld"] = "Found but couldn't parse"
                
        return metadata
    
    def _extract_url_info(self, url: str) -> Dict[str, Any]:
        """Extract detailed URL information."""
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        info = {
            "full_path": parsed.path,
            "path_parts": path_parts,
            "last_segment": path_parts[-1] if path_parts else None,
            "query_params": dict(param.split('=') for param in parsed.query.split('&') if '=' in param) if parsed.query else {},
            "potential_id": self._extract_id_from_url(url),
            "file_extension": Path(parsed.path).suffix
        }
        
        return info
    
    def _is_likely_main_image(self, img: Tag) -> bool:
        """Determine if an image is likely the main Digimon image."""
        src = img.get('src', '').lower()
        alt = img.get('alt', '').lower()
        classes = ' '.join(img.get('class', [])).lower()
        
        # Positive indicators
        if any(term in src for term in ['main', 'detail', 'large', 'digimon']):
            return True
        if any(term in alt for term in ['digimon', 'デジモン']):
            return True
        if any(term in classes for term in ['main', 'digimon', 'character']):
            return True
            
        # Size check
        try:
            width = int(img.get('width', 0))
            height = int(img.get('height', 0))
            if width > 200 or height > 200:
                return True
        except:
            pass
            
        return False
    
    def _contains_katakana(self, text: str) -> bool:
        """Check if text contains katakana characters."""
        katakana_range = range(0x30A0, 0x30FF)
        return any(ord(char) in katakana_range for char in text)
    
    def _translate_common_terms(self, term: str) -> Optional[str]:
        """Translate common Digimon-related terms."""
        translations = {
            'レベル': 'Level',
            'タイプ': 'Type',
            '属性': 'Attribute',
            '必殺技': 'Special Move',
            '進化': 'Evolution',
            'プロフィール': 'Profile',
            '世代': 'Generation'
        }
        return translations.get(term)
        
    def _normalize_url(self, url: str) -> str:
        """Normalize relative URLs to absolute."""
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            # Use the index URL's base for absolute paths
            from urllib.parse import urlparse
            parsed = urlparse(self.index_url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            return f"{base}{url}"
        else:
            # For relative paths, use the index URL's directory
            return f"{self.index_url.rsplit('/', 1)[0]}/{url}"
            
    def _is_english(self, text: str) -> bool:
        """Check if text is primarily English."""
        try:
            text.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False
            
    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """Try to extract a Digimon ID from URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Try different patterns
        if 'detail/' in path:
            parts = path.split('detail/')
            if len(parts) > 1:
                return parts[1].replace('.html', '').replace('/', '_')
                
        # Last resort: use last path segment
        segments = path.split('/')
        if segments:
            return segments[-1].replace('.html', '')
            
        return None
        
    def investigate_structure(self, sample_size: int = 5) -> Dict[str, Any]:
        """Perform full structure investigation."""
        logger.info("Starting comprehensive structure investigation...")
        
        # First, get the index page
        logger.info(f"Fetching index page: {self.index_url}")
        index_soup = self.fetch_sample_page()
        if not index_soup:
            logger.error("Failed to fetch index page")
            return {}
            
        # Find Digimon links
        logger.info("Searching for Digimon detail page links...")
        link_analysis = self.find_digimon_links(index_soup)
        
        # Get sample detail URLs
        sample_urls = []
        for description, links in link_analysis.items():
            logger.info(f"{description}: Found {len(links)} links")
            sample_urls.extend(links)
            
        # Deduplicate and limit
        sample_urls = list(dict.fromkeys(sample_urls))[:sample_size]
        
        if not sample_urls:
            logger.error("No Digimon detail URLs found!")
            return {"error": "No detail page URLs found on index page"}
            
        logger.info(f"Will analyze {len(sample_urls)} sample pages")
        
        # Analyze detail pages
        detail_analyses = []
        for i, url in enumerate(sample_urls, 1):
            logger.info(f"\nAnalyzing page {i}/{len(sample_urls)}: {url}")
            analysis = self.analyze_detail_page(url)
            if analysis:
                detail_analyses.append(analysis)
                # Log summary of findings
                self._log_page_summary(analysis)
                
        # Compile results
        investigation_results = {
            "investigation_date": datetime.now().isoformat(),
            "index_page_analysis": {
                "url": self.index_url,
                "link_patterns_found": link_analysis,
                "total_unique_urls": len(set(sum(link_analysis.values(), [])))
            },
            "sample_detail_pages": detail_analyses,
            "aggregated_insights": self._aggregate_insights(detail_analyses),
            "recommendations": self._generate_recommendations(detail_analyses),
            "ai_friendly_summary": self._generate_ai_summary(detail_analyses)
        }
        
        # Save results
        output_path = Path("data/investigation_results.json")
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(investigation_results, f, ensure_ascii=False, indent=2)
            
        # Also save a markdown summary
        self._save_markdown_summary(investigation_results)
            
        logger.info(f"\nInvestigation complete!")
        logger.info(f"Results saved to: {output_path}")
        logger.info(f"Markdown summary: data/investigation_summary.md")
        
        return investigation_results
    
    def _log_page_summary(self, analysis: Dict[str, Any]) -> None:
        """Log a summary of page analysis findings."""
        logger.info("  Page structure:")
        if analysis.get("page_structure", {}).get("main_containers"):
            containers = analysis["page_structure"]["main_containers"]
            logger.info(f"    Found {len(containers)} main containers")
            
        if analysis.get("title_elements"):
            logger.info(f"    Found {len(analysis['title_elements'])} title elements")
            
        if analysis.get("data_sections", {}).get("definition_lists"):
            dl_count = len(analysis["data_sections"]["definition_lists"])
            logger.info(f"    Found {dl_count} definition lists with data")
            
        if analysis.get("image_elements", {}).get("main_image_candidates"):
            img_count = len(analysis["image_elements"]["main_image_candidates"])
            logger.info(f"    Found {img_count} main image candidates")
    
    def _aggregate_insights(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate insights across all analyzed pages."""
        insights = {
            "common_selectors": {},
            "data_patterns": {},
            "url_patterns": [],
            "content_consistency": {}
        }
        
        # Aggregate common selectors
        selector_counts = Counter()
        for analysis in analyses:
            for selector in analysis.get("title_elements", {}).keys():
                selector_counts[selector] += 1
                
        insights["common_selectors"]["titles"] = {
            selector: count for selector, count in selector_counts.most_common(5)
        }
        
        # Aggregate data patterns
        data_types = Counter()
        for analysis in analyses:
            if analysis.get("data_sections", {}).get("definition_lists"):
                data_types["definition_lists"] += 1
            if analysis.get("data_sections", {}).get("tables"):
                data_types["tables"] += 1
                
        insights["data_patterns"] = dict(data_types)
        
        # URL patterns
        url_patterns = set()
        for analysis in analyses:
            if analysis.get("metadata", {}).get("url_info", {}).get("potential_id"):
                url_patterns.add("Has extractable ID")
            if ".html" in analysis.get("url", ""):
                url_patterns.add("HTML file extension")
            if ".php" in analysis.get("url", ""):
                url_patterns.add("PHP file extension")
                
        insights["url_patterns"] = list(url_patterns)
        
        return insights
        
    def _generate_recommendations(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detailed selector recommendations based on analysis."""
        recommendations = {
            "selectors": {},
            "extraction_strategy": {},
            "confidence_scores": {},
            "warnings": [],
            "notes": []
        }
        
        if not analyses:
            recommendations["warnings"].append("No pages analyzed, cannot generate recommendations")
            return recommendations
            
        # Analyze title consistency
        title_selector_counts = Counter()
        for analysis in analyses:
            for selector in analysis.get("title_elements", {}).keys():
                title_selector_counts[selector] += 1
                
        # Find most common selectors
        total_pages = len(analyses)
        for selector, count in title_selector_counts.most_common():
            confidence = count / total_pages
            if confidence >= 0.8:  # Present in 80%+ of pages
                # Determine if it's Japanese or English
                is_english = any(
                    analysis.get("title_elements", {}).get(selector, {}).get("is_english", False)
                    for analysis in analyses
                )
                
                if "main" in selector or (confidence == 1.0 and not is_english):
                    recommendations["selectors"]["japanese_name"] = selector
                    recommendations["confidence_scores"]["japanese_name"] = confidence
                elif "sub" in selector or is_english:
                    recommendations["selectors"]["english_name"] = selector
                    recommendations["confidence_scores"]["english_name"] = confidence
                    
        # Analyze data extraction
        has_dl = sum(1 for a in analyses if a.get("data_sections", {}).get("definition_lists"))
        has_tables = sum(1 for a in analyses if a.get("data_sections", {}).get("tables"))
        
        if has_dl > has_tables:
            recommendations["extraction_strategy"]["primary_data"] = "definition_lists"
            recommendations["selectors"]["data_container"] = "dl"
        elif has_tables > 0:
            recommendations["extraction_strategy"]["primary_data"] = "tables"
            recommendations["selectors"]["data_container"] = "table"
            
        # Image recommendations
        image_selector_scores = Counter()
        for analysis in analyses:
            if analysis.get("image_elements", {}).get("main_image_candidates"):
                for img in analysis["image_elements"]["main_image_candidates"]:
                    if img.get("parent_classes"):
                        for cls in img["parent_classes"]:
                            image_selector_scores[f".{cls} img"] += 1
                            
        if image_selector_scores:
            best_img_selector = image_selector_scores.most_common(1)[0][0]
            recommendations["selectors"]["main_image"] = best_img_selector
        else:
            recommendations["selectors"]["main_image"] = "img[alt*='digimon' i], img[alt*='デジモン']"
            
        # Add helpful notes
        if recommendations["selectors"].get("japanese_name"):
            recommendations["notes"].append(f"Japanese name selector '{recommendations['selectors']['japanese_name']}' found in {title_selector_counts[recommendations['selectors']['japanese_name']]} pages")
            
        if not recommendations["selectors"].get("english_name"):
            recommendations["warnings"].append("No consistent English name selector found - may need translation")
            
        # Evolution and move extraction
        has_evolution = sum(1 for a in analyses if a.get("evolution_info", {}).get("evolution_keywords"))
        if has_evolution:
            recommendations["extraction_strategy"]["evolution_data"] = "keyword_search"
            recommendations["notes"].append(f"Evolution information found in {has_evolution}/{total_pages} pages")
            
        return recommendations
    
    def _generate_ai_summary(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate an AI-friendly summary of findings."""
        summary = {
            "overview": "",
            "page_structure": "",
            "data_extraction_approach": "",
            "key_selectors": {},
            "challenges": [],
            "next_steps": []
        }
        
        if not analyses:
            summary["overview"] = "No pages were successfully analyzed."
            return summary
            
        # Overview
        total = len(analyses)
        summary["overview"] = f"Analyzed {total} Digimon detail pages from digimon.net/reference."
        
        # Page structure summary
        common_containers = Counter()
        for analysis in analyses:
            for container in analysis.get("page_structure", {}).get("main_containers", []):
                common_containers[container["selector"]] += 1
                
        if common_containers:
            most_common = common_containers.most_common(1)[0]
            summary["page_structure"] = f"Pages consistently use '{most_common[0]}' as main content container."
            
        # Data extraction approach
        dl_count = sum(1 for a in analyses if a.get("data_sections", {}).get("definition_lists"))
        if dl_count == total:
            summary["data_extraction_approach"] = "All pages use definition lists (<dl>) for structured data. Extract key-value pairs from <dt>/<dd> elements."
        elif dl_count > 0:
            summary["data_extraction_approach"] = f"{dl_count}/{total} pages use definition lists. Mixed approach needed."
            
        # Key selectors
        if analyses[0].get("title_elements"):
            for selector, data in list(analyses[0]["title_elements"].items())[:3]:
                summary["key_selectors"][selector] = f"Contains: {data.get('text', '')[:50]}..."
                
        # Challenges
        if not any(a.get("title_elements", {}).get(".c-titleSet__sub", {}).get("is_english") for a in analyses):
            summary["challenges"].append("No English names found - will need translation")
            
        # Next steps
        summary["next_steps"] = [
            "Implement scraper using identified selectors",
            "Set up translation for Japanese text",
            "Handle pagination on index page",
            "Extract evolution relationships from linked pages"
        ]
        
        return summary
    
    def _save_markdown_summary(self, results: Dict[str, Any]) -> None:
        """Save a markdown summary of the investigation."""
        output_path = Path("data/investigation_summary.md")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Digimon.net Structure Investigation Summary\n\n")
            
            # Overview
            f.write("## Overview\n")
            summary = results.get("ai_friendly_summary", {})
            f.write(f"{summary.get('overview', '')}\n\n")
            
            # Key Findings
            f.write("## Key Findings\n\n")
            
            # Selectors
            if results.get("recommendations", {}).get("selectors"):
                f.write("### Recommended Selectors\n")
                for key, selector in results["recommendations"]["selectors"].items():
                    confidence = results["recommendations"].get("confidence_scores", {}).get(key, "N/A")
                    if isinstance(confidence, (int, float)):
                        f.write(f"- **{key}**: `{selector}` (confidence: {confidence:.0%})\n")
                    else:
                        f.write(f"- **{key}**: `{selector}`\n")
                f.write("\n")
                
            # Data Structure
            f.write("### Data Structure\n")
            f.write(f"{summary.get('data_extraction_approach', '')}\n\n")
            
            # Sample Data
            if results.get("sample_detail_pages"):
                f.write("## Sample Data Extracted\n\n")
                for i, page in enumerate(results["sample_detail_pages"][:2], 1):
                    f.write(f"### Page {i}: {page.get('url', '')}\n")
                    
                    # Title info
                    if page.get("title_elements"):
                        f.write("**Titles found:**\n")
                        for selector, data in list(page["title_elements"].items())[:3]:
                            f.write(f"- {selector}: \"{data.get('text', '')[:50]}...\"\n")
                        f.write("\n")
                        
                    # Data sections
                    if page.get("data_sections", {}).get("definition_lists"):
                        f.write("**Data fields found:**\n")
                        dl = page["data_sections"]["definition_lists"][0]
                        for item in dl.get("items", [])[:5]:
                            f.write(f"- {item['key']}: {item['value'][:50]}...\n")
                        f.write("\n")
                        
            # Challenges
            if summary.get("challenges"):
                f.write("## Challenges\n")
                for challenge in summary["challenges"]:
                    f.write(f"- {challenge}\n")
                f.write("\n")
                
            # Next Steps
            if summary.get("next_steps"):
                f.write("## Next Steps\n")
                for step in summary["next_steps"]:
                    f.write(f"1. {step}\n")
                    
        logger.info(f"Markdown summary saved to {output_path}")


def main():
    """Run the structure investigation."""
    investigator = StructureInvestigator()
    results = investigator.investigate_structure(sample_size=3)
    
    # Print summary
    if results.get("recommendations"):
        logger.info("Recommended selectors:")
        for key, value in results["recommendations"].items():
            if key != "notes":
                logger.info(f"  {key}: {value}")
                
        if results["recommendations"].get("notes"):
            logger.info("Notes:")
            for note in results["recommendations"]["notes"]:
                logger.info(f"  - {note}")


if __name__ == "__main__":
    main()