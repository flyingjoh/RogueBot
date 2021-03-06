import config

from telegram.ext.dispatcher import run_async
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import Job

import tornamentmanager
import databasemanager
import usermanager
import telegram
import logging
import os

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger('rg')

question_filename = 'question.int'
question_yes = 0
question_no = 0
asked = [ ]

def reply_job(bot, job):
	c_id, bot, txt, buttons, photo = job.context
	reply(c_id, bot, txt, buttons, photo)

@run_async
def reply(c_id, bot, txt, buttons=None, photo=None):
	if c_id == 0:
		return
	if buttons:
		custom_keyboard = [ ]

		for b in buttons:
			if isinstance(b, list):
				custom_keyboard.append(b)
			else:
				custom_keyboard.append([b])

		reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True)
		bot.sendMessage(c_id, text=txt, reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
	elif len(txt) > 0:
		bot.sendMessage(c_id,
						text=txt, 
						parse_mode=telegram.ParseMode.MARKDOWN)

	if photo:
		bot.sendSticker(c_id, sticker=photo)

def start(bot, update):
	bot.sendMessage(update.message.chat_id, text='Теперь скажи мне свое имя.')
	usermanager.new_user(update.message.chat_id)

def setname(bot, update):
	txt = update.message.text.split()
	if len(txt) > 9:
		name = update.message.text[10:]
		usermanager.setname(update.message.chat_id, name)

		bot.sendMessage(update.message.chat_id, text='Ну хорошо')

def debug_print(bot, update):
	inf = usermanager.debug_info(update.message.chat_id)
	bot.sendMessage(update.message.chat_id, text=inf)

def room(bot, update):
	c_id = update.message.chat_id

	if str(c_id) in config.MODERS_IDS:
		cmd, room_type, name = update.message.text.split()
		usermanager.open_room(c_id, lambda *a, **kw: reply(c_id, bot, *a, **kw), room_type, name)
	else:
		bot.sendMessage(update.message.chat_id, text='NO.')

def give(bot, update):
	if str(update.message.chat_id) in config.MODERS_IDS:
		cmd, item_type, name = update.message.text.split()
		usermanager.give_item(update.message.chat_id, item_type, name)
	else:
		bot.sendMessage(update.message.chat_id, text='NO.')

def pet(bot, update):
	if str(update.message.chat_id) in config.MODERS_IDS:
		cmd, pet, name = update.message.text.split()
		usermanager.new_pet(update.message.chat_id, pet, name)
	else:
		bot.sendMessage(update.message.chat_id, text='NO.')

def notify(bot, update):
	if str(update.message.chat_id) in config.ADMINS_IDS:
		msg = update.message.text[len('/notify'):]

		logger.info(msg)

		for user_id in usermanager.get_telegram_users():
			try:
				reply(user_id, bot, msg)
			except:
				logger.info('Couldn\'t send message to {0}'.format(user_id))
	else:
		bot.sendMessage(update.message.chat_id, text='NO.')

def save_question():
	with open(question_filename, 'w') as f:
		f.write('{0} {1}\n'.format(question_yes, question_no))
		f.write(' '.join(asked))

def zero(bot, update):
	global question_yes, question_no, asked

	if str(update.message.chat_id) in config.ADMINS_IDS:
		question_yes = 0
		question_no = 0

		asked = [ ]

		save_question()
	else:
		bot.sendMessage(update.message.chat_id, text='NO.')

def question_status(bot, update):
	msg ='Да: {0}\nНет: {1}'.format(question_yes, question_no)
	bot.sendMessage(update.message.chat_id, text=msg)

def yes(bot, update):
	global question_yes, asked

	uid = str(update.message.chat_id)

	if uid in asked:
		bot.sendMessage(update.message.chat_id, text='Только 1 раз ;)')
	else:
		question_yes += 1
		bot.sendMessage(update.message.chat_id, text='Голос учтен. Чтобы посмотреть результат, используй /question_status')
		asked.append(uid)

		save_question()

def no(bot, update):
	global question_no, asked

	uid = str(update.message.chat_id)

	if uid in asked:
		bot.sendMessage(update.message.chat_id, text='Только 1 раз ;)')
	else:
		question_no += 1
		bot.sendMessage(update.message.chat_id, text='Голос учтен. Чтобы посмотреть результат, используй /question_status')
		asked.append(uid)

		save_question()

def update_tornament(bot, job):
	global uid, msg, image, buttons
	uid = 0
	msg = ''
	image = None
	buttons = None

	def rep(c_id, txt, btns=None, photo=None):
		global uid, msg, image, buttons

		if uid != 0 and c_id != uid:
			reply(uid, bot, msg, buttons, image)

			msg = ''
			image = None
			buttons = None

		uid = c_id

		msg += '\n\n'
		msg += txt

		if btns:
			buttons = btns
		if photo:
			image = photo

	tornamentmanager.update(rep)
	if len(msg) > 0 or image:
		reply(uid, bot, msg, buttons, image)

def divine_intervention(bot, job):
	logger.info('Divine intervention!')

	for uid in usermanager.get_telegram_users():
		global msg, image, buttons
		msg = ''
		image = None
		buttons = None

		def rep(txt, btns=None, photo=None):
			global msg, image, buttons

			if len(msg) + len(txt) + 2 >= 4096:
				reply(uid, bot, msg, buttons, image)

				msg = ''
				image = None
				buttons = None


			msg += '\n\n'
			msg += txt

			if btns:
				buttons = btns
			if photo:
				image = photo
				
		usermanager.divine_intervention(uid, rep)

		if len(msg) > 0 or image:
			reply(uid, bot, msg, buttons, image)

def msg(bot, update):
	c_id = update.message.chat_id

	global msg, image, buttons
	msg = ''
	image = None
	buttons = None

	def rep(txt, btns=None, photo=None):
		global msg, image, buttons

		if len(msg) + len(txt) + 2 >= 4096:
			reply(c_id, bot, msg, buttons, image)

			msg = ''
			image = None
			buttons = None


		msg += '\n\n'
		msg += txt

		if btns:
			buttons = btns
		if photo:
			image = photo

	usermanager.message(c_id, rep, update.message.text)

	if len(msg) > 0 or image:
		global updater

		send_job = Job(reply_job,
						0.040,
						repeat=False,
						context=(c_id, bot, msg, buttons, image))
		reply(c_id, bot, msg, buttons, image)

def leaderboard(bot, update):
	c_id = update.message.chat_id

	lb = databasemanager.ROOMS_TABLE
	cnt = 10
	if len(update.message.text.split(' ')) >= 2:
		lb = update.message.text.split(' ')[1]
		if len(update.message.text.split(' ')) >= 3:
			try:
				cnt_ = int(update.message.text.split(' ')[2])
				if cnt_ > 0:
					cnt = cnt_
			except:
				pass

	res = databasemanager.get_leaderboard(lb, count=cnt)
	msg = ''

	if lb == 'death':
		for i, r in enumerate(res):
			msg += '{0}. {1}: {2}\n'.format(i + 1, r[0], r[1])
	else:
		for i, r in enumerate(res):
			uid = r['uid']
			name = r['name']
			score = r['score']
			username = bot.getChat(uid)['username']
			death_reason = None
			if 'death_reason' in r:
				death_reason = r['death_reason']

			table_name = "{0}".format(name)
			if len(username) > 0:
				table_name += ' (@{0})'.format(username)
				
			msg += '{0}. {1}: {2}\n'.format(i + 1, table_name, score)
			if death_reason is not None:
				msg += 'Причина смерти: ' + death_reason

			msg += '\n'

	bot.sendMessage(update.message.chat_id, text=msg)

def stop(bot, update):
	usermanager.delete(update.message.chat_id)

def cesar(bot, update):
	v = databasemanager.get_variable('ces', def_val=True)
	databasemanager.set_variable('ces', not v)

def error_callback(bot, update, error):
	error_msg = 'User "%s" had error "%s"' % (update.message.chat_id, error)
	if '429' in str(error):
		logger.warn('429!')
	else:
		logger.warn(error_msg)
	msg = 'Ошибка внутри сервера. Если это мешает играть, сообщите @yegorf1'
	bot.sendMessage(update.message.chat_id, text=msg)
	bot.sendMessage(update.message.chat_id, 
					text='```text\n{0}\n```'.format(error_msg),
					parse_mode=telegram.ParseMode.MARKDOWN)

if __name__ == '__main__':
	if os.path.isfile(question_filename):
		with open(question_filename, 'r') as f:
			question_yes, question_no = map(int, f.readline().split())
			asked = f.readline().split()
			
	if not os.path.isdir(config.USERS_PATH):
		logger.info('Creating users directory')
		os.makedirs(config.USERS_PATH)

	logger.info('Creating Updater...')
	updater = Updater(config.TELEGRAM_TOKEN)

	updater.dispatcher.add_handler(CommandHandler('leaderboard', leaderboard))
	updater.dispatcher.add_handler(CommandHandler('setname', setname))
	updater.dispatcher.add_handler(CommandHandler('notify', notify))
	updater.dispatcher.add_handler(CommandHandler('debug', debug_print))
	updater.dispatcher.add_handler(CommandHandler('cesar', cesar))
	updater.dispatcher.add_handler(CommandHandler('start', start))
	updater.dispatcher.add_handler(CommandHandler('stop', stop))
	updater.dispatcher.add_handler(CommandHandler('room', room))
	updater.dispatcher.add_handler(CommandHandler('give', give))
	updater.dispatcher.add_handler(CommandHandler('pet', pet))


	updater.dispatcher.add_handler(CommandHandler('question_status', question_status))
	updater.dispatcher.add_handler(CommandHandler('zero', zero))
	updater.dispatcher.add_handler(CommandHandler('yes', yes))
	updater.dispatcher.add_handler(CommandHandler('no', no))
	updater.dispatcher.add_handler(MessageHandler(False, msg))
	updater.dispatcher.add_error_handler(error_callback)

	intervention_job = Job(divine_intervention, 3 * 60 * 60.0)
	update_tornament_job = Job(update_tornament, 10.0)
	updater.job_queue.put(intervention_job)
	updater.job_queue.put(update_tornament_job)

	logger.info('Starting polling...')
	updater.start_polling()

	logger.info('Bot now officially started!')
	updater.idle()
