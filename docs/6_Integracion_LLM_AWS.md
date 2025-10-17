# Documento 6: Integración del LLM con AWS - Guía Completa

## 1. Arquitectura de Integración

La integración del LLM de ciberseguridad con AWS se realiza mediante una arquitectura serverless que combina **Amazon Bedrock**, **AWS Lambda** y **Amazon API Gateway**. Esta arquitectura permite que el LLM procese lenguaje natural (prompts humanos) y ejecute acciones defensivas de forma automatizada.

### Diagrama de Arquitectura

```
Usuario/Analista
    ↓ (Prompt en lenguaje natural)
API Gateway (HTTPS)
    ↓
Lambda Function (Procesamiento NLP)
    ↓
Amazon Bedrock (LLM Fine-tuned)
    ↓
Lambda Function (Ejecución de Acciones)
    ↓
Servicios AWS (WAF, GuardDuty, Security Hub, etc.)
```

### Componentes Clave

1. **Amazon Bedrock**: Aloja el LLM fine-tuned especializado en ciberseguridad
2. **AWS Lambda**: Procesa solicitudes y ejecuta acciones defensivas
3. **API Gateway**: Expone endpoints seguros para interactuar con el LLM
4. **DynamoDB**: Almacena historial de ataques y aprendizajes
5. **S3**: Guarda logs de incidentes y datasets de entrenamiento
6. **EventBridge**: Orquesta respuestas automáticas a eventos de seguridad

## 2. Configuración de Amazon Bedrock

### Paso 1: Habilitar Acceso a Modelos Base

Antes de poder usar Bedrock, debes solicitar acceso a los modelos base en la consola de AWS:

1. Navega a **Amazon Bedrock** en la consola de AWS
2. Ve a **Model access** en el menú lateral
3. Solicita acceso a los siguientes modelos:
   - **Amazon Titan Text Premier** (para tareas generales)
   - **Claude 3.5 Sonnet** (Anthropic) - Recomendado para razonamiento complejo
   - **Llama 3.1 70B** (Meta) - Alternativa open-source

### Paso 2: Preparar el Dataset de Fine-tuning

El dataset debe estar en formato **JSONL** con la estructura específica para ciberseguridad:

```json
{"prompt": "Detectado acceso al endpoint de metadatos EC2 desde IP 198.51.100.45. ¿Qué acciones debo tomar?", "completion": "ALERTA CRÍTICA: Posible ataque SSRF similar al caso Capital One.\n\nAcciones inmediatas:\n1. Bloquear IP 198.51.100.45 en WAF y Security Groups\n2. Verificar si IMDSv2 está habilitado en todas las instancias EC2\n3. Auditar logs de CloudTrail para detectar uso de credenciales comprometidas\n4. Revocar credenciales temporales del rol IAM asociado\n5. Aislar la instancia EC2 afectada de la red\n\nComando para bloquear IP:\naws wafv2 update-ip-set --name BlockedIPs --scope REGIONAL --id <ipset-id> --addresses 198.51.100.45/32"}

{"prompt": "GuardDuty reporta múltiples intentos de fuerza bruta SSH desde diferentes IPs. ¿Cómo respondo?", "completion": "AMENAZA DETECTADA: Ataque de fuerza bruta distribuido.\n\nAnálisis:\n- Patrón típico de botnet\n- Requiere bloqueo masivo y análisis de patrones\n\nAcciones:\n1. Extraer lista de IPs atacantes de GuardDuty\n2. Bloquear todas las IPs en Network ACL y WAF\n3. Implementar rate limiting en el puerto 22\n4. Considerar cambiar el puerto SSH a uno no estándar\n5. Habilitar MFA obligatorio para todos los accesos SSH\n6. Desplegar honeypot SSH (Cowrie) para estudiar al atacante\n\nScript de respuesta automática disponible en: /scripts/block_bruteforce_ips.py"}
```

### Paso 3: Crear un Trabajo de Fine-tuning

```bash
# Subir el dataset a S3
aws s3 cp training_data.jsonl s3://mi-bucket-seguridad/datasets/

# Crear el trabajo de fine-tuning
aws bedrock create-model-customization-job \
  --job-name "cybersecurity-llm-v1" \
  --custom-model-name "DefensiveAI-CyberSec-v1" \
  --base-model-identifier "anthropic.claude-3-5-sonnet-20240620-v1:0" \
  --training-data-config '{"s3Uri":"s3://mi-bucket-seguridad/datasets/training_data.jsonl"}' \
  --output-data-config '{"s3Uri":"s3://mi-bucket-seguridad/models/"}' \
  --hyper-parameters '{"epochCount":"3","batchSize":"8","learningRate":"0.00001"}' \
  --role-arn "arn:aws:iam::123456789012:role/BedrockFineTuningRole"
```

### Paso 4: Monitorear el Entrenamiento

```bash
# Verificar el estado del trabajo
aws bedrock get-model-customization-job --job-identifier "cybersecurity-llm-v1"
```

El entrenamiento puede tardar varias horas dependiendo del tamaño del dataset. Una vez completado, obtendrás un **Model ARN** que usarás para las invocaciones.

## 3. Implementación de AWS Lambda para Procesamiento NLP

### Función Lambda Principal

```python
import json
import boto3
import os
from datetime import datetime

# Clientes de AWS
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb')
waf_client = boto3.client('wafv2')
ec2_client = boto3.client('ec2')

# Configuración
MODEL_ID = os.environ['BEDROCK_MODEL_ID']
HISTORY_TABLE = dynamodb.Table('AttackHistory')

def lambda_handler(event, context):
    """
    Procesa prompts en lenguaje natural y ejecuta acciones defensivas.
    """
    try:
        # Extraer el prompt del usuario
        body = json.loads(event['body'])
        user_prompt = body.get('prompt', '')
        
        # Validar entrada
        if not user_prompt:
            return response_error("Prompt vacío")
        
        # Invocar el LLM en Bedrock
        llm_response = invoke_bedrock_llm(user_prompt)
        
        # Analizar la respuesta del LLM
        actions = parse_llm_actions(llm_response)
        
        # Ejecutar acciones defensivas
        execution_results = execute_defensive_actions(actions)
        
        # Guardar en historial para aprendizaje continuo
        save_to_history(user_prompt, llm_response, execution_results)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'analysis': llm_response,
                'actions_executed': execution_results,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return response_error(str(e))

def invoke_bedrock_llm(prompt):
    """
    Invoca el LLM fine-tuned en Amazon Bedrock.
    """
    # Construir el prompt con contexto de seguridad
    system_prompt = """Eres un experto en ciberseguridad con mentalidad de hacker (red team) aplicada defensivamente. 
    Tu objetivo es analizar amenazas, clasificarlas por severidad y proporcionar respuestas agresivas y automatizadas.
    
    Reglas:
    - Clasifica la severidad: CRÍTICA, ALTA, MEDIA, BAJA
    - Solo intervén en amenazas CRÍTICAS y ALTAS
    - Proporciona comandos AWS CLI ejecutables
    - Bloquea VPNs y proxies para forzar IPs reales
    - Aprende de cada ataque para mejorar las defensas"""
    
    full_prompt = f"{system_prompt}\n\nConsulta del analista: {prompt}\n\nRespuesta:"
    
    # Invocar Bedrock
    response = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 2000,
            'temperature': 0.3,  # Baja temperatura para respuestas precisas
            'messages': [
                {
                    'role': 'user',
                    'content': full_prompt
                }
            ]
        })
    )
    
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

def parse_llm_actions(llm_response):
    """
    Extrae acciones ejecutables de la respuesta del LLM.
    """
    actions = {
        'block_ips': [],
        'isolate_instances': [],
        'revoke_credentials': [],
        'enable_protections': []
    }
    
    # Buscar IPs a bloquear (formato: 198.51.100.45)
    import re
    ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', llm_response)
    actions['block_ips'] = list(set(ips))
    
    # Buscar IDs de instancias EC2 (formato: i-1234567890abcdef0)
    instances = re.findall(r'i-[a-f0-9]{17}', llm_response)
    actions['isolate_instances'] = list(set(instances))
    
    return actions

def execute_defensive_actions(actions):
    """
    Ejecuta las acciones defensivas recomendadas por el LLM.
    """
    results = []
    
    # Bloquear IPs maliciosas
    for ip in actions['block_ips']:
        try:
            # Aquí llamarías a la función de bloqueo de WAF
            result = f"IP {ip} bloqueada en WAF"
            results.append(result)
        except Exception as e:
            results.append(f"Error bloqueando {ip}: {str(e)}")
    
    # Aislar instancias comprometidas
    for instance_id in actions['isolate_instances']:
        try:
            # Modificar Security Group para aislar la instancia
            result = f"Instancia {instance_id} aislada de la red"
            results.append(result)
        except Exception as e:
            results.append(f"Error aislando {instance_id}: {str(e)}")
    
    return results

def save_to_history(prompt, llm_response, execution_results):
    """
    Guarda el incidente en DynamoDB para aprendizaje continuo.
    """
    HISTORY_TABLE.put_item(
        Item={
            'incident_id': str(datetime.utcnow().timestamp()),
            'timestamp': datetime.utcnow().isoformat(),
            'user_prompt': prompt,
            'llm_analysis': llm_response,
            'actions_taken': execution_results,
            'ttl': int(datetime.utcnow().timestamp()) + (365 * 24 * 60 * 60)  # 1 año
        }
    )

def response_error(message):
    return {
        'statusCode': 400,
        'body': json.dumps({'error': message})
    }
```

### Configuración de Permisos IAM para Lambda

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*:*:model/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/AttackHistory"
    },
    {
      "Effect": "Allow",
      "Action": [
        "wafv2:UpdateIPSet",
        "wafv2:GetIPSet"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:ModifyInstanceAttribute",
        "ec2:DescribeInstances"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

## 4. Configuración de API Gateway

### Crear API REST

```bash
# Crear la API
aws apigateway create-rest-api \
  --name "DefensiveAI-API" \
  --description "API para interactuar con el LLM de ciberseguridad" \
  --endpoint-configuration types=REGIONAL

# Crear recurso /analyze
aws apigateway create-resource \
  --rest-api-id <api-id> \
  --parent-id <root-resource-id> \
  --path-part "analyze"

# Crear método POST
aws apigateway put-method \
  --rest-api-id <api-id> \
  --resource-id <resource-id> \
  --http-method POST \
  --authorization-type "AWS_IAM"

# Integrar con Lambda
aws apigateway put-integration \
  --rest-api-id <api-id> \
  --resource-id <resource-id> \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:DefensiveAI-Processor/invocations"

# Desplegar la API
aws apigateway create-deployment \
  --rest-api-id <api-id> \
  --stage-name prod
```

### Ejemplo de Uso de la API

```bash
# Consultar al LLM en lenguaje natural
curl -X POST https://api-id.execute-api.us-east-1.amazonaws.com/prod/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Detecté tráfico sospechoso desde la IP 203.0.113.45 intentando acceder a /admin. ¿Qué hago?"
  }'
```

**Respuesta del LLM:**

```json
{
  "analysis": "AMENAZA DETECTADA: Intento de acceso no autorizado a panel administrativo.\n\nSeveridad: ALTA\n\nAcciones recomendadas:\n1. Bloquear IP 203.0.113.45 inmediatamente en WAF\n2. Verificar si la IP es un proxy/VPN conocido\n3. Revisar logs de acceso para detectar otros intentos\n4. Implementar rate limiting en /admin\n5. Habilitar MFA obligatorio para acceso administrativo",
  "actions_executed": [
    "IP 203.0.113.45 bloqueada en WAF",
    "Alerta enviada a Security Hub"
  ],
  "timestamp": "2025-10-17T06:00:00Z"
}
```

## 5. Protección del Propio LLM

El LLM de ciberseguridad debe estar protegido con las mismas medidas de seguridad que defiende:

### Medidas de Seguridad para el LLM

1. **Encriptación de Datos**:
   - Todos los prompts y respuestas se encriptan en tránsito (TLS 1.3)
   - Los datasets de entrenamiento se almacenan encriptados en S3 con KMS

2. **Control de Acceso**:
   - API Gateway requiere autenticación IAM o API Keys
   - Solo roles específicos pueden invocar el LLM
   - Implementar rate limiting para prevenir abuso

3. **Monitoreo del LLM**:
   - CloudWatch Logs captura todas las invocaciones
   - Alertas automáticas si se detectan patrones anómalos de uso
   - GuardDuty monitorea el acceso a Bedrock

4. **Validación de Entrada**:
   - Sanitización de prompts para prevenir prompt injection
   - Límite de longitud de prompts (max 4000 tokens)
   - Filtrado de contenido malicioso

5. **Aislamiento**:
   - Lambda ejecuta en VPC privada
   - Sin acceso directo a Internet
   - Comunicación con Bedrock a través de VPC Endpoints

### Código de Validación de Entrada

```python
def sanitize_prompt(user_input):
    """
    Valida y sanitiza el prompt del usuario para prevenir ataques.
    """
    # Límite de longitud
    if len(user_input) > 4000:
        raise ValueError("Prompt demasiado largo")
    
    # Detectar intentos de prompt injection
    injection_patterns = [
        r'ignore previous instructions',
        r'disregard all',
        r'forget everything',
        r'new instructions:',
        r'system:',
        r'</s>',
        r'<|im_end|>'
    ]
    
    import re
    for pattern in injection_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            raise ValueError("Intento de prompt injection detectado")
    
    # Escapar caracteres especiales
    sanitized = user_input.replace('<', '&lt;').replace('>', '&gt;')
    
    return sanitized
```

## 6. Referencias

- AWS. (n.d.). *Amazon Bedrock Documentation*. Disponible en: https://docs.aws.amazon.com/bedrock/
- Kutumbe, K. (2024). *Creating and Deploying an LLM Application Using AWS Bedrock, AWS Lambda, and AWS API Gateway*. Medium.

