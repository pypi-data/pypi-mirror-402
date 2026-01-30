from oslo_config import cfg

plugin_group = cfg.OptGroup(
    name="aprsd_openweathermap_plugin",
    title="APRSD Slack Plugin settings",
)

plugin_opts = [
    cfg.BoolOpt(
        "enabled",
        default=False,
        help="Enable the plugin?",
    ),
    cfg.StrOpt(
        "apiKey",
        help="OpenWeatherMap api key. "
        "Some plugins use the OpenWeatherMap API fetch "
        "location and weather information. "
        "To use this plugin you need to get an openweathermap"
        "account and apikey."
        "https://home.openweathermap.org/api_keys",
    ),
]

ALL_OPTS = plugin_opts


def register_opts(cfg):
    cfg.register_group(plugin_group)
    cfg.register_opts(ALL_OPTS, group=plugin_group)


def list_opts():
    return {
        plugin_group.name: plugin_opts,
    }
