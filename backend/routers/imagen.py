import os
import uuid
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from PIL import Image
from bson.objectid import ObjectId
from google import genai
from google.genai import types

from backend.db.mongo import db
from backend.utils.cloudinary_helper import upload_image_to_cloudinary  # <-- Necesario
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

GENAI_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GENAI_API_KEY:
    raise RuntimeError("No se encontró GOOGLE_API_KEY en el entorno.")

client = genai.Client(api_key=GENAI_API_KEY)

def get_mime_type_bytes(data: bytes) -> str:
    header = data[:12]
    if header.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if header.startswith(b"\x89PNG"):
        return "image/png"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"

def convert_pil_to_jpeg_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.convert("RGB").save(buf, format="JPEG")
    buf.seek(0)
    return buf

def descripcion_prenda(imagen_prenda: Image.Image) -> str:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            "SOLO DAME LA DESCRIPCION EL TIPO DE PRENDA Y CARACTERISTICAS SOBRE SALIENTES, "
            "Ejemplo de salida (Anorak: Ligero, de nailon, con cremallera corta, capucha con cordón y detalles en bloques de color (azul y negro) en los hombros y las mangas. Logotipo KINGOFTHEKONGO, ADIDAS, etc.). "
            "LA SALIDA ESPERADA TIENE QUE SER EN INGLÉS",
            imagen_prenda
        ],
        config=types.GenerateContentConfig(response_modalities=['Text'])
    )
    return response.candidates[0].content.parts[0].text

@router.post("/probar_prenda")
async def probar_prenda(
    user_id: str = Form(...),
    file_prenda: UploadFile = File(...),
    file_usuario: UploadFile = File(...)
):
    contenido_prenda = await file_prenda.read()
    contenido_usuario = await file_usuario.read()

    mime_prenda = get_mime_type_bytes(contenido_prenda)
    try:
        if mime_prenda != "image/jpeg":
            tmp = Image.open(BytesIO(contenido_prenda)).convert("RGB")
            contenido_prenda = convert_pil_to_jpeg_bytes(tmp).getvalue()
        img_prenda = Image.open(BytesIO(contenido_prenda))
    except Exception:
        raise HTTPException(status_code=400, detail="La imagen de la prenda no es válida")

    mime_usuario = get_mime_type_bytes(contenido_usuario)
    try:
        if mime_usuario != "image/jpeg":
            tmp2 = Image.open(BytesIO(contenido_usuario)).convert("RGB")
            contenido_usuario = convert_pil_to_jpeg_bytes(tmp2).getvalue()
        img_usuario = Image.open(BytesIO(contenido_usuario))
    except Exception:
        raise HTTPException(status_code=400, detail="La imagen del usuario no es válida")

    prenda = descripcion_prenda(img_prenda)

    prompt = (f"""Replace the {prenda} worn by the subject in Image 2 with the exact {prenda} from Image 1, ensuring a realistic and seamless integration. The face and background of Image 2 MUST remain completely unaltered.

    I. Prenda Extraction and Preservation (Image1):

    Precisely isolate the {prenda} in (Image1), excluding all other elements (background, subject's body, especially the face).
    Maintain the exact color, texture, shape, dimensions, patterns (e.g., 'KINGOFTHEKONGO' if applicable), logos, seams, and all other details of the {prenda}. Include all attachments like pockets, buttons, and zippers.
    II. Integration into Image 2:

    Completely replace the existing garment in Image 2 with the extracted {prenda}. Do not combine or blend any elements of the original garment in (Image2).
    Adjust the scale, perspective, and angle of the extracted {prenda} to perfectly match the subject's pose in Image 2, ensuring it drapes and fits naturally.
    Realistically adapt the lighting, shadows, and reflections on the inserted {prenda} to match the light source in Image 2, creating a three-dimensional appearance and natural contact shadows.
    III. Image 2 Preservation (Non-Negotiable):

    The subject's face in Image 2 must remain 100% identical to the original.
    All other elements of the subject (hair, accessories, other clothing) and the entire background of Image 2 must remain unchanged.
    The editing should be strictly limited to the area of the replaced {prenda}, without any spillover or alterations to surrounding areas.
    Negative Constraints:

    Do not combine or fuse any features of the original garment in Image 2 with the {prenda} from Image 1.
    Absolutely no modifications to the subject's face, hair, or expression are allowed.
    Do not alter any accessories, other clothing, or background elements in Image 2.
    Do not add any new shadows, reflections, or effects that are not directly a result of the inserted {prenda} and its interaction with the existing lighting.
    Avoid any blending or merging that compromises the natural appearance and volume of the inserted {prenda}."
    Key Changes in the Revision:

    More Direct Opening: Starts with the core task and immediate constraints.
    Streamlined Language: Uses slightly less technical jargon where the outcome is clearer.
    Emphasis on Non-Negotiables: Highlights the critical preservation aspects early and repeats them in the negative constraints.
    Focus on Outcome: Describes the desired visual effect rather than the specific technical steps the AI should take (which it doesn't directly control)."""
    "Asegúrate de que la prenda insertada se adapte de forma realista a la forma del cuerpo del sujeto en la Imagen 2, respetando los contornos, pliegues naturales y cómo caería la tela según su postura."
    f"La salida esperada es la image2 con la nueva prenda {prenda} integrada de forma realista y natural, manteniendo la cara y el fondo sin cambios. El resultado debe ser una imagen que parezca auténtica y profesional, como si la prenda siempre hubiera estado en la imagen original."
    f"The expected output is the image2 with the new {prenda} integrated realistically and naturally, keeping the face and background unchanged. The result should be an image that looks authentic and professional, as if the {prenda} had always been in the original image."
    ) 

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=[
            prompt,
            img_prenda,    
            img_usuario    
        ],
        config=types.GenerateContentConfig(response_modalities=['Text', 'Image'])
    )

    img_result = None
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            img_result = Image.open(BytesIO(part.inline_data.data))
            break

    if img_result is None:
        raise HTTPException(status_code=500, detail="Gemini no devolvió imagen resultante")

    # >>> Cambia este bloque <<<
    # 1. Guarda la imagen en memoria y subila a Cloudinary:
    output_buf = BytesIO()
    img_result.save(output_buf, format="JPEG")
    output_buf.seek(0)
    url_result, _ = await upload_image_to_cloudinary(output_buf, folder="historial")
    # ^^^ url_result es el string que vas a guardar en MongoDB ^^^

    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    historial = usuario.get("historial", [])
    if len(historial) >= 5:
        # Opcional: podrías borrar la imagen anterior de Cloudinary si querés
        historial.pop(0)
    historial.append(url_result)
    db["usuarios"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"historial": historial}}
    )

    return {
        "img_generada": url_result,
        "historial": historial
    }
