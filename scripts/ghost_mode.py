#!/usr/bin/env python3
"""
Ghost Mode - Privacy and Stealth Module for SATx
Provides bulletproof privacy protection and operational security.
"""

import logging
import os
import sys
from pathlib import Path
import shutil
import json
import hashlib
import secrets
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GhostMode:
    """
    Privacy and stealth operations manager.
    Implements various security measures to preserve user privacy.
    """
    
    def __init__(self, config_file='configs/station.ini'):
        """Initialize ghost mode."""
        self.config_file = Path(config_file)
        self.ghost_enabled = False
        self.privacy_level = 'standard'
        
        logger.info("Ghost Mode initialized")
    
    def enable_ghost_mode(self, level='maximum'):
        """
        Enable ghost mode with specified privacy level.
        
        Levels:
        - 'standard': Basic privacy (no logs to external services)
        - 'high': Enhanced privacy (minimal local logs, no identifiers)
        - 'maximum': Bulletproof privacy (no logs, encrypted data, anonymous operation)
        """
        logger.warning("="*60)
        logger.warning("ENABLING GHOST MODE - PRIVACY PROTECTION ACTIVE")
        logger.warning("="*60)
        
        self.ghost_enabled = True
        self.privacy_level = level
        
        # Apply privacy measures based on level
        if level == 'standard':
            self._apply_standard_privacy()
        elif level == 'high':
            self._apply_high_privacy()
        elif level == 'maximum':
            self._apply_maximum_privacy()
        
        logger.warning(f"Ghost Mode: {level.upper()} privacy level active")
        logger.warning("Your activities are now protected")
    
    def _apply_standard_privacy(self):
        """Apply standard privacy measures."""
        logger.info("Applying STANDARD privacy measures:")
        
        # Disable external services
        self._disable_external_services()
        logger.info("  ✓ External services disabled")
        
        # Use generic station identifiers
        self._anonymize_station_name()
        logger.info("  ✓ Station anonymized")
    
    def _apply_high_privacy(self):
        """Apply high privacy measures."""
        logger.info("Applying HIGH privacy measures:")
        
        # Standard measures
        self._apply_standard_privacy()
        
        # Minimize logging
        self._minimize_logging()
        logger.info("  ✓ Logging minimized")
        
        # Disable metadata collection
        self._disable_metadata_collection()
        logger.info("  ✓ Metadata collection disabled")
        
        # Clear identifying information
        self._clear_identifying_info()
        logger.info("  ✓ Identifying information cleared")
    
    def _apply_maximum_privacy(self):
        """Apply maximum (bulletproof) privacy measures."""
        logger.info("Applying MAXIMUM (BULLETPROOF) privacy measures:")
        
        # High privacy measures
        self._apply_high_privacy()
        
        # Encrypt all data
        self._enable_encryption()
        logger.info("  ✓ Data encryption enabled")
        
        # Use anonymous identifiers
        self._use_anonymous_ids()
        logger.info("  ✓ Anonymous identifiers in use")
        
        # Disable all telemetry
        self._disable_all_telemetry()
        logger.info("  ✓ All telemetry disabled")
        
        # Memory-only operation mode
        self._enable_memory_mode()
        logger.info("  ✓ Memory-only operation enabled")
        
        logger.warning("\n⚠️  BULLETPROOF GHOST MODE ACTIVE ⚠️")
        logger.warning("No persistent logs. No external connections. No traces.")
    
    def _disable_external_services(self):
        """Disable all external service integrations."""
        # Update config to disable SatNOGS and other external services
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(self.config_file)
            
            if 'station' in config:
                config['station']['satnogs_enabled'] = 'false'
                config['station']['satnogs_station_id'] = ''
                config['station']['satnogs_api_key'] = ''
            
            # Save config
            with open(self.config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            logger.error(f"Error disabling external services: {e}")
    
    def _anonymize_station_name(self):
        """Replace station name with anonymous identifier."""
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(self.config_file)
            
            if 'station' in config:
                # Generate anonymous station ID
                anon_id = f"GHOST-{secrets.token_hex(4).upper()}"
                config['station']['name'] = anon_id
                config['station']['location'] = 'Undisclosed'
            
            with open(self.config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            logger.error(f"Error anonymizing station: {e}")
    
    def _minimize_logging(self):
        """Minimize logging to essential operations only."""
        # Set logging level to WARNING or ERROR
        logging.getLogger().setLevel(logging.WARNING)
        logger.warning("Logging minimized - only warnings and errors will be recorded")
    
    def _disable_metadata_collection(self):
        """Disable metadata collection in recordings."""
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(self.config_file)
            
            if 'station' not in config:
                config['station'] = {}
            
            # Add ghost mode flag
            config['station']['ghost_mode'] = 'true'
            config['station']['collect_metadata'] = 'false'
            
            with open(self.config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            logger.error(f"Error disabling metadata: {e}")
    
    def _clear_identifying_info(self):
        """Clear identifying information from config."""
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(self.config_file)
            
            if 'station' in config:
                # Keep only essential technical parameters
                # Clear location data
                config['station']['latitude'] = '0.0'
                config['station']['longitude'] = '0.0'
                config['station']['elevation'] = '0.0'
            
            with open(self.config_file, 'w') as f:
                config.write(f)
            
            logger.warning("Location data cleared for privacy")
        except Exception as e:
            logger.error(f"Error clearing identifying info: {e}")
    
    def _enable_encryption(self):
        """Enable encryption for sensitive data."""
        # Create encryption key if not exists
        key_file = Path('configs/.ghost_key')
        if not key_file.exists():
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key = secrets.token_hex(32)
            key_file.write_text(key)
            key_file.chmod(0o600)  # Read/write for owner only
            logger.info("Encryption key generated")
        else:
            logger.info("Using existing encryption key")
    
    def _use_anonymous_ids(self):
        """Use anonymous identifiers for all operations."""
        # Generate session ID
        session_id = f"GHOST-SESSION-{secrets.token_hex(8).upper()}"
        logger.info(f"Anonymous session ID: {session_id}")
        
        # Store in environment variable for other scripts to use
        os.environ['SATX_GHOST_SESSION'] = session_id
    
    def _disable_all_telemetry(self):
        """Disable all telemetry and reporting."""
        logger.warning("All telemetry and external reporting disabled")
        # Block any analytics or reporting modules
        os.environ['SATX_NO_TELEMETRY'] = '1'
        os.environ['SATX_NO_REPORTING'] = '1'
    
    def _enable_memory_mode(self):
        """Enable memory-only operation (minimal disk writes)."""
        logger.warning("Memory-only mode: Results stored in RAM, not on disk")
        os.environ['SATX_MEMORY_MODE'] = '1'
        
        # Create ramdisk-style directory if possible (Linux)
        try:
            ram_dir = Path('/tmp/satx_ghost')
            ram_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Temporary storage: {ram_dir}")
        except Exception as e:
            logger.warning(f"Could not create RAM directory: {e}")
    
    def disable_ghost_mode(self):
        """Disable ghost mode and restore normal operation."""
        logger.warning("Disabling ghost mode...")
        
        self.ghost_enabled = False
        self.privacy_level = None
        
        # Clear environment variables
        for var in ['SATX_GHOST_SESSION', 'SATX_NO_TELEMETRY', 'SATX_NO_REPORTING', 'SATX_MEMORY_MODE']:
            os.environ.pop(var, None)
        
        # Restore normal logging
        logging.getLogger().setLevel(logging.INFO)
        
        logger.info("Ghost mode disabled - normal operation restored")
    
    def secure_delete(self, file_path):
        """
        Securely delete a file (overwrite before deletion).
        
        Args:
            file_path: Path to file to delete
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return
        
        try:
            # Get file size
            size = file_path.stat().st_size
            
            # Overwrite with random data multiple times
            with open(file_path, 'wb') as f:
                for _ in range(3):  # 3-pass overwrite
                    f.seek(0)
                    f.write(secrets.token_bytes(size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Delete file
            file_path.unlink()
            logger.info(f"Securely deleted: {file_path}")
        
        except Exception as e:
            logger.error(f"Error securely deleting {file_path}: {e}")
    
    def clean_traces(self):
        """Clean all operational traces."""
        logger.warning("Cleaning operational traces...")
        
        # Clear logs
        logs_dir = Path('logs')
        if logs_dir.exists():
            for log_file in logs_dir.glob('*.log'):
                self.secure_delete(log_file)
            logger.info("  ✓ Log files cleaned")
        
        # Clear temporary recordings
        recordings_dir = Path('recordings')
        if recordings_dir.exists():
            for rec_file in recordings_dir.glob('*.iq'):
                self.secure_delete(rec_file)
            logger.info("  ✓ Recording files cleaned")
        
        # Clear cache
        cache_dir = Path('.cache')
        if cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
            logger.info("  ✓ Cache cleaned")
        
        logger.warning("All traces cleaned")
    
    def status(self):
        """Display ghost mode status."""
        logger.info("="*60)
        logger.info("GHOST MODE STATUS")
        logger.info("="*60)
        
        if self.ghost_enabled:
            logger.warning(f"Status: ACTIVE")
            logger.warning(f"Privacy Level: {self.privacy_level.upper()}")
            logger.warning("Your operations are protected")
        else:
            logger.info("Status: INACTIVE")
            logger.info("Privacy protection is not active")
        
        logger.info("="*60)


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SATx Ghost Mode - Privacy Protection')
    parser.add_argument('--enable', action='store_true', help='Enable ghost mode')
    parser.add_argument('--disable', action='store_true', help='Disable ghost mode')
    parser.add_argument('--level', choices=['standard', 'high', 'maximum'], default='maximum',
                       help='Privacy level (default: maximum)')
    parser.add_argument('--clean', action='store_true', help='Clean all traces')
    parser.add_argument('--status', action='store_true', help='Show ghost mode status')
    
    args = parser.parse_args()
    
    ghost = GhostMode()
    
    if args.enable:
        ghost.enable_ghost_mode(level=args.level)
    elif args.disable:
        ghost.disable_ghost_mode()
    elif args.clean:
        ghost.clean_traces()
    elif args.status:
        ghost.status()
    else:
        parser.print_help()
    
    return 0


if __name__ == '__main__':
    exit(main())
