"""Tagging service for managing file tagging operations."""

import json
import re
import shutil
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlmodel import Session, select, and_, or_

from .database import get_session_sync
from .models import (
    TaggedFileDB, TaggedFile, AudibleSearchResult, AudibleBookDetails,
    TaggingJobCreate, TaggingJobUpdate, JobDB, JobType, JobStatus
)
from .utils import cleanup_backup_files


class TaggingService:
    """Service for managing file tagging operations."""
    
    def __init__(self):
        self.session = get_session_sync()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    def get_untagged_files(self, limit: int = 50, offset: int = 0) -> List[TaggedFile]:
        """Get all converted but untagged M4B files."""
        from .config import OUTPUT_DIR
        
        # Find all M4B files in output directory
        m4b_files = []
        if OUTPUT_DIR.exists():
            for file_path in OUTPUT_DIR.rglob("*.m4b"):
                # Check if file is already in database
                existing = self.get_tagged_file_by_path(str(file_path))
                if not existing or not existing.is_tagged:
                    m4b_files.append(file_path)
        
        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        paginated_files = m4b_files[start_idx:end_idx]
        
        # Convert to TaggedFile objects
        result = []
        for file_path in paginated_files:
            existing = self.get_tagged_file_by_path(str(file_path))
            if existing:
                result.append(self.to_tagged_file(existing))
            else:
                # Create new entry for untagged file
                tagged_file_db = TaggedFileDB(
                    file_path=str(file_path),
                    is_tagged=False
                )
                self.session.add(tagged_file_db)
                self.session.commit()
                self.session.refresh(tagged_file_db)
                result.append(self.to_tagged_file(tagged_file_db))
        
        return result
    
    def get_tagged_file_by_path(self, file_path: str) -> Optional[TaggedFileDB]:
        """Get tagged file by path."""
        statement = select(TaggedFileDB).where(TaggedFileDB.file_path == file_path)
        return self.session.exec(statement).first()
    
    def get_tagged_file(self, file_id: UUID) -> Optional[TaggedFileDB]:
        """Get tagged file by ID."""
        statement = select(TaggedFileDB).where(TaggedFileDB.id == file_id)
        return self.session.exec(statement).first()
    
    def create_tagging_job(self, job_data: TaggingJobCreate) -> JobDB:
        """Create a new tagging job."""
        job = JobDB(
            job_type=JobType.TAGGING,
            input_folders=json.dumps([job_data.file_path]),
            status=JobStatus.QUEUED
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job
    
    def search_audible(self, query: str) -> List[AudibleSearchResult]:
        """Search Audible for books matching the query."""
        try:
            # Use multiple locales for better coverage
            locales = ["com", "co.uk", "ca", "fr", "de", "it", "es", "co.jp", "com.au", "com.br"]
            results = []
            
            for locale in locales:
                try:
                    search_url = f"https://api.audible.{locale}/1.0/catalog/products"
                    params = {
                        "keywords": query,
                        "response_groups": "category_ladders,contributors,media,product_desc,product_attrs,product_extended_attrs,rating,series",
                        "image_sizes": "500,1000",
                        "num_results": "5",
                    }
                    
                    response = requests.get(
                        search_url, params=params, headers=self.headers, timeout=10
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    if "products" in data:
                        for product in data["products"]:
                            asin = product.get("asin", "")
                            title = product.get("title", "Unknown Title")
                            
                            # Extract authors
                            author = self._process_authors(product.get("authors", []))
                            
                            # Extract narrators
                            narrators = []
                            if "narrators" in product:
                                for narrator in product["narrators"]:
                                    narrators.append(narrator.get("name", ""))
                            narrator = ", ".join(narrators) if narrators else None
                            
                            # Extract series information
                            series_info = ""
                            if "series" in product and product["series"]:
                                series_list = product["series"]
                                if series_list:
                                    series_info = series_list[0].get("title", "")
                                    if series_list[0].get("sequence"):
                                        series_info += f" #{series_list[0]['sequence']}"
                            
                            # Check if we already have this ASIN
                            if not any(r.asin == asin for r in results):
                                results.append(AudibleSearchResult(
                                    title=title,
                                    author=author,
                                    narrator=narrator,
                                    series=series_info if series_info else None,
                                    asin=asin,
                                    locale=locale
                                ))
                    
                    # If we found results, we can stop searching other locales
                    if results:
                        break
                        
                except Exception as e:
                    continue
            
            return results[:5]  # Limit to 5 results
            
        except Exception as e:
            return []
    
    def get_book_details(self, asin: str, locale: str = "com") -> Optional[AudibleBookDetails]:
        """Get detailed book information from Audible."""
        try:
            # Try multiple locales if the first one fails
            locales = [locale, "com", "co.uk", "ca", "fr", "de", "it", "es", "co.jp", "com.au", "com.br"]
            
            product = None
            for current_locale in locales:
                try:
                    # Use search API to get full product data instead of individual product API
                    # The individual product API doesn't return all the data we need
                    url = f"https://api.audible.{current_locale}/1.0/catalog/products"
                    params = {
                        "keywords": asin,  # Search by ASIN
                        "response_groups": "category_ladders,contributors,media,product_desc,product_attrs,product_extended_attrs,rating,series",
                        "image_sizes": "500,1000",
                        "num_results": "1",
                    }
                    
                    response = requests.get(
                        url, params=params, headers=self.headers, timeout=10
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    if "products" not in data or not data["products"]:
                        continue  # Try next locale
                    
                    # Find the product with matching ASIN
                    for p in data["products"]:
                        if p.get("asin") == asin:
                            product = p
                            break
                    
                    if product:
                        break  # Found the product, break out of locale loop
                        
                except Exception as e:
                    # If this locale fails, try the next one
                    continue
            
            if not product:
                return None
            
            # Extract comprehensive metadata
            details = AudibleBookDetails(
                asin=asin,
                title=product.get("title", ""),
                subtitle=product.get("subtitle", ""),
                author="",
                authors=[],
                narrator="",
                narrators=[],
                series="",
                series_part="",
                description="",
                publisher_summary="",
                runtime_length_min="",
                rating="",
                release_date="",
                release_time="",
                language="",
                format_type="",
                publisher_name="",
                is_adult_product=False,
                cover_url="",
                genres=[],
                copyright="",
                isbn="",
                explicit=False
            )
            
            # Extract authors
            if "authors" in product:
                details.authors = [
                    author.get("name", "")
                    for author in product["authors"]
                    if author.get("name")
                ]
                details.author = self._process_authors(product["authors"])
            
            # Extract narrators
            if "narrators" in product:
                for narrator in product["narrators"]:
                    details.narrators.append(narrator.get("name", ""))
                details.narrator = ", ".join(details.narrators)
            
            # Extract series information
            if "series" in product:
                series_list = product["series"]
                if series_list:
                    series_info = series_list[0]
                    details.series = series_info.get("title", "")
                    details.series_part = str(series_info.get("sequence", ""))
            
            # Extract description/summary
            if "publisher_summary" in product:
                clean_summary = self._clean_html_text(product["publisher_summary"])
                details.publisher_summary = clean_summary
                details.description = clean_summary
            elif "merchandising_summary" in product:
                details.publisher_summary = product["merchandising_summary"]
                details.description = product["merchandising_summary"]
            elif "product_desc" in product:
                details.publisher_summary = product["product_desc"]
                details.description = product["product_desc"]
            
            # Extract runtime
            if "runtime_length_min" in product:
                details.runtime_length_min = str(product["runtime_length_min"])
            
            # Extract rating
            if "rating" in product:
                rating = product["rating"]
                if "overall_distribution" in rating:
                    overall = rating["overall_distribution"]
                    details.rating = overall.get("display_average_rating", "")
            
            # Extract release date
            if "publication_datetime" in product:
                details.release_date = product["publication_datetime"]
                try:
                    dt = datetime.fromisoformat(
                        product["publication_datetime"].replace("Z", "+00:00")
                    )
                    details.release_time = dt.strftime("%Y-%m-%d")
                except:
                    details.release_time = (
                        product["publication_datetime"][:10]
                        if len(product["publication_datetime"]) >= 10
                        else ""
                    )
            
            # Extract other fields
            details.language = product.get("language", "")
            details.format_type = product.get("format_type", "")
            details.publisher_name = product.get("publisher_name", "")
            details.is_adult_product = product.get("is_adult_product", False)
            details.explicit = product.get("is_adult_product", False)
            
            # Extract cover image
            if "product_images" in product:
                images = product["product_images"]
                details.cover_url = images.get("1000", images.get("500", ""))
            
            # Extract genres from category ladders
            if "category_ladders" in product:
                for ladder in product["category_ladders"]:
                    if ladder.get("root") == "Genres":
                        for category in ladder.get("ladder", []):
                            details.genres.append(category.get("name", ""))
            
            # Extract copyright and ISBN from extended attributes
            if "product_extended_attrs" in product:
                ext_attrs = product["product_extended_attrs"]
                details.copyright = ext_attrs.get("copyright", "")
                details.isbn = ext_attrs.get("isbn", "") or ext_attrs.get("isbn13", "") or ext_attrs.get("isbn10", "")
            
            return details
            
        except Exception as e:
            return None
    
    def apply_metadata_to_file(self, file_id: UUID, metadata: AudibleBookDetails) -> bool:
        """Apply metadata to a file and mark it as tagged."""
        try:
            tagged_file = self.get_tagged_file(file_id)
            if not tagged_file:
                return False
            
            file_path = Path(tagged_file.file_path)
            if not file_path.exists():
                print(f"File not found: {file_path}")
                return False
            
            # Download cover if available
            cover_path = None
            if metadata.cover_url:
                cover_path = self.download_cover(metadata.cover_url, metadata.asin)
            
            # Tag the file with metadata using mutagen
            if not self.tag_file(file_path, metadata, cover_path):
                print(f"Failed to tag file: {file_path}")
                return False
            
            # Store original file path for backup cleanup
            original_file_path = tagged_file.file_path
            
            # Move file to organized library structure
            new_path = self.move_to_library(file_path, metadata, cover_path)
            
            # Update the tagged file record with new path and metadata
            tagged_file.file_path = str(new_path)
            tagged_file.asin = metadata.asin
            tagged_file.title = metadata.title
            tagged_file.author = metadata.author
            tagged_file.narrator = metadata.narrator
            tagged_file.series = metadata.series
            tagged_file.series_part = metadata.series_part
            tagged_file.description = metadata.description
            tagged_file.cover_url = metadata.cover_url
            tagged_file.cover_path = cover_path
            tagged_file.is_tagged = True
            tagged_file.updated_at = datetime.utcnow()
            
            self.session.add(tagged_file)
            self.session.commit()
            
            # Clean up backup files after successful tagging
            # Use the original file path to find the associated backup files
            self.cleanup_backup_files_for_output(original_file_path)
            
            return True
            
        except Exception as e:
            print(f"Error applying metadata to file: {e}")
            return False
    
    def cleanup_backup_files_for_output(self, output_file_path: str) -> None:
        """Find and clean up backup files for a given output file."""
        try:
            # Find the conversion job that created this output file
            statement = select(JobDB).where(
                and_(
                    JobDB.job_type == JobType.CONVERSION,
                    JobDB.output_file == output_file_path,
                    JobDB.status == JobStatus.COMPLETED
                )
            )
            job = self.session.exec(statement).first()
            
            if job and job.backup_paths:
                import json
                backup_paths = json.loads(job.backup_paths)
                cleanup_backup_files(backup_paths)
                print(f"Cleaned up {len(backup_paths)} backup files for {output_file_path}")
            else:
                print(f"No backup files found for {output_file_path}")
                
        except Exception as e:
            print(f"Error cleaning up backup files for {output_file_path}: {e}")
    
    def delete_tagged_file(self, file_id: UUID) -> bool:
        """Delete a tagged file record."""
        tagged_file = self.get_tagged_file(file_id)
        if not tagged_file:
            return False
        
        self.session.delete(tagged_file)
        self.session.commit()
        return True
    
    def to_tagged_file(self, tagged_file_db: TaggedFileDB) -> TaggedFile:
        """Convert TaggedFileDB to TaggedFile for API responses."""
        return TaggedFile(
            id=tagged_file_db.id,
            file_path=tagged_file_db.file_path,
            asin=tagged_file_db.asin,
            title=tagged_file_db.title,
            author=tagged_file_db.author,
            narrator=tagged_file_db.narrator,
            series=tagged_file_db.series,
            series_part=tagged_file_db.series_part,
            description=tagged_file_db.description,
            cover_url=tagged_file_db.cover_url,
            cover_path=tagged_file_db.cover_path,
            is_tagged=tagged_file_db.is_tagged,
            created_at=tagged_file_db.created_at,
            updated_at=tagged_file_db.updated_at
        )
    
    def _process_authors(self, authors_list: List[Dict]) -> str:
        """Process authors list according to configuration settings."""
        if not authors_list:
            return "Unknown Author"
        
        # Filter out translators
        translator_keywords = [
            "traducteur", "traductrice", "translator", "traductor", "traductora",
            "übersetzer", "übersetzerin", "traduttore", "traduttrice",
            "翻訳者", "번역가", "переводчик", "переводчица"
        ]
        
        filtered_authors = []
        for author in authors_list:
            author_name = author.get("name", "").strip()
            if not author_name:
                continue
            
            # Skip translators
            is_translator = any(
                keyword.lower() in author_name.lower()
                for keyword in translator_keywords
            )
            if is_translator:
                continue
            
            filtered_authors.append(author_name)
        
        # If no authors after filtering, return original list
        if not filtered_authors:
            filtered_authors = [
                author.get("name", "").strip()
                for author in authors_list
                if author.get("name", "").strip()
            ]
        
        return ", ".join(filtered_authors) if filtered_authors else "Unknown Author"
    
    def _clean_html_text(self, html_text: str) -> str:
        """Clean HTML text and format for plain text."""
        if not html_text:
            return ""
        
        # Replace common HTML entities
        html_text = html_text.replace("&nbsp;", " ")
        html_text = html_text.replace("&amp;", "&")
        html_text = html_text.replace("&lt;", "<")
        html_text = html_text.replace("&gt;", ">")
        html_text = html_text.replace("&quot;", '"')
        html_text = html_text.replace("&#39;", "'")
        html_text = html_text.replace("&apos;", "'")
        html_text = html_text.replace("&ldquo;", '"')
        html_text = html_text.replace("&rdquo;", '"')
        html_text = html_text.replace("&lsquo;", "'")
        html_text = html_text.replace("&rsquo;", "'")
        html_text = html_text.replace("&mdash;", "—")
        html_text = html_text.replace("&ndash;", "–")
        html_text = html_text.replace("&hellip;", "...")
        
        # Remove HTML tags
        clean_text = re.sub(r"<[^>]+>", "", html_text)
        
        # Split into paragraphs and clean each one
        paragraphs = clean_text.split("\n")
        clean_text = "\n\n".join([p.strip() for p in paragraphs if p.strip()])
        
        return clean_text
    
    def download_cover(self, cover_url: str, asin: str) -> Optional[str]:
        """Download and save cover image."""
        try:
            if not cover_url:
                return None
            
            response = requests.get(cover_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Create covers directory
            from .config import OUTPUT_DIR
            covers_dir = OUTPUT_DIR / "covers"
            covers_dir.mkdir(exist_ok=True)
            
            # Save cover to covers directory
            cover_path = covers_dir / f"{asin}.jpg"
            with open(cover_path, "wb") as f:
                f.write(response.content)
            
            return str(cover_path)
            
        except Exception as e:
            print(f"Error downloading cover: {e}")
            return None
    
    def tag_file(self, file_path: Path, metadata: AudibleBookDetails, cover_path: Optional[str] = None) -> bool:
        """Tag the .m4b file with comprehensive metadata using mutagen."""
        try:
            from mutagen.mp4 import MP4, MP4Cover, MP4FreeForm
            
            # Load the M4B file
            audio = MP4(file_path)
            
            # Build comprehensive metadata dictionary
            tags = {}
            
            # Basic tags
            if metadata.title:
                tags["\xa9nam"] = metadata.title  # Title
                tags["\xa9alb"] = metadata.title  # Album
            
            if metadata.release_date:
                year = metadata.release_date[:4]
                if year:
                    tags["\xa9day"] = year  # Year
            
            # Author tags
            if metadata.author:
                tags["\xa9ART"] = metadata.author  # Artist
                tags["aART"] = metadata.author  # Album Artist
            
            # Narrator as composer
            if metadata.narrator:
                tags["\xa9wrt"] = metadata.narrator  # Composer (Narrator)
            
            # Series tags
            if metadata.series:
                tags["----:com.apple.iTunes:SERIES"] = MP4FreeForm(metadata.series.encode("utf-8"))
                if metadata.series_part:
                    tags["----:com.apple.iTunes:SERIES-PART"] = MP4FreeForm(metadata.series_part.encode("utf-8"))
            
            # Description as comment
            if metadata.description:
                clean_desc = self._clean_html_text(metadata.description)
                tags["\xa9cmt"] = clean_desc  # Comment
            
            # Genre tags
            if metadata.genres:
                tags["\xa9gen"] = "; ".join(metadata.genres)  # Genre
            
            # ASIN tags
            if metadata.asin:
                tags["----:com.apple.iTunes:ASIN"] = MP4FreeForm(metadata.asin.encode("utf-8"))
                tags["----:com.apple.iTunes:AUDIBLE_ASIN"] = MP4FreeForm(metadata.asin.encode("utf-8"))
            
            # Language
            if metadata.language:
                tags["----:com.apple.iTunes:LANGUAGE"] = MP4FreeForm(metadata.language.encode("utf-8"))
            
            # Format
            if metadata.format_type:
                tags["----:com.apple.iTunes:FORMAT"] = MP4FreeForm(metadata.format_type.encode("utf-8"))
            
            # Subtitle
            if metadata.subtitle:
                tags["----:com.apple.iTunes:SUBTITLE"] = MP4FreeForm(metadata.subtitle.encode("utf-8"))
            
            # Release time
            if metadata.release_time:
                tags["----:com.apple.iTunes:RELEASETIME"] = MP4FreeForm(metadata.release_time.encode("utf-8"))
            
            # Rating
            if metadata.rating:
                tags["----:com.apple.iTunes:RATING"] = MP4FreeForm(metadata.rating.encode("utf-8"))
            
            # Explicit content
            if metadata.explicit:
                tags["----:com.apple.iTunes:EXPLICIT"] = MP4FreeForm("1".encode("utf-8"))
            else:
                tags["----:com.apple.iTunes:EXPLICIT"] = MP4FreeForm("0".encode("utf-8"))
            
            # Audible URL
            if metadata.asin:
                audible_url = f"https://www.audible.com/pd/{metadata.asin}"
                tags["----:com.apple.iTunes:WWWAUDIOFILE"] = MP4FreeForm(audible_url.encode("utf-8"))
            
            # iTunes specific tags
            tags["pgap"] = [1]  # Gapless
            tags["stik"] = [2]  # Audiobook
            
            # Apply all tags
            for key, value in tags.items():
                try:
                    if key.startswith("----:"):
                        # Freeform tags need to be MP4FreeForm objects
                        audio.tags[key] = [value]
                    elif key in ["pgap", "stik"]:
                        # Integer tags
                        audio.tags[key] = value
                    else:
                        # Standard tags can be strings
                        audio.tags[key] = [value]
                except Exception as tag_error:
                    print(f"Error applying tag {key}: {tag_error}")
                    continue
            
            # Add cover art if available
            if cover_path and Path(cover_path).exists():
                try:
                    with open(cover_path, "rb") as f:
                        cover_data = f.read()
                    audio["covr"] = [MP4Cover(cover_data)]
                except Exception as e:
                    print(f"Could not embed cover art: {e}")
            
            # Save the file
            audio.save()
            return True
            
        except Exception as e:
            print(f"Error with mutagen tagging: {e}")
            return False
    
    def move_to_library(self, file_path: Path, metadata: AudibleBookDetails, cover_path: Optional[str] = None) -> Path:
        """Move tagged file to organized library structure compatible with series."""
        try:
            from .config import OUTPUT_DIR
            
            # Create library directory structure: library/Author/Series/Title.m4b
            author = metadata.author or "Unknown Author"
            series = metadata.series or ""
            title = metadata.title or "Unknown Title"
            
            # Clean names for filesystem with Unicode handling
            def clean_filename(name: str) -> str:
                """Clean filename for filesystem compatibility."""
                if not name:
                    return "Unknown"
                # Remove or replace problematic characters
                cleaned = re.sub(r'[<>:"/\\|?*]', "_", name)
                # Handle Unicode characters that might cause issues
                cleaned = cleaned.encode("utf-8", errors="replace").decode("utf-8")
                # Remove leading/trailing spaces and dots
                cleaned = cleaned.strip(" .")
                return cleaned if cleaned else "Unknown"
            
            author_clean = clean_filename(author)
            series_clean = clean_filename(series) if series else ""
            title_clean = clean_filename(title)
            
            # Get series part number if available
            series_part = metadata.series_part or ""
            
            # Create filename with series number if available
            if series_part and series_clean:
                # Include series number in the filename
                filename = f"{title_clean} ({series_clean} #{series_part}).m4b"
            elif series_clean:
                # Include series name without number
                filename = f"{title_clean} ({series_clean}).m4b"
            else:
                # No series information
                filename = f"{title_clean}.m4b"
            
            # Create destination path - each book gets its own folder
            if series_clean:
                # For series: library/Author/Series/Title (Series #1)/Title (Series #1).m4b
                if series_part:
                    folder_name = f"{title_clean} ({series_clean} #{series_part})"
                else:
                    folder_name = f"{title_clean} ({series_clean})"
                dest_dir = OUTPUT_DIR / "library" / author_clean / series_clean / folder_name
            else:
                # For standalone: library/Author/Title/Title.m4b
                dest_dir = OUTPUT_DIR / "library" / author_clean / title_clean
            
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / filename
            
            # Move file with proper Unicode handling
            try:
                shutil.move(str(file_path), str(dest_path))
            except UnicodeEncodeError as e:
                # Fallback: try with encoded path
                encoded_src = str(file_path).encode("utf-8", errors="replace").decode("utf-8")
                encoded_dest = str(dest_path).encode("utf-8", errors="replace").decode("utf-8")
                shutil.move(encoded_src, encoded_dest)
            
            # Create additional metadata files for Audiobookshelf compatibility
            self.create_additional_metadata_files(dest_dir, metadata, cover_path, file_path)
            
            return dest_path
            
        except Exception as e:
            print(f"Error moving file to library: {e}")
            return file_path
    
    def create_additional_metadata_files(
        self,
        dest_dir: Path,
        metadata: AudibleBookDetails,
        cover_path: Optional[str] = None,
        file_path: Optional[Path] = None,
    ) -> None:
        """Create additional metadata files compatible with Audiobookshelf."""
        try:
            # Create desc.txt (description)
            if metadata.description:
                desc_content = self._clean_html_text(metadata.description)
                desc_file = dest_dir / "desc.txt"
                with open(desc_file, "w", encoding="utf-8") as f:
                    f.write(desc_content)
            
            # Create reader.txt (narrator)
            if metadata.narrator:
                reader_file = dest_dir / "reader.txt"
                with open(reader_file, "w", encoding="utf-8") as f:
                    f.write(metadata.narrator)
            
            # Create OPF file (Open Packaging Format)
            opf_content = self.create_opf_content(metadata)
            if opf_content:
                # Use the new processed filename for the .opf file
                # Get the .m4b file in the destination directory
                m4b_files = list(dest_dir.glob("*.m4b"))
                if m4b_files:
                    # Use the first .m4b file found (should be the processed one)
                    m4b_name = m4b_files[0].stem  # Get filename without extension
                else:
                    # Fallback: construct the filename from metadata
                    title = metadata.title or "Unknown Title"
                    series = metadata.series or ""
                    series_part = metadata.series_part or ""
                    
                    # Clean the title for filename
                    def clean_filename(name: str) -> str:
                        if not name:
                            return "Unknown"
                        cleaned = re.sub(r'[<>:"/\\|?*]', "_", name)
                        cleaned = cleaned.encode("utf-8", errors="replace").decode("utf-8")
                        cleaned = cleaned.strip(" .")
                        return cleaned if cleaned else "Unknown"
                    
                    title_clean = clean_filename(title)
                    
                    # Build filename similar to how it's done in move_to_library
                    if series_part and series:
                        m4b_name = f"{title_clean} ({clean_filename(series)} #{series_part})"
                    elif series:
                        m4b_name = f"{title_clean} ({clean_filename(series)})"
                    else:
                        m4b_name = title_clean
                
                opf_file = dest_dir / f"{m4b_name}.opf"
                with open(opf_file, "w", encoding="utf-8") as f:
                    f.write(opf_content)
            
            # Copy cover image to book folder if available
            if cover_path and Path(cover_path).exists():
                cover_dest = dest_dir / "cover.jpg"
                try:
                    shutil.copy2(cover_path, cover_dest)
                except Exception as e:
                    print(f"Could not copy cover to book folder: {e}")
            
        except Exception as e:
            print(f"Error creating additional metadata files: {e}")
    
    def create_opf_content(self, metadata: AudibleBookDetails) -> str:
        """Create OPF content for Audiobookshelf compatibility."""
        try:
            from xml.sax.saxutils import escape
            
            # Extract basic information with proper None handling
            title = metadata.title or "Unknown Title"
            author = metadata.author or "Unknown Author"
            narrator = metadata.narrator or ""
            publisher = metadata.publisher_name or ""
            isbn = metadata.isbn or ""
            description = self._clean_html_text(metadata.description or "")
            language = metadata.language or "en"
            series = metadata.series or ""
            series_part = metadata.series_part or ""
            
            # Extract publish year from release date
            publish_year = ""
            if metadata.release_date:
                try:
                    publish_year = metadata.release_date[:4]
                except:
                    pass
            
            # Ensure we have a proper volume number for series
            volume_number = metadata.series_part or ""
            if volume_number and volume_number.isdigit():
                volume_number = str(int(volume_number))  # Remove leading zeros
            
            # Create genres list
            genres = metadata.genres or []
            
            # Create OPF content with conditional fields
            opf_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:identifier id="BookId">{metadata.asin or 'unknown'}</dc:identifier>
        <dc:title>{escape(title)}</dc:title>
        <dc:creator>{escape(author)}</dc:creator>"""
            
            # Add optional fields only if they have content
            if publisher:
                opf_content += f"\n        <dc:publisher>{escape(publisher)}</dc:publisher>"
            else:
                opf_content += "\n        <dc:publisher></dc:publisher>"
            
            opf_content += f"\n        <dc:language>{language}</dc:language>"
            
            if description:
                opf_content += f"\n        <dc:description>{escape(description)}</dc:description>"
            else:
                opf_content += "\n        <dc:description></dc:description>"
            
            # Add individual genre tags
            if genres:
                for genre in genres:
                    opf_content += f"\n        <dc:subject>{escape(genre)}</dc:subject>"
            else:
                opf_content += "\n        <dc:subject></dc:subject>"
            
            if publish_year:
                opf_content += f"\n        <dc:date>{publish_year}</dc:date>"
            else:
                opf_content += "\n        <dc:date></dc:date>"
            
            opf_content += f'\n        <dc:identifier opf:scheme="ASIN">{metadata.asin or ""}</dc:identifier>'
            
            # Add ISBN if available
            if isbn:
                opf_content += f'\n        <dc:identifier opf:scheme="ISBN">{escape(isbn)}</dc:identifier>'
            
            # Add narrator if available
            if narrator:
                opf_content += f'\n        <dc:contributor role="nrt">{escape(narrator)}</dc:contributor>'
            
            # Add series information if available
            if series:
                opf_content += f'\n        <dc:subject opf:authority="series">{escape(series)}</dc:subject>'
                if volume_number:
                    opf_content += f'\n        <meta property="series-part">{volume_number}</meta>'
            
            # Add additional metadata for Audiobookshelf compatibility
            if metadata.runtime_length_min:
                opf_content += f'\n        <meta property="duration">{metadata.runtime_length_min}</meta>'
            
            if metadata.rating:
                opf_content += f'\n        <meta property="rating">{escape(metadata.rating)}</meta>'
            
            # Close OPF content
            opf_content += """\n    </metadata>
<manifest>
    <item id="cover" href="cover.jpg" media-type="image/jpeg"/>
</manifest>
<spine>
    <itemref idref="cover"/>
</spine>
</package>"""
            
            return opf_content
            
        except Exception as e:
            print(f"Error creating OPF content: {e}")
            return ""


# Global tagging service instance
tagging_service = TaggingService()
