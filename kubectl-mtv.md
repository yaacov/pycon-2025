# **The Complete Guide to kubectl-mtv**

This document provides a comprehensive overview of the kubectl-mtv command-line tool, a kubectl plugin for facilitating virtual machine migrations to Kubernetes using the Forklift/Migration Toolkit for Virtualization (MTV).

## **Chapter 1: Installation and Initial Setup**

Before you can begin migrating VMs, you need to install the kubectl-mtv plugin and configure your environment.

### **1.1 Prerequisites**

Ensure your environment meets the following requirements:

* A Kubernetes cluster (version 1.23 or higher).  
* The Forklift (upstream) or Migration Toolkit for Virtualization (MTV) operator installed on the cluster.  
* kubectl installed and configured to access your cluster.  
* Administrative permissions to manage cluster resources, including RBAC objects and secrets.

### **1.2 Installation Methods**

You can install kubectl-mtv using one of several methods.

#### **Method 1: Krew Plugin Manager (Recommended)**

Krew is the recommended way to manage kubectl plugins.

1. **Install Krew:** If you don't have it, follow the official Krew installation instructions.  
2. **Install the plugin:**  
   kubectl krew install mtv

3. **Verify:**  
   kubectl mtv \--help

#### **Method 2: Download Release Binaries**

You can download pre-built binaries directly from the project's GitHub releases page. An automated script can handle this for you:

REPO=yaacov/kubectl-mtv  
ASSET=kubectl-mtv.tar.gz  
LATEST\_VER=$(curl \-s https://api.github.com/repos/$REPO/releases/latest | grep \-m1 '"tag\_name"' | cut \-d'"' \-f4)  
curl \-L \-o $ASSET https://github.com/$REPO/releases/download/$LATEST\_VER/$ASSET  
tar \-xzf $ASSET  
chmod \+x kubectl-mtv  
sudo mv kubectl-mtv /usr/local/bin/

#### **Method 3: Build from Source**

For development or custom builds, you can compile the tool from source.

1. **Prerequisites:** Ensure you have Go 1.23+ and make installed.  
2. **Clone and build:**  
   git clone https://github.com/yaacov/kubectl-mtv.git  
   cd kubectl-mtv  
   make  
   sudo cp kubectl-mtv /usr/local/bin/

### **1.3 Initial Configuration**

kubectl-mtv uses your existing kubeconfig file for cluster authentication. For certain operations, you may need to set environment variables.

* **VDDK Image (for VMware):** When migrating from VMware, you must specify a VDDK (Virtual Disk Development Kit) image.  
  export MTV\_VDDK\_INIT\_IMAGE=quay.io/your-registry/vddk:8.0.1

## **Chapter 2: A Step-by-Step Migration Demo**

This chapter walks through a complete migration workflow from start to finish, providing a practical overview of the core commands.

### **Step 1: Project Setup**

Create a dedicated namespace for your migration activities.

kubectl create namespace demo-ns

### **Step 2: Register Source and Target Providers**

A "Provider" is a resource that defines a connection to a source virtualization platform or a target Kubernetes cluster.

1. **Register Kubernetes as the target provider:**  
   kubectl mtv create provider host \--type openshift

2. **Register VMware vSphere as the source provider:**  
   \# Ensure YOUR\_PASSWORD is set securely  
   kubectl mtv create provider vmware \--type vsphere \\  
     \-U https://your.vsphere.server.com/sdk \\  
     \-u your\_vsphere\_username \\  
     \-p $YOUR\_PASSWORD \\  
     \--vddk-init-image $MTV\_VDDK\_INIT\_IMAGE \\  
     \--provider-insecure-skip-tls

3. **List providers to verify:**  
   kubectl mtv get providers

### **Step 3: Discover Virtual Machines**

Use the inventory command to query the source provider and find VMs to migrate.

\# Find VMs with names matching a pattern and more than one disk  
kubectl mtv get inventory vms vmware \-q "where name \~= 'your\_vm\_name' and len disks \> 1"

### **Step 4: Create a Migration Plan**

A "Plan" defines all the parameters for migrating a specific set of VMs. This includes network and storage mappings.

kubectl mtv create plan demo \-S vmware \--vms comma\_separated\_list\_of\_selected\_vms

### **Step 5: Execute the Migration**

Once the plan is created and reviewed, you can start the migration process.

1. **Review the plan:**  
   kubectl mtv describe plan demo

2. **Start the migration:**  
   kubectl mtv start plan demo

### **Step 6: Monitor the Migration**

You can monitor the progress of the migration at different levels of detail.

\# Watch the overall plan status  
kubectl mtv describe plan demo \-w

\# Watch the status of individual VMs in the plan  
kubectl mtv get plan-vms demo \-w

\# Monitor logs for a specific migrating VM (identified by its vmID)  
kubectl logs \-l vmID=\<vm-id\> \-f

## **Chapter 3: Querying the Inventory**

Before you can create mappings or plans, you need to understand the resources available on your source provider. The get inventory command is a powerful tool for this purpose.

### **3.1 Supported Resources**

You can query the following resource types:

* vms: Virtual Machines  
* networks: Virtual networks  
* storage: Datastores or storage domains  
* hosts: vSphere ESXi hosts  
* namespaces: Kubernetes/OpenShift namespaces

### **3.2 Basic Syntax and Examples**

The command structure is kubectl mtv get inventory \<resource-type\> \<provider-name\> \[flags\].

* **List all VMs:**  
  kubectl mtv get inventory vms vsphere-provider

* **List all networks:**  
  kubectl mtv get inventory networks vsphere-provider

* **List all storage:**  
  kubectl mtv get inventory storage vsphere-provider

### **3.3 Advanced Filtering with the Query Language**

The \-q flag allows for powerful SQL-like queries to filter, sort, and select specific fields from the inventory.

* **Find powered-on VMs with more than 4GB of memory:**  
  kubectl mtv get inventory vms vsphere-provider \-q "WHERE powerState \= 'poweredOn' AND memoryMB \> 4096"

* **Find datastores with over 500GB of free space, sorted:**  
  kubectl mtv get inventory storage vsphere-provider \-q "WHERE free \> 500Gi ORDER BY free DESC"

* **Select specific fields with custom aliases:**  
  kubectl mtv get inventory vms vsphere-provider \-q "SELECT name, powerStateHuman AS state, memoryGB, ipAddress"

### **3.4 Exporting for Migration Plans**

A key feature is exporting a filtered VM list directly into a format that can be used to create a migration plan.

\# Export the list of VMs to a YAML file  
kubectl mtv get inventory vms vsphere-provider \-q "WHERE name LIKE 'web-%'" \-o planvms \> web-vms.yaml

\# Use the file to create a plan  
kubectl mtv create plan web-migration-plan \--source vsphere-provider \--vms @web-vms.yaml

## **Chapter 4: Configuring Network and Storage Mappings**

Mappings are crucial resources that define how a VM's network and storage from the source platform are translated to the target Kubernetes environment.

### **4.1 Creating Standalone Mappings**

You can create reusable mapping resources that can be referenced by multiple migration plans.

#### **Network Mappings**

A network mapping connects a source network (like a VMware PortGroup) to a target Kubernetes network (like a Multus NetworkAttachmentDefinition or the default pod network).

* **Syntax:**  
  kubectl-mtv create mapping network \<mapping-name\> \\  
    \--source \<source-provider\> \\  
    \--target \<target-provider\> \\  
    \--network-pairs "\<source-net\>:\<target-net\>,..."

* **Example:**  
  kubectl-mtv create mapping network production-networks \\  
    \--source vsphere-provider \\  
    \--target openshift-provider \\  
    \--network-pairs "VM Network:production/prod-net,Management:default,Backup Network:ignored"

#### **Storage Mappings**

A storage mapping connects a source datastore to a target Kubernetes StorageClass.

* **Syntax:**  
  kubectl-mtv create mapping storage \<mapping-name\> \\  
    \--source \<source-provider\> \\  
    \--target \<target-provider\> \\  
    \--storage-pairs "\<source-store\>:\<target-sc\>,..."

* **Example:**  
  kubectl-mtv create mapping storage tiered-storage \\  
    \--source vsphere-provider \\  
    \--target openshift-provider \\  
    \--storage-pairs "SSD-Datastore:fast-ssd,SATA-Datastore:standard"

### **4.2 Using Mappings When Creating Plans**

When creating a migration plan, you have three mutually exclusive options for defining mappings.

* Option 1: Reference Existing Mappings (Recommended for Production)  
  Use pre-created, reusable mapping resources.  
  kubectl mtv create plan my-plan \\  
    \--network-mapping production-networks \\  
    \--storage-mapping tiered-storage \\  
    \--vms vm1,vm2

* Option 2: Use Inline Mapping Pairs (for Quick Migrations)  
  Define mappings directly in the create plan command. This will automatically create mapping resources named \<plan-name\>-network and \<plan-name\>-storage.  
  kubectl mtv create plan my-plan \\  
    \--network-pairs "VM Network:default" \\  
    \--storage-pairs "datastore1:standard" \\  
    \--vms vm1,vm2

* Option 3: Use Default Mappings (for Simple Tests)  
  Map all source resources to a single default target.  
  kubectl mtv create plan my-plan \\  
    \--default-target-network default \\  
    \--default-target-storage-class standard \\  
    \--vms vm1,vm2

### **4.3 Modifying Existing Mappings**

You can add, update, or remove pairs from existing mappings without recreating them using the patch command.

* **Add new pairs to a network mapping:**  
  kubectl mtv patch mapping network production-networks \\  
    \--add-pairs "New-Network:production/new-net"

* **Update an existing pair in a storage mapping:**  
  kubectl mtv patch mapping storage tiered-storage \\  
    \--update-pairs "SATA-Datastore:slow-archive"

* **Remove a pair from a network mapping:**  
  kubectl mtv patch mapping network production-networks \\  
    \--remove-pairs "Backup Network"

## **Chapter 5: Advanced Features**

kubectl-mtv provides several advanced features for more complex migration scenarios.

### **5.1 Migration Hooks**

Hooks allow you to run custom automation tasks (packaged as container images) at specific points in the migration lifecycle, such as before migration starts (PreHook) or after it finishes (PostHook).

* Creating a Hook:  
  A hook is defined by a container image and an optional Ansible playbook or command.  
  \# Create a hook that runs an Ansible playbook  
  kubectl-mtv create hook database-backup \\  
    \--image quay.io/ansible/creator-ee:latest \\  
    \--service-account migration-sa \\  
    \--playbook @backup-playbook.yaml

* Using Hooks in a Plan:  
  You can attach hooks to all VMs in a plan during creation.  
  kubectl mtv create plan my-db-migration \\  
    \--vms db-vm1,db-vm2 \\  
    \--pre-hook database-backup \\  
    \--post-hook verification-script

### **5.2 vSphere Host Management**

For vSphere environments, you can create Host resources that allow MTV to connect directly to ESXi hosts. This can reduce the load on vCenter and optimize data transfer.

* Syntax:  
  Host creation is only supported for vSphere providers. You must specify either an IP address or a network adapter name for IP resolution.  
  kubectl-mtv create host \<host-id\> \--provider \<vsphere-provider\> \\  
    (--ip-address \<ip\> | \--network-adapter \<adapter-name\>) \[auth-options\]

* Example:  
  Create a Host resource for an ESXi server by looking up its IP on the "Management Network" and providing new credentials.  
  kubectl-mtv create host esxi-01.corp.local \\  
    \--provider vsphere-prod \\  
    \--network-adapter "Management Network" \\  
    \--username root \\  
    \--password MySecretPassword

## **Chapter 6: Administration and Development**

This chapter covers topics relevant for cluster administrators and developers looking to contribute to the project.

### **6.1 Service Account and Token Management**

For automation and providing permissions to hooks, you often need to create a ServiceAccount with limited-scope admin rights and an associated authentication token.

1. **Create a namespace and ServiceAccount:**  
   kubectl create namespace demo-ns  
   kubectl create serviceaccount demo-admin \-n demo-ns

2. **Grant admin rights within that namespace:**  
   kubectl create rolebinding demo-admin-binding \\  
     \--clusterrole=admin \\  
     \--serviceaccount=demo-ns:demo-admin \\  
     \--namespace demo-ns

3. **Generate a short-lived token (Kubernetes 1.24+):**  
   kubectl \-n demo-ns create token demo-admin \--duration=24h

### **6.2 Development Guide**

If you wish to contribute to kubectl-mtv, follow these steps.

* **Prerequisites:** Go 1.23+, git, make, and musl-gcc for static builds.  
* **Setup:** Clone the repository and install development tools:  
  git clone https://github.com/yaacov/kubectl-mtv.git  
  cd kubectl-mtv  
  make install-tools

* **Common Commands:**  
  * make: Build the binary.  
  * make test: Run the test suite.  
  * make lint: Run code quality checks.  
  * make fmt: Format the code.  
* **Project Structure:** The cmd/ directory contains command implementations, while core logic resides in the pkg/ directory.
