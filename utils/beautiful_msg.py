from aiogram.utils.markdown import hbold, hlink

def beautiful_procedure(row_data):
    card = f'{hlink(title="{}[{}]".format(row_data.get("owner"), row_data.get("id")), url=row_data.get("link"))}\n' \
               f'{hbold("Наименование: ")}{row_data.get("name")}\n' \
               f'{hbold("НДС: ")}{"{} %".format(row_data.get("nds")) if row_data.get("useNDS") else "Нет"}\n' \
               f'{hbold("Начало: ")}{row_data.get("reBiddingStart")}\n' \
               f'{hbold("Окончание: ")}{row_data.get("reBiddingEnd")}\n🔥'
    return card


def beautiful_positions(row_data):
    id_msg = f'[{hbold("КЛ-"+ row_data["common_message"]["Id"])}]\n'

    if row_data['common_message']:
        common = {k:v for k,v in row_data['common_message'].items() if v}
        common_msg = ''
        if common.get('ownerSrok'):
            common_msg += f'{hbold("Условия оплаты: ")}{common.get("ownerSrok")}\n'
        if common.get('ownerSklad'):
            common_msg += f'{hbold("Сроки поставки: ")}{common.get("ownerSklad")}\n'
        if common.get('deliveryPlace'):
            common_msg += f'{hbold("deliveryPlace: ")}{common.get("deliveryPlace")}\n'

    if row_data['positions']:
        position_msg = ''
        for pos in row_data['positions']:
            position_msg += f'{hbold("Наименование: ")}{pos.get("name")}\n' \
                            f'{hbold("Количество: ")}{pos.get("totalCount")} {pos.get("unit")}\n' \
                            f'{hbold("Цена: ")}{pos.get("price")}\n\n'

    print_msg = f'{id_msg}\nУсловия:\n{common_msg}\nПозиции:\n{position_msg}'
    return print_msg

