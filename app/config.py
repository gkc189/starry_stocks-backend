from pathlib import Path

from starry_stocks_common.config_loader import load_config, save_config
from starry_stocks_common.engine import resolve_sell_puts_max_dte

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


def get_dte_buckets() -> list[list[int]]:
    config = load_config(str(CONFIG_DIR / 'config_sell_puts.yaml'))
    return config.get('dte', {}).get('buckets', [])


def set_dte_buckets(buckets: list[list[int]]) -> list[list[int]]:
    config_path = str(CONFIG_DIR / 'config_sell_puts.yaml')
    config = load_config(config_path)
    dte_config = config.setdefault('dte', {})
    dte_config['buckets'] = buckets
    # max_dte is derived from the buckets at scan time (see resolve_sell_puts_max_dte);
    # kept in sync here purely so the persisted file doesn't show a stale value.
    dte_config['max_dte'] = resolve_sell_puts_max_dte(buckets)
    save_config(config, config_path)
    return buckets


DEFAULT_PUT_CREDIT_SPREAD_MAX_DTE = 60


def get_put_credit_spread_max_dte() -> int:
    config = load_config(str(CONFIG_DIR / 'config_put_spreads.yaml'))
    return config.get('max_dte', DEFAULT_PUT_CREDIT_SPREAD_MAX_DTE)


def set_put_credit_spread_max_dte(max_dte: int) -> int:
    config_path = str(CONFIG_DIR / 'config_put_spreads.yaml')
    config = load_config(config_path)
    config['max_dte'] = max_dte
    save_config(config, config_path)
    return max_dte


def get_sell_puts_config() -> dict:
    config = load_config(str(CONFIG_DIR / 'config.yaml'))
    config.update(load_config(str(CONFIG_DIR / 'config_sell_puts.yaml')))
    return config


def get_put_credit_spread_configs() -> tuple[dict, dict]:
    """Returns (merged_config, put_spreads_config) - mirrors the CLI's main()."""
    config = get_sell_puts_config()
    put_spreads_config = load_config(str(CONFIG_DIR / 'config_put_spreads.yaml'))
    config.update(put_spreads_config)

    return config, put_spreads_config
