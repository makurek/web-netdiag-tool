import os
import re
from flask import Flask
from flask_wtf import FlaskForm
from flask import render_template
from flask import request
from flask_bootstrap import Bootstrap
from wtforms import StringField
from wtforms.validators import InputRequired
from nornir import InitNornir
from nornir.plugins.tasks.networking import napalm_get
from nornir.plugins.tasks.networking import napalm_cli
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command
'''
Perform basic diag checks
Input params:
{ router, switch, router-interface, vlan, switch-interface, bgp, bfd }

 confirm router IP addressing
 interface operational status
 ping neighbor
 if not ping
    proceed with sw diag   
 else
 if bgp
    check bgp session status
    if estab
      get received prefixes


'''

nr = InitNornir(config_file="config.yaml")

# This is temporary form to pass parameters
# In future, they will be passed from external source of truth

class initForm(FlaskForm):

    router = StringField('Router', validators=[InputRequired()])
    interface = StringField('Inteface', validators=[InputRequired()])


app = Flask(__name__)
app.config['SECRET_KEY'] = '443436456542'
Bootstrap(app)

@app.route("/", methods=["GET", "POST"])

def index():
    form = initForm()
    if form.validate_on_submit():
        router = request.form.get("router")
        interface = request.form.get("interface")
        nr1 = nr.filter(hostname=router)
        cmd = "show interface " + interface
        res = nr1.run(name="Run CLI command", task=netmiko_send_command, command_string=cmd)
        res1 = res[router][0]
        return render_template("home.html", form=form, result=res1)
    else:
        return render_template("home.html", form=form)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
