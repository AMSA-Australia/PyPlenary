#   Copyright © 2021  Lee Yingtong Li (RunasSudo)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import flask
import toml

app = flask.Flask(__name__, template_folder='jinja2')

# Load config

with open('config.toml', 'r') as f:
	config = toml.load(f)

# Views

@app.route('/')
def index():
	return flask.render_template('index.html', active_tab='index')

@app.route('/speaker-list')
def speaker_list():
	return flask.render_template('speaker_list.html', active_tab='speaker_list')

# Jinja2 context

@app.context_processor
def inject_jinja2_context():
	return {'config': config}
