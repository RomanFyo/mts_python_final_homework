import pytest
from fastapi import status
from sqlalchemy import select

from src.models import Book

API_V1_URL_PREFIX = "/api/v1/books"

# функция для получения токена
async def get_token(async_client, e_mail, password):
    authorization_response = await async_client.post(
        f"/api/v1/token/",
        json={
            "e_mail": e_mail,
            "password": password
        }
    )
    token = authorization_response.json().get("access_token")
    return token

# Тест на ручку создающую книгу
@pytest.mark.asyncio()
async def test_create_book(db_session, async_client, seller):
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": seller.id
    }

    token = await get_token(async_client, "mail@gmail.com", "1234")
    response = await async_client.post(
        f"{API_V1_URL_PREFIX}/",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    resp_book_id = result_data.pop("id", None)
    assert resp_book_id is not None, "Book id not returned from endpoint"

    assert result_data == {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "pages": 300,
        "year": 2025,
        "seller_id": seller.id
    }


@pytest.mark.asyncio()
async def test_create_book_with_old_year(async_client, seller):
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 1986,
        "seller_id": seller.id
    }

    token = await get_token(async_client, "mail@gmail.com", "1234")
    response = await async_client.post(
        f"{API_V1_URL_PREFIX}/",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Тест на ручку получения списка книг
@pytest.mark.asyncio()
async def test_get_books(db_session, async_client, seller):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2021, pages=104, seller_id=seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=2021, pages=108, seller_id=seller.id)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/")

    assert response.status_code == status.HTTP_200_OK

    assert len(response.json()["books"]) == 2  # Опасный паттерн! Если в БД есть данные, то тест упадет

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "books": [
            {
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2021,
                "id": book.id,
                "pages": 104,
                "seller_id": seller.id
            },
            {
                "title": "Mziri",
                "author": "Lermontov",
                "year": 2021,
                "id": book_2.id,
                "pages": 108,
                "seller_id": seller.id
            },
        ]
    }


# Тест на ручку получения одной книги
@pytest.mark.asyncio()
async def test_get_single_book(db_session, async_client, seller):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=1997, pages=104, seller_id=seller.id)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/{book.id}")

    assert response.status_code == status.HTTP_200_OK

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "year": 2001,
        "pages": 104,
        "id": book.id,
        "seller_id": seller.id
    }


@pytest.mark.asyncio()
async def test_get_single_book_with_wrong_id(db_session, async_client, seller):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/426548")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# Тест на ручку обновления книги
@pytest.mark.asyncio()
async def test_update_book_with_valid_seller_id(db_session, async_client, seller):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    data = {
        "title": "Mziri",
        "author": "Lermontov",
        "pages": 250,
        "year": 2024,
    }

    token = await get_token(async_client, "mail@gmail.com", "1234")
    response = await async_client.put(
        f"{API_V1_URL_PREFIX}/{book.id}",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # Проверяем, что обновились все поля
    res = await db_session.get(Book, book.id)
    assert res.title == "Mziri"
    assert res.author == "Lermontov"
    assert res.pages == 250
    assert res.year == 2024
    assert res.id == book.id
    assert res.seller_id == seller.id


@pytest.mark.asyncio()
async def test_delete_book(db_session, async_client, seller):
    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{book.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()
    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()

    assert len(res) == 0


@pytest.mark.asyncio()
async def test_delete_book_with_invalid_book_id(db_session, async_client, seller):
    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{book.id + 1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- ТЕСТЫ, ДОБАВЛЕННЫЕ ПРИ ВЫПОЛНЕНИИ ДОМАШНЕЙ РАБОТЫ ---

@pytest.mark.asyncio()
async def test_add_book_with_invalid_seller_id(async_client, seller):
    """
    Тест, проверяющий, что при добавлении книги с seller_id, которого нет в таблице sellers_table,
    будет возвращен response_status 404
    """
    data = {
        "author": "Lermontov",
        "title": "Mziri",
        "count_pages": 510,
        "year": 2024,
        "seller_id": 1234523
    }

    token = await get_token(async_client, "mail@gmail.com", "1234")
    response = await async_client.post(
        f"{API_V1_URL_PREFIX}/",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio()
async def test_add_book_with_valid_seller_id(db_session, async_client, seller):
    """
    Тест, проверяющий, что при добавлении книги с seller_id, который есть в таблице sellers_table,
    будет возвращен response_status 201 и само добавление книги будет выполнено правильно
    """
    data = {
        "author": "Lermontov",
        "title": "Mziri",
        "count_pages": 510,
        "year": 2024,
        "seller_id": seller.id
    }

    token = await get_token(async_client, "mail@gmail.com", "1234")
    response = await async_client.post(
        f"{API_V1_URL_PREFIX}/",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    resp_book_id = result_data.pop("id", None)
    assert resp_book_id is not None, "Book id not returned from endpoint"

    assert result_data == {
        "author": "Lermontov",
        "title": "Mziri",
        "pages": 510,
        "year": 2024,
        "seller_id": seller.id
    }