import os, time
from dotenv import load_dotenv
from exchange import make_exchange, fetch_ohlcv_df
from config import SYMBOLS, TIMEFRAMES, PARAMS
from strategy import detect
from notifier import cooldown_ok, send_telegram, format_signal

def main():
    load_dotenv()
    ex = make_exchange()

    while True:
        for symbol in SYMBOLS:
            try:
                df15 = fetch_ohlcv_df(ex, symbol, TIMEFRAMES["entry"], limit=300)
                df1h = fetch_ohlcv_df(ex, symbol, TIMEFRAMES["bias"], limit=300)
                df4h = fetch_ohlcv_df(ex, symbol, TIMEFRAMES["regime"], limit=300)

                sig = detect(df15, df1h, df4h, symbol, PARAMS)
                if sig:
                    key = f"{symbol}:{sig.side}"
                    if cooldown_ok(key, PARAMS["cooldown_minutes"]):
                        send_telegram(format_signal(sig))

            except Exception as e:
                # print errors for debugging
                print("ERR", symbol, str(e))

        time.sleep(60)  # scan every minute

if __name__ == "__main__":
    main()