_# Documento 4: Encriptación Automática de Datos en AWS

## 1. La Encriptación como Pilar de la Defensa en Profundidad

La encriptación es una de las contramedidas de seguridad más efectivas. Garantiza que, incluso si un atacante logra eludir otras defensas y acceder a los datos, no pueda leerlos ni utilizarlos. En un entorno de nube como AWS, la encriptación debe ser omnipresente, protegiendo los datos en sus tres estados:

-   **Datos en Reposo (Data at Rest)**: Datos almacenados en servicios como Amazon S3, Amazon EBS, Amazon RDS, etc.
-   **Datos en Tránsito (Data in Transit)**: Datos que se mueven entre los servicios de AWS, entre la nube y el entorno on-premise, o entre la nube y los usuarios finales.
-   **Datos en Uso (Data in Use)**: Aunque es un campo más emergente (computación confidencial), nos enfocamos en proteger las claves y los secretos que se utilizan para procesar los datos.

La automatización de la encriptación es crucial para eliminar el error humano y asegurar que las políticas de seguridad se apliquen de manera consistente en toda la infraestructura.

## 2. AWS Key Management Service (KMS) como Base

El servicio central para la gestión de la encriptación en AWS es **AWS Key Management Service (KMS)**. KMS facilita la creación y el control de las claves de encriptación utilizadas para cifrar los datos. Es fundamental entender dos tipos de claves en este contexto:

-   **Customer Master Keys (CMKs)**: Ahora llamadas **KMS keys**. Son las claves que se crean y gestionan en KMS. Nunca abandonan el módulo de hardware de seguridad (HSM) de KMS sin encriptar. Se utilizan para generar, encriptar y desencriptar las Claves de Datos.
-   **Data Keys (Claves de Datos)**: Son las claves que realmente encriptan los datos. Son generadas por KMS a partir de una KMS key. El proceso, conocido como **Envelope Encryption**, funciona así:
    1.  Se solicita a KMS una clave de datos para un conjunto de datos específico.
    2.  KMS devuelve dos versiones de la clave de datos: una en texto plano (para encriptar los datos) y otra encriptada con la KMS key especificada.
    3.  Se utiliza la clave de datos en texto plano para encriptar los datos.
    4.  Se descarta de forma segura la clave de datos en texto plano de la memoria.
    5.  Se almacena la clave de datos encriptada junto con los datos encriptados.

Para desencriptar, el proceso se invierte: se envían los datos encriptados y la clave de datos encriptada a un servicio que tenga acceso a la KMS key. El servicio solicita a KMS que desencripte la clave de datos, y con la clave de datos en texto plano, desencripta los datos.

## 3. El AWS Encryption SDK para la Automatización

Mientras que muchos servicios de AWS ofrecen encriptación del lado del servidor integrada con KMS (como la encriptación de buckets S3), la verdadera automatización a nivel de aplicación se logra con el **AWS Encryption SDK** [6].

El SDK proporciona bibliotecas para varios lenguajes de programación (Python, Java, C++, etc.) que simplifican la implementación de la *envelope encryption* del lado del cliente. Esto significa que los datos se encriptan en la propia aplicación antes de ser enviados a cualquier otro servicio (como S3 o una base de datos).

### Características Clave del AWS Encryption SDK:

-   **Abstracción de la Complejidad**: El desarrollador no necesita ser un experto en criptografía. El SDK maneja las mejores prácticas, como la generación de claves de datos únicas por cada objeto.
-   **Contexto de Encriptación**: Permite asociar un conjunto de pares clave-valor no secretos a los datos encriptados. Este contexto se verifica durante el descifrado, proporcionando una capa adicional de autenticación y control de políticas.
-   **Portabilidad**: El mensaje encriptado que produce el SDK es un formato estandarizado y portátil que contiene tanto los datos cifrados como la clave de datos cifrada, facilitando su almacenamiento y movimiento.
-   **Verificación Formal**: El núcleo del SDK está siendo reescrito en **Dafny**, un lenguaje que permite la verificación formal, demostrando matemáticamente la corrección y seguridad de la implementación [6].

### Ejemplo de Flujo de Encriptación Automática de Archivos:

Imaginemos un escenario donde un usuario sube un archivo a través de una aplicación web que se ejecuta en EC2.

1.  La aplicación en el servidor EC2 recibe el archivo.
2.  La aplicación utiliza el **AWS Encryption SDK** para solicitar una nueva clave de datos a KMS, especificando una KMS key de la aplicación.
3.  El SDK recibe la clave de datos en texto plano y la encriptada.
4.  El SDK encripta el archivo del usuario con la clave de datos en texto plano.
5.  El SDK borra la clave de datos en texto plano de la memoria.
6.  La aplicación sube a un bucket de S3 un único objeto: el archivo encriptado junto con la clave de datos encriptada.

El bucket de S3 puede tener su propia política de encriptación del lado del servidor, pero gracias al SDK, el archivo ya estaba encriptado *antes* de llegar a S3, proporcionando una capa de seguridad adicional y controlada por la aplicación.

## 4. Repositorios de GitHub y Herramientas para la Automatización

Además del SDK oficial, existen varias herramientas y repositorios en GitHub que facilitan la automatización de la encriptación en AWS.

| Herramienta/Repositorio        | URL                                                                       | Descripción                                                                                                                            |
| :----------------------------- | :------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------- |
| **age (FiloSottile/age)**      | https://github.com/FiloSottile/age                                        | Una herramienta de encriptación de archivos simple, moderna y segura. Puede ser automatizada en scripts para encriptar artefactos o backups. |
| **sops (getsops/sops)**        | https://github.com/getsops/sops                                           | Un editor de archivos encriptados que soporta YAML, JSON, ENV, etc. Se integra con AWS KMS para gestionar secretos en repositorios de Git. |
| **aws-volume-encryption**      | https://github.com/acwwat/aws-volume-encryption                           | Un script de Python que automatiza la (re)encriptación de volúmenes EBS que están adjuntos a una instancia EC2.                       |
| **aws-samples/aws-system-manager-automation-unencrypted-to-encrypted-resources** | https://github.com/aws-samples/aws-system-manager-automation-unencrypted-to-encrypted-resources | Documentos de automatización de AWS Systems Manager para remediar automáticamente recursos no encriptados, como volúmenes EBS.          |

### Estrategia de Implementación:

1.  **Encriptación por Defecto**: Habilitar la encriptación por defecto en todos los servicios de AWS que lo soporten (e.g., para nuevos volúmenes EBS y buckets S3).
2.  **Remediación Automática**: Utilizar AWS Config y AWS Systems Manager para detectar recursos existentes no encriptados y aplicar la encriptación automáticamente.
3.  **Encriptación a Nivel de Aplicación**: Para datos altamente sensibles, utilizar el **AWS Encryption SDK** dentro de las aplicaciones para implementar la encriptación del lado del cliente.
4.  **Gestión de Secretos**: Utilizar **sops** para gestionar de forma segura los secretos de configuración (como claves de API, contraseñas de bases de datos) en los repositorios de código, encriptándolos con KMS.
5.  **Automatización de Scripts**: Integrar herramientas como **age** en los pipelines de CI/CD para encriptar automáticamente los artefactos de construcción o los backups antes de almacenarlos.

## 5. Referencias

[6] AWS. (n.d.). *AWS Encryption SDK*. GitHub. Disponible en: https://github.com/aws/aws-encryption-sdk

