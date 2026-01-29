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
from typing import Optional, Dict, Any, List, Iterator
from pathlib import Path
import json


__version__ = "1.0.1"

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
    """Represents a processed document result"""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

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

    def __repr__(self):
        return f"DocumentResult(status={self.status}, type={self.document_type})"


class Batch:
    """Represents a batch processing job"""

    def __init__(self, batch_id: str, client: 'KitaClient'):
        self.id = batch_id
        self._client = client
        self._status_data = None

    def status(self) -> Dict[str, Any]:
        """Get current batch status"""
        response = self._client._request('GET', f'/api/v1/batch/{self.id}')
        self._status_data = response
        return response

    def wait(self, poll_interval: int = 2, timeout: int = 600) -> Dict[str, Any]:
        """
        Wait for batch to complete

        Args:
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait

        Returns:
            Final batch status
        """
        start_time = time.time()

        while True:
            status = self.status()

            if status['status'] in ['completed', 'failed', 'cancelled']:
                return status

            if time.time() - start_time > timeout:
                raise KitaError(f"Batch {self.id} timeout after {timeout}s")

            time.sleep(poll_interval)

    def results(self) -> Iterator[DocumentResult]:
        """
        Iterate over completed document results

        Yields:
            DocumentResult objects
        """
        status = self.status()

        if status['status'] != 'completed':
            self.wait()
            status = self.status()

        for doc in status.get('documents', []):
            if doc.get('status') == 'completed' and doc.get('result'):
                yield DocumentResult(doc['result'])

    @property
    def completed(self) -> bool:
        """Check if batch is completed"""
        if not self._status_data:
            self.status()
        return self._status_data.get('status') == 'completed'

    @property
    def progress(self) -> Dict[str, int]:
        """Get progress counts"""
        if not self._status_data:
            self.status()
        return {
            'total': self._status_data.get('total_documents', 0),
            'completed': self._status_data.get('documents_completed', 0),
            'failed': self._status_data.get('documents_failed', 0),
            'pending': self._status_data.get('documents_pending', 0)
        }


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
        password: str = None
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

        return self._wait_for_document(document_id, poll_interval, timeout)

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
        timeout: int
    ) -> DocumentResult:
        """Wait for a document to be processed"""
        start_time = time.time()

        while True:
            try:
                response = self._request('GET', f'/api/results/{document_id}')

                status = response.get('status') or response.get('processing_status')

                if status == 'completed':
                    return DocumentResult(response)

                if status == 'failed':
                    error_msg = response.get('error_message', 'Processing failed')
                    raise KitaError(f"Document processing failed: {error_msg}")

            except KitaAPIError as e:
                if e.status_code != 404:
                    raise
                # Document not ready yet, continue polling

            if time.time() - start_time > timeout:
                raise KitaError(f"Document {document_id} timeout after {timeout}s")

            time.sleep(poll_interval)

    def batch_process(
        self,
        folder_path: str,
        document_type: str,
        wait: bool = False,
        extensions: List[str] = None,
        recursive: bool = False
    ) -> Batch:
        """
        Process multiple documents from a folder

        Args:
            folder_path: Path to folder containing documents
            document_type: Type of documents (all must be same type)
            wait: If True, wait for batch to complete before returning
            extensions: File extensions to include (default: ['.pdf'])
            recursive: If True, search subdirectories

        Returns:
            Batch object for tracking progress

        Example:
            batch = client.batch_process("/docs", "bank_statement")
            batch.wait()
            for result in batch.results():
                print(result.transactions)
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

        # Upload files and create batch
        file_uploads = []
        for file_path in files:
            with open(file_path, 'rb') as f:
                upload_files = {'file': (file_path.name, f, self._get_mime_type(file_path))}
                upload_data = {'document_type': doc_type}
                response = self._request('POST', '/api/process-async', files=upload_files, data=upload_data)
                file_uploads.append(response)

        # Create a virtual batch from individual uploads
        batch_id = f"batch_{int(time.time())}_{len(files)}"

        batch = Batch(batch_id, self)
        batch._uploads = file_uploads

        if wait:
            batch.wait()

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
