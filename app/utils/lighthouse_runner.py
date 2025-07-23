# lighthouse_runner.py
import asyncio
import subprocess
import json
import os
import tempfile
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class LighthouseRunner:
    def __init__(self):
        self.reports_dir = "/app/reports"
        os.makedirs(self.reports_dir, exist_ok=True)
    
    async def run_audit(self, url: str, device_type: str = "desktop") -> Optional[Dict[str, Any]]:
        """Run Lighthouse audit on a single URL"""
        try:
            # Create temporary file for the report
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_file = f.name
            
            # Configure Lighthouse command
            cmd = [
                'lighthouse',
                url,
                '--output=json',
                f'--output-path={output_file}',
                '--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage',
                '--no-enable-error-reporting',
                '--quiet'
            ]
            
            # Add device emulation
            if device_type == "mobile":
                cmd.extend([
                    '--preset=perf',
                    '--emulated-form-factor=mobile',
                    '--throttling-method=simulate'
                ])
            else:
                cmd.extend([
                    '--preset=perf',
                    '--emulated-form-factor=desktop',
                    '--throttling-method=simulate'
                ])
            
            # Run Lighthouse
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Read the report
                with open(output_file, 'r') as f:
                    report = json.load(f)
                
                # Clean up temporary file
                os.unlink(output_file)
                
                return report
            else:
                logger.error(f"Lighthouse failed for {url}: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error running Lighthouse for {url}: {e}")
            return None
    
    def extract_scores(self, report: Dict[str, Any]) -> Dict[str, float]:
        """Extract scores from Lighthouse report"""
        categories = report.get('categories', {})
        
        return {
            'performance': self._get_score(categories.get('performance')),
            'accessibility': self._get_score(categories.get('accessibility')),
            'best_practices': self._get_score(categories.get('best-practices')),
            'seo': self._get_score(categories.get('seo')),
            'pwa': self._get_score(categories.get('pwa'))
        }
    
    def _get_score(self, category: Optional[Dict]) -> Optional[float]:
        """Extract score from category, convert to percentage"""
        if category and 'score' in category and category['score'] is not None:
            return category['score'] * 100
        return None