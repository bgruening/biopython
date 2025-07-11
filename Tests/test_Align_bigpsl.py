# Copyright 2022 by Michiel de Hoon.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.
"""Tests for Align.bigpsl module."""
import tempfile
import unittest

from Bio import Align
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import BeforePosition
from Bio.SeqFeature import CompoundLocation
from Bio.SeqFeature import ExactPosition
from Bio.SeqFeature import SeqFeature
from Bio.SeqFeature import SimpleLocation

try:
    import numpy as np
except ImportError:
    from Bio import MissingPythonDependencyError

    raise MissingPythonDependencyError(
        "Install numpy if you want to use Bio.Align.bigpsl."
    ) from None


class TestAlign_declaration(unittest.TestCase):
    def test_declaration(self):
        with open("Blat/bigPsl.as") as stream:
            declaration = stream.read()
        self.assertEqual(str(Align.bigpsl.declaration), declaration)


class TestAlign_dna_rna(unittest.TestCase):
    # The bigPsl file dna_rna.psl.bb was generated using these commands:
    # pslToBigPsl dna_rna.psl stdout | sort -k1,1 -k2,2n > dna_rna.bigPslInput
    # bedToBigBed -type=bed12+13 -tab -as=bigPsl.as dna_rna.bigPslInput hg38.chrom.sizes dna_rna.psl.bb

    def setUp(self):
        data = {}
        records = SeqIO.parse("Blat/dna.fa", "fasta")
        for record in records:
            name, start_end = record.id.split(":")
            assert name == "chr3"
            start, end = start_end.split("-")
            start = int(start)
            end = int(end)
            sequence = str(record.seq)
            assert len(sequence) == end - start
            data[start] = sequence
        self.dna = data
        records = SeqIO.parse("Blat/rna.fa", "fasta")
        self.rna = {record.id: record.seq for record in records}
        self.path = "Blat/dna_rna.psl.bb"

    def test_reading(self):
        """Test parsing dna_rna.psl.bb."""
        alignments = Align.parse(self.path, "bigpsl")
        self.check_alignments(alignments)
        alignments = iter(alignments)
        self.check_alignments(alignments)
        with Align.parse(self.path, "bigpsl") as alignments:
            self.check_alignments(alignments)
        with self.assertRaises(AttributeError):
            alignments._stream
        with Align.parse(self.path, "bigpsl") as alignments:
            pass
        with self.assertRaises(AttributeError):
            alignments._stream

    def test_writing(self):
        """Test writing dna_rna.psl.bb."""
        alignments = Align.parse(self.path, "bigpsl")
        with tempfile.TemporaryFile() as output:
            Align.write(alignments, output, "bigpsl")
            output.flush()
            output.seek(0)
            alignments = Align.parse(output, "bigpsl")
            self.check_alignments(alignments)

    def check_alignments(self, alignments):
        self.assertEqual(alignments.declaration, Align.bigpsl.declaration)
        self.assertEqual(len(alignments.targets), 1)
        self.assertEqual(alignments.targets[0].id, "chr3")
        self.assertEqual(len(alignments.targets[0]), 198295559)
        self.assertEqual(len(alignments), 4)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 175)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 6)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 42530895)
        self.assertEqual(alignment.thickEnd, 42532606)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 1711))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr3")
        self.assertEqual(alignment.query.id, "NR_046654.1")
        self.assertEqual(len(alignment.target.seq), 198295559)
        self.assertEqual(len(alignment.query.seq), 181)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[42530895, 42530958, 42532020, 42532095, 42532563, 42532606],
                          [     181,      118,      118,       43,       43,        0]])
                # fmt: on
            )
        )
        dna = Seq(self.dna, length=len(alignment.target))
        alignment.target.seq = dna
        alignment.query.seq = self.rna[alignment.query.id]
        self.assertTrue(
            np.array_equal(
                alignment.substitutions,
                # fmt: off
            np.array([[36.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0., 40.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0., 57.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0.,  0., 42.,  0.,  0.,  0.,  0.],
                      [ 2.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  1.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0.,  3.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
                     ])
            )
        )
        self.assertEqual(alignment.substitutions.alphabet, "ACGTacgt")
        matches = sum(
            alignment.substitutions[c, c] for c in alignment.substitutions.alphabet
        )
        repMatches = sum(
            alignment.substitutions[c, c.swapcase()]
            for c in alignment.substitutions.alphabet
        )
        self.assertEqual(matches, alignment.matches)
        self.assertEqual(repMatches, alignment.repMatches)
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (181 aligned letters; 175 identities; 6 mismatches; 1530 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 181:
        identities = 175,
        mismatches = 6.
    gaps = 1530:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 1530:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 1530:
                open_internal_deletions = 2,
                extend_internal_deletions = 1528;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 1530)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 1530)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 1530)
        self.assertEqual(counts.gaps, 1530)
        self.assertEqual(counts.aligned, 181)
        self.assertEqual(counts.identities, 175)
        self.assertEqual(counts.mismatches, 6)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 172)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 6)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 42530895)
        self.assertEqual(alignment.thickEnd, 42532606)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 1714))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr3")
        self.assertEqual(alignment.query.id, "NR_046654.1_modified")
        self.assertEqual(len(alignment.target.seq), 198295559)
        self.assertEqual(len(alignment.query.seq), 190)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[42530895, 42530922, 42530922, 42530958, 42532020,
                           42532037, 42532039, 42532095, 42532563, 42532606],
                          [     185,      158,      155,      119,      119,
                                102,      102,       46,       46,        3],
                         ])
                # fmt: on
            )
        )
        dna = Seq(self.dna, length=len(alignment.target))
        alignment.target.seq = dna
        alignment.query.seq = self.rna[alignment.query.id]
        self.assertTrue(
            np.array_equal(
                alignment.substitutions,
                # fmt: off
            np.array([[34.,  0.,  0.,  1.,  0.,  0.,  0.,  0.],
                      [ 0., 40.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0., 57.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0.,  0., 41.,  0.,  0.,  0.,  0.],
                      [ 2.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  1.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0.,  3.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
                     ]),
            )
        )
        self.assertEqual(alignment.substitutions.alphabet, "ACGTacgt")
        matches = sum(
            alignment.substitutions[c, c] for c in alignment.substitutions.alphabet
        )
        repMatches = sum(
            alignment.substitutions[c, c.swapcase()]
            for c in alignment.substitutions.alphabet
            if c != "X"
        )
        self.assertEqual(matches, alignment.matches)
        self.assertEqual(repMatches, alignment.repMatches)
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (179 aligned letters; 172 identities; 7 mismatches; 1535 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 179:
        identities = 172,
        mismatches = 7.
    gaps = 1535:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 1535:
            internal_insertions = 3:
                open_internal_insertions = 1,
                extend_internal_insertions = 2;
            internal_deletions = 1532:
                open_internal_deletions = 3,
                extend_internal_deletions = 1529;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 3)
        self.assertEqual(counts.internal_deletions, 1532)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 1535)
        self.assertEqual(counts.insertions, 3)
        self.assertEqual(counts.deletions, 1532)
        self.assertEqual(counts.gaps, 1535)
        self.assertEqual(counts.aligned, 179)
        self.assertEqual(counts.identities, 172)
        self.assertEqual(counts.mismatches, 7)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 165)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 39)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 48663767)
        self.assertEqual(alignment.thickEnd, 48669174)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 5407))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr3")
        self.assertEqual(alignment.query.id, "NR_111921.1")
        self.assertEqual(len(alignment.target.seq), 198295559)
        self.assertEqual(len(alignment.query.seq), 216)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array( [[48663767, 48663813, 48665640, 48665722, 48669098, 48669174],
                           [       0,        46,      46,      128,      128,      204]]),
                # fmt: on
            )
        )
        dna = Seq(self.dna, length=len(alignment.target.seq))
        alignment.target.seq = dna
        alignment.query.seq = self.rna[alignment.query.id]
        self.assertTrue(
            np.array_equal(
                alignment.substitutions,
                # fmt: off
            np.array([[53.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0., 35.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0., 50.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0.,  0., 27.,  0.,  0.,  0.,  0.],
                      [ 9.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  7.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0., 16.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0.,  0.,  7.,  0.,  0.,  0.,  0.],
                     ])
            )
        )
        self.assertEqual(alignment.substitutions.alphabet, "ACGTacgt")
        matches = sum(
            alignment.substitutions[c, c] for c in alignment.substitutions.alphabet
        )
        repMatches = sum(
            alignment.substitutions[c, c.swapcase()]
            for c in alignment.substitutions.alphabet
        )
        self.assertEqual(matches, alignment.matches)
        self.assertEqual(repMatches, alignment.repMatches)
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (204 aligned letters; 165 identities; 39 mismatches; 5203 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 204:
        identities = 165,
        mismatches = 39.
    gaps = 5203:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 5203:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 5203:
                open_internal_deletions = 2,
                extend_internal_deletions = 5201;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 5203)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 5203)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 5203)
        self.assertEqual(counts.gaps, 5203)
        self.assertEqual(counts.aligned, 204)
        self.assertEqual(counts.identities, 165)
        self.assertEqual(counts.mismatches, 39)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 162)
        self.assertEqual(alignment.misMatches, 2)
        self.assertEqual(alignment.repMatches, 39)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 48663767)
        self.assertEqual(alignment.thickEnd, 48669174)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 5409))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr3")
        self.assertEqual(alignment.query.id, "NR_111921.1_modified")
        self.assertEqual(len(alignment.target.seq), 198295559)
        self.assertEqual(len(alignment.query.seq), 220)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[48663767, 48663795, 48663796, 48663813, 48665640,
                           48665716, 48665716, 48665722, 48669098, 48669174],
                          [       3,       31,       31,       48,       48,
                                124,      126,      132,      132,      208]
                         ])
                # fmt: on
            )
        )
        dna = Seq(self.dna, length=len(alignment.target))
        alignment.target.seq = dna
        alignment.query.seq = self.rna[alignment.query.id]
        self.assertTrue(
            np.array_equal(
                alignment.substitutions,
                # fmt: off
            np.array([[53.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0., 34.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  2., 48.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0.,  0., 27.,  0.,  0.,  0.,  0.],
                      [ 9.,  0.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  7.,  0.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0., 16.,  0.,  0.,  0.,  0.,  0.],
                      [ 0.,  0.,  0.,  7.,  0.,  0.,  0.,  0.],
                     ]),
            )
        )
        self.assertEqual(alignment.substitutions.alphabet, "ACGTacgt")
        matches = sum(
            alignment.substitutions[c, c] for c in alignment.substitutions.alphabet
        )
        repMatches = sum(
            alignment.substitutions[c, c.swapcase()]
            for c in alignment.substitutions.alphabet
            if c != "X"
        )
        self.assertEqual(matches, alignment.matches)
        self.assertEqual(repMatches, alignment.repMatches)
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (203 aligned letters; 162 identities; 41 mismatches; 5206 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 203:
        identities = 162,
        mismatches = 41.
    gaps = 5206:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 5206:
            internal_insertions = 2:
                open_internal_insertions = 1,
                extend_internal_insertions = 1;
            internal_deletions = 5204:
                open_internal_deletions = 3,
                extend_internal_deletions = 5201;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 2)
        self.assertEqual(counts.internal_deletions, 5204)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 5206)
        self.assertEqual(counts.insertions, 2)
        self.assertEqual(counts.deletions, 5204)
        self.assertEqual(counts.gaps, 5206)
        self.assertEqual(counts.aligned, 203)
        self.assertEqual(counts.identities, 162)
        self.assertEqual(counts.mismatches, 41)
        self.assertRaises(StopIteration, next, alignments)


class TestAlign_dna(unittest.TestCase):
    queries = {
        record.id: record.seq for record in SeqIO.parse("Blat/fasta_34.fa", "fasta")
    }

    def test_reading_psl_34_001(self):
        """Test parsing psl_34_001.psl.bb."""
        # The bigPsl file psl_34_001.psl.bb was generated using these commands:
        # pslToBigPsl -fa=fasta_34.fa psl_34_001.psl stdout | sort -k1,1 -k2,2n > psl_34_001.bigPslInput
        # bedToBigBed -type=bed12+13 -tab -as=bigPsl.as psl_34_001.bigPslInput hg19.chrom.sizes psl_34_001.psl.bb

        path = "Blat/psl_34_001.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        self.check_psl_34_001(alignments)

    def test_writing_psl_34_001(self):
        """Test writing psl_34_001.psl.bb."""
        path = "Blat/psl_34_001.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        with tempfile.TemporaryFile() as output:
            Align.write(alignments, output, "bigpsl", fa=True)
            output.flush()
            output.seek(0)
            alignments = Align.parse(output, "bigpsl")
            self.check_psl_34_001(alignments)

    def check_psl_34_001(self, alignments):
        self.assertEqual(alignments.declaration, Align.bigpsl.declaration)
        self.assertEqual(len(alignments.targets), 10)
        self.assertEqual(alignments.targets[0].id, "chr1")
        self.assertEqual(len(alignments.targets[0]), 249250621)
        self.assertEqual(alignments.targets[1].id, "chr10")
        self.assertEqual(len(alignments.targets[1]), 135534747)
        self.assertEqual(alignments.targets[2].id, "chr13")
        self.assertEqual(len(alignments.targets[2]), 115169878)
        self.assertEqual(alignments.targets[3].id, "chr18")
        self.assertEqual(len(alignments.targets[3]), 78077248)
        self.assertEqual(alignments.targets[4].id, "chr19")
        self.assertEqual(len(alignments.targets[4]), 59128983)
        self.assertEqual(alignments.targets[5].id, "chr2")
        self.assertEqual(len(alignments.targets[5]), 243199373)
        self.assertEqual(alignments.targets[6].id, "chr22")
        self.assertEqual(len(alignments.targets[6]), 51304566)
        self.assertEqual(alignments.targets[7].id, "chr4")
        self.assertEqual(len(alignments.targets[7]), 191154276)
        self.assertEqual(alignments.targets[8].id, "chr8")
        self.assertEqual(len(alignments.targets[8]), 146364022)
        self.assertEqual(alignments.targets[9].id, "chr9")
        self.assertEqual(len(alignments.targets[9]), 141213431)
        self.assertEqual(len(alignments), 22)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 50)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 1207056)
        self.assertEqual(alignment.thickEnd, 1207106)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 50))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[1207056, 1207106],
                          [      0,      50]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (50 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 50:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 50)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 10271783)
        self.assertEqual(alignment.thickEnd, 10271816)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 33))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg18_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 33)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[10271783, 10271816],
                          [       0,       33]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (33 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 33:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 33)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 35)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 39368490)
        self.assertEqual(alignment.thickEnd, 39368526)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[39368490, 39368526],
                          [      49,       13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 31)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 61700837)
        self.assertEqual(alignment.thickEnd, 61700871)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 34))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[61700837, 61700871],
                          [       1,       35]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (34 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 34:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 34)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 220325687)
        self.assertEqual(alignment.thickEnd, 220325721)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 34))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[220325687, 220325721],
                          [       47,        13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (34 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 34:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 34)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 99388555)
        self.assertEqual(alignment.thickEnd, 99388591)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr10")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 135534747)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[99388555, 99388591],
                          [      49,       13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 24)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 112178171)
        self.assertEqual(alignment.thickEnd, 112178196)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 25))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr10")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 135534747)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[112178171, 112178196],
                          [       35,        10]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (25 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 25:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 25)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 44)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 52759147)
        self.assertEqual(alignment.thickEnd, 52759198)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 54))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr13")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 115169878)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[52759147, 52759154, 52759160, 52759160, 52759198],
                          [       1,        8,        8,       11,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (45 aligned letters; 0 identities; 0 mismatches; 9 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 45:
        identities = 0,
        mismatches = 0.
    gaps = 9:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 9:
            internal_insertions = 3:
                open_internal_insertions = 1,
                extend_internal_insertions = 2;
            internal_deletions = 6:
                open_internal_deletions = 1,
                extend_internal_deletions = 5;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 3)
        self.assertEqual(counts.internal_deletions, 6)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 9)
        self.assertEqual(counts.insertions, 3)
        self.assertEqual(counts.deletions, 6)
        self.assertEqual(counts.gaps, 9)
        self.assertEqual(counts.aligned, 45)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 39)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 23891310)
        self.assertEqual(alignment.thickEnd, 23891349)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 39))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr18")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 78077248)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[23891310, 23891349],
                          [      10,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (39 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 39:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 39)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 27)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 43252217)
        self.assertEqual(alignment.thickEnd, 43252245)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 28))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr18")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 78077248)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[43252217, 43252245],
                          [      21,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (28 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 28:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 28)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 36)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 553742)
        self.assertEqual(alignment.thickEnd, 553781)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 39))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr19")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 59128983)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[553742, 553781],
                          [    49,     10]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (39 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 39:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 39)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 34)
        self.assertEqual(alignment.misMatches, 2)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 35483340)
        self.assertEqual(alignment.thickEnd, 35483510)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 170))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr19")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 59128983)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[35483340, 35483365, 35483499, 35483510],
                          [      10,       35,       35,       46]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 134 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 134:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 134:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 134:
                open_internal_deletions = 1,
                extend_internal_deletions = 133;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 134)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 134)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 134)
        self.assertEqual(counts.gaps, 134)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 39)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 54017130)
        self.assertEqual(alignment.thickEnd, 54017169)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 39))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr19")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 59128983)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[54017130, 54017169],
                          [      49,       10]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (39 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 39:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 39)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 17)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 53575980)
        self.assertEqual(alignment.thickEnd, 53575997)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 17))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr2")
        self.assertEqual(alignment.query.id, "hg18_dna")
        self.assertEqual(len(alignment.target.seq), 243199373)
        self.assertEqual(len(alignment.query.seq), 33)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[53575980, 53575997],
                          [      25,        8]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (17 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 17:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 17)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 35)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 120641740)
        self.assertEqual(alignment.thickEnd, 120641776)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr2")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 243199373)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[120641740, 120641776],
                          [       49,        13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 43)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 183925984)
        self.assertEqual(alignment.thickEnd, 183926028)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 48))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr2")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 243199373)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[183925984, 183925990, 183925990, 183926028],
                          [        1,         7,        11,        49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (44 aligned letters; 0 identities; 0 mismatches; 4 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 44:
        identities = 0,
        mismatches = 0.
    gaps = 4:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 4:
            internal_insertions = 4:
                open_internal_insertions = 1,
                extend_internal_insertions = 3;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 4)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 4)
        self.assertEqual(counts.insertions, 4)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 4)
        self.assertEqual(counts.aligned, 44)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 42144400)
        self.assertEqual(alignment.thickEnd, 42144436)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr22")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 51304566)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[42144400, 42144436],
                          [      11,       47]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 35)
        self.assertEqual(alignment.misMatches, 2)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 48997405)
        self.assertEqual(alignment.thickEnd, 48997442)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 37))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr22")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 51304566)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[48997405, 48997442],
                          [      49,       12]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (37 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 37:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 37)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 28)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 37558157)
        self.assertEqual(alignment.thickEnd, 37558191)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 44))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr4")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 191154276)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[37558157, 37558167, 37558173, 37558173, 37558191],
                          [      49,       39,       39,       29,       11]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (28 aligned letters; 0 identities; 0 mismatches; 16 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 28:
        identities = 0,
        mismatches = 0.
    gaps = 16:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 16:
            internal_insertions = 10:
                open_internal_insertions = 1,
                extend_internal_insertions = 9;
            internal_deletions = 6:
                open_internal_deletions = 1,
                extend_internal_deletions = 5;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 10)
        self.assertEqual(counts.internal_deletions, 6)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 16)
        self.assertEqual(counts.insertions, 10)
        self.assertEqual(counts.deletions, 6)
        self.assertEqual(counts.gaps, 16)
        self.assertEqual(counts.aligned, 28)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 16)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 61646095)
        self.assertEqual(alignment.thickEnd, 61646111)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 16))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr4")
        self.assertEqual(alignment.query.id, "hg18_dna")
        self.assertEqual(len(alignment.target.seq), 191154276)
        self.assertEqual(len(alignment.query.seq), 33)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[61646095, 61646111],
                          [      11,       27]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (16 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 16:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 16)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 41)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 95160479)
        self.assertEqual(alignment.thickEnd, 95160520)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 41))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr8")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 146364022)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[95160479, 95160520],
                          [       8,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (41 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 41:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 41)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 38)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 85737865)
        self.assertEqual(alignment.thickEnd, 85737906)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 41))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr9")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 141213431)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[85737865, 85737906],
                          [       9,       50]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (41 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 41:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 41)
        self.assertRaises(StopIteration, next, alignments)

    def test_reading_psl_34_003(self):
        """Test parsing psl_34_003.psl.bb."""
        # The bigPsl file psl_34_003.psl.bb was generated using these commands:
        # pslToBigPsl -fa=fasta_34.fa psl_34_003.psl stdout | sort -k1,1 -k2,2n > psl_34_003.bigPslInput
        # bedToBigBed -type=bed12+13 -tab -as=bigPsl.as psl_34_003.bigPslInput hg19.chrom.sizes psl_34_003.psl.bb

        path = "Blat/psl_34_003.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        self.check_psl_34_003(alignments)

    def test_writing_psl_34_003(self):
        """Test writing psl_34_003.psl.bb."""
        path = "Blat/psl_34_003.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        with tempfile.TemporaryFile() as output:
            Align.write(alignments, output, "bigpsl", fa=True)
            output.flush()
            output.seek(0)
            alignments = Align.parse(output, "bigpsl")
            self.check_psl_34_003(alignments)

    def check_psl_34_003(self, alignments):
        self.assertEqual(alignments.declaration, Align.bigpsl.declaration)
        self.assertEqual(len(alignments.targets), 3)
        self.assertEqual(alignments.targets[0].id, "chr1")
        self.assertEqual(len(alignments.targets[0]), 249250621)
        self.assertEqual(alignments.targets[1].id, "chr2")
        self.assertEqual(len(alignments.targets[1]), 243199373)
        self.assertEqual(alignments.targets[2].id, "chr4")
        self.assertEqual(len(alignments.targets[2]), 191154276)
        self.assertEqual(len(alignments), 3)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 10271783)
        self.assertEqual(alignment.thickEnd, 10271816)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 33))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg18_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 33)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[10271783, 10271816],
                          [       0,       33]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (33 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 33:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 33)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 17)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 53575980)
        self.assertEqual(alignment.thickEnd, 53575997)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 17))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr2")
        self.assertEqual(alignment.query.id, "hg18_dna")
        self.assertEqual(len(alignment.target.seq), 243199373)
        self.assertEqual(len(alignment.query.seq), 33)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[53575980, 53575997],
                          [      25,        8]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (17 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 17:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 17)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 16)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 61646095)
        self.assertEqual(alignment.thickEnd, 61646111)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 16))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr4")
        self.assertEqual(alignment.query.id, "hg18_dna")
        self.assertEqual(len(alignment.target.seq), 191154276)
        self.assertEqual(len(alignment.query.seq), 33)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[61646095, 61646111],
                          [      11,       27]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (16 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 16:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 16)
        self.assertRaises(StopIteration, next, alignments)

    def test_reading_psl_34_004(self):
        """Test parsing psl_34_004.psl.bb."""
        # The bigPsl file psl_34_004.psl.bb was generated using these commands:
        # pslToBigPsl -fa=fasta_34.fa psl_34_004.psl stdout | sort -k1,1 -k2,2n > psl_34_004.bigPslInput
        # bedToBigBed -type=bed12+13 -tab -as=bigPsl.as psl_34_004.bigPslInput hg19.chrom.sizes psl_34_004.psl.bb
        path = "Blat/psl_34_004.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        self.check_psl_34_004(alignments)

    def test_writing_psl_34_004(self):
        """Test writing psl_34_004.psl.bb."""
        path = "Blat/psl_34_004.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        with tempfile.TemporaryFile() as output:
            Align.write(alignments, output, "bigpsl", fa=True)
            output.flush()
            output.seek(0)
            alignments = Align.parse(output, "bigpsl")
            self.check_psl_34_004(alignments)

    def check_psl_34_004(self, alignments):
        self.assertEqual(alignments.declaration, Align.bigpsl.declaration)
        self.assertEqual(len(alignments.targets), 10)
        self.assertEqual(alignments.targets[0].id, "chr1")
        self.assertEqual(len(alignments.targets[0]), 249250621)
        self.assertEqual(alignments.targets[1].id, "chr10")
        self.assertEqual(len(alignments.targets[1]), 135534747)
        self.assertEqual(alignments.targets[2].id, "chr13")
        self.assertEqual(len(alignments.targets[2]), 115169878)
        self.assertEqual(alignments.targets[3].id, "chr18")
        self.assertEqual(len(alignments.targets[3]), 78077248)
        self.assertEqual(alignments.targets[4].id, "chr19")
        self.assertEqual(len(alignments.targets[4]), 59128983)
        self.assertEqual(alignments.targets[5].id, "chr2")
        self.assertEqual(len(alignments.targets[5]), 243199373)
        self.assertEqual(alignments.targets[6].id, "chr22")
        self.assertEqual(len(alignments.targets[6]), 51304566)
        self.assertEqual(alignments.targets[7].id, "chr4")
        self.assertEqual(len(alignments.targets[7]), 191154276)
        self.assertEqual(alignments.targets[8].id, "chr8")
        self.assertEqual(len(alignments.targets[8]), 146364022)
        self.assertEqual(alignments.targets[9].id, "chr9")
        self.assertEqual(len(alignments.targets[9]), 141213431)
        self.assertEqual(len(alignments), 19)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 50)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 1207056)
        self.assertEqual(alignment.thickEnd, 1207106)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 50))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[1207056, 1207106],
                          [      0,      50]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (50 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 50:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 50)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 35)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 39368490)
        self.assertEqual(alignment.thickEnd, 39368526)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[39368490, 39368526],
                          [      49,       13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 31)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 61700837)
        self.assertEqual(alignment.thickEnd, 61700871)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 34))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[61700837, 61700871],
                          [       1,       35]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (34 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 34:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 34)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 220325687)
        self.assertEqual(alignment.thickEnd, 220325721)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 34))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[220325687, 220325721],
                          [       47,        13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (34 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 34:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 34)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 99388555)
        self.assertEqual(alignment.thickEnd, 99388591)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr10")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 135534747)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[99388555, 99388591],
                          [      49,       13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 24)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 112178171)
        self.assertEqual(alignment.thickEnd, 112178196)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 25))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr10")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 135534747)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[112178171, 112178196],
                          [       35,        10]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (25 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 25:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 25)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 44)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 52759147)
        self.assertEqual(alignment.thickEnd, 52759198)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 54))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr13")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 115169878)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[52759147, 52759154, 52759160, 52759160, 52759198],
                          [       1,        8,        8,       11,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (45 aligned letters; 0 identities; 0 mismatches; 9 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 45:
        identities = 0,
        mismatches = 0.
    gaps = 9:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 9:
            internal_insertions = 3:
                open_internal_insertions = 1,
                extend_internal_insertions = 2;
            internal_deletions = 6:
                open_internal_deletions = 1,
                extend_internal_deletions = 5;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 3)
        self.assertEqual(counts.internal_deletions, 6)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 9)
        self.assertEqual(counts.insertions, 3)
        self.assertEqual(counts.deletions, 6)
        self.assertEqual(counts.gaps, 9)
        self.assertEqual(counts.aligned, 45)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 39)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 23891310)
        self.assertEqual(alignment.thickEnd, 23891349)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 39))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr18")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 78077248)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[23891310, 23891349],
                          [      10,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (39 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 39:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 39)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 27)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 43252217)
        self.assertEqual(alignment.thickEnd, 43252245)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 28))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr18")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 78077248)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[43252217, 43252245],
                          [      21,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (28 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 28:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 28)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 36)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 553742)
        self.assertEqual(alignment.thickEnd, 553781)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 39))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr19")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 59128983)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[553742, 553781],
                          [    49,     10]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (39 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 39:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 39)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 34)
        self.assertEqual(alignment.misMatches, 2)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 35483340)
        self.assertEqual(alignment.thickEnd, 35483510)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 170))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr19")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 59128983)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[35483340, 35483365, 35483499, 35483510],
                          [      10,       35,       35,       46]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 134 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 134:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 134:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 134:
                open_internal_deletions = 1,
                extend_internal_deletions = 133;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 134)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 134)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 134)
        self.assertEqual(counts.gaps, 134)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 39)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 54017130)
        self.assertEqual(alignment.thickEnd, 54017169)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 39))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr19")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 59128983)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[54017130, 54017169],
                          [      49,       10]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (39 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 39:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 39)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 35)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 120641740)
        self.assertEqual(alignment.thickEnd, 120641776)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr2")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 243199373)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[120641740, 120641776],
                          [       49,        13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 43)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 183925984)
        self.assertEqual(alignment.thickEnd, 183926028)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 48))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr2")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 243199373)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[183925984, 183925990, 183925990, 183926028],
                          [        1,         7,        11,        49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (44 aligned letters; 0 identities; 0 mismatches; 4 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 44:
        identities = 0,
        mismatches = 0.
    gaps = 4:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 4:
            internal_insertions = 4:
                open_internal_insertions = 1,
                extend_internal_insertions = 3;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 4)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 4)
        self.assertEqual(counts.insertions, 4)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 4)
        self.assertEqual(counts.aligned, 44)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 42144400)
        self.assertEqual(alignment.thickEnd, 42144436)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr22")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 51304566)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[42144400, 42144436],
                          [      11,       47]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 35)
        self.assertEqual(alignment.misMatches, 2)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 48997405)
        self.assertEqual(alignment.thickEnd, 48997442)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 37))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr22")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 51304566)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[48997405, 48997442],
                          [      49,       12]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (37 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 37:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 37)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 28)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 37558157)
        self.assertEqual(alignment.thickEnd, 37558191)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 44))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr4")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 191154276)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[37558157, 37558167, 37558173, 37558173, 37558191],
                          [      49,       39,       39,       29,       11]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (28 aligned letters; 0 identities; 0 mismatches; 16 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 28:
        identities = 0,
        mismatches = 0.
    gaps = 16:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 16:
            internal_insertions = 10:
                open_internal_insertions = 1,
                extend_internal_insertions = 9;
            internal_deletions = 6:
                open_internal_deletions = 1,
                extend_internal_deletions = 5;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 10)
        self.assertEqual(counts.internal_deletions, 6)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 16)
        self.assertEqual(counts.insertions, 10)
        self.assertEqual(counts.deletions, 6)
        self.assertEqual(counts.gaps, 16)
        self.assertEqual(counts.aligned, 28)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 41)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 95160479)
        self.assertEqual(alignment.thickEnd, 95160520)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 41))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr8")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 146364022)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[95160479, 95160520],
                          [       8,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (41 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 41:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 41)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 38)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 85737865)
        self.assertEqual(alignment.thickEnd, 85737906)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 41))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr9")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 141213431)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[85737865, 85737906],
                          [       9,       50]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (41 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 41:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 41)
        self.assertRaises(StopIteration, next, alignments)

    def test_reading_psl_34_005(self):
        """Test parsing psl_34_005.psl.bb."""
        # The bigPsl file psl_34_005.psl.bb was generated using these commands:
        # pslToBigPsl -fa=fasta_34.fa psl_34_005.psl stdout | sort -k1,1 -k2,2n > psl_34_005.bigPslInput
        # bedToBigBed -type=bed12+13 -tab -as=bigPsl.as psl_34_005.bigPslInput hg19.chrom.sizes psl_34_005.psl.bb

        path = "Blat/psl_34_005.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        self.check_psl_34_005(alignments)

    def test_writing_psl_34_005(self):
        """Test writing psl_34_005.psl.bb."""
        path = "Blat/psl_34_005.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        with tempfile.TemporaryFile() as output:
            Align.write(alignments, output, "bigpsl", fa=True)
            output.flush()
            output.seek(0)
            alignments = Align.parse(output, "bigpsl")
            self.check_psl_34_005(alignments)

    def check_psl_34_005(self, alignments):
        self.assertEqual(alignments.declaration, Align.bigpsl.declaration)
        self.assertEqual(len(alignments.targets), 10)
        self.assertEqual(alignments.targets[0].id, "chr1")
        self.assertEqual(len(alignments.targets[0]), 249250621)
        self.assertEqual(alignments.targets[1].id, "chr10")
        self.assertEqual(len(alignments.targets[1]), 135534747)
        self.assertEqual(alignments.targets[2].id, "chr13")
        self.assertEqual(len(alignments.targets[2]), 115169878)
        self.assertEqual(alignments.targets[3].id, "chr18")
        self.assertEqual(len(alignments.targets[3]), 78077248)
        self.assertEqual(alignments.targets[4].id, "chr19")
        self.assertEqual(len(alignments.targets[4]), 59128983)
        self.assertEqual(alignments.targets[5].id, "chr2")
        self.assertEqual(len(alignments.targets[5]), 243199373)
        self.assertEqual(alignments.targets[6].id, "chr22")
        self.assertEqual(len(alignments.targets[6]), 51304566)
        self.assertEqual(alignments.targets[7].id, "chr4")
        self.assertEqual(len(alignments.targets[7]), 191154276)
        self.assertEqual(alignments.targets[8].id, "chr8")
        self.assertEqual(len(alignments.targets[8]), 146364022)
        self.assertEqual(alignments.targets[9].id, "chr9")
        self.assertEqual(len(alignments.targets[9]), 141213431)
        self.assertEqual(len(alignments), 22)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 50)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 1207056)
        self.assertEqual(alignment.thickEnd, 1207106)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 50))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[1207056, 1207106],
                          [      0,      50]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (50 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 50:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 50)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 10271783)
        self.assertEqual(alignment.thickEnd, 10271816)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 33))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg18_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 33)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[10271783, 10271816],
                          [       0,       33]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (33 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 33:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 33)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 35)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 39368490)
        self.assertEqual(alignment.thickEnd, 39368526)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[39368490, 39368526],
                          [      49,       13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 31)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 61700837)
        self.assertEqual(alignment.thickEnd, 61700871)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 34))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[61700837, 61700871],
                          [       1,       35]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (34 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 34:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 34)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 220325687)
        self.assertEqual(alignment.thickEnd, 220325721)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 34))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 249250621)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[220325687, 220325721],
                          [       47,        13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (34 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 34:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 34)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 99388555)
        self.assertEqual(alignment.thickEnd, 99388591)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr10")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 135534747)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[99388555, 99388591],
                          [      49,       13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 24)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 112178171)
        self.assertEqual(alignment.thickEnd, 112178196)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 25))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr10")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 135534747)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[112178171, 112178196],
                          [       35,        10]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (25 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 25:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 25)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 44)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 52759147)
        self.assertEqual(alignment.thickEnd, 52759198)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 54))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr13")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 115169878)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[52759147, 52759154, 52759160, 52759160, 52759198],
                          [       1,        8,        8,       11,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (45 aligned letters; 0 identities; 0 mismatches; 9 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 45:
        identities = 0,
        mismatches = 0.
    gaps = 9:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 9:
            internal_insertions = 3:
                open_internal_insertions = 1,
                extend_internal_insertions = 2;
            internal_deletions = 6:
                open_internal_deletions = 1,
                extend_internal_deletions = 5;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 3)
        self.assertEqual(counts.internal_deletions, 6)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 9)
        self.assertEqual(counts.insertions, 3)
        self.assertEqual(counts.deletions, 6)
        self.assertEqual(counts.gaps, 9)
        self.assertEqual(counts.aligned, 45)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 39)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 23891310)
        self.assertEqual(alignment.thickEnd, 23891349)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 39))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr18")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 78077248)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[23891310, 23891349],
                          [      10,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (39 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 39:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 39)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 27)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 43252217)
        self.assertEqual(alignment.thickEnd, 43252245)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 28))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr18")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 78077248)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[43252217, 43252245],
                          [      21,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (28 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 28:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 28)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 36)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 553742)
        self.assertEqual(alignment.thickEnd, 553781)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 39))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr19")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 59128983)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[553742, 553781],
                          [    49,     10]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (39 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 39:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 39)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 34)
        self.assertEqual(alignment.misMatches, 2)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 35483340)
        self.assertEqual(alignment.thickEnd, 35483510)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 170))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr19")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 59128983)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[35483340, 35483365, 35483499, 35483510],
                          [      10,       35,       35,       46]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 134 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 134:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 134:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 134:
                open_internal_deletions = 1,
                extend_internal_deletions = 133;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 134)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 134)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 134)
        self.assertEqual(counts.gaps, 134)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 39)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 54017130)
        self.assertEqual(alignment.thickEnd, 54017169)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 39))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr19")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 59128983)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[54017130, 54017169],
                          [      49,       10]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (39 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 39:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 39)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 17)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 53575980)
        self.assertEqual(alignment.thickEnd, 53575997)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 17))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr2")
        self.assertEqual(alignment.query.id, "hg18_dna")
        self.assertEqual(len(alignment.target.seq), 243199373)
        self.assertEqual(len(alignment.query.seq), 33)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[53575980, 53575997],
                          [      25,        8]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (17 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 17:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 17)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 35)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 120641740)
        self.assertEqual(alignment.thickEnd, 120641776)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr2")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 243199373)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[120641740, 120641776],
                          [       49,        13]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 43)
        self.assertEqual(alignment.misMatches, 1)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 183925984)
        self.assertEqual(alignment.thickEnd, 183926028)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 48))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr2")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 243199373)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[183925984, 183925990, 183925990, 183926028],
                          [        1,         7,        11,        49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (44 aligned letters; 0 identities; 0 mismatches; 4 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 44:
        identities = 0,
        mismatches = 0.
    gaps = 4:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 4:
            internal_insertions = 4:
                open_internal_insertions = 1,
                extend_internal_insertions = 3;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 4)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 4)
        self.assertEqual(counts.insertions, 4)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 4)
        self.assertEqual(counts.aligned, 44)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 33)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 42144400)
        self.assertEqual(alignment.thickEnd, 42144436)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 36))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr22")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 51304566)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[42144400, 42144436],
                          [      11,       47]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (36 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 36:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 36)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 35)
        self.assertEqual(alignment.misMatches, 2)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 48997405)
        self.assertEqual(alignment.thickEnd, 48997442)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 37))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr22")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 51304566)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[48997405, 48997442],
                          [      49,       12]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (37 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 37:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 37)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 28)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 37558157)
        self.assertEqual(alignment.thickEnd, 37558191)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 44))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertGreater(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr4")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 191154276)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[37558157, 37558167, 37558173, 37558173, 37558191],
                          [      49,       39,       39,       29,       11]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (28 aligned letters; 0 identities; 0 mismatches; 16 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 28:
        identities = 0,
        mismatches = 0.
    gaps = 16:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 16:
            internal_insertions = 10:
                open_internal_insertions = 1,
                extend_internal_insertions = 9;
            internal_deletions = 6:
                open_internal_deletions = 1,
                extend_internal_deletions = 5;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 10)
        self.assertEqual(counts.internal_deletions, 6)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 16)
        self.assertEqual(counts.insertions, 10)
        self.assertEqual(counts.deletions, 6)
        self.assertEqual(counts.gaps, 16)
        self.assertEqual(counts.aligned, 28)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 16)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 61646095)
        self.assertEqual(alignment.thickEnd, 61646111)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 16))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr4")
        self.assertEqual(alignment.query.id, "hg18_dna")
        self.assertEqual(len(alignment.target.seq), 191154276)
        self.assertEqual(len(alignment.query.seq), 33)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[61646095, 61646111],
                          [      11,       27]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (16 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 16:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 16)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 41)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 95160479)
        self.assertEqual(alignment.thickEnd, 95160520)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 41))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr8")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 146364022)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[95160479, 95160520],
                          [       8,       49]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (41 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 41:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 41)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 38)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 85737865)
        self.assertEqual(alignment.thickEnd, 85737906)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertEqual(alignment.shape, (2, 41))
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr9")
        self.assertEqual(alignment.query.id, "hg19_dna")
        self.assertEqual(len(alignment.target.seq), 141213431)
        self.assertEqual(len(alignment.query.seq), 50)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[85737865, 85737906],
                          [       9,       50]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (41 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 41:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 41)
        self.assertRaises(StopIteration, next, alignments)


class TestAlign_dnax_prot(unittest.TestCase):
    queries = {
        record.id: record.seq
        for record in SeqIO.parse("Blat/CAG33136.1.fasta", "fasta")
    }

    def test_reading_psl_35_001(self):
        """Test parsing psl_35_001.psl.bb."""
        # The bigPsl file psl_35_001.psl.bb was generated using these commands:
        # pslToBigPsl -fa=CAG33136.1.fasta psl_35_001.psl stdout | sort -k1,1 -k2,2n > psl_35_001.bigPslInput
        # bedToBigBed -type=bed12+13 -tab -as=bigPsl.as psl_35_001.bigPslInput hg38.chrom.sizes psl_35_001.psl.bb

        path = "Blat/psl_35_001.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        self.check_psl_35_001(alignments)

    def test_writing_psl_35_001(self):
        """Test writing psl_35_001.psl.bb."""
        path = "Blat/psl_35_001.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        with tempfile.TemporaryFile() as output:
            Align.write(alignments, output, "bigpsl", fa=True)
            output.flush()
            output.seek(0)
            alignments = Align.parse(output, "bigpsl")
            self.check_psl_35_001(alignments)

    def check_psl_35_001(self, alignments):
        self.assertEqual(alignments.declaration, Align.bigpsl.declaration)
        self.assertEqual(len(alignments.targets), 2)
        self.assertEqual(alignments.targets[0].id, "chr13")
        self.assertEqual(len(alignments.targets[0]), 114364328)
        self.assertEqual(alignments.targets[1].id, "chr4")
        self.assertEqual(len(alignments.targets[1]), 190214555)
        self.assertEqual(len(alignments), 8)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 44)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 75549820)
        self.assertEqual(alignment.thickEnd, 75567312)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr13")
        self.assertEqual(alignment.query.id, "CAG33136.1")
        self.assertEqual(len(alignment.target.seq), 114364328)
        self.assertEqual(len(alignment.query.seq), 230)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[75549820, 75549865, 75567225, 75567225, 75567312],
                          [       0,       15,       15,      113,      142]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (132 aligned letters; 0 identities; 0 mismatches; 17458 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 132:
        identities = 0,
        mismatches = 0.
    gaps = 17458:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 17458:
            internal_insertions = 98:
                open_internal_insertions = 1,
                extend_internal_insertions = 97;
            internal_deletions = 17360:
                open_internal_deletions = 1,
                extend_internal_deletions = 17359;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 98)
        self.assertEqual(counts.internal_deletions, 17360)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 17458)
        self.assertEqual(counts.insertions, 98)
        self.assertEqual(counts.deletions, 17360)
        self.assertEqual(counts.gaps, 17458)
        self.assertEqual(counts.aligned, 132)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 44)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 75560749)
        self.assertEqual(alignment.thickEnd, 75560881)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr13")
        self.assertEqual(alignment.query.id, "CAG33136.1")
        self.assertEqual(len(alignment.target.seq), 114364328)
        self.assertEqual(len(alignment.query.seq), 230)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[75560749, 75560881],
                          [      17,       61]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (132 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 132:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 132)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 52)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 75566694)
        self.assertEqual(alignment.thickEnd, 75566850)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr13")
        self.assertEqual(alignment.query.id, "CAG33136.1")
        self.assertEqual(len(alignment.target.seq), 114364328)
        self.assertEqual(len(alignment.query.seq), 230)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[75566694, 75566850],
                          [      61,      113]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (156 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 156:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 156)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 16)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 75569459)
        self.assertEqual(alignment.thickEnd, 75569507)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr13")
        self.assertEqual(alignment.query.id, "CAG33136.1")
        self.assertEqual(len(alignment.target.seq), 114364328)
        self.assertEqual(len(alignment.query.seq), 230)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[75569459, 75569507],
                          [     142,      158]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (48 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 48:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 48)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 25)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 75594914)
        self.assertEqual(alignment.thickEnd, 75594989)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr13")
        self.assertEqual(alignment.query.id, "CAG33136.1")
        self.assertEqual(len(alignment.target.seq), 114364328)
        self.assertEqual(len(alignment.query.seq), 230)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[75594914, 75594989],
                          [     158,      183]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (75 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 75:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 75)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 47)
        self.assertEqual(alignment.misMatches, 0)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 75604767)
        self.assertEqual(alignment.thickEnd, 75605809)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr13")
        self.assertEqual(alignment.query.id, "CAG33136.1")
        self.assertEqual(len(alignment.target.seq), 114364328)
        self.assertEqual(len(alignment.query.seq), 230)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[75604767, 75604827, 75605728, 75605809],
                          [     183,      203,      203,      230]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (141 aligned letters; 0 identities; 0 mismatches; 901 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 141:
        identities = 0,
        mismatches = 0.
    gaps = 901:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 901:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 901:
                open_internal_deletions = 1,
                extend_internal_deletions = 900;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 901)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 901)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 901)
        self.assertEqual(counts.gaps, 901)
        self.assertEqual(counts.aligned, 141)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 37)
        self.assertEqual(alignment.misMatches, 26)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 41257605)
        self.assertEqual(alignment.thickEnd, 41263290)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr4")
        self.assertEqual(alignment.query.id, "CAG33136.1")
        self.assertEqual(len(alignment.target.seq), 190214555)
        self.assertEqual(len(alignment.query.seq), 230)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[41257605, 41257731, 41263227, 41263227, 41263290],
                          [      17,       59,       59,      162,      183]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (189 aligned letters; 0 identities; 0 mismatches; 5599 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 189:
        identities = 0,
        mismatches = 0.
    gaps = 5599:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 5599:
            internal_insertions = 103:
                open_internal_insertions = 1,
                extend_internal_insertions = 102;
            internal_deletions = 5496:
                open_internal_deletions = 1,
                extend_internal_deletions = 5495;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 103)
        self.assertEqual(counts.internal_deletions, 5496)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 5599)
        self.assertEqual(counts.insertions, 103)
        self.assertEqual(counts.deletions, 5496)
        self.assertEqual(counts.gaps, 5599)
        self.assertEqual(counts.aligned, 189)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 26)
        self.assertEqual(alignment.misMatches, 8)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 41260685)
        self.assertEqual(alignment.thickEnd, 41260787)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr4")
        self.assertEqual(alignment.query.id, "CAG33136.1")
        self.assertEqual(len(alignment.target.seq), 190214555)
        self.assertEqual(len(alignment.query.seq), 230)
        self.assertEqual(alignment.query.seq, self.queries[alignment.query.id])
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[41260685, 41260787],
                          [      76,      110]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (102 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 102:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 102)
        self.assertRaises(StopIteration, next, alignments)

    def check_psl_35_002(self, alignments):
        self.assertEqual(alignments.declaration, Align.bigpsl.declaration)
        self.assertEqual(len(alignments.targets), 2)
        self.assertEqual(alignments.targets[0].id, "KI537194")
        self.assertEqual(len(alignments.targets[0]), 37111980)
        self.assertEqual(alignments.targets[1].id, "KI537979")
        self.assertEqual(len(alignments.targets[1]), 14052872)
        self.assertEqual(len(alignments), 2)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 204)
        self.assertEqual(alignment.misMatches, 6)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 20872390)
        self.assertEqual(alignment.thickEnd, 20873021)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertGreater(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "KI537194")
        self.assertEqual(alignment.query.id, "CAG33136.1")
        self.assertEqual(len(alignment.target.seq), 37111980)
        self.assertEqual(len(alignment.query.seq), 230)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[20873021, 20872472, 20872471, 20872471, 20872390],
                          [       0,      183,      183,      203,      230]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (630 aligned letters; 0 identities; 0 mismatches; 21 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 630:
        identities = 0,
        mismatches = 0.
    gaps = 21:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 21:
            internal_insertions = 20:
                open_internal_insertions = 1,
                extend_internal_insertions = 19;
            internal_deletions = 1:
                open_internal_deletions = 1,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 20)
        self.assertEqual(counts.internal_deletions, 1)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 21)
        self.assertEqual(counts.insertions, 20)
        self.assertEqual(counts.deletions, 1)
        self.assertEqual(counts.gaps, 21)
        self.assertEqual(counts.aligned, 630)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 210)
        self.assertEqual(alignment.misMatches, 3)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 9712654)
        self.assertEqual(alignment.thickEnd, 9744592)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "KI537979")
        self.assertEqual(alignment.query.id, "CAG33136.1")
        self.assertEqual(len(alignment.target.seq), 14052872)
        self.assertEqual(len(alignment.query.seq), 230)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[9712654, 9712786, 9715941, 9716097, 9716445, 9716532,
                           9718374, 9718422, 9739264, 9739339, 9743706, 9743766,
                           9744511, 9744592],
                          [     17,      61,      61,     113,     113,     142,
                               142,     158,     158,     183,     183,     203,
                               203,     230]]),
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (639 aligned letters; 0 identities; 0 mismatches; 31299 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 639:
        identities = 0,
        mismatches = 0.
    gaps = 31299:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 31299:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 31299:
                open_internal_deletions = 6,
                extend_internal_deletions = 31293;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 31299)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 31299)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 31299)
        self.assertEqual(counts.gaps, 31299)
        self.assertEqual(counts.aligned, 639)
        self.assertRaises(StopIteration, next, alignments)

    def test_reading_psl_35_002(self):
        """Test parsing psl_35_002.psl.bb."""
        # The bigPsl file psl_35_002.psl.bb was generated using these commands:
        # pslToBigPsl -fa=CAG33136.1.fasta psl_35_002.psl stdout | grep -v KI538594 | sort -k1,1 -k2,2n > psl_35_002.bigPslInput
        # (where we excluded KI538594 because its alignment has a negative gap)
        # bedToBigBed -type=bed12+13 -tab -as=bigPsl.as psl_35_002.bigPslInput balAcu1.chrom.sizes psl_35_002.psl.bb

        # See below for a description of the file balAcu1.fa.
        # We use this file here so we can check the SeqFeatures.
        records = SeqIO.parse("Blat/balAcu1.fa", "fasta")
        self.dna = {}
        for record in records:
            name, start_end = record.id.split(":")
            start, end = start_end.split("-")
            start = int(start)
            end = int(end)
            sequence = str(record.seq)
            self.dna[name] = Seq({start: sequence}, length=end)
        path = "Blat/psl_35_002.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        self.check_psl_35_002(alignments)

    def test_writing_psl_35_002(self):
        """Test writing psl_35_002.psl.bb."""
        path = "Blat/psl_35_002.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        with tempfile.TemporaryFile() as output:
            Align.write(alignments, output, "bigpsl", fa=True)
            output.flush()
            output.seek(0)
            alignments = Align.parse(output, "bigpsl")
            self.check_psl_35_002(alignments)


class TestAlign_bigpsl(unittest.TestCase):
    # The bigPsl file bigPsl.bb was generated from the UCSC example files using these commands:
    # pslToBigPsl bigPsl.psl -cds=bigPsl.cds stdout | sort -k1,1 -k2,2n > bigPsl.txt
    # bedToBigBed -as=bigPsl.as -type=bed12+13 -tab bigPsl.txt hg38.chrom.sizes bigPsl.bb
    # (see https://genome.ucsc.edu/goldenPath/help/bigPsl.html)

    def test_reading(self):
        """Test parsing bigPsl.bb."""
        path = "Blat/bigPsl.bb"
        alignments = Align.parse(path, "bigpsl")
        self.check_alignments(alignments)

    def test_writing(self):
        """Test writing bigPsl.bb."""
        path = "Blat/bigPsl.bb"
        alignments = Align.parse(path, "bigpsl")
        with tempfile.TemporaryFile() as output:
            Align.write(alignments, output, "bigpsl", cds=True)
            output.flush()
            output.seek(0)
            alignments = Align.parse(output, "bigpsl")
            self.check_alignments(alignments)

    def check_alignments(self, alignments):
        self.assertEqual(alignments.declaration, Align.bigpsl.declaration)
        self.assertEqual(len(alignments.targets), 1)
        self.assertEqual(alignments.targets[0].id, "chr1")
        self.assertEqual(len(alignments.targets[0]), 248956422)
        self.assertEqual(len(alignments), 100)
        alignment = next(alignments)
        self.assertEqual(alignment.matches, 1579)
        self.assertEqual(alignment.misMatches, 25)
        self.assertEqual(alignment.repMatches, 0)
        self.assertEqual(alignment.nCount, 0)
        self.assertEqual(alignment.score, 1000)
        self.assertEqual(alignment.thickStart, 12622)
        self.assertEqual(alignment.thickEnd, 13259)
        self.assertEqual(alignment.itemRgb, "0")
        self.assertLess(alignment.coordinates[0, 0], alignment.coordinates[0, -1])
        self.assertLess(alignment.coordinates[1, 0], alignment.coordinates[1, -1])
        self.assertEqual(len(alignment), 2)
        self.assertIs(alignment.sequences[0], alignment.target)
        self.assertIs(alignment.sequences[1], alignment.query)
        self.assertEqual(alignment.target.id, "chr1")
        self.assertEqual(alignment.query.id, "mAM992877")
        self.assertEqual(len(alignment.target.seq), 248956422)
        self.assertEqual(len(alignment.query.seq), 1604)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[11873, 12227, 12612, 12721, 13220, 14361],
                          [    0,   354,   354,   463,   463,  1604]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1604 aligned letters; 0 identities; 0 mismatches; 884 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1604:
        identities = 0,
        mismatches = 0.
    gaps = 884:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 884:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 884:
                open_internal_deletions = 2,
                extend_internal_deletions = 882;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 884)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 884)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 884)
        self.assertEqual(counts.gaps, 884)
        self.assertEqual(counts.aligned, 1604)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAM992881")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(ExactPosition(382), ExactPosition(718), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[11873, 12227, 12594, 12721, 13402, 14361],
                              [0,   354,   354,   481,   481,  1440]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1440 aligned letters; 0 identities; 0 mismatches; 1048 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1440:
        identities = 0,
        mismatches = 0.
    gaps = 1048:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 1048:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 1048:
                open_internal_deletions = 2,
                extend_internal_deletions = 1046;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 1048)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 1048)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 1048)
        self.assertEqual(counts.gaps, 1048)
        self.assertEqual(counts.aligned, 1440)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAM992878")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(ExactPosition(733), ExactPosition(1003), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[11873, 12227, 12645, 12697, 13220, 13656, 13658,
                           13957, 13958, 14362],
                          [    0,   354,   354,   406,   406,   842,   842,
                            1141,  1141,  1545]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1545 aligned letters; 0 identities; 0 mismatches; 944 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1545:
        identities = 0,
        mismatches = 0.
    gaps = 944:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 944:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 944:
                open_internal_deletions = 4,
                extend_internal_deletions = 940;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 944)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 944)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 944)
        self.assertEqual(counts.gaps, 944)
        self.assertEqual(counts.aligned, 1545)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAM992879")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(ExactPosition(364), ExactPosition(502), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[11873, 12227, 12612, 12721, 13220, 14362],
                          [    0,   354,   354,   463,   463,  1605]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1605 aligned letters; 0 identities; 0 mismatches; 884 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1605:
        identities = 0,
        mismatches = 0.
    gaps = 884:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 884:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 884:
                open_internal_deletions = 2,
                extend_internal_deletions = 882;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 884)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 884)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 884)
        self.assertEqual(counts.gaps, 884)
        self.assertEqual(counts.aligned, 1605)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAM992871")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(ExactPosition(1401), ExactPosition(1632), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[11873, 12227, 12612, 12721, 13220, 14409],
                          [    0,   354,   354,   463,   463,  1652]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1652 aligned letters; 0 identities; 0 mismatches; 884 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1652:
        identities = 0,
        mismatches = 0.
    gaps = 884:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 884:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 884:
                open_internal_deletions = 2,
                extend_internal_deletions = 882;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 884)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 884)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 884)
        self.assertEqual(counts.gaps, 884)
        self.assertEqual(counts.aligned, 1652)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAM992872")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(ExactPosition(1401), ExactPosition(1632), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[11873, 12227, 12612, 12721, 13220, 14409],
                          [    0,   354,   354,   463,   463,  1652]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1652 aligned letters; 0 identities; 0 mismatches; 884 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1652:
        identities = 0,
        mismatches = 0.
    gaps = 884:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 884:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 884:
                open_internal_deletions = 2,
                extend_internal_deletions = 882;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 884)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 884)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 884)
        self.assertEqual(counts.gaps, 884)
        self.assertEqual(counts.aligned, 1652)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAM992875")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(ExactPosition(1401), ExactPosition(1632), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[11873, 12227, 12612, 12721, 13220, 14409],
                          [    0,   354,   354,   463,   463,  1652]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1652 aligned letters; 0 identities; 0 mismatches; 884 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1652:
        identities = 0,
        mismatches = 0.
    gaps = 884:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 884:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 884:
                open_internal_deletions = 2,
                extend_internal_deletions = 882;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 884)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 884)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 884)
        self.assertEqual(counts.gaps, 884)
        self.assertEqual(counts.aligned, 1652)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAM992880")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(ExactPosition(316), ExactPosition(718), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[11873, 12227, 12594, 12721, 13402, 14409],
                          [    0,   354,   354,   481,   481,  1488]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1488 aligned letters; 0 identities; 0 mismatches; 1048 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1488:
        identities = 0,
        mismatches = 0.
    gaps = 1048:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 1048:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 1048:
                open_internal_deletions = 2,
                extend_internal_deletions = 1046;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 1048)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 1048)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 1048)
        self.assertEqual(counts.gaps, 1048)
        self.assertEqual(counts.aligned, 1488)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mBC032353")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[11873, 12227, 12612, 12721, 13220, 13957, 13958,
                           14258, 14270, 14409],
                          [    0,   354,   354,   463,   463,  1200,  1200,
                            1500,  1500,  1639]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1639 aligned letters; 0 identities; 0 mismatches; 897 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1639:
        identities = 0,
        mismatches = 0.
    gaps = 897:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 897:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 897:
                open_internal_deletions = 4,
                extend_internal_deletions = 893;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 897)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 897)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 897)
        self.assertEqual(counts.gaps, 897)
        self.assertEqual(counts.aligned, 1639)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAM992873")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(BeforePosition(436), ExactPosition(706), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[12612, 12721, 13220, 13656, 13658, 13957, 13958, 14362],
                          [    0,   109,   109,   545,   545,   844,   844,  1248]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1248 aligned letters; 0 identities; 0 mismatches; 502 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1248:
        identities = 0,
        mismatches = 0.
    gaps = 502:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 502:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 502:
                open_internal_deletions = 3,
                extend_internal_deletions = 499;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 502)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 502)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 502)
        self.assertEqual(counts.gaps, 502)
        self.assertEqual(counts.aligned, 1248)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD190877")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[12993, 13016], [0, 23]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (23 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 23:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 23)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD167845")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[13001, 13024], [0, 23]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (23 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 23:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 23)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD469098")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[13003, 13024], [2, 23]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (21 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 21:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 21)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD485136")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[13087, 13107], [0, 20]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (20 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 20:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 20)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mBC070227")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[13420, 13957, 13958, 14259, 14271, 14407],
                          [    0,   537,   537,   838,   838,   974]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (974 aligned letters; 0 identities; 0 mismatches; 13 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 974:
        identities = 0,
        mismatches = 0.
    gaps = 13:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 13:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 13:
                open_internal_deletions = 2,
                extend_internal_deletions = 11;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 13)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 13)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 13)
        self.assertEqual(counts.gaps, 13)
        self.assertEqual(counts.aligned, 974)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD282506")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[13721, 13745], [0, 24]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (24 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 24:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 24)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD192765")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[13877, 13909], [0, 32]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD191631")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[13932, 13964], [0, 32]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD135207")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[13939, 13971], [0, 32]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD157229")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14002, 14023], [0, 21]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (21 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 21:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 21)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD199172")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14241, 14265], [0, 24]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (24 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 24:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 24)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD422311")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14246, 14278], [0, 32]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD108953")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14322, 14354], [0, 32]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD227419")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14378, 14407], [1, 30]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (29 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 29:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 29)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mBC063555")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14404, 14455, 14455, 14829, 14969, 15038, 15795,
                           15905, 15906, 15906, 15947, 16606, 16765, 16857,
                           17055, 17232, 17742, 17914, 18061, 18267, 18369,
                           18500, 18554, 18912, 19236],
                          [ 2146,  2095,  2090,  1716,  1716,  1647,  1647,
                            1537,  1537,  1535,  1494,  1494,  1335,  1335,
                            1137,  1137,   627,   627,   480,   480,   378,
                             378,   324,   324,     0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (2139 aligned letters; 0 identities; 0 mismatches; 2700 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 2139:
        identities = 0,
        mismatches = 0.
    gaps = 2700:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 2700:
            internal_insertions = 7:
                open_internal_insertions = 2,
                extend_internal_insertions = 5;
            internal_deletions = 2693:
                open_internal_deletions = 10,
                extend_internal_deletions = 2683;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 7)
        self.assertEqual(counts.internal_deletions, 2693)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 2700)
        self.assertEqual(counts.insertions, 7)
        self.assertEqual(counts.deletions, 2693)
        self.assertEqual(counts.gaps, 2700)
        self.assertEqual(counts.aligned, 2139)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mBC063893")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14404, 14511, 14513, 14829, 14969, 15038, 15795,
                           15903, 15903, 15947, 16606, 16765, 16857, 17055,
                           17232, 17358, 17361, 17742, 17914, 18061, 18267,
                           18366, 18912, 19720],
                          [ 2563,  2456,  2456,  2140,  2140,  2071,  2071,
                            1963,  1962,  1918,  1918,  1759,  1759,  1561,
                            1561,  1435,  1435,  1054,  1054,   907,   907,
                             808,   808,     0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (2562 aligned letters; 0 identities; 0 mismatches; 2755 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 2562:
        identities = 0,
        mismatches = 0.
    gaps = 2755:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 2755:
            internal_insertions = 1:
                open_internal_insertions = 1,
                extend_internal_insertions = 0;
            internal_deletions = 2754:
                open_internal_deletions = 10,
                extend_internal_deletions = 2744;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 1)
        self.assertEqual(counts.internal_deletions, 2754)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 2755)
        self.assertEqual(counts.insertions, 1)
        self.assertEqual(counts.deletions, 2754)
        self.assertEqual(counts.gaps, 2755)
        self.assertEqual(counts.aligned, 2562)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mBC053987")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14404, 14455, 14455, 14829, 14969, 15038, 15795,
                           15905, 15906, 15906, 15947, 16606, 16765, 16857,
                           17055, 17232, 17368, 17605, 17742, 17914, 18061,
                           18267, 18366, 18912, 19763],
                          [ 2379,  2328,  2323,  1949,  1949,  1880,  1880,
                            1770,  1770,  1768,  1727,  1727,  1568,  1568,
                            1370,  1370,  1234,  1234,  1097,  1097,   950,
                             950,   851,   851,     0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (2372 aligned letters; 0 identities; 0 mismatches; 2994 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 2372:
        identities = 0,
        mismatches = 0.
    gaps = 2994:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 2994:
            internal_insertions = 7:
                open_internal_insertions = 2,
                extend_internal_insertions = 5;
            internal_deletions = 2987:
                open_internal_deletions = 10,
                extend_internal_deletions = 2977;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 7)
        self.assertEqual(counts.internal_deletions, 2987)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 2994)
        self.assertEqual(counts.insertions, 7)
        self.assertEqual(counts.deletions, 2987)
        self.assertEqual(counts.gaps, 2994)
        self.assertEqual(counts.aligned, 2372)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAL137714")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                CompoundLocation(
                    [
                        SimpleLocation(
                            ExactPosition(168), ExactPosition(318), strand=1
                        ),
                        SimpleLocation(
                            ExactPosition(311), ExactPosition(704), strand=1
                        ),
                        SimpleLocation(
                            ExactPosition(940), ExactPosition(1273), strand=1
                        ),
                        SimpleLocation(
                            ExactPosition(3005), ExactPosition(3209), strand=1
                        ),
                    ],
                    "join",
                ),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[ 14404,  14511,  14513,  14829,  14969,  15250, 185765,
                           186064, 186064, 186623, 186626, 187287, 187379, 187577,
                           187754, 188266, 188438, 188485, 188485, 188584, 188790,
                           188889, 195262, 195416, 199836, 199999],
                          [  3498,   3391,   3391,   3075,   3075,   2794,   2794,
                             2495,   2493,   1934,   1934,   1273,   1273,   1075,
                             1075,    563,    563,    516,    515,    416,    416,
                              317,    317,    163,    163,      0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (3495 aligned letters; 0 identities; 0 mismatches; 182103 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 3495:
        identities = 0,
        mismatches = 0.
    gaps = 182103:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 182103:
            internal_insertions = 3:
                open_internal_insertions = 2,
                extend_internal_insertions = 1;
            internal_deletions = 182100:
                open_internal_deletions = 10,
                extend_internal_deletions = 182090;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 3)
        self.assertEqual(counts.internal_deletions, 182100)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 182103)
        self.assertEqual(counts.insertions, 3)
        self.assertEqual(counts.deletions, 182100)
        self.assertEqual(counts.gaps, 182103)
        self.assertEqual(counts.aligned, 3495)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mBC048328")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14404, 14455, 14455, 14829, 14969, 15038, 15795, 15905,
                           15906, 15906, 15947, 16606, 16722, 16722, 16768, 16856,
                           17055, 17232, 17368, 17605, 17742, 17914, 18061, 18267,
                           18379, 24737, 24891],
                          [ 1720,  1669,  1664,  1290,  1290,  1221,  1221,  1111,
                            1111,  1109,  1068,  1068,   952,   943,   897,   897,
                             698,   698,   562,   562,   425,   425,   278,   278,
                             166,   166,    12]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1692 aligned letters; 0 identities; 0 mismatches; 8811 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1692:
        identities = 0,
        mismatches = 0.
    gaps = 8811:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 8811:
            internal_insertions = 16:
                open_internal_insertions = 3,
                extend_internal_insertions = 13;
            internal_deletions = 8795:
                open_internal_deletions = 10,
                extend_internal_deletions = 8785;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 16)
        self.assertEqual(counts.internal_deletions, 8795)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 8811)
        self.assertEqual(counts.insertions, 16)
        self.assertEqual(counts.deletions, 8795)
        self.assertEqual(counts.gaps, 8811)
        self.assertEqual(counts.aligned, 1692)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mBC063470")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14404, 14455, 14455, 14829, 15795, 15905, 15906,
                           15906, 15947, 16606, 16765, 16857, 17055, 17605,
                           18061, 24737, 24891, 29320, 29346],
                          [ 1576,  1525,  1520,  1146,  1146,  1036,  1036,
                            1034,   993,   993,   834,   834,   636,   636,
                             180,   180,    26,    26,     0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1569 aligned letters; 0 identities; 0 mismatches; 13380 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1569:
        identities = 0,
        mismatches = 0.
    gaps = 13380:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 13380:
            internal_insertions = 7:
                open_internal_insertions = 2,
                extend_internal_insertions = 5;
            internal_deletions = 13373:
                open_internal_deletions = 7,
                extend_internal_deletions = 13366;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 7)
        self.assertEqual(counts.internal_deletions, 13373)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 13380)
        self.assertEqual(counts.insertions, 7)
        self.assertEqual(counts.deletions, 13373)
        self.assertEqual(counts.gaps, 13380)
        self.assertEqual(counts.aligned, 1569)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mBX537637")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                CompoundLocation(
                    [
                        SimpleLocation(
                            ExactPosition(240), ExactPosition(432), strand=1
                        ),
                        SimpleLocation(
                            ExactPosition(431), ExactPosition(1166), strand=1
                        ),
                        SimpleLocation(
                            ExactPosition(1165), ExactPosition(1591), strand=1
                        ),
                    ],
                    "join",
                ),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14404, 14495, 14559, 14571, 15004, 15038, 15795, 15903,
                           15903, 15947, 16606, 16765, 16857, 17055, 17232, 17368,
                           17605, 17742, 17914, 18061, 18267, 18366, 24737, 24891,
                           29533, 29809],
                          [ 1597,  1506,  1506,  1494,  1494,  1460,  1460,  1352,
                            1351,  1307,  1307,  1148,  1148,   950,   950,   814,
                             814,   677,   677,   530,   530,   431,   431,   277,
                             277,     1]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1595 aligned letters; 0 identities; 0 mismatches; 13811 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1595:
        identities = 0,
        mismatches = 0.
    gaps = 13811:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 13811:
            internal_insertions = 1:
                open_internal_insertions = 1,
                extend_internal_insertions = 0;
            internal_deletions = 13810:
                open_internal_deletions = 11,
                extend_internal_deletions = 13799;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 1)
        self.assertEqual(counts.internal_deletions, 13810)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 13811)
        self.assertEqual(counts.insertions, 1)
        self.assertEqual(counts.deletions, 13810)
        self.assertEqual(counts.gaps, 13811)
        self.assertEqual(counts.aligned, 1595)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAK024481")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(BeforePosition(1345), ExactPosition(1897), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14406, 15905, 15906, 15906, 16765, 16857, 18733],
                          [ 4236,  2737,  2737,  2735,  1876,  1876,     0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (4234 aligned letters; 0 identities; 0 mismatches; 95 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 4234:
        identities = 0,
        mismatches = 0.
    gaps = 95:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 95:
            internal_insertions = 2:
                open_internal_insertions = 1,
                extend_internal_insertions = 1;
            internal_deletions = 93:
                open_internal_deletions = 2,
                extend_internal_deletions = 91;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 2)
        self.assertEqual(counts.internal_deletions, 93)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 95)
        self.assertEqual(counts.insertions, 2)
        self.assertEqual(counts.deletions, 93)
        self.assertEqual(counts.gaps, 95)
        self.assertEqual(counts.aligned, 4234)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAK057951")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[ 14406,  14829,  14969,  15038,  15795,  15903,  15903,
                            15947,  16606,  16768,  16856,  17055,  17232,  17368,
                            17605,  17745,  18036,  18061,  18267,  18366,  24737,
                            24893, 188471, 188485, 188485, 188584, 188790, 188889,
                           195262, 195416, 199836, 199861],
                          [  1954,   1531,   1531,   1462,   1462,   1354,   1353,
                             1309,   1309,   1147,   1147,    948,    948,    812,
                              812,    672,    672,    647,    647,    548,    548,
                              392,    392,    378,    377,    278,    278,    179,
                              179,     25,     25,      0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1952 aligned letters; 0 identities; 0 mismatches; 183505 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1952:
        identities = 0,
        mismatches = 0.
    gaps = 183505:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 183505:
            internal_insertions = 2:
                open_internal_insertions = 2,
                extend_internal_insertions = 0;
            internal_deletions = 183503:
                open_internal_deletions = 13,
                extend_internal_deletions = 183490;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 2)
        self.assertEqual(counts.internal_deletions, 183503)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 183505)
        self.assertEqual(counts.insertions, 2)
        self.assertEqual(counts.deletions, 183503)
        self.assertEqual(counts.gaps, 183505)
        self.assertEqual(counts.aligned, 1952)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAK092583")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(ExactPosition(72), ExactPosition(555), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14406, 14455, 14455, 15905, 15906, 15906, 16765,
                           16857, 17055, 17232, 17368, 17605, 17742, 17914,
                           18061, 24737, 24891, 29320, 29344],
                          [ 3161,  3112,  3107,  1657,  1657,  1655,   796,
                             796,   598,   598,   462,   462,   325,   325,
                             178,   178,    24,    24,     0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (3154 aligned letters; 0 identities; 0 mismatches; 11791 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 3154:
        identities = 0,
        mismatches = 0.
    gaps = 11791:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 11791:
            internal_insertions = 7:
                open_internal_insertions = 2,
                extend_internal_insertions = 5;
            internal_deletions = 11784:
                open_internal_deletions = 7,
                extend_internal_deletions = 11777;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 7)
        self.assertEqual(counts.internal_deletions, 11784)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 11791)
        self.assertEqual(counts.insertions, 7)
        self.assertEqual(counts.deletions, 11784)
        self.assertEqual(counts.gaps, 11791)
        self.assertEqual(counts.aligned, 3154)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAX747611")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14406, 14455, 14455, 15905, 15906, 15906, 16765,
                           16857, 17055, 17232, 17368, 17605, 17742, 17914,
                           18061, 24737, 24891, 29320, 29344],
                          [ 3161,  3112,  3107,  1657,  1657,  1655,   796,
                             796,   598,   598,   462,   462,   325,   325,
                             178,   178,    24,    24,     0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (3154 aligned letters; 0 identities; 0 mismatches; 11791 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 3154:
        identities = 0,
        mismatches = 0.
    gaps = 11791:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 11791:
            internal_insertions = 7:
                open_internal_insertions = 2,
                extend_internal_insertions = 5;
            internal_deletions = 11784:
                open_internal_deletions = 7,
                extend_internal_deletions = 11777;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 7)
        self.assertEqual(counts.internal_deletions, 11784)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 11791)
        self.assertEqual(counts.insertions, 7)
        self.assertEqual(counts.deletions, 11784)
        self.assertEqual(counts.gaps, 11791)
        self.assertEqual(counts.aligned, 3154)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAK056232")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14406, 14455, 14455, 14829, 14969, 15038, 15795,
                           15905, 15906, 15906, 15947, 16606, 16768, 16856,
                           17055, 17232, 17368, 17605, 17742, 17914, 18061,
                           18267, 18366, 24737, 24891, 29320, 29902, 29912,
                           30000],
                          [ 2354,  2305,  2300,  1926,  1926,  1857,  1857,
                            1747,  1747,  1745,  1704,  1704,  1542,  1542,
                            1343,  1343,  1207,  1207,  1070,  1070,   923,
                            923,    824,   824,   670,   670,    88,    88,
                            0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (2347 aligned letters; 0 identities; 0 mismatches; 13254 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 2347:
        identities = 0,
        mismatches = 0.
    gaps = 13254:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 13254:
            internal_insertions = 7:
                open_internal_insertions = 2,
                extend_internal_insertions = 5;
            internal_deletions = 13247:
                open_internal_deletions = 12,
                extend_internal_deletions = 13235;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 7)
        self.assertEqual(counts.internal_deletions, 13247)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 13254)
        self.assertEqual(counts.insertions, 7)
        self.assertEqual(counts.deletions, 13247)
        self.assertEqual(counts.gaps, 13254)
        self.assertEqual(counts.aligned, 2347)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mBC094698")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14407, 14455, 14455, 14829, 14969, 15038, 15795,
                           15905, 15906, 15906, 15947, 16606, 16765, 16857,
                           17055, 17232, 17742, 17914, 18061, 18267, 19108],
                          [ 2504,  2456,  2451,  2077,  2077,  2008,  2008,
                            1898,  1898,  1896,  1855,  1855,  1696,  1696,
                            1498,  1498,   988,   988,   841,   841,     0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (2497 aligned letters; 0 identities; 0 mismatches; 2211 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 2497:
        identities = 0,
        mismatches = 0.
    gaps = 2211:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 2211:
            internal_insertions = 7:
                open_internal_insertions = 2,
                extend_internal_insertions = 5;
            internal_deletions = 2204:
                open_internal_deletions = 8,
                extend_internal_deletions = 2196;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 7)
        self.assertEqual(counts.internal_deletions, 2204)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 2211)
        self.assertEqual(counts.insertions, 7)
        self.assertEqual(counts.deletions, 2204)
        self.assertEqual(counts.gaps, 2211)
        self.assertEqual(counts.aligned, 2497)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mBC041177")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14407, 14455, 14455, 14829, 14969, 15038, 15795,
                           15905, 15906, 15906, 15947, 16606, 16722, 16731,
                           16768, 16856, 17055, 17232, 17368, 17605, 17742,
                           17914, 18061, 18267, 18379, 18912, 19190, 19191,
                           19716],
                          [ 2336,  2288,  2283,  1909,  1909,  1840,  1840,
                            1730,  1730,  1728,  1687,  1687,  1571,  1571,
                            1534,  1534,  1335,  1335,  1199,  1199,  1062,
                            1062,   915,   915,   803,   803,   525,   525,
                               0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (2329 aligned letters; 0 identities; 0 mismatches; 2987 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 2329:
        identities = 0,
        mismatches = 0.
    gaps = 2987:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 2987:
            internal_insertions = 7:
                open_internal_insertions = 2,
                extend_internal_insertions = 5;
            internal_deletions = 2980:
                open_internal_deletions = 12,
                extend_internal_deletions = 2968;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 7)
        self.assertEqual(counts.internal_deletions, 2980)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 2987)
        self.assertEqual(counts.insertions, 7)
        self.assertEqual(counts.deletions, 2980)
        self.assertEqual(counts.gaps, 2987)
        self.assertEqual(counts.aligned, 2329)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAY217347")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(ExactPosition(1303), ExactPosition(2089), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14407, 14455, 14455, 14829, 14969, 15038, 15795,
                           15905, 15906, 15906, 15947, 16606, 16722, 16731,
                           16768, 16856, 17055, 17232, 17368, 17605, 17742,
                           17914, 18061, 18267, 18379, 18912, 19759],
                          [ 2382,  2334,  2329,  1955,  1955,  1886,  1886,
                            1776,  1776,  1774,  1733,  1733,  1617,  1617,
                            1580,  1580,  1381,  1381,  1245,  1245,  1108,
                            1108,   961,   961,   849,   849,     2]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (2373 aligned letters; 0 identities; 0 mismatches; 2986 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 2373:
        identities = 0,
        mismatches = 0.
    gaps = 2986:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 2986:
            internal_insertions = 7:
                open_internal_insertions = 2,
                extend_internal_insertions = 5;
            internal_deletions = 2979:
                open_internal_deletions = 11,
                extend_internal_deletions = 2968;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 7)
        self.assertEqual(counts.internal_deletions, 2979)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 2986)
        self.assertEqual(counts.insertions, 7)
        self.assertEqual(counts.deletions, 2979)
        self.assertEqual(counts.gaps, 2986)
        self.assertEqual(counts.aligned, 2373)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD043865")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14423, 14455], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD464022")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14453, 14485], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD464023")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14455, 14485], [30, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (30 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 30:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 30)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD426250")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14496, 14528], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD319762")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14537, 14569], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD439184")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14538, 14570], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAK289708")
        self.assertEqual(len(alignment.query.features), 1)
        self.assertEqual(
            alignment.query.features[0],
            SeqFeature(
                SimpleLocation(ExactPosition(146), ExactPosition(1553), strand=1),
                type="CDS",
            ),
        )
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[14570, 14829, 14969, 15038, 15795, 15905, 15906,
                           15906, 15947, 16606, 16722, 16722, 16768, 16856,
                           17055, 17232, 17368, 17605, 17742, 17914, 18061,
                           18267, 18379, 24737, 24891, 29823, 29961],
                          [ 1678,  1419,  1419,  1350,  1350,  1240,  1240,
                            1238,  1197,  1197,  1081,  1072,  1026,  1026,
                             827,   827,   691,   691,   554,   554,   407,
                             407,   295,   295,   141,   141,     3]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1664 aligned letters; 0 identities; 0 mismatches; 13738 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1664:
        identities = 0,
        mismatches = 0.
    gaps = 13738:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 13738:
            internal_insertions = 11:
                open_internal_insertions = 2,
                extend_internal_insertions = 9;
            internal_deletions = 13727:
                open_internal_deletions = 11,
                extend_internal_deletions = 13716;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 11)
        self.assertEqual(counts.internal_deletions, 13727)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 13738)
        self.assertEqual(counts.insertions, 11)
        self.assertEqual(counts.deletions, 13727)
        self.assertEqual(counts.gaps, 13738)
        self.assertEqual(counts.aligned, 1664)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mDQ588205")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14629, 14657], [0, 28]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (28 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 28:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 28)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD033185")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14643, 14667], [0, 24]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (24 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 24:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 24)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD386972")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14643, 14667], [24, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (24 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 24:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 24)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD469492")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14673, 14705], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD371043")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                np.array([[14702, 14717, 14720, 14737], [32, 17, 17, 0]]),
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 3 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 3:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 3:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 3:
                open_internal_deletions = 1,
                extend_internal_deletions = 2;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 3)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 3)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 3)
        self.assertEqual(counts.gaps, 3)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD186991")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                np.array([[14703, 14717, 14720, 14738], [32, 18, 18, 0]]),
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 3 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 3:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 3:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 3:
                open_internal_deletions = 1,
                extend_internal_deletions = 2;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 3)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 3)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 3)
        self.assertEqual(counts.gaps, 3)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD178321")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14704, 14725], [21, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (21 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 21:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 21)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD371044")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14705, 14737], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD492409")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14739, 14771], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD248147")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14746, 14770], [24, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (24 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 24:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 24)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD044295")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14785, 14817], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD433165")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14810, 14842], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD055458")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14823, 14855], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD131561")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14828, 14853], [25, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (25 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 25:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 25)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD129847")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14936, 14956], [20, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (20 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 20:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 20)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD219312")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[14950, 14971], [21, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (21 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 21:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 21)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD546847")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15086, 15118], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD218460")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15097, 15129], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mKJ806766")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                np.array([[15118, 15122, 15122, 15654], [9, 13, 14, 546]]),
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (536 aligned letters; 0 identities; 0 mismatches; 1 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 536:
        identities = 0,
        mismatches = 0.
    gaps = 1:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 1:
            internal_insertions = 1:
                open_internal_insertions = 1,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 1)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 1)
        self.assertEqual(counts.insertions, 1)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 1)
        self.assertEqual(counts.aligned, 536)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD131237")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15187, 15219], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD128091")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15209, 15241], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD422546")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15274, 15305], [31, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (31 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 31:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 31)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD153435")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15292, 15324], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD367640")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15461, 15493], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD487131")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15468, 15500], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD493181")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15480, 15512], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD205712")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15558, 15590], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD425846")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15584, 15616], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD219639")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15603, 15634], [32, 1]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (31 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 31:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 31)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD078677")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15603, 15635], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD078676")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15614, 15635], [21, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (21 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 21:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 21)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD253503")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15643, 15675], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD253504")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15644, 15675], [31, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (31 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 31:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 31)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD159284")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15664, 15687], [23, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (23 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 23:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 23)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD115871")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15675, 15707], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD456634")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15677, 15709], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD487879")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15741, 15772], [32, 1]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (31 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 31:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 31)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD080014")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15741, 15773], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD336830")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15760, 15792], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD444008")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15761, 15793], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD460507")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15812, 15836], [24, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (24 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 24:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 24)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mAK308574")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(
                alignment.coordinates,
                # fmt: off
                np.array([[15870, 15903, 15903, 16027, 16606, 16765, 16857,
                           17055, 17232, 17364, 17521, 17742, 17914, 18061,
                           18267, 18366, 29320, 29359],
                          [ 1153,  1120,  1119,   995,   995,   836,   836,
                             638,   638,   506,   506,   285,   285,   138,
                             138,    39,    39,     0]])
                # fmt: on
            )
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1152 aligned letters; 0 identities; 0 mismatches; 12338 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1152:
        identities = 0,
        mismatches = 0.
    gaps = 12338:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 12338:
            internal_insertions = 1:
                open_internal_insertions = 1,
                extend_internal_insertions = 0;
            internal_deletions = 12337:
                open_internal_deletions = 7,
                extend_internal_deletions = 12330;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 1)
        self.assertEqual(counts.internal_deletions, 12337)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 12338)
        self.assertEqual(counts.insertions, 1)
        self.assertEqual(counts.deletions, 12337)
        self.assertEqual(counts.gaps, 12338)
        self.assertEqual(counts.aligned, 1152)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD389037")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15906, 15936], [30, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (30 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 30:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 30)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD521711")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15947, 15979], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD383617")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15972, 16004], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD491045")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15982, 16014], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD318660")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[15985, 16017], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD341280")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[16118, 16150], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD220623")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[16157, 16189], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD465423")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[16165, 16197], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD515432")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[16176, 16208], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD542452")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[16184, 16216], [32, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (32 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 32:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 32)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD507246")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[16201, 16230], [30, 1]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (29 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 29:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 29)
        alignment = next(alignments)
        self.assertEqual(alignment.query.id, "mJD102852")
        self.assertEqual(len(alignment.query.features), 0)
        self.assertTrue(
            np.array_equal(alignment.coordinates, np.array([[16253, 16274], [21, 0]]))
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (21 aligned letters; 0 identities; 0 mismatches; 0 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 21:
        identities = 0,
        mismatches = 0.
    gaps = 0:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 0:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 0:
                open_internal_deletions = 0,
                extend_internal_deletions = 0;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 0)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 0)
        self.assertEqual(counts.insertions, 0)
        self.assertEqual(counts.deletions, 0)
        self.assertEqual(counts.gaps, 0)
        self.assertEqual(counts.aligned, 21)
        self.assertRaises(StopIteration, next, alignments)


class TestAlign_searching(unittest.TestCase):
    # The BED file bigbedtest.bed contains the following data:
    # chr1     10     100     name1   1       +
    # chr1     29      39     name2   2       -
    # chr1    200     300     name3   3       +
    # chr2     50      50     name4   6       +
    # chr2    100     110     name5   4       +
    # chr2    200     210     name6   5       +
    # chr2    220     220     name7   6       +
    # chr3      0       0     name8   7       -

    # with chromosome sizes in bigbedtest.chrom.sizes:
    # chr1 1000
    # chr2 2000
    # chr3 1000

    # The bigPsl file bigbedtest.psl.bb was generated using these commands:
    # bedToPsl bigbedtest.chrom.sizes bigbedtest.bed bigbedtest.psl
    # pslToBigPsl bigbedtest.psl stdout | sort -k1,1 -k2,2n > bigbedtest.bigPslInput
    # bedToBigBed -type=bed12+13 -tab -as=bigPsl.as bigbedtest.bigPslInput bigbedtest.chrom.sizes bigbedtest.psl.bb

    def test_search_chromosome(self):
        path = "Blat/bigbedtest.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        self.assertEqual(alignments.declaration, Align.bigpsl.declaration)
        selected_alignments = alignments.search("chr2")
        names = [alignment.query.id for alignment in selected_alignments]
        self.assertEqual(names, ["name4", "name5", "name6", "name7"])

    def test_search_region(self):
        path = "Blat/bigbedtest.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        selected_alignments = alignments.search("chr2", 105, 1000)
        names = [alignment.query.id for alignment in selected_alignments]
        self.assertEqual(names, ["name5", "name6", "name7"])
        selected_alignments = alignments.search("chr2", 110, 1000)
        names = [alignment.query.id for alignment in selected_alignments]
        self.assertEqual(names, ["name6", "name7"])
        selected_alignments = alignments.search("chr2", 40, 50)
        names = [alignment.query.id for alignment in selected_alignments]
        self.assertEqual(names, ["name4"])
        selected_alignments = alignments.search("chr2", 50, 50)
        names = [alignment.query.id for alignment in selected_alignments]
        self.assertEqual(names, ["name4"])
        selected_alignments = alignments.search("chr2", 50, 200)
        names = [alignment.query.id for alignment in selected_alignments]
        self.assertEqual(names, ["name4", "name5"])
        selected_alignments = alignments.search("chr2", 200, 220)
        names = [alignment.query.id for alignment in selected_alignments]
        self.assertEqual(names, ["name6", "name7"])
        selected_alignments = alignments.search("chr2", 220, 220)
        names = [alignment.query.id for alignment in selected_alignments]
        self.assertEqual(names, ["name7"])

    def test_search_position(self):
        path = "Blat/bigbedtest.psl.bb"
        alignments = Align.parse(path, "bigpsl")
        selected_alignments = alignments.search("chr1", 250)
        names = [alignment.query.id for alignment in selected_alignments]
        self.assertEqual(names, ["name3"])

    def test_three_iterators(self):
        """Create three iterators and use them concurrently."""
        path = "Blat/bigbedtest.psl.bb"
        alignments1 = Align.parse(path, "bigpsl")
        alignments2 = alignments1.search("chr2")
        alignments3 = alignments1.search("chr2", 110, 1000)
        alignment1 = next(alignments1)
        self.assertEqual(alignment1.query.id, "name1")
        alignment1 = next(alignments1)
        self.assertEqual(alignment1.query.id, "name2")
        alignment2 = next(alignments2)
        self.assertEqual(alignment2.query.id, "name4")
        alignment2 = next(alignments2)
        self.assertEqual(alignment2.query.id, "name5")
        alignment2 = next(alignments2)
        self.assertEqual(alignment2.query.id, "name6")
        alignment3 = next(alignments3)
        self.assertEqual(alignment3.query.id, "name6")
        alignment3 = next(alignments3)
        self.assertEqual(alignment3.query.id, "name7")
        alignment1 = next(alignments1)
        self.assertEqual(alignment1.query.id, "name3")
        alignment1 = next(alignments1)
        self.assertEqual(alignment1.query.id, "name4")
        alignment1 = next(alignments1)
        self.assertEqual(alignment1.query.id, "name5")
        alignment2 = next(alignments2)
        self.assertEqual(alignment2.query.id, "name7")
        self.assertRaises(StopIteration, next, alignments2)
        alignment1 = next(alignments1)
        self.assertEqual(alignment1.query.id, "name6")
        alignment1 = next(alignments1)
        self.assertEqual(alignment1.query.id, "name7")
        self.assertRaises(StopIteration, next, alignments3)
        alignment1 = next(alignments1)
        self.assertEqual(alignment1.query.id, "name8")
        self.assertRaises(StopIteration, next, alignments1)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
