"""
Main entry point for classification training using Lightning CLI.

This script provides the standard Lightning CLI interface for training,
testing, and prediction.
"""

from cph_classification.classification.cli import CLSLightningCLI


def cli_main():
    """Main function to run Lightning CLI."""
    # Use CLSLightningCLI instead of LightningCLI for compatibility with .yaml
    cli = CLSLightningCLI()


if __name__ == "__main__":
    cli_main()

