import asyncio
import httpx
import os
import sys
from dotenv import load_dotenv
from decimal import Decimal, ROUND_HALF_UP

load_dotenv()
oanda_platform = os.environ.get('OANDA_PLATFORM')
oanda_account = os.environ.get('OANDA_ACCOUNT')
oanda_API_key = os.environ.get('OANDA_API_KEY')


async def get_token():
    async with httpx.AsyncClient() as client:
        url = "http://localhost:5001/auth/login/"
        response = await client.post(url,
                              headers={'Content-Type': 'application/json'},
                              json={'email': 'kennethqzw@gmail.com', 'password': 'Qwe123!!'})
        if response.status_code == 200:
            try:
                return response.json()['access']
            except KeyError:
                raise ValueError(f"Access token not found in response. {response.text}")


async def fetch_market_data(instrument_name):
    try:
        async with httpx.AsyncClient() as client:
            print(f'instrument: {instrument_name}')
            response = await client.get(f'{oanda_platform}/v3/accounts/{oanda_account}/candles/latest?candleSpecifications={instrument_name}:D:M', headers={'Authorization': 'Bearer ' + oanda_API_key})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None


async def analyze_data_and_trade(data):
    print("Analyzing data...")
    highest = float('-inf')
    lowest = float('inf')
    current_price = None
    print(data)
    for instrument in data['latestCandles']:
        candles = instrument['candles']
        for candle in candles:
            high = float(candle['mid']['h'])
            low = float(candle['mid']['l'])
            if high > highest:
                highest = high
            if low < lowest:
                lowest = low
            current_price = float(candle['mid']['c'])
        if 'JPY' in instrument['instrument']:
            rounded_high = f"{highest:.2f}"
            rounded_low = f"{lowest:.2f}"
        else:
            rounded_high = f"{highest:.5f}"
            rounded_low = f"{lowest:.5f}"
    await asyncio.sleep(15)
    print("Trade signal based on data")
    stop_loss_price = rounded_high
    take_profit = rounded_low
    units = -8888
    return True, stop_loss_price, take_profit, units


async def create_market_order_oanda(token, instrument_name, stop_loss_price, take_profit_price, units):
    async with httpx.AsyncClient() as client:
        script_path = os.path.abspath(__file__)
        url = "http://localhost:5001/api/order/oanda/create/"
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        data = {
            'instrument': instrument_name,
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price,
            'units': units,
            'script_path': script_path
        }
        response = await client.post(url, headers=headers, json=data)
        if response.status_code == 201:
            return True
        else:
            print(f'{response.status_code}: {response.text}')
            return False


async def trading_loop(instrument_name):
    while True:
        access_token = await get_token()
        data = await fetch_market_data(instrument_name)
        signal, stop_loss_price, take_profit, units = await analyze_data_and_trade(data)
        if signal:
            result = await create_market_order_oanda(access_token, instrument_name, stop_loss_price, take_profit, units)
            if result:
                break
        await asyncio.sleep(5)


def main(instrument_name):
    try:
        asyncio.run(trading_loop(instrument))
    except asyncio.CancelledError:
        print("Operation was cancelled.")

if __name__ == '__main__':
    # Example usage: python script.py USD_JPY
    if len(sys.argv) < 2:
        print("Usage: python <script.py> <instrument_name>")
        sys.exit(1)
    instrument = sys.argv[1]
    asyncio.run(trading_loop(instrument))
