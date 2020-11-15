# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import threading
import sqlite3
from sqlite3 import Error
import json

FIRST_URL=str(input("Введите ссылку: "))
# общий словарь ссылок для проверки
GLOBAL_LINKS = {}
BAD_PREFS=['#', 'mailto:', 'tel:']
HEADERS = {
# Прокинем парочку header'ов в запросе, чтобы сайт не посчитал данный скрипт за бота
'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

# SQL запрос для создания таблицы
CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS links(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	page_name TEXT,
	page_link TEXT NOT NULL,
	url_name TEXT,
	url_link TEXT
);
"""

# Общий словарь ссылок, с которым будет дальше работать скрипт
DATA_DICT={}

def get_html(url):
	r = requests.get(url, headers=HEADERS)
	return r.text

# Получение тайтла обрабатываемой страницы
def get_title(url):
	soup = BeautifulSoup(get_html(url), 'lxml')
	try:
		title = str(soup.find('title').text.strip().replace("\n","").replace("\r",""))
		# Удаление лишних пробелов из тайтла
		while "  " in title:
			title=title.replace("  ", " ")
	except:
		title = ""
	
	return json.loads(json.dumps(title))

def get_links(cur_url, html):
	soup = BeautifulSoup(html, 'lxml')
	page_links={}
	temp = {}
	urls=[]
	# Обработка ссылок
	for a in soup.find_all('a', href=True):
		temp_link = a['href'].strip()
		print("\033[32m\033[1m{}\033[0m".format("Parsing: ")+temp_link)
		name = str(a.text)
		# Проверка на то, чтобы ссылка не являлась якорной/ссылкой на почту/ссылкой на телефон 
		if not temp_link.startswith(tuple(BAD_PREFS)):
			if not len(temp_link) == 0:
				# Приведение относительных ссылок к абсолютным
				if temp_link[:1]=='/':
					temp_link=str(str(FIRST_URL)+temp_link)
					page_links.update({name: str(temp_link)})
					urls.append(temp_link)
				else:
					page_links.update({name: temp_link})
					urls.append(temp_link)
	# Вызов функции получения тайтла ссылки
	cur_name = get_title(cur_url)
	# Добавление в словарь со структурой "ключ: словарь", где словарь представляет собой "ключ(тайтл ссылки): словарь "ключ: значение" всех ссылок, что есть на данной странице "
	DATA_DICT.update({cur_url: {cur_name: page_links}})
	GLOBAL_LINKS.update({str(cur_url): page_links})
	# Генератор для обхода в глубину
	my_gen = (get_links(link, get_html(temp_link)) for link in urls if (not link in GLOBAL_LINKS) and link[:len(cur_url)]==str(cur_url))
	for link in urls:
		try:
			next(my_gen)
		except StopIteration:
			break


# Функция подключения к БД
def create_connection(path):
	connection = None
	try:
		connection = sqlite3.connect(path)
		print("\033[34m\033[1m{}\033[0m".format("Подключение к базе данных прошло успешно"))
	except Exception as exc:
		print(exc)
	
	return connection

# Функция создания таблицы
def create_table_exec(connection, query):
	cursor = connection.cursor()
	try:
		cursor.execute(str(query))
		connection.commit()
		print("\033[34m\033[1m{}\033[0m".format('Успешно создана таблица "links"'))
	except Error as e:
		print(f"The error '{e}' occurred")

# Функция записи в базу данных
def db_write(connection, data):
	cursor = connection.cursor()
	for key in data:
		page_name = key
		page_link = get_title(key)
		try:
			for sec_key in data[key][page_link]:
				if not len(data[key][page_link]) == 0:
					url_name = str(sec_key)
					url_link = str(data[key][page_link][sec_key])
				else:
					url_name = ""
					url_link = ""
				try:
					cursor.execute('INSERT INTO links(page_name, page_link, url_name, url_link) VALUES (?, ?, ?, ?)', [page_name, page_link, url_name, url_link])
					connection.commit()
				except Exception as exc:
					print("\033[31m\033[1m{}\033[0m".format("Ошибка!"))
					print(exc)
					break
		except Exception as exc:
			print("\033[31m\033[1m{}\033[0m".format("Ошибка!"))
			print(exc)
			break


def main():
	try:
		print("\033[34m\033[1m{}\033[0m".format("Пожалуйста, подождите, парсинг может занять некоторое время..."))		
		t = threading.Thread(target=get_links, name='thread', args=(FIRST_URL, get_html(FIRST_URL), ))
		t.start()
		t.join()
		# Дамп в json файл для удобства работы со словарём
		with open('json_dump.txt', 'w') as json_file:
			json.dump(DATA_DICT, json_file)
		con = create_connection('./result.db')
		data = json.loads(open('./json_dump.txt').read())
		create_table_exec(con, CREATE_TABLE_QUERY)
		print("\033[34m\033[1m{}\033[0m".format("Пожалуйста, подождите, идёт сохранение в базу данных"))
		db_write(con, data)
		print("\033[32m\033[1m{}\033[0m".format('Данные успешно сохранены в файл "result.db"'))
	except ValueError:
		print("\033[31m\033[1m{}\033[0m".format("Ошибка!"))
		print("Пожалуйста, введите ссылку.\nНапример: https://yandex.ru")
	except Exception as exc:
		print("\033[31m\033[1m{}\033[0m".format("Что-то пошло не так"))
		print(exc)
if __name__=='__main__':
	main()
