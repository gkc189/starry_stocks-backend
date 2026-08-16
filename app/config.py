import re
from pathlib import Path

from starry_stocks_common.config_loader import load_config, save_config
from starry_stocks_common.engine import DEFAULT_PUT_CREDIT_SPREAD_DTE_BUCKETS, resolve_max_dte

CONFIG_DIR = Path(__file__).parent / 'configs'
GENERAL_CONFIG_PATH = CONFIG_DIR / 'config.yaml'

STRATEGY_CONFIG_DIRS: dict[str, str] = {
    'sell-puts': 'sell-puts',
    'put-credit-spread': 'put-credit-spread',
}

DEFAULT_CONFIG_NAME = 'Default-Config'


def _strategy_dir(strategy_id: str) -> Path:
    path = CONFIG_DIR / STRATEGY_CONFIG_DIRS[strategy_id]
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify_config_name(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', name.strip().lower()).strip('-')


def _config_file_path(strategy_id: str, config_name: str) -> Path:
    return _strategy_dir(strategy_id) / f"{slugify_config_name(config_name)}.yaml"


def list_strategy_configs(strategy_id: str) -> list[str]:
    """Returns the display names of all configs for a strategy, sorted alphabetically."""
    names = []
    for path in _strategy_dir(strategy_id).glob('*.yaml'):
        config = load_config(str(path))
        names.append(config.get('name', path.stem))
    return sorted(names, key=str.lower)


def get_selected_config_name(strategy_id: str) -> str:
    """
    Returns the currently selected config name for a strategy, self-healing to
    an available config if the persisted selection no longer exists on disk.
    """
    general = load_config(str(GENERAL_CONFIG_PATH))
    selected = general.get('selected_configs', {}).get(strategy_id)
    available = list_strategy_configs(strategy_id)

    if selected in available:
        return selected
    return available[0] if available else DEFAULT_CONFIG_NAME


def set_selected_config_name(strategy_id: str, config_name: str) -> None:
    general = load_config(str(GENERAL_CONFIG_PATH))
    general.setdefault('selected_configs', {})[strategy_id] = config_name
    save_config(general, str(GENERAL_CONFIG_PATH))


def _selected_config_path(strategy_id: str) -> Path:
    return _config_file_path(strategy_id, get_selected_config_name(strategy_id))


def create_strategy_config(strategy_id: str, name: str) -> str:
    """
    Creates a new config for a strategy by cloning the currently selected
    config's contents (so every field the UI depends on stays populated),
    selects it, and returns its display name.
    """
    slug = slugify_config_name(name)
    if not slug:
        raise ValueError('Config name must contain at least one letter or number.')

    new_path = _strategy_dir(strategy_id) / f"{slug}.yaml"
    if new_path.exists():
        raise ValueError(f"A config named '{name}' already exists.")

    source_path = _selected_config_path(strategy_id)
    config = load_config(str(source_path)) if source_path.exists() else {}
    config['name'] = name
    save_config(config, str(new_path))

    set_selected_config_name(strategy_id, name)
    return name


def delete_strategy_config(strategy_id: str, name: str) -> str:
    """
    Deletes a config for a strategy. If it was the selected one, falls back to
    another remaining config (preferring Default-Config) and persists that.
    Returns the (possibly changed) selected config name.
    """
    available = list_strategy_configs(strategy_id)
    if name not in available:
        raise ValueError(f"No config named '{name}' for strategy: {strategy_id}")
    if len(available) <= 1:
        raise ValueError('Cannot delete the only remaining config for this strategy.')

    was_selected = get_selected_config_name(strategy_id) == name

    _config_file_path(strategy_id, name).unlink(missing_ok=True)

    if was_selected:
        remaining = [n for n in available if n != name]
        fallback = DEFAULT_CONFIG_NAME if DEFAULT_CONFIG_NAME in remaining else remaining[0]
        set_selected_config_name(strategy_id, fallback)
        return fallback

    return get_selected_config_name(strategy_id)


def get_strategy_universe(strategy_id: str) -> list[str]:
    """
    Returns the search-set for a strategy's currently selected config, falling
    back to the shared default in the general config if unset.
    """
    base_config = load_config(str(GENERAL_CONFIG_PATH))
    strategy_config = load_config(str(_selected_config_path(strategy_id)))
    return strategy_config.get('search_set', base_config.get('search_set', []))


def set_strategy_universe(strategy_id: str, tickers: list[str]) -> list[str]:
    """Persists `tickers` as the search_set in the strategy's currently selected config."""
    config_path = str(_selected_config_path(strategy_id))
    config = load_config(config_path)
    config['search_set'] = tickers
    save_config(config, config_path)
    return tickers


# sell-puts configs are always seeded with real buckets already, so an empty
# fallback there is inert; put-credit-spread configs may not have any yet, so
# fall back to the window it's always implicitly used (0-60 DTE).
DEFAULT_DTE_BUCKETS: dict[str, list[list[int]]] = {
    'sell-puts': [],
    'put-credit-spread': DEFAULT_PUT_CREDIT_SPREAD_DTE_BUCKETS,
}


def get_dte_buckets(strategy_id: str) -> list[list[int]]:
    config = load_config(str(_selected_config_path(strategy_id)))
    return config.get('dte', {}).get('buckets') or DEFAULT_DTE_BUCKETS.get(strategy_id, [])


def set_dte_buckets(strategy_id: str, buckets: list[list[int]]) -> list[list[int]]:
    config_path = str(_selected_config_path(strategy_id))
    config = load_config(config_path)
    dte_config = config.setdefault('dte', {})
    dte_config['buckets'] = buckets
    # max_dte is derived from the buckets at scan time (see resolve_max_dte);
    # kept in sync here purely so the persisted file doesn't show a stale value.
    dte_config['max_dte'] = resolve_max_dte(buckets)
    save_config(config, config_path)
    return buckets


# The "delta" hard filter is named differently per strategy (a plain delta band
# for sell-puts vs. the short leg's delta band for a credit spread), so the API
# exposes it uniformly as `delta_range` and this maps that back to the YAML key.
FILTER_DELTA_RANGE_KEYS: dict[str, str] = {
    'sell-puts': 'delta',
    'put-credit-spread': 'delta-short-leg',
}

DEFAULT_DELTA_RANGE = {'min': 0.0, 'max': 1.0}
DEFAULT_USE_SCORING = True
DEFAULT_RISK_REWARD_MIN = 0.01


def get_strategy_filters(strategy_id: str) -> dict:
    """Returns the strategy's currently selected config's hard filters, defaults filled in."""
    config = load_config(str(_selected_config_path(strategy_id)))
    filters = config.get('filters', {})
    range_key = FILTER_DELTA_RANGE_KEYS[strategy_id]

    return {
        'use_scoring': filters.get('use-scoring', DEFAULT_USE_SCORING),
        'delta_range': {**DEFAULT_DELTA_RANGE, **filters.get(range_key, {})},
        'risk_reward_min': filters.get('risk-reward', DEFAULT_RISK_REWARD_MIN),
    }


def set_strategy_filters(strategy_id: str, use_scoring: bool, delta_range: dict, risk_reward_min: float) -> dict:
    config_path = str(_selected_config_path(strategy_id))
    config = load_config(config_path)
    range_key = FILTER_DELTA_RANGE_KEYS[strategy_id]

    config['filters'] = {
        'use-scoring': use_scoring,
        range_key: {'min': delta_range['min'], 'max': delta_range['max']},
        'risk-reward': risk_reward_min,
    }
    save_config(config, config_path)
    return get_strategy_filters(strategy_id)


def get_sell_puts_config() -> dict:
    config = load_config(str(GENERAL_CONFIG_PATH))
    config.update(load_config(str(_selected_config_path('sell-puts'))))
    return config


def get_put_credit_spread_configs() -> tuple[dict, dict]:
    """Returns (merged_config, put_spreads_config) - mirrors the CLI's main()."""
    config = get_sell_puts_config()
    put_spreads_config = load_config(str(_selected_config_path('put-credit-spread')))
    config.update(put_spreads_config)

    return config, put_spreads_config
