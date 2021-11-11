#!/usr/bin/env python3

"""
File:         filter_gte_file.py
Created:      2021/10/28
Last Changed: 2021/11/10
Author:       M.Vochteloo

Copyright (C) 2020 M.Vochteloo
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

A copy of the GNU General Public License can be found in the LICENSE file in the
root directory of this source tree. If not, see <https://www.gnu.org/licenses/>.
"""

# Standard imports.
from __future__ import print_function
from pathlib import Path
import argparse
import glob
import os

# Third party imports.
import pandas as pd
import numpy as np

# Local application imports.

# Metadata
__program__ = "Filter GTE file"
__author__ = "Martijn Vochteloo"
__maintainer__ = "Martijn Vochteloo"
__email__ = "m.vochteloo@rug.nl"
__license__ = "GPLv3"
__version__ = 1.0
__description__ = "{} is a program developed and maintained by {}. " \
                  "This program is licensed under the {} license and is " \
                  "provided 'as-is' without any warranty or indemnification " \
                  "of any kind.".format(__program__,
                                        __author__,
                                        __license__)

"""
Syntax: 
./filter_gte_file.py -gte /groups/umcg-bios/tmp01/projects/PICALO/data/BIOS_GTE.txt.gz -e ../data/BIOS_SamplesWithoutRNAAlignmentInfo.txt.gz -o BIOS_noRNAPhenoNA

./filter_gte_file.py -gte /groups/umcg-bios/tmp01/projects/PICALO/data/BIOS_GTE.txt.gz -e ../data/BIOS_SamplesWithoutRNAAlignmentInfo_and_MDSOutlierSamples.txt.gz -o BIOS_noRNAPhenoNA_NoMDSOutlier 
"""


class main():
    def __init__(self):
        # Get the command line arguments.
        arguments = self.create_argument_parser()
        self.gte_path = getattr(arguments, 'genotype_to_expression')
        self.e_gte_path = getattr(arguments, 'exclude_genotype_to_expression')
        outdir = getattr(arguments, 'outdir')

        # Set variables.
        self.outdir = os.path.join(str(Path(__file__).parent.parent), 'filter_gte_file', outdir)
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

    @staticmethod
    def create_argument_parser():
        parser = argparse.ArgumentParser(prog=__program__,
                                         description=__description__,
                                         )

        # Add optional arguments.
        parser.add_argument("-v",
                            "--version",
                            action="version",
                            version="{} {}".format(__program__,
                                                   __version__),
                            help="show program's version number and exit.")
        parser.add_argument("-gte",
                            "--genotype_to_expression",
                            type=str,
                            required=False,
                            default=None,
                            help="The path to the genotype-to-expression"
                                 " link matrix.")
        parser.add_argument("-e",
                            "--exclude_genotype_to_expression",
                            type=str,
                            required=True,
                            help="The path to the samples to remove"
                                 "in GTE format.")
        parser.add_argument("-o",
                            "--outdir",
                            type=str,
                            required=True,
                            help="The path to the output directory.")

        return parser.parse_args()

    def start(self):
        self.print_arguments()

        print("Loading data.")
        gte_df = self.load_file(self.gte_path, header=0, index_col=None)
        se_df = self.load_file(self.e_gte_path, header=0, index_col=None)
        print(gte_df)
        print(se_df)
        print(se_df["dataset"].value_counts())

        ########################################################################

        print("Removing samples.")
        remove_rnaseq_ids = set(se_df["rnaseq_id"])
        mask = [False if sample in remove_rnaseq_ids else True for sample in gte_df["rnaseq_id"]]
        subset_gte_df = gte_df.loc[mask, :]
        del gte_df

        ########################################################################

        print("Saving files.")
        # Gene-to-expression file.
        self.save_file(df=subset_gte_df, outpath=os.path.join(self.outdir, "GenotypeToExpression.txt.gz"), index=False)

        # Sample-to-dataset file.
        std_df = subset_gte_df.loc[:, ["rnaseq_id", "dataset"]]
        std_df.columns = ["sample", "dataset"]
        self.save_file(df=std_df, outpath=os.path.join(self.outdir, "SampleToDataset.txt.gz"), index=False)

        # Family-genotype file (for MDS analyses).
        gte_fid_df = subset_gte_df.loc[:, ["genotype_id"]].copy()
        gte_fid_df.insert(0, "family_id", 0)
        self.save_file(df=gte_fid_df, outpath=os.path.join(self.outdir, "FamilyToGenotype.txt"), header=False, index=False)

    @staticmethod
    def load_file(inpath, header, index_col, sep="\t", low_memory=True,
                  nrows=None, skiprows=None):
        if inpath.endswith(".pkl"):
            df = pd.read_pickle(inpath)
        else:
            df = pd.read_csv(inpath, sep=sep, header=header, index_col=index_col,
                             low_memory=low_memory, nrows=nrows, skiprows=skiprows)
        print("\tLoaded dataframe: {} "
              "with shape: {}".format(os.path.basename(inpath),
                                      df.shape))
        return df

    @staticmethod
    def save_file(df, outpath, header=True, index=True, sep="\t"):
        compression = 'infer'
        if outpath.endswith('.gz'):
            compression = 'gzip'

        df.to_csv(outpath, sep=sep, index=index, header=header,
                  compression=compression)
        print("\tSaved dataframe: {} "
              "with shape: {}".format(os.path.basename(outpath),
                                      df.shape))

    def print_arguments(self):
        print("Arguments:")
        print("  > GTE path: {}".format(self.gte_path))
        print("  > Exclude GTE path: {}".format(self.e_gte_path))
        print("  > Output directory: {}".format(self.outdir))
        print("")


if __name__ == '__main__':
    m = main()
    m.start()