locals {
  vm_public_ip = oci_core_instance.voice_notes.public_ip
}
output "vm_public_ip" {
    description = "Public IP of voice-notes VM"
    value = local.vm_public_ip
}

output "vm_ssh_command" {
    description = "Ready to copy ssh command"
    value = "ssh -i ~/.ssh/voice_notes_oracle_vm_ed25519 ubuntu@${local.vm_public_ip}"
    
}