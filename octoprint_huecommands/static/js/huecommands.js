/*
 * View model for OctoPrint-OctoHue
 *
 * Author: LMS0815
 * License: AGPLv3
 *
 * http://beautifytools.com/javascript-validator.php
 *
 * https://community.octoprint.org/t/german-python-script-mit-button-ausfuhren/11161/3
 * https://github.com/foosel/OctoPrint/blob/master/docs/plugins/viewmodels.rst
 */
$(function() {
	function hueCommandsViewModel(parameters) {
		var self = this;
		var MSG_TITLE = 'hue Commands';

		self.allSettings = parameters[0];
		self.loginState = parameters[1];

		self.presets = ko.observableArray([]);
		self.bridgeaddr = ko.observable('');
		self.username = ko.observable('');
		self.userdevice = ko.observable('');

		self.cli = ko.observable('');
		self.connected = ko.observable(false);
		self.error = ko.observable('');
		self.hue_lights = ko.observableArray([]);
		self.hue_groups = ko.observableArray([]);
		self.hue_bridges = ko.observableArray([]);


		self.onAllBound = function() {
			self.getInfo();
		};


		self.onAfterBinding = function() {
			/* self.confirmation = $("#confirmation"); */
		};


		self.onBeforeBinding = function() {
			self.presets(self.allSettings.settings.plugins.huecommands.presets.slice(0));
			self.bridgeaddr = self.allSettings.settings.plugins.huecommands.bridgeaddr;
			self.username = self.allSettings.settings.plugins.huecommands.username;
		};


		self.onSettingsBeforeSave = function() {
			// http://www.knockmeout.net/2011/04/utility-functions-in-knockoutjs.html
			var temp = ko.observableArray();
			temp.justIDs = ko.computed(function() {var ids = ko.utils.arrayMap(self.presets(), function(item) {return item.id().toUpperCase();});return ids.sort();}, temp);
			if ( temp.justIDs()[0] === '' ) {
				console.log('EMPTY KEY FOUND');
				new PNotify({
					'title': 'Settings not saved',
					'text': 'Empty preset key found',
					'type': 'error',
					'hide': true
					});
				return false;
			}
			temp.uniqueIDs = ko.dependentObservable(function() {return ko.utils.arrayGetDistinctValues(temp.justIDs()).sort();}, temp);
			if ( temp.justIDs().length !== temp.uniqueIDs().length ) {
				console.log('EMPTY KEY FOUND');
				new PNotify({
					'title': 'Settings not saved',
					'text': 'Duplicate preset key found',
					'type': 'error',
					'hide': true
					});
				return false;
			}
			self.allSettings.settings.plugins.huecommands.presets(self.presets.slice(0));
			self.allSettings.settings.plugins.huecommands.bridgeaddr(self.bridgeaddr());
			self.allSettings.settings.plugins.huecommands.username(self.username());
			self.getInfo({'username': self.username(), 'bridgeaddr': self.bridgeaddr()});
		};


		self.PresetMove = function(index, amount) {
			var definition = self.presets.splice(index, 1)[0];
			var newIndex = Math.max(index + amount, 0);
			self.presets.splice(newIndex, 0, definition);
		};


		self.PresetAdd = function(index) {
			self.presets.unshift({
				'id': ko.observable('OFF'),
				'isgroup': ko.observable(false),
				'resid': ko.observable(0),
				'color': ko.observable('#000000'),
				'kelvin': ko.observable(0),
				'bri': ko.observable(0),
				'trans': ko.observable(0)
			});
			self.PresetMove (0, index);
			self.allSettings.settings.plugins.huecommands.presets(self.presets.slice(0));
		};


		self.PresetRemove = function(definition) {
			self.presets.remove(definition);
		};


		self.visibleTest = function () {
			if ( !self.loginState.isUser() ) {return false; }
			//alert(self.presets().length);
			return true;
		};


		self.callAPI = function(command, data, async ) {
			// OctoPrint.plugins.huecommands.get()
			if (data === undefined) { data = '' ;}
			if (async === undefined) { async = false ;}
			var result = JSON.stringify({'responseText': {'state': 'API ERROR'}});
			$.ajax({
				'url':			API_BASEURL+'plugin/huecommands',
				'async': 		false, //async,
				'type':			'POST',
				'dataType':		'json',
				'contentType':	'application/json',
				'headers':		{'X-Api-Key': UI_API_KEY},
				'data':			JSON.stringify({'command': command, 'data': data}),
				'complete':		function(data) {result = data;},
				'success':		function(data) {result = data;},
				'error':		function(data) {result = data;}
			});
			// if (async) return {'state': ''};
			result =  JSON.parse(result.responseText || JSON.stringify({'state': 'NO RESPONSE'}));
			self.connected(result.state == 'OK' );
			self.error(result.error || '');
			//alert(JSON.stringify(result));
			return result;
		};


		self.callCLI = function(data) {
			var result = self.callAPI ('hue', data, true);
			if (self.error()) {
				new PNotify({
					'title': MSG_TITLE,
					'text': self.error() || 'unknown',
					'type': 'error',
					'hide': true
					});
				}
			return result;
		};


		self.ip2int = function(ip) {
			return ip.split(':')[0].split('.').reduce(function(ipInt, octet) { return (ipInt<<8) + parseInt(octet, 10);}, 0) >>> 0;
		};


		self.int2ip = function(ipInt) {
			return ( (ipInt>>>24) +'.' + (ipInt>>16 & 255) +'.' + (ipInt>>8 & 255) +'.' + (ipInt & 255) );
		};


		self.getInfo = function(command) {
			if (command === null) { command = '' ;}
			var result = self.callAPI ('info', command, false) || '{}';
			//alert(JSON.stringify(result, null, 4));
			if ( self.connected() ) {
				if (result.username) self.username(result.username);
				if (result.userdevice) self.userdevice(result.userdevice);
				//self.hue_lights(ko.mapping.fromJS(result.lights.sort(function(a,b){return parseInt(a.no) - parseInt(b.no);})));
				//self.hue_groups(ko.mapping.fromJS(result.groups.sort(function(a,b){return parseInt(a.no) - parseInt(b.no);})));
				self.hue_lights(result.lights.sort(function(a,b){return parseInt(a.no) - parseInt(b.no);}));
				self.hue_groups(result.groups.sort(function(a,b){return parseInt(a.no) - parseInt(b.no);}));
				/*
				alert(ko.toJSON(self.hue_lights, null, 4));
				alert(ko.toJSON(self.hue_groups, null, 4));
				*/
			}
			return result;
		};


		self.createUser = function() {
			var result = {};
			if ( !(self.bridgeaddr() || '').trim()) {
				result = self.callAPI ('discover',window.location.host);
				//alert(JSON.stringify(result, null, 4));
				//self.hue_bridges(ko.mapping.fromJS(result.bridges.sort(function(a,b){return self.ip2int(a.ip) - self.ip2int(b.ip);})));
				self.hue_bridges(result.bridges.sort(function(a,b){return self.ip2int(a.ip) - self.ip2int(b.ip);}));
				if (!self.hue_bridges().length) {
					new PNotify({
						'title': MSG_TITLE,
						'text': 'No bridge found, try again.',
						'type': 'notice', // ['notice','error','info','success','disabled']
						'hide': true
					});
				}
				//alert(ko.toJSON(self.hue_bridges, null, 4));
				return true;
			}

			if ((self.username() || '').trim()) {
				result = self.getInfo ({ 'bridgeaddr': self.bridgeaddr(), 'username': self.username()});
				if ( self.connected() ) {
					self.userdevice(result.userdevice);
					new PNotify({
						'title': MSG_TITLE,
						'text': 'Connected to hue bridge.',
						'type': 'success', // ['notice','error','info','success','disabled']
						'hide': true
						});
				} else {
					new PNotify({
						'title': MSG_TITLE,
						'text': 'Not connected.<br/><br/>' + (result.error || ''),
						'type': 'error', // ['notice','error','info','success','disabled']
						'hide': true
						});
				}
				return true;
			}

			if ( !(self.userdevice() || '').trim()) {
				self.userdevice('OctoPrint hue Commands#'+Math.floor( Math.random() * 0xEFFFFF + 0x100000).toString(16));
				new PNotify({
					'title': MSG_TITLE,
					'text': 'Go and press the button on the bridge.',
					'type': 'info',
					'hide': true
					});
				return true;
			}

			result = self.callAPI ('create', { 'bridgeaddr': self.bridgeaddr(), 'userdevice': self.userdevice()} , false) || '{}';
			if ( self.connected() ) {
				self.userdevice(result.userdevice);
				new PNotify({
					'title': MSG_TITLE,
					'text': 'Connected to hue bridge.',
					'type': 'success', // ['notice','error','info','success','disabled']
					'hide': true
					});
			} else {
				new PNotify({
					'title': MSG_TITLE,
					'text': 'Press the button on the bridge first.<br/><br/>' + (result.error || ''),
					'type': 'error', // ['notice','error','info','success','disabled']
					'hide': true
					});
			}
			return true;
		};

		// ------------------------------------------------------------------------------------------------------------------------
		// Settings handler
		self.onSettingsShown = function() {
			self.settingsBeenShown = true;
			$('#HGCReportBug').off('click').on('click',function(){
				$(this).find('i').toggleClass('skull-crossbones bug');
				url = 'https://github.com/LMS0815/OctoPrint-hueCommands/issues/new';
				var body = "[\n ENTER DESCRIPTION HERE- ALSO ADD SCREENSHOT IF POSSIBLE!\n Describe your problem?\n What is the problem?\n Can you recreate it?\n Did you try disabling plugins?\n Did you remeber to update the subject?\n]\n\n**Plugins installed:**\n";
				$(Object.entries(OctoPrint.coreui.viewmodels.settingsViewModel.settings.plugins)).each(function(x,item){
					body += '- ' + item[0] + "\n";
				})
				body += "\n\n**Software versions:**\n- "+$('#footer_version li').map(function(){return $(this).text()}).get().join("\n- ");
				window.open(url+'?body='+encodeURI(body),'UICBugReport');
				$(this).blur();
			});
		}

	}

	OCTOPRINT_VIEWMODELS.push([
		hueCommandsViewModel,
		["settingsViewModel","loginStateViewModel"],
		["#settings_plugin_huecommands","#sidebar_plugin_huecommands"]
	]);
});
