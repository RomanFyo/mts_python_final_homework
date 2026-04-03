import pytest
from fastapi import status
from sqlalchemy import select

from src.models import Book, Seller

API_V1_URL_PREFIX = "/api/v1/sellers"

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

# тест на ручку, создающую селлера
@pytest.mark.asyncio()
async def test_create_seller(db_session, async_client):
    data = {
        "first_name": "Vasya",
        "last_name": "Pupkin",
        "e_mail": "mail@gmail.com",
        "password": "1234"
    }
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    resp_seller_id = result_data.pop("id", None)
    assert resp_seller_id is not None, "Seller id not returned from endpoint"

    assert result_data == {
        "first_name": "Vasya",
        "last_name": "Pupkin",
        "e_mail": "mail@gmail.com",
        "password": "1234"
    }

# тест на ручку, возвращающую список всех селлеров
@pytest.mark.asyncio()
async def test_get_sellers(db_session, async_client):
    seller1 = Seller(
        first_name="Vasya",
        last_name="Pupkin",
        e_mail="mail1@gmail.com",
        password="1234"
    )
    seller2 = Seller(
        first_name="Ivan",
        last_name="Ivanov",
        e_mail="mail2@gmail.com",
        password="23543"
    )

    db_session.add_all([seller1, seller2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/")

    assert response.status_code == status.HTTP_200_OK

    assert len(response.json()["sellers"]) == 2
    assert response.json() == {
        "sellers": [
            {
                "first_name": "Vasya",
                "last_name": "Pupkin",
                "e_mail": "mail1@gmail.com",
                "id": seller1.id
            },
            {
                "first_name": "Ivan",
                "last_name": "Ivanov",
                "e_mail": "mail2@gmail.com",
                "id": seller2.id
            }
        ]
    }

# тест для проверки ручки, возвращающей одного селлера
@pytest.mark.asyncio()
async def test_get_single_seller(db_session, async_client):
    seller = Seller(
        first_name="Vasya",
        last_name="Pupkin",
        e_mail="mail@gmail.com",
        password="1234"
    )
    seller2 = Seller(
        first_name="Ivan",
        last_name="Ivanov",
        e_mail="mail2@gmail.com",
        password="1234"
    )

    # добавим сначала продавца и сделаем flush, так как иначе не получится добавить книги с seller.id
    db_session.add_all([seller, seller2])
    await db_session.flush()

    book1 = Book(author="Pushkin", title="Eugeny Onegin", year=2021, pages=104, seller_id=seller.id)
    book2 = Book(author="Lermontov", title="Mziri", year=2021, pages=108, seller_id=seller.id)
    book3 = Book(author="Mitchell", title="Gone with the Wind", year=2021, pages=868, seller_id=seller2.id)

    db_session.add_all([book1, book2, book3])
    await db_session.flush()

    token = await get_token(async_client, "mail@gmail.com", "1234")
    response = await async_client.get(
        f"{API_V1_URL_PREFIX}/{seller.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "first_name": "Vasya",
        "last_name": "Pupkin",
        "e_mail": "mail@gmail.com",
        "id": seller.id,
        "books": [
            {
                "author": "Pushkin",
                "title": "Eugeny Onegin",
                "year": 2021,
                "pages": 104
            },
            {
                "author": "Lermontov",
                "title": "Mziri",
                "year": 2021,
                "pages": 108
            }
        ]
    }

@pytest.mark.asyncio()
async def test_get_single_seller_with_invalid_id(db_session, async_client):
    seller = Seller(
        first_name="Vasya",
        last_name="Pupkin",
        e_mail="mail@gmail.com",
        password="1234"
    )

    db_session.add(seller)
    await db_session.flush()

    token = await get_token(async_client, "mail@gmail.com", "1234")
    response = await async_client.get(
        f"{API_V1_URL_PREFIX}/12345678",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND

# тест для проверки ручки, обновляющей сведения о селлере
@pytest.mark.asyncio()
async def test_update_seller(db_session, async_client):
    seller = Seller(
        first_name="Vasya",
        last_name="Pupkin",
        e_mail="mail@gmail.com",
        password="1234"
    )

    db_session.add(seller)
    await db_session.flush()

    data = {
        "first_name": "Ivan",
        "last_name": "Ivanov",
        "e_mail": "IvanMail@gmail.com",
        "password": "new_pass"
    }

    response = await async_client.put(f"{API_V1_URL_PREFIX}/{seller.id}", json=data)

    assert response.status_code == status.HTTP_200_OK

    await db_session.flush()
    updated_data = await db_session.get(Seller, seller.id)

    assert updated_data.first_name == data["first_name"]
    assert updated_data.last_name == data["last_name"]
    assert updated_data.e_mail == data["e_mail"]
    assert updated_data.password == seller.password  # пароль не нужно менять по ТЗ

@pytest.mark.asyncio()
async def test_delete_seller(db_session, async_client):
    seller = Seller(
        first_name="Vasya",
        last_name="Pupkin",
        e_mail="mail@gmail.com",
        password="1234"
    )

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{seller.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    await db_session.flush()

    deleted_seller = await db_session.get(Seller, seller.id)

    assert deleted_seller is None

@pytest.mark.asyncio()
async def test_delete_seller_with_invalid_id(db_session, async_client):
    seller = Seller(
        first_name="Vasya",
        last_name="Pupkin",
        e_mail="mail@gmail.com",
        password="1234"
    )

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/12345678")

    assert response.status_code == status.HTTP_404_NOT_FOUND

# тест на то, что при удалении селлера все связанные с ним книги удаляются
@pytest.mark.asyncio()
async def test_books_related_to_seller_deleted(db_session, async_client):
    """
    Тест для проверки того, что при удалении seller книги, принадлежащие продавцу, тоже будут удалены
    (books.seller_id == seller.id)
    """
    seller = Seller(
        first_name="Vasya",
        last_name="Pupkin",
        e_mail="mail@gmail.com",
        password="1234"
    )

    seller2 = Seller(
        first_name="Ivan",
        last_name="Ivanov",
        e_mail="mail2@gmail.com",
        password="1234"
    )

    # добавим сначала продавца и сделаем flush, так как иначе не получится добавить книги с seller.id
    db_session.add_all([seller, seller2])
    await db_session.flush()

    book1 = Book(author="Pushkin", title="Eugeny Onegin", year=2021, pages=104, seller_id=seller.id)
    book2 = Book(author="Lermontov", title="Mziri", year=2021, pages=108, seller_id=seller.id)
    book3 = Book(author="Mitchell", title="Gone with the Wind", year=2021, pages=868, seller_id=seller2.id)

    db_session.add_all([book1, book2, book3])
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{seller.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    await db_session.flush()

    deleted_book1 = await db_session.get(Book, book1.id)
    deleted_book2 = await db_session.get(Book, book2.id)

    assert deleted_book1 is None
    assert deleted_book2 is None

    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()

    assert len(res) == 1