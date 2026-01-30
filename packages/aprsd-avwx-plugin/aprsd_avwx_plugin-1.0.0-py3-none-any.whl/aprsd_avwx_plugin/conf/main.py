from oslo_config import cfg

avwx_group = cfg.OptGroup(
    name="avwx_plugin",
    title="Options for the AVWXWeatherPlugin",
)

avwx_opts = [
    cfg.StrOpt(
        "apiKey",
        help="avwx-api is an opensource project that has"
        "a hosted service here: https://avwx.rest/"
        "You can launch your own avwx-api in a container"
        "by cloning the githug repo here:"
        "https://github.com/avwx-rest/AVWX-API",
    ),
    cfg.StrOpt(
        "base_url",
        default="https://avwx.rest",
        help="The base url for the avwx API.  If you are hosting your own"
        "Here is where you change the url to point to yours.",
    ),
]

ALL_OPTS = avwx_opts


def register_opts(config):
    config.register_group(avwx_group)
    config.register_opts(avwx_opts, group=avwx_group)


def list_opts():
    return {
        avwx_group.name: avwx_opts,
    }
