import asyncio
from dassco_utils.messaging import AsyncRabbitMqClient

async def handler_one(msg, props):
    print('Handler One Running')
    await asyncio.sleep(5)
    print('Handler One Completed')

async def handler_two(msg, props):
    print('Handler Two Running')
    await asyncio.sleep(2)
    print('Handler Two Completed')

async def main():
    client = AsyncRabbitMqClient()

    await client.publish('test_queue', 'Hello World')
    await client.publish('test_queue2', 'Hello World')

    await client.add_handler('test_queue', handler_one)
    await client.add_handler('test_queue2', handler_two)
    await client.loop()

asyncio.run(main())