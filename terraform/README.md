# Terraform foundation

This directory is intentionally incomplete for deployment safety. It defines low-risk architectural foundations but does not create an ECS service, public load balancer, NAT gateway, or secrets.

Commands for review only:

```bash
terraform init
terraform fmt -check
terraform validate
terraform plan
```

Do not run `terraform apply` until AWS credentials, region, budget alerts, IAM permissions, networking, and cleanup steps are approved.
