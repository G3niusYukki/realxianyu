output "cluster_name" {
  description = "Name of the Kind cluster"
  value       = kind_cluster.xianyuflow.name
}

output "kubeconfig_path" {
  description = "Path to the kubeconfig file"
  value       = kind_cluster.xianyuflow.kubeconfig_path
}

output "namespaces" {
  description = "List of created namespaces"
  value       = [kubernetes_namespace.xianyuflow.metadata[0].name, kubernetes_namespace.monitoring.metadata[0].name]
}
