def n1():
    """Напишите функцию, которая парсит одну страницу с книгой. Функция принимает на вход URL, возвращает словарь со всей информацией о книге (включая количество звездочек, ссылку на изображение, доступное количество и жанр). В случае 404 ошибки возбудите ValueError


    import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


def parse_book_page(url: str) -> dict:
    # 1) GET-запрос
    response = requests.get(url)
    if response.status_code == 404:
        raise ValueError(f"Страница не найдена: {url}")
    if not response.ok:
        raise ValueError(f"Ошибка при запросе страницы: {response.status_code}")

    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")

    # 2) Основная информация
    # Название книги
    title_tag = soup.find("div", class_="product_main").find("h1")
    title = title_tag.text.strip() if title_tag else None

    # Цена
    price_tag = soup.find("p", class_="price_color")
    price = price_tag.text.strip() if price_tag else None

    # Рейтинг (в виде слова, напр. "Three")
    rating_tag = soup.find("p", class_=re.compile("star-rating"))
    rating = None
    if rating_tag:
        # Класс содержит текст рейтинга
        classes = rating_tag.get("class", [])
        for cls in classes:
            if cls != "star-rating":
                rating = cls  # "One", "Two", "Three"...
                break

    # Изображение (полная ссылка)
    image_tag = soup.find("div", id="product_gallery").find("img")
    image_src = None
    if image_tag:
        image_src = image_tag.get("src")
        image_src = urljoin(url, image_src)

    # Жанр (в хлебных крошках)
    genre = None
    breadcrumb = soup.find("ul", class_="breadcrumb")
    if breadcrumb:
        crumbs = breadcrumb.find_all("a")
        # обычно третий элемент — это жанр
        if len(crumbs) >= 3:
            genre = crumbs[2].text.strip()

    # Описание
    desc_tag = soup.find("div", id="product_description")
    description = None
    if desc_tag:
        # описание — следующий тег p после заголовка
        next_p = desc_tag.find_next_sibling("p")
        if next_p:
            description = next_p.text.strip()

    # Таблица с данными (UPC, доступность и т.д.)
    table = soup.find("table", class_="table table-striped")
    upc = None
    availability = None
    if table:
        for row in table.find_all("tr"):
            th = row.find("th").text.strip()
            td = row.find("td").text.strip()
            if th == "UPC":
                upc = td
            elif th == "Availability":
                # Извлечь число доступных
                m = re.search(r"\d+", td)
                if m:
                    availability = int(m.group())

    return {
        "title": title,
        "price": price,
        "rating": rating,
        "image_url": image_src,
        "genre": genre,
        "description": description,
        "upc": upc,
        "availability": availability
    }



    book_url = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
data = parse_book_page(book_url)
print(data)"""


def n2():
    """Напишите функцию, которая обрабатывает одну страницу из каталога книг (возвращает список словарей по каждой из книг).


    import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = "http://books.toscrape.com/"

def parse_catalog_page(page_url):
    Парсит одну страницу каталога книг и возвращает список словарей с книгами.
    response = requests.get(page_url)
    if response.status_code != 200:
        raise ValueError(f"Страница не найдена: {page_url}")

    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, 'html.parser')
    books = []

    # Все книги на странице находятся в <article class="product_pod">
    for article in soup.find_all('article', class_='product_pod'):
        # Название книги
        title = article.h3.a['title']

        # Ссылка на страницу книги (относительная -> абсолютная)
        book_url = urljoin(BASE_URL, article.h3.a['href'])

        # Ссылка на изображение
        image_url = urljoin(BASE_URL, article.find('img')['src'])

        # Цена
        price = article.find('p', class_='price_color').text.strip()

        # Рейтинг (в виде строки: One, Two, Three...)
        rating_class = article.find('p', class_='star-rating')['class']
        rating = [r for r in rating_class if r != 'star-rating'][0]

        # Наличие (коротко, на странице каталога это всегда "In stock")
        availability = article.find('p', class_='instock availability').text.strip()

        books.append({
            'title': title,
            'book_url': book_url,
            'image_url': image_url,
            'price': price,
            'rating': rating,
            'availability': availability
        })

    return books



    page_url = "http://books.toscrape.com/catalogue/page-1.html"
result = parse_catalog_page(page_url)
for book in result:  # показываем первые 3 книги
    print(book)"""


def n3():
    """Создайте массив NumPy, содержащий информацию о ценах книг. Магазин вводит скидку 15% на все книги. Найдите минимальную цену книги после введения скидки



    import requests
from bs4 import BeautifulSoup
import numpy as np



base_url = "http://books.toscrape.com/catalogue/page-{}.html"

all_prices = []

page = 1
while True:
    url = base_url.format(page)
    response = requests.get(url)

    # Если страницы нет — прекращаем
    if response.status_code == 404:
        break

    soup = BeautifulSoup(response.text, 'html.parser')
    price_elements = soup.select('p.price_color')

    # Преобразуем текст цены в float (убираем £ и странные символы)
    prices = [float(p.text.replace('£', '').replace('Â', '').strip()) for p in price_elements]
    all_prices.extend(prices)

    page += 1  # идём на следующую страницу

# Превращаем список в NumPy массив
prices_array = np.array(all_prices)

# Применяем скидку 15%
discount = 0.15
prices_after_discount = prices_array * (1 - discount)

# Находим минимальную цену после скидки
min_price = np.min(prices_after_discount)
print(f"Минимальная цена книги после скидки: £{min_price:.2f}")
"""


def n4():
    """Создайте массив NumPy, содержащий информацию о количестве книг. Посчитайте общую выручку, которую магазин получит, продав все книги



    import requests
from bs4 import BeautifulSoup
import numpy as np



base_url = "http://books.toscrape.com/catalogue/"
page_url = "page-1.html"

prices = []
quantities = []

while page_url:
    url = base_url + page_url
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    # Парсим цены
    price_elements = soup.select('p.price_color')
    page_prices = [float(p.text.strip().lstrip('£')) for p in price_elements]
    prices.extend(page_prices)

    # Для простоты считаем, что у каждой книги 1 экземпляр
    quantities.extend([1] * len(page_prices))

    # Ищем ссылку на следующую страницу
    next_li = soup.select_one('li.next > a')
    if next_li:
        page_url = next_li['href']  # берем href следующей страницы
    else:
        page_url = None  # дальше страниц нет

# Создаём NumPy массив
data = np.array([prices, quantities]).T
total_revenue = np.sum(data[:, 0] * data[:, 1])

print(f"Всего книг: {len(data)}")
print(f"Общая выручка, если продать все книги: £{total_revenue:.2f}")"""


def n5():
    """Создайте массив NumPy с закодированными значениями жанра. Магазин вводит скидку на каждый жанр по отдельной.Создайте массив NumPy со значениями скидок (размер массива зависит от количества жанров в выборке). Примените скидку к каждой книге в зависимости от жанра



    import requests
from bs4 import BeautifulSoup
import numpy as np



BASE_URL = "http://books.toscrape.com/"

# Получение списка всех категорий
categories_page = requests.get(BASE_URL)
soup = BeautifulSoup(categories_page.text, "html.parser")

categories = soup.select("div.side_categories ul li ul li a")
category_links = {a.text.strip(): BASE_URL + a['href'] for a in categories}
print("Категории:", list(category_links.keys()))



books_data = []

for genre, link in category_links.items():
    page_url = link
    while True:
        r = requests.get(page_url)
        soup = BeautifulSoup(r.text, "html.parser")

        # Находим все книги на странице
        for book in soup.select("article.product_pod"):
            price_text = book.select_one("p.price_color").text
            price = float(price_text[2:])  # убираем '£'
            books_data.append({"price": price, "genre": genre})

        # Переход к следующей странице, если есть
        next_page = soup.select_one("li.next a")
        if next_page:
            page_url = "/".join(page_url.split("/")[:-1]) + "/" + next_page['href']
        else:
            break



            unique_genres = sorted(list({b["genre"] for b in books_data}))

# Кодируем жанры числами
genre_to_code = {genre: i for i, genre in enumerate(unique_genres)}
codes = np.array([genre_to_code[b["genre"]] for b in books_data])

# Массив цен
prices = np.array([b["price"] for b in books_data])

print(prices)

# Пример скидок для каждого жанра (в процентах)
discounts = np.full(len(unique_genres), 0.10)

final_prices = prices * (1 - discounts[codes])

final_prices"""


def n6():
    """Соберите словарь вида {жанр: список книг жанра}. Сохраните словарь в формат JSON. Прочитайте файл.



    import requests
from bs4 import BeautifulSoup
import json



base_url = "http://books.toscrape.com/catalogue/"
page_url = "page-1.html"

genre_books = {}  # Словарь вида {жанр: список книг}

while page_url:
    url = base_url + page_url
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    # Находим все книги на странице
    articles = soup.find_all('article', class_='product_pod')

    for article in articles:
        # Название книги
        title = article.h3.a['title']
        # Ссылка на страницу книги (чтобы взять жанр)
        book_link = article.h3.a['href']
        book_url = base_url + book_link

        # Получаем страницу книги
        book_resp = requests.get(book_url)
        book_resp.encoding = 'utf-8'
        book_soup = BeautifulSoup(book_resp.text, "html.parser")

        # Жанр книги (находится в хлебных крошках, второй элемент после Home)
        genre = book_soup.find('ul', class_='breadcrumb').find_all('li')[2].a.text.strip()

        # Добавляем в словарь
        if genre not in genre_books:
            genre_books[genre] = []
        genre_books[genre].append(title)

    # Переходим на следующую страницу
    next_btn = soup.find('li', class_='next')
    if next_btn:
        page_url = next_btn.a['href']
    else:
        page_url = None



        # Сохраняем словарь в JSON
with open('genre_books.json', 'w', encoding='utf-8') as f:
    json.dump(genre_books, f, ensure_ascii=False, indent=4)

print("Словарь сохранён в 'genre_books.json'")

# Чтение JSON обратно
with open('genre_books.json', 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)

print("Прочитанные данные:")
for genre, books in loaded_data.items():
    print(f"{genre}: {len(books)} книг")"""


def n7():
    """# 7 (не ебу работает или нет потому что ячейка с кодом грузилась 20 минут и я заебался ждать)


    Соберите кортеж из двух элементов (список книг, облагаемых налогами; список книг, не облагаемых налогами). Сохраните кортеж в формат Pickle. Считайте файл.



    import requests
from bs4 import BeautifulSoup
import pickle



base_url = "http://books.toscrape.com/catalogue/"
page_url = "page-1.html"

taxable_books = []
non_taxable_books = []

while page_url:
    url = base_url + page_url
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    articles = soup.select("article.product_pod")

    for article in articles:
        title = article.h3.a['title']
        detail_url = base_url + article.h3.a['href']

        # Парсим детальную страницу книги
        detail_resp = requests.get(detail_url)
        detail_resp.encoding = 'utf-8'
        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")

        # Таблица с информацией о книге
        table = detail_soup.select("table.table.table-striped")
        tax_text = None
        for row in table[0].select("tr"):
            th = row.th.text.strip()
            td = row.td.text.strip()
            if th == "Tax":
                tax_text = td
                break

        # Преобразуем в число
        tax = float(tax_text.lstrip('£'))

        if tax > 0:
            taxable_books.append(title)
        else:
            non_taxable_books.append(title)

    # Переход на следующую страницу
    next_button = soup.select_one("li.next a")
    if next_button:
        page_url = "page-" + next_button['href'].split("page-")[-1]
    else:
        page_url = None



        books_tuple = (taxable_books, non_taxable_books)

# Сохраняем в Pickle
with open("books.pkl", "wb") as f:
    pickle.dump(books_tuple, f)

# Считываем файл
with open("books.pkl", "rb") as f:
    loaded_books = pickle.load(f)

print("Облагаемые книги:", loaded_books[0][:5], "...")  # первые 5 для примера
print("Не облагаемые книги:", loaded_books[1][:5], "...")"""


def n8():
    """Создайте pd.DataFrame, содержащий всю полученную информацию о книгах. Сохраните его в файл xlsx.



    import requests
from bs4 import BeautifulSoup
import pandas as pd
import time



# Базовый URL
base_url = "http://books.toscrape.com/catalogue/"
page_url = "page-1.html"

# Списки для хранения данных
titles = []
prices = []
availabilities = []
ratings = []
categories = []

# Функция для конвертации рейтинга в число
def rating_to_int(rating_str):
    rating_dict = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    return rating_dict.get(rating_str, 0)

while page_url:
    url = base_url + page_url
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    books = soup.select("article.product_pod")
    for book in books:
        # Название
        title = book.h3.a['title']
        titles.append(title)

        # Цена
        price = float(book.select_one("p.price_color").text.strip().lstrip('£'))
        prices.append(price)

        # Наличие
        availability_text = book.select_one("p.availability").text.strip()
        availabilities.append(availability_text)

        # Рейтинг
        rating_class = book.select_one("p.star-rating")['class'][1]
        ratings.append(rating_to_int(rating_class))

        # Категория (из breadcrumbs)
        # На странице с книгой категория берется из URL
        categories.append("unknown")  # пока неизвестно, можно будет уточнить на странице книги

    # Переход на следующую страницу
    next_button = soup.select_one("li.next a")
    if next_button:
        page_url = next_button['href']
    else:
        page_url = None

    # Чтобы не перегружать сервер
    time.sleep(0.1)



    df = pd.DataFrame({
    "Title": titles,
    "Price": prices,
    "Availability": availabilities,
    "Rating": ratings,
    "Category": categories
})

# Сохраняем в Excel
df.to_excel("books.xlsx", index=False)

print("Данные успешно сохранены в books.xlsx")"""


def n9():
    """# 9 (не ебу работает или нет потому что на маке чуть другой код писать надо)


    При помощи xlwings добавьте в xlsx файл столбец с ценой в рублях. Используйте протягиваемые формулы. Курс зафиксируйте на отдельном листе.




    import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import xlwings as xw



# Базовый URL
base_url = "http://books.toscrape.com/catalogue/"
page_url = "page-1.html"

# Списки для хранения данных
titles = []
prices = []
availabilities = []
ratings = []
categories = []

# Функция для конвертации рейтинга в число
def rating_to_int(rating_str):
    rating_dict = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    return rating_dict.get(rating_str, 0)

while page_url:
    url = base_url + page_url
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    books = soup.select("article.product_pod")
    for book in books:
        # Название
        title = book.h3.a['title']
        titles.append(title)

        # Цена
        price = float(book.select_one("p.price_color").text.strip().lstrip('£'))
        prices.append(price)

        # Наличие
        availability_text = book.select_one("p.availability").text.strip()
        availabilities.append(availability_text)

        # Рейтинг
        rating_class = book.select_one("p.star-rating")['class'][1]
        ratings.append(rating_to_int(rating_class))

        # Категория (из breadcrumbs)
        # На странице с книгой категория берется из URL
        categories.append("unknown")  # пока неизвестно, можно будет уточнить на странице книги

    # Переход на следующую страницу
    next_button = soup.select_one("li.next a")
    if next_button:
        page_url = next_button['href']
    else:
        page_url = None

    # Чтобы не перегружать сервер
    time.sleep(0.1)



    df = pd.DataFrame({
    "Title": titles,
    "Price": prices,
    "Availability": availabilities,
    "Rating": ratings,
    "Category": categories
})

# Сохраняем в Excel
df.to_excel("books.xlsx", index=False)

print("Данные успешно сохранены в books.xlsx")



file_path = "books.xlsx"  # путь к вашему файлу
wb = xw.Book(file_path)

# Проверяем наличие листа "Курс" или создаем его
if "Курс" in [s.name for s in wb.sheets]:
    sheet_rate = wb.sheets["Курс"]
else:
    sheet_rate = wb.sheets.add("Курс")

# Устанавливаем курс USD->RUB
sheet_rate.range("A1").value = "USD_to_RUB"
sheet_rate.range("B1").value = 100  # пример курса

# Основной лист с данными (предположим, что первый лист)
sheet_main = wb.sheets[0]

# Найдем столбец с заголовком "Price" автоматически
header_row = 1
headers = sheet_main.range(f"A{header_row}:Z{header_row}").value  # проверим первые 26 столбцов
try:
    price_col_index = headers.index("Price") + 1  # +1, потому что индекс в Excel начинается с 1
except ValueError:
    raise ValueError("Не найден столбец с заголовком 'Price'")

# Новый столбец для рублевой цены
rub_col_index = price_col_index + 1
sheet_main.range((header_row, rub_col_index)).value = "Price_RUB"

# Последняя строка с данными
last_row = sheet_main.range((sheet_main.cells.last_cell.row, price_col_index)).end('up').row

# Проставляем формулы
for row in range(header_row + 1, last_row + 1):
    sheet_main.range((row, rub_col_index)).formula = f"={sheet_main.range((row, price_col_index)).get_address()}*Курс!B1"

# Сохраняем
wb.save(file_path)
wb.close()"""


def n10():
    """При помощи xlwings раскрасьте столбец с названием книги. Если в наличии более 20 книг, сделайте заливку зеленым, иначе - желтым.



    import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import xlwings as xw



# Базовый URL
base_url = "http://books.toscrape.com/catalogue/"
page_url = "page-1.html"

# Списки для хранения данных
titles = []
prices = []
availabilities = []
ratings = []
categories = []

# Функция для конвертации рейтинга в число
def rating_to_int(rating_str):
    rating_dict = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    return rating_dict.get(rating_str, 0)

while page_url:
    url = base_url + page_url
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    books = soup.select("article.product_pod")
    for book in books:
        # Название
        title = book.h3.a['title']
        titles.append(title)

        # Цена
        price = float(book.select_one("p.price_color").text.strip().lstrip('£'))
        prices.append(price)

        # Наличие
        availability_text = book.select_one("p.availability").text.strip()
        availabilities.append(availability_text)

        # Рейтинг
        rating_class = book.select_one("p.star-rating")['class'][1]
        ratings.append(rating_to_int(rating_class))

        # Категория (из breadcrumbs)
        # На странице с книгой категория берется из URL
        categories.append("unknown")  # пока неизвестно, можно будет уточнить на странице книги

    # Переход на следующую страницу
    next_button = soup.select_one("li.next a")
    if next_button:
        page_url = next_button['href']
    else:
        page_url = None

    # Чтобы не перегружать сервер
    time.sleep(0.1)



    df = pd.DataFrame({
    "Title": titles,
    "Price": prices,
    "Availability": availabilities,
    "Rating": ratings,
    "Category": categories
})

# Сохраняем в Excel
df.to_excel("books.xlsx", index=False)

print("Данные успешно сохранены в books.xlsx")



wb = xw.Book("books.xlsx")
ws = wb.sheets[0]

# Определяем цвет
num_books = len(df)
color = (146, 208, 80) if num_books > 20 else (255, 255, 0)

# Находим столбец с названием книги
title_col_idx = df.columns.get_loc("Title") + 1  # 1-based индекс

# Переводим индекс в букву колонки
def col_letter(n):
    Преобразует 1-based индекс колонки в букву Excel (1 -> A, 27 -> AA)
    result = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result

title_col_letter = col_letter(title_col_idx)

# Диапазон ячеек с названиями книг
range_str = f"{title_col_letter}2:{title_col_letter}{num_books + 1}"
cell_range = ws.range(range_str)

# Применяем заливку
cell_range.color = color

# Сохраняем в новый файл
wb.save("books_colored.xlsx")
wb.close()"""


def n11():
    """Напишите функцию, которая извлекает из текстов описаний имена собственные. Имя собственное - это слово, начинающееся с заглавной буквы и за которым следует одна или несколько строчных букв.



    import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from time import sleep



BASE_URL = "http://books.toscrape.com/"

def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def extract_proper_names(text):
    Извлекает собственные имена из текста.
    pattern = r'\b[A-ZА-ЯЁ][a-zа-яё]+\b'
    return re.findall(pattern, text)

def get_book_links(page_url):
    Возвращает список ссылок на книги на одной странице.
    soup = get_soup(page_url)
    links = []
    for h3 in soup.select("h3 > a"):
        href = h3['href']
        # Приведение относительной ссылки к абсолютной
        links.append(BASE_URL + "catalogue/" + href.replace("../", ""))
    return links

def get_book_description(book_url):
    Возвращает заголовок книги и описание.
    soup = get_soup(book_url)
    title = soup.find("h1").text.strip()
    desc_tag = soup.find("meta", {"name": "description"})
    description = desc_tag['content'].strip() if desc_tag else ""
    return title, description

def scrape_all_books():
    Собирает данные по всем книгам и извлекает собственные имена.
    books_data = []
    page = 1
    while True:
        page_url = f"{BASE_URL}catalogue/page-{page}.html"
        try:
            book_links = get_book_links(page_url)
            if not book_links:
                break
            for link in book_links:
                title, description = get_book_description(link)
                proper_names = extract_proper_names(description)
                books_data.append({"title": title, "proper_names": proper_names})
                sleep(0.1)  # чтобы не перегружать сервер
            page += 1
        except requests.HTTPError:
            break  # дошли до несуществующей страницы
    return pd.DataFrame(books_data)

# Запуск
df = scrape_all_books()
print(df.head())"""


def n12():
    """Представьте каждое описание в виде вектора при помощи TfidfVectorizer. Для каждой пары описаний посчитайте косинусную близость между ними. Визуализируйте результат в виде heatmap.


    import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
from tqdm import tqdm

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import seaborn as sns
import matplotlib.pyplot as plt



BASE_URL = "http://books.toscrape.com/"
CATALOGUE = urljoin(BASE_URL, "catalogue/")

titles = []
descriptions = []
book_urls = []

# Начинаем с первой страницы
page_url = urljoin(CATALOGUE, "page-1.html")

while page_url:
    resp = requests.get(page_url)
    if resp.status_code != 200:
        break

    soup = BeautifulSoup(resp.text, "html.parser")

    # Ссылки на книги на этой странице
    for a in soup.select("article.product_pod h3 a"):
        href = a.get("href")
        detail_url = urljoin(CATALOGUE, href)
        book_urls.append(detail_url)

    # Ищем ссылку на следующую страницу
    next_page = soup.select_one("li.next a")
    if next_page:
        next_href = next_page.get("href")
        page_url = urljoin(CATALOGUE, next_href)
    else:
        page_url = None  # больше страниц нет

    time.sleep(0.2)

book_urls = list(dict.fromkeys(book_urls))
print(f"Всего найдено книг: {len(book_urls)}")

# Парсим описания каждой книги (как раньше)
for url in tqdm(book_urls):
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    title_tag = soup.select_one("div.product_main h1")
    desc_tag = soup.select_one("#product_description ~ p")

    titles.append(title_tag.text.strip() if title_tag else "")
    descriptions.append(desc_tag.text.strip() if desc_tag else "")

    time.sleep(0.1)

# DataFrame
import pandas as pd
df = pd.DataFrame({"title": titles, "description": descriptions})
print(df.head())



tfidf = TfidfVectorizer(
    stop_words="english",
    max_df=0.95,
    min_df=2
)

tfidf_matrix = tfidf.fit_transform(df["description"])
print(f"TF‑IDF matrix shape: {tfidf_matrix.shape}")

cos_sim_matrix = cosine_similarity(tfidf_matrix)



N = 30
plt.figure(figsize=(12,10))
sns.heatmap(
    cos_sim_matrix[:N, :N],
    xticklabels=df["title"][:N],
    yticklabels=df["title"][:N],
    cmap="viridis",
    linewidths=0.3
)
plt.xticks(rotation=90, fontsize=8)
plt.yticks(rotation=0, fontsize=8)
plt.title("Косинусная близость (первые 30 книг)")
plt.tight_layout()
plt.show()"""


def n13():
    """Найдите собственные числа матрицы косинусной близости. Найдите разность между максимальным и минимальным собственным значением.



    import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
from tqdm import tqdm

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import seaborn as sns
import matplotlib.pyplot as plt



BASE_URL = "http://books.toscrape.com/"
CATALOGUE = urljoin(BASE_URL, "catalogue/")

titles = []
descriptions = []
book_urls = []

# Начинаем с первой страницы
page_url = urljoin(CATALOGUE, "page-1.html")

while page_url:
    resp = requests.get(page_url)
    if resp.status_code != 200:
        break

    soup = BeautifulSoup(resp.text, "html.parser")

    # Ссылки на книги на этой странице
    for a in soup.select("article.product_pod h3 a"):
        href = a.get("href")
        detail_url = urljoin(CATALOGUE, href)
        book_urls.append(detail_url)

    # Ищем ссылку на следующую страницу
    next_page = soup.select_one("li.next a")
    if next_page:
        next_href = next_page.get("href")
        page_url = urljoin(CATALOGUE, next_href)
    else:
        page_url = None  # больше страниц нет

    time.sleep(0.2)

book_urls = list(dict.fromkeys(book_urls))
print(f"Всего найдено книг: {len(book_urls)}")

# Парсим описания каждой книги (как раньше)
for url in tqdm(book_urls):
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    title_tag = soup.select_one("div.product_main h1")
    desc_tag = soup.select_one("#product_description ~ p")

    titles.append(title_tag.text.strip() if title_tag else "")
    descriptions.append(desc_tag.text.strip() if desc_tag else "")

    time.sleep(0.1)

# DataFrame
import pandas as pd
df = pd.DataFrame({"title": titles, "description": descriptions})
print(df.head())



tfidf = TfidfVectorizer(
    stop_words="english",
    max_df=0.95,
    min_df=2
)

tfidf_matrix = tfidf.fit_transform(df["description"])
print(f"TF‑IDF matrix shape: {tfidf_matrix.shape}")

cos_sim_matrix = cosine_similarity(tfidf_matrix)



import numpy as np

# cos_sim — ваша матрица косинусной близости
# Находим собственные значения
eigenvalues = np.linalg.eigvals(cos_sim_matrix)

# Выводим несколько первых для проверки
print("Первые 10 собственных значений:", eigenvalues[:10])

# Разность между максимальным и минимальным
max_val = np.max(eigenvalues)
min_val = np.min(eigenvalues)
diff = max_val - min_val

print(f"Максимальное собственное значение: {max_val}")
print(f"Минимальное собственное значение: {min_val}")
print(f"Разность между ними: {diff}")"""


def n14():
    """Используя pandas, найдите самую дорогую книгу в каждом из жанров



    import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin




BASE_URL = "http://books.toscrape.com/"

# 1️⃣ Получаем список жанров
resp = requests.get(urljoin(BASE_URL, "index.html"))
soup = BeautifulSoup(resp.text, "lxml")

genres = []
for a in soup.select(".side_categories ul li ul li a"):
    genre_name = a.text.strip()
    genre_link = urljoin(BASE_URL, a['href'])
    genres.append((genre_name, genre_link))

all_books = []

# 2️⃣ Проходим по каждому жанру и собираем книги
for genre_name, genre_link in genres:
    page_url = genre_link
    while True:
        resp = requests.get(page_url)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, "lxml")

        books = soup.select("article.product_pod")
        for book in books:
            title = book.h3.a['title']
            price = book.select_one(".price_color").text
            price = float(price.replace('£',''))
            all_books.append({
                "genre": genre_name,
                "title": title,
                "price": price
            })

        # Проверяем есть ли следующая страница
        next_page = soup.select_one(".next a")
        if next_page:
            page_url = urljoin(page_url, next_page['href'])
        else:
            break

# 3️⃣ Создаём DataFrame
df = pd.DataFrame(all_books)

# 4️⃣ Находим самую дорогую книгу в каждом жанре
max_price_per_genre = df.groupby('genre')['price'].max().reset_index()
result = max_price_per_genre.merge(df, on=['genre','price'])
result = result.rename(columns={'genre':'Genre','title':'Title','price':'Price'}).sort_values('Genre')

print(result)"""


def n15():
    """Используя pandas, разбейте книги на 3 ценовые категории. Для каждой категории посчитайте количество книг с разбивкой по рейтингам.



    import requests
from bs4 import BeautifulSoup
import pandas as pd
import math

# Функция для получения всех страниц сайта
def get_all_book_pages(base_url="http://books.toscrape.com/catalogue/page-1.html"):
    pages = []
    url = base_url
    while True:
        response = requests.get(url)
        if response.status_code != 200:
            break
        pages.append(response.text)
        soup = BeautifulSoup(response.text, "html.parser")
        next_page = soup.select_one("li.next a")
        if next_page:
            next_url = next_page.get("href")
            # формируем полный URL для следующей страницы
            url = "/".join(url.split("/")[:-1]) + "/" + next_url
        else:
            break
    return pages

# Функция для парсинга данных о книгах со страницы
def parse_books_from_page(html):
    soup = BeautifulSoup(html, "html.parser")
    books = []
    for book in soup.select("article.product_pod"):
        title = book.h3.a["title"]
        price_str = book.select_one("p.price_color").text
        price = float(price_str[2:])  # убираем символ £ и преобразуем в float
        rating_class = book.select_one("p.star-rating")["class"]
        rating = rating_class[1]  # второй класс содержит рейтинг словом
        rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
        rating_num = rating_map.get(rating, 0)
        books.append({"title": title, "price": price, "rating": rating_num})
    return books

# Получаем все книги
all_pages = get_all_book_pages()
all_books = []
for page_html in all_pages:
    all_books.extend(parse_books_from_page(page_html))

# Создаем DataFrame
df = pd.DataFrame(all_books)

# Разбиваем книги на 3 ценовые категории (низкая, средняя, высокая)
# Для этого используем tertiles (третьи) распределения цены
df['price_category'] = pd.qcut(df['price'], 3, labels=["Low", "Medium", "High"])

# Считаем количество книг в каждой категории по рейтингу
result = df.groupby(['price_category', 'rating']).size().unstack(fill_value=0)

print(result)"""


def n16():
    """Сохраните данные о книгах в БД sqlite3. Напишите функцию, которая по введенному пользователем названию жанра возвращает кол-во книг в этом жанре.



    import requests
from bs4 import BeautifulSoup
import sqlite3

BASE_URL = "http://books.toscrape.com/"

# Функция для получения всех страниц
def get_soup(url):
    r = requests.get(url)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

# Создаем БД и таблицу
conn = sqlite3.connect("books.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    price TEXT,
    genre TEXT
)
''')
conn.commit()

# Получаем список всех жанров
soup = get_soup(BASE_URL)
genres = soup.select("ul.nav.nav-list ul li a")
genre_links = {g.text.strip(): BASE_URL + g['href'] for g in genres}

# Парсим книги по жанрам
for genre_name, genre_url in genre_links.items():
    page_url = genre_url
    while True:
        soup = get_soup(page_url)
        books = soup.select("article.product_pod")
        for book in books:
            title = book.h3.a['title']
            price = book.select_one("p.price_color").text
            cursor.execute(
                "INSERT INTO books (title, price, genre) VALUES (?, ?, ?)",
                (title, price, genre_name)
            )
        conn.commit()
        # Пагинация
        next_page = soup.select_one("li.next a")
        if next_page:
            page_url = "/".join(page_url.split("/")[:-1]) + "/" + next_page['href']
        else:
            break

# Функция для запроса количества книг по жанру
def count_books_by_genre(genre_name):
    cursor.execute("SELECT COUNT(*) FROM books WHERE genre = ?", (genre_name,))
    count = cursor.fetchone()[0]
    return count

# Пример использования
user_genre = input("Введите жанр: ")
print(f"Количество книг в жанре '{user_genre}': {count_books_by_genre(user_genre)}")

# Закрываем соединение с БД
conn.close()"""


def n17():
    """Напишите функцию, которая добавляет новую запись в таблицу. Продемонстрируйте результат



    import requests
from bs4 import BeautifulSoup
import sqlite3

BASE_URL = "http://books.toscrape.com/"

# Функция для получения всех страниц
def get_soup(url):
    r = requests.get(url)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

# Создаем БД и таблицу
conn = sqlite3.connect("books.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    price TEXT,
    genre TEXT
)
''')
conn.commit()

# Получаем список всех жанров
soup = get_soup(BASE_URL)
genres = soup.select("ul.nav.nav-list ul li a")
genre_links = {g.text.strip(): BASE_URL + g['href'] for g in genres}

# Парсим книги по жанрам
for genre_name, genre_url in genre_links.items():
    page_url = genre_url
    while True:
        soup = get_soup(page_url)
        books = soup.select("article.product_pod")
        for book in books:
            title = book.h3.a['title']
            price = book.select_one("p.price_color").text
            cursor.execute(
                "INSERT INTO books (title, price, genre) VALUES (?, ?, ?)",
                (title, price, genre_name)
            )
        conn.commit()
        # Пагинация
        next_page = soup.select_one("li.next a")
        if next_page:
            page_url = "/".join(page_url.split("/")[:-1]) + "/" + next_page['href']
        else:
            break



            conn = sqlite3.connect("books.db")
cursor = conn.cursor()

# Функция для добавления новой книги
def add_book(title, price, genre):
    cursor.execute(
        "INSERT INTO books (title, price, genre) VALUES (?, ?, ?)",
        (title, price, genre)
    )
    conn.commit()
    print(f"Книга '{title}' добавлена в жанр '{genre}' с ценой {price}.")

# Функция для отображения всех книг (для проверки)
def show_all_books():
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    for book in books:
        print(book)

# --- Демонстрация ---
add_book("Новая книга", "12.99", "Фантастика")

print("\nВсе книги в БД после добавления:")
show_all_books()

# Закрываем соединение с БД
conn.close()"""


def n18():
    """# 18 (в юпитере не работает а так работает)


    Воспользовавшись модулем multiprocessing, соберите информацию о всех книгах с сайта (распаралелльте вычисления по страницам каталога)



    import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool, cpu_count
import pandas as pd

BASE_URL = "http://books.toscrape.com/catalogue/page-{}.html"

def get_total_pages():
    url = BASE_URL.format(1)
    resp = requests.get(url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    pager = soup.find("li", class_="current")
    if pager:
        total_pages = int(pager.text.strip().split()[-1])
    else:
        total_pages = 1
    return total_pages

def parse_book(book_soup):
    title = book_soup.h3.a["title"]
    price = book_soup.find("p", class_="price_color").text[1:]
    availability = book_soup.find("p", class_="instock availability").text.strip()
    rating = book_soup.p["class"][1]
    link = book_soup.h3.a["href"]
    return {
        "title": title,
        "price": price,
        "availability": availability,
        "rating": rating,
        "link": link
    }

def parse_page(page_number):
    url = BASE_URL.format(page_number)
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    books = soup.find_all("article", class_="product_pod")
    return [parse_book(b) for b in books]

def run_scraping():
    total_pages = get_total_pages()
    print(f"Всего страниц: {total_pages}")

    with Pool(cpu_count()) as pool:
        all_books = pool.map(parse_page, range(1, total_pages + 1))

    all_books_flat = [book for sublist in all_books for book in sublist]
    df = pd.DataFrame(all_books_flat)
    df.to_excel("books.xlsx", index=False)
    print(f"Собрано книг: {len(df)}")
    print(all_books)

if __name__ == "__main__":
    run_scraping()
"""


def n19():
    """Воспользовавшись dask.delayed, скачайте изображения книг с сайта (распараллельте вычисления по страницам каталога) (использование Dask должно приводить к истинной параллельной обработке данных).



    import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from dask import delayed, compute
from dask.distributed import Client, LocalCluster

BASE_URL = "http://books.toscrape.com/"
OUTPUT_DIR = "book_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_image(img_url, filename):
    try:
        resp = requests.get(img_url, timeout=15)
        resp.raise_for_status()
        with open(filename, "wb") as f:
            f.write(resp.content)
        print(f"[OK] {filename}")
    except Exception as e:
        print(f"[ERR] {img_url} -> {e}")

def process_book(book_url):
    try:
        resp = requests.get(book_url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        img_tag = soup.select_one("div.item img")
        src = img_tag["src"]
        img_url = urljoin(book_url, src)
        filename = os.path.join(OUTPUT_DIR, os.path.basename(img_url).split("?")[0])
        fetch_image(img_url, filename)  # сразу скачиваем
    except Exception as e:
        print(f"[BOOK ERR] {book_url} -> {e}")

def process_page(page_url):
    resp = requests.get(page_url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    books = soup.select("article.product_pod")
    tasks = []
    for book in books:
        href = book.select_one("h3 > a")["href"]
        book_url = urljoin(page_url, href)
        tasks.append(delayed(process_book)(book_url))
    return tasks

def generate_page_urls():
    for i in range(1, 51):
        if i == 1:
            yield BASE_URL
        else:
            yield urljoin(BASE_URL, f"catalogue/page-{i}.html")

def main():
    cluster = LocalCluster(n_workers=8, threads_per_worker=1)
    client = Client(cluster)
    print(client)

    all_tasks = []
    for page_url in generate_page_urls():
        all_tasks.extend(process_page(page_url))  # собираем все задачи книг

    compute(*all_tasks)  # вычисляем все задачи, изображения будут скачаны

    print("✅ All images downloaded.")

if __name__ == "__main__":
    main()"""


def n20():
    """Сохраните информацию о книгах в формате JSONl с разбивкой на файлы по жанрам.



    import requests
from bs4 import BeautifulSoup
import json
import os

BASE_URL = "http://books.toscrape.com/"

# Создаем папку для сохранения файлов
os.makedirs("books_by_genre", exist_ok=True)

def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

# Получаем список жанров
def get_genres():
    soup = get_soup(BASE_URL)
    genre_links = soup.select("ul.nav.nav-list ul li a")
    genres = {}
    for link in genre_links:
        name = link.get_text(strip=True)
        href = link["href"]
        genres[name] = BASE_URL + href
    return genres

# Получаем книги с одной страницы жанра
def get_books_from_page(soup):
    books = []
    for book in soup.select("article.product_pod"):
        title = book.h3.a["title"]
        price = book.select_one("p.price_color").get_text(strip=True)
        availability = book.select_one("p.availability").get_text(strip=True)
        rating_class = book.p["class"]
        rating = rating_class[1] if len(rating_class) > 1 else "None"
        books.append({
            "title": title,
            "price": price,
            "availability": availability,
            "rating": rating
        })
    return books

# Получаем все книги жанра с пагинацией
def get_all_books_in_genre(genre_url):
    books = []
    url = genre_url
    while True:
        soup = get_soup(url)
        books.extend(get_books_from_page(soup))
        next_page = soup.select_one("li.next a")
        if next_page:
            next_href = next_page["href"]
            # строим URL следующей страницы
            url = "/".join(url.split("/")[:-1]) + "/" + next_href
        else:
            break
    return books

# Главная логика
genres = get_genres()
for genre_name, genre_url in genres.items():
    print(f"Парсим жанр: {genre_name}")
    books = get_all_books_in_genre(genre_url)
    filename = f"books_by_genre/{genre_name.replace(' ', '_')}.jsonl"
    with open(filename, "w", encoding="utf-8") as f:
        for book in books:
            f.write(json.dumps(book, ensure_ascii=False) + "\n")
    print(f"Сохранено {len(books)} книг в {filename}")"""


def n21():
    """Считайте данные в виде Dask Bag. Посчитайте, для скольких книг описание имеет больше 10 предложений. Выполните задание с использованием dask.bag, распараллелив процесс обработки данных (использование Dask должно приводить к истинной параллельной обработке данных).



    import re
import requests
from bs4 import BeautifulSoup

import dask.bag as db
from dask.distributed import Client

# ======================
# Функция для скачивания и парсинга
# ======================

BASE = 'http://books.toscrape.com/'

def fetch_html(url):
    Скачивает HTML и возвращает BeautifulSoup.
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        return BeautifulSoup(r.text, 'lxml')
    except Exception as e:
        print(f"ERROR fetching {url}: {e}")
        return None

def get_book_urls_from_page(page_url):
    Возвращает список ссылок на книги на странице каталога.
    soup = fetch_html(page_url)
    if not soup:
        return []

    urls = []
    for a in soup.select('article.product_pod h3 a'):
        href = a.get('href')
        # делаем абсолютную ссылку
        full = requests.compat.urljoin(page_url, href)
        urls.append(full)
    return urls

def get_description_from_book(book_url):
    Извлекает описание книги (если есть).
    soup = fetch_html(book_url)
    if not soup:
        return ""

    # ищем описание
    desc = ""

    # В books.toscrape описание находится в следующем теге:
    # <meta name="description" content="...">
    meta = soup.select_one('meta[name="description"]')
    if meta and meta.get('content'):
        desc = meta.get('content').strip()
    else:
        # fallback: искать по классу
        descr_tag = soup.select_one('#product_description ~ p')
        if descr_tag:
            desc = descr_tag.text.strip()

    return desc

def count_sentences(text):
    Считает количество предложений.
    # простое правило: . ? !
    # можно сложнее, но этого достаточно для примера
    sentences = re.split(r'[.!?]+', text)
    # очищаем пустые
    sentences = [s for s in sentences if s.strip()]
    return len(sentences)

# ======================
# Собираем URL всех страниц каталога
# ======================

def get_all_catalog_pages():
    Собираем все страницы каталога (pagination).
    pages = []
    next_url = BASE + 'catalogue/page-1.html'
    while next_url:
        print(f"Found page: {next_url}")
        pages.append(next_url)

        soup = fetch_html(next_url)
        if not soup:
            break

        nxt = soup.select_one('li.next a')
        if nxt and nxt.get('href'):
            next_url = requests.compat.urljoin(next_url, nxt.get('href'))
        else:
            next_url = None

    return pages

# ======================
# Dask Bag
# ======================

if __name__ == "__main__":
    # запускаем локальный Dask (в логах можно видеть параллельную обработку)
    client = Client()  # можно указать n_workers, threads_per_worker
    print(client)

    # собираем страницы каталога
    catalog_pages = get_all_catalog_pages()

    # 1) делаем Bag из всех страниц каталога
    pages_bag = db.from_sequence(catalog_pages, npartitions=len(catalog_pages))

    # 2) на каждой странице вытаскиваем ссылки на книги
    book_urls_bag = pages_bag.map(get_book_urls_from_page).flatten()

    # 3) получаем описания
    descriptions_bag = book_urls_bag.map(get_description_from_book)

    # 4) считаем, сколько предложений
    sentences_count_bag = descriptions_bag.map(count_sentences)

    # 5) фильтруем > 10
    big_desc_bag = sentences_count_bag.filter(lambda n: n > 10)

    # 6) считаем количество таких описаний
    result = big_desc_bag.count().compute()

    print(f"Количество описаний с > 10 предложениями: {result}")

    client.close()"""


def n22():
    """Сохраните данные о книгах в виде нескольких csv-файлов. Считайте их в виде Dask DataFrame. Выясните, есть ли в датасете книги, на которые оставили хоть один отзыв



    # scrape_books.py

import requests
from bs4 import BeautifulSoup
import os
import csv
from urllib.parse import urljoin

BASE_URL = "http://books.toscrape.com/"

def get_soup(url):
    r = requests.get(url)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def get_categories():
    soup = get_soup(BASE_URL)
    cats = soup.select(".side_categories ul li ul li a")
    return [(c.text.strip(), urljoin(BASE_URL, c["href"])) for c in cats]

def parse_book_page(url):
    soup = get_soup(url)
    table = soup.select_one("table.table.table-striped")
    trs = table.find_all("tr")
    info = {tr.th.text: tr.td.text for tr in trs}
    # Вытягиваем нужные поля
    return {
        "title": soup.select_one("div.product_main h1").text,
        "price": info.get("Price (incl. tax)", ""),
        "availability": info.get("Availability", ""),
        "review_rating": soup.select_one("p.star-rating")["class"][1],
        "num_reviews": int(info.get("Number of reviews", "0"))
    }

def scrape_category(name, url):
    print(f"Scraping category: {name}")
    page_url = url
    os.makedirs("csv_data", exist_ok=True)
    csv_file = os.path.join("csv_data", f"{name.replace(' ', '_')}.csv")

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "price", "availability", "review_rating", "num_reviews", "category"])

        while True:
            soup = get_soup(page_url)
            books = soup.select("article.product_pod h3 a")
            for book in books:
                book_url = urljoin(page_url, book["href"])
                data = parse_book_page(book_url)
                writer.writerow([
                    data["title"], data["price"], data["availability"],
                    data["review_rating"], data["num_reviews"], name
                ])

            next_btn = soup.select_one("li.next a")
            if next_btn:
                page_url = urljoin(page_url, next_btn["href"])
            else:
                break

def main():
    cats = get_categories()
    for name, url in cats:
        scrape_category(name, url)

if __name__ == "__main__":
    main()



    import dask.dataframe as dd

# читаем все CSV
df = dd.read_csv("csv_data/*.csv")

# приводим num_reviews к числу
df["num_reviews"] = df["num_reviews"].astype(int)

df



# считаем число таких книг
has_reviews = df[df["num_reviews"] > 0]["num_reviews"].count().compute()

print("Количество книг с отзывами:", has_reviews)

if has_reviews > 0:
    print("Да — есть книги с хотя бы одним отзывом.")
else:
    print("Нет — в датасете нет книг с отзывами.")"""


def n23():
    """# 23 (тоже в юпитере не работает а так работает)


    Посчитайте кол-во обложек книг, которые по ширине больше, чем по длине. Разбейте весь набор файлов на 4 группы и выполните обработку в 4 процесса.



    import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from multiprocessing import Pool
from io import BytesIO
from PIL import Image

BASE_URL = "http://books.toscrape.com/"

def get_all_cover_urls():
    cover_urls = []
    next_page = BASE_URL + "catalogue/page-1.html"
    while True:
        resp = requests.get(next_page)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Собираем ссылки на обложки из текущей страницы
        for img in soup.select("article.product_pod img"):
            src = img["src"]
            # Приводим к абсолютному URL
            full = urljoin(next_page, src)
            cover_urls.append(full)

        # Пытаемся перейти на следующую страницу
        nxt = soup.select_one("li.next > a")
        if not nxt:
            break
        next_page = urljoin(next_page, nxt["href"])
    return cover_urls

def process_image(url):
    try:
        r = requests.get(url, timeout=10)
        img = Image.open(BytesIO(r.content))
        w, h = img.size
        return 1 if w > h else 0
    except Exception as e:
        print(f"Error with {url}: {e}")
        return 0

if __name__ == "__main__":
    urls = get_all_cover_urls()
    print(f"Total covers found: {len(urls)}")

    # Запускаем 4 процесса
    with Pool(processes=4) as pool:
        results = pool.map(process_image, urls)

    count_wider = sum(results)
    print(f"Number of covers with width > height: {count_wider}")"""