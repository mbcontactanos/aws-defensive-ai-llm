# Documento 3: Defensa Activa, Análisis Forense y Contramedidas

## 1. De la Reacción a la Proacción: La Filosofía de la Defensa Activa

La ciberseguridad tradicional se ha centrado en la defensa pasiva: construir muros más altos (firewalls), cerrar puertas (hardening) y esperar a que un atacante falle. La **Defensa Activa** cambia este paradigma. En lugar de esperar pasivamente, se adoptan medidas proactivas para engañar, confundir, ralentizar y estudiar a los atacantes. Este enfoque nos permite transformar un ataque de ser un riesgo puro a ser una oportunidad de inteligencia.

Este documento traduce conceptos como "responder con virus" o "encontrar al hacker" en técnicas profesionales y éticas de ciberseguridad.

-   **"Responder con Virus" ↔️ Técnicas de Engaño y Disuasión**: No se lanzan programas maliciosos contra el atacante, lo cual es ilegal y contraproducente. En su lugar, se despliegan sistemas de engaño (*honeypots*, *tarpits*) que simulan ser sistemas valiosos pero vulnerables. El objetivo es atraer al atacante, hacerle perder tiempo y revelar sus herramientas y métodos en un entorno controlado.

-   **"Encontrar al Hacker" ↔️ Análisis Forense Digital y Atribución**: La identificación de un atacante no es una tarea de "rastreo de IP" en tiempo real como en las películas. Es un meticuloso proceso de **Análisis Forense Digital y Respuesta a Incidentes (DFIR)**, donde se recolecta, preserva y analiza evidencia digital para reconstruir las acciones del atacante y, si es posible, atribuir el ataque.

-   **"Tumbar IPs" ↔️ Contramedidas Automatizadas**: La acción de "tumbar" una IP se implementa como una contramedida defensiva, donde las direcciones IP identificadas como maliciosas son bloqueadas automáticamente en los puntos de control de la red (WAF, Network Firewalls, NACLs) para neutralizar la amenaza activa.

## 2. Implementación de Técnicas de Engaño (Deception Technology)

El repositorio **Awesome Active Defense** [5] ofrece una lista exhaustiva de herramientas para implementar estas técnicas.

### Tabla de Herramientas de Defensa Activa

| Técnica          | Herramienta Sugerida | Propósito                                                                                                                            |
| :--------------- | :------------------- | :----------------------------------------------------------------------------------------------------------------------------------- |
| **Honeypots**      | `Cowrie`             | Simula un servidor SSH/Telnet vulnerable. Atrae a los atacantes que buscan acceso por fuerza bruta y registra sus comandos y payloads. |
| **Honey Tokens**   | `CanaryTokens`       | Crea "archivos trampa" (e.g., un PDF, un documento de Word, credenciales de AWS falsas) que envían una alerta cuando son abiertos o utilizados. |
| **Tarpits**        | `PHP-HTTP-Tarpit`    | Ralentiza a los escáneres y spiders web maliciosos, haciéndoles perder tiempo y recursos al responder muy lentamente.                |
| **Port Deception** | `Portspoof`          | Hace que todos los puertos de un sistema parezcan abiertos, confundiendo y ralentizando enormemente la fase de reconocimiento del atacante. |

El despliegue de estas herramientas alimenta directamente a nuestro LLM. Por ejemplo, una alerta de `CanaryTokens` indicando que un documento llamado `Q4-Financial-Projections.docx` ha sido abierto desde una IP en un país inesperado, es una señal de altísima fidelidad de una brecha de datos, permitiendo una respuesta inmediata y dirigida.

## 3. El Proceso de Análisis Forense Digital (DFIR)

Cuando se detecta un incidente grave, se activa el proceso de DFIR. El objetivo es responder a las preguntas clave: ¿quién?, ¿qué?, ¿cuándo?, ¿dónde? y ¿cómo? El repositorio **Awesome Incident Response** [3] es una mina de oro de herramientas para este fin.

### Fases del Proceso DFIR

1.  **Preparación**: Tener las herramientas y el personal listos antes de que ocurra un incidente. Esto incluye tener roles definidos y playbooks pre-aprobados.

2.  **Identificación**: Confirmar que un incidente ha ocurrido. Aquí es donde el LLM, al correlacionar alertas, juega un papel crucial.

3.  **Contención**: Limitar el daño. Esto puede ser a corto plazo (ej. aislar una máquina de la red) y a largo plazo (ej. parchear la vulnerabilidad explotada).

4.  **Erradicación**: Eliminar la causa raíz del incidente, como el malware o la cuenta de usuario comprometida.

5.  **Recuperación**: Restaurar los sistemas a su estado normal de operación de forma segura.

6.  **Lecciones Aprendidas**: Analizar el incidente y la respuesta para mejorar la postura de seguridad futura. Los resultados de este análisis deben usarse para actualizar el dataset de entrenamiento del LLM.

### Recolección de Evidencia en AWS

Para el análisis, es vital recolectar artefactos forenses. Herramientas como **CyLR** o **Live Response Collection** [3] pueden ser automatizadas a través de AWS Systems Manager Agent para recolectar datos de instancias EC2 comprometidas:

-   **Imágenes de Memoria (RAM)**: Para analizar procesos en ejecución y conexiones de red en el momento del ataque.
-   **Imágenes de Disco (EBS Snapshots)**: Para un análisis completo del sistema de archivos, buscando malware, herramientas del atacante y archivos modificados.
-   **Logs**: VPC Flow Logs, CloudTrail Logs, logs de aplicaciones, etc.
-   **Artefactos del Sistema**: $MFT (en Windows), `bash_history` (en Linux), Prefetch files, etc.

Una vez recolectada, esta evidencia se analiza en un entorno de laboratorio seguro (una "clean room" en una VPC separada) para reconstruir la línea de tiempo del ataque y extraer Indicadores de Compromiso (IOCs).

## 4. Contraataque y Atribución Ética

El sistema **IDCAS (Intrusion Detection and Counter Attack System)** [4] demuestra un concepto interesante: la detección de un patrón de ataque y su replicación. En un contexto de defensa empresarial, no replicamos el ataque a otros, sino que usamos ese patrón para:

1.  **Crear una Firma de Detección**: El patrón del ataque (ej. una secuencia específica de llamadas a una API, un payload en una petición HTTP) se convierte en una regla de detección personalizada para el WAF, el IDS o las reglas de GuardDuty.

2.  **Automatizar el Bloqueo**: El LLM, al identificar el patrón, instruye a AWS Lambda para que bloquee la IP de origen en todos los puntos de control de la red.

3.  **Threat Hunting Proactivo**: El patrón se utiliza para buscar de forma proactiva en los logs históricos de toda la infraestructura si el mismo ataque ha ocurrido antes sin ser detectado.

La **atribución**, o identificar al actor detrás del teclado, es extremadamente difícil. Sin embargo, al analizar las herramientas, la infraestructura y los TTPs (Tácticas, Técnicas y Procedimientos) del atacante a través del análisis forense, se puede obtener inteligencia valiosa para comparar con informes de inteligencia de amenazas y potencialmente identificar al grupo de actores responsable.

## 5. Referencias

[3] Meir, M. (n.d.). *Awesome Incident Response*. GitHub. Disponible en: https://github.com/meirwah/awesome-incident-response

[4] Magnani, S. (2024). *IDCAS - Intrusion Detection and Counter Attack System*. GitHub. Disponible en: https://github.com/s41m0n/idcas

[5] Konsela, B. (n.d.). *Awesome Active Defense*. GitHub. Disponible en: https://github.com/adhdproject/awesome-active-defense

