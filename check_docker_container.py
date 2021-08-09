#!python

"""Check if docker container is running"""

import argparse
import subprocess
import re

import nagiosplugin

class ContainerState:
    def __init__(self, state: str, exit_code: int,  time: str, is_paused: bool):
        self.state = state
        self.exit_code = None
        self.time = time
        self.is_paused = is_paused

class Container(nagiosplugin.Resource):

    def __init__(self, cnt_name: str):
        self.cnt_name = cnt_name


    def probe(self):
        #TODO add LANG=en_US ?
        result = subprocess.run([
            "docker",
            "ps",
            "-a",
            '--format',
            r'{{.Names}};{{.Status}}',
            "-f"
            "name=%s" % self.cnt_name
        ], encoding="UTF-8", capture_output=True)

        if result.returncode != 0:
            raise Exception(str(result.stderr))

        if not result.stdout:
            raise Exception(f"No containers returned by 'docker ps' command")

        cs = self.parse(result.stdout)
        
        return [nagiosplugin.Metric('state', cs, context='container')]

    status_re = re.compile(r"(.+);([a-zA-Z]+) (.*)( \(Paused\))?")

    def parse(self, data):
        for ln in data.splitlines():
            match = Container.status_re.match(data)
            if not match:
                raise Exception(f"Cannot parse docker output: {data}")

            parts = match.groups()
            if parts[0] == self.cnt_name:
                return ContainerState(
                    state = parts[1],
                    uptime = parts[2],
                    is_paused = parts[3] is not None
                )
        raise Exception(f"Container {self.cnt_name} not found")


class ContainerContext(nagiosplugin.Context):

    def __init__(self):
        super().__init__(name="container")


    def evaluate(self, metric, resource):
        val = metric.value
        if val.state == "Up":
            if not val.is_paused:
                return nagiosplugin.state.Ok
            else:
                return nagiosplugin.state.Warn
        return nagiosplugin.state.Critical

class ContainerSummary(nagiosplugin.Summary):

    def ok(self, results):
        return '%s %s' % (
            results[0].metric.value.state,
            results[0].metric.value.uptime,
        )

    def problem(self, results):
        val = results[0].metric.value
        return '%s %s' % (
            val.state,
            val.uptime
        )


@nagiosplugin.guarded
def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-n', '--name', metavar='NAME', required=True,
        help='container name')

    args = argp.parse_args()

    check = nagiosplugin.Check(
        Container(args.name),
        ContainerContext(),
        ContainerSummary()
    )
    check.main()


if __name__ == '__main__':
    main()

