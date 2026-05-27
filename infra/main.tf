resource "oci_core_vcn" "voice_notes" {
    compartment_id = var.tenancy_ocid
    cidr_blocks = ["10.0.0.0/16"]
    display_name = "voice-notes-vcn"
    dns_label = "voicenotes"
  
}
resource "oci_core_internet_gateway" "voice_notes" {
    compartment_id = var.tenancy_ocid
    vcn_id = oci_core_vcn.voice_notes.id
    display_name = "voice-notes-igw"
  
}
resource "oci_core_default_route_table" "voice_notes" {
    manage_default_resource_id = oci_core_vcn.voice_notes.default_route_table_id
    display_name = "voice-notes-defaut-rt"

    route_rules {
      network_entity_id = oci_core_internet_gateway.voice_notes.id
      destination = "0.0.0.0/0"
      destination_type = "CIDR_BLOCK"
    }
  
}
resource "oci_core_default_security_list" "voice_notes" {
  manage_default_resource_id = oci_core_vcn.voice_notes.default_security_list_id
  display_name               = "voice-notes-default-sl"

  # Allow all outbound traffic
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  # Allow SSH (port 22) inbound
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"  # 6 = TCP
    tcp_options {
      min = 22
      max = 22
    }
  }

  # Allow your app (port 8000) inbound
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"  # 6 = TCP
    tcp_options {
      min = 8080
      max = 8080
    }
  }
# Allow HTTP (port 80) — needed for Let's Encrypt + redirects
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"  # 6 = TCP
    tcp_options {
      min = 80
      max = 80
    }
  }

# Allow HTTPS (port 443) — main public traffic
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"  # 6 = TCP
    tcp_options {
      min = 443
      max = 443
    }
  }
}
resource "oci_core_subnet" "voice-notes" {
  compartment_id = var.tenancy_ocid
  vcn_id = oci_core_vcn.voice_notes.id
  cidr_block = "10.0.1.0/24"
  display_name = "voice-notes-subnet"
  dns_label = "vnsubnet"
}

# Data source: find latest Ubuntu 22.04 ARM image
data "oci_core_images" "ubuntu" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# The VM itself
resource "oci_core_instance" "voice_notes" {
  compartment_id      = var.tenancy_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[var.ad_index].name
  shape               = "VM.Standard.A1.Flex"
  display_name        = "voice-notes-vm"

  shape_config {
    ocpus         = 1
    memory_in_gbs = 6
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu.images[0].id
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.voice-notes.id
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = file("~/.ssh/voice_notes_oracle_vm_ed25519.pub")
  }
}

# Data source: find availability domains in this region
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}