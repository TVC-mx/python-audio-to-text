# 🚀 GitHub Actions Workflows

Este directorio contiene los workflows de GitHub Actions para automatizar el despliegue y monitoreo del sistema de transcripción de audio en Azure VM.

## 📋 **Workflows Disponibles**

### **1. `setup-vm.yml` - Configuración Inicial de VM**
- **Trigger**: Manual (`workflow_dispatch`)
- **Propósito**: Crear y configurar una nueva VM en Azure
- **Funciones**:
  - Crear grupo de recursos
  - Crear VM con GPU
  - Instalar Docker y drivers NVIDIA
  - Configurar soporte para GPU
  - Verificar configuración

**Uso:**
```bash
# Ejecutar desde GitHub Actions
# Actions → Setup Azure VM → Run workflow
```

### **2. `deploy.yml` - Despliegue Automático**
- **Trigger**: 
  - Push a `main`
  - Manual (`workflow_dispatch`)
- **Propósito**: Desplegar cambios automáticamente a la VM usando Key Vault
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

### **3. `monitor.yml` - Monitoreo Automático**
- **Trigger**: 
  - Cada 6 horas (`cron: '0 */6 * * *'`)
  - Manual (`workflow_dispatch`)
- **Propósito**: Monitorear el estado de la VM y procesamiento
- **Funciones**:
  - Verificar estado del sistema
  - Monitorear uso de GPU
  - Verificar estado de Docker
  - Generar reportes de monitoreo

**Uso:**
```bash
# Automático cada 6 horas
# Manual desde GitHub Actions
# Actions → Monitor Azure VM → Run workflow
```

### **4. `cleanup.yml` - Gestión de Recursos**
- **Trigger**: Manual (`workflow_dispatch`)
- **Propósito**: Gestionar recursos de Azure
- **Funciones**:
  - Detener VM (ahorro de costos)
  - Iniciar VM
  - Reiniciar VM
  - Eliminar VM y recursos

**Uso:**
```bash
# Manual desde GitHub Actions
# Actions → Cleanup Azure Resources → Run workflow
```

## 🔐 **Secrets Requeridos**

Configura estos secrets en tu repositorio GitHub:

### **Azure Authentication:**
- `AZURE_CLIENT_ID`: ID del cliente de Azure
- `AZURE_CLIENT_SECRET`: Secreto del cliente de Azure
- `AZURE_TENANT_ID`: ID del tenant de Azure
- `AZURE_SUBSCRIPTION_ID`: ID de la suscripción de Azure

### **SSH Access:**
- `SSH_PRIVATE_KEY`: Clave privada SSH para acceder a la VM

## 🚀 **Flujo de Trabajo Recomendado**

### **Paso 1: Configuración Inicial**
1. Configurar secrets en GitHub
2. Ejecutar `setup-vm.yml` para crear VM
3. Configurar variables de entorno en la VM

### **Paso 2: Desarrollo y Deploy**
1. Hacer cambios en el código
2. Hacer push a `main` (deploy automático)
3. Monitorear con `monitor.yml`

### **Paso 3: Gestión de Costos**
1. Usar `cleanup.yml` para detener VM cuando no se use
2. Usar `cleanup.yml` para iniciar VM cuando se necesite
3. Monitorear costos en Azure Portal

## 📊 **Monitoreo y Alertas**

### **Métricas Monitoreadas:**
- Uso de CPU
- Uso de RAM
- Uso de GPU
- Estado de Docker
- Archivos procesados
- Errores en logs

### **Alertas Automáticas:**
- VM no disponible
- Contenedor falló
- Errores en procesamiento
- Recursos agotados

## 🔧 **Configuración Avanzada**

### **Personalizar Workflows:**
```yaml
# Cambiar frecuencia de monitoreo
schedule:
  - cron: '0 */2 * * *'  # Cada 2 horas

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
