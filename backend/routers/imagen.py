import os
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from PIL import Image
from bson.objectid import ObjectId
from google import genai
from google.genai import types

from backend.db.mongo import db
from backend.utils.cloudinary_helper import upload_image_to_cloudinary
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api", tags=["imagen"])

# Inicializa el cliente de Gemini
GENAI_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GENAI_API_KEY:
    raise RuntimeError("No se encontró GOOGLE_API_KEY en el entorno.")
client = genai.Client(api_key=GENAI_API_KEY)


def normalize_to_jpeg(data: bytes) -> bytes:
    """
    Convierte cualquier byte array de imagen a JPEG (RGB).
    """
    img = Image.open(BytesIO(data)).convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def descripcion_prenda(img: Image.Image) -> str:
    """
    Genera la descripción de la prenda usando Gemini.
    """
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            "SOLO DAME LA DESCRIPCION EL TIPO DE PRENDA Y CARACTERISTICAS SOBRE SALIENTES, "
            "Ejemplo de salida (Anorak: Ligero, de nailon, con cremallera corta, capucha con cordón y detalles en bloques de color (azul y negro) en los hombros y las mangas. Logotipo KINGOFTHEKONGO, ADIDAS, etc.). "
            "LA SALIDA ESPERADA TIENE QUE SER EN INGLÉS",
            img
        ],
        config=types.GenerateContentConfig(response_modalities=["Text"])
    )
    return resp.candidates[0].content.parts[0].text


@router.post("/probar_prenda")
async def probar_prenda(
    user_id: str = Form(...),
    file_prenda: UploadFile = File(...),
    file_usuario: UploadFile = File(...)
):
    # 1) Leer y normalizar imágenes a JPEG bytes
    prenda_bytes = await file_prenda.read()
    if not prenda_bytes.startswith(b"\xff\xd8"):
        prenda_bytes = normalize_to_jpeg(prenda_bytes)

    usuario_bytes = await file_usuario.read()
    if not usuario_bytes.startswith(b"\xff\xd8"):
        usuario_bytes = normalize_to_jpeg(usuario_bytes)

    img_prenda = Image.open(BytesIO(prenda_bytes))
    img_usuario = Image.open(BytesIO(usuario_bytes))

    # 2) Generar descripción de la prenda
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
    gen_resp = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=[prompt, img_prenda, img_usuario],
        config=types.GenerateContentConfig(response_modalities=["Image"])
    )

    # Extraer bytes de la imagen generada
    img_data = None
    for part in gen_resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None):
            img_data = part.inline_data.data
            break
    if img_data is None:
        raise HTTPException(500, "Gemini no devolvió la imagen resultante")

    # 4) Subir a Cloudinary
    buf = BytesIO(img_data)
    try:
        url, _ = await upload_image_to_cloudinary(buf, folder="historial")
    except Exception as e:
        raise HTTPException(500, f"Error subiendo imagen: {e}")

    # 5) Devolver solo la URL
    return {"img_generada": url}
