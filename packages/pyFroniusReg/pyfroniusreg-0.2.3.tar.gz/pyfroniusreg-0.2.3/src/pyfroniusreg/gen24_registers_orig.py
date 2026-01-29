from pyfroniusreg import froniusreg

MaxChaRte = froniusreg.FroniusReg(40155, froniusreg.uint16, 1, "Max Charge Rate")
MaxChaRte_SF = froniusreg.FroniusReg(40156, froniusreg.int16, 1, "Max Charge Rate SF")

wChaGra = froniusreg.FroniusReg(40357, froniusreg.uint16, 1, "Max Charge Power")
storageStateOfCharge = froniusreg.FroniusReg(
    40362, froniusreg.uint16, 1, "Storage State of Charge"
)
storageStateOfChargeSF = froniusreg.FroniusReg(
    40376, froniusreg.int16, 1, "Storage State of Charge Scaling Factor"
)
scaledStateOfCharge = froniusreg.ScaledFroniusReg(storageStateOfCharge, storageStateOfChargeSF)

ID = froniusreg.FroniusReg(
    40003,
    froniusreg.uint16,
    1,
    "Well-known value. Uniquely identifies this as a sunspec model 'common' (1)",
)
L = froniusreg.FroniusReg(40004, froniusreg.uint16, 1, "Sunspec model commen register count")
Mn = froniusreg.FroniusReg(40005, froniusreg.string16, 1, "Manufacturer")
Md = froniusreg.FroniusReg(40021, froniusreg.string16, 1, "Device Model")
Vr = froniusreg.FroniusReg(40045, froniusreg.string8, 1, "SW version")
SN = froniusreg.FroniusReg(40068, froniusreg.string16, 1, "Serial Number")
DA = froniusreg.FroniusReg(40069, froniusreg.uint16, 1, "Modbus Device Address")

InputID = froniusreg.FroniusReg(40304, froniusreg.uint16, 1, "Input ID")
InputIDString = froniusreg.FroniusReg(40305, froniusreg.string8, 1, "Input ID String")

module3DCW = froniusreg.FroniusReg(
    40325,
    froniusreg.uint16,
    1,
    "When the battery is discharged the data-points of the charge input are set to 0",
)

module4DCW = froniusreg.FroniusReg(
    40345,
    froniusreg.uint16,
    1,
    "When the battery is charged the data-points of the discharge input are set to 0",
)

DCW_SF = froniusreg.FroniusReg(40268, froniusreg.int16, 1, "DC Power Scaling factor")

OutWRte = froniusreg.FroniusReg(40366, froniusreg.int16, 1, "DischargeRate")
InWRte = froniusreg.FroniusReg(40367, froniusreg.int16, 1, "ChargeRate")
WRteSF = froniusreg.FroniusReg(40379, froniusreg.int16, 1, "ScalingFactor for storage Watts")
StorCtl_Mode = froniusreg.FroniusReg(40359, froniusreg.uint16, 1, "Hold/Charge/Discharge limit")
MinRsvPct = froniusreg.FroniusReg(40361, froniusreg.uint16, 1, "Reserve Percentage")
InOutWRte_RvrtTms = froniusreg.FroniusReg(
    40369, froniusreg.uint16, 1, "Revert timer for charge settings"
)
ChaGriSet = froniusreg.FroniusReg(
    40371, froniusreg.uint16, 1, "enum16, 0 = PV only, 1 = Grid enabled"
)
WChaDisChaGra_SF = froniusreg.FroniusReg(40373, froniusreg.int16, 1, "Charge/Discharge Power SF")
MinRsvPct_SF = froniusreg.FroniusReg(40375, froniusreg.int16, 1, "Reserve Percentage Scaling")

scaledOutWRte = froniusreg.ScaledFroniusReg(OutWRte, WRteSF)
scaledInWRte = froniusreg.ScaledFroniusReg(InWRte, WRteSF)
scaledReserve = froniusreg.ScaledFroniusReg(MinRsvPct, MinRsvPct_SF)
scaledMaxChaRte = froniusreg.ScaledFroniusReg(MaxChaRte, MaxChaRte_SF)
scaledMaxWChaGra = froniusreg.ScaledFroniusReg(wChaGra, WChaDisChaGra_SF)
scaledToBattery = froniusreg.ScaledFroniusReg(module3DCW, DCW_SF)
scaledFromBattery = froniusreg.ScaledFroniusReg(module4DCW, DCW_SF)
