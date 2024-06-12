"""Импортируем необходимые библиотеки."""
import requests


def apikey_validation(key_list: list) -> str:
    """Создаём функцию проверки актуальности Scopus API Key."""
    # key = input('Введите актуальный API Key: ')
    query_key_test = 'xenon'
    # check = pub_counts(key, query_key_test)
    for key in key_list:
        if int(pub_counts(key, query_key_test)):
            break
        else:
            continue
    return key


# key = '4ec2b5c76d9d72e9a34d16848908723b'
# query = 'xenon'


def pub_counts(key: str, query: str) -> int:
    """Запрос на количество публикаций в Scopus."""
    url: str = 'https://api.elsevier.com/content/search/scopus?start=0&count=1'
    try:
        res = requests.get(f'{url}&query={query}&apiKey={key}')
    except Exception as e:
        return ('Error', e)
    return res.json()['search-results']['opensearch:totalResults']


# print(pub_counts(key, query))
