# Documento 7: Casos Reales de Ataques a AWS y Sistema de Aprendizaje Continuo

## 1. Introducción: Aprender de los Errores del Pasado

La mejor manera de entrenar un LLM de ciberseguridad es alimentarlo con **casos reales de ataques exitosos**. Cada brecha de seguridad documentada es una lección invaluable que el sistema debe aprender para prevenir futuros incidentes similares. Este documento analiza los ataques más significativos a infraestructuras AWS y cómo implementar un sistema de aprendizaje continuo que mejore con cada nuevo ataque.

## 2. Caso Real #1: Capital One (2019) - Ataque SSRF y Exfiltración de Datos

### Resumen del Ataque

**Fecha**: 22-23 de marzo de 2019  
**Detección**: 19 de julio de 2019 (4 meses después)  
**Datos comprometidos**: 100+ millones de registros  
**Atacante**: Paige Thompson (ex-empleada de AWS)  
**Técnica**: Server-Side Request Forgery (SSRF)

### Anatomía del Ataque

El ataque a Capital One es un caso de estudio perfecto de cómo una mala configuración puede llevar a una brecha masiva de datos. La cadena de ataque fue la siguiente:

#### Paso 1: Reconocimiento

La atacante identificó una aplicación web de Capital One alojada en AWS que era vulnerable a SSRF. Esta vulnerabilidad permitía forzar al servidor a realizar peticiones HTTP a destinos arbitrarios.

#### Paso 2: Explotación de SSRF

La atacante utilizó la vulnerabilidad SSRF para hacer que el servidor web accediera al **servicio de metadatos de EC2** en la dirección especial `169.254.169.254`. Este servicio, accesible solo desde dentro de una instancia EC2, proporciona información sensible sobre la instancia, incluyendo credenciales temporales de IAM.

**Comando ejecutado por la atacante**:

```bash
curl http://<servidor-vulnerable>/proxy?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/<nombre-del-rol>
```

El servidor, al procesar esta petición, devolvió las credenciales temporales del rol IAM asociado a la instancia EC2.

**Respuesta del servidor de metadatos (IMDSv1)**:

```json
{
  "Code": "Success",
  "LastUpdated": "2019-03-22T10:00:00Z",
  "Type": "AWS-HMAC",
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "wJalr...",
  "Token": "IQoJb3JpZ2luX2VjEJ...",
  "Expiration": "2019-03-22T16:00:00Z"
}
```

#### Paso 3: Escalada de Privilegios

Con las credenciales temporales en su poder, la atacante configuró el AWS CLI con estas credenciales:

```bash
export AWS_ACCESS_KEY_ID=ASIA...
export AWS_SECRET_ACCESS_KEY=wJalr...
export AWS_SESSION_TOKEN=IQoJb3JpZ2luX2VjEJ...
```

Luego, listó los buckets de S3 accesibles con ese rol:

```bash
aws s3 ls
```

#### Paso 4: Exfiltración de Datos

El rol IAM tenía permisos excesivamente amplios, permitiendo acceso de lectura a múltiples buckets de S3 que contenían datos sensibles de clientes. La atacante descargó:

- 100 millones de solicitudes de tarjetas de crédito
- 140,000 números de Seguro Social (SSN)
- 80,000 números de cuenta bancaria

```bash
aws s3 sync s3://capital-one-customer-data /local/exfiltrated-data/
```

### Vulnerabilidades Explotadas

1. **SSRF en la aplicación web**: Falta de validación de URLs en un parámetro de entrada
2. **IMDSv1 habilitado**: No requería autenticación para acceder a metadatos
3. **Permisos IAM excesivos**: El rol tenía acceso de lectura a buckets críticos
4. **Falta de monitoreo**: El acceso anómalo a S3 no generó alertas
5. **WAF mal configurado**: No bloqueaba peticiones al rango 169.254.0.0/16

### Cómo el LLM Debe Aprender de Este Caso

El LLM debe ser entrenado con este patrón de ataque para detectarlo y prevenirlo:

**Entrada de entrenamiento**:

```json
{
  "attack_pattern": "SSRF to IMDS",
  "indicators": [
    "Peticiones HTTP a 169.254.169.254",
    "Acceso al endpoint /latest/meta-data/iam/security-credentials/",
    "Uso de credenciales temporales desde IP externa",
    "Acceso masivo a S3 desde credenciales de EC2"
  ],
  "severity": "CRÍTICA",
  "automated_response": [
    "Bloquear inmediatamente la IP de origen en WAF",
    "Revocar las credenciales temporales del rol IAM",
    "Aislar la instancia EC2 de la red",
    "Habilitar IMDSv2 en todas las instancias",
    "Auditar todos los buckets S3 accedidos en las últimas 24 horas",
    "Notificar al equipo de respuesta a incidentes"
  ],
  "prevention": [
    "Implementar IMDSv2 obligatorio",
    "Validar y sanitizar todas las URLs en parámetros de entrada",
    "Configurar WAF para bloquear peticiones a 169.254.0.0/16",
    "Aplicar principio de menor privilegio en roles IAM",
    "Habilitar CloudTrail y GuardDuty",
    "Implementar alertas de acceso anómalo a S3"
  ]
}
```

### Detección Automatizada por el LLM

Cuando el LLM detecta este patrón en los logs, debe responder inmediatamente:

**Prompt del sistema de monitoreo**:
```
"Detectadas 15 peticiones HTTP al endpoint 169.254.169.254/latest/meta-data/iam/security-credentials/ desde la instancia i-0abc123def456 en los últimos 5 minutos. ¿Qué acciones debo tomar?"
```

**Respuesta del LLM**:
```
🚨 ALERTA CRÍTICA: Posible ataque SSRF similar al caso Capital One detectado.

ANÁLISIS:
- Patrón coincide 95% con el ataque de Capital One 2019
- Acceso anómalo al servicio de metadatos de EC2
- Riesgo de exfiltración de credenciales IAM

ACCIONES INMEDIATAS (ejecutando automáticamente):

1. ✅ Bloqueando IP de origen en WAF
2. ✅ Revocando credenciales temporales del rol IAM
3. ✅ Aislando instancia i-0abc123def456 de la red
4. ✅ Habilitando IMDSv2 en la instancia afectada
5. ✅ Auditando accesos a S3 con las credenciales comprometidas

COMANDOS EJECUTADOS:
aws wafv2 update-ip-set --name BlockedIPs --addresses <IP>/32
aws iam update-role --role-name <rol> --max-session-duration 0
aws ec2 modify-instance-attribute --instance-id i-0abc123def456 --no-source-dest-check

PRÓXIMOS PASOS:
- Revisar logs de CloudTrail para identificar datos accedidos
- Notificar a clientes afectados si se confirma exfiltración
- Realizar análisis forense de la instancia EC2
```

## 3. Caso Real #2: Uber (2016) - Credenciales en GitHub

### Resumen del Ataque

**Fecha**: Octubre de 2016  
**Detección**: Noviembre de 2017 (1 año después)  
**Datos comprometidos**: 57 millones de usuarios y conductores  
**Técnica**: Credenciales de AWS expuestas en repositorio de GitHub

### Anatomía del Ataque

#### Paso 1: Descubrimiento de Credenciales

Los atacantes escanearon repositorios públicos de GitHub buscando credenciales de AWS expuestas accidentalmente. Encontraron un commit en un repositorio privado de Uber que contenía:

```python
# config.py
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

#### Paso 2: Acceso a AWS

Con estas credenciales, los atacantes accedieron a la cuenta de AWS de Uber:

```bash
aws configure set aws_access_key_id AKIAIOSFODNN7EXAMPLE
aws configure set aws_secret_access_key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Listar buckets S3
aws s3 ls
```

#### Paso 3: Exfiltración de Datos

Los atacantes descargaron datos de 57 millones de usuarios desde buckets de S3, incluyendo:
- Nombres y correos electrónicos
- Números de teléfono
- Licencias de conducir de 600,000 conductores

### Cómo el LLM Debe Detectar Esto

El LLM debe monitorear el uso de credenciales y detectar patrones anómalos:

**Indicadores de compromiso**:
- Uso de credenciales desde IP geográficamente inusual
- Acceso a recursos nunca antes accedidos por esas credenciales
- Volumen de descarga de S3 anormalmente alto
- Uso de credenciales fuera del horario laboral

**Respuesta automatizada del LLM**:

```json
{
  "alert": "Credenciales AWS sospechosas detectadas",
  "indicators": [
    "Acceso desde IP en Rusia (credenciales normalmente usadas en EE.UU.)",
    "Descarga de 2TB de datos de S3 en 1 hora",
    "Acceso a buckets nunca antes accedidos"
  ],
  "actions": [
    "Revocar credenciales inmediatamente",
    "Bloquear IP de origen",
    "Auditar todos los recursos accedidos",
    "Rotar todas las credenciales del equipo",
    "Escanear GitHub en busca de credenciales expuestas"
  ]
}
```

## 4. Sistema de Aprendizaje Continuo

El LLM debe mejorar con cada ataque detectado. Esto se logra mediante un ciclo de retroalimentación:

### Arquitectura del Sistema de Aprendizaje

```
Ataque Detectado
    ↓
Análisis del LLM
    ↓
Acciones Ejecutadas
    ↓
Resultado de las Acciones (éxito/fallo)
    ↓
Almacenamiento en DynamoDB
    ↓
Generación de Nuevo Ejemplo de Entrenamiento
    ↓
Re-entrenamiento Periódico del LLM
    ↓
Modelo Mejorado Desplegado
```

### Implementación del Aprendizaje Continuo

```python
def learn_from_incident(incident_data):
    """
    Genera un nuevo ejemplo de entrenamiento a partir de un incidente real.
    """
    # Extraer información clave
    attack_pattern = incident_data['attack_type']
    indicators = incident_data['iocs']
    actions_taken = incident_data['response_actions']
    effectiveness = incident_data['effectiveness_score']  # 0-100
    
    # Si la respuesta fue efectiva (>80%), agregar al dataset de entrenamiento
    if effectiveness > 80:
        training_example = {
            "prompt": f"Detectado patrón de ataque: {attack_pattern}. Indicadores: {', '.join(indicators)}. ¿Cómo respondo?",
            "completion": f"Acciones recomendadas basadas en incidente exitosamente mitigado:\n" + 
                         "\n".join([f"{i+1}. {action}" for i, action in enumerate(actions_taken)])
        }
        
        # Guardar en S3 para el próximo ciclo de fine-tuning
        s3_client.put_object(
            Bucket='training-data-bucket',
            Key=f'continuous-learning/{datetime.now().isoformat()}.json',
            Body=json.dumps(training_example)
        )
        
        print(f"Nuevo ejemplo de entrenamiento generado y guardado")
    else:
        print(f"Respuesta no fue efectiva ({effectiveness}%), requiere revisión humana")

def trigger_retraining():
    """
    Desencadena un nuevo ciclo de fine-tuning cuando hay suficientes ejemplos nuevos.
    """
    # Contar nuevos ejemplos
    response = s3_client.list_objects_v2(
        Bucket='training-data-bucket',
        Prefix='continuous-learning/'
    )
    
    new_examples_count = response['KeyCount']
    
    # Re-entrenar cada 1000 nuevos ejemplos
    if new_examples_count >= 1000:
        print("Iniciando re-entrenamiento del modelo...")
        
        # Combinar ejemplos antiguos y nuevos
        # Crear nuevo trabajo de fine-tuning en Bedrock
        # Desplegar modelo mejorado
        
        # Limpiar ejemplos procesados
        # ...
```

### Métricas de Mejora Continua

El sistema debe rastrear:

1. **Tiempo de Detección**: ¿Cuánto tarda en detectar un ataque?
2. **Tasa de Falsos Positivos**: ¿Cuántas alertas son falsas alarmas?
3. **Efectividad de Respuesta**: ¿Las acciones tomadas detuvieron el ataque?
4. **Tiempo de Respuesta**: ¿Cuánto tarda en ejecutar contramedidas?

Estas métricas se almacenan en CloudWatch y se usan para evaluar cada nueva versión del modelo.

## 5. Detección y Bloqueo de VPNs/Proxies

Para forzar a los atacantes a usar sus IPs reales, el LLM debe detectar y bloquear VPNs y proxies.

### Técnicas de Detección

```python
import requests

def is_vpn_or_proxy(ip_address):
    """
    Detecta si una IP es de un VPN o proxy conocido.
    """
    # Usar APIs de detección de VPN
    vpn_detection_apis = [
        f"https://vpnapi.io/api/{ip_address}?key=YOUR_API_KEY",
        f"https://proxycheck.io/v2/{ip_address}?key=YOUR_API_KEY",
        f"https://ipqualityscore.com/api/json/ip/YOUR_API_KEY/{ip_address}"
    ]
    
    for api_url in vpn_detection_apis:
        try:
            response = requests.get(api_url, timeout=5)
            data = response.json()
            
            # Cada API tiene su propio formato de respuesta
            if 'vpn' in data and data['vpn'] == True:
                return True
            if 'proxy' in data and data['proxy'] == True:
                return True
                
        except Exception as e:
            print(f"Error consultando API: {e}")
            continue
    
    return False

def block_vpn_traffic():
    """
    Bloquea tráfico de VPNs conocidos en WAF.
    """
    # Obtener listas actualizadas de IPs de VPNs
    vpn_ip_lists = [
        "https://raw.githubusercontent.com/X4BNet/lists_vpn/main/output/vpn/ipv4.txt",
        "https://raw.githubusercontent.com/ejrv/VPNs/master/vpn-ipv4.txt"
    ]
    
    all_vpn_ips = []
    for url in vpn_ip_lists:
        response = requests.get(url)
        ips = response.text.strip().split('\n')
        all_vpn_ips.extend(ips)
    
    # Actualizar IPSet en WAF
    waf_client.update_ip_set(
        Name='BlockedVPNs',
        Scope='REGIONAL',
        Id='vpn-ipset-id',
        Addresses=all_vpn_ips[:10000],  # WAF tiene límite de 10,000 IPs
        LockToken='...'
    )
    
    print(f"Bloqueadas {len(all_vpn_ips)} IPs de VPNs en WAF")
```

## 6. Referencias

- AppSecEngineer. (2023). *AWS Shared Responsibility Model: Capital One Breach Case Study*. Disponible en: https://www.appsecengineer.com/blog/aws-shared-responsibility-model-capital-one-breach-case-study
- Snyk. (2023). *High Profile AWS Breaches: Lessons To Be Learned*. Disponible en: https://snyk.io/blog/aws-security-breaches/
- BlackFog. (n.d.). *AWS Data Breach: Lesson From 4 High Profile Breaches*. Disponible en: https://www.blackfog.com/aws-data-breach/

