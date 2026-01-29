"""
Kita Document Processing SDK

A Python client library for the Kita Document Processing API.

Example:
    from kita import KitaClient

    client = KitaClient(api_key="kita_prod_...")
    result = client.process("document.pdf", "bank_statement")
    print(result)
"""

import requests
import time
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any, List, Iterator
from pathlib import Path
import json


class _Spinner:
    """Simple spinner for CLI progress indication"""

    FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def __init__(self, message: str = "Processing"):
        self.message = message
        self._stop_event = threading.Event()
        self._thread = None

    def _spin(self):
        idx = 0
        while not self._stop_event.is_set():
            frame = self.FRAMES[idx % len(self.FRAMES)]
            sys.stdout.write(f'\r{frame} {self.message}...')
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self, final_message: str = None):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        # Clear the line
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        if final_message:
            print(final_message)
        sys.stdout.flush()


class _ProgressBar:
    """Simple progress bar for batch processing"""

    def __init__(self, total: int, prefix: str = "Processing"):
        self.total = total
        self.prefix = prefix
        self.current = 0

    def update(self, current: int, status: str = ""):
        self.current = current
        filled = int(30 * current / self.total) if self.total > 0 else 0
        bar = '█' * filled + '░' * (30 - filled)
        percent = (current / self.total * 100) if self.total > 0 else 0
        status_text = f" - {status}" if status else ""
        sys.stdout.write(f'\r{self.prefix}: [{bar}] {current}/{self.total} ({percent:.0f}%){status_text}')
        sys.stdout.flush()

    def finish(self, message: str = None):
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        if message:
            print(message)
        sys.stdout.flush()


__version__ = "1.1.0"

# Production API URL - override with KITA_API_URL environment variable
DEFAULT_API_URL = "https://api.usekita.com"


class KitaError(Exception):
    """Base exception for Kita SDK errors"""
    pass


class KitaAPIError(KitaError):
    """API returned an error response"""
    def __init__(self, status_code: int, message: str, details: Any = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"API Error {status_code}: {message}")


class KitaAuthenticationError(KitaAPIError):
    """Authentication failed"""
    pass


class KitaRateLimitError(KitaAPIError):
    """Rate limit exceeded"""
    def __init__(self, status_code: int, message: str, retry_after: int = None, details: Any = None):
        super().__init__(status_code, message, details)
        self.retry_after = retry_after


class DocumentResult:
    """Represents a processed document result with dict-like access"""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    # Dict-like access
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access: result['metadata']"""
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator: 'metadata' in result"""
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get with default"""
        return self._data.get(key, default)

    def keys(self):
        """Return available keys"""
        return self._data.keys()

    @property
    def status(self) -> str:
        return self._data.get('status', 'unknown')

    @property
    def document_type(self) -> str:
        return self._data.get('document_type', '')

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._data.get('metadata', {})

    @property
    def transactions(self) -> List[Dict[str, Any]]:
        """Get transactions (for bank statements/passbooks)"""
        return self._data.get('transactions', [])

    @property
    def signals(self) -> Dict[str, Any]:
        """Get financial signals"""
        return self._data.get('signals', {})

    @property
    def raw(self) -> Dict[str, Any]:
        """Get raw response data"""
        return self._data

    def to_dict(self) -> Dict[str, Any]:
        return self._data

    def to_json(self, indent: int = 2) -> str:
        """Return result as formatted JSON string"""
        return json.dumps(self._data, indent=indent, default=str)

    def save_json(self, file_path: str, indent: int = 2) -> None:
        """
        Save result to a JSON file

        Args:
            file_path: Path to save JSON file
            indent: JSON indentation (default: 2)
        """
        with open(file_path, 'w') as f:
            json.dump(self._data, f, indent=indent, default=str)

    def __repr__(self):
        return f"DocumentResult(status={self.status}, type={self.document_type})"


class Batch:
    """
    Represents a batch processing job.

    Usage:
        batch = client.batch_process("/docs", "bank_statement")
        results = batch.results()  # Returns {filepath: DocumentResult}

        # Access by filepath
        results['/docs/statement1.pdf']['metadata']

        # Iterate
        for filepath, result in results.items():
            result.save_json(f"{filepath}.json")
    """

    def __init__(self, batch_id: str, client: 'KitaClient', show_progress: bool = True):
        self.id = batch_id
        self._client = client
        self._show_progress = show_progress
        self._uploads = []  # List of {doc_id, filepath, response}
        self._results = {}  # filepath -> result response

    def _poll_results(self, poll_interval: int = 2, timeout: int = 600, max_workers: int = 10):
        """Poll for all results to complete (with parallel polling)"""
        start_time = time.time()
        total = len(self._uploads)
        progress = _ProgressBar(total, "Processing") if self._show_progress else None

        # Filter out upload failures
        pending = {u['_filepath']: u for u in self._uploads if u.get('status') != 'upload_failed'}
        lock = threading.Lock()

        def check_status(filepath: str, upload: Dict) -> tuple:
            """Check status of a single document"""
            doc_id = upload.get('documentId') or upload.get('document_id')
            if not doc_id:
                return filepath, None, 'no_doc_id'

            try:
                response = self._client._request('GET', f'/api/results/{doc_id}')
                status = response.get('status') or response.get('processing_status', 'pending')
                response['_filepath'] = filepath
                return filepath, response, status
            except Exception:
                return filepath, None, 'pending'

        while pending:
            # Parallel status checks
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(check_status, fp, up) for fp, up in pending.items()]
                for future in as_completed(futures):
                    filepath, response, status = future.result()
                    if status in ['completed', 'failed']:
                        with lock:
                            self._results[filepath] = response
                            if filepath in pending:
                                del pending[filepath]

            if progress:
                done = len(self._results)
                failed = sum(1 for r in self._results.values() if r.get('status') == 'failed')
                progress.update(done, f"{done - failed} completed, {failed} failed")

            if not pending:
                break

            if time.time() - start_time > timeout:
                if progress:
                    progress.finish(f"✗ Batch timed out: {len(self._results)}/{total} completed")
                raise KitaError(f"Batch {self.id} timeout after {timeout}s")

            time.sleep(poll_interval)

        if progress:
            failed = sum(1 for r in self._results.values() if r.get('status') == 'failed')
            succeeded = len(self._results) - failed
            progress.finish(f"✓ Batch complete: {succeeded} succeeded, {failed} failed")

    def results(self, poll_interval: int = 2, timeout: int = 600) -> Dict[str, 'DocumentResult']:
        """
        Wait for batch to complete and return results as a dictionary.

        Returns:
            Dict mapping filepath -> DocumentResult

        Example:
            results = batch.results()
            results['/path/to/doc.pdf']['metadata']

            for filepath, result in results.items():
                result.save_json(f"{filepath}_output.json")
        """
        if not self._results or len(self._results) < len(self._uploads):
            self._poll_results(poll_interval, timeout)

        return {
            filepath: DocumentResult(result)
            for filepath, result in self._results.items()
        }

    @property
    def status(self) -> Dict[str, Any]:
        """Get current batch status"""
        total = len(self._uploads)
        completed = sum(1 for r in self._results.values()
                       if r.get('status') == 'completed' or r.get('processing_status') == 'completed')
        failed = sum(1 for r in self._results.values() if r.get('status') == 'failed')
        pending = total - len(self._results)

        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'pending': pending
        }

    def __len__(self):
        return len(self._uploads)


class KitaClient:
    """
    Kita Document Processing API Client

    Example:
        from kita import KitaClient

        # Initialize with API key (uses production URL by default)
        client = KitaClient(api_key="kita_prod_...")

        # Process single document
        result = client.process("paystub.pdf", "payslip")
        print(result.metadata)
        print(result.transactions)

        # Batch process folder
        batch = client.batch_process("/folder", "bank_statement")
        batch.wait()
        for doc in batch.results():
            print(doc.transactions)

    Environment Variables:
        KITA_API_KEY: Default API key (optional)
        KITA_API_URL: Override default API URL (optional)
    """

    # Supported document types
    DOCUMENT_TYPES = [
        'bank_statement',
        'passbook',
        'payslip',
        'bill',
        'audited_financial_statement',
        'other_document'
    ]

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        timeout: int = 60
    ):
        """
        Initialize Kita client

        Args:
            api_key: Your Kita API key. Can also be set via KITA_API_KEY env var.
            base_url: API base URL. Defaults to production (https://api.usekita.com).
                      Can also be set via KITA_API_URL env var.
            timeout: Request timeout in seconds
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.environ.get('KITA_API_KEY')

        if not self.api_key:
            raise KitaError(
                "API key required. Pass api_key parameter or set KITA_API_KEY environment variable. "
                "Get your API key at https://api.usekita.com/api-keys.html"
            )

        if not self.api_key.startswith('kita_'):
            raise KitaError("Invalid API key format. Must start with 'kita_'")

        # Get base URL from parameter, environment, or default
        self.base_url = (base_url or os.environ.get('KITA_API_URL') or DEFAULT_API_URL).rstrip('/')
        self.timeout = timeout

        # Setup session with auth headers
        self._session = requests.Session()
        self._session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': f'kita-python-sdk/{__version__}',
            'Accept': 'application/json'
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)

        try:
            response = self._session.request(method, url, **kwargs)

            # Handle non-JSON responses
            try:
                data = response.json()
            except json.JSONDecodeError:
                data = {'raw': response.text}

            # Handle errors
            if response.status_code == 401:
                raise KitaAuthenticationError(
                    response.status_code,
                    data.get('message', 'Authentication failed'),
                    data
                )

            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                raise KitaRateLimitError(
                    response.status_code,
                    data.get('message', 'Rate limit exceeded'),
                    int(retry_after) if retry_after else None,
                    data
                )

            if response.status_code >= 400:
                raise KitaAPIError(
                    response.status_code,
                    data.get('message', data.get('error', 'Unknown error')),
                    data
                )

            return data

        except requests.RequestException as e:
            raise KitaError(f"Request failed: {str(e)}")

    def process(
        self,
        file_path: str,
        document_type: str,
        wait: bool = True,
        poll_interval: int = 2,
        timeout: int = 600,
        password: str = None,
        show_progress: bool = True
    ) -> DocumentResult:
        """
        Process a single document

        Args:
            file_path: Path to document file (PDF, PNG, JPG, etc.)
            document_type: Type of document:
                - 'bank_statement': Bank account statements
                - 'passbook': Savings passbooks
                - 'payslip': Salary/pay stubs
                - 'bill': Utility bills
                - 'audited_financial_statement': AFS/annual reports
                - 'other_document': Other document types
            wait: If True, wait for processing to complete (default: True)
            poll_interval: Seconds between status checks (if wait=True)
            timeout: Maximum seconds to wait (if wait=True)
            password: PDF password if document is encrypted
            show_progress: If True, show spinner while processing (default: True)

        Returns:
            DocumentResult object with parsed data

        Example:
            result = client.process("statement.pdf", "bank_statement")
            print(result.metadata)
            for tx in result.transactions:
                print(tx['date'], tx['description'], tx['amount'])
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise KitaError(f"File not found: {file_path}")

        # Normalize document type
        doc_type = document_type.lower().replace(' ', '_').replace('-', '_')

        # Upload file
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, self._get_mime_type(file_path))}
            data = {'document_type': doc_type}

            if password:
                data['password'] = password

            # Use async endpoint for better handling
            response = self._request('POST', '/api/process-async', files=files, data=data)

        if not wait:
            return DocumentResult(response)

        # Poll for completion
        document_id = response.get('documentId') or response.get('document_id')
        if not document_id:
            # Synchronous processing completed
            return DocumentResult(response)

        return self._wait_for_document(document_id, poll_interval, timeout, show_progress, file_path.name)

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type based on file extension"""
        ext = file_path.suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.bmp': 'image/bmp',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'application/octet-stream')

    def _wait_for_document(
        self,
        document_id: str,
        poll_interval: int,
        timeout: int,
        show_progress: bool = True,
        filename: str = None
    ) -> DocumentResult:
        """Wait for a document to be processed"""
        start_time = time.time()
        spinner = None

        if show_progress:
            msg = f"Processing {filename}" if filename else "Processing document"
            spinner = _Spinner(msg)
            spinner.start()

        try:
            while True:
                try:
                    response = self._request('GET', f'/api/results/{document_id}')

                    status = response.get('status') or response.get('processing_status')

                    if status == 'completed':
                        if spinner:
                            spinner.stop(f"✓ {filename or 'Document'} processed successfully")
                        return DocumentResult(response)

                    if status == 'failed':
                        if spinner:
                            spinner.stop(f"✗ {filename or 'Document'} processing failed")
                        error_msg = response.get('error_message', 'Processing failed')
                        raise KitaError(f"Document processing failed: {error_msg}")

                except KitaAPIError as e:
                    if e.status_code != 404:
                        if spinner:
                            spinner.stop()
                        raise
                    # Document not ready yet, continue polling

                if time.time() - start_time > timeout:
                    if spinner:
                        spinner.stop(f"✗ {filename or 'Document'} timed out")
                    raise KitaError(f"Document {document_id} timeout after {timeout}s")

                time.sleep(poll_interval)
        except Exception:
            if spinner:
                spinner.stop()
            raise

    def batch_process(
        self,
        folder_path: str,
        document_type: str,
        extensions: List[str] = None,
        recursive: bool = False,
        max_workers: int = 5,
        show_progress: bool = True
    ) -> 'Batch':
        """
        Process multiple documents from a folder (with parallel uploads)

        Args:
            folder_path: Path to folder containing documents
            document_type: Type of documents (all must be same type)
            extensions: File extensions to include (default: ['.pdf', '.png', '.jpg', '.jpeg'])
            recursive: If True, search subdirectories
            max_workers: Number of parallel upload threads (default: 5)
            show_progress: If True, show progress bars (default: True)

        Returns:
            Batch object - call batch.results() to get {filepath: DocumentResult}

        Example:
            batch = client.batch_process("/docs", "bank_statement")
            results = batch.results()  # {filepath: DocumentResult}

            for filepath, result in results.items():
                result.save_json(f"{filepath}_output.json")
        """
        folder = Path(folder_path)

        if not folder.is_dir():
            raise KitaError(f"Folder not found: {folder_path}")

        if extensions is None:
            extensions = ['.pdf', '.png', '.jpg', '.jpeg']

        # Collect files
        files = []
        for ext in extensions:
            pattern = f'**/*{ext}' if recursive else f'*{ext}'
            files.extend(folder.glob(pattern))

        if not files:
            raise KitaError(f"No files with extensions {extensions} found in {folder_path}")

        # Normalize document type
        doc_type = document_type.lower().replace(' ', '_').replace('-', '_')

        total_files = len(files)
        progress = _ProgressBar(total_files, "Uploading") if show_progress else None
        completed_count = 0
        lock = threading.Lock()

        def upload_file(file_path: Path) -> Dict[str, Any]:
            """Upload a single file and return response with filepath"""
            nonlocal completed_count
            with open(file_path, 'rb') as f:
                upload_files = {'file': (file_path.name, f, self._get_mime_type(file_path))}
                upload_data = {'document_type': doc_type}
                response = self._request('POST', '/api/process-async', files=upload_files, data=upload_data)
                response['_filepath'] = str(file_path)

            with lock:
                completed_count += 1
                if progress:
                    progress.update(completed_count, file_path.name)

            return response

        # Parallel upload with ThreadPoolExecutor
        file_uploads = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(upload_file, fp): fp for fp in files}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    file_uploads.append(result)
                except Exception as e:
                    filepath = futures[future]
                    file_uploads.append({
                        '_filepath': str(filepath),
                        '_error': str(e),
                        'status': 'upload_failed'
                    })

        if progress:
            progress.finish(f"✓ Uploaded {total_files} documents")

        # Create batch
        batch_id = f"batch_{int(time.time())}_{len(files)}"
        batch = Batch(batch_id, self, show_progress=show_progress)
        batch._uploads = file_uploads

        return batch

    def get_document(self, document_id: str) -> DocumentResult:
        """
        Get a processed document by ID

        Args:
            document_id: The document ID

        Returns:
            DocumentResult object
        """
        response = self._request('GET', f'/api/results/{document_id}')
        return DocumentResult(response)

    def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List processed documents

        Args:
            limit: Maximum results to return
            offset: Pagination offset
            status: Filter by status (pending, processing, completed, failed)
            document_type: Filter by document type

        Returns:
            Dictionary with 'documents' list and pagination info
        """
        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status
        if document_type:
            params['document_type'] = document_type.lower()

        return self._request('GET', '/api/documents', params=params)


# Convenience function for quick processing
def process(
    file_path: str,
    document_type: str,
    api_key: str = None,
    **kwargs
) -> DocumentResult:
    """
    Quick function to process a single document

    Args:
        file_path: Path to document
        document_type: Type of document
        api_key: API key (or set KITA_API_KEY env var)
        **kwargs: Additional arguments passed to KitaClient.process()

    Returns:
        DocumentResult object

    Example:
        from kita import process
        result = process("doc.pdf", "bank_statement")
    """
    client = KitaClient(api_key=api_key)
    return client.process(file_path, document_type, **kwargs)


__all__ = [
    'KitaClient',
    'DocumentResult',
    'Batch',
    'KitaError',
    'KitaAPIError',
    'KitaAuthenticationError',
    'KitaRateLimitError',
    'process'
]
