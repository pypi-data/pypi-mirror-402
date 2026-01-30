import argparse

from typing import Iterator, Tuple

import numpy as np
import pandas as pd

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq

settings = {}


def get_paf(paf_path: str) -> pd.DataFrame:
    """Read a .paf file and return a respective pd.DataFrame.

    Parameters
    ----------
    paf_path : str
        Path to .paf alignment of query to target.

    Returns
    -------
    pd.DataFrame
        Table of .paf alignments

    Examples
    --------
    >>> paf = get_paf("test.paf")
    >>> print(paf.head())
       query  query_len  query_start  query_end strand target  target_len  target_start  target_end  n_match  aln_len  mapq
    0  contig1       1000            0        100      +   chr1       2000           100         200      100      100    60

    """
    cols = [
        "query", "query_len", "query_start", "query_end", "strand", "target",
        "target_len", "target_start", "target_end", "n_match", "aln_len",
        "mapq"
    ]
    df = pd.read_csv(paf_path,
                     sep='\t',
                     header=None,
                     names=cols,
                     usecols=range(12))

    return df


def get_best_matching_target(query_paf: pd.DataFrame) -> str:
    """Get best match for .paf.

    This function reads a .paf table and returns the 'target' with
    largest sum of alignments.

    Parameters
    ----------
    query_paf : pd.DataFrame
        Table of .paf alignments of single 'query' contig

    Returns
    -------
    str
        'target' contig name with largest sum of alignments

    Examples
    --------
    >>> paf = {
    ...     'query': ['contig1', 'contig1', 'contig1'],
    ...     'target': ['chr1', 'chr2', 'chr1'],
    ...     'aln_len': [100, 200, 150]
    ... }
    >>> df = pd.DataFrame(paf_data)
    >>> get_best_matching_target(df)
    'chr1'

    """
    sums = query_paf.groupby("target")["aln_len"].sum()
    sums.sort_values(ascending=False, inplace=True)
    return sums.index[0]


def is_reverse_complement(query_paf: pd.DataFrame, target: str) -> bool:
    """Get optimal orientation of 'query' contig.

    This function reads a .paf table and returns a boolean, indicating whether
    forward alignments or reverse complement alignments of a query contig have
    a larger sum of aligned bases.

    Parameters
    ----------
    query_paf : pd.DataFrame
        Table of .paf alignments of single 'query' contig
    target : str
        'target' contig to find best orientation for

    Returns
    -------
    bool
        Boolean, indicating whether forward sequence or reverse
        complement maximize alignments

    Examples
    --------
    >>> paf = {
    ...     'query': ['contig1', 'contig1'],
    ...     'target': ['chr1', 'chr1'],
    ...     'strand': ['+', '-'],
    ...     'aln_len': [100, 200]
    ... }
    >>> df = pd.DataFrame(paf_data)
    >>> is_reverse_complement(df, 'chr1')
    True

    """
    query_paf = query_paf.loc[query_paf["target"] == target, :]

    lens = query_paf.groupby("strand")["aln_len"].sum()

    if len(lens.keys()) == 0:
        ret = False
    elif len(lens.keys()) == 1:
        ret = lens.keys()[0] == "-"
    else:
        ret = lens.loc["-"] > lens.loc["+"]

    return ret


def get_best_chrs(paf: pd.DataFrame) -> Tuple[dict, dict]:
    """Get best 'target' contig and orientation for each 'query' contig.

    This function gets a pd.DataFrame with .paf alignments and returns
    the best 'target' contig and orientation of each 'query' contig.

    Parameters
    ----------
    paf : pd.DataFrame
        pd.DataFrame with .paf alignments

    Returns
    -------
    Tuple[dict, dict]
        Tuple of dicts for ideal 'target' contigs and orientations as
        values. Keys are 'query' contig names

    Examples
    --------
    >>> get_best_chrs(paf)
    ({'contig1': 'chr1', 'contig2': 'chr2'}, {'contig1': True, 'contig2': False})

    """
    best_matches = {}
    reorient = {}

    for name, query_contig in paf.groupby("query"):
        best_matches[name] = get_best_matching_target(query_contig)
        reorient[name] = is_reverse_complement(query_contig,
                                               best_matches[name])

    return best_matches, reorient


def contigs_per_chr(best_matches: dict) -> dict:
    """Get dict with 'query' contigs by 'target' contigs.

    Create a dict with 'target' contig names as keys and lists of
    respective 'query' contig names as values.

    Parameters
    ----------
    best_matches : dict
        Dict with 'query' contig names as keys and 'target' contig names as
        values

    Returns
    -------
    dict
        Dict with 'target' contig names as key and lists of 'query'
        contig names as values

    Examples
    --------
    >>> contigs_per_chr({'contig1': 'chr1', 'contig2': 'chr1'})
    {'chr1': ['contig1', 'contig2']}

    """
    ret = {}

    for query, target in best_matches.items():
        ret[target] = ret.get(target, []) + [query]

    return ret


def order_query_contigs_by_target(target: str, query_contigs: list,
                                  paf: pd.DataFrame) -> list:
    """Order 'query_contigs' based on alignments to 'target' contig in 'paf'.

    Order 'query' contigs along 'target' contig based on 'target_start'
    fields of .paf file. The largest aligned segment of each 'query'
    contig determines the position on 'target' contig.

    Parameters
    ----------
    target : str
        'target' contig name
    query_contigs : list
        'query' contig names
    paf : pd.DataFrame
        pd.DataFrame with alignments of 'query' to 'target'

    Returns
    -------
    list
        List of 'query' contigs ordered along 'target' contig

    Examples
    --------
    >>> paf_data = {
    ...     'query': ['contig1', 'contig2'],
    ...     'target': ['chr1', 'chr1'],
    ...     'target_start': [100, 50]
    ... }
    >>> df = pd.DataFrame(paf_data)
    >>> order_query_contigs_by_target('chr1', ['contig1', 'contig2'], df)
    ['contig2', 'contig1']
    """
    ret = []

    paf = paf.loc[paf["target"] == target, :]

    pos = {}

    for query, paf_query in paf.groupby("query"):
        if query not in query_contigs:
            continue

        pos[query] = paf_query.iloc[0, :]["target_start"]

    ret = pd.Series(pos).sort_values().index

    return ret


def get_fasta(fasta_path: str) -> Iterator[SeqRecord]:
    """Get SeqIO Iterator of .fasta file.

    Get SeqIO Iterator of .fasta file stored at 'fasta_path'.

    Parameters
    ----------
    fasta_path : str
        Path to .fasta file.

    Returns
    -------
    Iterator[SeqRecord]
        Iterator of SeqRecords of .fasta file.

    Examples
    --------
    >>> fasta = get_fasta("test.fasta")
    >>> records = list(fasta)
    >>> print(records[0].id)
    'contig1'
    """
    fasta = SeqIO.parse(fasta_path, format="fasta")

    return fasta


def get_fasta_contig_order(fasta) -> list:
    """Get contig order from .fasta file.

    Get the order of contig names as in .fasta file.

    Parameters
    ----------
    fasta : Iterator[SeqRecord]
        Iterator of SeqRecord objects

    Returns
    -------
    list
        List of contig names ordered as in .fasta file

    Examples
    --------
    >>> fasta = SeqIO.parse("example.fasta", format="fasta")
    >>> get_fasta_contig_order(fasta)
    ['contig1', 'contig2', 'contig3']

    """
    return [record.id for record in fasta]


def parse_args() -> None:
    argparser = argparse.ArgumentParser(
        description="Sort contigs based on alignment to reference")

    argparser.add_argument(
        "-p",
        "--paf",
        required=True,
        help="path to .paf file containing alignments of query to target")
    argparser.add_argument("-q",
                           "--query",
                           required=True,
                           help="path to .fasta file of query contigs")
    argparser.add_argument("-t",
                           "--target",
                           required=True,
                           help="path to .fasta file of target contigs")
    argparser.add_argument("-o",
                           "--out",
                           required=True,
                           help="path to output .fasta file")
    argparser.add_argument("-rc",
                           "--rename_contigs",
                           default=False,
                           action='store_true',
                           help="rename contigs in output file")
    argparser.add_argument("-rp",
                           "--rename-prefix",
                           default="ctg",
                           help="prefix for renamed contigs")

    args = argparser.parse_args()

    settings["paf"] = args.paf
    settings["query"] = args.query
    settings["target"] = args.target
    settings["out"] = args.out
    settings["rename_contigs"] = args.rename_contigs
    settings["rename_prefix"] = args.rename_prefix


def main() -> None:
    """Main function.

    This is the main function of 'sort-contigs.py'.

    Examples
    --------
    >>> main()
    None

    """
    # Parse arguments
    parse_args()
    # Get pd.DataFrame with .paf
    paf = get_paf(settings["paf"])
    # Get query .fasta
    query_fasta_indexed = get_fasta(settings["query"])
    # Get target .fasta
    target_fasta = get_fasta(settings["target"])

    # Get contig order of target
    orig_target_order = get_fasta_contig_order(target_fasta)
    # Get contig order of query
    orig_query_order = get_fasta_contig_order(query_fasta_indexed)

    # Determine target contigs and orientation
    best_target_per_query, reorient = get_best_chrs(paf)
    # Determine query contig order for each target contig
    query_contigs_per_target = contigs_per_chr(best_target_per_query)

    # Differ between aligned and unaligned contigs
    matched_query_contigs = []
    for name, queries in query_contigs_per_target.items():
        matched_query_contigs.extend(queries)

    unmatched_query_contigs = list(
        set(orig_query_order) - set(matched_query_contigs))

    # Create output records
    output_records = []

    # Create indexed SeqIO object
    query_fasta_indexed = SeqIO.index(settings["query"], format="fasta")

    # Iterate in 'target' order
    for target in orig_target_order:
        # Skip if not aligned
        if target not in query_contigs_per_target.keys():
            continue

        # Get order of query contigs for target contig
        query_contigs = order_query_contigs_by_target(
            target, query_contigs_per_target[target], paf)
        # Iterate query contigs in order
        for query_contig in query_contigs:
            # Get sequence
            seq = query_fasta_indexed[query_contig].seq
            # Reverse complement, if alignment is greater
            seq = seq.reverse_complement() if reorient[query_contig] else seq
            # Append record to output
            output_records.append(
                SeqRecord(
                    seq=seq,
                    id=query_fasta_indexed[query_contig].id,
                    description=query_fasta_indexed[query_contig].description))

    # Iterate over unaligned query contigs
    for query_contig in unmatched_query_contigs:
        # Append all unaligned query contigs
        output_records.append(
            SeqRecord(
                seq=query_fasta_indexed[query_contig].seq,
                id=query_fasta_indexed[query_contig].id,
                description=query_fasta_indexed[query_contig].description))

    # If 'settings['rename_contigs'] is set, enumerate/rename contigs
    if settings["rename_contigs"]:
        for i, record in enumerate(output_records):
            record.id = "{}{:04d}".format(settings["rename_prefix"], i + 1)

    # Write to output
    with open(settings["out"], "w") as f:
        SeqIO.write(output_records, f, "fasta")
        f.close()


if __name__ == "__main__":
    main()
