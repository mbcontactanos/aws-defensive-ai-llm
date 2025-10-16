#!/usr/bin/env python3
"""
Script de Automatización: Bloqueo de IP Maliciosa en AWS WAF

Este script demuestra cómo bloquear automáticamente una dirección IP maliciosa
en AWS WAF cuando se detecta una amenaza. Está diseñado para ser invocado por
una función AWS Lambda en respuesta a una alerta de GuardDuty o Security Hub.

Requisitos:
    - boto3 (AWS SDK para Python)
    - Permisos IAM para actualizar IPSets en WAFv2

Uso:
    python3 block_malicious_ip.py --ip 198.51.100.10 --ipset-name BlockedIPs --ipset-id <ID> --scope REGIONAL

Autor: Manus AI
Licencia: MIT
"""

import boto3
import argparse
import sys
from botocore.exceptions import ClientError

def get_ipset_lock_token(wafv2_client, ipset_name, ipset_id, scope):
    """
    Obtiene el LockToken actual del IPSet, necesario para actualizarlo.
    
    Args:
        wafv2_client: Cliente boto3 de WAFv2
        ipset_name: Nombre del IPSet
        ipset_id: ID del IPSet
        scope: Ámbito del IPSet (REGIONAL o CLOUDFRONT)
    
    Returns:
        tuple: (lock_token, current_addresses)
    """
    try:
        response = wafv2_client.get_ip_set(
            Name=ipset_name,
            Scope=scope,
            Id=ipset_id
        )
        return response['LockToken'], response['IPSet']['Addresses']
    except ClientError as e:
        print(f"Error al obtener el IPSet: {e}")
        sys.exit(1)

def block_ip_in_waf(ip_address, ipset_name, ipset_id, scope='REGIONAL', region='us-east-1'):
    """
    Añade una dirección IP a un IPSet de AWS WAF para bloquearla.
    
    Args:
        ip_address: Dirección IP a bloquear (formato CIDR, ej. 198.51.100.10/32)
        ipset_name: Nombre del IPSet en WAF
        ipset_id: ID del IPSet en WAF
        scope: REGIONAL o CLOUDFRONT
        region: Región de AWS (solo para REGIONAL)
    
    Returns:
        bool: True si se bloqueó exitosamente, False en caso contrario
    """
    # Asegurar formato CIDR
    if '/' not in ip_address:
        ip_address = f"{ip_address}/32"
    
    # Crear cliente de WAFv2
    if scope == 'CLOUDFRONT':
        wafv2_client = boto3.client('wafv2', region_name='us-east-1')  # CloudFront siempre usa us-east-1
    else:
        wafv2_client = boto3.client('wafv2', region_name=region)
    
    # Obtener el estado actual del IPSet
    lock_token, current_addresses = get_ipset_lock_token(wafv2_client, ipset_name, ipset_id, scope)
    
    # Verificar si la IP ya está bloqueada
    if ip_address in current_addresses:
        print(f"La IP {ip_address} ya está bloqueada en el IPSet '{ipset_name}'.")
        return True
    
    # Añadir la nueva IP a la lista
    updated_addresses = current_addresses + [ip_address]
    
    # Actualizar el IPSet
    try:
        wafv2_client.update_ip_set(
            Name=ipset_name,
            Scope=scope,
            Id=ipset_id,
            Addresses=updated_addresses,
            LockToken=lock_token
        )
        print(f"✅ IP {ip_address} bloqueada exitosamente en el IPSet '{ipset_name}'.")
        return True
    except ClientError as e:
        print(f"❌ Error al bloquear la IP: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Bloquea una dirección IP maliciosa en AWS WAF.'
    )
    parser.add_argument('--ip', required=True, help='Dirección IP a bloquear')
    parser.add_argument('--ipset-name', required=True, help='Nombre del IPSet en WAF')
    parser.add_argument('--ipset-id', required=True, help='ID del IPSet en WAF')
    parser.add_argument('--scope', default='REGIONAL', choices=['REGIONAL', 'CLOUDFRONT'],
                        help='Ámbito del IPSet (REGIONAL o CLOUDFRONT)')
    parser.add_argument('--region', default='us-east-1', help='Región de AWS (para REGIONAL)')
    
    args = parser.parse_args()
    
    print(f"🔒 Iniciando bloqueo de IP: {args.ip}")
    success = block_ip_in_waf(
        ip_address=args.ip,
        ipset_name=args.ipset_name,
        ipset_id=args.ipset_id,
        scope=args.scope,
        region=args.region
    )
    
    if success:
        print("✅ Operación completada exitosamente.")
        sys.exit(0)
    else:
        print("❌ La operación falló.")
        sys.exit(1)

if __name__ == '__main__':
    main()

