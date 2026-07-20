from pathlib import Path
from typing import Optional

from starry_stocks_common.config_loader import load_config, save_config

CONFIG_DIR = Path(__file__).parent / 'configs'


def get_universe() -> list[str]:
    config = load_config(str(CONFIG_DIR / 'config.yaml'))
    return config.get('search_set', [])


def set_universe(tickers: list[str]) -> list[str]:
    config_path = str(CONFIG_DIR / 'config.yaml')
    config = load_config(config_path)
    config['search_set'] = tickers
    save_config(config, config_path)
    return tickers


def get_sell_puts_config(tickers: Optional[list[str]] = None) -> dict:
    config = load_config(str(CONFIG_DIR / 'config.yaml'))
    config.update(load_config(str(CONFIG_DIR / 'config_sell_puts.yaml')))

    if tickers:
        config['search_set'] = tickers

    return config


def get_put_credit_spread_configs(tickers: Optional[list[str]] = None) -> tuple[dict, dict]:
    """Returns (merged_config, put_spreads_config) - mirrors the CLI's main()."""
    config = get_sell_puts_config(tickers)
    put_spreads_config = load_config(str(CONFIG_DIR / 'config_put_spreads.yaml'))
    config.update(put_spreads_config)

    return config, put_spreads_config
