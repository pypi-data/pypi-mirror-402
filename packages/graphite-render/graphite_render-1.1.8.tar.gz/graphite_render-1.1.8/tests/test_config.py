import os
import tempfile
import unittest
import warnings

import yaml


class TestConfigFallback(unittest.TestCase):
    """Test configuration file fallback behavior."""

    def test_primary_config_file_exists(self):
        """Test that primary config file is loaded when it exists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('time_zone: America/New_York\n')
            primary_config = f.name
        
        try:
            # Set the env var to point to our test config
            old_env = os.environ.get('GRAPHITE_API_CONFIG')
            os.environ['GRAPHITE_API_CONFIG'] = primary_config
            
            from flask import Flask
            from graphite_render.config import configure
            
            app = Flask(__name__)
            configure(app)
            
            # Verify the config was loaded from primary
            self.assertEqual(app.config['TIME_ZONE'], 'America/New_York')
            
            # Restore env
            if old_env:
                os.environ['GRAPHITE_API_CONFIG'] = old_env
            else:
                os.environ.pop('GRAPHITE_API_CONFIG', None)
        finally:
            if os.path.exists(primary_config):
                os.unlink(primary_config)
    
    def test_fallback_logic_in_code(self):
        """Test that the configure function has fallback logic."""
        # Verify the code contains the expected fallback logic
        import graphite_render.config as config_module
        import inspect
        
        source = inspect.getsource(config_module.configure)
        
        # Check that fallback logic exists
        self.assertIn('fallback_config_file', source, 
                     "Configure function should have fallback_config_file variable")
        self.assertIn('/etc/graphite-api.yml', source,
                     "Configure function should reference /etc/graphite-api.yml")
        self.assertIn('elif os.path.exists(fallback_config_file)', source,
                     "Configure function should check for fallback file existence")
    
    def test_neither_config_file_exists(self):
        """Test that defaults are used when neither config file exists."""
        from flask import Flask
        from graphite_render.config import configure
        
        # Use a non-existent config path and ensure fallback also doesn't exist
        old_env = os.environ.get('GRAPHITE_API_CONFIG')
        os.environ['GRAPHITE_API_CONFIG'] = '/tmp/nonexistent-primary-test-xyz123.yaml'
        
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                app = Flask(__name__)
                configure(app)
                
                # Check that a warning was issued about both files
                warning_messages = [str(warning.message) if hasattr(warning, 'message') else str(warning) for warning in w]
                found_config_warning = any(
                    "Unable to find configuration file" in msg and
                    "/etc/graphite-api.yml" in msg
                    for msg in warning_messages
                )
                self.assertTrue(found_config_warning, 
                               f"Expected config warning mentioning both files. Got: {warning_messages}")
                
                # Check that default timezone was used
                self.assertIsNotNone(app.config.get('TIME_ZONE'))
        finally:
            if old_env:
                os.environ['GRAPHITE_API_CONFIG'] = old_env
            else:
                os.environ.pop('GRAPHITE_API_CONFIG', None)


if __name__ == '__main__':
    unittest.main()
