# Air-Gap / Offline Deployment Guide

This guide explains how to use Co-DataScientist in environments without internet access (air-gapped, isolated, or offline environments).

## Quick Start

Run this **once while connected to the internet**:

```bash
co-datascientist setup-airgap
```

That's it! You can now disconnect from the internet and run workflows normally.

## What It Does

The `setup-airgap` command:

1. **Pulls base Python image** from Docker Hub (e.g., `python:3.10-slim`)
2. **Builds complete Docker image** with all your project dependencies pre-installed
3. **Updates your config.yaml** to use the pre-built image

After setup, all subsequent Docker builds use the locally cached image - no internet required!

## Detailed Usage

### Basic Setup

```bash
# Navigate to your project
cd /path/to/your/project

# Run air-gap setup (requires internet)
co-datascientist setup-airgap

# Disconnect from internet

# Run workflows normally (works offline)
co-datascientist run config.yaml
```

### Advanced Options

```bash
# Specify Python version
co-datascientist setup-airgap --python-version 3.11

# Custom image name
co-datascientist setup-airgap --image-name my-company-ml-env

# Different project directory
co-datascientist setup-airgap -d /path/to/project

# Custom config file location
co-datascientist setup-airgap --config custom-config.yaml
```

## Requirements

### Before Running Setup

1. **Docker installed** and running
2. **Internet connection** (for initial setup only)
3. **requirements.txt** in your project (recommended but optional)

### After Setup

- No internet required
- Docker images stored locally
- All workflows run normally

## How It Works

### With Internet (Normal Mode)

When you run a workflow normally, Co-DataScientist generates a Dockerfile like:

```dockerfile
FROM python:3.10-slim         # Requires Docker Hub access
RUN apt-get update...         # Requires Ubuntu repos
RUN pip install pandas...     # Requires PyPI access
COPY . .
CMD ["python", "train.py"]
```

Each line marked with a comment requires internet access.

### Without Internet (Air-Gap Mode)

After running `setup-airgap`, your config.yaml contains:

```yaml
custom_base_image: co-datascientist-airgap:3.10
```

Now Co-DataScientist generates minimal Dockerfiles:

```dockerfile
FROM co-datascientist-airgap:3.10  # Uses local cached image
COPY . .                           # Only copies your code
CMD ["python", "train.py"]
```

This works completely offline because:
- The base image is already cached locally by Docker
- All dependencies are pre-installed in the base image
- Only your code needs to be copied (no downloads)

## Troubleshooting

### "Failed to pull base image"

**Cause:** Docker Hub is not accessible.

**Solution:** Make sure you have internet access during setup.

### "Failed to build image"

**Cause:** Missing dependencies or requirements.txt issues.

**Solution:** 
- Create a `requirements.txt` with all your packages
- Test it first: `pip install -r requirements.txt`
- Then run `setup-airgap` again

### "No such image" error when running workflow

**Cause:** The air-gap image was deleted or never built.

**Solution:** Run `setup-airgap` again (requires internet).

### Workflow runs but missing packages

**Cause:** Your `requirements.txt` is incomplete.

**Solution:**
1. Update your `requirements.txt` with missing packages
2. Re-run `setup-airgap` to rebuild the image

## Private Registry Support

If you want to use your organization's private Docker registry:

```yaml
# config.yaml
custom_base_image: my-registry.company.com/ml-python:3.10
```

Just make sure:
1. The image exists in your registry
2. Docker is authenticated to pull from it
3. The image has Python and all dependencies installed

## Verifying Setup

Check that everything is ready:

```bash
# Verify Docker images are cached
docker images | grep co-datascientist-airgap

# Should show:
# co-datascientist-airgap  3.10  abc123...  2 minutes ago  450MB

# Verify config is updated
cat config.yaml | grep custom_base_image

# Should show:
# custom_base_image: co-datascientist-airgap:3.10
```

## Cleaning Up

To remove the air-gap images and free up space:

```bash
# Remove air-gap image
docker rmi co-datascientist-airgap:3.10

# Also remove from config.yaml
# (Delete or comment out the custom_base_image line)
```

## Best Practices

1. **Create requirements.txt**: Don't rely on `pip freeze` - it includes everything
2. **Test before disconnecting**: Run one workflow online to verify setup
3. **Version pin packages**: Use `pandas==2.0.0` not `pandas` for reproducibility
4. **Document the image**: Keep notes on what Python version and packages are in it

## Example Workflow

Complete example from start to finish:

```bash
# 1. Setup (with internet)
cd my-ml-project
echo "pandas==2.0.0
scikit-learn==1.3.0
numpy==1.24.0" > requirements.txt

co-datascientist setup-airgap

# 2. Verify
docker images | grep co-datascientist-airgap
# co-datascientist-airgap  3.10  abc123...

# 3. Test (still with internet)
co-datascientist run config.yaml

# 4. Disconnect from internet

# 5. Run offline
co-datascientist run config.yaml  # Works!
```

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your Docker and requirements.txt
3. Contact support with the error message

## Technical Details

- **Base image size**: ~450MB (Python + build tools + your packages)
- **Hypothesis images**: ~10MB each (only your code, builds in ~10 seconds)
- **Storage**: Docker stores all images in `/var/lib/docker/`
- **Persistence**: Images survive reboots until explicitly deleted
