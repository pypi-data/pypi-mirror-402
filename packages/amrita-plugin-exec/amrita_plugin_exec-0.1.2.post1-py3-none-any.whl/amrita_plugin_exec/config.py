from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    enable_docker: bool = False
    image_name: str = "alpine:latest"
    docker_host: str = "unix://var/run/docker.sock"
    shell_name: str = "sh"
    auto_rebuild_container: bool = True


CONFIG = get_plugin_config(Config)
