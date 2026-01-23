### Ver version de la imagen de n8n
```
docker exec -it n8n n8n --version
```

### Generar token
```
openssl rand -hex 32
```
### Crear  N8N_RUNNERS_AUTH_TOKEN
<!-- Docker Compose NO lee automáticamente tu ~/.zshrc.
👉 ~/.zshrc solo se carga cuando:
abres una terminal interactiva
o haces source ~/.zshrc
Pero docker compose:
se ejecuta en un proceso no interactivo
no hereda esas variables si no están exportadas en la sesión actual -->
```
vim ~/.zshrc
export N8N_RUNNERS_AUTH_TOKEN=6d49b678d21d295738d69790dba77026b0d6a7c03d030e987ac0f2ab1531018a
```
### Refrescar ~/.zshrc
```
source ~/.zshrc
```

### Verificar Token
```
echo $N8N_RUNNERS_AUTH_TOKEN
```

### Instalar el contenedor de N8N
```
docker run -d \
  --name n8n \
  --network n8n_net \
  -p 5678:5678 \
  -e N8N_RUNNERS_ENABLED=true \
  -e N8N_RUNNERS_MODE=external \
  -e N8N_RUNNERS_BROKER_LISTEN_ADDRESS=0.0.0.0 \
  -e N8N_RUNNERS_AUTH_TOKEN=$N8N_RUNNERS_AUTH_TOKEN \
  -e N8N_EXECUTE_COMMAND_ALLOW=true \
  -v n8n_data:/home/node/.n8n \
  -v ~/Sites/n8n/n8n-python/eliminar-duplicados:/files \
  docker.n8n.io/n8nio/n8n:latest
```

### Instalar el contenedor de runner
```
docker run -d \
  --name n8n-runners \
  --network n8n_net \
  -e N8N_RUNNERS_AUTH_TOKEN=$N8N_RUNNERS_AUTH_TOKEN \
  -e N8N_RUNNERS_TASK_BROKER_URI=http://n8n:5679 \
  n8nio/runners:2.3.2
```

### Ver logs de runners y n8n 
```
docker logs n8n
docker logs n8n-runners
```

### Verificar imagenes descargadas
```
docker images | grep n8n
```

### si usamos docker-compose, tenemos que usar .env
```
docker compose up -d
```

### Dar de baja los contenedores
```
docker compose down
```

### Ver variables de entorno de los contenedores
```
docker exec -it n8n env | grep N8N_RUNNERS_AUTH_TOKEN
```

### Eliminar el contenedor deteniendolo sin mostrar errores en pantalla
```
docker rm -f n8n 2>/dev/null
```