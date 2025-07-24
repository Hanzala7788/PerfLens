import subprocess
import os
import tempfile
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def run_lighthouse_audit(url: str, device_type: str = "desktop") -> Optional[str]:
    """
    Run Lighthouse audit on a URL and return the path to the generated HTML report.
    Returns None if the audit fails.
    """
    try:
        # Debugging output (can remove these print statements once fixed)
        print("\n--- Python Environment Debugging ---")
        python_path = os.environ.get('PATH')
        print(f"Current PATH in Python: {python_path}")
        try:
            where_process = subprocess.run(
                ['where', 'lighthouse'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                check=False
            )
            print(f"'where lighthouse' stdout: {where_process.stdout.strip()}")
            print(f"'where lighthouse' stderr: {where_process.stderr.strip()}")
            if where_process.returncode == 0:
                found_lighthouse_path = where_process.stdout.strip().split('\n')[0]
                print(f"Lighthouse found at (via 'where'): {found_lighthouse_path}")
            else:
                found_lighthouse_path = None
                print("Lighthouse not found by 'where' command within Python subprocess.")
        except Exception as e:
            print(f"Error trying 'where lighthouse': {e}")
            found_lighthouse_path = None
        print("--- END DEBUGGING CODE ---\n")

        # Create temporary file for the HTML report
        # We need to explicitly name it .html
        temp_dir = tempfile.gettempdir()
        output_file = os.path.join(temp_dir, f"lighthouse_report_{os.urandom(8).hex()}.html")
        
        # Use the full, explicit path to lighthouse.cmd
        lighthouse_executable_path = r"C:\Users\MuhammadHanzala\AppData\Roaming\npm\lighthouse.cmd"

        cmd = [
            lighthouse_executable_path, # Use the full, explicit path
            url,
            '--output=html', # <--- CHANGE THIS TO HTML
            f'--output-path={output_file}',
            '--chrome-flags=--headless --no-sandbox',
            '--quiet',
            '--only-categories=performance,accessibility,seo,best-practices,pwa'
        ]
        
        # Specify Chrome path for Windows
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if os.path.exists(chrome_path):
            cmd.append(f'--chrome-path={chrome_path}')
        
        # Add device emulation
        if device_type == "mobile":
            cmd.extend(['--emulated-form-factor=mobile', '--throttling-method=simulate'])
        else:
            cmd.extend(['--emulated-form-factor=desktop', '--throttling-method=simulate'])
        
        # Run Lighthouse
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            timeout=120  # 2-minute timeout
        )
        
        if process.returncode == 0:
            # Check if the HTML file was created
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logger.info(f"Lighthouse HTML report generated at: {output_file}")
                return output_file
            else:
                logger.error(f"Lighthouse succeeded but HTML report file was not found or is empty: {output_file}")
                # Try to clean up if a file was created but is empty
                if os.path.exists(output_file):
                    os.unlink(output_file)
                return None
        else:
            # It's good practice to log the stderr as well, as it might contain
            # useful error messages from Lighthouse itself.
            logger.error(f"Lighthouse failed for {url}: {process.stderr}")
            # Ensure the output_file is cleaned up even on error if it was created
            if os.path.exists(output_file):
                os.unlink(output_file)
            return None
    
    except subprocess.TimeoutExpired:
        logger.error(f"Lighthouse audit timed out for {url}")
        # Ensure the output_file is cleaned up if it was created
        if 'output_file' in locals() and os.path.exists(output_file):
            os.unlink(output_file)
        return None
    except Exception as e:
        logger.error(f"Error running Lighthouse for {url}: {e}")
        # Ensure the output_file is cleaned up if it was created
        if 'output_file' in locals() and os.path.exists(output_file):
            os.unlink(output_file)
        return None

def extract_scores(report: Optional[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    """Extract scores from Lighthouse report."""
    if not report:
        return {
            'performance': None,
            'accessibility': None,
            'best_practices': None,
            'seo': None,
            'pwa': None
        }

    categories = report.get('categories', {})

    def _get_score(category: Optional[Dict]) -> Optional[float]:
        if category and 'score' in category and category['score'] is not None:
            return category['score'] * 100
        return None

    return {
        'performance': _get_score(categories.get('performance')),
        'accessibility': _get_score(categories.get('accessibility')),
        'best_practices': _get_score(categories.get('best-practices')),
        'seo': _get_score(categories.get('seo')),
        'pwa': _get_score(categories.get('pwa'))
    }

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_url = "https://www.google.com"
    
    print(f"\nRunning Lighthouse audit for {test_url} (desktop)...")
    html_report_path = run_lighthouse_audit(test_url, "desktop")

    if html_report_path:
        print(f"Successfully generated HTML report at: {html_report_path}")
        print(f"You can open this file in your browser to view the report.")
        # Optional: Open the report automatically (requires webbrowser module)
        # import webbrowser
        # webbrowser.open(html_report_path)
    else:
        print(f"Failed to generate HTML report for {test_url}.")

    print(f"\nRunning Lighthouse audit for {test_url} (mobile)...")
    html_report_path_mobile = run_lighthouse_audit(test_url, "mobile")

    if html_report_path_mobile:
        print(f"Successfully generated HTML report at: {html_report_path_mobile}")
        print(f"You can open this file in your browser to view the report.")
    else:
        print(f"Failed to generate HTML report for {test_url} (mobile).")