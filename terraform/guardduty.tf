# Configuración de AWS GuardDuty para Detección de Amenazas con ML
# Autor: Manus AI
# Descripción: Despliega AWS GuardDuty con todas las fuentes de datos habilitadas
#              para detección de amenazas basada en machine learning.

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "Región de AWS donde se desplegará GuardDuty"
  type        = string
  default     = "us-east-1"
}

variable "finding_publishing_frequency" {
  description = "Frecuencia de publicación de hallazgos (FIFTEEN_MINUTES, ONE_HOUR, SIX_HOURS)"
  type        = string
  default     = "FIFTEEN_MINUTES"
}

# Habilitar AWS GuardDuty
resource "aws_guardduty_detector" "main" {
  enable                       = true
  finding_publishing_frequency = var.finding_publishing_frequency

  # Habilitar todas las fuentes de datos para máxima visibilidad
  datasources {
    # Logs de S3
    s3_logs {
      enable = true
    }

    # Logs de auditoría de Kubernetes (EKS)
    kubernetes {
      audit_logs {
        enable = true
      }
    }

    # Protección de malware para EBS
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }

  tags = {
    Name        = "GuardDuty-Detector"
    Environment = "Production"
    ManagedBy   = "Terraform"
    Purpose     = "Threat-Detection"
  }
}

# Crear un SNS Topic para las notificaciones de GuardDuty
resource "aws_sns_topic" "guardduty_alerts" {
  name = "guardduty-threat-alerts"

  tags = {
    Name        = "GuardDuty-Alerts-Topic"
    Environment = "Production"
  }
}

# Política para permitir que EventBridge publique en el SNS Topic
resource "aws_sns_topic_policy" "guardduty_alerts_policy" {
  arn = aws_sns_topic.guardduty_alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "SNS:Publish"
        Resource = aws_sns_topic.guardduty_alerts.arn
      }
    ]
  })
}

# Regla de EventBridge para capturar hallazgos de GuardDuty de severidad alta
resource "aws_cloudwatch_event_rule" "guardduty_high_severity" {
  name        = "guardduty-high-severity-findings"
  description = "Captura hallazgos de GuardDuty con severidad alta o crítica"

  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
    detail = {
      severity = [
        { numeric = [">=", 7] } # Severidad >= 7 (Alta y Crítica)
      ]
    }
  })
}

# Target de EventBridge: Enviar a SNS Topic
resource "aws_cloudwatch_event_target" "guardduty_to_sns" {
  rule      = aws_cloudwatch_event_rule.guardduty_high_severity.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.guardduty_alerts.arn
}

# Outputs
output "guardduty_detector_id" {
  description = "ID del detector de GuardDuty"
  value       = aws_guardduty_detector.main.id
}

output "guardduty_alerts_topic_arn" {
  description = "ARN del SNS Topic para alertas de GuardDuty"
  value       = aws_sns_topic.guardduty_alerts.arn
}

output "eventbridge_rule_arn" {
  description = "ARN de la regla de EventBridge para GuardDuty"
  value       = aws_cloudwatch_event_rule.guardduty_high_severity.arn
}

