variable "cluster_name" {
  description = "Name of the Kind cluster"
  type        = string
  default     = "xianyuflow-local"
}

variable "postgres_password" {
  description = "Password for PostgreSQL database"
  type        = string
  default     = "xianyu2024"
  sensitive   = true
}

variable "redis_password" {
  description = "Password for Redis cache"
  type        = string
  default     = "xianyu2024"
  sensitive   = true
}
