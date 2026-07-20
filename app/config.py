from pathlib import Path
from typing import Optional

from starry_stocks_common.config_loader import load_config, save_config

CONFIG_DIR = Path(__file__).parent / 'configs'


STRATEGY_CONFIG_FILENAMES: dict[str, str] = {
    'sell-puts': 'config_sell_puts.yaml',
    'put-credit-spread': 'config_put_spreads.yaml',
}


def get_strategy_universe(strategy_id: str) -> list[str]:
    """
    Returns the search-set for a strategy: its own config file's search_set if
    present, else the shared default from config.yaml.
    """
    filename = STRATEGY_CONFIG_FILENAMES[strategy_id]
    base_config = load_config(str(CONFIG_DIR / 'config.yaml'))
    strategy_config = load_config(str(CONFIG_DIR / filename))
    return strategy_config.get('search_set', base_config.get('search_set', []))


def set_strategy_universe(strategy_id: str, tickers: list[str]) -> list[str]:
    """Persists `tickers` as the search_set in the strategy's own config file."""
    config_path = str(CONFIG_DIR / STRATEGY_CONFIG_FILENAMES[strategy_id])
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
