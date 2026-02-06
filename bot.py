import os
import asyncio
import logging
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TOPIC_ID = int(os.getenv("TOPIC_ID"))
TEAM = os.getenv("TEAM", "@AntFrolov,@Alexander_Malofeev,@MalashkinaTV,@alexandertebekin,@lapiosta,@GrigoryGol").split(",")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeeklyBot:
    def __init__(self):
        self.responses = {}
    
    async def start(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle_message))
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        logger.info("✅ Бот запущен для 'ВИ_Развитие' тема 21")
        await self.send_to_topic("🤖 Бот для еженедельных отчетов запущен!")
        await self.scheduler()
    
    async def handle_message(self, update: Update, context):
        if update.message.message_thread_id != TOPIC_ID:
            return
        user = f"@{update.message.from_user.username}"
        text = update.message.text.lower()
        if user in TEAM and any(w in text for w in ['готово', 'выполнено', 'сделано', 'готов']):
            self.responses[user] = datetime.now()
            await update.message.reply_text(f"✅ {user} отметился в {self.responses[user].strftime('%H:%M')}", quote=True)
            logger.info(f"{user} ответил")
    
    async def send_to_topic(self, text, parse_mode='Markdown'):
        try:
            await self.app.bot.send_message(
                chat_id=CHAT_ID,
                message_thread_id=TOPIC_ID,
                text=text,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False
    
    async def send_weekly_task(self):
        self.responses.clear()
        message = f"📢 **ЕЖЕНЕДЕЛЬНОЕ ОБНОВЛЕНИЕ ДАННЫХ!**\n\nКоллеги {', '.join(TEAM)},\nобновите данные до *17:00*!\n\n✅ **Как подтвердить:** Напишите «Готово»\n\n⏰ **Дедлайн:** 17:00\n👥 **Ожидаем:** {len(TEAM)} человек\n📅 {datetime.now().strftime('%d.%m.%Y')}"
        await self.send_to_topic(message)
        logger.info("📨 Напоминание отправлено")
    
    async def send_reminder(self):
        not_responded = [u for u in TEAM if u not in self.responses]
        if not_responded:
            message = f"⏰ **ДО ДЕДЛАЙНА 1 ЧАС!**\n\nЕще не отчитались:\n" + "\n".join(f"• {u}" for u in not_responded) + f"\n\nПожалуйста, напишите «Готово»!"
            await self.send_to_topic(message)
            logger.info(f"🔔 Напоминание для {len(not_responded)}")
    
    async def send_report(self):
        responded = list(self.responses.keys())
        not_responded = [u for u in TEAM if u not in self.responses]
        report = f"📊 **ИТОГОВЫЙ ОТЧЕТ**\n\n✅ **Выполнили ({len(responded)}/{len(TEAM)}):**\n"
        if responded:
            for user in responded:
                time_str = self.responses[user].strftime('%H:%M')
                report += f"• {user} — {time_str}\n"
        else:
            report += "—\n"
        report += f"\n❌ **Не выполнили ({len(not_responded)}):**\n"
        if not_responded:
            for user in not_responded:
                report += f"• {user}\n"
        else:
            report += "—\n"
        report += f"\n---\n📈 **Выполнение:** {len(responded)*100//len(TEAM)}%"
        await self.send_to_topic(report)
        logger.info("📄 Отчет отправлен")
    
    async def scheduler(self):
        logger.info("⏰ Планировщик запущен (ПН 9:00, 16:00, 17:10)")
        while True:
            now = datetime.now()
            if now.weekday() == 0 and now.hour == 9 and now.minute == 0:
                await self.send_weekly_task()
                await asyncio.sleep(60)
            if now.weekday() == 0 and now.hour == 16 and now.minute == 0:
                await self.send_reminder()
                await asyncio.sleep(60)
            if now.weekday() == 0 and now.hour == 17 and now.minute == 10:
                await self.send_report()
                await asyncio.sleep(60)
            await asyncio.sleep(30)

async def main():
    bot = WeeklyBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
