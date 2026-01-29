"""
Command-line interface entry point for cph-classification.

This module provides the main CLI command that can be invoked via:
    cph-classification fit --config yourproject.yaml
    cph-classification test --config yourproject.yaml
    cph-classification --config yourproject.yaml  (runs fit+test)
"""

import sys
from cph_classification.classification.cli import CLSLightningCLI
from cph_classification.classification.mainfittest import cli_main as fit_test_main


def main():
    """
    Main entry point for cph-classification CLI.
    
    If --config is provided without a subcommand (fit/test/predict),
    defaults to fit+test workflow. Otherwise uses standard Lightning CLI.
    """
    # Check if first argument is a subcommand
    if len(sys.argv) > 1 and sys.argv[1] in ['fit', 'test', 'predict', 'validate']:
        # Standard Lightning CLI with subcommand
        cli = CLSLightningCLI()
    elif '--config' in sys.argv:
        # No subcommand but --config provided, run fit+test workflow
        fit_test_main()
    else:
        # No arguments or unrecognized - use standard CLI (will show help)
        cli = CLSLightningCLI()


if __name__ == "__main__":
    main()
