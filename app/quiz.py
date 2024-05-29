from os import path


PSYCHOTYPES_IMG_FOLDER = 'images'

PSYCHOTYPES = {'kinesthetic': {'rus': 'кинестетик',
                               'image': path.join(PSYCHOTYPES_IMG_FOLDER, 'kinesthetic.png'),
                               'garden': '«Сад объятий»',
                               'description': '. В нем максимально комфортно и приятно находиться. '
                                              'Здесь можно пройтись босиком теплому дереву террасной доски, '
                                              'согретому на солнце природному камню или мягкой свежескошенной траве.\n\n'
                                              'Идя мимо растительных композиций, можно ощущать руками касания нежных '
                                              'колосков злаков или прикоснуться к хвойным растениям '
                                              'и ощутить их текстуру. Можно собрать букет из свежесрезанных '
                                              'многолетних цветов и поставить их в вазу на стол.\n\n'
                                              'Мягкая мебель на террасе не позволит пройти мимо, так и хочется '
                                              'присесть и полюбоваться на красоту пейзажа вокруг. '
                                              'Мягкие подушки, плед создают дополнительный уют. '
                                              'Свечи и элементы рукотворного декора создадут '
                                              'душевную атмосферу в вашем саду.'},

               'visual': {'rus': 'визуал',
                          'image': path.join(PSYCHOTYPES_IMG_FOLDER, 'visual.png'),
                          'garden': '«Сад искусств»',
                          'description': ', где есть яркие акценты, живые картины, '
                                         'нарисованные словно самой природой. Акцентные цвета растений, '
                                         'формы и текстуры листьев создают непередаваемые эмоции, которые радуют глаз. '
                                         'Сад – это место созерцания изящных изгибов дорожек, нависающих деревьев, '
                                         'изучения сложных деталей и фактур всех материалов. '
                                         'Силуэты деревьев, очертания лужаек и цветников, дополняют друг друга, '
                                         'образуя гармоничную садовую композицию. Так и хочется сделать фотографию '
                                         'или нарисовать картину вашего пейзажа.'},

               'audial': {'rus': 'аудиал',
                          'image': path.join(PSYCHOTYPES_IMG_FOLDER, 'audial.png'),
                          'garden': '«Сад чувств»',
                          'description': ', который состоит из множества тихих уголков и зеленых комнат. '
                                         'Здесь вы сможете насладиться тишиной и покоем, '
                                         'прогуляться по плавным дорожкам, послушать шелест листвы на деревьях, '
                                         'насладиться пением птиц и понаблюдать за колыханием злаков. '
                                         'Многолетние растения в цветниках наполнят воздух приятной успокаивающей '
                                         'летней мелодией и создадут атмосферу свежести и умиротворения, '
                                         'помогут отвлечься от городской суеты и шума.'}}

PSYCHOTYPES_NAMES = tuple(PSYCHOTYPES.keys())

KINESTHETIC, VISUAL, AUDIAL = PSYCHOTYPES_NAMES

QUIZ = (('За что вы цените жизнь за городом?',

         {KINESTHETIC: 'Большая территория для игры с детьми и животными, много разных зон, большая парковка',
          AUDIAL: 'Хочется больше природы и не слышать соседей',
          VISUAL: 'Возможность создать красивый сад с разными зонами отдыха, цветниками и деревьями'}),


        ('Какие материалы для дорожек вы предпочитаете?',

         {AUDIAL: 'Натуральные каменные плиты, отсев, каменная крошка',
          KINESTHETIC: 'Тротуарная плитка, декинг',
          VISUAL: 'Клинкерный кирпич, природный камень'}),


        ('Выберите группу растений, которые вам нравятся больше остальных?',

         {VISUAL: 'Клен, бересклет, магнолия, рябина, сосна ниваки, багряник, спирея, пузыреплодник',
          AUDIAL: 'Ива, осина, береза, вейник, молиния, осока, мискантус',
          KINESTHETIC: 'Сирень, роза ругоза, чубушник, гортензия, черемуха, мелисса, вербена'}),


        ('В какой зоне сада вы предпочтете провести свой вечер?',

         {KINESTHETIC: 'В зоне барбекю или летней кухни',
          AUDIAL: 'В большой компании на патио под свет гирлянд и фонарей',
          VISUAL: 'Костровая зона в компании 2-4 человек'}),


        ('Какую планировку сада вы выберите?',

         {AUDIAL: 'Плавные природные линии, места отдыха с водными объектами, тихие зоны для бесед с друзьями',
          VISUAL: 'Различные места отдыха с эффектными видовыми точками и живописным окрестным пейзажем',
          KINESTHETIC: 'Уютные зеленые комнаты, внутренний дворик, веранда, беседка, многочисленные островки отдыха'}),


        ('Опишите ваше утро',

         {KINESTHETIC: 'Пью кофе сидя на мягком диване. '
                       'Сад наполнен ароматом аппетитных яблок, меня окружают растения необычных форм и фактур',
          VISUAL: 'Прогуливаюсь по саду, любуясь яркими утренними цветами, росой на траве. '
                  'Лужайка ровная, обрамленная извилистыми дорожками идеально вписанными в ландшафт',
          AUDIAL: 'Сижу на террасе, слушаю пение птиц, играет приятная музыка'}),


        ('Как бы вы провели 2 часа свободного времени в саду?',

         {AUDIAL: 'Полежу в шезлонге в тени деревьев, послушаю шелест листвы и звуки природы',
          VISUAL: 'Проведу осмотр участка на предмет сорняков и разросшихся растений и приведу его в порядок',
          KINESTHETIC: 'Присмотрю в интернет-магазине декор для своего участка или смастерю его самостоятельно'}),


        ('Какую часть дня вы любите проводить в саду?',

         {KINESTHETIC: 'Днем',
          VISUAL: 'Вечером',
          AUDIAL: 'Утро'}),


        ('Как часто вы приглашаете друзей и большие компании?',

         {AUDIAL: 'Каждую неделю и чаще',
          KINESTHETIC: 'Редко, может раз в несколько месяцев',
          VISUAL: 'Пару раз в месяц'}),


        ('Какие ощущения вы хотите испытывать чаще в своем саду?',

         {VISUAL: 'Чувствуете себя свободно, наполняюсь энергией и силой',
          AUDIAL: 'Вам умиротворенно, легко, в полной безопасности – это мой мир',
          KINESTHETIC: 'Вам уютно, спокойно, комфортно'}))


QUIZ_LEN = len(QUIZ)


def get_question_by_position(position: int) -> tuple[str, dict]:
    try:
        return QUIZ[position]
    except IndexError:
        return QUIZ[0]
