import asyncio
import subprocess
import sys

async def run_cod_bot():
    """Запускает бота для генерации QR-кодов (cod.py)"""
    process = await asyncio.create_subprocess_exec(
        sys.executable, "cod.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return process

async def run_forwarder_bot():
    """Запускает бота-пересыльщика сообщений (bot.py)"""
    process = await asyncio.create_subprocess_exec(
        sys.executable, "bot.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return process

async def main():
    # Запускаем оба бота параллельно
    cod_process, forwarder_process = await asyncio.gather(
        run_cod_bot(),
        run_forwarder_bot()
    )

    # Ждем завершения (хотя боты должны работать бесконечно)
    await asyncio.gather(
        cod_process.wait(),
        forwarder_process.wait()
    )

if __name__ == "__main__":
    asyncio.run(main())