
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.vectorstore.retrieval import (
    delete_document_chunks,
    search_document_chunks,
)


class FakeQdrantClient:
    def __init__(self):
        self.search_args = None
        self.delete_args = None
        self.search_results = [SimpleNamespace(id="point-1", score=0.95)]

    def query_points(self, **kwargs):
        self.search_args = kwargs
        return SimpleNamespace(points=self.search_results)

    def delete(self, **kwargs):
        self.delete_args = kwargs


@pytest.fixture
def user_id():
    return str(uuid4())


@pytest.fixture
def document_id():
    return str(uuid4())


@pytest.fixture
def query_vector():
    return [1.0] + [0.0] * 383


def test_search_filters_by_user_and_document(
    user_id, document_id, query_vector
):
    client = FakeQdrantClient()

    results = search_document_chunks(
        client=client,
        query_vector=query_vector,
        user_id=user_id,
        document_id=document_id,
        limit=3,
    )

    assert results == client.search_results

    args = client.search_args
    assert args["collection_name"] == "investorlens_chunks"
    assert args["query"] == query_vector
    assert args["limit"] == 3
    assert args["with_payload"] is True
    assert args["with_vectors"] is False

    conditions = args["query_filter"].must
    assert len(conditions) == 2
    assert conditions[0].key == "user_id"
    assert conditions[0].match.value == user_id
    assert conditions[1].key == "document_id"
    assert conditions[1].match.value == document_id


def test_search_always_filters_by_user(
    user_id, query_vector
):
    client = FakeQdrantClient()

    search_document_chunks(
        client=client,
        query_vector=query_vector,
        user_id=user_id,
    )

    conditions = client.search_args["query_filter"].must

    assert len(conditions) == 1
    assert conditions[0].key == "user_id"
    assert conditions[0].match.value == user_id


def test_delete_filters_by_user_and_document(user_id, document_id):
    client = FakeQdrantClient()

    delete_document_chunks(
        client=client,
        user_id=user_id,
        document_id=document_id,
    )

    args = client.delete_args
    assert args["collection_name"] == "investorlens_chunks"
    assert args["wait"] is True

    conditions = args["points_selector"].filter.must
    assert len(conditions) == 2
    assert conditions[0].key == "user_id"
    assert conditions[0].match.value == user_id
    assert conditions[1].key == "document_id"
    assert conditions[1].match.value == document_id


def test_search_rejects_invalid_user_id(query_vector):
    with pytest.raises(ValueError):
        search_document_chunks(
            FakeQdrantClient(),
            query_vector,
            user_id="not-a-uuid",
        )


def test_search_rejects_invalid_document_id(user_id, query_vector):
    with pytest.raises(ValueError):
        search_document_chunks(
            FakeQdrantClient(),
            query_vector,
            user_id=user_id,
            document_id="not-a-uuid",
        )


def test_search_rejects_wrong_vector_dimensions(user_id):
    with pytest.raises(ValueError, match="384"):
        search_document_chunks(
            FakeQdrantClient(),
            query_vector=[0.1, 0.2, 0.3],
            user_id=user_id,
        )


def test_search_rejects_non_finite_vector(user_id):
    vector = [0.0] * 384
    vector[0] = float("nan")

    with pytest.raises(ValueError, match="non-finite"):
        search_document_chunks(
            FakeQdrantClient(),
            query_vector=vector,
            user_id=user_id,
        )


def test_search_rejects_non_positive_limit(user_id, query_vector):
    with pytest.raises(ValueError, match="positive"):
        search_document_chunks(
            FakeQdrantClient(),
            query_vector=query_vector,
            user_id=user_id,
            limit=0,
        )


def test_delete_rejects_invalid_ids(document_id):
    with pytest.raises(ValueError):
        delete_document_chunks(
            FakeQdrantClient(),
            user_id="not-a-uuid",
            document_id=document_id,
        )
