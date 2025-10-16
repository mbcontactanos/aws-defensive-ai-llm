# Repositorio de Documentación: IA Defensiva para AWS

**ADVERTENCIA:** Este repositorio y su contenido se proporcionan únicamente con fines educativos y de investigación en el ámbito de la ciberseguridad defensiva. El uso de estas técnicas para actividades maliciosas, ataques no autorizados o cualquier otra acción ilegal está estrictamente prohibido. Los autores no asumen ninguna responsabilidad por el mal uso de la información aquí contenida.

## Filosofía del Proyecto

Este proyecto tiene como objetivo documentar la creación de un sistema de seguridad inteligente y adaptativo para entornos de AWS, utilizando un Modelo de Lenguaje Grande (LLM) como núcleo de orquestación y decisión. La filosofía se basa en una **defensa proactiva y en profundidad**, que no solo reacciona a las amenazas, sino que también las anticipa, las engaña y aprende de ellas.

Se abordan conceptos solicitados como "respuesta con virus" y "tumbar IPs" desde una perspectiva ética y legal, traduciéndolos a técnicas de ciberseguridad profesionales:

- **Respuesta con "Virus"**: Se implementa como **Defensa Activa**, utilizando herramientas como *honeypots*, *tarpits* y *canary tokens* para engañar, ralentizar, y obtener inteligencia sobre los atacantes.
- **Encontrar al Hacker**: Se aborda mediante **Análisis Forense Digital (DFIR)** y técnicas de **Atribución**, recolectando y analizando evidencia para identificar el origen y los métodos del ataque.
- **Tumbar IPs**: Se traduce en **Contramedidas Defensivas Automatizadas**, como el bloqueo dinámico y automático de direcciones IP maliciosas en Firewalls de Aplicaciones Web (WAF), Network Firewalls y listas de control de acceso (ACLs).

## Estructura del Repositorio

El repositorio está organizado en las siguientes carpetas principales:

- `/docs`: Contiene toda la documentación detallada del proyecto, desde la arquitectura hasta los manuales de uso.
- `/terraform`: Incluye código de Infraestructura como Código (IaC) para desplegar la arquitectura base en AWS.
- `/scripts`: Scripts de automatización (Python, Bash) para tareas de recolección, análisis y respuesta.
- `/llm-training-data`: Ejemplos de datasets sintéticos para el entrenamiento y ajuste fino del LLM.
- `/active-defense`: Configuraciones y guías para desplegar herramientas de defensa activa como honeypots.

## Contenido de la Documentación

La documentación principal se encuentra en la carpeta `/docs` y está dividida en los siguientes módulos:

1.  **Introducción y Filosofía**: Este mismo documento.
2.  **Arquitectura de Seguridad en AWS**: Detalla la arquitectura de referencia, los servicios de AWS implicados y cómo se integran siguiendo el framework NIST (Identify, Protect, Detect, Respond, Recover).
3.  **Entrenamiento del LLM para Ciberseguridad**: Guía sobre cómo preparar y entrenar un LLM para que actúe como un analista de seguridad, generando playbooks de respuesta, interactuando con APIs de AWS y tomando decisiones basadas en la evidencia.
4.  **Defensa Activa y Análisis Forense**: Manual de uso de técnicas de engaño y herramientas forenses para la recolección de inteligencia y la atribución de ataques.
5.  **Encriptación Automática de Datos**: Guía para implementar la encriptación automática de archivos y datos en reposo y en tránsito utilizando el AWS Encryption SDK.
6.  **Manual de Seguridad de AWS**: Un compendio de las mejores prácticas de seguridad recomendadas por AWS para la configuración y mantenimiento de la infraestructura.

Para comenzar, se recomienda leer la documentación en el orden presentado.

