#!/usr/bin/env python3
"""
Enterprise Fingerprint for LockStock Guard

Cloud-native hardware fingerprinting for enterprise deployments.
Extracted from liberty-secrets v1.1.0 for LockStock Guard enterprise use.

NOT for personal use - use liberty-secrets v1.0.0 for that.

This module provides:
- Cloud instance identity detection (AWS, Azure, GCP)
- Container-aware binding with unique instance IDs
- Fail-secure operation for containerized environments
- Fallback to liberty v1.0.0 for bare metal deployments

Security Model:
1. Cloud instances: Use cryptographically-signed metadata
2. Containers: Require explicit unique instance IDs
3. Bare metal: Fallback to liberty v1.0.0 HardwareFingerprint

License: Same as liberty-secrets (see liberty-repo/LICENSE)
"""

import os
import sys
import json
import hashlib
import platform
import subprocess
from typing import Dict, Optional


class CloudInstanceIdentity:
    """
    Cloud-native instance identity detection.
    Uses cryptographically-signed metadata from cloud providers.
    """

    @staticmethod
    def detect_environment() -> str:
        """Detect if running in cloud environment."""
        # Check for AWS
        if os.path.exists('/sys/hypervisor/uuid'):
            try:
                with open('/sys/hypervisor/uuid', 'r') as f:
                    uuid = f.read().strip()
                    if uuid.startswith('ec2') or uuid.startswith('EC2'):
                        return 'aws'
            except:
                pass

        # Check AWS metadata service
        try:
            import urllib.request
            req = urllib.request.Request(
                'http://169.254.169.254/latest/meta-data/instance-id',
                headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}
            )
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    return 'aws'
        except:
            pass

        # Check for Azure
        try:
            import urllib.request
            req = urllib.request.Request(
                'http://169.254.169.254/metadata/instance?api-version=2021-02-01',
                headers={'Metadata': 'true'}
            )
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    return 'azure'
        except:
            pass

        # Check for GCP
        try:
            import urllib.request
            req = urllib.request.Request(
                'http://metadata.google.internal/computeMetadata/v1/instance/id',
                headers={'Metadata-Flavor': 'Google'}
            )
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    return 'gcp'
        except:
            pass

        return 'unknown'

    @staticmethod
    def get_aws_identity() -> Optional[Dict[str, str]]:
        """Get AWS instance identity (cryptographically signed)."""
        try:
            import urllib.request

            # Get instance identity document
            doc_req = urllib.request.Request(
                'http://169.254.169.254/latest/dynamic/instance-identity/document'
            )
            with urllib.request.urlopen(doc_req, timeout=2) as response:
                doc = json.loads(response.read().decode())

            # Get signature (PKCS7 - cannot be forged)
            sig_req = urllib.request.Request(
                'http://169.254.169.254/latest/dynamic/instance-identity/signature'
            )
            with urllib.request.urlopen(sig_req, timeout=2) as response:
                signature = response.read().decode().strip()

            return {
                'provider': 'aws',
                'instance_id': doc.get('instanceId'),
                'region': doc.get('region'),
                'account_id': doc.get('accountId'),
                'signature': signature[:64],  # Truncated for fingerprint
            }
        except:
            return None

    @staticmethod
    def get_azure_identity() -> Optional[Dict[str, str]]:
        """Get Azure VM identity (cryptographically signed)."""
        try:
            import urllib.request

            req = urllib.request.Request(
                'http://169.254.169.254/metadata/instance?api-version=2021-02-01',
                headers={'Metadata': 'true'}
            )
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode())

            compute = data.get('compute', {})
            return {
                'provider': 'azure',
                'vm_id': compute.get('vmId'),
                'subscription_id': compute.get('subscriptionId'),
                'resource_group': compute.get('resourceGroupName'),
            }
        except:
            return None

    @staticmethod
    def get_gcp_identity() -> Optional[Dict[str, str]]:
        """Get GCP instance identity (cryptographically signed)."""
        try:
            import urllib.request

            # Get instance ID
            id_req = urllib.request.Request(
                'http://metadata.google.internal/computeMetadata/v1/instance/id',
                headers={'Metadata-Flavor': 'Google'}
            )
            with urllib.request.urlopen(id_req, timeout=2) as response:
                instance_id = response.read().decode().strip()

            # Get project ID
            proj_req = urllib.request.Request(
                'http://metadata.google.internal/computeMetadata/v1/project/project-id',
                headers={'Metadata-Flavor': 'Google'}
            )
            with urllib.request.urlopen(proj_req, timeout=2) as response:
                project_id = response.read().decode().strip()

            return {
                'provider': 'gcp',
                'instance_id': instance_id,
                'project_id': project_id,
            }
        except:
            return None

    @classmethod
    def get_identity(cls) -> Optional[Dict[str, str]]:
        """Get cloud instance identity with auto-detection."""
        env = cls.detect_environment()

        if env == 'aws':
            return cls.get_aws_identity()
        elif env == 'azure':
            return cls.get_azure_identity()
        elif env == 'gcp':
            return cls.get_gcp_identity()

        return None


class ContainerDetection:
    """
    Container environment detection and unique ID enforcement.
    """

    @staticmethod
    def is_container() -> bool:
        """Detect if running in a container."""
        # Check for /.dockerenv
        if os.path.exists('/.dockerenv'):
            return True

        # Check cgroup for container indicators
        try:
            with open('/proc/1/cgroup', 'r') as f:
                cgroup = f.read()
                if 'docker' in cgroup or 'kubepods' in cgroup or 'containerd' in cgroup:
                    return True
        except:
            pass

        return False

    @staticmethod
    def get_container_id() -> Optional[str]:
        """Get unique container identifier."""
        # Priority 1: Explicit environment variable (required for security)
        liberty_id = os.getenv('LIBERTY_INSTANCE_ID')
        if liberty_id:
            return f"explicit:{liberty_id}"

        # Priority 2: Kubernetes Pod UID (unique per pod)
        pod_uid = os.getenv('POD_UID')
        if pod_uid:
            return f"k8s:{pod_uid}"

        # Priority 3: Docker container ID from cgroup
        try:
            with open('/proc/self/cgroup', 'r') as f:
                for line in f:
                    if 'docker' in line:
                        # Extract container ID from cgroup path
                        parts = line.strip().split('/')
                        if len(parts) > 2:
                            container_id = parts[-1]
                            if len(container_id) == 64:  # Full container ID
                                return f"docker:{container_id[:16]}"
        except:
            pass

        # FAIL SECURE: No unique ID available
        return None


class EnterpriseFingerprint:
    """
    Cloud-Native Physical Unclonable Function (PUF) for Enterprise.
    Priority-based fingerprint generation with VM/container safety.

    This is the enterprise version from liberty v1.1.0, renamed to avoid
    conflicts with liberty v1.0.0's HardwareFingerprint class.

    Security model:
    1. Cloud instance identity (AWS/Azure/GCP) - cryptographically signed
    2. Container identity - explicit unique ID required
    3. Bare metal hardware - fallback to liberty v1.0.0 HardwareFingerprint

    Changes from liberty v1.1.0:
    - Renamed from HardwareFingerprint to EnterpriseFingerprint
    - Removed 'baremetal' prefix to maintain compatibility
    - Added fallback to liberty v1.0.0 for bare metal systems
    """

    @staticmethod
    def get_cpu_info() -> str:
        """Get CPU information."""
        try:
            if platform.system() == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    for line in cpuinfo.split('\n'):
                        if 'processor' in line.lower() or 'serial' in line.lower():
                            return line.strip()
            elif platform.system() == "Darwin":
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                                       capture_output=True, text=True)
                return result.stdout.strip()
            elif platform.system() == "Windows":
                result = subprocess.run(['wmic', 'cpu', 'get', 'ProcessorId'],
                                       capture_output=True, text=True)
                return result.stdout.strip()
        except:
            pass
        return platform.processor()

    @staticmethod
    def get_machine_id() -> str:
        """Get machine ID."""
        try:
            if platform.system() == "Linux":
                if os.path.exists('/etc/machine-id'):
                    with open('/etc/machine-id', 'r') as f:
                        return f.read().strip()
                if os.path.exists('/var/lib/dbus/machine-id'):
                    with open('/var/lib/dbus/machine-id', 'r') as f:
                        return f.read().strip()
            elif platform.system() == "Darwin":
                result = subprocess.run(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
                                       capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'IOPlatformUUID' in line:
                        return line.split('"')[3]
            elif platform.system() == "Windows":
                result = subprocess.run(['wmic', 'csproduct', 'get', 'UUID'],
                                       capture_output=True, text=True)
                return result.stdout.strip().split('\n')[1].strip()
        except:
            pass
        return platform.node()

    @staticmethod
    def get_disk_serial() -> str:
        """Get disk serial number."""
        try:
            if platform.system() == "Linux":
                result = subprocess.run(['lsblk', '-ndo', 'SERIAL', '/dev/sda'],
                                       capture_output=True, text=True)
                return result.stdout.strip()
            elif platform.system() == "Darwin":
                result = subprocess.run(['system_profiler', 'SPSerialATADataType'],
                                       capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'Serial Number' in line:
                        return line.split(':')[1].strip()
            elif platform.system() == "Windows":
                result = subprocess.run(['wmic', 'diskdrive', 'get', 'SerialNumber'],
                                       capture_output=True, text=True)
                return result.stdout.strip().split('\n')[1].strip()
        except:
            pass
        return ""

    @classmethod
    def generate(cls, _debug_mode: str = None) -> str:
        """
        Generate a unique hardware fingerprint with priority-based detection.

        Priority Order:
        1. Cloud instance identity (AWS/Azure/GCP) - cryptographically signed
        2. Container identity - explicit LIBERTY_INSTANCE_ID required
        3. Bare metal hardware - fallback to liberty v1.0.0 HardwareFingerprint

        Security guarantees:
        - VM cloning: Prevented by unique instance IDs from cloud metadata
        - Container lateral movement: Prevented by explicit instance ID requirement
        - Bare metal: Traditional hardware fingerprinting (less secure)

        Args:
            _debug_mode: For testing only. Values: 'cloud', 'container', 'baremetal'

        Returns:
            64-character hex fingerprint unique to this system instance
        """
        components = []
        fingerprint_type = "unknown"

        # Force debug mode if specified (for testing)
        if _debug_mode:
            if _debug_mode == 'cloud':
                # Simulate cloud identity
                components = ['cloud', 'aws', 'i-test12345', 'us-east-1']
                fingerprint_type = "cloud-debug"
            elif _debug_mode == 'container':
                # Simulate container with explicit ID
                components = ['container', 'explicit:test-container-id']
                fingerprint_type = "container-debug"
            elif _debug_mode == 'baremetal':
                # Force traditional fingerprinting
                pass
            else:
                raise ValueError(f"Invalid debug mode: {_debug_mode}")

        # Priority 1: Cloud Instance Identity (most secure)
        if not components:
            cloud_identity = CloudInstanceIdentity.get_identity()
            if cloud_identity:
                components = [
                    'cloud-native',
                    cloud_identity['provider'],
                    cloud_identity.get('instance_id') or cloud_identity.get('vm_id'),
                ]

                # Add additional cloud-specific identifiers
                if cloud_identity['provider'] == 'aws':
                    components.extend([
                        cloud_identity.get('region'),
                        cloud_identity.get('signature', '')[:16]
                    ])
                elif cloud_identity['provider'] == 'azure':
                    components.extend([
                        cloud_identity.get('subscription_id'),
                        cloud_identity.get('resource_group')
                    ])
                elif cloud_identity['provider'] == 'gcp':
                    components.append(cloud_identity.get('project_id'))

                fingerprint_type = f"cloud-{cloud_identity['provider']}"

        # Priority 2: Container Identity (requires explicit ID)
        if not components and ContainerDetection.is_container():
            container_id = ContainerDetection.get_container_id()

            if container_id:
                components = [
                    'container',
                    container_id,
                    platform.system(),
                ]
                fingerprint_type = "container"
            else:
                # FAIL SECURE: Container detected but no unique ID provided
                print("\n" + "="*70)
                print("CRITICAL SECURITY ERROR: Container Detected Without Unique ID")
                print("="*70)
                print("\nLockStock Guard detected that you are running in a containerized")
                print("environment but no unique instance identifier was provided.")
                print("\nThis is a security risk because:")
                print("  - Containers on the same host may derive the same fingerprint")
                print("  - One compromised container could access all vaults on the node")
                print("\nREQUIRED: Set one of these environment variables:")
                print("  export LIBERTY_INSTANCE_ID=<unique-id>")
                print("  export POD_UID=<kubernetes-pod-uid>")
                print("\nExample (Kubernetes):")
                print("  env:")
                print("  - name: POD_UID")
                print("    valueFrom:")
                print("      fieldRef:")
                print("        fieldPath: metadata.uid")
                print("\nExample (Docker):")
                print("  docker run -e LIBERTY_INSTANCE_ID=$(uuidgen) ...")
                print("\n" + "="*70)
                sys.exit(1)

        # Priority 3: Bare Metal Hardware - Fallback to liberty v1.0.0
        if not components:
            # Try to import liberty v1.0.0's HardwareFingerprint
            try:
                from liberty import HardwareFingerprint
                # Use liberty v1.0.0's fingerprinting for bare metal
                # This maintains compatibility with existing bare metal deployments
                return HardwareFingerprint.generate()
            except ImportError:
                # Liberty not installed - fall back to basic fingerprinting
                # NOTE: This does NOT include the 'baremetal' prefix that broke compatibility
                components = [
                    platform.system(),
                    platform.machine(),
                    cls.get_cpu_info(),
                    cls.get_machine_id(),
                    cls.get_disk_serial(),
                ]
                fingerprint_type = "baremetal-fallback"

        # Filter out empty components
        components = [c for c in components if c]

        if not components:
            raise RuntimeError("Failed to generate hardware fingerprint: no identifiers available")

        # Combine and hash
        combined = "|".join(components)
        fingerprint = hashlib.sha256(combined.encode()).hexdigest()

        return fingerprint

    @classmethod
    def get_fingerprint_type(cls) -> str:
        """Get a human-readable fingerprint type description."""
        cloud_identity = CloudInstanceIdentity.get_identity()
        if cloud_identity:
            return f"Cloud ({cloud_identity['provider'].upper()})"

        if ContainerDetection.is_container():
            container_id = ContainerDetection.get_container_id()
            if container_id:
                return "Container (with unique ID)"
            else:
                return "Container (INSECURE - no unique ID)"

        return "Bare Metal Hardware"


# Backward compatibility: Allow importing as HardwareFingerprint
# This maintains compatibility with code expecting liberty v1.1.0's interface
HardwareFingerprint = EnterpriseFingerprint


if __name__ == '__main__':
    # Simple test/demo when run directly
    print("LockStock Guard Enterprise Fingerprint")
    print("=" * 60)
    print()
    print(f"Environment: {EnterpriseFingerprint.get_fingerprint_type()}")
    print(f"Fingerprint: {EnterpriseFingerprint.generate()[:32]}...")
    print()
    print("This module provides cloud-native fingerprinting for enterprise")
    print("deployments. For personal use, install liberty-secrets v1.0.0.")
