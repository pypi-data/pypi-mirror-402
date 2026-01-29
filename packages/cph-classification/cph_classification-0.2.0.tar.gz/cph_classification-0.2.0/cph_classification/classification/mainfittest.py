"""
Main entry point for fit+test workflow.

This script runs both training and testing in sequence,
useful for quick experimentation and validation.
"""

from cph_classification.classification.cli import CLSLightningCLI


def cli_main():
    """
    Main function to run fit+test workflow.
    
    Creates CLI instance without running, then manually calls
    fit and test methods.
    """
    # Create CLI instance without running
    cli = CLSLightningCLI(run=False)
    
    # Run training
    # Get ckpt_path from config (can be None for new training)
    fit_config = getattr(cli.config, 'fit', None)
    if fit_config is not None:
        ckpt_path = getattr(fit_config, 'ckpt_path', None)
    else:
        ckpt_path = None
    
    cli.trainer.fit(
        model=cli.model,
        datamodule=cli.datamodule,
        ckpt_path=ckpt_path
    )
    
    # Run testing
    # Get test ckpt_path (defaults to 'best')
    test_config = getattr(cli.config, 'test', None)
    if test_config is not None:
        test_ckpt_path = getattr(test_config, 'ckpt_path', 'best')
    else:
        test_ckpt_path = 'best'
    
    cli.trainer.test(
        datamodule=cli.datamodule,
        ckpt_path=test_ckpt_path
    )


if __name__ == "__main__":
    cli_main()

