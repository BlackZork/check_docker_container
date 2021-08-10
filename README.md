# check_docker_container
A simple nagios/icinga2 plugin for checking docker containter state.

Parses docker ps output for performance.

Issues CRITICAL if a container is not Up, WARINING if container is paused.

# Icinga2 Mini-HOWTO

1. Define check command:

command_docker_container.conf:
```
object CheckCommand "docker_container" {
  import "plugin-check-command"
  command = [ PluginDir + "/check_docker_container" ]

  arguments = {
    "--name" = {
      value = "$docker_container_name$"
      description = "Name of docker container to monitor"
    }
  }
}
```

2. Define service that accepts list of container names:

services.conf:
```
apply Service for (container_name in host.vars.docker_containers) {
  import "generic-service"
  check_command = "docker_container"

  vars.docker_container_name = container_name
}
```

3. Add list of containers that you want to monitor:

host.conf:
```
object Host "sds.infoklinika.pl" {
  /* Import the default host template defined in `templates.conf`. */
  import "linux-server"

  [...]

  vars.docker_containers = [
    "my-container1",
    "my-container2",
    "my-container3",
    "my-container4"
  ]
}
```