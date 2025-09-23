# 🚀 GitHub Actions Workflow

Este directorio contiene el workflow de GitHub Actions para automatizar el despliegue del sistema de transcripción de audio en Azure VM usando Azure Key Vault.

## 📋 **Workflow Disponible**

### **`deploy.yml` - Despliegue Automático**
- **Trigger**: 
  - Push a `main`
  - Manual (`workflow_dispatch`)
- **Propósito**: Desplegar cambios automáticamente a la VM usando Azure Key Vault
- **Funciones**:
  - Obtener clave SSH desde Azure Key Vault
  - Detener contenedores existentes
  - Actualizar código desde GitHub
  - Reconstruir y ejecutar con GPU
  - Verificar estado del despliegue

**Uso:**
```bash
# Automático al hacer push
git push origin main

# Manual desde GitHub Actions
# Actions → Deploy to Azure VM → Run workflow
```

## 🔐 **Secrets Requeridos**

Configura estos secrets en tu repositorio GitHub:

### **Azure Authentication:**
- `AZURE_CLIENT_ID`: ID del cliente de Azure
- `AZURE_CLIENT_SECRET`: Secreto del cliente de Azure
- `AZURE_TENANT_ID`: ID del tenant de Azure
- `AZURE_SUBSCRIPTION_ID`: ID de la suscripción de Azure

### **Key Vault Configuration:**
- `SSH_KEY_SECRET_NAME`: Nombre del secret que contiene la clave SSH
- `RESOURCE_GROUP_NAME`: Nombre del grupo de recursos

**Nota**: El workflow detecta automáticamente:
- VMs que coincidan con el patrón `tvc-audio2text-*-kv`
- Key Vault en el mismo grupo de recursos

## 🚀 **Flujo de Trabajo**

### **Paso 1: Configuración Inicial**
1. Configurar secrets en GitHub
2. Crear VM manualmente en Azure
3. Configurar variables de entorno en la VM

### **Paso 2: Desarrollo y Deploy**
1. Hacer cambios en el código
2. Hacer push a `main` (deploy automático)
3. Verificar logs en GitHub Actions

## 🔧 **Configuración Avanzada**

### **Personalizar Workflow:**
```yaml
# Cambiar tamaño de VM
vm_size: 'Standard_NC4as_T4_v3'  # T4 GPU
```

### **Variables de Entorno:**
```yaml
env:
  WHISPER_MODEL: 'large'
  DB_HOST: 'tu-host-mysql'
  DB_USER: 'tu-usuario'
```

## 📞 **Soporte**

- **Documentación**: [README.md](../README.md)
- **Deploy Manual**: [DEPLOYMENT.md](../DEPLOYMENT.md)
- **Issues**: [GitHub Issues](https://github.com/TVC-mx/python-audio-to-text/issues)

---

**¡Automatización completa para tu sistema de transcripción! 🎵🤖**
