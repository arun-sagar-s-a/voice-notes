variable "tenancy_ocid" {
  type        = string
  description = "OCID of the Oracle Cloud tenancy"
}

variable "user_ocid" {
  type        = string
  description = "OCID of the OCI user"
}

variable "fingerprint" {
  type        = string
  description = "Fingerprint of the API key uploaded to OCI"
}

variable "private_key_path" {
  type        = string
  description = "Path to the OCI API private key (.pem file) on the machine"
}

variable "region" {
  type        = string
  description = "OCI region, e.g. us-ashburn-1"
}
variable "ad_index" {
  type        = number
  description = "Which availability domain index to use (0, 1, or 2)"
  default     = 1
}