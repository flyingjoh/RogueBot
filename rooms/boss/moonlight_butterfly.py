import random

name = 'Лунная Бабочка'

hp = 49500
damage_range = ( 0, 49 )

coins = random.randrange( 1000, 20000, 1 )


def skill_preparing(user, reply, boss):
  msg = (
    'Ты услышал громыхающее рычание и увидел, что Лунная Бабочка выпускает ядовитую пыльцу.'
  )

  reply(msg)
