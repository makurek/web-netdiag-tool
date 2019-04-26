import os
import re
import ipaddress
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

# Ping a list of neighbors
# This method should return a following dictionary
# { 'neighbor_ip_1' : True,
#   'neighbor_ip_2' : False }
# Typically we will ping only one neighbor

def pingNeighbor(nr1, router, ips):
   result = {}
   for ip in ips:
      cmd = "ping " + str(ip + 1) 
      nr_result = nr1.run(name = "Ping IPv4 neighbor", task=netmiko_send_command, command_string=cmd)
      output = str(nr_result[router][0]).split("\n")[4]
      print(output)
      if "!" in output:
         result[str(ip + 1)] = "True"
      else:
         result[str(ip + 1)] = "False"
   print(result) 
   return result
   

# This method should return a dictionary with results
# { 'ip_address': "1.2.3.4/24",
#   'if_status': "up",
#
#

def initDiag(router, interface):
  
  # Filter to run commands on single router only
  nr1 = nr.filter(hostname=router)
  
  # Get basic facts
  # TODO: error handling
  basic_facts = nr1.run(name="Get interfaces", task=napalm_get, getters=["interfaces", "interfaces_ip"])
  phy_iface = basic_facts[router][0].result['interfaces'][interface]
  # TODO: this is bad approach, because interface might be nonexistent
  ip_iface = basic_facts[router][0].result['interfaces_ip'][interface]
  ips = []
  # Iterate through IPv4 addresses
  for k, v in ip_iface['ipv4'].items():
     ips.append(ipaddress.ip_address(k))
  d = {}
  d['phy_iface'] = phy_iface
  d['ip_iface'] = ip_iface
  d['ping_neighbor'] = pingNeighbor(nr1, router, ips)
  return d


@app.route("/", methods=["GET", "POST"])

def index():
    form = initForm()
    if form.validate_on_submit():
        
	# Get all params 
        router = request.form.get("router")
        interface = request.form.get("interface")
        
	# Initiate checks using data passed to web form
        result = initDiag(router, interface)
        return render_template("home.html", form=form, result=result)
    else:
        return render_template("home.html", form=form)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
