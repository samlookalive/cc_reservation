import telegram
import asyncio

async def main(): #실행시킬 함수명 임의지정
    #token = 'https://api.telegram.org/bot6259535023:AAFjdZ_7n78PeKzk4vdyxCI1C8_08NrVle8/getUpdates'
    token = "6259535023:AAFjdZ_7n78PeKzk4vdyxCI1C8_08NrVle8"
    bot = telegram.Bot(token = token)
    await bot.send_message('5328028034',"하하")

asyncio.run(main()) #봇 실행하는 코드
