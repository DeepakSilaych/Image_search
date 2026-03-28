from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models

COLLECTION_IMAGES = "images"
COLLECTION_FACES = "faces"

CLIP_VECTOR_SIZE = 512
FACE_VECTOR_SIZE = 512


def ensure_collections(client: QdrantClient):
    if not client.collection_exists(COLLECTION_IMAGES):
        client.create_collection(
            collection_name=COLLECTION_IMAGES,
            vectors_config=models.VectorParams(size=CLIP_VECTOR_SIZE, distance=models.Distance.COSINE),
        )
        client.create_payload_index(COLLECTION_IMAGES, "image_id", models.PayloadSchemaType.KEYWORD)

    if not client.collection_exists(COLLECTION_FACES):
        client.create_collection(
            collection_name=COLLECTION_FACES,
            vectors_config=models.VectorParams(size=FACE_VECTOR_SIZE, distance=models.Distance.COSINE),
        )
        client.create_payload_index(COLLECTION_FACES, "person_id", models.PayloadSchemaType.KEYWORD)


def upsert_image_vector(client: QdrantClient, image_id: UUID, vector: list[float], payload: dict | None = None):
    point_payload = {"image_id": str(image_id)}
    if payload:
        point_payload.update(payload)
    client.upsert(
        collection_name=COLLECTION_IMAGES,
        points=[models.PointStruct(id=str(image_id), vector=vector, payload=point_payload)],
    )


def upsert_face_vector(client: QdrantClient, face_id: UUID, vector: list[float], person_id: UUID | None = None):
    payload = {"face_id": str(face_id)}
    if person_id:
        payload["person_id"] = str(person_id)
    client.upsert(
        collection_name=COLLECTION_FACES,
        points=[models.PointStruct(id=str(face_id), vector=vector, payload=payload)],
    )


def search_similar_images(
    client: QdrantClient, vector: list[float], limit: int = 200, filters: models.Filter | None = None
) -> list[models.ScoredPoint]:
    return client.query_points(
        collection_name=COLLECTION_IMAGES,
        query=vector,
        query_filter=filters,
        limit=limit,
    ).points


def search_similar_faces(client: QdrantClient, vector: list[float], limit: int = 5) -> list[models.ScoredPoint]:
    return client.query_points(
        collection_name=COLLECTION_FACES,
        query=vector,
        limit=limit,
    ).points


def delete_image_vector(client: QdrantClient, image_id: UUID):
    client.delete(collection_name=COLLECTION_IMAGES, points_selector=models.PointIdsList(points=[str(image_id)]))


def get_face_vector(client: QdrantClient, face_id: UUID) -> list[float] | None:
    try:
        points = client.retrieve(collection_name=COLLECTION_FACES, ids=[str(face_id)], with_vectors=True)
        if points:
            return points[0].vector
    except Exception:
        pass
    return None


def get_collection_info(client: QdrantClient, name: str):
    try:
        return client.get_collection(name)
    except Exception:
        return None
