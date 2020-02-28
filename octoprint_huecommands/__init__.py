#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# https://pythonbuddy.com/
# https://www.tutorialspoint.com/online_python_formatter.htm
#


from __future__ import absolute_import

import octoprint.plugin
import time
import os
import sys
import re
import json
import socket

from flask_babel import gettext

import http.client
import io

from colorsys import rgb_to_hsv # https://docs.python.org/2/library/colorsys.html
from qhue import Bridge, QhueException # https://github.com/quentinsf/qhue


__author__ = 'LMS0815'
__license__ = 'AGPLv3'
__copyright__ = 'Copyright (C) 2019 LMS0815 - Released under terms of the ' + __license__ + ' License'
__description__ = gettext('Illuminate your print job and signal its status using a Philips Hue light. Enter a GCODE equivalent anywhere you want.')


#from ssdpy import SSDPClient # https://github.com/MoshiBin/ssdpy


class hueCommands(  octoprint.plugin.StartupPlugin,
                    octoprint.plugin.TemplatePlugin,
                    octoprint.plugin.SimpleApiPlugin, # WebIf command buttons
                    octoprint.plugin.AssetPlugin,
                    octoprint.plugin.SettingsPlugin):

    def __init__(self):
        self.username = ''
        self.bridgeaddr = ''
        self.presetdict = {}
        self.capabilities = {}
        self.hue_bridge = '' # Hue Bridge and Functions
        self.hue_state = ''


    def parseFloat(self, numstr):
        return float(re.sub('[^0-9.]', '', str(numstr)) or 0)


    def parseInt(self, numstr):
        return int(re.sub('[^0-9.]', '', str(numstr)) or 0)


    def RGBtoHSV(self, rstring):
        rstring = re.sub('[^0-9A-Fa-f]', '', str(rstring) + '000000')[:6]
        (h,s,v) = rgb_to_hsv( int(rstring[0:2], 16) / 255.0 , int(rstring[2:4], 16) / 255.0, int(rstring[4:6], 16) / 255.0)
        return ( int( h * 65534.0 + 0.5) ,int(s * 254.0 + 0.5),int(v * 254.0 + 0.5))


    def KelvinToMired (self, kelvin=0):
        kelvin = self.parseInt(kelvin)
        # Hue bulbs can have a Color temperature of between 2000K and 6550K corresponding to Mired 500-153. That's it. Have fun.
        if kelvin < 2000 or kelvin > 6550: mired = 0
        else: mired = min([int( 1000000.0 / float(kelvin) + 0.5), 0xFFFF])
        return mired


    def hue_cli(self, cmds):
        #self._logger.debug('hue cli: {}'.format(cmds))

        cli_result = {'state':'ERROR'}

        cmds = cmds.split(';')[0].upper().split()
        cmds.sort()

        capabilitie = ''
        ressource_id = 0
        state = {   'on': True,
                    'transitiontime': 0,
                    'bri': 254}

        for cmd_id in cmds:
            # https://developers.meethue.com/develop/get-started-2/
            # https://developers.meethue.com/develop/hue-api/
            #
            # Device
            if cmd_id[:1]== 'L': # Lights
                capabilitie = 'lights'
                ressource_id = self.parseInt(cmd_id[1:])
            elif cmd_id[:1]== 'G': # Grops
                capabilitie = 'groups'
                ressource_id = self.parseInt(cmd_id[1:])
            # Preset
            elif cmd_id[:1]== '$':
                definition = self.presetdict.get(cmd_id[1:], None)
                #self._logger.debug('${}: {}'.format(cmd_id[1:], json.dumps(definition)))
                if definition == None:
                    cli_result['error'] = 'undefined preset: {}'.format(cmd_id)
                else:
                    capabilitie = 'groups' if definition['isgroup'] else 'lights'
                    if definition['color'] == '#000000':
                        temp = self.KelvinToMired(self.parseInt(definition.get('kelvin', 0)))
                        if temp == 0 or definition['bri'] == 0:
                            state['on'] = False
                        else:
                            state['ct'] = temp
                            state['bri'] = definition['bri']
                    else:
                        (state['hue'], state['sat'], state['bri']) = self.RGBtoHSV (definition['color'])
                    if definition['resid'] > 0: ressource_id = definition['resid']
                    if definition['trans'] > 0: state['transitiontime'] = definition['trans']
            # Transitiontime
            elif cmd_id[:1]== 'T': state['transitiontime'] = min([self.parseInt(cmd_id[1:]), 0xFFFF])
            elif cmd_id[:1]== 'D': state['transitiontime'] = min([int(self.parseFloat(cmd_id[1:]) * 10 + 0.5), 0xFFFF])
            elif cmd_id[:1]== 'M':
                time=('0:0:0:0' + str(re.sub('[^0-9.\\:]', '', cmd_id[1:])) + '.0').split('.')[0].split(':')
                state['transitiontime'] = min([int(time[-3]) * 36000 + int(time[-2]) * 600 + int(time[-1]) * 10  + int((temp[1]+'0')[:1]), 0xFFFF])
            # Color
            elif cmd_id[:1]== '#': (state['hue'], state['sat'], state['bri']) = self.RGBtoHSV (cmd_id[1:])
            elif cmd_id[:1]== 'C': state['ct'] = min([self.parseInt(cmd_id[1:]), 0xFFFF])
            elif cmd_id[:1]== 'K':
                temp = self.KelvinToMired(cmd_id[1:])
                if temp > 0: state['ct'] = temp
            # Brightness
            elif cmd_id[:1]== 'B': state['bri'] = min([self.parseInt(self.parseInt(cmd_id[1:])), 0xFE])
            elif cmd_id[:1]== '%': state['bri'] = min([int(self.parseFloat(cmd_id[1:]) * 2.54 + 0.5), 0xFE])
            # Saturation
            elif cmd_id[:1]== 'S': state['sat'] = min([self.parseInt(cmd_id[1:]), 0xFE])
            elif cmd_id[:1]== 'V': state['sat'] = min([int(self.parseFloat(cmd_id[1:]) * 2.54 + 0.5), 0xFE])
            # Hue:
            elif cmd_id[:1]== 'H': state['transitiontime'] = min([self.parseInt(cmd_id[1:]), 0xFFFF])
            elif cmd_id[:1]== 'U': state['transitiontime'] = min([int(self.parseFloat(cmd_id[1:]) * 655.35 + 0.5), 0xFFFF])
            # State
            elif cmd_id== 'ON':  state['on'] = True
            elif cmd_id== 'OFF': state['on'] = False
            else: cli_result['error'] = 'UNKNOWN COMMAND: {}'.format(cmd_id)

        if not state['on'] or state['bri'] == 0:
            state['on'] = False
            del state['bri']

        #ressource_id = str(ressource_id)
        if self.capabilities.get(capabilitie , None ) == None:
            cli_result['state'] = 'OK'
            cli_result['error'] = 'Device (group or light) missing'
        elif self.capabilities[capabilitie].get(ressource_id, None) == None:
            cli_result['state'] = 'OK'
            cli_result['error'] = 'Device missing: {}[{}]'.format(capabilitie, ressource_id)
        else:
            if capabilitie == 'lights': action = 'state'
            else: action = 'action'
            #self._logger.debug('cli: {}'.format(state))
            try:
                result = self.hue_bridge(capabilitie, ressource_id, action, **state)
                cli_result['state'] = 'OK'
                cli_result['success'] = result
            except QhueException as err:
                cli_result['error'] = '{}'.format(err)
            except:
                 cli_result['error'] = '{}'.format(sys.exc_info()[0])
        return cli_result



    def discover_hue(self, ip=''):
        class SSDPResponse(object):
            class _FakeSocket(io.BytesIO):
                def makefile(self, *args, **kw):
                    return self
            def __init__(self, response):
                r = http.client.HTTPResponse(self._FakeSocket(response))
                r.begin()
                #self.location = r.getheader('location')
                #self.usn = r.getheader('usn')
                #self.st = r.getheader('st')
                #self.bridgeid = r.getheader('hue-bridgeid')
                self.headers = r.getheaders()
                #self.cache = r.getheader('cache-control').split('=')[1]
            def __repr__(self):
                return '{headers}'.format(**self.__dict__)[1:-1]
                #return '{headers},\n{location},\n{st},\n{usn},\n{bridgeid}'.format(**self.__dict__)

        bridges = {}
        discover_result = {'state': 'DOSCOVERY'}
        group = ("239.255.255.250", 1900)
        message = '\r\n'.join([
            'M-SEARCH * HTTP/1.1',
            'HOST: {0}:{1}',
            'MAN: "ssdp:discover"',
            'ST: {st}','MX: {mx}','',''])
        mx = 2.5
        socket.setdefaulttimeout(mx+0.5)
        service = 'hue-bridgeid:all' # 'ssdp:all'

        if ip and not ip.startswith("127."):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((ip.split(':')[0], 80))
            ips = [s.getsockname()[0]]
        else:
            ips = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]

        #self._logger.debug('Discovery IPs: {}'.format(ips))
        for ip in ips:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.bind((ip,0))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            message_bytes = message.format(*group, st=service, mx=mx).encode('utf-8')
            sock.sendto(message_bytes, group)
            while True:
                try:
                    response = str(SSDPResponse(sock.recv(1024)))
                    if 'hue-bridgeid' in response: bridges[re.search(r"hue-bridgeid', '(.*?)'", response).group(1)] = re.search(r'http://(.*?)/', response).group(1)
                except socket.timeout:
                    break

        discover_result['bridges'] = []
        if bridges:
            for bridge_id in bridges.keys():
                discover_result['bridges'].append({'name': '{} - {}'.format(bridges[bridge_id], bridge_id), 'ip': bridges[bridge_id][:-3] if bridges[bridge_id][-3:] == ':80' else bridges[bridge_id]})
            #self._logger.info('Discover result: {}'.format(json.dumps(discover_result,indent=4)))
        else:
            discover_result['error'] = 'no bridge discovered'
        return discover_result


    def get_api_commands(self):
        return dict(hue=['data'], info=['data'], create=['data'], discover=['data'])


    def on_api_command(self, command, data):
        api_result = {'state':'ERROR'}
        command = command.lower()
        # self._logger.info('API call{}'.format(command))

        if command == 'hue':
            data = '{data}'.format(**data)
            api_result = self.hue_cli (data)

        elif command == 'info':
            data = data.get('data') or {}
            if data.get('bridgeaddr','') > '' and data.get('username','') > '': api_result = self.reload_hue(data['bridgeaddr'], data['username'])
            elif data.get('bridgeaddr', '') > '': api_result = self.reload_hue(data['bridgeaddr'], self.username)
            elif data.get('username', '') > '': api_result = self.reload_hue(self.bridgeaddr, data['username'])
            else: api_result = self.reload_hue(self.bridgeaddr, self.username)

        elif command == 'discover':
            api_result = self.discover_hue("{data}".format(**data))

        elif command == 'create':
            data = data.get('data', '') or {}
            if data.get('bridgeaddr','') > '':
                try:
                    hue_bridge = Bridge(data['bridgeaddr'],'')
                    userdevice=data.get('userdevice','') or '{}-{}'.format( __plugin_name__.replace(' ','#'), uuid1().bytes)
                    result = hue_bridge( 'api', devicetype=userdevice, http_method='post').get('success',{})
                    username = result.get('username', '')
                    if (username): api_result = self.reload_hue(data['bridgeaddr'], username)
                    else: api_result['error'] = result
                except QhueException as err:
                    api_result['error'] = '{}'.format(err)
                except:
                    reload_result['error'] = '{}'.format(sys.exc_info()[0])
            else:
                api_result['error'] = 'no address provided'
        else:
            api_result['error'] = 'UNKNOWN COMMAND: {}'.format(command)

        if api_result.get('error', '') != '': self._logger.error('API call {}: {}'.format(command, json.dumps(api_result)))
            #self._logger.debug('API {}: {}'.format(command, json.dumps(api_result,indent=0)))
        #else: self._logger.info('API {}: {}'.format(command, json.dumps(api_result,indent=4))
        return json.dumps(api_result)


    def hook_gcode_queuing(
            self,
            comm_instance,
            phase,
            cmd,
            cmd_type,
            gcode,
            *args,
            **kwargs
        ):
        if not gcode and cmd.split(' ')[0].upper() == 'HUE':
            self.hue_cli (cmd[4:])
            return (None, )


    def reload_hue(self, bridgeaddr, username):
        reload_result = {'state':'OFFLINE'}
        if bridgeaddr > '' and username > '':
            self.hue_bridge = Bridge(bridgeaddr, username)
            self.capabilities = {}
            userdevice = ''
            try:
                config = self.hue_bridge.config()
                userdevice = (config['whitelist'].get(username,{}) or {})['name']
                reload_result['userdevice'] = userdevice
                reload_result['username'] = username
                reload_result['state'] = 'OK'

                for capabilitie in ['lights', 'groups']:
                    reload_result[capabilitie] = [{'no': 0, 'name': '0: not defined '}]
                    self.capabilities[capabilitie] = {}
                    for temp in self.hue_bridge[capabilitie]():
                        capabilitie_number = self.parseInt(temp.split(':')[-1])
                        config = self.hue_bridge[capabilitie][capabilitie_number]()
                        reload_result[capabilitie].append({'no': capabilitie_number, 'name': u'{}: {} - {}'.format( capabilitie_number,  config['name'], config['type'])})
                        #reload_result[capabilitie].append({'id': capabilitie_number, 'name': '{:03d} {} - {}'.format( capabilitie_number,  config['name'], config['type'])})
                        #self.capabilities[capabilitie][capabilitie_number] = {'type': config['type'], 'name': config['name']}
                        self.capabilities[capabilitie][capabilitie_number] = {'name': config['name']}


            except QhueException as err:
                reload_result['error'] = '{}'.format(err)
            except:
                reload_result['error'] = '{}'.format(sys.exc_info()[0])
        return reload_result

    def reload_presetdict(self):
        self.username = self._settings.get(['username'])
        self.bridgeaddr = self._settings.get(['bridgeaddr'])
        presetdict_temp = self._settings.get(['presets'])
        self.presetdict = {}
        for definition in presetdict_temp:
            presetid = definition.get('id','OFF').upper()
            self.presetdict[presetid] = {   'isgroup': bool(definition.get('isgroup') or  False),
                                            'resid': min([self.parseInt(definition.get('resid')), 0xFF]),
                                            'color':  str(definition.get('color', '#000000').strip().upper()),
                                            'kelvin': min([self.parseInt(definition.get('kelvin')), 0xFFFF]),
                                            'bri': min([int(self.parseFloat(definition.get('bri')) * 2.54 + 0.5), 0xFE]),
                                            'trans': min([int(self.parseFloat(definition.get('trans')) * 10), 0xFFFF])
                                        }
        self.reload_hue(self.bridgeaddr, self.username)


    def get_settings_defaults(self):
        return dict(username = '', bridgeaddr = '127.0.0.1', presets = [{   'id': 'OFF',
                                                                             'isgroup': False,
                                                                             'resid': 0,
                                                                             'color':  '#000000',
                                                                             'kelvin': 0,
                                                                             'bri': 0,
                                                                             'trans':0
                                                                         }], capabilities = {})


    def get_settings_restricted_paths(self):
        return dict(admin=[["bridgeaddr"],["husername"],["presets"]], user=[["presets"]])


    def on_settings_initialized(self):
        self.reload_presetdict()


    def on_settings_save(self, data):
        '''
        if data.get('presets'):
            for val in data['presets']: val['resid'] = int(val['resid'])
        '''
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.reload_presetdict()


    def get_template_configs(self):
        return [
            dict(   type = 'settings',
                    name = 'hue ' + gettext("Commands"),
                    custom_bindings = True)
        ]


    def get_assets(self):
        return {
            #'css': ['css/huecommands.css'],
            'js': ['js/huecommands.js']
        }


    def get_update_information(self):
        # version check: github repository
        # update method: pip w/ dependency links
        return dict(huecommands = dict(
            displayName = 'hue GCODE Commands',
            displayVersion = self._plugin_version,
            type = 'github_release',
            user = 'lms0815',
            repo = 'OctoPrint-hueCommands',
            current = self._plugin_version,
            pip = 'https://github.com/LMS0815/OctoPrint-hueCommands/archive/{target_version}.zip',))


__plugin_name__ = 'hue GCODE Commands'
__plugin_description__ = __description__
__plugin_author__ = __author__
__plugin_license__ = __license__
__plugin_pythoncompat__ = '>=2.7,<4' # Compatible with python 2 and 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = hueCommands()

    global __plugin_hooks__
    __plugin_hooks__ = {    'octoprint.comm.protocol.gcode.queuing': __plugin_implementation__.hook_gcode_queuing,
                            'octoprint.plugin.softwareupdate.check_config': __plugin_implementation__.get_update_information}
