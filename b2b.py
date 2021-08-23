"""
Project: B2B (set attributes)
Port - attribute location (slot...Hosts)
StreamBlock - 1 bidirectional
"""
num_of_sessions = 'const'

from StcPython import StcPython

stc = StcPython()

chassis_address = "10.190.0.65"
slot = 4
port_1 = 9
port_2 = 10

port_1_location = f"//{chassis_address}/{slot}/{port_1}"
port_2_location = f"//{chassis_address}/{slot}/{port_2}"

print(f"using {port_1_location}")
print(f"using {port_2_location}\n")

#  Set up the log file
stc.config('automationoptions', loglevel='info', logto='required_path')

#  Set up the project - root
print("Creating a project - root")
project = stc.create('project', name='B2B')

#  Get project attributes
print("Getting project attributes")
projectAtt = stc.get(project, 'name')
print(projectAtt)

# Set up ports
print(f"Creating ports under {project}")
port1 = stc.create('port', under=project)
port2 = stc.create('port', under=project)

print("Configuring ports locarion")
stc.config(port1, location=port_1_location)
stc.config(port2, location=port_2_location)

# Set up emulated devices
print(f"Creating {num_of_sessions} devices on each port")
port1_devices = stc.create('EmulatedDeviceGenParams', under=port1, count=num_of_sessions, BlockMode='ONE_DEVICE_PER_BLOCK')  # do i want this?
port2_devices = stc.create('EmulatedDeviceGenParams', under=port2, count=num_of_sessions, BlockMode='ONE_DEVICE_PER_BLOCK')  # do i want this?
ip_if_1 = stc.create('DeviceGenIpv4IfParams', under=port1_devices, PrefixLength=16, Addr="2.2.1.1", Gateway="2.2.1.0")
ip_if_2 = stc.create('DeviceGenIpv4IfParams', under=port2_devices, PrefixLength=16, Addr="3.3.1.1", Gateway="3.3.1.0")
stc.config(port1_devices, topLevelIf=ip_if_1)
stc.config(port2_devices, topLevelIf=ip_if_2)
stc.create('DeviceGenLinkedStep', under=ip_if_1, PropertyId='Addr', step="0.0.0.1", LinkToId="port")
stc.create('DeviceGenLinkedStep', under=ip_if_1, PropertyId='Addr', step="0.0.0.1", LinkToId="port")
eth_if_1 = stc.create('DeviceGenEthIIIfParams', under=port1_devices, SrcMac="00:20:94:00:00:01")
eth_if_2 = stc.create('DeviceGenEthIIIfParams', under=port2_devices, SrcMac="00:30:94:00:00:01")
stc.config(ip_if_1, StackedOn=eth_if_1)
stc.config(ip_if_2, StackedOn=eth_if_2)
stc.create("BgpDeviceGenProtocolParams", under=port1_devices, UseGatewayAsDutIpAddr=True, AsNum=100, DutAs=100)  # what r the last 2?
stc.create("BgpDeviceGenProtocolParams", under=port2_devices, UseGatewayAsDutIpAddr=True, AsNum=100, DutAs=100)  # what r the last 2?
stc.perform('DeviceGenConfigExpand', GenParams=port1_devices, DeleteExisting='NO')
stc.perform('DeviceGenConfigExpand', GenParams=port2_devices, DeleteExisting='NO')

# Set up stream blocks
print("Creating StreamBlock on port 1")
streamBlock_1 = stc.create('streamBlock', under=port1, frameLengthMethod='FIXED', FixedFrameLength='1440') # can go bidirectonal, how do i control rate?
generator_1 = stc.get(port1, 'children-generator')
analyzer_1 = stc.get(port2, 'children-analyzer')
print("Creating StreamBlock on port 2")
streamBlock_2 = stc.create('streamBlock', under=port2, frameLengthMethod='FIXED', FixedFrameLength='1440') # can go bidirectonal, how do i control rate?
generator_2 = stc.get(port2, 'children-generator')
analyzer_2 = stc.get(port1, 'children-analyzer')


print("Attaching ports...")
stc.perform('AttachPorts', portList=[port1, port2], autoConnect='TRUE')

print("Applying...")
stc.apply()

#  Call subscribes
print("Calling subscriber...")
port1GeneratorResult = stc.subscribe(Parent=project, 
                                    ResultParent=port1, 
                                    ConfigType='Generator', 
                                    resulttype='GeneratorPortResults', 
                                    filenameprefix=f"Generator_port1_counter_{port1}",
                                    Interval=2)
port2GeneratorResult = stc.subscribe(Parent=project, 
                                    ResultParent=port2, 
                                    ConfigType='Generator', 
                                    resulttype='GeneratorPortResults', 
                                    filenameprefix=f"Generator_port2_counter_{port2}",
                                    Interval=2)
port2AnalyzerResult = stc.subscribe(Parent=project, 
                                    ResultParent=port2, 
                                    ConfigType='Analyzer', 
                                    resulttype='AnalyzerPortResults', 
                                    filenameprefix=f"Analyzer_port2_counter_{port1}")
port1AnalyzerResult = stc.subscribe(Parent=project, 
                                    ResultParent=port1, 
                                    ConfigType='Analyzer', 
                                    resulttype='AnalyzerPortResults', 
                                    filenameprefix=f"Analyzer_port1_counter_{port2}")
                                    

#  Start traffic
stc.perform('AnalyzerStart', analyzerList=[analyzer_1, analyzer_2])
#  Wait for analyzer to start
stc.sleep(1)

print("Starting generator...")
stc.perform('GeneratorStart', generatorList=[generator_1, generator_2])
print("running traffic for 5 seconds")
stc.sleep()

#  Stop traffic
print("Stopping traffic")
stc.perform('GeneratorStop', generatorList=[generator_1, generator_2])
stc.perform('AnalyzerStop', analyzerList=[analyzer_1, analyzer_2])

#  Call unsubscribes
stc.unsubscribe(port2AnalyzerResult)
stc.unsubscribe(port1GeneratorResult)

#  Disconnect
print("Diconnecting...")
stc.disconnect(chassis_address)
stc.delete(project)
