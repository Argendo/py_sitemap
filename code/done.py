import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
import csv
import threading

FIRST_URL=str(input())
#FIRST_URL='https://crawler-test.com'
#FIRST_URL='https://yandex.ru'
GLOBAL_LINKS = {}
UNIQ_LINKS = []
BAD_PREFS=['#', 'mailto:', 'tel:']
HEADERS = {
# Прокинем парочку header'ов в запросе, чтобы сайт не посчитал данный скрипт за бота
'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}


def get_html(url):
	r = requests.get(url, headers=HEADERS)
	return r.text

def get_links(cur_url, html):
	soup = BeautifulSoup(html, 'lxml')
	page_links=[]
	# Обработка ссылок
	for a in soup.find_all('a', href=True):
		temp_link = a['href'].strip()
		# Проверка на то, чтобы ссылка не являлась якорной/ссылкой на почту/ссылкой на телефон 
		if not temp_link.startswith(tuple(BAD_PREFS)):
			# Приведение относительных ссылок к абсолютным
			if temp_link[:1]=='/':
				temp_link=str(str(FIRST_URL)+temp_link)
				page_links.append(str(temp_link)+' '+str(temp_link.text))
			else:
				page_links.append(temp_link)
	# Добавление в словарь со структурой "ключ: массив значений"
	GLOBAL_LINKS.update({str(cur_url): page_links})
	# Генератор для обхода в глубину
	my_gen = (get_links(link, get_html(temp_link)) for link in page_links if (not link in GLOBAL_LINKS) and link[:len(cur_url)]==str(cur_url))
	for link in page_links:
		try:
			next(my_gen)
		except StopIteration:
			break


# Просто функция для записи в .csv файл
def db_write(data):
	with open('dict.csv', 'w') as f:
		writer = csv.writer(f)
		for key, value in data.items():
			writer.writerow([key, value])

def main():
	try:
		print("Пожалуйста, подождите, парсинг может занять некоторое время...")
		get_links(FIRST_URL, get_html(FIRST_URL))
		# В отдельном потоке запишем все ссылки в .csv файл
		t = threading.Thread(target=db_write, name='thread', args=(GLOBAL_LINKS,))
		t.start()
		t.join()
		print(GLOBAL_LINKS)
		print(len(GLOBAL_LINKS))
	except ValueError:
		print("Пожалуйста, введите ссылку.\nНапример: https://yandex.ru")
	except Exception:
		print("Что-то пошло не так")

if __name__=='__main__':
	main()
