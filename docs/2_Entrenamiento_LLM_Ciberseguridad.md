# Documento 2: Entrenamiento del LLM para Ciberseguridad Defensiva

## 1. El Rol del LLM como Analista de Seguridad Aumentado

En nuestra arquitectura, el Modelo de Lenguaje Grande (LLM) no es simplemente una herramienta de chat, sino el núcleo cognitivo del Centro de Operaciones de Seguridad (SOC). Actúa como un **analista de seguridad aumentado**, realizando tareas que tradicionalmente requieren una intensa intervención humana, pero a la velocidad y escala de la máquina.

Sus funciones principales son:

-   **Interpretación y Correlación**: Ingerir y comprender hallazgos de seguridad, logs y alertas de docenas de fuentes distintas (GuardDuty, WAF, Inspector, etc.) en lenguaje natural y formatos estructurados.
-   **Análisis de Causa Raíz**: Formular hipótesis sobre la naturaleza de un ataque, su vector y su posible impacto, basándose en la evidencia recolectada.
-   **Generación de Planes de Respuesta**: Crear dinámicamente *playbooks* de respuesta a incidentes, detallando paso a paso las acciones de contención, erradicación y recuperación.
-   **Orquestación de Herramientas**: Traducir los planes de respuesta en comandos y llamadas a API ejecutables para interactuar directamente con los servicios de AWS y las herramientas de seguridad.

Para lograr esto, un LLM de propósito general debe ser especializado a través de un proceso de **fine-tuning** (ajuste fino) utilizando datos específicos del dominio de la ciberseguridad en AWS.

## 2. Preparación de Datos para el Fine-Tuning

La calidad del fine-tuning depende enteramente de la calidad y relevancia del dataset de entrenamiento. El objetivo es enseñarle al LLM a "pensar" como un analista de seguridad experto. El dataset debe consistir en pares de `prompt` (entrada) y `completion` (salida deseada).

### Tabla de Fuentes de Datos para Entrenamiento

| Tipo de Dato                        | Propósito                                                                      | Ejemplo de `Prompt` (Entrada)                                                                                             | Ejemplo de `Completion` (Salida)                                                                                                                               |
| :---------------------------------- | :----------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Playbooks de Respuesta**          | Enseñar al LLM los procedimientos estándar para diferentes tipos de incidentes. | "Incidente: Ransomware detectado en la instancia i-0123456789abcdef0. Genera un playbook de respuesta."                      | Un JSON estructurado con pasos: 1. Aislar instancia, 2. Tomar snapshot de EBS, 3. Rotar credenciales IAM, 4. Analizar memoria.                                   |
| **Logs de Servicios AWS (Sintéticos)** | Aprender a identificar patrones maliciosos en logs de CloudTrail, VPC, etc.     | Un bloque de logs de VPC Flow con múltiples conexiones a una IP conocida de C2 (Comando y Control).                      | "Análisis: Tráfico de red anómalo detectado. Múltiples conexiones salientes a una IP de C2 desde la instancia X. Posible exfiltración de datos o baliza de malware." |
| **Documentación de APIs de AWS**    | Aprender la sintaxis correcta para interactuar con los servicios de AWS.       | "Tarea: Bloquear la dirección IP 54.123.45.67 en el WAF 'Main-WAF'."                                                      | El comando JSON para la llamada a la API `aws wafv2 update-ip-set` con los parámetros correctos.                                                                |
| **Informes de Threat Intelligence** | Incorporar conocimiento sobre Tácticas, Técnicas y Procedimientos (TTPs) de actores. | "Alerta de GuardDuty: 'Stealth:IAMUser/S3ServerAccessLoggingDisabled'. ¿Cuál es el riesgo y el TTP de MITRE asociado?" | "Análisis: Un atacante ha deshabilitado el logging de acceso a S3 para ocultar sus rastros. Corresponde al TTP T1562.001 (Disable or Modify Tools)."          |

## 3. Generación de Datasets Sintéticos

Debido a la sensibilidad de los datos de seguridad reales, es fundamental generar un **dataset sintético** de alta calidad. Este proceso implica la creación de miles de ejemplos realistas que simulan escenarios de ataque y las respuestas ideales.

El formato comúnmente utilizado es **JSON Lines (JSONL)**, donde cada línea es un objeto JSON que contiene un par de `prompt` y `completion`.

**Ejemplo de una entrada en el dataset (`synthetic_playbooks.jsonl`):**

```json
{"prompt": "{\"detail-type\": \"GuardDuty Finding\", \"source\": \"aws.guardduty\", \"detail\": {\"type\": \"Recon:EC2/PortProbeUnprotectedPort\", \"resource\": {\"instanceDetails\": {\"instanceId\": \"i-0123456789abcdef0\"}}, \"service\": {\"action\": {\"portProbeAction\": {\"portProbeDetails\": [{\"remoteIpDetails\": {\"ipAddressV4\": \"198.51.100.10\"}}], \"blocked\": false}}}}", "completion": "{\"analysis\": {\"summary\": \"Se ha detectado un escaneo de puertos desde la IP 198.51.100.10 contra la instancia i-0123456789abcdef0. Esto indica una fase de reconocimiento por parte de un posible atacante.\", \"mitre_ttp\": \"T1046 - Port Scan\", \"risk_level\": \"Medio\"}, \"response_plan\": [ {\"step\": 1, \"action\": \"Block_IP\", \"description\": \"Añadir la IP 198.51.100.10 a un IPSet de bloqueo en AWS WAF y asociarlo a la ACL de red.\", \"parameters\": {\"ip_address\": \"198.51.100.10\", \"waf_name\": \"Main-WAF\"}}, {\"step\": 2, \"action\": \"Review_Security_Group\", \"description\": \"Revisar las reglas del Security Group asociado a la instancia para asegurar que solo los puertos necesarios están expuestos.\", \"parameters\": {\"instance_id\": \"i-0123456789abcdef0\"}}, {\"step\": 3, \"action\": \"Deploy_Honeypot\", \"description\": \"Considerar el despliegue de un honeypot de baja interacción en el puerto escaneado para recolectar inteligencia sobre el atacante.\", \"parameters\": {}} ]}"}
```

*Puede encontrar ejemplos de estos datasets en la carpeta `/llm-training-data`.* 

## 4. Proceso de Entrenamiento y Evaluación

El proceso de fine-tuning se puede resumir en los siguientes pasos:

1.  **Selección del Modelo Base**: Elegir un modelo fundacional potente y con buenas capacidades de razonamiento, como los disponibles a través de **Amazon Bedrock**.
2.  **Ejecución del Fine-Tuning**: Utilizar los servicios de AWS, como **Amazon SageMaker** o las propias capacidades de fine-tuning de Bedrock, para entrenar el modelo base con el dataset sintético. Este proceso ajusta los pesos del modelo para especializarlo en el dominio de la ciberseguridad.
3.  **Evaluación del Modelo**: Una vez entrenado, el modelo se evalúa contra un conjunto de datos de prueba (que no se usó en el entrenamiento) para medir su precisión, coherencia y la seguridad de sus respuestas. Se debe verificar que no "alucina" comandos peligrosos y que sigue las directrices de seguridad.
4.  **Despliegue**: El modelo ajustado se despliega como un endpoint de inferencia privado, listo para ser consumido por el resto de la arquitectura de seguridad (por ejemplo, por una función AWS Lambda que procesa las alertas).

Este ciclo de entrenamiento y evaluación es iterativo. A medida que surgen nuevas amenazas y TTPs, el dataset de entrenamiento debe ser actualizado y el modelo re-entrenado para mantener su eficacia.

## 5. Referencias

[1] Brooks, A. (2025). *Building an AI-Powered Security Operations Center on AWS*. Medium. Disponible en: https://medium.com/@rotordev/building-an-ai-powered-security-operations-center-on-aws-a-technical-deep-dive-6cd4ca5ec8ee

[2] Dora, R. (2025). *Building a Resilient Cybersecurity Architecture with AI/ML on AWS*. Altimetrik Blog. Disponible en: https://www.altimetrik.com/blog/building-resilient-cybersecurity-ai-ml-aws

