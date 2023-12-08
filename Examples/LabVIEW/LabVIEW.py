import labview_wrapper as wrap

wrap.init("192.168.2.94")

wrap.transformMethodsToFunctions()

wrap.setPotential(1)
wrap.setCurrent(10e-9)
wrap.setPotentiostatMode(1)  # 1 = pot; 2 = gal
wrap.enablePotentiostat()
print(f"Current: {wrap.getCurrent()}")
print(f"Voltage: {wrap.getVoltage()}")
wrap.disablePotentiostat()

wrap.disconnect()
