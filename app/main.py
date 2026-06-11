from io import BytesIO

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

from app.predictor import predict_island
from app.validation import (
    validate_description,
    validate_has_video,
    validate_num_extra_images,
    validate_tags,
    validate_thumbnail,
    validate_title,
)


app = FastAPI(title="Fortnite Island Predictor")

templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.post("/predict")
async def predict(
    title: str = Form(...),
    description: str = Form(...),
    tags: str = Form(""),
    has_video: int = Form(0),
    num_extra_images: int = Form(0),
    thumbnail: UploadFile = None,
):
    errors: dict[str, str] = {}

    title_error = validate_title(title)
    if title_error:
        errors["title"] = title_error

    description_error = validate_description(description)
    if description_error:
        errors["description"] = description_error

    parsed_tags, tags_error = validate_tags(tags)
    if tags_error:
        errors["tags"] = tags_error

    video_error = validate_has_video(has_video)
    if video_error:
        errors["has_video"] = video_error

    images_error = validate_num_extra_images(num_extra_images)
    if images_error:
        errors["num_extra_images"] = images_error

    if thumbnail is None or not thumbnail.filename:
        errors["thumbnail"] = "Thumbnail image is required."
    else:
        content = await thumbnail.read()
        thumb_error = validate_thumbnail(content, thumbnail.content_type)
        if thumb_error:
            errors["thumbnail"] = thumb_error

    if errors:
        return JSONResponse(
            status_code=422,
            content={"errors": errors},
        )

    image = Image.open(BytesIO(content)).convert("RGB")

    result = predict_island(
        title.strip(),
        description.strip(),
        image,
        parsed_tags,
        has_video,
        num_extra_images,
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return result


app.mount("/static", StaticFiles(directory="app/static"), name="static")
