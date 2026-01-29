# pyFroniusReg

The aim of this python library is to provide some nice to use abstractions to interact with Fronius(tm) solar inverters and storage systems over ModBus. It is tested on a Gen24 Primo 5kW system with an attached BYD battery storage system using 'float' mode of the sunspec ModBus over TCP protocol. Some testing has been done in int&sf mode.

# Installation

Currently you can grab the .whl from the releases page. I'll figure out PyPI addition eventually

# Examples

check_peak.py: Designed to be run from a cron job to check if we have enough storage to run the house for the peak pricing periods.

force_charge.py: Use the library to force my system to charge at 2.5kW

read_regs.py: Use the library to read some relevant registers from the non-storage inverter

read_regs_storage.py: use the library to read some relevant registers from the storage inverter

reset_charge.py: Use the library to set my storage system back to defaults


# Acknowledgements

A lot of ideas and some orignating code came from:
https://github.com/oscarknapp/Fronius-Gen-24-Modbus-Integration/tree/main


Special thanks to VK2TTY <@vk2tty@mastodon.radio> for their generous assistance in bringing me up to speed with a more pythonic way of doing things!


# Legal

pyFroniusReg, a python library for interacting with Fronius inverters
Copyright (C) 2024  Paul Warren

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Froinus(tm), Symo(tm), Primo(tm), Tauro(tm) are tradmarks of Fronius International GmbH who have no involvement in this project.
