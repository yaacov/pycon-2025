## What is MTV?

Migration Toolkit for Virtualization (MTV) is the downstream product of the open-source [Forklift project](https://github.com/kubev2v/forklift). It provides a comprehensive solution for migrating virtual machines from traditional virtualization platforms to Kubernetes/OpenShift using KubeVirt technology.

### Key Benefits

- **Multi-Platform Support**: Migrate VMs from vSphere, oVirt/RHV, OpenStack, OpenShift, and OVA files
- **Flexible Migration Options**: Support for cold, warm, and live migrations (live migration only for OCP-to-OCP) to minimize downtime
- **Resource Mapping**: Intelligent mapping of networks and storage between source and target environments
- **Inventory Discovery**: Powerful query capabilities to discover and filter source VMs
- **Automation-Ready**: Command-line interface perfect for scripting and automation
- **Production-Tested**: Enterprise-grade solution used in production environments

### Architecture Overview

MTV operates as a Kubernetes operator that orchestrates the migration process:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Source        │    │      MTV        │    │   Target        │
│ (vSphere/oVirt/ │ -> │   Controller    │ -> │  (Kubernetes/   │
│  OpenStack/OVA) │    │   + kubectl-mtv │    │   OpenShift)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Key Concepts

### Providers

**Providers** represent source and target virtualization platforms. MTV supports various provider types:

- **Source Providers**: vSphere, oVirt, OpenStack, OpenShift, OVA
- **Target Providers**: OpenShift/Kubernetes (with KubeVirt)

Each provider contains:
- Connection details (URLs, credentials, certificates)
- Performance optimizations (VDDK for vSphere)
- Inventory of available resources

### Mappings

**Mappings** define how source resources correspond to target resources:

#### Network Mappings
Map source networks to target networks:
- **Pod Network**: Default Kubernetes networking (`default`)
- **Multus Networks**: Custom NetworkAttachmentDefinitions (`namespace/network-name`)
- **Ignored Networks**: Networks that don't need mapping (`ignored`)

#### Storage Mappings
Map source storage to Kubernetes StorageClasses:
- **Performance Tiers**: Map datastores to appropriate storage classes
- **Access Modes**: Configure ReadWriteOnce, ReadWriteMany, etc.
- **Volume Modes**: Block vs Filesystem storage

### Migration Plans

**Migration Plans** orchestrate the entire migration process:
- Define which VMs to migrate
- Reference network and storage mappings
- Configure migration behavior (warm, cold, live)
- Set target specifications (namespace, labels, affinity)
- Include custom hooks for automation

### Inventory System

The **Inventory System** provides real-time discovery of source resources:
- VM details (CPU, memory, disks, networks)
- Infrastructure components (hosts, clusters, datastores)
- Powerful query language for filtering and selection

## Supported Source Platforms

### VMware vSphere

**Requirements:**
- vCenter Server or ESXi host access
- Valid credentials with VM management permissions
- Optional: VDDK container for optimized disk transfers

**Features:**
- Direct ESXi host connections for performance
- VDDK optimization for large disk migrations
- Static IP preservation
- Guest agent integration

**Example Configuration:**
```bash
kubectl mtv create provider vsphere-prod --type vsphere \
  --url https://vcenter.example.com/sdk \
  --username administrator@vsphere.local \
  --password $PASSWORD \
  --vddk-init-image quay.io/org/vddk:8.0.1 \
  --cacert @vcenter-ca.crt
```

### Red Hat Virtualization (oVirt/RHV)

**Requirements:**
- oVirt Engine API access
- Valid user credentials
- CA certificate for secure connections

**Features:**
- Cluster CPU model preservation
- Storage domain mapping
- Network profile support

**Example Configuration:**
```bash
kubectl mtv create provider ovirt-prod --type ovirt \
  --url https://engine.example.com/ovirt-engine/api \
  --username admin@internal \
  --password $PASSWORD \
  --cacert @ovirt-ca.crt
```

### OpenStack

**Requirements:**
- Keystone authentication endpoint
- Valid project/domain credentials
- Regional configuration

**Features:**
- Multi-tenant support
- Flavor and image discovery
- Network and storage service integration

**Example Configuration:**
```bash
kubectl mtv create provider openstack-prod --type openstack \
  --url https://keystone.example.com:5000/v3 \
  --username admin \
  --password $PASSWORD \
  --provider-domain-name default \
  --provider-project-name admin \
  --provider-region-name RegionOne
```

### OpenShift Virtualization

**Requirements:**
- OpenShift cluster access
- KubeVirt/OpenShift Virtualization installed
- Appropriate RBAC permissions

**Features:**
- Cluster-to-cluster migrations
- Namespace-based organization
- DataVolume and PVC integration
- **Live migration support** (only when both source and target are OpenShift with supported versions)

### OVA Files

**Requirements:**
- Accessible file storage (NFS, HTTP, HTTPS)
- Valid OVA/OVF file format

**Features:**
- Direct file-based migration
- No running infrastructure required
- Batch processing capabilities

## Core Components

### MTV Controller

The **MTV Controller** is the core orchestration engine:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: forklift-controller
spec:
  containers:
  - name: main
    # Main controller logic
  - name: inventory
    # Inventory service
```

**Responsibilities:**
- Provider connectivity management
- Migration plan execution
- Resource state reconciliation
- Inventory data collection

### kubectl-mtv CLI

The **kubectl-mtv CLI** provides command-line access to MTV functionality:

**Tool Categories:**
- **Provider Management**: Create, update, delete providers
- **Inventory Discovery**: Query and explore source resources
- **Mapping Management**: Configure network and storage mappings
- **Migration Planning**: Create and manage migration plans
- **Lifecycle Control**: Start, monitor, and control migrations

### Inventory Service

The **Inventory Service** provides real-time resource discovery:

**Capabilities:**
- Real-time resource enumeration
- Powerful SQL-like query language (TSL)
- Resource relationship mapping
- Change detection and updates

**Query Examples:**
```bash
# Find Linux VMs with >4GB memory
kubectl mtv get inventory vms vsphere -q "WHERE guestOS ~= '.*[Ll]inux.*' AND memoryMB > 4096"

# Find VMs with multiple disks in production
kubectl mtv get inventory vms vsphere -q "WHERE name ~= 'prod-.*' AND len(disks) > 1"

# Get resource counts by cluster
kubectl mtv get inventory vms vsphere -q "SELECT cluster, count(*) GROUP BY cluster"
```

## Migration Types

MTV supports multiple migration strategies to balance downtime and complexity:

**Important Note**: Live migration is only available for OpenShift to OpenShift migrations on supported OpenShift Virtualization versions. For migrations from vSphere, oVirt, OpenStack, or OVA sources, only cold, warm, and conversion-only migration types are available.

### Cold Migration

**Description**: Traditional migration with VM shutdown during the process.

**Characteristics:**
- Complete VM shutdown on source
- Full disk and configuration transfer
- VM startup on target
- Highest data consistency guarantee

**Best For:**
- Non-critical workloads
- Maintenance windows available
- Maximum reliability required

**Downtime**: Complete duration of migration process

**Example:**
```bash
kubectl mtv create plan cold-migration \
  --source vsphere-prod \
  --vms app-server-01,app-server-02 \
  --migration-type cold
```

### Warm Migration

**Description**: Multi-phase migration with initial sync while VM runs, followed by brief cutover.

**Characteristics:**
- Initial bulk data transfer while VM runs
- Incremental sync of changes
- Brief cutover period for final sync
- Scheduled cutover capability

**Best For:**
- Production workloads with downtime constraints
- Large VMs with significant data
- Scheduled maintenance windows

**Downtime**: Minutes (final cutover only)

**Example:**
```bash
# Create warm migration plan
kubectl mtv create plan warm-migration \
  --source vsphere-prod \
  --vms database-vm \
  --migration-type warm

# Start initial sync
kubectl mtv start plan warm-migration

# Schedule cutover for maintenance window
kubectl mtv cutover plan warm-migration --cutover "2024-01-15T02:00:00Z"
```

### Live Migration

**Description**: Minimal-downtime migration with advanced VM state transfer.

**Important Limitation**: Live migration is **only available for OpenShift to OpenShift (OCP to OCP) migrations** on supported OpenShift Virtualization versions. It cannot be used when migrating from other platforms like vSphere, oVirt, or OpenStack.

**Characteristics:**
- Continuous VM operation during migration
- Memory and CPU state preservation
- Minimal service interruption
- Advanced synchronization requirements
- **Source and target must both be OpenShift with compatible versions**

**Best For:**
- Critical, always-on services running on OpenShift
- VMs with strict uptime requirements in OCP-to-OCP scenarios
- OpenShift cluster migrations or upgrades

**Downtime**: Seconds (state transfer only)

**Requirements:**
- Source provider: OpenShift/Kubernetes with OpenShift Virtualization
- Target provider: OpenShift/Kubernetes with compatible OpenShift Virtualization version
- Network connectivity between source and target clusters

**Example (OCP to OCP only):**
```bash
# Only works with OpenShift source providers
kubectl mtv create plan live-migration \
  --source openshift-source-cluster \
  --target openshift-target-cluster \
  --vms critical-service \
  --migration-type live
```

### Conversion-Only Migration

**Description**: Guest OS conversion without disk data transfer.

**Characteristics:**
- Only performs guest OS adaptation
- No storage migration occurs
- Existing storage remains in place
- Network configuration only

**Best For:**
- VMs with external storage systems
- Container-based workloads
- Hybrid cloud scenarios

**Example:**
```bash
kubectl mtv create plan conversion-only \
  --source vsphere-prod \
  --vms containerized-app \
  --migration-type conversion \
  --network-pairs "VM Network:default"
  # Note: No storage mapping needed for conversion-only
```

## Essential Migration Workflow

This section provides a complete, step-by-step migration workflow from setup to completion.

### Phase 1: Environment Preparation

#### 1.1 Verify MTV Installation

```bash
# Check MTV operator status
kubectl mtv version

# Verify controller pods
kubectl get pods -n forklift-operator
```

#### 1.2 Create Target Provider

```bash
# Register Kubernetes/OpenShift as target
kubectl mtv create provider host --type openshift
```

#### 1.3 Create Source Provider

Choose based on your source platform:

**vSphere Example:**
```bash
kubectl mtv create provider vsphere-prod --type vsphere \
  --url https://vcenter.example.com/sdk \
  --username administrator@vsphere.local \
  --password $PASSWORD \
  --vddk-init-image quay.io/org/vddk:8.0.1 \
  --cacert @vcenter-ca.crt
```

**oVirt Example:**
```bash
kubectl mtv create provider ovirt-prod --type ovirt \
  --url https://engine.example.com/ovirt-engine/api \
  --username admin@internal \
  --password $PASSWORD \
  --cacert @ovirt-ca.crt
```

### Phase 2: Discovery and Planning

#### 2.1 Explore Source Inventory

```bash
# List all VMs
kubectl mtv get inventory vms vsphere-prod

# Find specific VMs with query
kubectl mtv get inventory vms vsphere-prod -q "WHERE name ~= 'web-.*' AND powerState = 'poweredOn'"

# Get VM details in planvms format
kubectl mtv get inventory vms vsphere-prod -o planvms > available-vms.yaml
```

#### 2.2 Analyze Network and Storage Requirements

```bash
# Discover available networks
kubectl mtv get inventory networks vsphere-prod

# Discover storage resources
kubectl mtv get inventory storage vsphere-prod

# List target storage classes
kubectl get storageclass
```

### Phase 3: Mapping Configuration

#### 3.1 Create Network Mappings

```bash
# Basic network mapping
kubectl mtv create mapping network prod-networks \
  --source vsphere-prod \
  --target host \
  --network-pairs "VM Network:default,Production VLAN:prod/prod-net,DMZ Network:security/dmz-net"
```

#### 3.2 Create Storage Mappings

```bash
# Performance-tiered storage mapping
kubectl mtv create mapping storage prod-storage \
  --source vsphere-prod \
  --target host \
  --storage-pairs "SSD-Datastore:fast-ssd,SATA-Datastore:standard,Archive-Storage:slow-archive"
```

### Phase 4: Migration Plan Creation

#### 4.1 Create Migration Plan

```bash
# Comprehensive migration plan
kubectl mtv create plan web-tier-migration \
  --source vsphere-prod \
  --target-namespace production \
  --network-mapping prod-networks \
  --storage-mapping prod-storage \
  --vms web-server-01,web-server-02,web-server-03 \
  --migration-type warm \
  --target-power-state on \
  --description "Production web tier migration"
```

#### 4.2 Customize Individual VMs (Optional)

```bash
# Customize specific VM settings
kubectl mtv patch planvm web-tier-migration web-server-01 \
  --target-name prod-web-01 \
  --pvc-name-template "prod-{{.VmName}}-disk-{{.DiskIndex}}" \
  --target-power-state on
```

### Phase 5: Migration Execution

#### 5.1 Start Migration

```bash
# Start the migration plan
kubectl mtv start plan web-tier-migration
```

#### 5.2 Monitor Progress

```bash
# Watch overall plan status
kubectl mtv describe plan web-tier-migration

# Monitor individual VM progress
kubectl mtv get plan web-tier-migration --vms

# Watch specific VM details
kubectl mtv describe plan web-tier-migration --vm web-server-01
```

#### 5.3 Handle Warm Migration Cutover

```bash
# For warm migrations, perform cutover when ready
kubectl mtv cutover plan web-tier-migration

# Or schedule cutover for specific time
kubectl mtv cutover plan web-tier-migration --cutover "2024-01-15T02:00:00Z"
```

### Phase 6: Post-Migration Tasks

#### 6.1 Verify Migration Success

```bash
# Check VM status in target cluster
kubectl get vm -n production

# Verify VM instances are running
kubectl get vmi -n production

# Check storage provisioning
kubectl get pvc -n production
```

#### 6.2 Clean Up

```bash
# Archive completed plan
kubectl mtv archive plan web-tier-migration

# Optional: Delete temporary resources
kubectl delete configmap temp-migration-config
```

## Advanced Migration Scenarios

### Scenario 1: Large-Scale Enterprise Migration

**Requirements:**
- Migrate 100+ VMs across multiple clusters
- Minimize business impact
- Maintain security boundaries

**Approach:**

1. **Batch Planning:**
```bash
# Create environment-specific plans
kubectl mtv create plan web-tier-batch-1 \
  --source vsphere-prod \
  --vms @web-tier-vms-batch1.yaml \
  --target-namespace web-production

kubectl mtv create plan app-tier-batch-1 \
  --source vsphere-prod \
  --vms @app-tier-vms-batch1.yaml \
  --target-namespace app-production
```

2. **Staged Execution:**
```bash
# Start non-critical tiers first
kubectl mtv start plan web-tier-batch-1

# Monitor and validate
kubectl mtv get plan web-tier-batch-1 --vms

# Continue with critical tiers
kubectl mtv start plan app-tier-batch-1
```

3. **Automation Integration:**
```bash
#!/bin/bash
# Migration automation script
for plan in web-tier-batch-1 app-tier-batch-1 db-tier-batch-1; do
  kubectl mtv start plan $plan
  
  # Wait for completion
  while [[ $(kubectl mtv get plan $plan -o json | jq -r '.status.phase') != "Succeeded" ]]; do
    sleep 60
    echo "Waiting for $plan to complete..."
  done
  
  echo "$plan completed successfully"
done
```

### Scenario 2: Cross-Cloud Migration

**Requirements:**
- Migrate from on-premises vSphere to public cloud OpenShift
- Handle network connectivity challenges
- Optimize for bandwidth constraints

**Approach:**

1. **Network Optimization:**
```bash
# Create provider with transfer network
kubectl mtv create provider vsphere-onprem --type vsphere \
  --url https://vcenter.internal.com/sdk \
  --username admin@vsphere.local \
  --password $PASSWORD \
  --vddk-init-image quay.io/org/vddk:8.0.1

# Plan with optimized settings
kubectl mtv create plan cloud-migration \
  --source vsphere-onprem \
  --vms critical-app-01,critical-app-02 \
  --migration-type warm \
  --transfer-network dedicated-migration/migration-net
```

2. **Bandwidth Management:**
```bash
# Use warm migration to minimize cutover window
kubectl mtv create plan bandwidth-optimized \
  --source vsphere-onprem \
  --vms large-database \
  --migration-type warm \
  --preserve-static-ips
```

### Scenario 3: Hybrid Cloud Integration

**Requirements:**
- Maintain some VMs on-premises
- Migrate others to cloud
- Preserve network connectivity

**Approach:**

1. **Network Mapping for Hybrid:**
```bash
# Create hybrid network mapping
kubectl mtv create mapping network hybrid-networks \
  --source vsphere-prod \
  --target openshift-cloud \
  --network-pairs "Internal-Network:vpn/internal-bridge,DMZ:cloud/dmz-network,Management:ignored"
```

2. **Selective Migration:**
```bash
# Migrate only public-facing services
kubectl mtv create plan cloud-services \
  --source vsphere-prod \
  --network-mapping hybrid-networks \
  --vms web-frontend,api-gateway \
  --target-namespace public-services
```

### Scenario 4: Disaster Recovery Migration

**Requirements:**
- Emergency migration from failed infrastructure
- Rapid deployment with minimal configuration
- Data consistency critical

**Approach:**

1. **Emergency Plan Creation:**
```bash
# Quick plan with automatic mappings
kubectl mtv create plan disaster-recovery \
  --source vsphere-dr \
  --vms @critical-vms.yaml \
  --migration-type cold \
  --target-namespace disaster-recovery \
  --target-power-state on
```

2. **Accelerated Execution:**
```bash
# Start immediately without customization
kubectl mtv start plan disaster-recovery

# Monitor closely
kubectl mtv describe plan disaster-recovery --watch
```

## Best Practices

### Planning and Preparation

#### 1. Assessment and Inventory

**Do:**
- Conduct thorough inventory assessment before migration
- Document VM dependencies and interconnections
- Identify resource requirements and constraints
- Test with non-critical VMs first

**Don't:**
- Migrate without understanding VM relationships
- Skip performance baseline measurements
- Ignore storage and network requirements

**Example Assessment:**
```bash
# Comprehensive VM analysis
kubectl mtv get inventory vms vsphere-prod -q "
SELECT name, 
       memoryMB/1024 AS memoryGB,
       len(disks) AS diskCount,
       sum(disks[*].capacity)/1073741824 AS totalStorageGB,
       powerState,
       guestOS
WHERE powerState = 'poweredOn'
ORDER BY totalStorageGB DESC
LIMIT 20"
```

#### 2. Network Planning

**Do:**
- Map all required network segments
- Verify NetworkAttachmentDefinition availability
- Plan for network policy requirements
- Test connectivity post-migration

**Don't:**
- Leave source networks unmapped
- Map multiple sources to same specific target
- Ignore security network boundaries

**Example Network Validation:**
```bash
# Verify target networks exist
kubectl get network-attachment-definitions -A

# Create comprehensive mapping
kubectl mtv create mapping network production-complete \
  --source vsphere-prod \
  --target host \
  --network-pairs "Frontend-VLAN:web/frontend-net,Backend-VLAN:app/backend-net,Database-VLAN:data/database-net,Management:ignored"
```

#### 3. Storage Strategy

**Do:**
- Choose appropriate storage classes for workloads
- Consider performance characteristics (IOPS, throughput)
- Plan for storage capacity and growth
- Use enhanced storage features when beneficial

**Don't:**
- Use default storage class for all workloads
- Ignore access mode requirements
- Forget about backup and snapshot capabilities

**Example Storage Planning:**
```bash
# List available storage classes with capabilities
kubectl get storageclass -o yaml | grep -E "name:|provisioner:|parameters:"

# Create performance-aware mapping
kubectl mtv create mapping storage performance-tiered \
  --source vsphere-prod \
  --target host \
  --storage-pairs "High-IOPS-SSD:fast-nvme;volumeMode=Block;accessMode=ReadWriteOnce,Standard-SSD:balanced;volumeMode=Filesystem;accessMode=ReadWriteOnce,Archive-Storage:cold;volumeMode=Filesystem;accessMode=ReadWriteMany"
```

### Execution Best Practices

#### 1. Migration Timing

**Do:**
- Schedule migrations during maintenance windows
- Use warm migration for production workloads
- Plan for rollback procedures
- Coordinate with application teams

**Example Scheduled Migration:**
```bash
# Schedule warm migration with specific cutover time
kubectl mtv create plan scheduled-production \
  --source vsphere-prod \
  --vms prod-database \
  --migration-type warm

kubectl mtv start plan scheduled-production

# Schedule cutover for 2 AM maintenance window
kubectl mtv cutover plan scheduled-production --cutover "2024-01-15T02:00:00Z"
```

#### 2. Monitoring and Alerting

**Do:**
- Monitor migration progress continuously
- Set up alerts for failures
- Track resource utilization
- Document issues and resolutions

**Example Monitoring Script:**
```bash
#!/bin/bash
PLAN_NAME="production-migration"

while true; do
  STATUS=$(kubectl mtv get plan $PLAN_NAME -o json | jq -r '.status.phase')
  VM_COUNT=$(kubectl mtv get plan $PLAN_NAME --vms -o json | jq '[.status.migration.vms[] | select(.phase == "Succeeded")] | length')
  TOTAL_VMS=$(kubectl mtv get plan $PLAN_NAME --vms -o json | jq '.status.migration.vms | length')
  
  echo "$(date): Plan: $STATUS, Completed VMs: $VM_COUNT/$TOTAL_VMS"
  
  if [[ $STATUS == "Succeeded" ]]; then
    echo "Migration completed successfully!"
    break
  elif [[ $STATUS == "Failed" ]]; then
    echo "Migration failed! Check logs."
    kubectl mtv describe plan $PLAN_NAME
    break
  fi
  
  sleep 60
done
```

### Security Considerations

#### 1. Credential Management

**Do:**
- Use Kubernetes secrets for sensitive data
- Rotate credentials regularly
- Apply least-privilege principles
- Audit access to migration resources

**Example Secure Provider:**
```bash
# Create secret for credentials
kubectl create secret generic vsphere-credentials \
  --from-literal=username=admin@vsphere.local \
  --from-literal=password=$SECURE_PASSWORD

# Reference secret in provider
kubectl mtv create provider vsphere-secure --type vsphere \
  --url https://vcenter.example.com/sdk \
  --secret vsphere-credentials \
  --cacert @vcenter-ca.crt
```

#### 2. Network Security

**Do:**
- Maintain network segmentation in target
- Configure appropriate network policies
- Validate security group equivalents
- Monitor network traffic patterns

**Example Network Policy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: migrated-web-tier-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      tier: web
      migrated: "true"
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-system
    ports:
    - protocol: TCP
      port: 8080
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Provider Connectivity Issues

**Symptoms:**
- Provider status shows "Connection failed"
- Inventory queries timeout
- Authentication errors

**Diagnosis:**
```bash
# Check provider status
kubectl mtv get providers -o yaml

# Test basic connectivity
kubectl mtv get inventory hosts vsphere-prod
```

**Solutions:**
```bash
# Update provider credentials
kubectl mtv patch provider vsphere-prod \
  --username newuser@vsphere.local \
  --password $NEW_PASSWORD

# Fix certificate issues
kubectl mtv patch provider vsphere-prod \
  --cacert @updated-ca.crt

# Skip TLS verification (temporary fix)
kubectl mtv patch provider vsphere-prod \
  --insecure-skip-tls
```

#### 2. Migration Failures

**Symptoms:**
- VM migration stuck in "Running" state
- Disk transfer errors
- Network configuration failures

**Diagnosis:**
```bash
# Check plan details
kubectl mtv describe plan failed-migration

# Check specific VM status
kubectl mtv describe plan failed-migration --vm stuck-vm

# Check storage resources
kubectl get pvc,dv -l plan=failed-migration-uuid

# Check logs
kubectl logs -n forklift-operator deployment/forklift-controller
```

**Solutions:**
```bash
# Cancel problematic VMs
kubectl mtv cancel plan failed-migration --vms stuck-vm1,stuck-vm2

# Fix mapping issues
kubectl mtv patch mapping storage prod-storage \
  --update-pairs "problematic-datastore:working-storage-class"

# Restart with corrected configuration
kubectl mtv create plan fixed-migration \
  --source vsphere-prod \
  --vms stuck-vm1,stuck-vm2 \
  --storage-mapping corrected-storage
```

#### 3. Performance Issues

**Symptoms:**
- Slow disk transfer rates
- High CPU usage on controller
- Network bottlenecks

**Diagnosis:**
```bash
# Monitor controller resources
kubectl top pods -n forklift-operator

# Check network utilization
kubectl get events --field-selector reason=NetworkNotReady

# Check storage performance
kubectl get pvc -o yaml | grep -A5 -B5 "storage.kubernetes.io/selected-node"
```

**Solutions:**
```bash
# Enable VDDK optimization for vSphere
kubectl mtv patch provider vsphere-prod \
  --use-vddk-aio-optimization \
  --vddk-buf-count=32 \
  --vddk-buf-size-in-64k=128

# Use dedicated transfer network
kubectl mtv patch plan slow-migration \
  --transfer-network dedicated-migration/high-speed-net

# Optimize storage mapping
kubectl mtv patch mapping storage prod-storage \
  --update-pairs "slow-datastore:fast-nvme-storage;volumeMode=Block"
```

### Log Analysis

#### 1. Controller Logs

```bash
# Main controller logs
kubectl logs -n forklift-operator deployment/forklift-controller -c main --tail=100

# Inventory service logs
kubectl logs -n forklift-operator deployment/forklift-controller -c inventory --tail=100

# Follow logs for real-time monitoring
kubectl logs -n forklift-operator deployment/forklift-controller -f
```

#### 2. Importer Pod Logs

```bash
# Find importer pods for specific migration
kubectl get pods -l app=containerized-data-importer

# Get logs from specific importer
kubectl logs importer-pod-name

# Monitor importer progress
kubectl logs -f importer-pod-name
```

#### 3. Event Analysis

```bash
# Get migration-related events
kubectl get events --field-selector involvedObject.kind=Plan

# Get VM-specific events
kubectl get events --field-selector involvedObject.name=vm-name

# Get recent events across all namespaces
kubectl get events --all-namespaces --sort-by='.lastTimestamp' | tail -20
```

### Debug Commands

#### 1. Resource State Analysis

```bash
# Get comprehensive plan status
kubectl mtv get plan migration-plan -o yaml | yq '.status'

# Check VM migration details
kubectl mtv get plan migration-plan --vms -o json | jq '.status.migration.vms[]'

# Analyze storage provisioning
kubectl get dv,pvc -l plan=migration-plan-uuid -o yaml
```

#### 2. Network Connectivity Testing

```bash
# Test from within cluster
kubectl run debug-pod --image=nicolaka/netshoot -it --rm -- /bin/bash

# From debug pod, test provider connectivity
nslookup vcenter.example.com
curl -k https://vcenter.example.com/sdk

# Test inventory service
curl http://inventory-service:8080/providers
```

## Integration and Automation

### CI/CD Integration

MTV can be integrated into CI/CD pipelines for automated migrations:

#### 1. GitOps Approach

**Repository Structure:**
```
migration-configs/
├── providers/
│   ├── vsphere-prod.yaml
│   └── ovirt-prod.yaml
├── mappings/
│   ├── network-mappings.yaml
│   └── storage-mappings.yaml
├── plans/
│   ├── web-tier-migration.yaml
│   └── app-tier-migration.yaml
└── scripts/
    ├── prepare-migration.sh
    └── validate-migration.sh
```

**Example Pipeline:**
```yaml
# .github/workflows/migration.yml
name: VM Migration Pipeline
on:
  push:
    paths:
      - 'migration-configs/**'

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup kubectl-mtv
      run: |
        curl -LO https://github.com/yaacov/kubectl-mtv/releases/download/v0.x.x/kubectl-mtv_linux_amd64.tar.gz
        tar -xzf kubectl-mtv_linux_amd64.tar.gz
        chmod +x kubectl-mtv
        sudo mv kubectl-mtv /usr/local/bin/
    
    - name: Validate configuration
      run: |
        kubectl mtv get providers --dry-run
        ./scripts/validate-migration.sh
    
    - name: Execute migration
      run: |
        kubectl apply -f migration-configs/
        ./scripts/execute-migration.sh
```

#### 2. Ansible Integration

**Ansible Playbook:**
```yaml
---
- name: MTV Migration Automation
  hosts: localhost
  tasks:
    - name: Create providers
      kubernetes.core.k8s:
        definition:
          apiVersion: forklift.konveyor.io/v1beta1
          kind: Provider
          metadata:
            name: "{{ item.name }}"
            namespace: "{{ mtv_namespace }}"
          spec: "{{ item.spec }}"
      loop: "{{ providers }}"
    
    - name: Wait for provider readiness
      kubernetes.core.k8s_info:
        api_version: forklift.konveyor.io/v1beta1
        kind: Provider
        name: "{{ item.name }}"
        namespace: "{{ mtv_namespace }}"
        wait: true
        wait_condition:
          type: Ready
          status: "True"
        wait_timeout: 600
      loop: "{{ providers }}"
    
    - name: Create migration plans
      shell: |
        kubectl mtv create plan {{ item.name }} \
          --source {{ item.source }} \
          --vms "{{ item.vms | join(',') }}" \
          --migration-type {{ item.type }} \
          --namespace {{ mtv_namespace }}
      loop: "{{ migration_plans }}"
    
    - name: Start migrations
      shell: kubectl mtv start plan {{ item.name }}
      loop: "{{ migration_plans }}"
```

### Monitoring and Observability

#### 1. Prometheus Integration

**Custom Metrics:**
```yaml
# ServiceMonitor for MTV metrics
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: mtv-controller-metrics
spec:
  selector:
    matchLabels:
      app: forklift-controller
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

**Example Queries:**
```promql
# Migration success rate
rate(mtv_migration_success_total[5m]) / rate(mtv_migration_total[5m])

# Average migration duration
avg(mtv_migration_duration_seconds)

# Failed migrations by provider
sum(mtv_migration_failed_total) by (provider)
```

#### 2. Grafana Dashboard

**Key Metrics to Monitor:**
- Migration success/failure rates
- Migration duration trends
- Provider connectivity status
- Resource utilization during migrations
- Storage throughput and IOPS

### API Integration

MTV provides Kubernetes APIs for programmatic access:

#### 1. Provider Management

```go
// Go client example
import (
    "context"
    "k8s.io/client-go/kubernetes"
    forkliftv1 "github.com/kubev2v/forklift/pkg/apis/forklift/v1beta1"
)

func createProvider(ctx context.Context, client kubernetes.Interface) error {
    provider := &forkliftv1.Provider{
        ObjectMeta: metav1.ObjectMeta{
            Name:      "vsphere-api-created",
            Namespace: "forklift-operator",
        },
        Spec: forkliftv1.ProviderSpec{
            Type: "vsphere",
            URL:  "https://vcenter.example.com/sdk",
            Secret: &v1.SecretReference{
                Name: "vsphere-credentials",
            },
        },
    }
    
    _, err := client.Create(ctx, provider, metav1.CreateOptions{})
    return err
}
```

#### 2. Plan Automation

```python
# Python client example
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def create_migration_plan(plan_name, source_provider, vms):
    config.load_kube_config()
    
    custom_api = client.CustomObjectsApi()
    
    plan_spec = {
        "apiVersion": "forklift.konveyor.io/v1beta1",
        "kind": "Plan",
        "metadata": {
            "name": plan_name,
            "namespace": "forklift-operator"
        },
        "spec": {
            "provider": {
                "source": {"name": source_provider},
                "target": {"name": "host"}
            },
            "vms": [{"name": vm} for vm in vms]
        }
    }
    
    try:
        custom_api.create_namespaced_custom_object(
            group="forklift.konveyor.io",
            version="v1beta1",
            namespace="forklift-operator",
            plural="plans",
            body=plan_spec
        )
        print(f"Created plan: {plan_name}")
    except ApiException as e:
        print(f"Error creating plan: {e}")
```

This comprehensive guide provides the foundation for understanding and successfully implementing MTV migrations. From basic concepts to advanced automation, these practices will help ensure successful virtual machine migrations to Kubernetes environments.
