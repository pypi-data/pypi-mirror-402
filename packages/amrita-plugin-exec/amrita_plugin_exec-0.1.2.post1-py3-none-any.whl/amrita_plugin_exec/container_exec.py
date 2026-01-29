import asyncio

import docker
from docker.errors import DockerException, ImageNotFound
from nonebot import logger

from .config import CONFIG


async def pull_image(image_name: str):
    try:
        client: docker.DockerClient = docker.DockerClient(base_url=CONFIG.docker_host)
        client.images.pull(image_name)
        return True
    except DockerException as e:
        logger.opt(exception=e, colors=True).exception(f"Failed to pull image: {e}")
        return False


async def execute_in_docker(*cmd_parts):
    image_name = "alpine:latest"
    try:
        client = docker.DockerClient(base_url=CONFIG.docker_host)
        # 将命令部分组合成完整的命令字符串
        cmd_text = " ".join(cmd_parts)
        container = client.containers.run(
            image_name,
            f"{CONFIG.shell_name} -c '{cmd_text}'",
            detach=True,
            remove=CONFIG.auto_rebuild_container,
            network_mode="none",
            mem_limit="128m",
            cpu_period=100000,
            cpu_quota=50000,
            pids_limit=100,
            read_only=True,
            security_opt=["no-new-privileges:true"],
        )

        try:
            result = await asyncio.to_thread(
                lambda: container.wait(timeout=10),
            )
            logs = container.logs().decode("utf-8")
            exit_code = result.get("StatusCode", 0)

            return logs, exit_code
        except DockerException as e:
            logger.opt(exception=e, colors=True).exception(
                f"Failed to get container logs: {e}"
            )

            return "", 1
        finally:
            if CONFIG.auto_rebuild_container:
                container.remove(force=True)
    except ImageNotFound:
        logger.warning(f"Image {image_name} not found. Pulling...")
        await pull_image(image_name)
        return await execute_in_docker(*cmd_parts)
    except DockerException as e:
        logger.error(f"Failed to run container: {e}")
        return f"Docker执行失败: {e}", 1
