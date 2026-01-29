"""
SDK Management - Handle SDK generation and distribution.

FIXED v2.1:
- ✅ Better domain context in error messages and logging
- ✅ Consistent validation patterns
- ✅ Improved error handling
- ✅ Fixed regenerate_all_sdks() default languages to include 'javascript'
- ✅ Added SUPPORTED_LANGUAGES and DEFAULT_LANGUAGES class constants
- ✅ Consistent language validation across all methods

UPDATED v2.2:
- ✅ Added per-call api_key support for RBAC enforcement
- ✅ All methods accept optional api_key parameter

FIXED v2.3:
- ✅ Replaced _get_headers() pattern with api_key kwarg pattern
- ✅ Now matches UserManager RBAC implementation
- ✅ Tests now pass for api_key parameter

Manages:
- SDK generation for domain schemas
- SDK download and distribution
- SDK version management
- Language-specific SDK creation
"""

import os
from typing import Dict, List, Any, Optional
import logging
import time

class SDKManager:
    """
    Manages SDK operations for a domain.
    
    Handles:
    - SDK generation (Python, JavaScript, Go, etc.)
    - SDK download and installation
    - Version management
    - Schema inclusion/exclusion

    RBAC Support (v2.2):
        All methods accept optional api_key parameter for per-call
        API key override, enabling multi-user server applications:

        >>> # Multi-user server scenario
        >>> sdk_mgr = SDKManager(domain_name, client)
        >>> 
        >>> # Each request uses user's API key
        >>> sdk_mgr.generate_sdk(language='python', api_key=user_key)
        >>> sdk_mgr.list_sdks(api_key=admin_key)
    """
    
    # Supported SDK languages
    SUPPORTED_LANGUAGES = ['python', 'javascript', 'typescript', 'go', 'java', 'csharp']
    
    # Default languages for multi-language operations
    DEFAULT_LANGUAGES = ['python', 'javascript']
    
    def __init__(
        self, 
        platform_client, 
        logger: logging.Logger = None,
        api_key: str = None
    ):
        """
        Initialize SDKManager.
        
        Args:
            platform_client: PlatformClient instance for API calls
            logger: Logger instance (creates new if None)
            api_key: Default API key for RBAC (can be overridden per-call)

        ✅ ADDED: Default api_key support for RBAC (v2.2)
        """
        self.client = platform_client
        self.logger = logger or logging.getLogger(__name__)
        self._default_api_key = api_key  # ✅ NEW: Store default API key
        
        # ✅ Extract from client (v3.0 context-aware)
        self.domain_name = platform_client.domain_name
        self.domain_uuid = platform_client.domain_uuid
        
        # Log initialization
        self.logger.debug(f"SDKManager initialized for domain: {self.domain_name}")
        self.logger.debug(f"  Supported languages: {self.SUPPORTED_LANGUAGES}")

    def _resolve_api_key(self, api_key: str = None) -> Optional[str]:
        """
        Resolve API key to use for a request.

        Priority:
        1. Per-call api_key parameter (if provided)
        2. Instance default api_key (if set)
        3. None (use client's default authentication)

        Args:
            api_key: Per-call API key override

        Returns:
            Resolved API key or None

        ✅ NEW: Helper method for RBAC (v2.2)
        """
        if api_key is not None:
            return api_key
        return self._default_api_key
    
    # ============================================
    # SDK GENERATION
    # ============================================
    
    def generate_sdk(
        self,
        language: str = 'python',
        version: str = None,
        include_schemas: List[str] = None,
        exclude_schemas: List[str] = None,
        output_format: str = None,
        package_name: str = None,
        api_key: str = None,
        **options
    ) -> Dict[str, Any]:
        """
        Generate SDK package for this domain's schemas.

        Creates a language-specific SDK with generated code for all schemas.

        Args:
            language: SDK language ('python', 'javascript', 'go', 'java', 'typescript', 'csharp')
            version: SDK version (auto-incremented if None)
            include_schemas: Schemas to include (all if None)
            exclude_schemas: Schemas to exclude
            output_format: Output format (auto-detected if None)
            package_name: Custom package name (auto-generated if None)
            api_key: Optional API key for RBAC (overrides instance default)
            **options: Additional SDK options

        Returns:
            SDK generation result dict

        ✅ FIXED v2.3: Uses api_key kwarg pattern (matches UserManager)
        """
        # Normalize language
        language = language.lower().strip()
        
        # Validate language
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {language} for domain '{self.domain_name}'. "
                f"Supported: {', '.join(self.SUPPORTED_LANGUAGES)}"
            )
        
        # Auto-detect output format if not provided
        if output_format is None:
            output_format = self._get_default_output_format(language)

        # Build payload
        payload = {
            'domain_name': self.domain_name,
            'language': language,
            'output_format': output_format,
        }

        # Add optional fields only if provided
        if version:
            payload['version'] = version
        if include_schemas:
            payload['include_schemas'] = include_schemas
        if exclude_schemas:
            payload['exclude_schemas'] = exclude_schemas
        if package_name:
            payload['package_name'] = package_name

        # Flatten all **options kwargs into top-level payload
        payload.update(options)

        self.logger.info(
            f"Generating {language} SDK for domain '{self.domain_name}'..."
        )

        # ✅ FIXED v2.3: Pass api_key as kwarg (not in headers)
        kwargs = {'json': payload}
        if api_key:
            kwargs['api_key'] = api_key

        # Generate SDK via Platform Core
        try:
            result = self.client.post('/sdks/generate', **kwargs)
        except Exception as e:
            self.logger.error(
                f"Failed to generate {language} SDK for domain '{self.domain_name}': {e}"
            )
            raise

        # Get metrics from result
        schemas_count = len(result.get('schemas_included', []))
        size_bytes = result.get('size_bytes', 0)
        size_kb = size_bytes / 1024

        version = result.get('version') or 'latest'
        self.logger.info(
            f"✓ SDK generated for '{self.domain_name}': {language} version: {result.get('version')} "
            f"({schemas_count} schemas, {size_kb:.1f} KB)"
        )

        # Optional: Warn about large SDKs
        if size_bytes > 10 * 1024 * 1024:  # > 10 MB
            self.logger.warning(
                f"⚠️ SDK is large ({size_kb / 1024:.1f} MB) for domain '{self.domain_name}'. "
                "Consider excluding unused schemas."
            )

        return result

    def generate_multi_language(
        self,
        languages: List[str] = None,
        api_key: str = None,
        **common_options
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate SDKs for multiple languages simultaneously.
        
        Args:
            languages: List of languages to generate (defaults to DEFAULT_LANGUAGES)
            api_key: Optional API key for RBAC (overrides instance default)
            **common_options: Common options applied to all SDKs
        
        Returns:
            Dict with results for each language
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        # Use default languages if not specified
        if languages is None:
            languages = self.DEFAULT_LANGUAGES.copy()
        
        results = {}
        errors = {}
        
        self.logger.info(
            f"Generating SDKs for {len(languages)} languages in domain '{self.domain_name}': {languages}"
        )
        
        for language in languages:
            try:
                # ✅ RBAC: Pass api_key through
                result = self.generate_sdk(
                    language=language,
                    api_key=api_key,
                    **common_options
                )
                results[language] = result
                self.logger.info(f"  ✓ {language} SDK generated")
            except Exception as e:
                errors[language] = str(e)
                self.logger.error(
                    f"  ✗ Failed to generate {language} SDK for '{self.domain_name}': {e}"
                )
        
        if errors:
            results['errors'] = errors
        
        self.logger.info(
            f"Multi-language SDK generation for '{self.domain_name}': "
            f"{len(results) - (1 if errors else 0)} succeeded, "
            f"{len(errors)} failed"
        )
        
        return results
    
    # ============================================
    # SDK DOWNLOAD
    # ============================================
    
    def download_sdk(
        self,
        sdk_uuid: str = None,
        version: str = None,
        language: str = None,
        output_path: str = None,
        output_dir: str = None,  # Backward compatibility
        artifact: str = None,
        api_key: str = None
    ) -> str:
        """
        Download SDK package.

        Args:
            sdk_uuid: SDK UUID (from generate_sdk)
            version: SDK version (latest if None)
            language: SDK language (required if version specified)
            output_path: Full output file path (optional)
            output_dir: Output directory - uses server's filename (optional)
            artifact: Artifact type (auto-detected if None)
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Path to downloaded file

        ✅ FIXED v2.3: Uses api_key kwarg pattern
        """
        # Handle backward compatibility: output_dir -> output_path
        if output_dir and not output_path:
            output_path = output_dir
        
        # Auto-detect artifact type based on language
        if artifact is None:
            artifact = self._get_default_artifact(language)

        # Build download URL
        if sdk_uuid:
            url = f'/sdks/{sdk_uuid}/download'
            params = {'artifact': artifact}
            log_id = f"SDK {sdk_uuid[:8]}..."
        elif version and language:
            url = '/sdks/download'
            params = {
                'domain': self.domain_name,
                'version': version,
                'language': language,
                'artifact': artifact
            }
            log_id = f"{language} SDK v{version}"
        else:
            url = '/sdks/download/latest'
            params = {
                'domain': self.domain_name,
                'artifact': artifact
            }
            if language:
                params['language'] = language
            log_id = f"latest {language or 'SDK'}"

        self.logger.info(f"Downloading {log_id} for domain '{self.domain_name}'...")

        # Build full URL if params exist
        if params:
            from urllib.parse import urlencode
            query_string = urlencode(params)
            full_url = f"{url}?{query_string}"
        else:
            full_url = url

        # ✅ FIXED v2.3: Pass api_key as kwarg (not in headers)
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key

        # Download file
        try:
            response = self.client.get_file(full_url, **kwargs)
        except Exception as e:
            self.logger.error(
                f"Failed to download {log_id} for domain '{self.domain_name}': {e}"
            )
            raise

        # Determine output path
        final_path = None

        # Case 1: Full file path provided (has extension)
        if output_path and os.path.splitext(output_path)[1]:
            final_path = output_path

        # Case 2: Directory provided or no output_path
        else:
            # Extract filename from Content-Disposition header
            server_filename = None
            content_disp = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disp:
                server_filename = content_disp.split('filename=')[1].strip('"').strip("'")

            if server_filename:
                if output_path:
                    final_path = os.path.join(output_path, server_filename)
                else:
                    final_path = os.path.join(os.getcwd(), server_filename)
            else:
                # Fallback
                ext = self._get_default_extension(language or 'python')
                fallback_name = f"{self.domain_name}_sdk{ext}"
                if output_path:
                    final_path = os.path.join(output_path, fallback_name)
                else:
                    final_path = os.path.join(os.getcwd(), fallback_name)

        # Ensure directory exists
        os.makedirs(os.path.dirname(final_path) or '.', exist_ok=True)

        # Save file
        with open(final_path, 'wb') as f:
            f.write(response.content)

        file_size = os.path.getsize(final_path)
        self.logger.info(
            f"✓ SDK downloaded for '{self.domain_name}': {final_path} ({file_size / 1024:.1f} KB)"
        )

        return final_path
    
    def download_all_languages(
        self,
        version: str = None,
        output_directory: str = '.',
        api_key: str = None
    ) -> Dict[str, str]:
        """
        Download SDKs for all available languages.

        Args:
            version: SDK version (latest if None)
            output_directory: Directory to save SDKs
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Dict mapping language to downloaded file path

        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        # Get available SDKs
        try:
            sdks = self.list_sdks(version=version, api_key=api_key)
        except Exception as e:
            self.logger.error(
                f"Failed to list SDKs for domain '{self.domain_name}': {e}"
            )
            raise

        results = {}
        errors = {}

        self.logger.info(
            f"Downloading {len(sdks)} SDKs for domain '{self.domain_name}'..."
        )

        for sdk_info in sdks:
            language = sdk_info['language']
            sdk_uuid = sdk_info['sdk_uuid']

            try:
                ext = self._get_default_extension(language)
                filename = f"{self.domain_name}_{language}_{sdk_info['version']}{ext}"
                output_path = os.path.join(output_directory, filename)

                path = self.download_sdk(
                    sdk_uuid=sdk_uuid, 
                    output_path=output_path,
                    api_key=api_key
                )
                results[language] = path

            except Exception as e:
                errors[language] = str(e)
                self.logger.error(
                    f"  ✗ Failed to download {language} SDK for '{self.domain_name}': {e}"
                )

        if errors:
            results['errors'] = errors

        return results
    
    # ============================================
    # SDK LISTING & INFO
    # ============================================
    
    def list_sdks(
        self,
        language: str = None,
        version: str = None,
        status: str = 'active',
        api_key: str = None
    ) -> List[Dict[str, Any]]:
        """
        List available SDK packages for this domain.

        Args:
            language: Filter by language
            version: Filter by version
            status: Filter by status (default: 'active')
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            List of SDK info dicts
        
        ✅ FIXED v2.3: Uses api_key kwarg pattern (matches UserManager)
        """
        params = {'limit': 50}  # Default limit

        if language:
            params['language'] = language
        if version:
            params['version'] = version
        if status:
            params['status'] = status

        # ✅ FIXED v2.3: Pass api_key as kwarg (not in headers)
        kwargs = {'params': params}
        if api_key:
            kwargs['api_key'] = api_key

        try:
            return self.client.get(
                f'/domains/{self.domain_name}/sdks', 
                **kwargs
            )
        except Exception as e:
            self.logger.error(
                f"Failed to list SDKs for domain '{self.domain_name}': {e}"
            )
            raise
    
    def get_sdk_info(self, sdk_uuid: str, api_key: str = None) -> Dict[str, Any]:
        """
        Alias for get_sdk() for backward compatibility.
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        return self.get_sdk(sdk_uuid, api_key=api_key)

    def get_sdk(self, sdk_uuid: str, api_key: str = None) -> Dict[str, Any]:
        """
        Get SDK details by UUID.
        
        Args:
            sdk_uuid: SDK UUID
            api_key: Optional API key for RBAC (overrides instance default)
        
        Returns:
            SDK info dict
        
        ✅ FIXED v2.3: Uses api_key kwarg pattern (matches UserManager)
        """
        if not sdk_uuid:
            raise ValueError("sdk_uuid is required")
        
        # ✅ FIXED v2.3: Pass api_key as kwarg (not in headers)
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key
        
        try:
            return self.client.get(f'/sdks/{sdk_uuid}', **kwargs)
        except Exception as e:
            self.logger.error(
                f"Failed to get SDK {sdk_uuid} for domain '{self.domain_name}': {e}"
            )
            raise
    
    def get_latest_sdk(
        self,
        language: str = None,
        api_key: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get latest SDK for domain (optionally filtered by language).
        
        Args:
            language: Filter by language (optional)
            api_key: Optional API key for RBAC (overrides instance default)
        
        Returns:
            Latest SDK info or None if no SDKs found
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        try:
            sdks = self.list_sdks(language=language, api_key=api_key)
        except Exception as e:
            self.logger.error(
                f"Failed to get latest SDK for domain '{self.domain_name}': {e}"
            )
            raise
        
        if not sdks:
            return None
        
        # Sort by created_at descending
        sorted_sdks = sorted(
            sdks,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
        
        return sorted_sdks[0]

    def get_latest_version(
        self,
        language: str = None,
        api_key: str = None
    ) -> str:
        """
        Get latest SDK version for domain.

        Args:
            language: Filter by language (all languages if None)
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Latest version string (e.g., '1.2.3')
        
        ✅ FIXED v2.3: Uses api_key kwarg pattern (matches UserManager)
        """
        params = {}
        if language:
            params['language'] = language

        # ✅ FIXED v2.3: Pass api_key as kwarg (not in headers)
        kwargs = {'params': params}
        if api_key:
            kwargs['api_key'] = api_key

        try:
            result = self.client.get(
                f'/domains/{self.domain_name}/sdks/history', 
                **kwargs
            )
        except Exception as e:
            self.logger.error(
                f"Failed to get latest version for domain '{self.domain_name}': {e}"
            )
            raise

        # Parse response to get latest version
        languages_data = result.get('languages', {})

        if language and language in languages_data:
            return languages_data[language].get('latest_version')
        elif not language and languages_data:
            # Return latest across all languages
            all_versions = [
                data.get('latest_version')
                for data in languages_data.values()
                if data.get('latest_version')
            ]
            return max(all_versions) if all_versions else None

        return None

    # ============================================
    # SDK DELETION & CLEANUP
    # ============================================
    
    def delete_sdk(
        self,
        sdk_uuid: str,
        delete_artifacts: bool = True,
        api_key: str = None
    ) -> bool:
        """
        Delete SDK package.

        Args:
            sdk_uuid: SDK UUID
            delete_artifacts: Delete S3 artifacts (default: True)
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            True if successful
        
        ✅ FIXED v2.3: Uses api_key kwarg pattern (matches UserManager)
        """
        if not sdk_uuid:
            raise ValueError("sdk_uuid is required")
        
        self.logger.info(f"🗑️  Deleting SDK {sdk_uuid[:8]}... for domain '{self.domain_name}'")

        params = {'delete_artifacts': 'true' if delete_artifacts else 'false'}

        # ✅ FIXED v2.3: Pass api_key as kwarg (not in headers)
        kwargs = {'params': params}
        if api_key:
            kwargs['api_key'] = api_key

        try:
            response = self.client.delete(
                f'/sdks/{sdk_uuid}', 
                **kwargs
            )
        except Exception as e:
            self.logger.error(
                f"Failed to delete SDK {sdk_uuid} for domain '{self.domain_name}': {e}"
            )
            raise

        if response.get('success', False):
            self.logger.info(f"✓ Deleted SDK {sdk_uuid[:8]}... for domain '{self.domain_name}'")

        return response.get('success', False)
    
    def delete_version(
        self,
        version: str,
        language: str = None,
        api_key: str = None
    ) -> Dict[str, Any]:
        """
        Delete all SDKs of a specific version.

        Args:
            version: Version to delete
            language: Delete specific language only (all if None)
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Dict with 'deleted' and 'failed' lists
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        # Get SDKs for this version
        try:
            sdks = self.list_sdks(version=version, language=language, api_key=api_key)
        except Exception as e:
            self.logger.error(
                f"Failed to list SDKs for version {version} in domain '{self.domain_name}': {e}"
            )
            raise

        deleted = []
        failed = []

        self.logger.info(
            f"Deleting version {version} for domain '{self.domain_name}' ({len(sdks)} SDKs)..."
        )

        for sdk in sdks:
            try:
                success = self.delete_sdk(sdk['sdk_uuid'], api_key=api_key)
                if success:
                    deleted.append(sdk['sdk_uuid'])
                else:
                    failed.append(sdk['sdk_uuid'])
            except Exception as e:
                failed.append(sdk['sdk_uuid'])
                self.logger.error(
                    f"  ✗ Failed to delete {sdk['sdk_uuid']} for '{self.domain_name}': {e}"
                )

        self.logger.info(
            f"Version {version} cleanup for '{self.domain_name}': "
            f"{len(deleted)} deleted, {len(failed)} failed"
        )

        return {
            'deleted': deleted,
            'failed': failed
        }
    
    # ============================================
    # SDK INSTALLATION HELPERS
    # ============================================
    
    def install_python_sdk(
        self,
        sdk_uuid: str = None,
        version: str = None,
        upgrade: bool = True,
        api_key: str = None
    ) -> bool:
        """
        Download and install Python SDK using pip.
        
        Args:
            sdk_uuid: SDK UUID
            version: SDK version (latest if None)
            upgrade: Upgrade if already installed
            api_key: Optional API key for RBAC (overrides instance default)
        
        Returns:
            True if installation successful
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        import subprocess
        
        # Download SDK
        try:
            sdk_path = self.download_sdk(
                sdk_uuid=sdk_uuid,
                version=version,
                language='python',
                api_key=api_key
            )
        except Exception as e:
            self.logger.error(
                f"Failed to download Python SDK for domain '{self.domain_name}': {e}"
            )
            return False
        
        # Install with pip
        cmd = ['pip', 'install', '--force-reinstall', '--no-deps']
        cmd.append(sdk_path)
        
        self.logger.info(f"Installing Python SDK for '{self.domain_name}': {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.logger.info(f"✓ Python SDK installed successfully for '{self.domain_name}'")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"✗ Installation failed for domain '{self.domain_name}': {e.stderr}"
            )
            return False
    
    def install_javascript_sdk(
        self,
        sdk_uuid: str = None,
        version: str = None,
        global_install: bool = False,
        api_key: str = None
    ) -> bool:
        """
        Download and install JavaScript SDK using npm.
        
        Args:
            sdk_uuid: SDK UUID
            version: SDK version (latest if None)
            global_install: Install globally with -g flag
            api_key: Optional API key for RBAC (overrides instance default)
        
        Returns:
            True if installation successful
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        import subprocess
        
        # Download SDK
        try:
            sdk_path = self.download_sdk(
                sdk_uuid=sdk_uuid,
                version=version,
                language='javascript',
                artifact='supero_js_tarball',
                api_key=api_key
            )
        except Exception as e:
            self.logger.error(
                f"Failed to download JavaScript SDK for domain '{self.domain_name}': {e}"
            )
            return False
        
        # Install with npm
        cmd = ['npm', 'install']
        if global_install:
            cmd.append('-g')
        cmd.append(sdk_path)
        
        self.logger.info(f"Installing JavaScript SDK for '{self.domain_name}': {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.logger.info(f"✓ JavaScript SDK installed successfully for '{self.domain_name}'")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"✗ Installation failed for domain '{self.domain_name}': {e.stderr}"
            )
            return False
    
    def get_installation_instructions(
        self,
        language: str,
        sdk_uuid: str = None,
        version: str = None
    ) -> str:
        """
        Get installation instructions for SDK.
        
        Args:
            language: SDK language
            sdk_uuid: SDK UUID
            version: SDK version
        
        Returns:
            Installation instructions as string
        """
        # Normalize language
        language = language.lower().strip()
        
        # Download URL
        if sdk_uuid:
            download_cmd = f"curl -O http://platform-core:8083/api/v1/sdk/download/{sdk_uuid}"
        elif version:
            download_cmd = f"curl -O http://platform-core:8083/api/v1/sdk/download?domain={self.domain_name}&version={version}&language={language}"
        else:
            download_cmd = f"curl -O http://platform-core:8083/api/v1/sdk/download/latest?domain={self.domain_name}&language={language}"
        
        # Underscore version of domain name for package imports
        domain_underscore = self.domain_name.replace('-', '_')
        
        instructions = {
            'python': f"""
# Python SDK Installation for {self.domain_name}

## Download SDK:
{download_cmd}

## Install with pip:
pip install {self.domain_name}_sdk-*.whl

## Usage:
import {domain_underscore}_sdk
org = {domain_underscore}_sdk.quickstart('{self.domain_name}', jwt_token='...')
            """,
            
            'javascript': f"""
# JavaScript SDK Installation for {self.domain_name}

## Download SDK:
{download_cmd}

## Install with npm:
npm install ./supero-supero_js_{domain_underscore}-*.tgz

## Usage (Node.js):
const {{ Supero }} = require('@supero/supero_js_{domain_underscore}');
const org = await Supero.quickstart('{self.domain_name}', {{ apiKey: '...' }});
            """
        }
        
        return instructions.get(language, f"Instructions not available for {language}")
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _get_default_extension(self, language: str) -> str:
        """Get default file extension for language."""
        extensions = {
            'python': '.whl',
            'javascript': '.tgz',
            'typescript': '.tgz',
            'go': '.tar.gz',
            'java': '.jar',
            'csharp': '.nupkg'
        }
        return extensions.get(language, '.tar.gz')
    
    def _get_default_output_format(self, language: str) -> str:
        """Get default output format for language."""
        formats = {
            'python': 'wheel',
            'javascript': 'npm',
            'typescript': 'npm',
            'go': 'module',
            'java': 'jar',
            'csharp': 'nupkg'
        }
        return formats.get(language, 'tar.gz')
    
    def _get_default_artifact(self, language: str) -> str:
        """Get default artifact type for language."""
        artifacts = {
            'python': 'wheel',
            'javascript': 'supero_js_tarball',
            'typescript': 'supero_js_tarball',
            'go': 'tarball',
            'java': 'jar',
            'csharp': 'nupkg'
        }
        return artifacts.get(language, 'tarball')

    def regenerate_all_sdks(
        self,
        version: str = None,
        delete_old: bool = True,
        languages: List[str] = None,
        api_key: str = None
    ) -> Dict[str, Any]:
        """
        Regenerate all SDKs for domain.
        
        Args:
            version: New version for SDKs
            delete_old: Whether to delete old SDKs first (default: True)
            languages: Languages to regenerate (defaults to DEFAULT_LANGUAGES)
            api_key: Optional API key for RBAC (overrides instance default)
        
        Returns:
            Dict with 'deleted' and 'generated' results
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        if languages is None:
            languages = self.DEFAULT_LANGUAGES.copy()
        
        results = {
            'deleted': [],
            'generated': [],
            'failed': []
        }
        
        self.logger.info(
            f"Regenerating SDKs for domain '{self.domain_name}' "
            f"(languages={languages}, delete_old={delete_old})..."
        )
        
        # Delete old SDKs if requested
        if delete_old:
            try:
                old_sdks = self.list_sdks(api_key=api_key)
                for sdk in old_sdks:
                    try:
                        self.delete_sdk(sdk['sdk_uuid'], api_key=api_key)
                        results['deleted'].append(sdk['sdk_uuid'])
                    except Exception as e:
                        self.logger.error(
                            f"Failed to delete {sdk['sdk_uuid']} for '{self.domain_name}': {e}"
                        )
            except Exception as e:
                self.logger.error(
                    f"Failed to list SDKs for cleanup in domain '{self.domain_name}': {e}"
                )
        
        # Generate new SDKs
        gen_result = self.generate_multi_language(
            languages=languages,
            version=version,
            api_key=api_key
        )
        
        results['generated'] = [k for k in gen_result.keys() if k != 'errors']
        if 'errors' in gen_result:
            results['failed'].extend(list(gen_result['errors'].keys()))
        
        self.logger.info(
            f"Regeneration complete for '{self.domain_name}': "
            f"{len(results['generated'])} generated, {len(results['failed'])} failed"
        )
        
        return results

    def check_status(self, sdk_uuid: str, api_key: str = None) -> Dict[str, Any]:
        """
        Check SDK generation status.

        Args:
            sdk_uuid: SDK UUID
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Status dict
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        return self.get_sdk(sdk_uuid, api_key=api_key)

    def wait_for_completion(
        self,
        sdk_uuid: str,
        timeout: int = 300,
        poll_interval: int = 5,
        api_key: str = None
    ) -> Dict[str, Any]:
        """
        Wait for SDK generation to complete.
        
        Args:
            sdk_uuid: SDK UUID
            timeout: Maximum wait time in seconds (default: 300)
            poll_interval: Time between status checks (default: 5)
            api_key: Optional API key for RBAC (overrides instance default)
        
        Returns:
            Final SDK status dict
        
        Raises:
            TimeoutError: If SDK not completed within timeout
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        start_time = time.time()
        
        self.logger.info(
            f"Waiting for SDK {sdk_uuid[:8]}... completion for domain '{self.domain_name}'..."
        )
        
        while time.time() - start_time < timeout:
            try:
                status = self.check_status(sdk_uuid, api_key=api_key)
            except Exception as e:
                self.logger.error(
                    f"Failed to check status for SDK {sdk_uuid} in domain '{self.domain_name}': {e}"
                )
                raise
            
            if status.get('status') == 'completed':
                self.logger.info(f"✓ SDK {sdk_uuid[:8]}... completed for '{self.domain_name}'")
                return status
            
            elif status.get('status') == 'failed':
                error = status.get('error', 'Unknown error')
                self.logger.error(
                    f"✗ SDK {sdk_uuid[:8]}... failed for '{self.domain_name}': {error}"
                )
                return status
            
            # Still pending
            progress = status.get('progress', 0)
            self.logger.debug(
                f"SDK {sdk_uuid[:8]}... in progress for '{self.domain_name}': {progress}%"
            )
            
            time.sleep(poll_interval)
        
        raise TimeoutError(
            f"SDK generation timed out after {timeout} seconds for domain '{self.domain_name}'"
        )
    
    def get_sdk_stats(self, api_key: str = None) -> Dict[str, Any]:
        """
        Get SDK statistics for domain.

        Args:
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Dict with statistics
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        try:
            sdks = self.list_sdks(api_key=api_key)
        except Exception as e:
            self.logger.error(
                f"Failed to get SDK stats for domain '{self.domain_name}': {e}"
            )
            raise

        stats = {
            'total': len(sdks),
            'by_language': {},
            'by_status': {},
            'by_version': {}
        }

        for sdk in sdks:
            # By language
            lang = sdk.get('language', 'unknown')
            stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1

            # By status
            status = sdk.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

            # By version
            version = sdk.get('version', 'unknown')
            stats['by_version'][version] = stats['by_version'].get(version, 0) + 1

        return stats

    def list_versions(
        self,
        language: str = None,
        api_key: str = None
    ) -> List[str]:
        """
        List all SDK versions for domain.
        
        Args:
            language: Filter by language (optional)
            api_key: Optional API key for RBAC (overrides instance default)
        
        Returns:
            Sorted list of unique version strings
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        try:
            sdks = self.list_sdks(language=language, api_key=api_key)
        except Exception as e:
            self.logger.error(
                f"Failed to list versions for domain '{self.domain_name}': {e}"
            )
            raise
        
        versions = set()
        for sdk in sdks:
            version = sdk.get('version')
            if version:
                versions.add(version)
        
        return sorted(list(versions))

    def cleanup_old_versions(
        self,
        keep_latest: int = 3,
        language: str = None,
        api_key: str = None
    ) -> Dict[str, List[str]]:
        """
        Clean up old SDK versions, keeping only latest N.

        Args:
            keep_latest: Number of latest versions to keep per language (default: 3)
            language: Only cleanup this language (optional)
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Dict with 'deleted', 'kept', and 'failed' lists
        
        ✅ ADDED: Per-call api_key support for RBAC (v2.2)
        """
        # List all SDKs
        try:
            sdks = self.list_sdks(language=language, api_key=api_key)
        except Exception as e:
            self.logger.error(
                f"Failed to list SDKs for cleanup in domain '{self.domain_name}': {e}"
            )
            raise

        # Group by language
        by_language = {}
        for sdk in sdks:
            lang = sdk.get('language', 'unknown')
            if lang not in by_language:
                by_language[lang] = []
            by_language[lang].append(sdk)

        results = {
            'deleted': [],
            'kept': [],
            'failed': []
        }

        self.logger.info(
            f"Cleaning up old SDKs for domain '{self.domain_name}' (keep {keep_latest} latest)..."
        )

        # Process each language
        for lang, lang_sdks in by_language.items():
            # Sort by created_at descending (newest first)
            sorted_sdks = sorted(
                lang_sdks,
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )

            # Keep latest N
            to_keep = sorted_sdks[:keep_latest]
            to_delete = sorted_sdks[keep_latest:]

            # Keep
            for sdk in to_keep:
                results['kept'].append(sdk['sdk_uuid'])

            # Delete old
            for sdk in to_delete:
                try:
                    self.delete_sdk(sdk['sdk_uuid'], api_key=api_key)
                    results['deleted'].append(sdk['sdk_uuid'])
                except Exception as e:
                    self.logger.error(
                        f"Failed to delete {sdk['sdk_uuid']} for '{self.domain_name}': {e}"
                    )
                    results['failed'].append({
                        'sdk_uuid': sdk['sdk_uuid'],
                        'error': str(e)
                    })

        self.logger.info(
            f"Cleanup complete for '{self.domain_name}': "
            f"{len(results['deleted'])} deleted, {len(results['kept'])} kept, "
            f"{len(results['failed'])} failed"
        )

        return results

    def get_sdk_status(self, request_id: str, api_key: str = None) -> Dict[str, Any]:
        """
        Get SDK generation status.

        Args:
            request_id: SDK generation request ID
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Status information

        ✅ FIXED v2.3: Uses api_key kwarg pattern (matches UserManager)
        """
        endpoint = f'/sdks/status/{request_id}'

        # ✅ FIXED v2.3: Pass api_key as kwarg (not in headers)
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key

        try:
            response = self.client.get(endpoint, **kwargs)
            return response
        except Exception as e:
            self.logger.error(f"Failed to get SDK status: {e}")
            raise
