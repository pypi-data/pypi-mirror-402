# pytaxapi – асинхронная библиотека Python для отправки чеков в приложении Мой Налог

## Использование
1. pip install pytaxapi

```main.py
import asyncio
from pytaxapi import Client
from pytaxapi.models import Receipt, TaxServices, TaxClient

client = Client(
    taxpayer_id="1234567890", // ИНН
    password="password", // Пароль от личного кабинета
    timeout=10 // Максимальное время выполнения запроса в секундах
)

async def main():
    receipt = Receipt(
        operation_time="2026-01-10T23:59:59+03:00", // Дата и время проведения операции
        services=[
            TaxServices(
                name=f"Подписка на новостной канал",
                amount=3600,
                quantity=1
            )
        ],
        total_amount="3600",
        client=TaxClient(),
    )

    response = await client.send_receipt(receipt=receipt)
        

if __name__ == "__main__":
    asyncio.run(main())
```