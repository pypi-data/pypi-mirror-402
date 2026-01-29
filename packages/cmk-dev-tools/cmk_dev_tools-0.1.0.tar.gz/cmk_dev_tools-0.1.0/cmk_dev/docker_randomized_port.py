#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["docker"]
# ///

import docker.client

client = docker.client.DockerClient()
cnt = client.containers.create(
    image="python",
    command="python3 -m http.server 80",
    name="python-http2",
    ports={"80/tcp": None},
)
try:
    cnt.start()  # run asynchonously in order to be able to read settings
    cnt.reload()  # needed to have `NetworkSettings` updated
    print(f"http://localhost:{cnt.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']}/")
    cnt.wait()
finally:
    cnt.stop()
    cnt.remove()
