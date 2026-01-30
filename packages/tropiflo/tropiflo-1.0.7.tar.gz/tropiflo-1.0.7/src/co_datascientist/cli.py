import asyncio
import logging
import sys
from pathlib import Path

import click
from yaspin import yaspin
import yaml
from . import co_datascientist_api, mcp_local_server
from .settings import settings
from .workflow_runner import workflow_runner
from .cloud_utils.databricks_utils import get_code_from_databricks_config
from .plotting.plot_kpi_progression import main as plot_kpi_main, parse_arguments as plot_kpi_parse_args
from .plotting.python_diff_pdf_simple import SimpleDiffPDFGenerator
from .project_packager import package_project





def ensure_keyring_works():
    """
    Ensure that keyring backend works; fall back to plaintext file if not.
    """
    try:
        import keyring
        test_service = "test_service"
        test_username = "test_user"
        test_password = "test_password"
        keyring.set_password(test_service, test_username, test_password)
        retrieved = keyring.get_password(test_service, test_username)
        keyring.delete_password(test_service, test_username)
        if retrieved == test_password:
            return
    except Exception:
        pass
    try:
        import keyring
        import keyrings.alt.file
        keyring.set_keyring(keyrings.alt.file.PlaintextKeyring())
        click.echo("Using file-based keyring for secure storage")
    except ImportError:
        click.echo("Please install keyrings.alt: pip install keyrings.alt")
        sys.exit(1)


def print_section_header(title: str):
    click.echo(f"\n{title}")
    click.echo("─" * len(title))


def print_success(message: str):
    click.echo(f"SUCCESS: {message}")


def print_info(message: str):
    click.echo(f"INFO: {message}")


def print_warning(message: str):
    click.echo(f"WARNING: {message}")


def print_error(message: str):
    click.echo(f"ERROR: {message}")


def print_logo():
    """Print the awesome Tropiflo ASCII logo in blue with tagline"""
    # Use print() instead of click.echo() to preserve ANSI colors
    BLUE = '\033[94m'
    RESET = '\033[0m'

    print(f"""
{BLUE}$$$$$$$$\\                            $$\\  $$$$$$\\  $$\\           
\\__$$  __|                           \\__|$$  __$$\\ $$ |          
   $$ | $$$$$$\\   $$$$$$\\   $$$$$$\\  $$\\ $$ /  \\__|$$ | $$$$$$\\  
   $$ |$$  __$$\\ $$  __$$\\ $$  __$$\\ $$ |$$$$\\     $$ |$$  __$$\\ 
   $$ |$$ |  \\__|$$ /  $$ |$$ /  $$ |$$ |$$  _|    $$ |$$ /  $$ |
   $$ |$$ |      $$ |  $$ |$$ |  $$ |$$ |$$ |      $$ |$$ |  $$ |
   $$ |$$ |      \\$$$$$$  |$$$$$$$  |$$ |$$ |      $$ |\\$$$$$$  |
   \\__|\\__|       \\______/ $$  ____/ \\__|\\__|      \\__| \\______/ 
                           $$ |                                  
                           $$ |                                  
                           \\__|{RESET}

{BLUE}>{RESET} lets explore this problem!""")


@click.group()
@click.option('--reset-openai-key', is_flag=True, help='Reset the OpenAI API key')
@click.pass_context
def main(ctx, reset_openai_key: bool):
    """Tropiflo: AI-Powered Code Evolution for ML & Data Science
    
    Automatically evolves your Python code to maximize KPIs through intelligent
    hypothesis-driven optimization. Works with both single files and multi-file projects.
    
    Getting Started:
        1. tropiflo set-token --token YOUR_TOKEN
        2. tropiflo run --config config.yaml
        3. tropiflo deploy co_datascientist_checkpoints/best_X/
    
    Core Commands:
        run         - Evolve your code to maximize KPIs
        deploy      - Deploy optimized checkpoints to production
        status      - Check your usage and API status
    
    Analysis Tools:
        plot-kpi    - Visualize KPI progression over time
        diff-pdf    - Generate beautiful code comparison PDFs
    
    Setup:
        set-token   - Configure your API key (REQUIRED before running)
        openai-key  - Add OpenAI key for unlimited usage
    
    Use 'tropiflo COMMAND --help' for detailed info on any command.
    """
    # Initialize keyring and logging
    ensure_keyring_works()
    logging.basicConfig(level=settings.log_level)
    logging.info(f"settings: {settings.model_dump()}")

    print_logo()

    # Reset OpenAI key if requested
    if reset_openai_key:
        settings.delete_openai_key()
        print_success("OpenAI key removed. Using free tier.")

    # Ensure API key exists for all commands except token management
    if ctx.invoked_subcommand not in ('set-token', 'openai-key'):
        try:
            settings.get_api_key()
            if not settings.api_key or not settings.api_key.get_secret_value():
                print_error("No API key found. Please run 'set-token' to configure your API key.")
                sys.exit(1)
        except Exception as e:
            print_error(f"Error loading API key: {e}")
            sys.exit(1)


@main.command()
def mcp_server():
    """Start the local MCP server for IDE integration
    
    Enables integration with IDEs that support the Model Context Protocol (MCP).
    This allows Co-DataScientist to be used directly from your editor.
    """
    print_section_header("MCP Server")
    print_info("Starting MCP server... Press Ctrl+C to exit.")
    asyncio.run(mcp_local_server.run_mcp_server())


@main.command()
@click.option('--working-directory', '-d', type=click.Path(exists=True), default='.', 
              help='Path to your project directory (default: current directory)')
@click.option('--python-version', '-p', type=str, default=None,
              help='Python version to use (default: auto-detect from current environment)')
@click.option('--image-name', '-n', type=str, default='co-datascientist-airgap',
              help='Name for the Docker image (default: co-datascientist-airgap)')
@click.option('--config', '-c', type=click.Path(), default='config.yaml',
              help='Path to config file to update (default: config.yaml)')
def setup_airgap(working_directory, python_version, image_name, config):
    """Prepare environment for air-gapped/offline deployment
    
    This command prepares your environment to work without internet access by:
    1. Pulling the base Python Docker image
    2. Building a complete Docker image with all your dependencies pre-installed
    3. Updating your config.yaml to use the pre-built image
    
    After running this once (with internet), you can disconnect and run workflows offline.
    
    Examples:
        # Basic setup (auto-detects everything)
        co-datascientist setup-airgap
        
        # Specify Python version
        co-datascientist setup-airgap --python-version 3.11
        
        # Custom image name
        co-datascientist setup-airgap --image-name my-ml-env
        
        # Different project directory
        co-datascientist setup-airgap -d /path/to/project
    """
    import subprocess
    import sys
    from pathlib import Path
    from .environment_detector import EnvironmentDetector
    
    print_section_header("Air-Gap Setup")
    print_info("Preparing environment for offline/air-gapped deployment...")
    print()
    
    working_dir = Path(working_directory).resolve()
    
    # Step 1: Auto-detect environment
    print_info("Step 1: Detecting environment...")
    detector = EnvironmentDetector(str(working_dir))
    env_snapshot = detector.get_environment_snapshot()
    
    if not python_version:
        python_version = env_snapshot['python_version']
    
    print_success(f"   Python version: {python_version}")
    print_success(f"   Packages detected: {len(env_snapshot['requirements'])}")
    print()
    
    # Check for requirements.txt
    req_file = working_dir / "requirements.txt"
    if not req_file.exists():
        print_warning("   No requirements.txt found!")
        print_info("   Using packages from your current environment (may include extras)")
        print_info("   TIP: Create requirements.txt with only needed packages for faster builds")
        print()
    
    # Step 2: Pull base Python image
    print_info(f"Step 2: Pulling base Python image (python:{python_version}-slim)...")
    try:
        result = subprocess.run(
            ["docker", "pull", f"python:{python_version}-slim"],
            capture_output=True,
            text=True,
            check=True
        )
        print_success("   Base image pulled successfully")
    except subprocess.CalledProcessError as e:
        print_error(f"   Failed to pull base image: {e.stderr}")
        print_error("   Make sure Docker is running and you have internet access")
        return
    except FileNotFoundError:
        print_error("   Docker not found. Please install Docker first.")
        return
    print()
    
    # Step 3: Build complete image with dependencies
    print_info(f"Step 3: Building complete Docker image with all dependencies...")
    print_info("   This may take a few minutes depending on your packages...")
    
    # Create temporary Dockerfile
    temp_dockerfile = working_dir / ".airgap.Dockerfile"
    try:
        dockerfile_content = f"""# Air-Gap Base Image for Co-DataScientist
FROM python:{python_version}-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt /tmp/requirements.txt 2>/dev/null || echo "# No requirements" > /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt || true

# Image is ready for offline use
"""
        
        temp_dockerfile.write_text(dockerfile_content)
        
        # Build the image
        image_tag = f"{image_name}:{python_version}"
        result = subprocess.run(
            ["docker", "build", "-t", image_tag, "-f", str(temp_dockerfile), str(working_dir)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print_error(f"   Failed to build image:")
            print_error(f"   {result.stderr}")
            return
        
        print_success(f"   Image built: {image_tag}")
        
    finally:
        # Clean up temp Dockerfile
        if temp_dockerfile.exists():
            temp_dockerfile.unlink()
    
    print()
    
    # Step 4: Update config.yaml
    print_info(f"Step 4: Updating configuration...")
    config_path = working_dir / config
    
    try:
        # Load existing config or create new one
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
            print_info(f"   Updating existing config: {config_path}")
        else:
            config_data = {}
            print_info(f"   Creating new config: {config_path}")
        
        # Add custom_base_image setting
        config_data['custom_base_image'] = image_tag
        
        # Write updated config
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
        print_success(f"   Config updated with: custom_base_image: {image_tag}")
        
    except Exception as e:
        print_error(f"   Failed to update config: {e}")
        print_warning(f"   Please manually add to your {config}:")
        print_warning(f"   custom_base_image: {image_tag}")
    
    print()
    print_section_header("Air-Gap Setup Complete!")
    print()
    print_success("Your environment is now ready for offline/air-gapped deployment!")
    print()
    print_info("What was done:")
    print_info(f"   1. Pulled base image: python:{python_version}-slim")
    print_info(f"   2. Built complete image: {image_tag}")
    print_info(f"   3. Updated config: {config_path}")
    print()
    print_info("Next steps:")
    print_info("   1. You can now disconnect from the internet")
    print_info("   2. Run your workflows normally: co-datascientist run")
    print_info("   3. All Docker builds will use the pre-built image")
    print()
    print_info("Note: The Docker images are stored locally and will persist until you run:")
    print_info(f"      docker rmi {image_tag}")
    print()
 

@main.command()
@click.option('--token', required=False, help='Your API key (if not provided, you will be prompted)')
def set_token(token):
    """Set your Co-DataScientist API key (required for first use)
    
    Get your API token from your Co-DataScientist account dashboard.
    This only needs to be done once - the key is securely stored.
    
    Example:
        co-datascientist set-token --token YOUR_TOKEN_HERE
    """
    from pydantic import SecretStr

    print_section_header("Set API Key")
    if not token:
        # import ipdb; ipdb.set_trace()
        token = click.prompt("Please enter your API key", hide_input=True)
    if not token:
        print_error("No API key provided. Aborting.")
        return

    settings.api_key = SecretStr(token)
    try:
        asyncio.run(co_datascientist_api.test_connection())
        print_success("Token validated successfully!")
    except Exception as e:
        print_error(f"Token validation failed: {e}")
        return

    try:
        import keyring
        keyring.set_password(settings.service_name, "user", token)
        print_success("API key saved and will be remembered between sessions!")
    except Exception as e:
        print_error(f"Failed to save API key: {e}")
        print_info("You can set the CO_DATASCIENTIST_API_KEY environment variable for persistence.")


@main.command(context_settings=dict(
    ignore_unknown_options=True,
))

# The idea is that we auto detect everything fdrom the working dir for the most simple usage and then if the stuff we need is not found then we tell the user to define it 

@click.argument('command', nargs=-1, type=click.UNPROCESSED, required=False)
@click.option('--working-directory', 'working_directory', required=False, type=click.Path(exists=True), default='.', show_default=True, help='Path to python file or directory to improve (defaults to current directory)')
@click.option('--config', 'config_path', required=False, type=click.Path(exists=True), help='Path to config file (supports local and cloud execution modes)')
# @click.option('--python-path', required=False, type=click.Path(), default=sys.executable, show_default=True, help='Path to the python interpreter to use')
# @click.option('--parallel', required=False, type=int, default=1, show_default=True, help='Number of code versions to run concurrently')
# @click.option('--run-command', required=False, type=str, help='Custom command to run the project (e.g., "bash run.sh")')
@click.option('--use-cached-qa', is_flag=True, help='Use cached Q&A answers instead of prompting (implies preflight enabled)')
# @click.option('--dockerfile', required=False, type=click.Path(), help='Path to your Dockerfile everything will now be docker based execution.')


def run(command, working_directory, config_path, use_cached_qa):
    """Evolve your code to maximize KPIs through AI-powered optimization
    
    Results are saved in:
    - results/runs/{run_name}/timeline/ (all executed versions)
    - results/runs/{run_name}/by_performance/ (sorted by KPI)
    - results/runs/{run_name}/best -> points to best version
    """
    
    # Load config from YAML file if provided
    config_dict = {}
    if config_path:
        print_info(f"Loading config from: {config_path}")
        with open(config_path, 'r') as file:
            config_dict = yaml.safe_load(file)
        
        # Set API key from config if provided (simplest approach!)
        if 'api_key' in config_dict:
            from .settings import settings
            settings.set_api_key_from_config(config_dict['api_key'])

        # Backend URL overrides (allow private endpoints)
        backend_url = config_dict.get('backend_url') or config_dict.get('co_datascientist_backend_url')
        backend_url_dev = config_dict.get('backend_url_dev') or config_dict.get('co_datascientist_backend_url_dev')
        if backend_url or backend_url_dev:
            settings.set_backend_urls_from_config(backend_url, backend_url_dev)
        
        # Validate and report execution mode
        mode = config_dict.get('mode', '').lower()
        if mode == 'local':
            print_info(f"Using Local executor (mode: local)")
            if config_dict.get('data_volume'):
                print_info(f"Data volume will be mounted: {config_dict['data_volume']}")
        elif 'gcloud' in config_dict or mode == 'gcloud':
            gcloud_config = config_dict.get('gcloud', config_dict)
            print_info(f"Using GCloud executor with project: {gcloud_config.get('project_id')}")
            # Check for data volume in both gcloud config and top-level config
            data_volume = gcloud_config.get('data_volume') or config_dict.get('data_volume')
            if data_volume:
                # Extract bucket name if it's a gs:// URL
                bucket = data_volume.replace("gs://", "").split("/")[0] if data_volume.startswith("gs://") else data_volume
                print_info(f"GCS bucket will be mounted: gs://{bucket}")
        elif 'aws' in config_dict or mode == 'aws':
            print_info(f"Using AWS executor")
        elif 'databricks' in config_dict or mode == 'databricks':
            print_info(f"Using Databricks executor")
        else:
            print_error("Config must contain 'mode' field or 'gcloud', 'aws', or 'databricks' configuration. Aborting.")
            return
        
        # Display engine configuration
        engine = config_dict.get('engine', 'EVOLVE_HYPOTHESIS').upper()
        print_info(f"AI Engine: {engine}")
    else:
        print_info("No config provided, using local executor")
        
    click.echo()
    spinner = None

    # Determine parallel from config, default to 1 if not present
    parallel = 1
    if "parallel" in config_dict:
        try:
            parallel = max(1, int(config_dict["parallel"]))
        except Exception:
            print_warning("Invalid 'parallel' value in config, defaulting to 1.")
            parallel = 1
    else:
        parallel = 1
    
    print(f"Running with parallel: {parallel}")
    
    asyncio.run(
        workflow_runner.run_workflow(
            working_directory, 
            {**config_dict, 'parallel': parallel, 'use_cached_qa': use_cached_qa},
            spinner, 
        )
    )
    # except Exception as e:
    #     msg = str(e)
        
    #     # Handle specific error cases with clean messages
    #     if "Unauthorized" in msg or "401" in msg:
    #         print_error("Authentication failed. Please run 'set-token' again.")
    #     else: 
    #         print_error(msg)
        


@main.command()
def status():
    """Show current usage status and API health
    
    Displays:
    - API connection status
    - Current usage statistics
    - OpenAI key configuration (if set)
    
    Example:
        co-datascientist status
    """
    try:
        with yaspin(text="Checking status...", color="yellow") as spinner:
            status = asyncio.run(co_datascientist_api.get_user_usage_status())
        print_section_header("Usage Status")
    except Exception as e:
        msg = str(e)
        if "Unauthorized" in msg or "401" in msg:
            print_error("Authentication failed. Please run 'set-token' again.")
        else:
            print_error(f"Error fetching status: {e}")


@main.command()
@click.option('--remove', is_flag=True, help='Remove stored OpenAI key')
def openai_key(remove):
    """Manage your OpenAI API key for unlimited usage
    
    Add your own OpenAI key to bypass Co-DataScientist usage limits.
    With your own key, you have unlimited code evolution runs.
    
    Examples:
        # Add OpenAI key
        co-datascientist openai-key
        
        # Remove OpenAI key (revert to Co-DataScientist limits)
        co-datascientist openai-key --remove
    """
    print_section_header("OpenAI Key Management")
    if remove:
        settings.delete_openai_key()
        print_success("OpenAI key removed. Using free tier.")
    else:
        current = settings.get_openai_key(prompt_if_missing=False)
        if current:
            print_success("OpenAI key is currently configured.")
            print_info("Your requests use your OpenAI account for unlimited usage.")
            print_info("Use '--remove' flag to switch back to free tier.")
        else:
            print_info("No OpenAI key configured. Using free tier.")
            settings.get_openai_key(prompt_if_missing=True)


@main.command()
@click.option('--checkpoints-dir', '-c', required=True, type=click.Path(exists=True), 
              help='Directory containing the checkpoint JSON files')
@click.option('--max-iteration', '-m', type=int, default=None,
              help='Maximum iteration to include in the plot (default: include all iterations)')
@click.option('--title', '-t', type=str, default='RMSE Progression Over Iterations',
              help='Title for the plot')
@click.option('--output', '-o', type=str, default=None,
              help='Output file path for the plot (default: auto-generated based on parameters)')
@click.option('--kpi-label', '-k', type=str, default='RMSE',
              help='Label for the KPI metric (default: "RMSE")')
def plot_kpi(checkpoints_dir, max_iteration, title, output, kpi_label):
    """Generate visualization of KPI progression over evolution generations
    
    Creates a line plot showing how your KPI improved across iterations.
    Reads metadata.json files from checkpoint directories.
    
    Examples:
        # Basic usage (new structure)
        co-datascientist plot-kpi -c results/runs/happy_panda_20260120_143025/
        
        # Old structure
        co-datascientist plot-kpi -c co_datascientist_checkpoints/
        
        # Custom title and KPI label
        co-datascientist plot-kpi -c checkpoints/ --title "Model Accuracy" --kpi-label "Accuracy"
        
        # Limit to first 100 iterations
        co-datascientist plot-kpi -c checkpoints/ --max-iteration 100
        
        # Custom output file
        co-datascientist plot-kpi -c checkpoints/ --output my_progress.png
    """
    print_section_header("KPI Progression Plot")
    
    try:
        # Import the plotting functions
        from .plotting.plot_kpi_progression import load_kpi_data, create_plot
        import os
        
        # Validate checkpoint directory
        if not os.path.exists(checkpoints_dir):
            print_error(f"Checkpoint directory not found: {checkpoints_dir}")
            return
        
        print_info(f"Loading KPI data from: {checkpoints_dir}")
        if max_iteration:
            print_info(f"Limiting to iterations <= {max_iteration}")
        print_info("Auto-converting negative KPI values to positive for better visualization")
        
        # Load data
        data = load_kpi_data(checkpoints_dir, max_iteration)
        
        if not data:
            print_error("No valid data found in JSON files!")
            return
        
        print_info(f"Found {len(data)} data points")
        
        # Generate output filename if not provided
        if output is None:
            base_name = "kpi_progression"
            if max_iteration:
                base_name += f"_max{max_iteration}"
            # Clean title for filename
            title_clean = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            title_clean = title_clean.replace(' ', '_').lower()
            if title_clean and title_clean != "rmse_progression_over_iterations":
                base_name += f"_{title_clean}"
            output_path = f"{base_name}_plot.png"
        else:
            output_path = output
        
        # Create the plot
        create_plot(data, title, kpi_label, output_path)
        print_success(f"KPI progression plot saved to: {output_path}")
        
    except Exception as e:
        print_error(f"Error creating KPI plot: {e}")


@main.command()
@click.argument('file1', type=click.Path(exists=True))
@click.argument('file2', type=click.Path(exists=True))
@click.option('--output', '-o', type=str, default=None,
              help='Output PDF file path (default: auto-generated from title)')
@click.option('--title', '-t', type=str, default='Beautiful Python Diff',
              help='Custom title for the diff report')
def diff_pdf(file1, file2, output, title):
    """Generate professional PDF comparison report between two code versions
    
    Creates a side-by-side diff visualization highlighting changes.
    Perfect for documentation, presentations, or code reviews.
    
    Examples:
        # Compare baseline with optimized version
        co-datascientist diff-pdf baseline.py optimized.py
        
        # Custom output filename
        co-datascientist diff-pdf old.py new.py --output improvements.pdf
        
        # Custom title for the report
        co-datascientist diff-pdf v1.py v2.py --title "XOR Optimization Results"
        
        # Compare checkpoints (new structure)
        co-datascientist diff-pdf \\
            results/runs/happy_panda_20260120/timeline/0001_kpi_0.9530_baseline/model.py \\
            results/runs/happy_panda_20260120/timeline/0006_kpi_0.9703_explore/model.py \\
            --title "Model Evolution" --output model_diff.pdf
    """
    print_section_header("Python Diff PDF Generator")
    
    try:
        # Validate files exist
        file1_path = Path(file1)
        file2_path = Path(file2)
        
        if not file1_path.exists():
            print_error(f"File '{file1}' not found")
            return
        
        if not file2_path.exists():
            print_error(f"File '{file2}' not found")
            return
        
        print_info(f"Comparing files:")
        print_info(f"   Baseline: {file1}")
        print_info(f"   Modified: {file2}")
        print_info(f"Generating beautiful PDF diff...")
        
        # Create diff
        generator = SimpleDiffPDFGenerator()
        output_path = generator.create_pdf_diff(str(file1_path), str(file2_path), output, title)
        
        print_success(f"PDF diff saved as '{output_path}'")
        
    except Exception as e:
        print_error(f"Error creating PDF diff: {e}")


@main.command()
@click.argument('checkpoint_path', type=click.Path(exists=True))
@click.option('--original-path', '-p', type=click.Path(exists=True), default=None,
              help='Path to original project directory (auto-detected if not provided)')
@click.option('--output-dir', '-o', type=str, default=None,
              help='Custom output directory name (auto-generated if not provided)')
def deploy(checkpoint_path, original_path, output_dir):
    """Deploy a checkpoint as a complete, runnable project
    
    Takes a checkpoint directory and creates a full copy of your project with the evolved code integrated.
    
    Examples:
    
        # New structure - deploy best checkpoint
        co-datascientist deploy results/runs/happy_panda_20260120/best/
        
        # New structure - deploy specific run
        co-datascientist deploy results/runs/happy_panda_20260120/timeline/0006_kpi_0.9703_explore/
        
        # Specify original project location
        co-datascientist deploy best_6_explore/ --original-path /path/to/my_project
        
        # Custom output directory name
        co-datascientist deploy best_6_explore/ --output-dir my_optimized_pipeline
    """
    import shutil
    import json
    from datetime import datetime
    
    print_section_header("Deploy Checkpoint")
    
    try:
        checkpoint_path = Path(checkpoint_path).resolve()
        
        # Validate checkpoint directory
        if not checkpoint_path.is_dir():
            print_error(f"Checkpoint path must be a directory: {checkpoint_path}")
            return
        
        metadata_path = checkpoint_path / "metadata.json"
        if not metadata_path.exists():
            print_error(f"No metadata.json found in checkpoint: {checkpoint_path}")
            print_info("Make sure you're pointing to a checkpoint directory like 'best_6_explore/'")
            return
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        files_in_checkpoint = metadata.get('files', [])
        checkpoint_name = checkpoint_path.name
        kpi = metadata.get('kpi', 'unknown')
        
        print_info(f"📦 Checkpoint: {checkpoint_name}")
        print_info(f"📊 KPI: {kpi}")
        print_info(f"📄 Files: {', '.join(files_in_checkpoint)}")
        
        # Determine original project path
        if original_path:
            original_path = Path(original_path).resolve()
        else:
            # Try to auto-detect: go up from checkpoint to find project root
            # New structure: project/results/runs/{run_name}/timeline/XXXX/ or /best/
            # Old structure: project/co_datascientist_checkpoints/best_X/
            
            if checkpoint_path.parent.name == "timeline":
                # New structure: timeline folder
                # Go up: timeline -> run_name -> runs -> results -> project
                original_path = checkpoint_path.parent.parent.parent.parent
                print_info(f"🔍 Auto-detected original project (new structure): {original_path}")
            elif checkpoint_path.parent.name == "runs":
                # New structure: /best/ or /by_performance/ symlink at run_name level
                # Go up: run_name -> runs -> results -> project
                original_path = checkpoint_path.parent.parent.parent
                print_info(f"🔍 Auto-detected original project (new structure): {original_path}")
            elif checkpoint_path.parent.parent.name == "co_datascientist_runs":
                # Old transition structure: /best/ or /by_performance/
                original_path = checkpoint_path.parent.parent.parent
                print_info(f"🔍 Auto-detected original project (old structure): {original_path}")
            elif checkpoint_path.parent.name == "co_datascientist_checkpoints":
                # Old structure
                original_path = checkpoint_path.parent.parent
                print_info(f"🔍 Auto-detected original project (old structure): {original_path}")
            else:
                print_error("Could not auto-detect original project path.")
                print_info("Please specify with --original-path")
                return
        
        if not original_path.exists():
            print_error(f"Original project path not found: {original_path}")
            return
        
        # Determine output directory name
        if output_dir:
            output_path = Path(output_dir).resolve()
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            project_name = original_path.name
            output_path = original_path.parent / f"{project_name}_deployed_{checkpoint_name}_{timestamp}"
        
        # Check if output already exists
        if output_path.exists():
            print_error(f"Output directory already exists: {output_path}")
            if not click.confirm("Overwrite?"):
                print_info("Deployment cancelled.")
                return
            shutil.rmtree(output_path)
        
        print_info(f"🚀 Deploying to: {output_path}")
        
        # Copy entire original project
        print_info("📋 Copying original project...")
        shutil.copytree(original_path, output_path, 
                       ignore=shutil.ignore_patterns(
                           'results',  # Main results folder (consolidated)
                           'co_datascientist_checkpoints', 
                           'current_runs',
                           'co_datascientist_runs',
                           'qa_cache.json',
                           '__pycache__',
                           '*.pyc',
                           '.git'
                       ))
        
        # Overwrite with checkpoint files
        print_info("✨ Integrating evolved code...")
        for filename in files_in_checkpoint:
            src_file = checkpoint_path / filename
            dst_file = output_path / filename
            
            if src_file.exists():
                # Create parent directories if needed
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                print_info(f"   ✓ {filename}")
            else:
                print_error(f"   ✗ {filename} (not found in checkpoint)")
        
        # Copy metadata for reference
        shutil.copy2(metadata_path, output_path / "deployment_info.json")
        
        print_success(f"\n✅ Deployment complete!")
        print_success(f"📁 Location: {output_path}")
        print_info(f"\nTo test your deployed project:")
        print_info(f"   cd {output_path}")
        
        # Try to detect run command from project
        if (output_path / "run.sh").exists():
            print_info(f"   bash run.sh")
        elif (output_path / "main.py").exists():
            print_info(f"   python main.py")
        else:
            print_info(f"   <your run command>")
        
    except Exception as e:
        print_error(f"Error deploying checkpoint: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
