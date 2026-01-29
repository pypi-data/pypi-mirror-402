import os
import requests
import json
import logging
from typing import Dict, Any, Optional, Iterator, Tuple
import httpx
from httpx_sse import connect_sse

logger = logging.getLogger(__name__)


class ToothFairyAPI:
    def __init__(
        self,
        base_url: str,
        ai_url: str,
        ai_stream_url: str,
        api_key: str,
        workspaceid: str,
        verbose: bool = False,
    ):
        """
        Initialize the ToothFairyAPI client.

        Args:
            base_url (str): The base URL for the ToothFairy API.
            ai_url (str): The URL for AI-related endpoints.
            ai_stream_url (str): The URL for AI streaming endpoints.
            api_key (str): The API key for authentication.
            workspaceid (str): The workspaceid for authentication.
            verbose (bool): Enable verbose logging for debugging.
        """
        self.base_url = base_url
        self.ai_url = ai_url
        self.ai_stream_url = ai_stream_url
        self.workspaceid = workspaceid
        self.verbose = verbose
        self.headers = {"Content-Type": "application/json", "x-api-key": api_key}

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the ToothFairy API.

        Args:
            method (str): The HTTP method to use.
            endpoint (str): The API endpoint to call.
            data (dict, optional): The data to send with the request.

        Returns:
            dict: The JSON response from the API.

        Raises:
            requests.HTTPError: If the request fails.
        """
        if method in ["POST", "PUT"] and data:
            data = {"workspaceid": self.workspaceid, **data}
        elif method == "GET" and data:
            # For GET requests, add data as query parameters
            from urllib.parse import urlencode

            query_params = urlencode(data)
            endpoint = f"{endpoint}?{query_params}"

        url = f"{self.base_url}/{endpoint}"

        if self.verbose:
            from rich.console import Console

            console = Console()
            console.print(f"[dim]--- API Request Debug ---[/dim]", err=True)
            console.print(f"[dim]Method: {method}[/dim]", err=True)
            console.print(f"[dim]URL: {url}[/dim]", err=True)
            console.print(f"[dim]Headers: {self.headers}[/dim]", err=True)
            if data and method in ["POST", "PUT"]:
                console.print(f"[dim]Data: {data}[/dim]", err=True)
            console.print(f"[dim]----------------------[/dim]", err=True)

        try:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                json=data if method in ["POST", "PUT"] else None,
            )

            if self.verbose:
                from rich.console import Console

                console = Console()
                console.print(f"[dim]--- API Response Debug ---[/dim]", err=True)
                console.print(
                    f"[dim]Status: {response.status_code} {response.reason}[/dim]",
                    err=True,
                )
                console.print(
                    f"[dim]Response Headers: {dict(response.headers)}[/dim]", err=True
                )
                console.print(f"[dim]Response Data: {response.text}[/dim]", err=True)
                console.print(f"[dim]------------------------[/dim]", err=True)

            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            if self.verbose:
                from rich.console import Console

                console = Console()
                console.print(f"[red]--- API Error Debug ---[/red]", err=True)
                console.print(f"[red]HTTP Error: {http_err}[/red]", err=True)
                console.print(f"[red]Status: {response.status_code}[/red]", err=True)
                console.print(f"[red]Response: {response.text}[/red]", err=True)
                console.print(f"[red]---------------------[/red]", err=True)
            logger.error(f"HTTP error occurred: {http_err}")
            raise
        except Exception as err:
            if self.verbose:
                from rich.console import Console

                console = Console()
                console.print(f"[red]--- API Error Debug ---[/red]", err=True)
                console.print(f"[red]Error: {err}[/red]", err=True)
                console.print(f"[red]---------------------[/red]", err=True)
            logger.error(f"An error occurred: {err}")
            raise

    def create_chat(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new chat."""
        return self._make_request("POST", "chat/create", chat_data)

    def update_chat(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing chat."""
        return self._make_request("POST", "chat/update", chat_data)

    def get_chat(self, chat_id: str) -> Dict[str, Any]:
        """Get a chat by its ID."""
        return self._make_request(
            "GET", f"chat/get/{chat_id}?workspaceid={self.workspaceid}"
        )

    def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new message in a chat."""
        return self._make_request("POST", "chat_message/create", message_data)

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get a message by its ID."""
        return self._make_request("GET", f"chat_message/get/{message_id}")

    def get_all_chats(self) -> Dict[str, Any]:
        """Get all chats for the workspace."""
        return self._make_request("GET", f"chat/list?workspaceid={self.workspaceid}")

    def get_agent_response(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a response from an AI agent.

        Args:
            agent_data (dict): The data for the agent request.

        Returns:
            dict: The agent's response data.

        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.ai_url}/chatter"
        agent_data = {"workspaceid": self.workspaceid, **agent_data}
        try:
            response = requests.post(url, headers=self.headers, json=agent_data)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            raise
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            raise

    def send_message_to_agent(
        self,
        message: str,
        agent_id: str,
        phone_number: Optional[str] = None,
        customer_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        customer_info: Optional[Dict[str, Any]] = None,
        chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a message to an agent and get a response.

        This combines chat creation, message creation, and agent response.
        """
        if customer_info is None:
            customer_info = {}

        try:
            # Use defaults for optional parameters
            customer_id = customer_id or f"cli-user-{hash(message) % 10000}"
            phone_number = phone_number or "+1234567890"
            provider_id = provider_id or "default-sms-provider"

            if chat_id:
                # Use existing chat - let REST endpoint handle message creation
                message_data = {
                    "text": message,
                    "role": "user",
                    "userID": "CLI",
                }

                agent_data = {
                    "chatid": chat_id,
                    "messages": [message_data],
                    "agentid": agent_id,
                }

                agent_response = self.get_agent_response(agent_data)

                return {
                    "chat_id": agent_response.get("chatId", chat_id),
                    "message_id": agent_response.get("messageId", "auto-generated"),
                    "agent_response": agent_response,
                }
            else:
                # No chat_id provided - let API create chat automatically
                message_data = {
                    "text": message,
                    "role": "user",
                    "userID": customer_id,
                }

                # Send agent request without chatid - API will create chat and message automatically
                agent_data = {
                    # No chatid - let API create the chat
                    "messages": [message_data],
                    "agentid": agent_id,
                    # Include chat creation data since we're not pre-creating
                    "phoneNumber": phone_number,
                    "customerId": customer_id,
                    "providerId": provider_id,
                    "customerInfo": customer_info,
                }

                agent_response = self.get_agent_response(agent_data)

                return {
                    "chat_id": agent_response.get("chatId", "auto-generated"),
                    "message_id": agent_response.get("messageId", "auto-generated"),
                    "agent_response": agent_response,
                }
        except Exception as e:
            logger.error(f"Error in send_message_to_agent: {e}")
            raise

    def search_documents(
        self, text: str, top_k: int = 10, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for documents in the knowledge hub.

        Args:
            text (str): Search query text
            top_k (int): Number of documents to retrieve (1-50)
            metadata (dict, optional): Metadata filters for advanced search
                - status: Document status filter ("published" or "suspended")
                - documentId: Specific document ID to search within
                - topic: Array of topic IDs to filter by

        Returns:
            dict: Search results with relevant documents
        """
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50")

        search_data = {"text": text, "topK": top_k}

        if metadata:
            search_data["metadata"] = metadata

        url = f"{self.ai_url}/searcher"
        search_data = {"workspaceid": self.workspaceid, **search_data}

        try:
            response = requests.post(url, headers=self.headers, json=search_data)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred during search: {http_err}")
            raise
        except Exception as err:
            logger.error(f"An error occurred during search: {err}")
            raise

    def send_message_to_agent_stream(
        self,
        message: str,
        agent_id: str,
        phone_number: Optional[str] = None,
        customer_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        customer_info: Optional[Dict[str, Any]] = None,
        chat_id: Optional[str] = None,
        raw_stream: bool = False,
    ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """
        Send a message to an agent and get a streaming response.

        This method handles the complete workflow with Server-Sent Events (SSE):
        1. Creates a chat
        2. Creates a message
        3. Streams the agent response in real-time

        Args:
            message (str): The message to send to the agent
            agent_id (str): The ID of the agent to send the message to
            phone_number (str, optional): Phone number for SMS channel
            customer_id (str, optional): Customer identifier
            provider_id (str, optional): SMS provider ID
            customer_info (dict, optional): Additional customer information
            chat_id (str, optional): Existing chat ID to continue conversation (default: None, creates new chat)
            raw_stream (bool, optional): Enable raw streaming mode for chunk-by-chunk output (default: False)

        Yields:
            Tuple[str, Dict[str, Any]]: A tuple containing:
                - event_type (str): Type of event ('status', 'progress', 'data', 'complete', 'error')
                - event_data (dict): The parsed event data

        Event Types Explained:
            - 'status': Connection status updates ('connected', 'complete')
            - 'progress': Agent processing status updates:
                * 'init': Agent initialization started
                * 'initial_setup_completed': Basic setup finished
                * 'tools_processing_completed': Tools processing finished
                * 'replying': Agent is generating response (text streaming starts)
                * 'updating_memory': Agent is updating conversation memory
                * 'memory_updated': Memory update completed
            - 'data': Actual response text chunks (progressive text building)
            - 'complete': Final response with all metadata
            - 'error': Error occurred during streaming
        """
        if customer_info is None:
            customer_info = {}

        try:
            # Use defaults for optional parameters
            customer_id = customer_id or f"cli-user-{hash(message) % 10000}"
            phone_number = phone_number or "+1234567890"
            provider_id = provider_id or "default-sms-provider"

            if chat_id:
                # Use existing chat - let SSE endpoint handle message creation
                message_data = {
                    "text": message,
                    "role": "user",
                    "userID": "CLI",
                }

                # Prepare agent data for streaming with existing chat
                agent_data = {
                    "workspaceid": self.workspaceid,
                    "chatid": chat_id,
                    "messages": [message_data],
                    "agentid": agent_id,
                    "raw_stream": raw_stream,
                }
            else:
                # No chat_id provided - let streaming API create chat automatically
                message_data = {
                    "text": message,
                    "role": "user",
                    "userID": customer_id,
                }

                # Send agent request without chatid - API will create chat and message automatically
                agent_data = {
                    "workspaceid": self.workspaceid,
                    # No chatid - let API create the chat
                    "messages": [message_data],
                    "agentid": agent_id,
                    # Include chat creation data since we're not pre-creating
                    "phoneNumber": phone_number,
                    "customerId": customer_id,
                    "providerId": provider_id,
                    "customerInfo": customer_info,
                    "raw_stream": raw_stream,
                }

            # Stream the agent response using the dedicated streaming URL
            stream_url = (
                f"{self.ai_stream_url}/agent"  # Using streaming URL for /agent endpoint
            )

            with httpx.Client() as client:
                with connect_sse(
                    client,
                    "POST",
                    stream_url,
                    headers=self.headers,
                    json=agent_data,
                    timeout=300.0,  # 5 minute timeout
                ) as event_source:

                    for sse_event in event_source.iter_sse():
                        try:
                            # Parse the SSE data
                            event_data = json.loads(sse_event.data)

                            # Determine event type based on the data structure
                            # Handle raw_stream token events (streaming text chunks)
                            if (
                                event_data.get("type") == "token"
                                and "chunk" in event_data
                            ):
                                # Token streaming event - emit as 'data' with text field for compatibility
                                yield ("data", {**event_data, "text": event_data["chunk"]})

                            elif "status" in event_data:
                                if event_data["status"] == "connected":
                                    yield ("status", event_data)
                                elif event_data["status"] == "complete":
                                    yield ("status", event_data)
                                elif event_data["status"] == "inProgress":
                                    # Parse metadata to understand what's happening
                                    metadata = {}
                                    if "metadata" in event_data:
                                        # metadata can be an object or a JSON string
                                        if isinstance(event_data["metadata"], dict):
                                            metadata = event_data["metadata"]
                                        else:
                                            try:
                                                metadata = json.loads(
                                                    event_data["metadata"]
                                                )
                                            except (json.JSONDecodeError, TypeError):
                                                metadata = {
                                                    "raw_metadata": event_data["metadata"]
                                                }

                                    # Determine progress type
                                    if "agent_processing_status" in metadata:
                                        processing_status = metadata[
                                            "agent_processing_status"
                                        ]
                                        yield (
                                            "progress",
                                            {
                                                **event_data,
                                                "processing_status": processing_status,
                                                "metadata_parsed": metadata,
                                            },
                                        )
                                    else:
                                        yield (
                                            "progress",
                                            {**event_data, "metadata_parsed": metadata},
                                        )

                                elif event_data["status"] == "fulfilled":
                                    # Final response with complete data
                                    yield ("complete", event_data)

                            elif (
                                "text" in event_data
                                and event_data.get("type") == "message"
                            ):
                                # This is streaming text data (non-raw_stream mode)
                                yield ("data", event_data)

                            elif (
                                event_data.get("type") == "message"
                                and event_data.get("chat_created") is True
                            ):
                                # Chat creation event from raw_stream mode
                                yield ("chat_created", {**event_data, "chatId": event_data.get("chatid")})

                            elif (
                                event_data.get("type") == "message"
                                and "images" in event_data
                            ):
                                # Additional message metadata (images, files, etc.)
                                yield ("metadata", event_data)

                            elif (
                                event_data.get("type") == "message"
                                and "callbackMetadata" in event_data
                            ):
                                # Callback metadata with function details and execution plan
                                yield ("callback", event_data)

                            else:
                                # Generic event data
                                yield ("unknown", event_data)

                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Failed to parse SSE data: {sse_event.data}, error: {e}"
                            )
                            yield (
                                "error",
                                {
                                    "error": "json_decode_error",
                                    "raw_data": sse_event.data,
                                    "message": str(e),
                                },
                            )
                        except Exception as e:
                            logger.error(f"Error processing SSE event: {e}")
                            yield (
                                "error",
                                {
                                    "error": "processing_error",
                                    "raw_data": sse_event.data,
                                    "message": str(e),
                                },
                            )

        except Exception as e:
            logger.error(f"Error in send_message_to_agent_stream: {e}")
            yield ("error", {"error": "stream_error", "message": str(e)})

    def get_upload_url(
        self,
        filename: str,
        import_type: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a pre-signed URL for uploading a file to the ToothFairy system.

        Args:
            filename: The name of the file to upload (should include workspaceid/filename)
            import_type: The type of import (optional, will be auto-detected from file extension)
            content_type: The MIME type of the file (optional, will be auto-detected)

        Returns:
            Upload URL and file metadata
        """
        params = {"filename": filename}

        if import_type:
            params["importType"] = import_type
        if content_type:
            params["contentType"] = content_type

        url = f"{self.base_url}/documents/requestPreSignedURL"

        if self.verbose:
            from rich.console import Console

            console = Console()
            console.print(f"[dim]--- Upload URL Request Debug ---[/dim]", err=True)
            console.print(f"[dim]URL: {url}[/dim]", err=True)
            console.print(f"[dim]Params: {params}[/dim]", err=True)
            console.print(f"[dim]----------------------------[/dim]", err=True)

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            logger.error(f"Upload URL request failed: {http_err}")
            raise
        except Exception as err:
            logger.error(f"An error occurred requesting upload URL: {err}")
            raise

    def upload_file(
        self,
        file_path: str,
        workspace_id: str,
        import_type: Optional[str] = None,
        content_type: Optional[str] = None,
        on_progress: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to ToothFairy using a pre-signed URL (matching frontend behavior).

        Args:
            file_path: Path to the local file to upload
            workspace_id: Workspace ID to upload to
            import_type: The type of import (optional, auto-detected if not provided)
            content_type: The MIME type of the file (optional, auto-detected if not provided)
            on_progress: Callback for upload progress (optional)

        Returns:
            Upload result
        """
        import os
        import time
        from pathlib import Path

        # Validate file exists and size
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        # Check 15MB limit
        if file_size_mb > 15:
            raise ValueError(f"File size ({file_size_mb:.2f}MB) exceeds 15MB limit")

        # Process filename following frontend behavior
        original_filename = Path(file_path).name
        sanitized_filename = self._sanitize_filename(original_filename)

        # Auto-detect import type if not provided
        final_import_type = import_type or self._get_import_type(file_path)

        # Auto-detect content type if not provided
        final_content_type = content_type or self._get_content_type(file_path)

        # Create full filename with workspace ID (preserve full path)
        full_filename = f"{workspace_id}/{file_path}"

        # Get upload URL
        upload_data = self.get_upload_url(
            full_filename, final_import_type, final_content_type
        )

        if self.verbose:
            from rich.console import Console

            console = Console()
            console.print(f"[dim]--- File Upload URL response ---[/dim]", err=True)
            console.print(f"[dim]Raw response: {upload_data}[/dim]", err=True)

        # Parse the nested response structure
        if upload_data.get("body") and isinstance(upload_data["body"], str):
            try:
                parsed_upload_data = json.loads(upload_data["body"])
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse upload response body: {e}")
        else:
            parsed_upload_data = upload_data

        if not parsed_upload_data.get("uploadURL"):
            raise ValueError("Failed to get upload URL from server")

        # Upload file to S3
        upload_url = parsed_upload_data["uploadURL"]

        if self.verbose:
            from rich.console import Console

            console = Console()
            console.print(f"[dim]--- File Upload Debug ---[/dim]", err=True)
            console.print(f"[dim]File: {file_path}[/dim]", err=True)
            console.print(
                f"[dim]Original filename: {original_filename}[/dim]", err=True
            )
            console.print(
                f"[dim]Sanitized filename: {sanitized_filename}[/dim]", err=True
            )
            console.print(f"[dim]Full filename: {full_filename}[/dim]", err=True)
            console.print(f"[dim]Import type: {final_import_type}[/dim]", err=True)
            console.print(f"[dim]Content type: {final_content_type}[/dim]", err=True)
            console.print(f"[dim]Size: {file_size_mb:.2f}MB[/dim]", err=True)
            console.print(f"[dim]Upload URL: {upload_url}[/dim]", err=True)
            console.print(f"[dim]------------------------[/dim]", err=True)

        try:
            with open(file_path, "rb") as f:
                # For progress tracking, we'll use a custom file-like object if callback provided
                if on_progress:
                    file_data = ProgressFile(f, file_size, on_progress)
                else:
                    file_data = f.read()

                response = requests.put(
                    upload_url,
                    data=file_data if not on_progress else file_data,
                    headers={"Content-Type": final_content_type},
                )
                response.raise_for_status()

            # Extract filename for download (remove S3 prefix if present)
            download_filename = full_filename
            if parsed_upload_data.get("filePath"):
                # Remove S3 bucket prefix from filePath to get clean filename for download
                import re

                download_filename = re.sub(
                    r"^s3://[^/]+/", "", parsed_upload_data["filePath"]
                )

            return {
                "success": True,
                "original_filename": original_filename,
                "sanitized_filename": sanitized_filename,
                "filename": download_filename,  # Clean filename for download
                "import_type": final_import_type,
                "content_type": final_content_type,
                "size": file_size,
                "size_mb": file_size_mb,
            }

        except requests.HTTPError as e:
            raise ValueError(
                f"Upload failed: HTTP {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            raise ValueError(f"Upload failed: {e}")

    def get_download_url(
        self, filename: str, workspace_id: str, context: str = "pdf"
    ) -> Dict[str, Any]:
        """
        Get a download URL for a file from ToothFairy (matching frontend behavior).

        Args:
            filename: Name of the file to download (without S3 prefix)
            workspace_id: Workspace ID
            context: Context for the download (default: "pdf")

        Returns:
            Download URL and metadata
        """
        params = {
            "filename": filename,
            "context": context,
            "workspaceid": workspace_id,
        }

        url = f"{self.base_url}/documents/requestDownloadURLIncognito"

        if self.verbose:
            from rich.console import Console

            console = Console()
            console.print(f"[dim]--- Download URL Request Debug ---[/dim]", err=True)
            console.print(f"[dim]URL: {url}[/dim]", err=True)
            console.print(f"[dim]Params: {params}[/dim]", err=True)
            console.print(f"[dim]-----------------------------[/dim]", err=True)

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            logger.error(f"Download URL request failed: {http_err}")
            raise
        except Exception as err:
            logger.error(f"An error occurred requesting download URL: {err}")
            raise

    def download_file(
        self,
        filename: str,
        workspace_id: str,
        output_path: str,
        context: str = "pdf",
        on_progress: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Download a file from ToothFairy to a local path (matching frontend behavior).

        Args:
            filename: Name of the file to download (without S3 prefix)
            workspace_id: Workspace ID
            output_path: Local path to save the file
            context: Context for the download (default: "pdf")
            on_progress: Callback for download progress (optional)

        Returns:
            Download result
        """
        import os
        from pathlib import Path

        # Get download URL
        download_data = self.get_download_url(filename, workspace_id, context)

        if not download_data.get("url"):
            raise ValueError("Failed to get download URL from server")

        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        if self.verbose:
            from rich.console import Console

            console = Console()
            console.print(f"[dim]--- File Download Debug ---[/dim]", err=True)
            console.print(f"[dim]Download URL: {download_data['url']}[/dim]", err=True)
            console.print(f"[dim]Output Path: {output_path}[/dim]", err=True)
            console.print(f"[dim]---------------------------[/dim]", err=True)

        try:
            with requests.get(download_data["url"], stream=True) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            if on_progress and total_size > 0:
                                percent = int((downloaded / total_size) * 100)
                                on_progress(percent, downloaded, total_size)

            # Get file stats
            file_size = os.path.getsize(output_path)

            return {
                "success": True,
                "output_path": output_path,
                "size": file_size,
                "size_mb": f"{(file_size / (1024 * 1024)):.2f}",
            }

        except requests.HTTPError as e:
            raise ValueError(
                f"Download failed: HTTP {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            raise ValueError(f"Download failed: {e}")

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename following frontend behavior.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename with timestamp
        """
        import re
        import time

        # Remove non-alphanumeric characters except dots
        sanitized = re.sub(r"[^a-zA-Z0-9.]", "", filename)

        # Check length limit
        if len(sanitized) > 100:
            raise ValueError("File name cannot be more than 100 characters.")

        # Add timestamp prefix like frontend
        timestamped_filename = str(int(time.time() * 1000)) + sanitized

        return timestamped_filename

    def _get_import_type(self, file_path: str) -> str:
        """
        Determine import type based on file extension (matching frontend logic).

        Args:
            file_path: Path to the file

        Returns:
            Import type
        """
        from pathlib import Path

        ext = Path(file_path).suffix.lower().lstrip(".")

        # Image extensions
        image_exts = ["png", "jpg", "jpeg", "gif", "bmp", "svg"]
        # Video extensions
        video_exts = ["mp4", "avi", "mov", "wmv", "flv", "webm"]
        # Audio extensions
        audio_exts = ["wav", "mp3", "aac", "ogg", "flac"]

        if ext in image_exts:
            return "imported-image"
        elif ext in video_exts:
            return "imported_video_files"
        elif ext in audio_exts:
            return "imported_audio_files"
        else:
            return "imported_doc_files"

    def _get_content_type(self, file_path: str) -> str:
        """
        Helper method to determine content type from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Content type
        """
        from pathlib import Path

        ext = Path(file_path).suffix.lower().lstrip(".")

        content_types = {
            "txt": "text/plain",
            "md": "text/markdown",
            "html": "text/html",
            "pdf": "application/pdf",
            "json": "application/json",
            "jsonl": "application/json",
            "wav": "audio/wav",
            "mp4": "video/mp4",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "csv": "text/csv",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "ppt": "application/vnd.ms-powerpoint",
            "java": "text/plain",
            "py": "text/plain",
            "js": "text/plain",
            "ts": "text/plain",
            "tsx": "text/plain",
            "jsx": "text/plain",
            "yaml": "text/plain",
            "yml": "text/plain",
            "sql": "text/plain",
            "sh": "text/plain",
            "php": "text/plain",
            "csharp": "text/plain",
            "rb": "text/plain",
        }

        return content_types.get(ext, "application/octet-stream")


class ProgressFile:
    """File-like object that tracks upload progress."""

    def __init__(self, file_obj, total_size: int, callback: callable):
        self.file_obj = file_obj
        self.total_size = total_size
        self.callback = callback
        self.uploaded = 0

    def read(self, size: int = -1):
        data = self.file_obj.read(size)
        if data:
            self.uploaded += len(data)
            if self.callback:
                percent = int((self.uploaded / self.total_size) * 100)
                self.callback(percent, self.uploaded, self.total_size)
        return data

    def __len__(self):
        return self.total_size

    # Agent Management Methods

    def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent."""
        return self._make_request("POST", "agent/create", agent_data)

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get a specific agent by ID."""
        return self._make_request("GET", f"agent/get/{agent_id}")

    def list_agents(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """List all agents in the workspace."""
        params = {"workspaceid": self.workspaceid}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "agent/list", params)

    def update_agent(self, agent_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing agent."""
        update_data = {"id": agent_id, **fields}
        return self._make_request("POST", f"agent/update/{agent_id}", update_data)

    def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """Delete an agent."""
        return self._make_request("DELETE", f"agent/delete/{agent_id}")

    # Authorization Management Methods

    def create_authorization(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new authorization."""
        return self._make_request("POST", "authorisation/create", auth_data)

    def get_authorization(self, auth_id: str) -> Dict[str, Any]:
        """Get a specific authorization by ID."""
        return self._make_request("GET", f"authorisation/get/{auth_id}")

    def list_authorizations(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """List all authorizations in the workspace."""
        params = {"workspaceid": self.workspaceid}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "authorisation/list", params)

    def update_authorization(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing authorization."""
        return self._make_request("POST", "authorisation/update", fields)

    def delete_authorization(self, auth_id: str) -> Dict[str, Any]:
        """Delete an authorization."""
        return self._make_request("DELETE", f"authorisation/delete/{auth_id}")

    # Benchmark Management Methods

    def create_benchmark(self, benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new benchmark."""
        return self._make_request("POST", "benchmark/create", benchmark_data)

    def get_benchmark(self, benchmark_id: str) -> Dict[str, Any]:
        """Get a specific benchmark by ID."""
        return self._make_request("GET", f"benchmark/get/{benchmark_id}")

    def list_benchmarks(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """List all benchmarks in the workspace."""
        params = {"workspaceid": self.workspaceid}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "benchmark/list", params)

    def update_benchmark(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing benchmark."""
        return self._make_request("POST", "benchmark/update", fields)

    def delete_benchmark(self, benchmark_id: str) -> Dict[str, Any]:
        """Delete a benchmark."""
        return self._make_request("DELETE", f"benchmark/delete/{benchmark_id}")

    # Billing Methods

    def get_month_costs(self, month: int, year: int) -> Dict[str, Any]:
        """Get monthly usage and cost information."""
        params = {
            "workspaceId": self.workspaceid,
            "month": month,
            "year": year,
        }
        return self._make_request("GET", "billing/monthCosts", params)

    # Channel Management Methods

    def create_channel(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new communication channel."""
        return self._make_request("POST", "channel/create", channel_data)

    def get_channel(self, channel_id: str) -> Dict[str, Any]:
        """Get a specific channel by ID."""
        return self._make_request("GET", f"channel/get/{channel_id}")

    def list_channels(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """List all channels in the workspace."""
        params = {"workspaceid": self.workspaceid}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "channel/list", params)

    def update_channel(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing channel."""
        return self._make_request("POST", "channel/update", fields)

    def delete_channel(self, channel_id: str) -> Dict[str, Any]:
        """Delete a channel."""
        return self._make_request("DELETE", f"channel/delete/{channel_id}")

    # Connection Management Methods

    def get_connection(self, connection_id: str) -> Dict[str, Any]:
        """Get a specific connection by ID."""
        return self._make_request("GET", f"connection/get/{connection_id}")

    def list_connections(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """List all connections in the workspace."""
        params = {"workspaceid": self.workspaceid}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "connection/list", params)

    def delete_connection(self, connection_id: str) -> Dict[str, Any]:
        """Delete a connection."""
        return self._make_request("DELETE", f"connection/delete/{connection_id}")

    # Dictionary Management Methods

    def get_dictionary(self, dictionary_id: str) -> Dict[str, Any]:
        """Get a specific dictionary entry by ID."""
        return self._make_request("GET", f"dictionary/get/{dictionary_id}")

    def list_dictionaries(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """List all dictionary entries in the workspace."""
        params = {"workspaceid": self.workspaceid}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "dictionary/list", params)

    # Embedding Management Methods

    def get_embedding(self, embedding_id: str) -> Dict[str, Any]:
        """Get a specific embedding by ID."""
        return self._make_request("GET", f"embedding/get/{embedding_id}")

    # Settings Management Methods

    def get_charting_settings(self, settings_id: str) -> Dict[str, Any]:
        """Get charting settings for the workspace."""
        return self._make_request("GET", f"charting_settings/get/{settings_id}")

    def update_charting_settings(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update charting settings for the workspace."""
        return self._make_request("POST", "charting_settings/update", fields)

    def get_embeddings_settings(self, settings_id: str) -> Dict[str, Any]:
        """Get embeddings settings for the workspace."""
        return self._make_request("GET", f"embeddings_settings/get/{settings_id}")

    def update_embeddings_settings(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update embeddings settings for the workspace."""
        return self._make_request("POST", "embeddings_settings/update", fields)

    # Stream Management Methods

    def get_stream(self, stream_id: str) -> Dict[str, Any]:
        """Get a specific stream by ID."""
        return self._make_request("GET", f"stream/get/{stream_id}")

    def list_streams(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """List all streams in the workspace."""
        params = {"workspaceid": self.workspaceid}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "stream/list", params)
