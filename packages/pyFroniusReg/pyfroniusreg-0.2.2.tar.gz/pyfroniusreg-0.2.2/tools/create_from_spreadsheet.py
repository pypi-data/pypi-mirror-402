#!/usr/bin/env python3

"""
This is meant to take the fronius provided spreadsheet and munge it into
a list of FroniusRegisters and ScaledFroniusRegisters
"""

import pandas
import argparse

from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="create_from_spreadsheet",
        description="Generate python registers from the given spreadsheet",
    )

    parser.add_argument("filename")
    parser.add_argument(
        "-o",
        "--output",
        help="Output Filename, defaults to input filename with the .py extnention instead",
    )
    parser.add_argument(
        "-u",
        "--modbus_unit",
        default=1,
        type=int,
        help="The modbus unit, my Inverter is 1, Smart Meter is 200",
    )
    args = parser.parse_args()

    input_file = Path(args.filename)

    if args.output is None:
        output_file = Path("./" + input_file.stem.lower() + ".py")
    else:
        output_file = Path(args.output)

    input_df = pandas.read_excel(open(input_file, "rb"), header=0, skiprows=2)

    # Coerce 'Start' strings to ints so we can sort
    input_df = input_df[input_df["Start"].apply(lambda x: isinstance(x, (int)))]

    # sort on Start register
    input_df = input_df.sort_values(["Start"])

    with open(output_file, "w") as f:
        f.write("from pyfroniusreg import froniusreg\n\n")
        # Output the direct registers
        for index, row in input_df.iterrows():
            if row["Type"] == "string":
                data_type = f'string{row["Size"]}'
            else:
                data_type = row["Type"]

            if row["Range\nof values"] != "not supported":
                f.write(
                    '%s = froniusreg.FroniusReg(%d, froniusreg.%s, %d, """%s""")\n'
                    % (
                        row["Name"].replace("/", "_"),
                        row["Start"],
                        data_type,
                        args.modbus_unit,
                        row["Description"],
                    )
                )

        # output the scaled registers
        for index, row in input_df.iterrows():
            if not pandas.isna(row["Scale Factor"]):
                if row["Range\nof values"] != "not supported":
                    f.write(
                        "scaled%s = froniusreg.ScaledFroniusReg(%s, %s)\n"
                        % (
                            row["Name"].replace("/", "_"),
                            row["Name"].replace("/", "_"),
                            row["Scale Factor"],
                        )
                    )


if __name__ == "__main__":
    main()
