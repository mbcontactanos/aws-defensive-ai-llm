# Documento 5: Manual de Mejores Prácticas de Seguridad en AWS

## 1. Introducción

Este documento sirve como un manual de referencia rápida que consolida las mejores prácticas de seguridad fundamentales para operar en el entorno de Amazon Web Services (AWS). Está basado en la documentación oficial de AWS, incluyendo la **Arquitectura de Referencia de Seguridad (SRA)** y las guías de mejores prácticas. El objetivo es proporcionar una guía clara y accionable para configurar y mantener un entorno de AWS seguro.

## 2. Gestión de Identidad y Acceso (IAM)

IAM es la piedra angular de la seguridad en AWS. Una mala configuración aquí puede exponer toda la infraestructura.

-   **No usar la cuenta raíz (root)**: La cuenta raíz tiene acceso ilimitado. No debe usarse para tareas diarias. En su lugar, cree usuarios IAM con los permisos necesarios. Habilite la Autenticación Multifactor (MFA) en la cuenta raíz y guarde las credenciales de forma segura.
-   **Principio de Menor Privilegio**: Otorgue a los usuarios, roles y servicios solo los permisos estrictamente necesarios para realizar sus tareas. Comience con un conjunto mínimo de permisos y añada más según sea necesario, en lugar de empezar con permisos amplios y restringirlos después.
-   **Usar Roles IAM para Aplicaciones y Servicios**: No incruste claves de acceso (Access Keys) en el código de las aplicaciones que se ejecutan en EC2, Lambda u otros servicios de AWS. En su lugar, asigne un Rol IAM al servicio, que le otorga credenciales temporales y rotativas automáticamente.
-   **Habilitar MFA para todos los usuarios**: La Autenticación Multifactor debe ser obligatoria para todos los usuarios humanos, especialmente para aquellos con permisos elevados.
-   **Rotar credenciales regularmente**: Rote las claves de acceso y las contraseñas periódicamente. Utilice políticas de contraseña fuertes para requerir complejidad y longitud.
-   **Revisar permisos con IAM Access Analyzer**: Utilice IAM Access Analyzer para identificar y revisar los recursos que se comparten con entidades externas y para validar que las políticas IAM proporcionan solo el acceso previsto.

## 3. Seguridad de la Infraestructura

-   **Proteger la red con VPCs**: Diseñe su red utilizando Amazon Virtual Private Cloud (VPC). Utilice subredes públicas para los recursos que deben estar de cara a Internet (como los balanceadores de carga) y subredes privadas para el backend (servidores de aplicaciones, bases de datos).
-   **Filtrar el tráfico con Security Groups y NACLs**:
    -   **Security Groups**: Actúan como un firewall a nivel de instancia (stateful). Permita solo el tráfico entrante necesario. Por ejemplo, si tiene un servidor web, solo permita el tráfico en los puertos 80 y 443 desde cualquier lugar (0.0.0.0/0). Para el acceso SSH (puerto 22), restrínjalo a un rango de IPs de confianza (ej. la IP de la oficina).
    -   **Network Access Control Lists (NACLs)**: Actúan como un firewall a nivel de subred (stateless). Proporcionan una segunda capa de defensa. Úselas para reglas de bloqueo amplias, como denegar todo el tráfico desde una dirección IP maliciosa conocida.
-   **Usar AWS WAF y Shield**: Para las aplicaciones web, utilice **AWS WAF (Web Application Firewall)** para protegerse contra ataques comunes de la capa de aplicación como inyecciones SQL y Cross-Site Scripting (XSS). **AWS Shield Standard** está habilitado por defecto y protege contra los ataques DDoS más comunes. Para una protección avanzada, considere **AWS Shield Advanced**.

## 4. Protección de Datos

-   **Encriptar todo, en todas partes**: Como se detalla en el Documento 4, la encriptación es fundamental.
    -   **En Reposo**: Habilite la encriptación por defecto en los buckets de S3, los volúmenes de EBS, las bases de datos RDS, etc., utilizando claves gestionadas por AWS KMS.
    -   **En Tránsito**: Fuerce el uso de HTTPS/TLS para todo el tráfico hacia y desde sus servicios. Utilice VPNs o AWS Direct Connect para el tráfico entre su entorno on-premise y AWS.
-   **Clasificar los datos**: Utilice **Amazon Macie** para descubrir y clasificar datos sensibles en sus buckets de S3. Esto le ayuda a entender dónde residen sus datos más críticos y a aplicar los controles de seguridad adecuados.
-   **Hacer backups regularmente**: Utilice **AWS Backup** para gestionar y automatizar de forma centralizada los backups de sus servicios de AWS. Asegúrese de que los backups también estén encriptados y probados periódicamente.

## 5. Detección de Amenazas y Monitorización

-   **Habilitar AWS CloudTrail en todas las regiones**: CloudTrail registra todas las llamadas a la API realizadas en su cuenta de AWS. Es su principal fuente de verdad para saber quién hizo qué y cuándo. Asegúrese de que los logs de CloudTrail estén encriptados y protegidos contra modificaciones.
-   **Habilitar AWS GuardDuty**: GuardDuty es un servicio de detección de amenazas que monitoriza continuamente en busca de actividad maliciosa y comportamiento no autorizado para proteger sus cuentas y cargas de trabajo de AWS.
-   **Centralizar los logs con AWS Security Hub**: Security Hub le proporciona una visión completa de su estado de seguridad en AWS. Agrega, organiza y prioriza sus alertas o hallazgos de seguridad de múltiples servicios de AWS, como GuardDuty, Inspector y Macie, así como de soluciones de socios de AWS.
-   **Configurar alertas con Amazon CloudWatch**: Cree alarmas de CloudWatch para notificarle sobre eventos específicos, como intentos fallidos de inicio de sesión, cambios en los Security Groups o picos inusuales en la actividad de la red.

## 6. Respuesta a Incidentes

-   **Automatizar la respuesta**: Utilice servicios como **Amazon EventBridge** y **AWS Lambda** para desencadenar respuestas automáticas a los hallazgos de seguridad. Por ejemplo, una función Lambda puede aislar una instancia EC2 o revocar credenciales cuando GuardDuty detecta una amenaza.
-   **Tener un plan de respuesta a incidentes**: Documente los pasos a seguir para diferentes tipos de incidentes. Utilice **AWS Systems Manager** para crear y ejecutar runbooks de automatización que ayuden a estandarizar y acelerar la respuesta.

Este manual proporciona una base sólida. La seguridad es un proceso continuo de mejora. Revise y adapte regularmente sus controles de seguridad para hacer frente a un panorama de amenazas en constante evolución.

## 7. Referencias

- AWS. (n.d.). *AWS Security Best Practices*. AWS Whitepaper. Disponible en: https://docs.aws.amazon.com/whitepapers/latest/aws-security-best-practices/welcome.html
- AWS. (n.d.). *AWS Security Reference Architecture (SRA)*. AWS Prescriptive Guidance. Disponible en: https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/welcome.html

