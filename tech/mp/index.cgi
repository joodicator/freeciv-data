#!/usr/bin/env python3

from collections import namedtuple
import re
import cgi
import cgitb

cgitb.enable()

def parse_fc_config(lines):
    result = {}
    section = None
    for line in lines:
        line = line.rstrip('\n')
        if re.match(r';|\s*$', line):
            continue

        match = re.match(r'\[(?P<section>.*)\]$', line)
        if match:
            section = match.group('section')
            continue

        match = re.match(r'(?P<name>\S+)\s*=\s*(?P<value>.*)', line)
        if match and section is not None:
            if section not in result: result[section] = {}
            name, value = match.group('name', 'value')
            while value.endswith('\\'):
                value = value[:-1] + next(lines).rstrip('\n')
            if value.startswith('_(') and value.endswith(')'):
                value = value[2:-1]
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            if value.startswith('?tech:'):
                value = value[6:]
            result[section][name] = value
            continue

        raise ValueError(line)

    return result

with open('techs.ruleset') as file:
    config = parse_fc_config(file)

Tech = namedtuple('Tech', ('name', 'reqs'))
techs = {}
for key, value in config.items():
    if not key.startswith('advance_'): continue
    if value.get('root_req'): continue
    techs[value['name']] = Tech(
        name = value['name'],
        reqs = tuple(value[k] for k in ('req1', 'req2')
                     if k in value and value[k] != 'None'))

def all_reqs(tech, seen=None):
    if seen is None: seen = set()
    seen.add(tech)
    for req in techs[tech].reqs:
        if req in seen: continue
        yield req
        yield from all_reqs(req, seen)

try:
    sciencebox = int(cgi.FieldStorage().getfirst('sciencebox', ''))
except ValueError:
    sciencebox = 100

print('Content-Type: text/html')
print('')
print('<!DOCTYPE html>')
print('<html>')
print('  <head>')
print('    <meta charset="utf8">')
print('    <title>Freeciv (multiplayer) Technology Costs</title>')
print('    <link rel="stylesheet" href="index.css">')
print('  </head>')
print('  <body>')
print('    <a href="https://github.com/joodicator/freeciv-data/tree/master/tech/mp"')
print('       class="github" title="View source code on GitHub">')
print('        <img src="icons/github.png" width="32" height="32" />')
print('    </a>')
print('    <form action="." method="GET">')
print('      <tt>sciencebox</tt>')
print('      <input name="sciencebox" type="text" size="3" autocomplete="off" value="%d">' % sciencebox)
print('      <input type="submit" value="Update">')
print('    </form>')
print('    <table>')
print('      <thead>')
print('        <tr>')
print('          <th>Technology</th>')
print('          <th>Prerequisites</th>')
print('          <th>Cost (Bulbs)</th>')
print('        </tr>')
print('      </thead>')
print('      <tbody>')
for tech in sorted(techs.values(), key=lambda t: t.name):
    total_reqs = sum(1 for _ in all_reqs(tech.name))
    bulb_cost = max(1, int(sciencebox * (total_reqs + 2.0)**1.5 / 10.0))
    print('        <tr>')
    print('          <td>%s</td>' % tech.name)
    print('          <td>%s</td>' % total_reqs)
    print('          <td>%s</td>' % bulb_cost)
    print('        </tr>')
print('      </tbody>')
print('    </table>')
print('  </body>')
print('</html>')
