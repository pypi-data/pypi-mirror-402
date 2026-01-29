"""
UNO Bridge - Connection manager for LibreOffice via UNO API.

This module provides a singleton connection to LibreOffice running in headless mode.
LibreOffice must be started with:
    soffice --headless --accept="socket,host=localhost,port=2002;urp;"
"""

import logging
import time
from typing import Optional, Any
from pathlib import Path

from ..config import get_config, UnoConfig
from ..utils.exceptions import ConnectionError, LibreOfficeNotRunningError

logger = logging.getLogger(__name__)


class UnoBridge:
    """
    Singleton for managing connection to LibreOffice via UNO API.

    Usage:
        bridge = UnoBridge()
        bridge.connect()
        desktop = bridge.get_desktop()
        doc = desktop.loadComponentFromURL(...)
    """

    _instance: Optional['UnoBridge'] = None
    _initialized: bool = False

    def __new__(cls) -> 'UnoBridge':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if UnoBridge._initialized:
            return

        self._config: UnoConfig = get_config().uno
        self._context: Optional[Any] = None
        self._desktop: Optional[Any] = None
        self._connected: bool = False

        UnoBridge._initialized = True

    @property
    def is_connected(self) -> bool:
        """Check if connected to LibreOffice."""
        return self._connected and self._context is not None

    def connect(self) -> bool:
        """
        Establish connection to LibreOffice headless.

        Returns:
            True if connection successful

        Raises:
            LibreOfficeNotRunningError: If LibreOffice is not running
            ConnectionError: If connection fails after retries
        """
        if self.is_connected:
            logger.debug("Already connected to LibreOffice")
            return True

        # Import uno here to avoid errors when LibreOffice is not available
        try:
            import uno
            from com.sun.star.connection import NoConnectException
        except ImportError as e:
            raise ConnectionError(
                "UNO module not available. Make sure LibreOffice Python is in PATH.",
                {"error": str(e)}
            )

        connection_string = self._config.connection_string
        logger.info(f"Connecting to LibreOffice: {connection_string}")

        for attempt in range(1, self._config.retry_attempts + 1):
            try:
                # Get local context
                local_context = uno.getComponentContext()
                resolver = local_context.ServiceManager.createInstanceWithContext(
                    "com.sun.star.bridge.UnoUrlResolver",
                    local_context
                )

                # Connect to LibreOffice
                self._context = resolver.resolve(connection_string)

                # Get service manager and desktop
                smgr = self._context.ServiceManager
                self._desktop = smgr.createInstanceWithContext(
                    "com.sun.star.frame.Desktop",
                    self._context
                )

                self._connected = True
                logger.info("Successfully connected to LibreOffice")

                # Initialize LeenO macros with the context
                self._initialize_leeno_macros()

                return True

            except NoConnectException as e:
                logger.warning(
                    f"Connection attempt {attempt}/{self._config.retry_attempts} failed: {e}"
                )
                if attempt < self._config.retry_attempts:
                    time.sleep(self._config.retry_delay)
            except Exception as e:
                logger.error(f"Unexpected error connecting to LibreOffice: {e}")
                break

        # All attempts failed
        raise LibreOfficeNotRunningError()

    def _initialize_leeno_macros(self) -> None:
        """Initialize LeenO macro integration with current context."""
        try:
            from .leeno_macros import get_macros
            macros = get_macros()
            if macros.initialize(self._context):
                logger.info("LeenO macros initialized")
            else:
                logger.warning("Failed to initialize LeenO macros")
        except Exception as e:
            logger.warning(f"Could not initialize LeenO macros: {e}")

    def disconnect(self) -> None:
        """Disconnect from LibreOffice."""
        self._context = None
        self._desktop = None
        self._connected = False
        logger.info("Disconnected from LibreOffice")

    def get_desktop(self) -> Any:
        """
        Get LibreOffice desktop object.

        Returns:
            com.sun.star.frame.Desktop

        Raises:
            ConnectionError: If not connected
        """
        if not self.is_connected:
            self.connect()
        return self._desktop

    def get_context(self) -> Any:
        """
        Get UNO component context.

        Returns:
            com.sun.star.uno.XComponentContext
        """
        if not self.is_connected:
            self.connect()
        return self._context

    def get_service_manager(self) -> Any:
        """
        Get UNO service manager.

        Returns:
            com.sun.star.lang.XMultiComponentFactory
        """
        return self.get_context().ServiceManager

    def create_service(self, service_name: str) -> Any:
        """
        Create a UNO service instance.

        Args:
            service_name: Fully qualified service name

        Returns:
            Service instance
        """
        return self.get_service_manager().createInstanceWithContext(
            service_name,
            self.get_context()
        )

    def create_document(self, template_path: Optional[str] = None) -> Any:
        """
        Create a new document from template or blank.

        Args:
            template_path: Path to template file (optional)

        Returns:
            com.sun.star.sheet.SpreadsheetDocument
        """
        try:
            import uno
            from com.sun.star.beans import PropertyValue
        except ImportError:
            raise ConnectionError("UNO module not available")

        desktop = self.get_desktop()

        if template_path:
            # Load from template
            url = self._path_to_url(template_path)
            props = (
                PropertyValue(Name="AsTemplate", Value=True),
                PropertyValue(Name="Hidden", Value=True),
            )
            doc = desktop.loadComponentFromURL(url, "_blank", 0, props)
        else:
            # Create blank spreadsheet
            props = (PropertyValue(Name="Hidden", Value=True),)
            doc = desktop.loadComponentFromURL(
                "private:factory/scalc",
                "_blank",
                0,
                props
            )

        return doc

    def open_document(self, file_path: str, read_only: bool = False) -> Any:
        """
        Open an existing document.

        Args:
            file_path: Path to document file
            read_only: Open in read-only mode

        Returns:
            com.sun.star.sheet.SpreadsheetDocument
        """
        try:
            from com.sun.star.beans import PropertyValue
        except ImportError:
            raise ConnectionError("UNO module not available")

        desktop = self.get_desktop()
        url = self._path_to_url(file_path)

        props = [
            PropertyValue(Name="Hidden", Value=True),
        ]
        if read_only:
            props.append(PropertyValue(Name="ReadOnly", Value=True))

        doc = desktop.loadComponentFromURL(url, "_blank", 0, tuple(props))
        return doc

    def save_document(self, doc: Any, file_path: Optional[str] = None) -> str:
        """
        Save document to file.

        Args:
            doc: Document to save
            file_path: Path to save to (optional, uses current location if not provided)

        Returns:
            Path where document was saved
        """
        try:
            from com.sun.star.beans import PropertyValue
        except ImportError:
            raise ConnectionError("UNO module not available")

        if file_path:
            url = self._path_to_url(file_path)
            props = (
                PropertyValue(Name="FilterName", Value="calc8"),
                PropertyValue(Name="Overwrite", Value=True),
            )
            doc.storeToURL(url, props)
            return file_path
        else:
            doc.store()
            return self._url_to_path(doc.URL)

    def close_document(self, doc: Any) -> None:
        """
        Close a document.

        Args:
            doc: Document to close
        """
        try:
            doc.close(True)
        except Exception as e:
            logger.warning(f"Error closing document: {e}")

    def _path_to_url(self, path: str) -> str:
        """Convert file path to file:// URL."""
        try:
            import uno
            return uno.systemPathToFileUrl(str(Path(path).resolve()))
        except ImportError:
            # Fallback
            path = str(Path(path).resolve())
            if not path.startswith("/"):
                path = "/" + path.replace("\\", "/")
            return f"file://{path}"

    def _url_to_path(self, url: str) -> str:
        """Convert file:// URL to file path."""
        try:
            import uno
            return uno.fileUrlToSystemPath(url)
        except ImportError:
            # Fallback
            if url.startswith("file://"):
                return url[7:]
            return url


# Global bridge instance
_bridge: Optional[UnoBridge] = None


def get_bridge() -> UnoBridge:
    """Get or create global UNO bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = UnoBridge()
    return _bridge
