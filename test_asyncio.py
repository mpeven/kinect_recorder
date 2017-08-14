import asyncio
import datetime as dt

async def record_stuff(encrypt_queue):
    vid = 0
    while True:
        print("Recording {}".format(vid))
        await asyncio.sleep(5)
        print("Recording {} done".format(vid))
        await encrypt_queue.put((vid,vid,vid))
        vid += 1

async def encrypt_stuff(encrypt_queue, tar_queue):
    while True:
        rgb_vid, depth_vid, metadata = await encrypt_queue.get()
        print("Encrypting video {}".format(rgb_vid))
        await asyncio.sleep(1)
        print("Encrypting video {} done".format(rgb_vid))
        await tar_queue.put((rgb_vid, depth_vid, metadata))

async def tar_stuff(tar_queue):
    while True:
        rgb_vid, depth_vid, metadata = await tar_queue.get()
        print("Tarring video {}".format(rgb_vid))
        await asyncio.sleep(10)
        print("Tarring video {} done".format(rgb_vid))


loop = asyncio.get_event_loop()
encrypt_queue = asyncio.Queue(loop=loop)
tar_queue = asyncio.Queue(loop=loop)

record_coro = record_stuff(encrypt_queue)
encrypt_coro = encrypt_stuff(encrypt_queue, tar_queue)
tar_coro = tar_stuff(tar_queue)

loop.run_until_complete(asyncio.gather(record_coro, encrypt_coro, tar_coro))
loop.close()
