"""am180 FastAPI application.

Serves four API endpoints for the generative art frontend, plus a
/health liveness probe. All rendering is delegated to the generator
registry - this module only handles HTTP concerns.
"""
import io

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response

from am180.registry import GENERATORS
from am180.schemas import GeneratorInfo, GeneratorSchema, RenderRequest

app = FastAPI(title="am180", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. Returns {"status": "ok"} when the server is up."""
    return {"status": "ok"}


@app.get("/api/generators")
def list_generators() -> list[GeneratorInfo]:
    """List all available generators."""
    return [
        GeneratorInfo(id=g.id, name=g.name, description=g.description)
        for g in GENERATORS.values()
    ]


@app.get("/api/generators/{generator_id}/schema")
def get_generator_schema(generator_id: str) -> GeneratorSchema:
    """Get the parameter schema for a generator."""
    gen = GENERATORS.get(generator_id)
    if gen is None:
        raise HTTPException(
            status_code=404, detail=f"Unknown generator: {generator_id}"
        )
    return GeneratorSchema(id=gen.id, name=gen.name, params=gen.param_schema)


def _render_image(request: RenderRequest, size: int) -> Response:
    """Shared render logic for preview and render endpoints."""
    gen = GENERATORS.get(request.generator)
    if gen is None:
        raise HTTPException(
            status_code=404, detail=f"Unknown generator: {request.generator}"
        )
    params = gen.params_model(**request.params)
    image = gen.render(params, request.seed, size)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/api/preview")
def preview(
    request: RenderRequest, size: int = Query(default=512, le=1024)
) -> Response:
    """Render a low-resolution preview image."""
    return _render_image(request, size)


@app.post("/api/render")
def render_full(
    request: RenderRequest, size: int = Query(default=4096, le=8192)
) -> Response:
    """Render a high-resolution image for export."""
    response = _render_image(request, size)
    filename = f"{request.generator}-{request.seed}.png"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )
    return response
