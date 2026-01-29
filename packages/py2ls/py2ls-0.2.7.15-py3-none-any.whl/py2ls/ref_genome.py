import subprocess
import os
import sys
from pathlib import Path
import shutil
import gzip
from datetime import datetime
import requests
from tqdm import tqdm
import hashlib
import json
import time
import tarfile

class RefGenomeDownloader:
    """Download genome references for various organisms and builds with robust error handling"""
    
    GENOME_SOURCES = {
        "ucsc": {
            "base_url": "https://hgdownload.soe.ucsc.edu/goldenPath",
            "fasta_pattern": "{genome}/bigZips/{genome}.fa.gz",
            "gtf_pattern": None,
        },
        "ensembl": {
            "base_url": "https://ftp.ensembl.org/pub",
            "fasta_pattern": "release-{release}/fasta/{species}/dna/{species_capital}.{build}.dna.primary_assembly.fa.gz",
            "gtf_pattern": "release-{release}/gtf/{species}/{species_capital}.{build}.{release}.gtf.gz",
        },
        "ensembl_fast": {
            "base_url": "https://ftp.ensembl.org/pub",
            "fasta_pattern": "release-{release}/fasta/{species}/dna/{species}.{build}.dna.primary_assembly.fa.gz",
            "gtf_pattern": "release-{release}/gtf/{species}/{species}.{build}.{release}.gtf.gz",
        },
        "ncbi": {
            "base_url": "https://ftp.ncbi.nlm.nih.gov/genomes/all",
            "fasta_pattern": "GCF/{accession1}/{accession2}/{accession}_{build}/{accession}_{build}_genomic.fna.gz",
            "gtf_pattern": "GCF/{accession1}/{accession2}/{accession}_{build}/{accession}_{build}_genomic.gtf.gz",
        },
        "ensembl_grch38_alt": {
            "base_url": "https://ftp.ensembl.org/pub",
            "fasta_pattern": "release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz",
            "gtf_pattern": "release-110/gtf/homo_sapiens/Homo_sapiens.GRCh38.110.gtf.gz",
        },
        "igenomes_aws": {
            "base_url": "https://igenomes.illumina.com.s3.amazonaws.com",
            "fasta_pattern": "Homo_sapiens/{build}/{source}/Homo_sapiens_{build}.fa",
            "gtf_pattern": "Homo_sapiens/{build}/{source}/Homo_sapiens_{build}.gtf",
        }
    }
    
    # Updated genome database with multiple source options
    GENOME_DATABASE = {
        # Human genomes - prioritize UCSC as it's more reliable
        "GRCh38": {
            "species": "homo_sapiens",
            "build": "GRCh38",
            "source": "ucsc",  # Changed to UCSC as primary
            "release": "113",
            "alias": ["hg38", "GRCh38.p14"],
            "ucsc_name": "hg38",  # UCSC name
            "accession": "GCF_000001405.40",
            "accession1": "000",
            "accession2": "001",
            "sources": ["ucsc", "ensembl_fast", "ncbi"],  # Priority order
        },
        "hg38": {
            "species": "homo_sapiens",
            "build": "hg38",
            "source": "ucsc",
            "alias": ["GRCh38"],
        },
        "GRCh37": {
            "species": "homo_sapiens", 
            "build": "GRCh37",
            "source": "ucsc",  # Changed to UCSC
            "release": "75",
            "alias": ["hg19", "GRCh37.p13"],
            "ucsc_name": "hg19",
            "accession": "GCF_000001405.25",
            "accession1": "000",
            "accession2": "001",
            "sources": ["ucsc", "ensembl_fast", "ncbi"],
        },
        "hg19": {
            "species": "homo_sapiens",
            "build": "hg19",
            "source": "ucsc",
            "alias": ["GRCh37"],
        },
        
        # Mouse genomes
        "mm10": {
            "species": "mus_musculus",
            "build": "mm10",
            "source": "ucsc",
            "alias": ["GRCm38"],
            "ucsc_name": "mm10",
        },
        "mm39": {
            "species": "mus_musculus",
            "build": "mm39",
            "source": "ucsc",
            "alias": ["GRCm39"],
            "ucsc_name": "mm39",
        },
        "GRCm38": {
            "species": "mus_musculus",
            "build": "GRCm38",
            "source": "ensembl_fast",
            "release": "113",
            "alias": ["mm10"],
            "sources": ["ucsc", "ensembl_fast"],
        },
        "GRCm39": {
            "species": "mus_musculus",
            "build": "GRCm39",
            "source": "ensembl_fast",
            "release": "113",
            "sources": ["ucsc", "ensembl_fast"],
        },
    }
    
    def __init__(self, genome_dir=None):
        """Initialize genome downloader"""
        if genome_dir is None:
            self.genome_dir = Path.home() / "igenomes"
        else:
            self.genome_dir = Path(genome_dir)
        
        self.genome_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.timeout = 30
    
    def _is_html_file(self, filepath):
        """Check if a file is HTML (error page) instead of a gzipped file"""
        try:
            with open(filepath, 'rb') as f:
                first_bytes = f.read(100)
                return first_bytes.startswith(b'<!') or b'html' in first_bytes.lower() or b'error' in first_bytes.lower()
        except:
            return False
    
    def _check_url_exists(self, url):
        """Check if URL exists and is downloadable"""
        try:
            response = self.session.head(url, allow_redirects=True, timeout=self.timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"    URL check failed: {e}")
            return False
        except Exception as e:
            print(f"    Unexpected error checking URL: {e}")
            return False
    
    def _get_fallback_urls(self, genome_info, file_type):
        """Get fallback URLs for different sources"""
        urls = []
        genome_name = list(self.GENOME_DATABASE.keys())[
            list(self.GENOME_DATABASE.values()).index(genome_info)
        ] if genome_info in self.GENOME_DATABASE.values() else None
        
        # Try multiple sources if specified
        if 'sources' in genome_info:
            for source in genome_info['sources']:
                if source == "ucsc":
                    build = genome_info.get('ucsc_name', genome_info['build'])
                    if file_type == "fasta":
                        urls.extend([
                            f"https://hgdownload.soe.ucsc.edu/goldenPath/{build}/bigZips/{build}.fa.gz",
                            f"https://hgdownload.soe.ucsc.edu/goldenPath/{build}/bigZips/genes/{build}.refGene.gtf.gz",
                            f"http://hgdownload.cse.ucsc.edu/goldenPath/{build}/bigZips/{build}.fa.gz",
                        ])
                elif source == "ensembl_fast":
                    species = genome_info['species']
                    build = genome_info['build']
                    release = genome_info.get('release', '113')
                    
                    if file_type == "fasta":
                        urls.extend([
                            f"https://ftp.ensembl.org/pub/release-{release}/fasta/{species}/dna/{species}.{build}.dna.primary_assembly.fa.gz",
                            f"https://ftp.ensembl.org/pub/release-{release}/fasta/{species}/dna/{species.capitalize()}.{build}.dna.primary_assembly.fa.gz",
                            f"https://ftp.ensembl.org/pub/release-{release}/fasta/{species}/dna/{species}.{build}.dna.toplevel.fa.gz",
                        ])
                    elif file_type == "gtf":
                        urls.extend([
                            f"https://ftp.ensembl.org/pub/release-{release}/gtf/{species}/{species}.{build}.{release}.gtf.gz",
                            f"https://ftp.ensembl.org/pub/release-{release}/gtf/{species}/{species.capitalize()}.{build}.{release}.gtf.gz",
                            f"https://ftp.ensembl.org/pub/release-{release}/gtf/{species}/{species}.{build}.gtf.gz",
                        ])
        
        # Add specific known working URLs for GRCh38
        if genome_name == "GRCh38" or genome_name == "hg38":
            if file_type == "fasta":
                urls.extend([
                    # UCSC URLs (most reliable)
                    "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz",
                    "http://hgdownload.cse.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz",
                    # Older Ensembl releases that might work
                    "https://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz",
                    "https://ftp.ensembl.org/pub/release-109/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz",
                    "https://ftp.ensembl.org/pub/release-108/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz",
                    "https://ftp.ensembl.org/pub/release-107/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz",
                    # NCBI URLs
                    "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.40_GRCh38.p14/GCF_000001405.40_GRCh38.p14_genomic.fna.gz",
                ])
            elif file_type == "gtf":
                urls.extend([
                    # UCSC GTF (via table browser)
                    "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/genes/hg38.refGene.gtf.gz",
                    # Ensembl GTF
                    "https://ftp.ensembl.org/pub/release-110/gtf/homo_sapiens/Homo_sapiens.GRCh38.110.gtf.gz",
                    "https://ftp.ensembl.org/pub/release-109/gtf/homo_sapiens/Homo_sapiens.GRCh38.109.gtf.gz",
                    "https://ftp.ensembl.org/pub/release-108/gtf/homo_sapiens/Homo_sapiens.GRCh38.108.gtf.gz",
                    "https://ftp.ensembl.org/pub/release-107/gtf/homo_sapiens/Homo_sapiens.GRCh38.107.gtf.gz",
                    # NCBI GTF
                    "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.40_GRCh38.p14/GCF_000001405.40_GRCh38.p14_genomic.gtf.gz",
                ])
        
        return list(dict.fromkeys(urls))  # Remove duplicates
    
    def build_download_urls(self, genome_info, file_type):
        """Build download URLs for a specific file type"""
        source = genome_info.get('source', 'ucsc')
        urls = []
        
        if source == "ucsc":
            build = genome_info.get('ucsc_name', genome_info['build'])
            if file_type == "fasta":
                urls.append(f"https://hgdownload.soe.ucsc.edu/goldenPath/{build}/bigZips/{build}.fa.gz")
            elif file_type == "gtf":
                # UCSC doesn't provide standard GTF, but has refGene
                urls.append(f"https://hgdownload.soe.ucsc.edu/goldenPath/{build}/bigZips/genes/{build}.refGene.gtf.gz")
        
        elif source == "ensembl_fast":
            species = genome_info['species']
            build = genome_info['build']
            release = genome_info.get('release', '113')
            
            if file_type == "fasta":
                urls.append(f"https://ftp.ensembl.org/pub/release-{release}/fasta/{species}/dna/{species}.{build}.dna.primary_assembly.fa.gz")
            elif file_type == "gtf":
                urls.append(f"https://ftp.ensembl.org/pub/release-{release}/gtf/{species}/{species}.{build}.{release}.gtf.gz")
        
        # Always add fallback URLs
        urls.extend(self._get_fallback_urls(genome_info, file_type))
        
        return urls
    
    def download_with_requests(self, url, output_path, max_retries=3):
        """Download file using requests with progress bar and validation"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file already exists and is valid
        if output_path.exists():
            if output_path.stat().st_size > 1000 and not self._is_html_file(output_path):
                print(f"  ✓ File already exists: {output_path}")
                return True
            else:
                print(f"  ! Existing file appears corrupted, re-downloading: {output_path}")
                output_path.unlink()
        
        for attempt in range(max_retries):
            print(f"  Download attempt {attempt + 1}/{max_retries}:")
            print(f"    URL: {url}")
            
            try:
                # First check if URL exists
                if not self._check_url_exists(url):
                    print(f"    ✗ URL not accessible")
                    if attempt == max_retries - 1:
                        return False
                    time.sleep(2)
                    continue
                
                # Download with progress bar
                response = self.session.get(url, stream=True, timeout=self.timeout)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                
                with open(output_path, 'wb') as f:
                    if total_size == 0:
                        f.write(response.content)
                        print(f"    ⚠ Downloaded without size info")
                    else:
                        chunk_size = 8192
                        with tqdm(total=total_size, unit='B', unit_scale=True, 
                                 desc='      Progress', ncols=80, mininterval=0.5) as pbar:
                            for chunk in response.iter_content(chunk_size=chunk_size):
                                if chunk:
                                    f.write(chunk)
                                    pbar.update(len(chunk))
                
                # Verify download
                if output_path.stat().st_size == 0:
                    print(f"    ✗ Downloaded file is empty")
                    output_path.unlink()
                    continue
                
                if self._is_html_file(output_path):
                    print(f"    ✗ Downloaded file is HTML (server error)")
                    output_path.unlink()
                    continue
                
                file_size_mb = output_path.stat().st_size / 1024 / 1024
                print(f"    ✓ Download successful: {file_size_mb:.2f} MB")
                return True
                
            except requests.exceptions.RequestException as e:
                print(f"    ✗ Request failed: {e}")
                if output_path.exists():
                    output_path.unlink()
                
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # Exponential backoff
                    print(f"    Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            except Exception as e:
                print(f"    ✗ Unexpected error: {e}")
                if output_path.exists():
                    output_path.unlink()
                
                if attempt < max_retries - 1:
                    print(f"    Retrying in 5 seconds...")
                    time.sleep(5)
        
        return False
    
    def download_with_wget(self, url, output_path, max_retries=3):
        """Download using wget as fallback"""
        output_path = Path(output_path)
        
        for attempt in range(max_retries):
            print(f"  Wget attempt {attempt + 1}/{max_retries}: {url}")
            
            try:
                cmd = ['wget', '--no-check-certificate', '-c', '-O', 
                      str(output_path), url, '-q', '--show-progress']
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
                    if not self._is_html_file(output_path):
                        print(f"    ✓ Wget download successful")
                        return True
                    else:
                        print(f"    ✗ Wget downloaded HTML")
                        output_path.unlink()
                else:
                    print(f"    ✗ Wget failed: {result.stderr[:100] if result.stderr else 'Unknown error'}")
            
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                print(f"    ✗ Wget not available or failed: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(5)
        
        return False
    
    def download_with_curl(self, url, output_path, max_retries=3):
        """Download using curl as fallback"""
        output_path = Path(output_path)
        
        for attempt in range(max_retries):
            print(f"  Curl attempt {attempt + 1}/{max_retries}: {url}")
            
            try:
                cmd = ['curl', '-L', '-k', '-o', str(output_path), url, '--progress-bar']
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
                    if not self._is_html_file(output_path):
                        print(f"    ✓ Curl download successful")
                        return True
                    else:
                        print(f"    ✗ Curl downloaded HTML")
                        output_path.unlink()
                else:
                    print(f"    ✗ Curl failed: {result.stderr[:100] if result.stderr else 'Unknown error'}")
            
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                print(f"    ✗ Curl not available or failed: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(5)
        
        return False
    
    def download_file(self, urls, output_path, file_type, max_retries_per_url=3):
        """Download a file trying multiple URLs and methods"""
        output_path = Path(output_path)
        
        for url_idx, url in enumerate(urls):
            print(f"\n  Trying {file_type} URL {url_idx + 1}/{len(urls)}")
            print(f"    {url}")
            
            # Try requests first
            if self.download_with_requests(url, output_path, max_retries_per_url):
                return True
            
            # Try wget as fallback
            if self.download_with_wget(url, output_path, max_retries_per_url):
                return True
            
            # Try curl as last resort
            if self.download_with_curl(url, output_path, max_retries_per_url):
                return True
        
        return False
    
    def decompress_file(self, compressed_path):
        """Decompress a gzipped file with validation"""
        compressed_path = Path(compressed_path)
        decompressed_path = compressed_path.with_suffix('')
        
        # Check if already decompressed
        if decompressed_path.exists():
            print(f"  ✓ Already decompressed: {decompressed_path}")
            return decompressed_path
        
        if not compressed_path.exists():
            print(f"  ✗ Compressed file not found: {compressed_path}")
            return None
        
        print(f"  Decompressing: {compressed_path.name}")
        
        try:
            # Verify it's a valid gzip file
            try:
                with gzip.open(compressed_path, 'rb') as test_gz:
                    test_gz.read(100)
            except (gzip.BadGzipFile, OSError) as e:
                print(f"    ✗ Not a valid gzip file: {e}")
                return None
            
            # Decompress the file
            with gzip.open(compressed_path, 'rb') as gz_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(gz_in, f_out)
            
            # Verify decompressed file
            if decompressed_path.stat().st_size == 0:
                print(f"    ✗ Decompressed file is empty")
                decompressed_path.unlink()
                return None
            
            # Remove compressed file
            compressed_path.unlink()
            
            file_size_mb = decompressed_path.stat().st_size / 1024 / 1024
            print(f"    ✓ Decompressed to: {decompressed_path} ({file_size_mb:.2f} MB)")
            return decompressed_path
            
        except Exception as e:
            print(f"    ✗ Decompression failed: {e}")
            if decompressed_path.exists():
                decompressed_path.unlink()
            return None
    
    def create_symlink_ucsc_to_ensembl(self, genome_dir, ucsc_name, ensembl_name):
        """Create symlink from UCSC download to Ensembl-named file"""
        ucsc_fasta = genome_dir / f"{ucsc_name}.fa"
        ensembl_fasta = genome_dir / "genome.fa"
        
        if ucsc_fasta.exists() and not ensembl_fasta.exists():
            try:
                ensembl_fasta.symlink_to(ucsc_fasta)
                print(f"  Created symlink: {ensembl_fasta} -> {ucsc_fasta}")
                return True
            except:
                # If symlink fails, copy the file
                shutil.copy2(ucsc_fasta, ensembl_fasta)
                print(f"  Copied file: {ucsc_fasta} -> {ensembl_fasta}")
                return True
        return False
    
    def download_genome(self, genome_name, download_gtf=True, force=False):
        """Download genome references with robust error handling"""
        # Resolve genome name
        resolved_name = self.resolve_genome_name(genome_name)
        if not resolved_name:
            raise ValueError(f"Unknown genome: {genome_name}")
        
        print(f"\n{'='*70}")
        print(f"DOWNLOADING GENOME: {resolved_name}")
        print(f"{'='*70}")
        
        # Get genome info
        genome_info = self.GENOME_DATABASE[resolved_name]
        species = genome_info['species'].replace('_', ' ').title()
        source = genome_info.get('source', 'unknown')
        
        print(f"Species: {species}")
        print(f"Primary source: {source}")
        print(f"Build: {genome_info.get('build', 'N/A')}")
        if 'release' in genome_info:
            print(f"Release: {genome_info.get('release', 'N/A')}")
        if 'ucsc_name' in genome_info:
            print(f"UCSC name: {genome_info.get('ucsc_name')}")
        print(f"Alternative sources: {', '.join(genome_info.get('sources', ['default']))}")
        
        # Create directory for this genome
        genome_dir = self.genome_dir / resolved_name
        genome_dir.mkdir(parents=True, exist_ok=True)
        
        success = True
        downloaded_files = {}
        
        # Download FASTA
        print(f"\n{'─' * 50}")
        print(f"1. DOWNLOADING FASTA FILE")
        print(f"{'─' * 50}")
        
        fasta_gz = genome_dir / "genome.fa.gz"
        fasta_file = genome_dir / "genome.fa"
        
        # Check if already exists and valid
        if not force and fasta_file.exists() and fasta_file.stat().st_size > 1000:
            print(f"  ✓ FASTA already exists: {fasta_file}")
            downloaded_files['fasta'] = str(fasta_file)
        else:
            # Clean up any existing corrupted files
            for f in [fasta_gz, fasta_file]:
                if f.exists():
                    f.unlink()
            
            # Get all possible FASTA URLs
            fasta_urls = self.build_download_urls(genome_info, "fasta")
            print(f"  Found {len(fasta_urls)} possible FASTA URLs")
            
            # Try to download FASTA
            if self.download_file(fasta_urls, fasta_gz, "FASTA", max_retries_per_url=2):
                # Decompress if download succeeded
                decompressed = self.decompress_file(fasta_gz)
                if decompressed:
                    downloaded_files['fasta'] = str(decompressed)
                else:
                    success = False
            else:
                print(f"  ✗ All FASTA download attempts failed")
                success = False
        
        # Download GTF (if requested)
        if download_gtf and success:
            print(f"\n{'─' * 50}")
            print(f"2. DOWNLOADING GTF FILE")
            print(f"{'─' * 50}")
            
            gtf_gz = genome_dir / "genes.gtf.gz"
            gtf_file = genome_dir / "genes.gtf"
            
            # Check if already exists and valid
            if not force and gtf_file.exists() and gtf_file.stat().st_size > 1000:
                print(f"  ✓ GTF already exists: {gtf_file}")
                downloaded_files['gtf'] = str(gtf_file)
            else:
                # Clean up any existing corrupted files
                for f in [gtf_gz, gtf_file]:
                    if f.exists():
                        f.unlink()
                
                # Get all possible GTF URLs
                gtf_urls = self.build_download_urls(genome_info, "gtf")
                print(f"  Found {len(gtf_urls)} possible GTF URLs")
                
                # Try to download GTF
                if self.download_file(gtf_urls, gtf_gz, "GTF", max_retries_per_url=2):
                    # Decompress if download succeeded
                    decompressed = self.decompress_file(gtf_gz)
                    if decompressed:
                        downloaded_files['gtf'] = str(decompressed)
                    else:
                        print(f"  ⚠ GTF download succeeded but decompression failed")
                else:
                    print(f"  ⚠ GTF download failed (genome FASTA was successful)")
                    # Continue without GTF if FASTA was successful
        
        # Download blacklist if available
        print(f"\n{'─' * 50}")
        print(f"3. DOWNLOADING BLACKLIST (if available)")
        print(f"{'─' * 50}")
        
        blacklist_urls = {
            'GRCh38': 'https://raw.githubusercontent.com/Boyle-Lab/Blacklist/master/lists/hg38-blacklist.v2.bed.gz',
            'hg38': 'https://raw.githubusercontent.com/Boyle-Lab/Blacklist/master/lists/hg38-blacklist.v2.bed.gz',
            'GRCh37': 'https://raw.githubusercontent.com/Boyle-Lab/Blacklist/master/lists/hg19-blacklist.v2.bed.gz',
            'hg19': 'https://raw.githubusercontent.com/Boyle-Lab/Blacklist/master/lists/hg19-blacklist.v2.bed.gz',
            'mm10': 'https://raw.githubusercontent.com/Boyle-Lab/Blacklist/master/lists/mm10-blacklist.v2.bed.gz',
            'GRCm38': 'https://raw.githubusercontent.com/Boyle-Lab/Blacklist/master/lists/mm10-blacklist.v2.bed.gz',
            'mm39': 'https://raw.githubusercontent.com/Boyle-Lab/Blacklist/master/lists/mm39-blacklist.v2.bed.gz',
            'GRCm39': 'https://raw.githubusercontent.com/Boyle-Lab/Blacklist/master/lists/mm39-blacklist.v2.bed.gz',
        }
        
        if resolved_name in blacklist_urls:
            blacklist_gz = genome_dir / "blacklist.bed.gz"
            blacklist_file = genome_dir / "blacklist.bed"
            
            if not force and blacklist_file.exists():
                print(f"  ✓ Blacklist already exists: {blacklist_file}")
                downloaded_files['blacklist'] = str(blacklist_file)
            else:
                url = blacklist_urls[resolved_name]
                if self.download_with_requests(url, blacklist_gz):
                    decompressed = self.decompress_file(blacklist_gz)
                    if decompressed:
                        downloaded_files['blacklist'] = str(decompressed)
                        print(f"  ✓ Blacklist downloaded successfully")
                    else:
                        print(f"  ⚠ Blacklist download succeeded but decompression failed")
                else:
                    print(f"  ⚠ Blacklist download failed (optional file)")
        
        # Create metadata file
        metadata = {
            'genome': resolved_name,
            'downloaded': datetime.now().isoformat(),
            'files': downloaded_files,
            'metadata': genome_info,
            'status': 'success' if success else 'partial',
        }
        
        metadata_file = genome_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Final status
        print(f"\n{'='*70}")
        if success and 'fasta' in downloaded_files:
            print(f"✓ SUCCESS: Downloaded {resolved_name}")
            print(f"  Location: {genome_dir}")
            print(f"\n  Downloaded files:")
            for file_type, file_path in downloaded_files.items():
                if Path(file_path).exists():
                    size_mb = Path(file_path).stat().st_size / 1024 / 1024
                    print(f"    • {file_type}: {file_path} ({size_mb:.2f} MB)")
            
            # Show nf-core usage
            print(f"\n  For nf-core pipelines, use:")
            print(f"    --genome {resolved_name}")
            if 'fasta' in downloaded_files:
                print(f"    --fasta {downloaded_files['fasta']}")
            if 'gtf' in downloaded_files:
                print(f"    --gtf {downloaded_files['gtf']}")
            
            return {
                'success': True,
                'genome': resolved_name,
                'directory': str(genome_dir),
                'files': downloaded_files,
            }
        else:
            print(f"✗ FAILED: Could not download {resolved_name}")
            print(f"  Partial downloads in: {genome_dir}")
            
            # Clean up if completely failed
            if 'fasta' not in downloaded_files:
                for f in genome_dir.glob("*"):
                    try:
                        f.unlink()
                    except:
                        pass
                try:
                    genome_dir.rmdir()
                except:
                    pass
            
            return {'success': False, 'genome': resolved_name}
    
    def resolve_genome_name(self, genome_name):
        """Resolve genome name aliases to canonical name"""
        genome_name = genome_name.strip()
        
        if genome_name in self.GENOME_DATABASE:
            return genome_name
        
        for canonical_name, info in self.GENOME_DATABASE.items():
            aliases = info.get('alias', [])
            if genome_name in aliases:
                print(f"Resolved '{genome_name}' to '{canonical_name}'")
                return canonical_name
        
        genome_name_lower = genome_name.lower()
        for canonical_name in self.GENOME_DATABASE.keys():
            if canonical_name.lower() == genome_name_lower:
                print(f"Resolved '{genome_name}' to '{canonical_name}' (case-insensitive)")
                return canonical_name
        
        return None
    
    def list_available_genomes(self):
        """List all available genomes"""
        print("AVAILABLE GENOMES:")
        print("-" * 60)
        
        categories = {
            'Human': [],
            'Mouse': [],
            'Other': []
        }
        
        for genome, info in self.GENOME_DATABASE.items():
            species = info.get('species', '')
            if 'homo_sapiens' in species:
                categories['Human'].append(genome)
            elif 'mus_musculus' in species:
                categories['Mouse'].append(genome)
            else:
                categories['Other'].append(genome)
        
        for category, genomes in categories.items():
            if genomes:
                print(f"\n{category}:")
                for genome in sorted(genomes):
                    info = self.GENOME_DATABASE[genome]
                    species = info.get('species', '').replace('_', ' ').title()
                    source = info.get('source', 'unknown')
                    print(f"  {genome:10} - {species:20} ({source})")
        
        print(f"\nTotal: {len(self.GENOME_DATABASE)} genomes available")
        return list(self.GENOME_DATABASE.keys())

    
    def setup_nfcore_paths(self, genome_name):
        """Setup paths for nf-core pipeline"""
        resolved_name = self.resolve_genome_name(genome_name)
        if not resolved_name:
            raise ValueError(f"Unknown genome: {genome_name}")
        
        genome_dir = self.genome_dir / resolved_name
        
        paths = {
            'genome': resolved_name,
            'fasta': str(genome_dir / "genome.fa"),
            'gtf': str(genome_dir / "genes.gtf"),
            'blacklist': str(genome_dir / "blacklist.bed") if (genome_dir / "blacklist.bed").exists() else None,
        }
        
        return paths
    
    def check_genome_available(self, genome_name, require_gtf=True):
        """Check if a genome is available locally"""
        resolved_name = self.resolve_genome_name(genome_name)
        if not resolved_name:
            return False
        
        genome_dir = self.genome_dir / resolved_name
        
        # Check for required files
        fasta_exists = (genome_dir / "genome.fa").exists()
        if fasta_exists:
            # Check file size
            fasta_size = (genome_dir / "genome.fa").stat().st_size
            if fasta_size < 1000:  # Too small, probably corrupted
                return False
        
        gtf_exists = (genome_dir / "genes.gtf").exists() if require_gtf else True
        if gtf_exists and require_gtf:
            gtf_size = (genome_dir / "genes.gtf").stat().st_size
            if gtf_size < 1000:  # Too small, probably corrupted
                return False
        
        return fasta_exists and gtf_exists
    def check_tools(self):
        """Check if required tools are available"""
        tools = ['wget', 'curl']
        available = []
        
        for tool in tools:
            try:
                subprocess.run(['which', tool], capture_output=True, check=True)
                available.append(tool)
            except:
                pass
        
        print(f"Available download tools: {', '.join(available) if available else 'None (using Python requests)'}")
        return available


def main():
    """Command-line interface for genome downloader"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Download genome references for bioinformatics pipelines',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s GRCh38          # Download GRCh38 (human) genome
  %(prog)s hg38            # Download hg38 (same as GRCh38, from UCSC)
  %(prog)s mm10            # Download mm10 (mouse) genome
  %(prog)s --list          # List all available genomes
  %(prog)s GRCh38 --force  # Force re-download existing genome
        """
    )
    
    parser.add_argument('genome', nargs='?', help='Genome name to download (e.g., GRCh38, hg19, mm10)')
    parser.add_argument('--list', action='store_true', help='List available genomes')
    parser.add_argument('--dir', default='~/igenomes', help='Directory to store genomes (default: ~/igenomes)')
    parser.add_argument('--force', action='store_true', help='Force re-download even if files exist')
    parser.add_argument('--no-gtf', action='store_true', help='Skip GTF annotation download')
    parser.add_argument('--info', metavar='GENOME', help='Show info about a specific genome')
    
    args = parser.parse_args()
    
    downloader = RefGenomeDownloader(args.dir)
    downloader.check_tools()
    
    if args.list:
        downloader.list_available_genomes()
        return
    
    if args.info:
        resolved_name = downloader.resolve_genome_name(args.info)
        if not resolved_name:
            print(f"Error: Unknown genome '{args.info}'")
            return
        
        info = downloader.GENOME_DATABASE[resolved_name]
        print(f"\nGenome Information:")
        print(f"  Name:        {resolved_name}")
        print(f"  Species:     {info.get('species', '').replace('_', ' ').title()}")
        print(f"  Build:       {info.get('build', 'N/A')}")
        print(f"  Source:      {info.get('source', 'unknown')}")
        if 'release' in info:
            print(f"  Release:     {info.get('release', 'N/A')}")
        if 'ucsc_name' in info:
            print(f"  UCSC name:   {info.get('ucsc_name')}")
        if 'alias' in info:
            print(f"  Aliases:     {', '.join(info['alias'])}")
        if 'sources' in info:
            print(f"  Sources:     {', '.join(info['sources'])}")
        return
    
    if args.genome:
        result = downloader.download_genome(
            args.genome,
            download_gtf=not args.no_gtf,
            force=args.force
        )
        
        if not result['success']:
            print(f"\n⚠  Download failed or incomplete.")
            print(f"   Try downloading from UCSC directly:")
            print(f"   For hg38: https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz")
            print(f"   For hg19: https://hgdownload.soe.ucsc.edu/goldenPath/hg19/bigZips/hg19.fa.gz")
            print(f"\n   Or use the UCSC name instead:")
            print(f"   python {sys.argv[0]} hg38")
            sys.exit(1)
    else:
        print("Please specify a genome to download or use --list to see available genomes")
        print(f"\nExample: python {sys.argv[0]} GRCh38")
        print(f"         python {sys.argv[0]} --list")
        sys.exit(1)


if __name__ == "__main__":
    main()