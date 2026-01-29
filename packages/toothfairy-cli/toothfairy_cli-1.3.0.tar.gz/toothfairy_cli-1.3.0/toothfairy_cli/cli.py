#!/usr/bin/env python3

import click
import json
import logging
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text

from .api import ToothFairyAPI
from .config import load_config, save_config, ToothFairyConfig

console = Console()


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def validate_configuration(config: ToothFairyConfig) -> None:
    """Validate configuration and provide helpful error messages."""
    missing_fields = []

    if not config.api_key:
        missing_fields.append("API Key")
    if not config.workspace_id:
        missing_fields.append("Workspace ID")

    if missing_fields:
        missing_str = " and ".join(missing_fields)
        console.print(f"[red]Error: Missing required configuration: {missing_str}[/red]")
        console.print()
        console.print("[yellow]To fix this, run the configure command:[/yellow]")
        console.print(
            "[dim]tf configure --api-key YOUR_API_KEY --workspace-id YOUR_WORKSPACE_ID[/dim]"
        )
        console.print()
        console.print("[yellow]Or set environment variables:[/yellow]")
        if not config.api_key:
            console.print("[dim]export TF_API_KEY='your-api-key'[/dim]")
        if not config.workspace_id:
            console.print("[dim]export TF_WORKSPACE_ID='your-workspace-id'[/dim]")
        console.print()
        console.print("[yellow]Or create a config file at ~/.toothfairy/config.yml:[/yellow]")
        console.print("[dim]api_key: your-api-key[/dim]")
        console.print("[dim]workspace_id: your-workspace-id[/dim]")
        raise click.ClickException(f"Configuration incomplete: missing {missing_str}")


@click.group()
@click.option("--config", "-c", help="Path to configuration file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """ToothFairyAI CLI - Interact with ToothFairyAI agents via command line."""
    setup_logging(verbose)

    try:
        tf_config = load_config(config)
        ctx.ensure_object(dict)
        ctx.obj["config"] = tf_config
        ctx.obj["api"] = ToothFairyAPI(
            base_url=tf_config.base_url,
            ai_url=tf_config.ai_url,
            ai_stream_url=tf_config.ai_stream_url,
            api_key=tf_config.api_key,
            workspaceid=tf_config.workspace_id,
            verbose=verbose,
        )
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option("--base-url", default="https://api.toothfairyai.com", help="ToothFairy API base URL")
@click.option("--ai-url", default="https://ai.toothfairyai.com", help="ToothFairyAI URL")
@click.option(
    "--ai-stream-url", default="https://ais.toothfairyai.com", help="ToothFairyAI Streaming URL"
)
@click.option("--api-key", required=True, help="API key")
@click.option("--workspace-id", required=True, help="Workspace ID")
@click.option("--config-path", help="Path to save config file")
def configure(
    base_url: str,
    ai_url: str,
    ai_stream_url: str,
    api_key: str,
    workspace_id: str,
    config_path: Optional[str],
):
    """Configure ToothFairy CLI credentials and settings."""
    config = ToothFairyConfig(
        base_url=base_url,
        ai_url=ai_url,
        ai_stream_url=ai_stream_url,
        api_key=api_key,
        workspace_id=workspace_id,
    )

    try:
        save_config(config, config_path)
        console.print("[green]Configuration saved successfully![/green]")
        if not config_path:
            console.print(f"Config saved to: {config.get_config_path()}")
    except Exception as e:
        console.print(f"[red]Error saving configuration: {e}[/red]")


@cli.command()
@click.argument("message")
@click.option("--agent-id", required=True, help="Agent ID to send message to")
@click.option("--chat-id", help="Existing chat ID to continue conversation")
@click.option("--phone-number", help="Phone number for SMS channel")
@click.option("--customer-id", help="Customer ID")
@click.option("--provider-id", help="SMS provider ID")
@click.option("--customer-info", help="Customer info as JSON string")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed response information")
@click.pass_context
def send(
    ctx,
    message: str,
    agent_id: str,
    chat_id: Optional[str],
    phone_number: Optional[str],
    customer_id: Optional[str],
    provider_id: Optional[str],
    customer_info: Optional[str],
    output: str,
    verbose: bool,
):
    """Send a message to a ToothFairyAI agent."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    # Parse customer info if provided
    parsed_customer_info = {}
    if customer_info:
        try:
            parsed_customer_info = json.loads(customer_info)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON in customer-info[/red]")
            ctx.exit(1)

    try:
        with console.status("Sending message to agent..."):
            response = api.send_message_to_agent(
                message=message,
                agent_id=agent_id,
                phone_number=phone_number,
                customer_id=customer_id,
                provider_id=provider_id,
                customer_info=parsed_customer_info,
                chat_id=chat_id,
            )

        if output == "json":
            console.print(json.dumps(response, indent=2))
        else:
            agent_resp = response["agent_response"]

            if verbose:
                # Verbose mode: show all details
                console.print(Panel(f"[bold green]Message sent successfully![/bold green]"))

                table = Table(title="Response Details")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")

                table.add_row("Chat ID", response["chat_id"])
                table.add_row("Message ID", response["message_id"])

                console.print(table)

                # Show full agent response
                console.print(
                    Panel(
                        Syntax(json.dumps(agent_resp, indent=2), "json"),
                        title="[bold blue]Agent Response (Full)[/bold blue]",
                        border_style="blue",
                    )
                )
            else:
                # Default mode: show only the clean agent text
                if "contents" in agent_resp and "content" in agent_resp["contents"]:
                    # Extract clean content from the response
                    clean_content = agent_resp["contents"]["content"].strip()
                    console.print(clean_content)
                elif "text" in agent_resp:
                    console.print(agent_resp["text"])
                else:
                    # Fallback to JSON if no recognizable text format
                    console.print(
                        "[yellow]No text response found. Use --verbose for full details.[/yellow]"
                    )

    except Exception as e:
        console.print(f"[red]Error sending message: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("message")
@click.option("--agent-id", required=True, help="Agent ID to send message to")
@click.option("--chat-id", help="Existing chat ID to continue conversation")
@click.option("--phone-number", help="Phone number for SMS channel")
@click.option("--customer-id", help="Customer ID")
@click.option("--provider-id", help="SMS provider ID")
@click.option("--customer-info", help="Customer info as JSON string")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed streaming information")
@click.option("--show-progress", is_flag=True, help="Show agent processing status updates")
@click.pass_context
def send_stream(
    ctx,
    message: str,
    agent_id: str,
    chat_id: Optional[str],
    phone_number: Optional[str],
    customer_id: Optional[str],
    provider_id: Optional[str],
    customer_info: Optional[str],
    output: str,
    verbose: bool,
    show_progress: bool,
):
    """Send a message to a ToothFairyAI agent with real-time streaming response.

    This command shows the agent's response as it's being generated in real-time,
    providing live updates on the agent's processing status and streaming text output.

    STREAMING BEHAVIOR EXPLAINED:

    🔄 STATUS UPDATES: The agent goes through several processing phases:

    • 'connected': Connection established with streaming server
    • 'init': Agent initialization started
    • 'initial_setup_completed': Basic setup and context loading finished
    • 'tools_processing_completed': Any required tools/functions processed
    • 'replying': Agent begins generating the actual response (text starts streaming)
    • 'updating_memory': Agent updates conversation memory
    • 'memory_updated': Memory update completed
    • 'complete': Stream finished successfully

    📝 TEXT STREAMING: Once the agent reaches 'replying' status, you'll see the response
    text being built progressively, word by word, just like ChatGPT or similar AI assistants.

    💡 TIP: Use --show-progress to see detailed status updates, or --verbose for full debug info.
    """
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    # Parse customer info if provided
    parsed_customer_info = {}
    if customer_info:
        try:
            parsed_customer_info = json.loads(customer_info)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON in customer-info[/red]")
            ctx.exit(1)

    # Initialize variables for streaming
    current_text = ""
    final_response = None
    processing_status = None
    connection_established = False
    has_started_response = False
    has_completed_response = False

    def map_state_with_label(state: str) -> str:
        """Map agent processing state to user-friendly label with emojis."""
        status_map = {
            "data_processing_completed": "📊 **Retrieving data**",
            "tools_processing_completed": "🛠️ **Choosing tools**",
            "replying": "🧚 **Responding**",
            "main_generation_completed": "✨ **Generation completed**",
            "memory_updated": "💾 Memory updated",
            "updating_memory": "💾 Updating memory...",
            "init": "🚀 Initializing...",
            "initial_setup_completed": "✅ Setup completed",
            "image_analysis_in_progress": "🖼️ Analyzing image...",
            "video_analysis_in_progress": "🎥 Analyzing video...",
            "audio_analysis_in_progress": "🎵 Analyzing audio...",
            "image_generation_in_progress": "🎨 Generating image...",
            "video_generation_in_progress": "🎬 Generating video...",
            "3D_model_generation_in_progress": "🏗️ Creating 3D model...",
            "code_generation_in_progress": "💻 Generating code...",
            "code_execution_in_progress": "⚡ Executing code...",
            "internet_search_in_progress": "🔍 Searching internet...",
            "planning_in_progress": "🗺️ Planning response...",
            "handed_off_to_human": "👤 Handed off to human",
            "completed": "🎉 Completed",
        }
        return status_map.get(state, f"📊 {state}")

    try:
        console.print(f"[cyan]Streaming message to agent {agent_id}...[/cyan]")
        console.print(f"[dim]Message: {message}[/dim]")
        console.print()

        if output == "json":
            # JSON mode: collect all events and output at the end
            all_events = []

            for event_type, event_data in api.send_message_to_agent_stream(
                message=message,
                agent_id=agent_id,
                phone_number=phone_number,
                customer_id=customer_id,
                provider_id=provider_id,
                customer_info=parsed_customer_info,
                chat_id=chat_id,
                raw_stream=True,  # Enable chunk-by-chunk streaming
            ):
                all_events.append({"event_type": event_type, "event_data": event_data})

                if event_type == "error":
                    console.print(
                        f"[red]Streaming error: {event_data.get('message', 'Unknown error')}[/red]"
                    )
                    break

            console.print(json.dumps(all_events, indent=2))

        else:
            # Text mode: show live streaming
            response_panel = None

            with Live(console=console, refresh_per_second=4) as live:

                for event_type, event_data in api.send_message_to_agent_stream(
                    message=message,
                    agent_id=agent_id,
                    phone_number=phone_number,
                    customer_id=customer_id,
                    provider_id=provider_id,
                    customer_info=parsed_customer_info,
                    chat_id=chat_id,
                    raw_stream=True,  # Enable chunk-by-chunk streaming
                ):

                    if verbose:
                        # Verbose mode: show all event details
                        console.print(
                            f"[dim]Event: {event_type} | Data: {json.dumps(event_data, indent=2)}[/dim]"
                        )

                    # Handle connection status events
                    if event_data.get("status") == "connected":
                        connection_established = True
                        if show_progress:
                            live.update(
                                Panel(
                                    "🔗 [green]Connected to streaming server[/green]",
                                    title="Status",
                                )
                            )
                        continue

                    if event_data.get("status") == "complete":
                        if show_progress:
                            live.update(
                                Panel(
                                    "🎉 [green]Stream completed successfully![/green]",
                                    title="Status",
                                )
                            )
                        break

                    # Handle streaming data events (tokens from raw_stream mode)
                    if event_type == "data" and event_data.get("text"):
                        # Print chunk directly (raw_stream sends individual chunks)
                        if not has_started_response:
                            live.stop()
                            console.print("[green]🧚 Responding[/green]")
                            has_started_response = True
                            live.start()

                        live.stop()
                        console.print(event_data["text"], end="")
                        current_text += event_data["text"]
                        live.start()

                    # Handle progress events (from raw_stream mode)
                    if event_type == "progress":
                        status = event_data.get("processing_status") or (
                            event_data.get("metadata_parsed", {}).get("agent_processing_status")
                        )
                        if status and status != processing_status:
                            processing_status = status
                            if show_progress:
                                status_msg = map_state_with_label(processing_status)
                                live.update(
                                    Panel(f"[yellow]{status_msg}[/yellow]", title="Agent Status")
                                )

                    # Handle chat_created events
                    if event_type == "chat_created" and event_data.get("chatId"):
                        if verbose:
                            live.stop()
                            console.print(f"[dim]📝 Chat created: {event_data['chatId']}[/dim]")
                            live.start()

                    # Handle complete events
                    if event_type == "complete":
                        final_response = event_data

                    # Handle message events (legacy format / additional metadata)
                    if event_data.get("type") == "message":
                        metadata = {}
                        agent_status = None

                        # Parse metadata if available
                        if event_data.get("metadata"):
                            if isinstance(event_data["metadata"], dict):
                                metadata = event_data["metadata"]
                            else:
                                try:
                                    metadata = json.loads(event_data["metadata"])
                                except json.JSONDecodeError:
                                    pass
                            agent_status = metadata.get("agent_processing_status")

                        # Handle status changes
                        if agent_status and agent_status != processing_status:
                            processing_status = agent_status
                            if show_progress:
                                status_msg = map_state_with_label(processing_status)
                                live.update(
                                    Panel(f"[yellow]{status_msg}[/yellow]", title="Agent Status")
                                )

                        # Handle fulfilled status (final response) - only show once
                        if event_data.get("status") == "fulfilled" and not has_completed_response:
                            final_response = event_data
                            has_completed_response = True
                            live.stop()
                            console.print("\n[blue]🪄 Response complete[/blue]")
                            live.start()

                        # Handle additional metadata events (images, files, callback metadata)
                        if (
                            event_data.get("images") is not None
                            or event_data.get("files") is not None
                        ):
                            if verbose:
                                console.print("[dim]📎 Attachments processed[/dim]")

                        if event_data.get("callbackMetadata"):
                            if verbose:
                                console.print("[dim]⚙️ Function execution metadata received[/dim]")

                    # Handle errors
                    if event_type == "error":
                        error_msg = event_data.get("message", "Unknown streaming error")
                        live.update(Panel(f"[red]❌ Error: {error_msg}[/red]", title="Error"))
                        console.print(f"[red]Streaming error: {error_msg}[/red]")
                        ctx.exit(1)

            # After streaming is complete
            console.print()

            if verbose and final_response:
                # Show final response metadata in verbose mode
                console.print(Panel("📊 [bold cyan]Final Response Metadata[/bold cyan]"))
                metadata_table = Table()
                metadata_table.add_column("Field", style="cyan")
                metadata_table.add_column("Value", style="white")

                if "metadata_parsed" in final_response:
                    metadata = final_response["metadata_parsed"]
                    for key, value in metadata.items():
                        if key != "agent_processing_status":  # Already shown during streaming
                            metadata_table.add_row(str(key), str(value))
                    console.print(metadata_table)

            if not current_text:
                console.print("[yellow]No text response received from agent.[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Streaming interrupted by user[/yellow]")
        ctx.exit(0)
    except Exception as e:
        console.print(f"[red]Error during streaming: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.pass_context
def chats(ctx, output: str):
    """List all chats in the workspace."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status("Fetching chats..."):
            chats_data = api.get_all_chats()

        if output == "json":
            console.print(json.dumps(chats_data, indent=2))
        else:
            if not chats_data:
                console.print("[yellow]No chats found[/yellow]")
                return

            table = Table(title="Workspace Chats")
            table.add_column("Chat ID", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Customer ID", style="green")
            table.add_column("Created", style="dim")

            # Handle different response formats
            chat_list = chats_data if isinstance(chats_data, list) else chats_data.get("items", [])

            for chat in chat_list:
                table.add_row(
                    chat.get("id", "N/A"),
                    chat.get("name", "N/A"),
                    chat.get("customerId", "N/A"),
                    chat.get("createdAt", "N/A"),
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error fetching chats: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("chat_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.pass_context
def chat(ctx, chat_id: str, output: str):
    """Get details of a specific chat."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching chat {chat_id}..."):
            chat_data = api.get_chat(chat_id)

        if output == "json":
            console.print(json.dumps(chat_data, indent=2))
        else:
            console.print(Panel(f"[bold green]Chat Details[/bold green]"))

            table = Table()
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")

            for key, value in chat_data.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                table.add_row(str(key), str(value))

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error fetching chat: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("query")
@click.option(
    "--top-k",
    "-k",
    default=10,
    type=click.IntRange(1, 50),
    help="Number of documents to retrieve (1-50)",
)
@click.option(
    "--status", type=click.Choice(["published", "suspended"]), help="Filter by document status"
)
@click.option("--document-id", help="Search within specific document ID")
@click.option("--topics", help="Comma-separated topic IDs to filter by")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed search information")
@click.pass_context
def search(
    ctx,
    query: str,
    top_k: int,
    status: Optional[str],
    document_id: Optional[str],
    topics: Optional[str],
    output: str,
    verbose: bool,
):
    """Search for documents in the knowledge hub."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    # Build metadata filters
    metadata = {}
    if status:
        metadata["status"] = status
    if document_id:
        metadata["documentId"] = document_id
    if topics:
        topic_list = [topic.strip() for topic in topics.split(",") if topic.strip()]
        if topic_list:
            metadata["topic"] = topic_list

    try:
        with console.status("Searching knowledge hub..."):
            results = api.search_documents(
                text=query, top_k=top_k, metadata=metadata if metadata else None
            )

        if output == "json":
            console.print(json.dumps(results, indent=2))
        else:
            # Handle different response formats - results might be array or dict
            documents = results if isinstance(results, list) else results.get("results", [])

            if not documents:
                console.print("[yellow]No documents found for your query[/yellow]")
                return

            console.print(Panel(f"[bold green]Found {len(documents)} document(s)[/bold green]"))

            for i, doc in enumerate(documents, 1):
                score = doc.get("cosinesim", 0)
                doc_id = doc.get("doc_id", doc.get("chunk_id", "N/A"))

                # Extract text content directly from document
                text_content = doc.get("raw_text", "No content available")
                doc_status = doc.get("status", "unknown")
                doc_topics = doc.get("topics", [])
                doc_title = doc.get("title", "Untitled")

                # Create header
                header = f"[bold cyan]Document {i}[/bold cyan] (Score: {score:.3f})"

                if verbose:
                    # Verbose mode: show all details
                    table = Table(title=f"Document {i} Details")
                    table.add_column("Field", style="cyan")
                    table.add_column("Value", style="white")

                    table.add_row("Document ID", doc_id)
                    table.add_row("Relevance Score", f"{score:.4f}")
                    table.add_row("Status", doc_status)
                    table.add_row("Topics", ", ".join(doc_topics) if doc_topics else "None")
                    table.add_row(
                        "Content Preview",
                        text_content[:200] + "..." if len(text_content) > 200 else text_content,
                    )

                    console.print(table)
                else:
                    # Default mode: show clean content
                    console.print(
                        Panel(
                            text_content[:500] + "..." if len(text_content) > 500 else text_content,
                            title=header,
                            border_style="blue",
                        )
                    )

                if i < len(documents):  # Add separator except for last item
                    console.print()

    except Exception as e:
        console.print(f"[red]Error searching documents: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    config: ToothFairyConfig = ctx.obj["config"]

    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Base URL", config.base_url)
    table.add_row("AI URL", config.ai_url)
    table.add_row("API Key", f"{'*' * 20}...{config.api_key[-4:]}" if config.api_key else "Not set")
    table.add_row("Workspace ID", config.workspace_id)

    console.print(table)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--import-type", help="Import type (optional, auto-detected from extension)")
@click.option("--content-type", help="Content type (optional, auto-detected from extension)")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed upload information")
@click.pass_context
def upload(
    ctx,
    file_path: str,
    import_type: Optional[str],
    content_type: Optional[str],
    output: str,
    verbose: bool,
):
    """Upload a file to ToothFairy workspace."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        from pathlib import Path

        # Resolve file path
        resolved_path = Path(file_path).resolve()
        local_filename = resolved_path.name

        # Validate file extension
        valid_extensions = [
            'pdf', 'docx', 'txt', 'csv', 'md', 'html', 'xlsx', 'pptx', 'ppt',
            'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'java', 'py', 'yaml',
            'yml', 'sql', 'sh', 'php', 'js', 'ts', 'tsx', 'jsx', 'csharp',
            'rb', 'jsonl', 'wav', 'mp3', 'aac', 'ogg', 'flac', 'mp4',
            'avi', 'mov', 'wmv', 'flv', 'webm', 'json'
        ]

        ext = resolved_path.suffix.lower().lstrip('.')
        if ext not in valid_extensions:
            console.print(f"[red]Error: Unsupported file extension '.{ext}'[/red]")
            console.print(f"[yellow]Supported extensions: {', '.join(valid_extensions)}[/yellow]")
            ctx.exit(1)

        console.print(f"[cyan]Uploading {local_filename} to ToothFairy...[/cyan]")
        if verbose:
            console.print(f"[dim]Local path: {resolved_path}[/dim]")

        # Progress tracking
        last_progress = 0

        def progress_callback(percent: int, loaded: int, total: int):
            nonlocal last_progress
            # Update progress every 5%
            if percent - last_progress >= 5 or percent == 100:
                console.print(
                    f"[dim]Uploading... {percent}% ({loaded/(1024*1024):.1f}MB / {total/(1024*1024):.1f}MB)[/dim]"
                )
                last_progress = percent

        with console.status("Preparing upload..."):
            result = api.upload_file(
                file_path=str(resolved_path),
                workspace_id=config.workspace_id,
                import_type=import_type,
                content_type=content_type,
                on_progress=progress_callback if verbose else None,
            )

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Upload completed successfully![/bold green]"))

            table = Table(title="Upload Details")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Original File", result["original_filename"])
            table.add_row("Sanitized File", result["sanitized_filename"])
            table.add_row("Import Type", result["import_type"])
            table.add_row("Content Type", result["content_type"])
            table.add_row("Size", f"{result['size_mb']:.2f}MB")
            table.add_row("Download Name", result["filename"])

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error uploading file: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option("--filename", required=True, help="Name of the file to download (from upload response)")
@click.option(
    "--workspace-id", help="Workspace ID (uses config default if not specified)"
)
@click.option("--context", default="pdf", help="Download context (default: pdf)")
@click.option("--output-dir", default="./downloads", help="Output directory")
@click.option("--output-name", help="Output filename (defaults to original filename)")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed download information")
@click.pass_context
def download(
    ctx,
    filename: str,
    workspace_id: Optional[str],
    context: str,
    output_dir: str,
    output_name: Optional[str],
    output: str,
    verbose: bool,
):
    """Download a file from ToothFairy workspace."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        from pathlib import Path

        workspace_id = workspace_id or config.workspace_id
        output_name = output_name or Path(filename).name
        output_path = Path(output_dir) / output_name

        console.print(f"[cyan]Downloading {filename} from ToothFairy...[/cyan]")
        if verbose:
            console.print(f"[dim]Workspace ID: {workspace_id}[/dim]")
            console.print(f"[dim]Filename: {filename}[/dim]")
            console.print(f"[dim]Context: {context}[/dim]")
            console.print(f"[dim]Output path: {output_path}[/dim]")

        # Progress tracking
        last_progress = 0

        def progress_callback(percent: int, loaded: int, total: int):
            nonlocal last_progress
            # Update progress every 5%
            if percent - last_progress >= 5 or percent == 100:
                console.print(
                    f"[dim]Downloading... {percent}% ({loaded/(1024*1024):.1f}MB / {total/(1024*1024):.1f}MB)[/dim]"
                )
                last_progress = percent

        with console.status("Preparing download..."):
            result = api.download_file(
                filename=filename,
                workspace_id=workspace_id,
                output_path=str(output_path),
                context=context,
                on_progress=progress_callback if verbose else None,
            )

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Download completed successfully![/bold green]"))

            table = Table(title="Download Details")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("File", filename)
            table.add_row("Size", f"{result['size_mb']}MB")
            table.add_row("Output Path", result["output_path"])
            table.add_row("Workspace ID", workspace_id)

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error downloading file: {e}[/red]")
        ctx.exit(1)


@cli.command()
def help_guide():
    """Show detailed help and usage examples."""
    console.print(
        Panel("[bold cyan]ToothFairyAI CLI - Complete Usage Guide[/bold cyan]", border_style="cyan")
    )

    console.print("\n[bold green]🚀 Getting Started[/bold green]")
    console.print("1. First, configure your credentials:")
    console.print("   [dim]tf configure --api-key YOUR_KEY --workspace-id YOUR_WORKSPACE[/dim]")

    console.print("\n2. Send a message to an agent:")
    console.print('   [dim]tf send "Hello, I need help" --agent-id YOUR_AGENT_ID[/dim]')

    console.print("\n3. Search the knowledge hub:")
    console.print('   [dim]tf search "AI configuration help"[/dim]')

    console.print("\n4. Upload and download files:")
    console.print("   [dim]tf upload document.pdf      # Upload a file to workspace[/dim]")
    console.print('   [dim]tf download --filename "1234567890document.pdf"  # Download file[/dim]')
    
    console.print("\n5. Explore your workspace:")
    console.print("   [dim]tf chats                    # List all conversations[/dim]")
    console.print("   [dim]tf config-show              # View current settings[/dim]")

    console.print("\n[bold blue]💬 Agent Communication Examples[/bold blue]")

    agent_examples = [
        ("Simple message", 'tf send "What are your hours?" --agent-id "info-agent"'),
        (
            "With customer info",
            'tf send "Schedule appointment" --agent-id "scheduler" --customer-info \'{"name": "John"}\'',
        ),
        ("Verbose output", 'tf send "Hello" --agent-id "agent-123" --verbose'),
        ("JSON for scripting", 'tf send "Help" --agent-id "agent-123" --output json'),
    ]

    agent_table = Table(show_header=True, header_style="bold blue")
    agent_table.add_column("Use Case", style="cyan", width=18)
    agent_table.add_column("Command", style="white")

    for use_case, command in agent_examples:
        agent_table.add_row(use_case, command)

    console.print(agent_table)

    console.print("\n[bold magenta]🔍 Knowledge Hub Search Examples[/bold magenta]")

    search_examples = [
        ("Basic search", 'tf search "AI agent configuration"'),
        ("Filter by status", 'tf search "machine learning" --status published'),
        ("Limit results", 'tf search "troubleshooting" --top-k 3'),
        ("Topic filtering", 'tf search "automation" --topics "topic_123,topic_456"'),
        ("Specific document", 'tf search "settings" --document-id "doc_550..."'),
        ("Verbose details", 'tf search "deployment" --verbose'),
        ("JSON output", 'tf search "API docs" --output json'),
    ]

    search_table = Table(show_header=True, header_style="bold magenta")
    search_table.add_column("Use Case", style="cyan", width=18)
    search_table.add_column("Command", style="white")

    for use_case, command in search_examples:
        search_table.add_row(use_case, command)

    console.print(search_table)

    console.print("\n[bold green]📁 File Management Examples[/bold green]")

    file_examples = [
        ("Upload document", "tf upload document.pdf"),
        ("Upload with type", "tf upload image.png --import-type imported-image"),
        ("Upload verbose", "tf upload data.csv --verbose"),
        ("Download file", 'tf download --filename "1234567890document.pdf"'),
        ("Download to folder", 'tf download --filename "file.pdf" --output-dir ./files'),
        ("Download verbose", 'tf download --filename "file.pdf" --verbose'),
    ]

    file_table = Table(show_header=True, header_style="bold green")
    file_table.add_column("Use Case", style="cyan", width=18)
    file_table.add_column("Command", style="white")

    for use_case, command in file_examples:
        file_table.add_row(use_case, command)

    console.print(file_table)

    console.print("\n[bold cyan]📋 Workspace Management Examples[/bold cyan]")

    mgmt_examples = [
        ("List all chats", "tf chats"),
        ("View chat details", "tf chat CHAT_ID"),
        ("Show config", "tf config-show"),
        ("Detailed help", "tf help-guide"),
    ]

    mgmt_table = Table(show_header=True, header_style="bold cyan")
    mgmt_table.add_column("Use Case", style="cyan", width=18)
    mgmt_table.add_column("Command", style="white")

    for use_case, command in mgmt_examples:
        mgmt_table.add_row(use_case, command)

    console.print(mgmt_table)

    console.print("\n[bold yellow]🔧 Configuration Options[/bold yellow]")
    config_table = Table(show_header=True, header_style="bold yellow")
    config_table.add_column("Method", style="cyan", width=15)
    config_table.add_column("Description", style="white")
    config_table.add_column("Example", style="dim")

    config_options = [
        ("Environment", "Set environment variables", "export TF_API_KEY=your_key"),
        (
            "Config file",
            "Use ~/.toothfairy/config.yml",
            "api_key: your_key\\nworkspace_id: your_workspace",
        ),
        ("CLI arguments", "Pass config file path", "tf --config /path/to/config.yml send ..."),
    ]

    for method, desc, example in config_options:
        config_table.add_row(method, desc, example)

    console.print(config_table)

    console.print("\n[bold red]⚠️  Common Issues & Solutions[/bold red]")
    issues_table = Table(show_header=True, header_style="bold red")
    issues_table.add_column("Issue", style="red", width=25)
    issues_table.add_column("Solution", style="white")

    issues = [
        (
            "Configuration incomplete",
            "Run: tf configure --api-key YOUR_KEY --workspace-id YOUR_WORKSPACE",
        ),
        ("No text response found", "Use --verbose flag to see full response details"),
        ("Agent not responding", "Check agent-id is correct and agent is active"),
        ("Network errors", "Verify API endpoints are accessible and credentials are valid"),
    ]

    for issue, solution in issues:
        issues_table.add_row(issue, solution)

    console.print(issues_table)

    console.print("\n[bold cyan]🔍 Search Filtering Guide[/bold cyan]")
    console.print("Knowledge Hub search supports powerful filtering options:")
    console.print("• [cyan]--status[/cyan]: Filter documents by 'published' or 'suspended' status")
    console.print("• [cyan]--topics[/cyan]: Use topic IDs from ToothFairyAI (comma-separated)")
    console.print("• [cyan]--document-id[/cyan]: Search within a specific document")
    console.print("• [cyan]--top-k[/cyan]: Control number of results (1-50)")
    console.print("• [cyan]--verbose[/cyan]: Show relevance scores and metadata")

    console.print("\n[bold magenta]📖 More Help[/bold magenta]")
    console.print("• Use [cyan]tf COMMAND --help[/cyan] for command-specific help")
    console.print("• Use [cyan]--verbose[/cyan] flag to see detailed request/response information")
    console.print("• Use [cyan]--output json[/cyan] for machine-readable output")
    console.print(
        "• Configuration is loaded from: environment variables → ~/.toothfairy/config.yml → CLI args"
    )

    console.print("\n[bold green]✨ Pro Tips[/bold green]")
    tips = [
        "💾 Save time: Configure once with 'tf configure', then just use 'tf send' and 'tf search'",
        "🔍 Debug issues: Use '--verbose' to see full API responses and troubleshoot",
        "📝 Scripting: Use '--output json' and tools like 'jq' to parse responses",
        "⚡ Quick tests: Only --agent-id is required for send, only query for search",
        "🎯 Better search: Use --status, --topics, and --document-id for targeted results",
        "🔧 Multiple environments: Use different config files with '--config' flag",
        "📁 File uploads: Supports PDF, images, audio, video, and documents up to 15MB",
        "📂 File downloads: Use the filename from upload response for download",
    ]

    for tip in tips:
        console.print(f"  {tip}")

    console.print(
        f"\n[dim]ToothFairy CLI v{__import__('toothfairy_cli').__version__} - For more help, visit the documentation[/dim]"
    )


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()


# Agent Management Commands

@cli.command()
@click.option("--label", help="Agent label")
@click.option("--description", help="Agent description")
@click.option("--emoji", help="Agent emoji")
@click.option("--mode", help="Agent mode (retriever|coder|chatter|planner|computer|voice)")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def create_agent(ctx, label, description, emoji, mode, output, verbose):
    """Create a new agent."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        agent_data = {}
        if label:
            agent_data["label"] = label
        if description:
            agent_data["description"] = description
        if emoji:
            agent_data["emoji"] = emoji
        if mode:
            agent_data["mode"] = mode

        with console.status("Creating agent..."):
            result = api.create_agent(agent_data)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Agent created successfully![/bold green]"))
            console.print(f"[dim]ID: {result.get('id', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error creating agent: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option("--limit", default=50, help="Maximum number to return")
@click.option("--offset", default=0, help="Number to skip")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def list_agents(ctx, limit, offset, output, verbose):
    """List all agents."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status("Fetching agents..."):
            result = api.list_agents(limit=limit, offset=offset)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            agents = result if isinstance(result, list) else result.get("items", [])
            console.print(Panel(f"[bold green]Found {len(agents)} agent(s)[/bold green]"))
            for agent in agents:
                console.print(f"[cyan]• {agent.get('label', 'Unnamed')} ({agent.get('id')})[/cyan]")

    except Exception as e:
        console.print(f"[red]Error listing agents: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("agent_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def get_agent(ctx, agent_id, output, verbose):
    """Get details of a specific agent."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching agent {agent_id}..."):
            result = api.get_agent(agent_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]Agent Details[/bold green]"))
            console.print(f"[dim]ID: {result.get('id')}[/dim]")
            console.print(f"[dim]Label: {result.get('label', 'N/A')}[/dim]")
            console.print(f"[dim]Description: {result.get('description', 'N/A')}[/dim]")
            console.print(f"[dim]Mode: {result.get('mode', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting agent: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("agent_id")
@click.option("--label", help="Agent label")
@click.option("--description", help="Agent description")
@click.option("--emoji", help="Agent emoji")
@click.option("--mode", help="Agent mode")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def update_agent(ctx, agent_id, label, description, emoji, mode, output, verbose):
    """Update an existing agent."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        fields = {}
        if label:
            fields["label"] = label
        if description:
            fields["description"] = description
        if emoji:
            fields["emoji"] = emoji
        if mode:
            fields["mode"] = mode

        with console.status(f"Updating agent {agent_id}..."):
            result = api.update_agent(agent_id, fields)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Agent updated successfully![/bold green]"))

    except Exception as e:
        console.print(f"[red]Error updating agent: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("agent_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def delete_agent(ctx, agent_id, confirm, output, verbose):
    """Delete an agent."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    if not confirm:
        if not click.confirm(f"[yellow]⚠️  Are you sure you want to delete agent {agent_id}?[/yellow]"):
            console.print("[dim]Deletion cancelled.[/dim]")
            ctx.exit(0)

    try:
        with console.status(f"Deleting agent {agent_id}..."):
            result = api.delete_agent(agent_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Agent deleted successfully![/bold green]"))

    except Exception as e:
        console.print(f"[red]Error deleting agent: {e}[/red]")
        ctx.exit(1)


# Authorization Management Commands

@cli.command()
@click.option("--name", help="Authorization name")
@click.option("--type", help="Authorization type")
@click.option("--config", help="Authorization configuration (JSON)")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def create_authorization(ctx, name, type, config, output, verbose):
    """Create a new authorization."""
    config_obj: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config_obj)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        auth_config = {}
        if config:
            try:
                auth_config = json.loads(config)
            except json.JSONDecodeError:
                console.print("[red]Invalid JSON in config[/red]")
                ctx.exit(1)

        auth_data = {}
        if name:
            auth_data["name"] = name
        if type:
            auth_data["type"] = type
        auth_data.update(auth_config)

        with console.status("Creating authorization..."):
            result = api.create_authorization(auth_data)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Authorization created successfully![/bold green]"))
            console.print(f"[dim]ID: {result.get('id', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error creating authorization: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option("--limit", default=50, help="Maximum number to return")
@click.option("--offset", default=0, help="Number to skip")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def list_authorizations(ctx, limit, offset, output, verbose):
    """List all authorizations."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status("Fetching authorizations..."):
            result = api.list_authorizations(limit=limit, offset=offset)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            auths = result if isinstance(result, list) else result.get("items", [])
            console.print(Panel(f"[bold green]Found {len(auths)} authorization(s)[/bold green]"))
            for auth in auths:
                console.print(f"[cyan]• {auth.get('name', 'Unnamed')} ({auth.get('id')})[/cyan]")

    except Exception as e:
        console.print(f"[red]Error listing authorizations: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("auth_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def get_authorization(ctx, auth_id, output, verbose):
    """Get details of a specific authorization."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching authorization {auth_id}..."):
            result = api.get_authorization(auth_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]Authorization Details[/bold green]"))
            console.print(f"[dim]ID: {result.get('id')}[/dim]")
            console.print(f"[dim]Name: {result.get('name', 'N/A')}[/dim]")
            console.print(f"[dim]Type: {result.get('type', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting authorization: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option("--id", help="Authorization ID")
@click.option("--name", help="Authorization name")
@click.option("--type", help="Authorization type")
@click.option("--config", help="Authorization configuration (JSON)")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def update_authorization(ctx, id, name, type, config, output, verbose):
    """Update an existing authorization."""
    config_obj: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config_obj)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        fields = {}
        if id:
            fields["id"] = id
        if name:
            fields["name"] = name
        if type:
            fields["type"] = type
        if config:
            try:
                auth_config = json.loads(config)
                fields.update(auth_config)
            except json.JSONDecodeError:
                console.print("[red]Invalid JSON in config[/red]")
                ctx.exit(1)

        with console.status("Updating authorization..."):
            result = api.update_authorization(fields)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Authorization updated successfully![/bold green]"))

    except Exception as e:
        console.print(f"[red]Error updating authorization: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("auth_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def delete_authorization(ctx, auth_id, confirm, output, verbose):
    """Delete an authorization."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    if not confirm:
        if not click.confirm(f"[yellow]⚠️  Are you sure you want to delete authorization {auth_id}?[/yellow]"):
            console.print("[dim]Deletion cancelled.[/dim]")
            ctx.exit(0)

    try:
        with console.status(f"Deleting authorization {auth_id}..."):
            result = api.delete_authorization(auth_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Authorization deleted successfully![/bold green]"))

    except Exception as e:
        console.print(f"[red]Error deleting authorization: {e}[/red]")
        ctx.exit(1)


# Benchmark Management Commands

@cli.command()
@click.option("--name", help="Benchmark name")
@click.option("--description", help="Benchmark description")
@click.option("--questions", help="Questions JSON array")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def create_benchmark(ctx, name, description, questions, output, verbose):
    """Create a new benchmark."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        questions_list = []
        if questions:
            try:
                questions_list = json.loads(questions)
            except json.JSONDecodeError:
                console.print("[red]Invalid JSON in questions[/red]")
                ctx.exit(1)

        benchmark_data = {}
        if name:
            benchmark_data["name"] = name
        if description:
            benchmark_data["description"] = description
        if questions_list:
            benchmark_data["questions"] = questions_list

        with console.status("Creating benchmark..."):
            result = api.create_benchmark(benchmark_data)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Benchmark created successfully![/bold green]"))
            console.print(f"[dim]ID: {result.get('id', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error creating benchmark: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option("--limit", default=50, help="Maximum number to return")
@click.option("--offset", default=0, help="Number to skip")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def list_benchmarks(ctx, limit, offset, output, verbose):
    """List all benchmarks."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status("Fetching benchmarks..."):
            result = api.list_benchmarks(limit=limit, offset=offset)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            benchmarks = result if isinstance(result, list) else result.get("items", [])
            console.print(Panel(f"[bold green]Found {len(benchmarks)} benchmark(s)[/bold green]"))
            for bm in benchmarks:
                console.print(f"[cyan]• {bm.get('name', 'Unnamed')} ({bm.get('id')})[/cyan]")

    except Exception as e:
        console.print(f"[red]Error listing benchmarks: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("benchmark_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def get_benchmark(ctx, benchmark_id, output, verbose):
    """Get details of a specific benchmark."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching benchmark {benchmark_id}..."):
            result = api.get_benchmark(benchmark_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]Benchmark Details[/bold green]"))
            console.print(f"[dim]ID: {result.get('id')}[/dim]")
            console.print(f"[dim]Name: {result.get('name', 'N/A')}[/dim]")
            console.print(f"[dim]Description: {result.get('description', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting benchmark: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option("--id", help="Benchmark ID")
@click.option("--name", help="Benchmark name")
@click.option("--description", help="Benchmark description")
@click.option("--questions", help="Questions JSON array")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def update_benchmark(ctx, id, name, description, questions, output, verbose):
    """Update an existing benchmark."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        fields = {}
        if id:
            fields["id"] = id
        if name:
            fields["name"] = name
        if description:
            fields["description"] = description
        if questions:
            try:
                fields["questions"] = json.loads(questions)
            except json.JSONDecodeError:
                console.print("[red]Invalid JSON in questions[/red]")
                ctx.exit(1)

        with console.status("Updating benchmark..."):
            result = api.update_benchmark(fields)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Benchmark updated successfully![/bold green]"))

    except Exception as e:
        console.print(f"[red]Error updating benchmark: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("benchmark_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def delete_benchmark(ctx, benchmark_id, confirm, output, verbose):
    """Delete a benchmark."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    if not confirm:
        if not click.confirm(f"[yellow]⚠️  Are you sure you want to delete benchmark {benchmark_id}?[/yellow]"):
            console.print("[dim]Deletion cancelled.[/dim]")
            ctx.exit(0)

    try:
        with console.status(f"Deleting benchmark {benchmark_id}..."):
            result = api.delete_benchmark(benchmark_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Benchmark deleted successfully![/bold green]"))

    except Exception as e:
        console.print(f"[red]Error deleting benchmark: {e}[/red]")
        ctx.exit(1)


# Billing Commands

@cli.command()
@click.argument("month", type=click.IntRange(1, 12))
@click.argument("year", type=click.IntRange(2020, 2100))
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def billing_month_costs(ctx, month, year, output, verbose):
    """Get monthly usage and cost information."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching billing information for {month}/{year}..."):
            result = api.get_month_costs(month, year)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel(f"[bold green]Billing Information for {month}/{year}[/bold green]"))
            
            if "apiUsage" in result:
                console.print("\n[cyan]API Usage:[/cyan]")
                if "totalUoI" in result["apiUsage"]:
                    console.print(f"[dim]  Total Units of Interaction: {result['apiUsage']['totalUoI']}[/dim]")
                if "totalCostUSD" in result["apiUsage"]:
                    console.print(f"[dim]  Total Cost: ${result['apiUsage']['totalCostUSD']}[/dim]")
            
            if "trainingUsage" in result:
                console.print("\n[cyan]Training Usage:[/cyan]")
                console.print("[dim]  See --verbose for details[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting billing information: {e}[/red]")
        ctx.exit(1)


# Channel Management Commands

@cli.command()
@click.option("--name", help="Channel name")
@click.option("--channel", help="Channel type (sms|whatsapp|email)")
@click.option("--provider", help="Service provider")
@click.option("--senderid", help="Sender ID")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def create_channel(ctx, name, channel, provider, senderid, output, verbose):
    """Create a new communication channel."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        channel_data = {}
        if name:
            channel_data["name"] = name
        if channel:
            channel_data["channel"] = channel
        if provider:
            channel_data["provider"] = provider
        if senderid:
            channel_data["senderid"] = senderid

        with console.status("Creating channel..."):
            result = api.create_channel(channel_data)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Channel created successfully![/bold green]"))
            console.print(f"[dim]ID: {result.get('id', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error creating channel: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option("--limit", default=50, help="Maximum number to return")
@click.option("--offset", default=0, help="Number to skip")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def list_channels(ctx, limit, offset, output, verbose):
    """List all channels."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status("Fetching channels..."):
            result = api.list_channels(limit=limit, offset=offset)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            channels = result if isinstance(result, list) else result.get("items", [])
            console.print(Panel(f"[bold green]Found {len(channels)} channel(s)[/bold green]"))
            for ch in channels:
                console.print(f"[cyan]• {ch.get('name', 'Unnamed')} ({ch.get('id')})[/cyan]")

    except Exception as e:
        console.print(f"[red]Error listing channels: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("channel_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def get_channel(ctx, channel_id, output, verbose):
    """Get details of a specific channel."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching channel {channel_id}..."):
            result = api.get_channel(channel_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]Channel Details[/bold green]"))
            console.print(f"[dim]ID: {result.get('id')}[/dim]")
            console.print(f"[dim]Name: {result.get('name', 'N/A')}[/dim]")
            console.print(f"[dim]Channel: {result.get('channel', 'N/A')}[/dim]")
            console.print(f"[dim]Provider: {result.get('provider', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting channel: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option("--id", help="Channel ID")
@click.option("--name", help="Channel name")
@click.option("--channel", help="Channel type")
@click.option("--provider", help="Service provider")
@click.option("--senderid", help="Sender ID")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def update_channel(ctx, id, name, channel, provider, senderid, output, verbose):
    """Update an existing channel."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        fields = {}
        if id:
            fields["id"] = id
        if name:
            fields["name"] = name
        if channel:
            fields["channel"] = channel
        if provider:
            fields["provider"] = provider
        if senderid:
            fields["senderid"] = senderid

        with console.status("Updating channel..."):
            result = api.update_channel(fields)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Channel updated successfully![/bold green]"))

    except Exception as e:
        console.print(f"[red]Error updating channel: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("channel_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def delete_channel(ctx, channel_id, confirm, output, verbose):
    """Delete a channel."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    if not confirm:
        if not click.confirm(f"[yellow]⚠️  Are you sure you want to delete channel {channel_id}?[/yellow]"):
            console.print("[dim]Deletion cancelled.[/dim]")
            ctx.exit(0)

    try:
        with console.status(f"Deleting channel {channel_id}..."):
            result = api.delete_channel(channel_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Channel deleted successfully![/bold green]"))

    except Exception as e:
        console.print(f"[red]Error deleting channel: {e}[/red]")
        ctx.exit(1)


# Connection Management Commands

@cli.command()
@click.option("--limit", default=50, help="Maximum number to return")
@click.option("--offset", default=0, help="Number to skip")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def list_connections(ctx, limit, offset, output, verbose):
    """List all connections."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status("Fetching connections..."):
            result = api.list_connections(limit=limit, offset=offset)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            connections = result if isinstance(result, list) else result.get("items", [])
            console.print(Panel(f"[bold green]Found {len(connections)} connection(s)[/bold green]"))
            for conn in connections:
                console.print(f"[cyan]• {conn.get('name', 'Unnamed')} ({conn.get('id')})[/cyan]")

    except Exception as e:
        console.print(f"[red]Error listing connections: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("connection_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def get_connection(ctx, connection_id, output, verbose):
    """Get details of a specific connection."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching connection {connection_id}..."):
            result = api.get_connection(connection_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]Connection Details[/bold green]"))
            console.print(f"[dim]ID: {result.get('id')}[/dim]")
            console.print(f"[dim]Name: {result.get('name', 'N/A')}[/dim]")
            console.print(f"[dim]Type: {result.get('type', 'N/A')}[/dim]")
            console.print(f"[dim]Host: {result.get('host', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting connection: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("connection_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def delete_connection(ctx, connection_id, confirm, output, verbose):
    """Delete a connection."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    if not confirm:
        if not click.confirm(f"[yellow]⚠️  Are you sure you want to delete connection {connection_id}?[/yellow]"):
            console.print("[dim]Deletion cancelled.[/dim]")
            ctx.exit(0)

    try:
        with console.status(f"Deleting connection {connection_id}..."):
            result = api.delete_connection(connection_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Connection deleted successfully![/bold green]"))

    except Exception as e:
        console.print(f"[red]Error deleting connection: {e}[/red]")
        ctx.exit(1)


# Dictionary Management Commands

@cli.command()
@click.option("--limit", default=50, help="Maximum number to return")
@click.option("--offset", default=0, help="Number to skip")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def list_dictionaries(ctx, limit, offset, output, verbose):
    """List all dictionary entries."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status("Fetching dictionary entries..."):
            result = api.list_dictionaries(limit=limit, offset=offset)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            dicts = result if isinstance(result, list) else result.get("items", [])
            console.print(Panel(f"[bold green]Found {len(dicts)} dictionary entr(y/ies)[/bold green]"))
            for d in dicts:
                console.print(f"[cyan]• {d.get('sourceText', 'N/A')} → {d.get('targetText', 'N/A')} ({d.get('id')})[/cyan]")

    except Exception as e:
        console.print(f"[red]Error listing dictionaries: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("dictionary_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def get_dictionary(ctx, dictionary_id, output, verbose):
    """Get details of a specific dictionary entry."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching dictionary entry {dictionary_id}..."):
            result = api.get_dictionary(dictionary_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]Dictionary Entry Details[/bold green]"))
            console.print(f"[dim]ID: {result.get('id')}[/dim]")
            console.print(f"[dim]Source: {result.get('sourceText', 'N/A')}[/dim]")
            console.print(f"[dim]Target: {result.get('targetText', 'N/A')}[/dim]")
            console.print(f"[dim]Source Language: {result.get('sourceLanguage', 'N/A')}[/dim]")
            console.print(f"[dim]Target Language: {result.get('targetLanguage', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting dictionary entry: {e}[/red]")
        ctx.exit(1)


# Embedding Management Commands

@cli.command()
@click.argument("embedding_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def get_embedding(ctx, embedding_id, output, verbose):
    """Get details of a specific embedding."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching embedding {embedding_id}..."):
            result = api.get_embedding(embedding_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]Embedding Details[/bold green]"))
            console.print(f"[dim]ID: {result.get('id')}[/dim]")
            console.print(f"[dim]Chunk ID: {result.get('chunk_id', 'N/A')}[/dim]")
            console.print(f"[dim]Title: {result.get('title', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting embedding: {e}[/red]")
        ctx.exit(1)


# Settings Management Commands

@cli.command()
@click.argument("settings_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def get_charting_settings(ctx, settings_id, output, verbose):
    """Get charting settings for the workspace."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching charting settings {settings_id}..."):
            result = api.get_charting_settings(settings_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]Charting Settings[/bold green]"))
            console.print(f"[dim]ID: {result.get('id')}[/dim]")
            console.print(f"[dim]Primary Color: {result.get('primaryColor', 'N/A')}[/dim]")
            console.print(f"[dim]Secondary Color: {result.get('secondaryColor', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting charting settings: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("settings_id")
@click.option("--config", help="Settings configuration (JSON)")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def update_charting_settings(ctx, settings_id, config, output, verbose):
    """Update charting settings for the workspace."""
    config_obj: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config_obj)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        settings_config = {}
        if config:
            try:
                settings_config = json.loads(config)
            except json.JSONDecodeError:
                console.print("[red]Invalid JSON in config[/red]")
                ctx.exit(1)

        fields = {"id": settings_id, **settings_config}

        with console.status("Updating charting settings..."):
            result = api.update_charting_settings(fields)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Charting settings updated successfully![/bold green]"))

    except Exception as e:
        console.print(f"[red]Error updating charting settings: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("settings_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def get_embeddings_settings(ctx, settings_id, output, verbose):
    """Get embeddings settings for the workspace."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching embeddings settings {settings_id}..."):
            result = api.get_embeddings_settings(settings_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]Embeddings Settings[/bold green]"))
            console.print(f"[dim]ID: {result.get('id')}[/dim]")
            console.print(f"[dim]Max Chunk Words: {result.get('maxChunkWords', 'N/A')}[/dim]")
            console.print(f"[dim]Chunking Strategy: {result.get('chunkingStrategy', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting embeddings settings: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("settings_id")
@click.option("--config", help="Settings configuration (JSON)")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def update_embeddings_settings(ctx, settings_id, config, output, verbose):
    """Update embeddings settings for the workspace."""
    config_obj: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config_obj)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        settings_config = {}
        if config:
            try:
                settings_config = json.loads(config)
            except json.JSONDecodeError:
                console.print("[red]Invalid JSON in config[/red]")
                ctx.exit(1)

        fields = {"id": settings_id, **settings_config}

        with console.status("Updating embeddings settings..."):
            result = api.update_embeddings_settings(fields)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]✅ Embeddings settings updated successfully![/bold green]"))

    except Exception as e:
        console.print(f"[red]Error updating embeddings settings: {e}[/red]")
        ctx.exit(1)


# Stream Management Commands

@cli.command()
@click.option("--limit", default=50, help="Maximum number to return")
@click.option("--offset", default=0, help="Number to skip")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def list_streams(ctx, limit, offset, output, verbose):
    """List all streams."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status("Fetching streams..."):
            result = api.list_streams(limit=limit, offset=offset)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            streams = result if isinstance(result, list) else result.get("items", [])
            console.print(Panel(f"[bold green]Found {len(streams)} stream(s)[/bold green]"))
            for stream in streams:
                console.print(f"[cyan]• {stream.get('id')}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error listing streams: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("stream_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def get_stream(ctx, stream_id, output, verbose):
    """Get details of a specific stream."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching stream {stream_id}..."):
            result = api.get_stream(stream_id)

        if output == "json":
            console.print(json.dumps(result, indent=2))
        else:
            console.print(Panel("[bold green]Stream Details[/bold green]"))
            console.print(f"[dim]ID: {result.get('id')}[/dim]")
            console.print(f"[dim]Type: {result.get('type', 'N/A')}[/dim]")
            console.print(f"[dim]Status: {result.get('status', 'N/A')}[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting stream: {e}[/red]")
        ctx.exit(1)
