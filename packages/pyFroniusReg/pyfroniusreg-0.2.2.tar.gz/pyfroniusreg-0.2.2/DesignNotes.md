# Purpose

I want to be able to charge my battery system sufficiently to never have to pull from the grid during peak charge times.


# Design Goals

Provide a machanism where I can set the system to charge from the grid
Provide a mechanism for seeing the current charge values
Provide a mechanims for turning off charging from the grid

# Eventual goals

Provide a mechanism to look at current SoC, discharge rate and current time, determine if we'll be below a given %SoC by the given Peak time, set to charge from grid if we'll be below that, turn off at given peak time. (Is this better suited to system level bash script?)
Home Assistant integration
Adjust SBAM code to do same.

# Non Goals

None as yet

# Objects

SimpleStorageControl
  Constructor:
    requires: modbus client object
    optional: 
  
  method: ChargeFromGrid
  params: Optional kW to charge at, default: MaxChargePower
  returns: None
  
  method: StopChargeFromGrid
  params: None
  returns: None
  
  method: getStateOfCharge
  params: None
  returns: Integer, percent

  method: getMaxChargePower
  params: None
  returns: Integer, Watts
  
  
  

