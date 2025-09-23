# 🚀 Deploy en Azure VM - Guía Completa

## 📋 **Resumen del Deploy**

Este documento explica cómo deployar el sistema de transcripción de audio en una VM de Azure optimizada para GPU.

## 🎯 **Opciones de VM Recomendadas**

### **1. NC6s_v3 (NVIDIA Tesla V100) - RECOMENDADA**
- **Especificaciones**: 6 vCPUs, 112GB RAM, 1x V100 GPU
- **Costo**: ~$3.20/hora
- **Rendimiento**: 5-8x más rápido que CPU
- **Tiempo estimado**: 3-4 días para 9,922 archivos
- **Costo total**: ~$230-300

### **2. NC4as_T4_v3 (NVIDIA Tesla T4) - ALTERNATIVA**
- **Especificaciones**: 4 vCPUs, 28GB RAM, 1x T4 GPU
- **Costo**: ~$2.50/hora
- **Rendimiento**: 3-5x más rápido que CPU
- **Tiempo estimado**: 5-6 días para 9,922 archivos
- **Costo total**: ~$300-360

## 🚀 **Deploy Directo con Azure CLI**

### **Paso 1: Crear VM con GPU**
```bash
# Crear grupo de recursos
az group create --name python-audio-to-text-rg --location eastus

# Crear VM con GPU
az vm create \
    --resource-group python-audio-to-text-rg \
    --name audio-transcription-vm \
    --image Ubuntu2204 \
    --size Standard_NC6s_v3 \
    --admin-username azureuser \
    --generate-ssh-keys \
    --public-ip-sku Standard \
    --storage-sku Premium_LRS \
    --os-disk-size-gb 100

# Abrir puerto SSH
az vm open-port --resource-group python-audio-to-text-rg --name audio-transcription-vm --port 22
```

### **Paso 2: Configurar VM**
```bash
# Conectarse a la VM
ssh azureuser@<IP_PUBLICA>

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar NVIDIA Docker
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# Instalar drivers NVIDIA
sudo apt install -y nvidia-driver-470
sudo reboot
```

### **Paso 3: Clonar y Configurar Proyecto**
```bash
# Clonar repositorio
git clone https://github.com/TVC-mx/python-audio-to-text.git
cd python-audio-to-text

# Configurar variables de entorno
cp env.example .env
nano .env

# Configurar:
DB_HOST=tu_host_mysql
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=tu_base_datos
WHISPER_MODEL=large

# Crear directorios
mkdir -p audios textos logs
```

### **Paso 4: Ejecutar Transcripción**
```bash
# Ejecutar con GPU
docker-compose -f azure-gpu-optimized.yml up --build
```

## 🔧 **Deploy con Azure Portal**

### **Paso 1: Crear VM en Azure Portal**
1. Ir a Azure Portal
2. Crear nueva VM
3. Seleccionar imagen: Ubuntu 22.04 LTS
4. Tamaño: Standard_NC6s_v3
5. Configurar SSH key
6. Crear VM

### **Paso 2: Conectarse y Configurar**
```bash
# Conectarse
ssh azureuser@<IP_PUBLICA>

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar NVIDIA Docker
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# Instalar drivers NVIDIA
sudo apt install -y nvidia-driver-470
sudo reboot
```

### **Paso 3: Clonar y Configurar Proyecto**
```bash
# Clonar repositorio
git clone https://github.com/TVC-mx/python-audio-to-text.git
cd python-audio-to-text

# Configurar variables
cp env.example .env
nano .env

# Crear directorios
mkdir -p audios textos logs
```

### **Paso 4: Ejecutar con GPU**
```bash
# Ejecutar transcripción
docker-compose -f azure-gpu-optimized.yml up --build
```

## 📊 **Monitoreo y Optimización**

### **Comandos de Monitoreo**
```bash
# Estado GPU
nvidia-smi

# Estado Docker
docker ps
docker logs audio-transcription-gpu

# Uso de recursos
htop

# Estado del sistema
free -h
df -h
```

### **Optimizaciones**
- **Spot Instances**: 60-80% descuento
- **Procesamiento en lotes**: Encender/apagar VM
- **Modelo 'medium'**: Más rápido que 'large'
- **Paralelización**: Múltiples contenedores

## 💰 **Estrategias de Ahorro**

### **1. Spot Instances**
```bash
# Crear VM con Spot
az vm create \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --image "Ubuntu2204" \
    --size $VM_SIZE \
    --priority Spot \
    --max-price -1
```

### **2. Procesamiento en Lotes**
```bash
# Procesar por lotes
for date in 2024-01-01 2024-01-02 2024-01-03; do
    echo "Procesando $date..."
    docker-compose -f azure-gpu-optimized.yml run --rm audio-transcription python main.py --start-date $date --end-date $date
done
```

### **3. Auto-apagado**
```bash
# Configurar auto-apagado después de completar
echo "sudo shutdown -h +60" | at now
```

## 🔒 **Seguridad**

### **Configuración de Red**
```bash
# Solo permitir SSH
az vm open-port \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --port 22 \
    --priority 1000
```

### **Backup de Datos**
```bash
# Backup automático
rsync -av /home/azureuser/python-audio-to-text/ /mnt/backup/
```

## 📈 **Escalabilidad**

### **Múltiples VMs**
```bash
# Crear múltiples VMs para procesamiento paralelo
for i in {1..3}; do
    az vm create \
        --resource-group $RESOURCE_GROUP \
        --name "audio-vm-$i" \
        --image "Ubuntu2204" \
        --size "Standard_NC6s_v3"
done
```

### **Load Balancer**
```bash
# Configurar load balancer para distribución
az network lb create \
    --resource-group $RESOURCE_GROUP \
    --name audio-lb \
    --sku Standard
```

## 🚨 **Troubleshooting**

### **Problemas Comunes**
1. **GPU no detectada**: Verificar drivers NVIDIA
2. **Memoria insuficiente**: Reducir modelo Whisper
3. **Conexión DB**: Verificar firewall y credenciales
4. **Docker GPU**: Verificar nvidia-docker2

### **Logs y Debugging**
```bash
# Ver logs detallados
docker logs audio-transcription-gpu -f

# Debug GPU
nvidia-smi -l 1

# Debug Docker
docker system df
docker system prune
```

## 📞 **Soporte**

- **Documentación**: [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/TVC-mx/python-audio-to-text/issues)
- **Comunidad**: [TVC-mx](https://github.com/TVC-mx)

---

**¡Tu sistema está listo para procesar audio con GPU en Azure! 🎵🚀**
