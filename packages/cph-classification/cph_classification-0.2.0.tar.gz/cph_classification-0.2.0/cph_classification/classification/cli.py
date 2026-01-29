"""
Custom Lightning CLI for classification tasks.

This module extends LightningCLI to add custom arguments for checkpoint
management and resume training, and links input_dim and num_classes from datamodule to model.
"""

import lightning as L
from lightning.pytorch.cli import LightningCLI


class CLSLightningCLI(LightningCLI):
    """
    Custom Lightning CLI for classification tasks.
    
    Extends LightningCLI with additional arguments for:
    - Resume training from checkpoint
    - Selecting checkpoint for testing (best/last)
    - Auto-linking input_dim and num_classes from datamodule to model
    """
    
    def add_arguments_to_parser(self, parser):
        """
        Add custom arguments to the parser.
        
        Args:
            parser: Argument parser
        """
        # For RESUME training
        parser.add_argument("--fit.ckpt_path", type=str, default=None)
        
        # Select last or best checkpoint for testing
        parser.add_argument("--test.ckpt_path", type=str, default="best")
    
    def before_instantiate_classes(self):
        """
        Called before instantiating classes.
        Auto-sets input_dim and num_classes in model config from datamodule.
        """
        try:
            # Get data config
            if hasattr(self.config, 'data') and hasattr(self.config.data, 'init_args'):
                data_init_args = self.config.data.init_args
                
                # Convert Namespace to dict
                if hasattr(data_init_args, '__dict__'):
                    data_config_dict = vars(data_init_args).copy()
                elif isinstance(data_init_args, dict):
                    data_config_dict = data_init_args.copy()
                else:
                    # Try to get all attributes
                    data_config_dict = {}
                    for key in dir(data_init_args):
                        if not key.startswith('_') and not callable(getattr(data_init_args, key, None)):
                            try:
                                value = getattr(data_init_args, key)
                                data_config_dict[key] = value
                            except:
                                pass
                
                # Check if model needs input_dim and num_classes
                if (hasattr(self.config, 'model') and 
                    hasattr(self.config.model, 'init_args') and
                    hasattr(self.config.model.init_args, 'model') and
                    hasattr(self.config.model.init_args.model, 'init_args')):
                    
                    model_model_init_args = self.config.model.init_args.model.init_args
                    current_input_dim = getattr(model_model_init_args, 'input_dim', None)
                    current_num_classes = getattr(model_model_init_args, 'num_classes', None)
                    
                    # If input_dim or num_classes is 0 or None, compute from datamodule
                    if (current_input_dim is None or current_input_dim == 0) or \
                       (current_num_classes is None or current_num_classes == 0):
                        # Create temporary datamodule to get dimensions
                        from cph_classification.classification.datamodule import DataModuleCLS
                        
                        # Create and setup datamodule
                        temp_dm = DataModuleCLS(**data_config_dict)
                        temp_dm.setup('fit')
                        
                        computed_input_dim = temp_dm.get_input_dim()
                        computed_num_classes = temp_dm.get_num_classes()
                        
                        # Set input_dim and num_classes in model config
                        if current_input_dim is None or current_input_dim == 0:
                            setattr(model_model_init_args, 'input_dim', computed_input_dim)
                        if current_num_classes is None or current_num_classes == 0:
                            setattr(model_model_init_args, 'num_classes', computed_num_classes)
                        
        except Exception as e:
            # If auto-detection fails, we'll try in after_instantiate_classes
            import warnings
            warnings.warn(
                f"Could not auto-detect dimensions in before_instantiate_classes: {e}. "
                "Will try again after instantiation."
            )
    
    def after_instantiate_classes(self):
        """
        Called after instantiating classes.
        Fallback: Auto-sets input_dim and num_classes in model from datamodule if not set.
        """
        try:
            # If model's dimensions are still 0, get them from datamodule
            if (hasattr(self.model, 'model') and 
                hasattr(self.model.model, 'input_dim') and
                hasattr(self.model.model, 'num_classes')):
                
                input_dim_ok = self.model.model.input_dim > 0
                num_classes_ok = self.model.model.num_classes > 0
                
                if not input_dim_ok or not num_classes_ok:
                    if hasattr(self.datamodule, 'get_input_dim') and hasattr(self.datamodule, 'get_num_classes'):
                        # Setup datamodule if not already done
                        if not hasattr(self.datamodule, 'input_dim') or self.datamodule.input_dim is None:
                            self.datamodule.setup('fit')
                        
                        input_dim = self.datamodule.get_input_dim()
                        num_classes = self.datamodule.get_num_classes()
                        
                        # Get model config from config object (not from partially built model)
                        if (hasattr(self.config, 'model') and 
                            hasattr(self.config.model, 'init_args') and
                            hasattr(self.config.model.init_args, 'model') and
                            hasattr(self.config.model.init_args.model, 'init_args')):
                            
                            model_init_args = self.config.model.init_args.model.init_args
                            
                            # Get config values
                            hidden_layers = getattr(model_init_args, 'hidden_layers', [128, 64, 32])
                            dropout_rates = getattr(model_init_args, 'dropout_rates', [0.15, 0.1, 0.05])
                            activation = getattr(model_init_args, 'activation', 'relu')
                            
                            # Recreate model with correct dimensions
                            from cph_classification.classification.modelfactory import ClassificationModel
                            
                            model_config = {
                                'input_dim': input_dim,
                                'num_classes': num_classes,
                                'hidden_layers': hidden_layers,
                                'dropout_rates': dropout_rates,
                                'activation': activation,
                            }
                            
                            # Create new model with correct dimensions
                            new_model = ClassificationModel(**model_config)
                            self.model.model = new_model
                        else:
                            # Fallback: use set_dimensions if available
                            if hasattr(self.model.model, 'set_dimensions'):
                                self.model.model.set_dimensions(input_dim, num_classes)
                            else:
                                raise RuntimeError("Cannot set dimensions: model config not accessible")
                    
        except Exception as e:
            import warnings
            import traceback
            warnings.warn(
                f"Could not auto-set dimensions in after_instantiate_classes: {e}\n"
                f"Traceback: {traceback.format_exc()}\n"
                "Please set input_dim and num_classes manually in config."
            )

