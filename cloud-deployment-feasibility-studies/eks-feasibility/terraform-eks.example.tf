# STUDY SKETCH. Not live Terraform.
# Live estate root is heavy-rental-project-instructure-and-cloud-deploy/terraform/academy/
# (no aws_eks_*). If a new pipeline is built, this belongs in terraform/eks/ — a
# different state key (eks/terraform.tfstate). Do not merge into the compose estate.
#
# Academy IAM (given): LabEksClusterRole for CLUSTER and NODE. Data-source only.
# Instance types: nano, micro, small, medium, large.
# Split: Terraform CREATES the cluster. Ansible does not.

variable "lab_eks_cluster_role_name" {
  type        = string
  default     = "LabEksClusterRole"
  description = "Vocareum pre-created role. Used for aws_eks_cluster.role_arn AND aws_eks_node_group.node_role_arn. Do not create IAM."
}

variable "node_instance_type" {
  type    = string
  default = "t3.medium"

  validation {
    condition     = can(regex("^(t[23]a?\\.(nano|micro|small|medium|large))$", var.node_instance_type))
    error_message = "Academy EKS nodes must be nano, micro, small, medium, or large."
  }
}

# Parallel to terraform/academy/data.tf LabRole — data-source, fail if missing.
data "aws_iam_role" "lab_eks" {
  name = var.lab_eks_cluster_role_name

  lifecycle {
    postcondition {
      condition     = self.name == "LabEksClusterRole"
      error_message = "Academy EKS must data-source LabEksClusterRole. Do not create IAM. Do not use LabRole / LabInstanceProfile here."
    }
  }
}

# VPC / subnets omitted — copy a small two-AZ layout from terraform/academy/vpc.tf
# or data-source a donated VPC. Do not also create asg-portal / asg-rest / …

resource "aws_eks_cluster" "this" {
  name     = "hr-eks-academy"
  role_arn = data.aws_iam_role.lab_eks.arn
  version  = "1.31"

  vpc_config {
    subnet_ids              = [] # fill from aws_subnet.eks[*].id
    endpoint_public_access  = true
    endpoint_private_access = true
  }

  access_config {
    authentication_mode                         = "API"
    bootstrap_cluster_creator_admin_permissions = true
  }

  # Do not attach compute_config Auto Mode — extra IAM, not LabEksClusterRole-only.
}

resource "aws_eks_node_group" "this" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "hr-eks-nodes"
  node_role_arn   = data.aws_iam_role.lab_eks.arn
  subnet_ids      = [] # private app subnets
  instance_types  = [var.node_instance_type]
  ami_type        = "AL2023_x86_64_STANDARD"
  capacity_type   = "ON_DEMAND"

  scaling_config {
    desired_size = 2
    min_size     = 1
    max_size     = 2
  }

  update_config {
    max_unavailable = 1
  }

  depends_on = [aws_eks_cluster.this]
}

output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "lab_eks_cluster_role_arn" {
  value = data.aws_iam_role.lab_eks.arn
}

# Paid (terraform/eks with var.deployment=actual) does NOT use this data source.
# It creates aws_iam_role.cluster + aws_iam_role.node. LabEksClusterRole will 404.
