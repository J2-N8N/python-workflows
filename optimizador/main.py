from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response
from PIL import Image
import io

app = FastAPI(title="Image to web converter")


@app.get("/test")
def health_check():
    return {"status": "ok", "message": "Service running"}


@app.post("/convert-webp")
async def convert_webp(file: UploadFile = File(...), quality: int = 80):
    #leemos el archivo original
    original_bytes = await file.read()
    #convertir los bytes en un archivo de memoria
    image = Image.open(io.BytesIO(original_bytes))

    # evualar la representacion en pixeles si es Palette o Luninance Alpha
    if image.mode in ("P", "LA"):
        image = image.convert("RGBA")
    elif image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    # Creamos un buffer en memoria para representar el archivo de salida
    output_buffer = io.BytesIO()
    image.save(
        output_buffer,  # usamos el buffer que creamos,
        format="WEBP",
        quality=quality,
        method=6,  # nivel de compresion
    )
    # regresar el cursor al inicio para leer el contenido del archivo que se creo de forma correcta
    output_buffer.seek(0)
    return Response(content=output_buffer.read(), media_type="image/webp")
