from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException, Response
from fastapi.responses import FileResponse
from tracker.models.schemas import (
    RegisterPeerRequest,
    RegisterPeerResponse,
    PeersListResponse,
    FilePeersResponse,
    HealthResponse,
)
from tracker.services.tracker_service import TrackerService

router = APIRouter(tags=["Tracker Core"])


def get_tracker_service() -> TrackerService:
    """Dependency provider for TrackerService."""
    return TrackerService()


@router.post(
    "/register",
    response_model=RegisterPeerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Peer",
    description="Registers a peer server's metadata (IP, port) and the list of files it hosts.",
)
def register_peer(
    request: RegisterPeerRequest,
    service: TrackerService = Depends(get_tracker_service),
) -> RegisterPeerResponse:
    return service.register_peer(request)


@router.get(
    "/peers",
    response_model=PeersListResponse,
    status_code=status.HTTP_200_OK,
    summary="List All Peers",
    description="Returns a list of all currently registered peers in the P2P network.",
)
def list_peers(
    service: TrackerService = Depends(get_tracker_service),
) -> PeersListResponse:
    return service.list_peers()


@router.get(
    "/peers/{filename}",
    response_model=FilePeersResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Peers For File",
    description="Returns all active peers that possess the specified filename.",
)
def get_peers_for_file(
    filename: str,
    service: TrackerService = Depends(get_tracker_service),
) -> FilePeersResponse:
    return service.get_peers_for_file(filename)


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Tracker Health Check",
    description="Returns current operational status of the tracker server along with active peer statistics.",
)
def health_check(
    service: TrackerService = Depends(get_tracker_service),
) -> HealthResponse:
    return service.check_health()


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload File via Web UI",
    description="Uploads a file via Web UI, stores it on the network seeder, and registers it with the tracker.",
)
async def upload_file(
    file: UploadFile = File(...),
    service: TrackerService = Depends(get_tracker_service),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    contents = await file.read()
    return service.save_uploaded_file(file.filename, contents)


@router.get(
    "/files/{filename}/metadata",
    summary="Get File Chunk Metadata",
    description="Returns chunk count, chunk size, total size, SHA-256 chunk hashes, and hosting peers for parallel download.",
)
def get_file_chunk_metadata(
    filename: str,
    chunk_size: int = 524288,
    service: TrackerService = Depends(get_tracker_service),
):
    meta = service.get_chunk_metadata(filename, chunk_size=chunk_size)
    if not meta:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
    return meta


@router.get(
    "/files/{filename}/chunks/{chunk_index}",
    summary="Download File Chunk",
    description="Fetches raw binary data for a specific chunk index along with X-SHA256 checksum header.",
)
def get_file_chunk(
    filename: str,
    chunk_index: int,
    chunk_size: int = 524288,
    service: TrackerService = Depends(get_tracker_service),
):
    result = service.get_file_chunk(filename, chunk_index, chunk_size=chunk_size)
    if not result:
        raise HTTPException(status_code=404, detail=f"Chunk {chunk_index} for file '{filename}' not found")

    chunk_bytes, sha256 = result
    headers = {
        "X-SHA256": sha256,
        "X-Chunk-Index": str(chunk_index),
        "Access-Control-Expose-Headers": "X-SHA256, X-Chunk-Index",
    }
    return Response(content=chunk_bytes, media_type="application/octet-stream", headers=headers)


@router.get(
    "/files/{filename}/download",
    summary="Direct Download Full File",
    description="Streams the complete file directly to the web client.",
)
def download_full_file(
    filename: str,
    service: TrackerService = Depends(get_tracker_service),
):
    file_path = service.get_file_path(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")

