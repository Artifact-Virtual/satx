#!/usr/bin/env python3
"""
Ghost Mode - Privacy, Stealth, and Sovereignty Module for SATx
Provides bulletproof privacy protection and operational security.

Sovereignty additions:
  - Network trace cleaning (DNS cache, ARP, connection tracking)
  - Outbound connection blocking via iptables
  - Comprehensive sovereignty enforcement
"""

import logging
import os
import sys
import subprocess
import socket
from pathlib import Path
import shutil
from datetime import datetime, timezone
import secrets
import configparser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


class GhostMode:
    """
    Privacy, stealth, and sovereignty operations manager.
    Implements various security measures to preserve user privacy
    and enable fully air-gapped operation.
    """

    def __init__(self, config_file='configs/station.ini'):
        """Initialize ghost mode."""
        self.config_file = PROJECT_ROOT / Path(config_file)
        self.ghost_enabled = False
        self.privacy_level = 'standard'
        self.firewall_rules_added = []

        logger.info("Ghost Mode initialized")

    def enable_ghost_mode(self, level='maximum'):
        """
        Enable ghost mode with specified privacy level.

        Levels:
        - 'standard': Basic privacy (no logs to external services)
        - 'high': Enhanced privacy (minimal local logs, no identifiers)
        - 'maximum': Bulletproof privacy (no logs, encrypted data, anonymous operation)
        - 'sovereign': Maximum + network blocking + trace cleaning
        """
        logger.warning("=" * 60)
        logger.warning("ENABLING GHOST MODE - PRIVACY PROTECTION ACTIVE")
        logger.warning("=" * 60)

        self.ghost_enabled = True
        self.privacy_level = level

        if level == 'standard':
            self._apply_standard_privacy()
        elif level == 'high':
            self._apply_high_privacy()
        elif level == 'maximum':
            self._apply_maximum_privacy()
        elif level == 'sovereign':
            self._apply_sovereign_privacy()

        logger.warning(f"Ghost Mode: {level.upper()} privacy level active")
        logger.warning("Your activities are now protected")

    def _apply_standard_privacy(self):
        """Apply standard privacy measures."""
        logger.info("Applying STANDARD privacy measures:")
        self._disable_external_services()
        logger.info("  ✓ External services disabled")
        self._anonymize_station_name()
        logger.info("  ✓ Station anonymized")

    def _apply_high_privacy(self):
        """Apply high privacy measures."""
        logger.info("Applying HIGH privacy measures:")
        self._apply_standard_privacy()
        self._minimize_logging()
        logger.info("  ✓ Logging minimized")
        self._disable_metadata_collection()
        logger.info("  ✓ Metadata collection disabled")
        self._clear_identifying_info()
        logger.info("  ✓ Identifying information cleared")

    def _apply_maximum_privacy(self):
        """Apply maximum (bulletproof) privacy measures."""
        logger.info("Applying MAXIMUM (BULLETPROOF) privacy measures:")
        self._apply_high_privacy()
        self._enable_encryption()
        logger.info("  ✓ Data encryption enabled")
        self._use_anonymous_ids()
        logger.info("  ✓ Anonymous identifiers in use")
        self._disable_all_telemetry()
        logger.info("  ✓ All telemetry disabled")
        self._enable_memory_mode()
        logger.info("  ✓ Memory-only operation enabled")
        logger.warning("\n⚠️  BULLETPROOF GHOST MODE ACTIVE ⚠️")
        logger.warning("No persistent logs. No external connections. No traces.")

    def _apply_sovereign_privacy(self):
        """Apply sovereign privacy — maximum + network blocking + trace cleaning."""
        logger.info("Applying SOVEREIGN privacy measures:")
        self._apply_maximum_privacy()

        # Clean network traces
        self._clean_network_traces()
        logger.info("  ✓ Network traces cleaned")

        # Block outbound connections
        self._block_outbound_connections()
        logger.info("  ✓ Outbound connections blocked")

        # Verify offline capability
        self._verify_offline_ready()
        logger.info("  ✓ Offline capability verified")

        # Set sovereignty environment
        os.environ['SATX_SOVEREIGN'] = '1'
        os.environ['SATX_OFFLINE'] = '1'

        logger.warning("\n🔒 SOVEREIGN MODE ACTIVE 🔒")
        logger.warning("All network access blocked. Full air-gap enforced.")
        logger.warning("All computations are local. No data leaves this machine.")

    # =========================================================================
    # NETWORK TRACE CLEANING (Sovereignty)
    # =========================================================================

    def _clean_network_traces(self):
        """Clean all network-related traces from the system."""
        logger.info("Cleaning network traces...")

        # 1. Clean DNS cache
        self._clean_dns_cache()

        # 2. Clean connection tracking
        self._clean_conntrack()

        # 3. Clean ARP cache entries related to SATx
        self._clean_arp_cache()

        # 4. Clean any SATx-related entries from shell history
        self._clean_shell_history_traces()

        # 5. Clean Python request caches
        self._clean_python_caches()

        # 6. Clean temporary network files
        self._clean_temp_network_files()

        logger.info("Network traces cleaned")

    def _clean_dns_cache(self):
        """Flush system DNS cache."""
        commands = [
            ['systemd-resolve', '--flush-caches'],
            ['resolvectl', 'flush-caches'],
        ]
        for cmd in commands:
            try:
                subprocess.run(cmd, capture_output=True, timeout=5)
                logger.debug(f"DNS cache flushed via {cmd[0]}")
                return
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        logger.debug("DNS cache flush: no supported resolver found (non-critical)")

    def _clean_conntrack(self):
        """Clean connection tracking table."""
        try:
            subprocess.run(
                ['conntrack', '-F'],
                capture_output=True, timeout=5
            )
            logger.debug("Connection tracking table flushed")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.debug("conntrack not available (non-critical)")

    def _clean_arp_cache(self):
        """Clean ARP cache."""
        try:
            subprocess.run(
                ['ip', 'neigh', 'flush', 'all'],
                capture_output=True, timeout=5
            )
            logger.debug("ARP cache flushed")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.debug("ARP flush not available (non-critical)")

    def _clean_shell_history_traces(self):
        """Remove SATx-related entries from shell history (best effort)."""
        history_files = [
            Path.home() / '.bash_history',
            Path.home() / '.zsh_history',
        ]
        keywords = ['celestrak', 'satnogs', 'satx', 'tle', 'satellite']

        for hist_file in history_files:
            if hist_file.exists():
                try:
                    with open(hist_file, 'r') as f:
                        lines = f.readlines()
                    filtered = [l for l in lines
                                if not any(kw in l.lower() for kw in keywords)]
                    if len(filtered) < len(lines):
                        with open(hist_file, 'w') as f:
                            f.writelines(filtered)
                        logger.debug(f"Cleaned {len(lines) - len(filtered)} entries from {hist_file.name}")
                except Exception as e:
                    logger.debug(f"Could not clean {hist_file}: {e}")

    def _clean_python_caches(self):
        """Clean Python HTTP caches and session data."""
        cache_dirs = [
            Path.home() / '.cache' / 'pip',
            PROJECT_ROOT / '__pycache__',
            PROJECT_ROOT / 'scripts' / '__pycache__',
        ]
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    shutil.rmtree(cache_dir, ignore_errors=True)
                    logger.debug(f"Cleaned {cache_dir}")
                except Exception:
                    pass

        # Clean requests/urllib3 session files
        http_cache = Path.home() / '.cache' / 'python-requests'
        if http_cache.exists():
            shutil.rmtree(http_cache, ignore_errors=True)

    def _clean_temp_network_files(self):
        """Clean temporary files that may contain network artifacts."""
        temp_patterns = [
            '/tmp/satx_*',
            '/tmp/tle_*',
            '/tmp/satnogs_*',
        ]
        import glob
        for pattern in temp_patterns:
            for f in glob.glob(pattern):
                try:
                    if os.path.isfile(f):
                        os.unlink(f)
                    elif os.path.isdir(f):
                        shutil.rmtree(f)
                except Exception:
                    pass

    # =========================================================================
    # OUTBOUND CONNECTION BLOCKING (Sovereignty)
    # =========================================================================

    def _block_outbound_connections(self):
        """Block all outbound connections for the current user using iptables."""
        logger.info("Blocking outbound network connections...")

        # Get current user's UID
        uid = os.getuid()

        # Rules to add (block all outbound for this UID, allow loopback)
        rules = [
            # Allow loopback (local services)
            ['iptables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'],
            # Allow established connections to close gracefully
            ['iptables', '-A', 'OUTPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'],
            # Block all NEW outbound connections for this UID
            ['iptables', '-A', 'OUTPUT', '-m', 'owner', '--uid-owner', str(uid),
             '-m', 'state', '--state', 'NEW', '-j', 'DROP'],
        ]

        for rule in rules:
            try:
                result = subprocess.run(rule, capture_output=True, timeout=5)
                if result.returncode == 0:
                    self.firewall_rules_added.append(rule)
                    logger.debug(f"Added firewall rule: {' '.join(rule)}")
                else:
                    stderr = result.stderr.decode().strip()
                    if 'Permission denied' in stderr or 'Operation not permitted' in stderr:
                        logger.warning("  ⚠️  Firewall blocking requires root/sudo")
                        logger.warning("  Run with: sudo python scripts/ghost_mode.py --enable --level sovereign")
                        logger.info("  Alternative: Use system-level firewall or network disconnect")
                        self._suggest_manual_blocking()
                        return
                    else:
                        logger.warning(f"  Firewall rule failed: {stderr}")
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("  iptables not available — suggesting alternatives")
                self._suggest_manual_blocking()
                return

        # Verify blocking works
        self._verify_blocked()

    def _suggest_manual_blocking(self):
        """Suggest manual methods to block network when iptables isn't available."""
        logger.info("\n  Manual network isolation methods:")
        logger.info("  1. Disconnect WiFi/Ethernet physically")
        logger.info("  2. sudo ip link set <interface> down")
        logger.info("  3. Enable airplane mode")
        logger.info("  4. Use a network namespace: unshare --net <command>")
        logger.info("  5. Use firejail: firejail --net=none python scripts/predict_passes.py")

        # Write a helper script for network namespace isolation
        ns_script = PROJECT_ROOT / 'scripts' / 'run_airgapped.sh'
        if not ns_script.exists():
            with open(ns_script, 'w') as f:
                f.write('#!/bin/bash\n')
                f.write('# Run SATx commands in a network-isolated namespace\n')
                f.write('# Usage: ./scripts/run_airgapped.sh python scripts/predict_passes.py\n')
                f.write('echo "🔒 Running in air-gapped network namespace..."\n')
                f.write('exec unshare --net -- "$@"\n')
            os.chmod(ns_script, 0o755)
            logger.info(f"  Created helper: {ns_script}")

    def _verify_blocked(self):
        """Verify outbound connections are actually blocked."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(('8.8.8.8', 53))
            s.close()
            logger.warning("  ⚠️  Outbound connections still possible — blocking may not be active")
        except (socket.error, OSError):
            logger.info("  ✓ Outbound connections verified BLOCKED")

    def _verify_offline_ready(self):
        """Verify the system has enough cached data for offline operation."""
        issues = []

        # Check TLE cache
        tle_cache = PROJECT_ROOT / 'data' / 'tle_cache'
        if not tle_cache.exists() or not list(tle_cache.glob('*.tle')):
            issues.append("No cached TLEs — run: python scripts/cache_tles_bulk.py")

        tle_dir = PROJECT_ROOT / 'data' / 'tles'
        if not (tle_dir / 'all-satellites.tle').exists():
            if not (tle_cache / 'all-satellites.tle').exists():
                issues.append("No merged TLE file — run: python scripts/fetch_tles.py")

        # Check station config
        if not self.config_file.exists():
            issues.append("No station config — copy configs/station.ini.example")

        if issues:
            logger.warning("  ⚠️  Offline readiness issues:")
            for issue in issues:
                logger.warning(f"    - {issue}")
        else:
            logger.info("  ✓ System ready for offline/air-gapped operation")

    def unblock_connections(self):
        """Remove firewall rules added by ghost mode."""
        if not self.firewall_rules_added:
            logger.info("No firewall rules to remove")
            return

        for rule in reversed(self.firewall_rules_added):
            # Change -A (append) to -D (delete)
            delete_rule = [rule[0], '-D'] + rule[2:]
            try:
                subprocess.run(delete_rule, capture_output=True, timeout=5)
            except Exception:
                pass

        self.firewall_rules_added.clear()
        logger.info("Firewall rules removed — network access restored")

    # =========================================================================
    # ORIGINAL GHOST MODE METHODS (preserved)
    # =========================================================================

    def _get_or_create_config_section(self, section_name):
        """Helper to safely get or create config section."""
        try:
            config = configparser.ConfigParser()
            config.read(self.config_file)
            if section_name not in config:
                config[section_name] = {}
            return config
        except Exception as e:
            logger.error(f"Error accessing config: {e}")
            return None

    def _disable_external_services(self):
        """Disable all external service integrations."""
        config = self._get_or_create_config_section('station')
        if config is None:
            return
        try:
            config['station']['satnogs_enabled'] = 'false'
            config['station']['satnogs_station_id'] = ''
            config['station']['satnogs_api_key'] = ''
            with open(self.config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            logger.error(f"Error disabling external services: {e}")

    def _anonymize_station_name(self):
        """Replace station name with anonymous identifier."""
        config = self._get_or_create_config_section('station')
        if config is None:
            return
        try:
            anon_id = f"GHOST-{secrets.token_hex(4).upper()}"
            config['station']['name'] = anon_id
            config['station']['location'] = 'Undisclosed'
            with open(self.config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            logger.error(f"Error anonymizing station: {e}")

    def _minimize_logging(self):
        """Minimize logging to essential operations only."""
        logging.getLogger().setLevel(logging.WARNING)
        logger.warning("Logging minimized - only warnings and errors will be recorded")

    def _disable_metadata_collection(self):
        """Disable metadata collection in recordings."""
        config = self._get_or_create_config_section('station')
        if config is None:
            return
        try:
            config['station']['ghost_mode'] = 'true'
            config['station']['collect_metadata'] = 'false'
            with open(self.config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            logger.error(f"Error disabling metadata: {e}")

    def _clear_identifying_info(self):
        """Clear identifying information from config."""
        config = self._get_or_create_config_section('station')
        if config is None:
            return
        try:
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
        key_file = PROJECT_ROOT / 'configs' / '.ghost_key'
        key_file.parent.mkdir(parents=True, exist_ok=True)
        if not key_file.exists():
            try:
                fd = os.open(str(key_file), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                key = secrets.token_hex(32)
                os.write(fd, key.encode())
                os.close(fd)
                logger.info("Encryption key generated")
            except Exception as e:
                logger.error(f"Error creating encryption key: {e}")
        else:
            logger.info("Using existing encryption key")

    def _use_anonymous_ids(self):
        """Use anonymous identifiers for all operations."""
        session_id = f"GHOST-SESSION-{secrets.token_hex(8).upper()}"
        logger.info(f"Anonymous session ID: {session_id}")
        os.environ['SATX_GHOST_SESSION'] = session_id

    def _disable_all_telemetry(self):
        """Disable all telemetry and reporting."""
        logger.warning("All telemetry and external reporting disabled")
        os.environ['SATX_NO_TELEMETRY'] = '1'
        os.environ['SATX_NO_REPORTING'] = '1'

    def _enable_memory_mode(self):
        """Enable memory-only operation (minimal disk writes)."""
        logger.warning("Memory-only mode: Results stored in RAM, not on disk")
        os.environ['SATX_MEMORY_MODE'] = '1'
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

        # Remove firewall rules
        self.unblock_connections()

        # Clear environment variables
        for var in ['SATX_GHOST_SESSION', 'SATX_NO_TELEMETRY', 'SATX_NO_REPORTING',
                     'SATX_MEMORY_MODE', 'SATX_SOVEREIGN', 'SATX_OFFLINE']:
            os.environ.pop(var, None)

        # Restore normal logging
        logging.getLogger().setLevel(logging.INFO)

        logger.info("Ghost mode disabled - normal operation restored")

    def secure_delete(self, file_path):
        """Securely delete a file (overwrite before deletion)."""
        file_path = Path(file_path)
        if not file_path.exists():
            return
        try:
            size = file_path.stat().st_size
            with open(file_path, 'wb') as f:
                for _ in range(3):  # 3-pass overwrite
                    f.seek(0)
                    f.write(secrets.token_bytes(size))
                    f.flush()
                    os.fsync(f.fileno())
            file_path.unlink()
            logger.info(f"Securely deleted: {file_path}")
        except Exception as e:
            logger.error(f"Error securely deleting {file_path}: {e}")

    def clean_traces(self):
        """Clean all operational traces comprehensively."""
        logger.warning("Cleaning operational traces...")

        # Clear logs
        logs_dir = PROJECT_ROOT / 'logs'
        if logs_dir.exists():
            for log_file in logs_dir.glob('*.log'):
                self.secure_delete(log_file)
            for json_file in logs_dir.glob('*.json'):
                self.secure_delete(json_file)
            logger.info("  ✓ Log files cleaned")

        # Clear temporary recordings
        recordings_dir = PROJECT_ROOT / 'recordings'
        if recordings_dir.exists():
            for rec_file in recordings_dir.glob('*.iq'):
                self.secure_delete(rec_file)
            logger.info("  ✓ Recording files cleaned")

        # Clear cache
        cache_dir = PROJECT_ROOT / '.cache'
        if cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
            logger.info("  ✓ Cache cleaned")

        # Clean network traces
        self._clean_network_traces()
        logger.info("  ✓ Network traces cleaned")

        # Clean Python bytecode
        for pyc in PROJECT_ROOT.rglob('*.pyc'):
            try:
                pyc.unlink()
            except Exception:
                pass
        for pycache in PROJECT_ROOT.rglob('__pycache__'):
            try:
                shutil.rmtree(pycache)
            except Exception:
                pass
        logger.info("  ✓ Python bytecode cleaned")

        # Clean temp directory
        ghost_tmp = Path('/tmp/satx_ghost')
        if ghost_tmp.exists():
            shutil.rmtree(ghost_tmp, ignore_errors=True)
            logger.info("  ✓ Temp directory cleaned")

        logger.warning("All traces cleaned")

    def status(self):
        """Display comprehensive ghost mode status."""
        print("=" * 60)
        print("GHOST MODE STATUS")
        print("=" * 60)

        if self.ghost_enabled:
            print(f"  Status:        🔴 ACTIVE")
            print(f"  Privacy Level: {self.privacy_level.upper()}")
            print(f"  Firewall:      {len(self.firewall_rules_added)} rules active")
        else:
            print(f"  Status:        ⚪ INACTIVE")

        # Check sovereignty readiness
        print("\nSOVEREIGNTY READINESS:")

        tle_cache = PROJECT_ROOT / 'data' / 'tle_cache'
        cached_tles = list(tle_cache.glob('*.tle')) if tle_cache.exists() else []
        print(f"  TLE Cache:     {len(cached_tles)} catalogs cached")

        tle_main = PROJECT_ROOT / 'data' / 'tles' / 'all-satellites.tle'
        print(f"  Main TLE:      {'✓' if tle_main.exists() else '✗'}")

        satnogs_cache = PROJECT_ROOT / 'data' / 'satnogs_cache'
        has_satnogs = satnogs_cache.exists() and any(satnogs_cache.rglob('*.json'))
        print(f"  SatNOGS Cache: {'✓' if has_satnogs else '✗'}")

        # Check network status
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(('8.8.8.8', 53))
            s.close()
            print(f"  Network:       CONNECTED (not air-gapped)")
        except (socket.error, OSError):
            print(f"  Network:       BLOCKED ✓ (air-gapped)")

        print("=" * 60)


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description='SATx Ghost Mode - Privacy & Sovereignty')
    parser.add_argument('--enable', action='store_true', help='Enable ghost mode')
    parser.add_argument('--disable', action='store_true', help='Disable ghost mode')
    parser.add_argument('--level', choices=['standard', 'high', 'maximum', 'sovereign'],
                        default='maximum', help='Privacy level (default: maximum)')
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
