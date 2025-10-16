# Defensa Activa: Guías de Implementación

Esta carpeta contiene guías y configuraciones para desplegar herramientas de **Defensa Activa** en su entorno de AWS. Estas técnicas están diseñadas para engañar, ralentizar y recolectar inteligencia sobre los atacantes.

## ⚠️ Advertencia Legal

Las herramientas y técnicas de defensa activa deben ser utilizadas **únicamente dentro de su propia infraestructura** y con fines defensivos. El uso de estas técnicas contra sistemas de terceros sin autorización es ilegal y puede constituir un delito. Consulte siempre con su equipo legal antes de implementar estas medidas.

## Herramientas Recomendadas

### 1. Cowrie - Honeypot SSH/Telnet

**Cowrie** es un honeypot de interacción media-alta que simula un servidor SSH y Telnet. Registra todos los intentos de inicio de sesión, los comandos ejecutados por el atacante y los archivos que intenta descargar.

**Repositorio:** https://github.com/cowrie/cowrie

**Caso de Uso:**
- Detectar intentos de acceso por fuerza bruta a SSH.
- Recolectar malware que los atacantes intentan desplegar.
- Estudiar las técnicas y herramientas de los atacantes.

**Despliegue en AWS:**
1. Lanzar una instancia EC2 pequeña (t3.micro) en una subred pública.
2. Configurar el Security Group para permitir tráfico SSH (puerto 22) desde cualquier lugar (0.0.0.0/0).
3. Instalar Cowrie siguiendo la documentación oficial.
4. Configurar Cowrie para que escuche en el puerto 22 (o redirigir el tráfico del puerto 22 al puerto de Cowrie).
5. Integrar los logs de Cowrie con CloudWatch Logs para análisis centralizado.

**Integración con el LLM:**
Los logs de Cowrie pueden ser analizados por el LLM para identificar patrones de ataque, extraer Indicadores de Compromiso (IOCs) y generar reportes de inteligencia de amenazas.

---

### 2. CanaryTokens - Tokens de Alerta Temprana

**CanaryTokens** son archivos, URLs o credenciales "trampa" que envían una alerta cuando son accedidos. Son extremadamente efectivos para detectar brechas de datos y movimiento lateral dentro de una red.

**Servicio Web:** https://canarytokens.org (Gratuito)
**Repositorio (Auto-hospedado):** https://github.com/thinkst/canarytokens

**Tipos de Tokens:**
- **Documentos de Office/PDF**: Archivos que envían una alerta cuando se abren.
- **Credenciales AWS**: Claves de acceso falsas que alertan cuando se usan.
- **URLs**: Enlaces que alertan cuando se visitan.
- **Clonación de Sitios Web**: Páginas web falsas que alertan cuando se acceden.

**Caso de Uso:**
- Colocar un documento PDF llamado "Confidential-Q4-Financials.pdf" en un bucket de S3 que simula ser un almacén de datos corporativos. Si un atacante accede al bucket y abre el PDF, recibe una alerta inmediata.
- Crear credenciales de AWS falsas y dejarlas en un repositorio de código o en un archivo de configuración. Si se utilizan, se recibe una alerta.

**Integración con el LLM:**
Las alertas de CanaryTokens son de altísima fidelidad (muy pocos falsos positivos). El LLM puede usar estas alertas para desencadenar una respuesta inmediata y agresiva, como aislar la subred, revocar todas las credenciales y activar el proceso de respuesta a incidentes.

---

### 3. Portspoof - Emulación de Servicios en Todos los Puertos

**Portspoof** hace que todos los puertos de un sistema parezcan abiertos y ejecutando servicios. Esto confunde enormemente a los atacantes durante la fase de reconocimiento, haciéndoles perder tiempo y recursos.

**Repositorio:** https://github.com/drk1wi/portspoof

**Caso de Uso:**
- Desplegar en una instancia EC2 "señuelo" que no tiene ningún servicio real.
- Los escáneres de puertos del atacante reportarán miles de puertos abiertos, haciendo que el análisis sea extremadamente lento y confuso.

**Despliegue en AWS:**
1. Lanzar una instancia EC2 en una subred pública.
2. Configurar el Security Group para permitir todo el tráfico entrante (para fines de demostración).
3. Instalar y ejecutar Portspoof.
4. Monitorear las conexiones entrantes para identificar intentos de escaneo.

---

### 4. Weblabyrinth - Laberinto de Páginas Web

**Weblabyrinth** crea un laberinto infinito de páginas web falsas para confundir y atrapar a los web crawlers y scrapers maliciosos.

**Repositorio:** https://github.com/adhdproject/weblabyrinth

**Caso de Uso:**
- Proteger aplicaciones web contra scrapers de contenido y bots maliciosos.
- Hacer que los atacantes pierdan tiempo navegando por páginas falsas.

---

## Mejores Prácticas

1. **Aislamiento**: Despliegue los honeypots en subredes aisladas con acceso limitado al resto de la infraestructura.
2. **Monitorización**: Integre todos los logs de las herramientas de defensa activa con CloudWatch y Security Hub.
3. **Análisis con IA**: Utilice el LLM para analizar los datos recolectados por los honeypots y extraer inteligencia accionable.
4. **Rotación**: Cambie periódicamente las direcciones IP y las configuraciones de los honeypots para evitar que sean identificados y evitados por los atacantes.

## Referencias

- Konsela, B. (n.d.). *Awesome Active Defense*. GitHub. Disponible en: https://github.com/adhdproject/awesome-active-defense

