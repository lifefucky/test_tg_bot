from typing import List

import requests
import pandas

sarmat_categories = {
    'Бытовая химия': [1811],
    'Хозтовары': [1817, 1794]
}

my_categories = {
    'Автоматизация бизнес-процессов': 1131,
    'Компьютеры': 1117
}

class OnlineContract:
    def __init__(self):
        self.categories = []

        self.procedures_url = "https://api.onlc.ru/purchases/v1/public/procedures"
        self.procedures_params = {}
        self.procedures_kc = ['id', 'type', 'name', 'date', 'status', 'useNDS', 'nds', 'reBiddingStart', 'reBiddingEnd',
                            'owner']

        self.positions_url = "https://api.onlc.ru/purchases/v1/public/procedures/|/positions"

    def build_procedures_params(self, categories):
        params = {'total': True,
                  'limit': 100,
                  'offset': 0,
                  'include': 'owner',
                  'sort': '-startAt',
                  'filters[status]': 1,
                  'filters[searchType]': 2,
                  'filters[categories]': categories}
        self.procedures_params = params
        return self

    def fetch_current_procedures(self):
        response = requests.get(self.procedures_url, params=self.procedures_params)
        data = {}
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"Request failed with status code {response.text}")
        return data

    def get_procedures(self, categories: List):
        self.build_procedures_params(categories)
        data = self.fetch_current_procedures()

        df = pandas.DataFrame()

        if data['data']:
            df = pandas.DataFrame(data['data'])
            df['owner'] = df['owner'].apply(lambda x: x['name'])
            df = df[self.procedures_kc]

            df['link'] = df['id'].apply(lambda x: f"https://onlinecontract.ru/tenders/{x}")
        return df.to_dict(orient='records')

    def build_positions_url(self, procedure_id):
        url_list = self.positions_url.split('|')
        url_list.insert(1, str(procedure_id))
        self.positions_url = ''.join(url_list)
        return self

    def fetch_positions(self):
        response = requests.get(self.positions_url)
        data = {}
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"Request failed with status code {response.text}")
        return data

    def get_positions(self, procedure_id):
        self.build_positions_url(procedure_id)
        data = self.fetch_positions()

        position_keys = ['name', 'totalCount', 'unit', 'price']
        common_message_keys = ['ownerSrok', 'ownerSklad', 'deliveryPlace']

        if data:
            data = data['data']

            common_message = [{key: row[key] for key in common_message_keys} for row in data]
            common_message_unique = {frozenset(d.items()): d for d in common_message}.values()
            common_message_unique = list(common_message_unique)

            if len(common_message_unique) == 1:
                common_message_unique = common_message_unique[0]
            else:
                common_message_unique = {}
                position_keys += common_message_keys

            common_message_unique.setdefault('Id', str(procedure_id))

            positions = [{key: row[key] for key in position_keys} for row in data]
            data = {'common_message': common_message_unique, 'positions': positions}
        return data



'''
online_cr = OnlineContract()
data = online_cr.get_positions(procedure_id=513323)

print(data)
'''
