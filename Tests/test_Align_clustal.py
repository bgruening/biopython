# Copyright 2006-2014 by Peter Cock.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.
"""Tests for Bio.Align.clustal module."""
import unittest
from io import StringIO
from tempfile import NamedTemporaryFile

import numpy as np

from Bio import Align
from Bio.Align import substitution_matrices

substitution_matrix = substitution_matrices.load("BLOSUM62")


class TestClustalReadingWriting(unittest.TestCase):
    def check_reading_writing(self, path):
        alignments = Align.parse(path, "clustal")
        stream = StringIO()
        n = Align.write(alignments, stream, "clustal")
        self.assertEqual(n, 1)
        alignments = Align.parse(path, "clustal")
        alignment = next(alignments)
        stream.seek(0)
        saved_alignments = Align.parse(stream, "clustal")
        self.assertEqual(saved_alignments.metadata, alignments.metadata)
        saved_alignment = next(saved_alignments)
        with self.assertRaises(StopIteration):
            next(saved_alignments)
        self.assertEqual(len(alignment), len(saved_alignment))
        for i, (sequence, saved_sequence) in enumerate(
            zip(alignment.sequences, saved_alignment.sequences)
        ):
            self.assertEqual(sequence.id, saved_sequence.id)
            self.assertEqual(sequence.seq, saved_sequence.seq)
            self.assertEqual(alignment[i], saved_alignment[i])

    def test_clustalw(self):
        path = "Clustalw/clustalw.aln"
        # includes the sequence length on the right hand side of each line
        with open(path) as stream:
            alignments = Align.parse(stream, "clustal")
            self.check_clustalw(alignments)
            alignments = iter(alignments)
            self.check_clustalw(alignments)
        with Align.parse(path, "clustal") as alignments:
            self.check_clustalw(alignments)
        with self.assertRaises(AttributeError):
            alignments._stream
        with Align.parse(path, "clustal") as alignments:
            pass
        with self.assertRaises(AttributeError):
            alignments._stream
        self.check_reading_writing(path)
        with open(path) as stream:
            data = stream.read()
        stream = NamedTemporaryFile("w+t")
        stream.write(data)
        stream.seek(0)
        alignments = Align.parse(stream, "clustal")
        self.check_clustalw(alignments)

    def check_clustalw(self, alignments):
        self.assertEqual(alignments.metadata["Program"], "CLUSTAL")
        self.assertEqual(alignments.metadata["Version"], "1.81")
        alignment = next(alignments)
        with self.assertRaises(StopIteration):
            next(alignments)
        self.assertEqual(
            repr(alignment),
            "<Alignment object (2 rows x 601 columns) at 0x%x>" % id(alignment),
        )
        self.assertEqual(len(alignment), 2)
        self.assertEqual(alignment.sequences[0].id, "gi|4959044|gb|AAD34209.1|AF069")
        self.assertEqual(alignment.sequences[1].id, "gi|671626|emb|CAA85685.1|")
        self.assertEqual(
            alignment.sequences[0].seq,
            "MENSDSNDKGSDQSAAQRRSQMDRLDREEAFYQFVNNLSEEDYRLMRDNNLLGTPGESTEEELLRRLQQIKEGPPPQSPDENRAGESSDDVTNSDSIIDWLNSVRQTGNTTRSRQRGNQSWRAVSRTNPNSGDFRFSLEINVNRNNGSQTSENESEPSTRRLSVENMESSSQRQMENSASESASARPSRAERNSTEAVTEVPTTRAQRRARSRSPEHRRTRARAERSMSPLQPTSEIPRRAPTLEQSSENEPEGSSRTRHHVTLRQQISGPELLGRGLFAASGSRNPSQGTSSSDTGSNSESSGSGQRPPTIVLDLQVRRVRPGEYRQRDSIASRTRSRSQAPNNTVTYESERGGFRRTFSRSERAGVRTYVSTIRIPIRRILNTGLSETTSVAIQTMLRQIMTGFGELSYFMYSDSDSEPSASVSSRNVERVESRNGRGSSGGGNSSGSSSSSSPSPSSSGESSESSSKMFEGSSEGGSSGPSRKDGRHRAPVTFDESGSLPFFSLAQFFLLNEDDEDQPRGLTKEQIDNLAMRSFGENDALKTCSVCITEYTEGDKLRKLPCSHEFHVHCIDRWLSENSTCPICRRAVLSSGNRESVV",
        )
        self.assertEqual(
            alignment.sequences[1].seq,
            "MSPQTETKASVGFKAGVKEYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAESSTGTWTTVWTDGLTSLDRYKGRCYHIEPVPGEKDQCICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRALRLEDLRIPVAYVKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEAIYKAQAETGEIKGHYLNATAGTCEEMIKRAIFARELGVPIVMHDYLTGGFTANTSLAHYCRDNGLLLHIHRAMHAVIDRQKNHGMHFRVLAKALRLSGGDHIHSGTVVGKLEGERDITLGFVDLLRDDFIEKDRSRGIYFTQDWVSLPGVIPVASGGIHVWHMPALTEIFGDDSVLQFGGGTLGHPWGNAPGAVANRVAVEACVKARNEGRDLAAEGNAIIREACKWSPELAAACEVWKEIKFEFPAMD",
        )
        self.assertEqual(
            alignment[0],
            "MENSDSNDKGSDQSAAQRRSQMDRLDREEAFYQFVNNLSEEDYRLMRDNNLLGTPGESTEEELLRRLQQIKEGPPPQSPDENRAGESSDDVTNSDSIIDWLNSVRQTGNTTRSRQRGNQSWRAVSRTNPNSGDFRFSLEINVNRNNGSQTSENESEPSTRRLSVENMESSSQRQMENSASESASARPSRAERNSTEAVTEVPTTRAQRRARSRSPEHRRTRARAERSMSPLQPTSEIPRRAPTLEQSSENEPEGSSRTRHHVTLRQQISGPELLGRGLFAASGSRNPSQGTSSSDTGSNSESSGSGQRPPTIVLDLQVRRVRPGEYRQRDSIASRTRSRSQAPNNTVTYESERGGFRRTFSRSERAGVRTYVSTIRIPIRRILNTGLSETTSVAIQTMLRQIMTGFGELSYFMYSDSDSEPSASVSSRNVERVESRNGRGSSGGGNSSGSSSSSSPSPSSSGESSESSSKMFEGSSEGGSSGPSRKDGRHRAPVTFDESGSLPFFSLAQFFLLNEDDEDQPRGLTKEQIDNLAMRSFGENDALKTCSVCITEYTEGDKLRKLPCSHEFHVHCIDRWLSE-NSTCPICRRAVLSSGNRESVV",
        )
        self.assertEqual(
            alignment[1],
            "---------MSPQTETKASVGFKAGVKEYKLTYYTPEYETKDTDILAAFRVTPQPG-----------------VPPEEAGAAVAAESSTGT---------WTTVWTDGLTSLDRYKG-----RCYHIEPVPG-------------------EKDQCICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRALRLEDLRIPVAYVKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEAIYKAQAETGEIKGHYLNATAG-----------------------TCEEMIKRAIFARELGVPIVMHDYLTGGFTANTSLAHYCRDNGLLLHIHRAMHAVIDRQKNHGMHFRVLAKALRLSGGDHIHSGTVVGKLEGERDITLGFVDLLRDDFIEKDRSRGIYFTQDWVSLPGVIPVASG-----------------------------GIHVWHMPALTEIFGDDSVLQFGGGTLGHPWGNAPGAVANRVA-----------VEACVKARNEG---RDLAAEGNAIIREACKWSPELAAACEVWKEIKFEFPAMD---",
        )
        self.assertEqual(
            str(alignment),
            """\
gi|495904         0 MENSDSNDKGSDQSAAQRRSQMDRLDREEAFYQFVNNLSEEDYRLMRDNNLLGTPGESTE
                  0 ---------.|.|..............|.............|............||----
gi|671626         0 ---------MSPQTETKASVGFKAGVKEYKLTYYTPEYETKDTDILAAFRVTPQPG----

gi|495904        60 EELLRRLQQIKEGPPPQSPDENRAGESSDDVTNSDSIIDWLNSVRQTGNTTRSRQRGNQS
                 60 -------------.||.......|.|||...---------...|...|.|...|..|---
gi|671626        47 -------------VPPEEAGAAVAAESSTGT---------WTTVWTDGLTSLDRYKG---

gi|495904       120 WRAVSRTNPNSGDFRFSLEINVNRNNGSQTSENESEPSTRRLSVENMESSSQRQMENSAS
                120 --......|..|-------------------|...............|..|...|..|..
gi|671626        82 --RCYHIEPVPG-------------------EKDQCICYVAYPLDLFEEGSVTNMFTSIV

gi|495904       180 ESASARPSRAERNSTEAVTEVPTTRAQRRARSRSPEHRRTRARAERSMSPLQPTSEIPRR
                180 ....................|................|.......|..............
gi|671626       121 GNVFGFKALRALRLEDLRIPVAYVKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLS

gi|495904       240 APTLEQSSENEPEGSSRTRHHVTLRQQISGPELLGRGLFAASGSRNPSQGTSSSDTGSNS
                240 |............|.....................|.||.|.........|.........
gi|671626       181 AKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEAIYKAQAETGEIKGHYLN

gi|495904       300 ESSGSGQRPPTIVLDLQVRRVRPGEYRQRDSIASRTRSRSQAPNNTVTYESERGGFRRTF
                300 ...|-----------------------.......|...........|......|||....
gi|671626       241 ATAG-----------------------TCEEMIKRAIFARELGVPIVMHDYLTGGFTANT

gi|495904       360 SRSERAGVRTYVSTIRIPIRRILNTGLSETTSVAIQTMLRQIMTGFGELSYFMYSDSDSE
                360 |.............|.............................|....|.........|
gi|671626       278 SLAHYCRDNGLLLHIHRAMHAVIDRQKNHGMHFRVLAKALRLSGGDHIHSGTVVGKLEGE

gi|495904       420 PSASVSSRNVERVESRNGRGSSGGGNSSGSSSSSSPSPSSSGESSESSSKMFEGSSEGGS
                420 ...........|........|.|........|.....|..||------------------
gi|671626       338 RDITLGFVDLLRDDFIEKDRSRGIYFTQDWVSLPGVIPVASG------------------

gi|495904       480 SGPSRKDGRHRAPVTFDESGSLPFFSLAQFFLLNEDDEDQPRGLTKEQIDNLAMRSFGEN
                480 -----------.............|...............|.|.......|...------
gi|671626       380 -----------GIHVWHMPALTEIFGDDSVLQFGGGTLGHPWGNAPGAVANRVA------

gi|495904       540 DALKTCSVCITEYTEGDKLRKLPCSHEFHVHCIDRWLSE-NSTCPICRRAVLSSGNRESV
                540 -----...|.....||---|.|.............|..|-...|..............--
gi|671626       423 -----VEACVKARNEG---RDLAAEGNAIIREACKWSPELAAACEVWKEIKFEFPAMD--

gi|495904       599 V 600
                600 - 601
gi|671626       473 - 473
""",
        )
        self.assertEqual(
            format(alignment, "clustal"),
            """\
gi|4959044|gb|AAD34209.1|AF069      MENSDSNDKGSDQSAAQRRSQMDRLDREEAFYQFVNNLSEEDYRLMRDNN
gi|671626|emb|CAA85685.1|           ---------MSPQTETKASVGFKAGVKEYKLTYYTPEYETKDTDILAAFR
                                              * *: ::    :.   :*  :  :. : . :*  ::   .

gi|4959044|gb|AAD34209.1|AF069      LLGTPGESTEEELLRRLQQIKEGPPPQSPDENRAGESSDDVTNSDSIIDW
gi|671626|emb|CAA85685.1|           VTPQPG-----------------VPPEEAGAAVAAESSTGT---------
                                    :   **                  **:...   *.*** ..         

gi|4959044|gb|AAD34209.1|AF069      LNSVRQTGNTTRSRQRGNQSWRAVSRTNPNSGDFRFSLEINVNRNNGSQT
gi|671626|emb|CAA85685.1|           WTTVWTDGLTSLDRYKG-----RCYHIEPVPG------------------
                                     .:*   * *: .* :*        : :* .*                  

gi|4959044|gb|AAD34209.1|AF069      SENESEPSTRRLSVENMESSSQRQMENSASESASARPSRAERNSTEAVTE
gi|671626|emb|CAA85685.1|           -EKDQCICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRALRLEDLRIP
                                     *::.  .    .:: :*..*  :* .*   .. .  :    .  :    

gi|4959044|gb|AAD34209.1|AF069      VPTTRAQRRARSRSPEHRRTRARAERSMSPLQPTSEIPRRAPTLEQSSEN
gi|671626|emb|CAA85685.1|           VAYVKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYE
                                    *. .:: : .      .* .  :  *.:     ..::   * .  ::  :

gi|4959044|gb|AAD34209.1|AF069      EPEGSSRTRHHVTLRQQISGPELLGRGLFAASGSRNPSQGTSSSDTGSNS
gi|671626|emb|CAA85685.1|           CLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEAIYKAQAETGEIKGHYLN
                                      .*.    :.    :. .  .  .* **.*..  :..  *.. .    .

gi|4959044|gb|AAD34209.1|AF069      ESSGSGQRPPTIVLDLQVRRVRPGEYRQRDSIASRTRSRSQAPNNTVTYE
gi|671626|emb|CAA85685.1|           ATAG-----------------------TCEEMIKRAIFARELGVPIVMHD
                                     ::*                         :.: .*:    :     * ::

gi|4959044|gb|AAD34209.1|AF069      SERGGFRRTFSRSERAGVRTYVSTIRIPIRRILNTGLSETTSVAIQTMLR
gi|671626|emb|CAA85685.1|           YLTGGFTANTSLAHYCRDNGLLLHIHRAMHAVIDRQKNHGMHFRVLAKAL
                                       ***  . * :. .  .  :  *: .:: :::   ..   . : :   

gi|4959044|gb|AAD34209.1|AF069      QIMTGFGELSYFMYSDSDSEPSASVSSRNVERVESRNGRGSSGGGNSSGS
gi|671626|emb|CAA85685.1|           RLSGGDHIHSGTVVGKLEGERDITLGFVDLLRDDFIEKDRSRGIYFTQDW
                                    ::  *    *  : .. :.* . ::.  :: * :  :   * *   :.. 

gi|4959044|gb|AAD34209.1|AF069      SSSSSPSPSSSGESSESSSKMFEGSSEGGSSGPSRKDGRHRAPVTFDESG
gi|671626|emb|CAA85685.1|           VSLPGVIPVASG-----------------------------GIHVWHMPA
                                     * ..  * :**                             .  .:. ..

gi|4959044|gb|AAD34209.1|AF069      SLPFFSLAQFFLLNEDDEDQPRGLTKEQIDNLAMRSFGENDALKTCSVCI
gi|671626|emb|CAA85685.1|           LTEIFGDDSVLQFGGGTLGHPWGNAPGAVANRVA-----------VEACV
                                       :*.  ..: :. .  .:* * :   : * .             ..*:

gi|4959044|gb|AAD34209.1|AF069      TEYTEGDKLRKLPCSHEFHVHCIDRWLSE-NSTCPICRRAVLSSGNRESV
gi|671626|emb|CAA85685.1|           KARNEG---RDLAAEGNAIIREACKWSPELAAACEVWKEIKFEFPAMD--
                                    .  .**   *.*... :  ::   :* .*  ::* : :.  :.    :  

gi|4959044|gb|AAD34209.1|AF069      V
gi|671626|emb|CAA85685.1|           -
                                     


""",  # noqa: W293
        )
        counts = alignment.counts(substitution_matrix)
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (substitution score = -34.0; 472 aligned letters; 64 identities; 408 mismatches; 126 positives; 129 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    substitution_score = -34.0,
    aligned = 472:
        identities = 64,
        positives = 126,
        mismatches = 408.
    gaps = 129:
        left_gaps = 9:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 9:
                open_left_deletions = 1,
                extend_left_deletions = 8;
        internal_gaps = 117:
            internal_insertions = 1:
                open_internal_insertions = 1,
                extend_internal_insertions = 0;
            internal_deletions = 116:
                open_internal_deletions = 8,
                extend_internal_deletions = 108;
        right_gaps = 3:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 3:
                open_right_deletions = 1,
                extend_right_deletions = 2.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 9)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 3)
        self.assertEqual(counts.internal_insertions, 1)
        self.assertEqual(counts.internal_deletions, 116)
        self.assertEqual(counts.left_gaps, 9)
        self.assertEqual(counts.right_gaps, 3)
        self.assertEqual(counts.internal_gaps, 117)
        self.assertEqual(counts.insertions, 1)
        self.assertEqual(counts.deletions, 128)
        self.assertEqual(counts.gaps, 129)
        self.assertEqual(counts.aligned, 472)
        self.assertEqual(counts.identities, 64)
        self.assertEqual(counts.mismatches, 408)
        self.assertEqual(counts.positives, 126)

    def test_msaprobs(self):
        path = "Clustalw/msaprobs.aln"
        # This example was obtained from
        # http://virgil.ruc.dk/kurser/Sekvens/Treedraw.htm
        with open(path) as stream:
            alignments = Align.parse(stream, "clustal")
            self.assertEqual(alignments.metadata["Program"], "MSAPROBS")
            self.assertEqual(alignments.metadata["Version"], "0.9.7")
            alignment = next(alignments)
            with self.assertRaises(StopIteration):
                next(alignments)
        self.assertEqual(
            repr(alignment),
            "<Alignment object (8 rows x 298 columns) at 0x%x>" % id(alignment),
        )
        self.assertEqual(len(alignment), 8)
        self.assertEqual(alignment.shape, (8, 298))
        self.assertEqual(alignment.sequences[0].id, "V_Harveyi_PATH")
        self.assertEqual(alignment.sequences[1].id, "B_subtilis_YXEM")
        self.assertEqual(alignment.sequences[2].id, "FLIY_ECOLI")
        self.assertEqual(alignment.sequences[3].id, "Deinococcus_radiodurans")
        self.assertEqual(alignment.sequences[4].id, "B_subtilis_GlnH_homo_YCKK")
        self.assertEqual(alignment.sequences[5].id, "YA80_HAEIN")
        self.assertEqual(alignment.sequences[6].id, "E_coli_GlnH")
        self.assertEqual(alignment.sequences[7].id, "HISJ_E_COLI")
        self.assertEqual(
            alignment.sequences[0].seq,
            "MKNWIKVAVAAIALSAATVQAATEVKVGMSGRYFPFTFVKQDKLQGFEVDMWDEIGKRNDYKIEYVTANFSGLFGLLETGRIDTISNQITMTDARKAKYLFADPYVVDGAQITVRKGNDSIQGVEDLAGKTVAVNLGSNFEQLLRDYDKDGKINIKTYDTGIEHDVALGRADAFIMDRLSALELIKKTGLPLQLAGEPFETIQNAWPFVDNEKGRKLQAEVNKALAEMRADGTVEKISVKWFGADITK",
        )
        self.assertEqual(
            alignment.sequences[1].seq,
            "MKMKKWTVLVVAALLAVLSACGNGNSSSKEDDNVLHVGATGQSYPFAYKENGKLTGFDVEVMEAVAKKIDMKLDWKLLEFSGLMGELQTGKLDTISNQVAVTDERKETYNFTKPYAYAGTQIVVKKDNTDIKSVDDLKGKTVAAVLGSNHAKNLESKDPDKKINIKTYETQEGTLKDVAYGRVDAYVNSRTVLIAQIKKTGLPLKLAGDPIVYEQVAFPFAKDDAHDKLRKKVNKALDELRKDGTLKKLSEKYFNEDITVEQKH",
        )
        self.assertEqual(
            alignment.sequences[2].seq,
            "MKLAHLGRQALMGVMAVALVAGMSVKSFADEGLLNKVKERGTLLVGLEGTYPPFSFQGDDGKLTGFEVEFAQQLAKHLGVEASLKPTKWDGMLASLDSKRIDVVINQVTISDERKKKYDFSTPYTISGIQALVKKGNEGTIKTADDLKGKKVGVGLGTNYEEWLRQNVQGVDVRTYDDDPTKYQDLRVGRIDAILVDRLAALDLVKKTNDTLAVTGEAFSRQESGVALRKGNEDLLKAVNDAIAEMQKDGTLQALSEKWFGADVTK",
        )
        self.assertEqual(
            alignment.sequences[3].seq,
            "MKKSLLSLKLSGLLVPSVLALSLSACSSPSSTLNQGTLKIAMEGTYPPFTSKNEQGELVGFDVDIAKAVAQKLNLKPEFVLTEWSGILAGLQANKYDVIVNQVGITPERQNSIGFSQPYAYSRPEIIVAKNNTFNPQSLADLKGKRVGSTLGSNYEKQLIDTGDIKIVTYPGAPEILADLVAGRIDAAYNDRLVVNYIINDQKLPVRGAGQIGDAAPVGIALKKGNSALKDQIDKALTEMRSDGTFEKISQKWFGQDVGQP",
        )
        self.assertEqual(
            alignment.sequences[4].seq,
            "MKKALLALFMVVSIAALAACGAGNDNQSKDNAKDGDLWASIKKKGVLTVGTEGTYEPFTYHDKDTDKLTGYDVEVITEVAKRLGLKVDFKETQWGSMFAGLNSKRFDVVANQVGKTDREDKYDFSDKYTTSRAVVVTKKDNNDIKSEADVKGKTSAQSLTSNYNKLATNAGAKVEGVEGMAQALQMIQQARVDMTYNDKLAVLNYLKTSGNKNVKIAFETGEPQSTYFTFRKGSGEVVDQVNKALKEMKEDGTLSKISKKWFGEDVSK",
        )
        self.assertEqual(
            alignment.sequences[5].seq,
            "MKKLLFTTALLTGAIAFSTFSHAGEIADRVEKTKTLLVGTEGTYAPFTFHDKSGKLTGFDVEVIRKVAEKLGLKVEFKETQWDAMYAGLNAKRFDVIANQTNPSPERLKKYSFTTPYNYSGGVIVTKSSDNSIKSFEDLKGRKSAQSATSNWGKDAKAAGAQILVVDGLAQSLELIKQGRAEATINDKLAVLDYFKQHPNSGLKIAYDRGDKTPTAFAFLQGEDALITKFNQVLEALRQDGTLKQISIEWFGYDITQ",
        )
        self.assertEqual(
            alignment.sequences[6].seq,
            "MKSVLKVSLAALTLAFAVSSHAADKKLVVATDTAFVPFEFKQGDKYVGFDVDLWAAIAKELKLDYELKPMDFSGIIPALQTKNVDLALAGITITDERKKAIDFSDGYYKSGLLVMVKANNNDVKSVKDLDGKVVAVKSGTGSVDYAKANIKTKDLRQFPNIDNAYMELGTNRADAVLHDTPNILYFIKTAGNGQFKAVGDSLEAQQYGIAFPKGSDELRDKVNGALKTLRENGTYNEIYKKWFGTEPK",
        )
        self.assertEqual(
            alignment.sequences[7].seq,
            "MKKLVLSLSLVLAFSSATAAFAAIPQNIRIGTDPTYAPFESKNSQGELVGFDIDLAKELCKRINTQCTFVENPLDALIPSLKAKKIDAIMSSLSITEKRQQEIAFTDKLYAADSRLVVAKNSDIQPTVESLKGKRVGVLQGTTQETFGNEHWAPKGIEIVSYQGQDNIYSDLTAGRIDAAFQDEVAASEGFLKQPVGKDYKFGGPSVKDEKLFGVGTGMGLRKEDNELREALNKAFAEMRADGTYEKLAKKYFDFDVYGG",
        )
        self.assertEqual(
            alignment[0],
            "MKNW--------IKV----AVAAI-A--LSAA-------------------TVQAATEVKVGMSGRYFPFTFVK--QDKLQGFEVDMWDEIGKRNDYKIEYVTANFSGLFGLLETGRIDTISNQITMTDARKAKYLFADPYVVDGAQITVRK-GNDSIQGVEDLAGKTVAVNLGSNFEQLLRDYDKDGKINIKTYDT--GIEHDVALGRADAFIMDRLSALE-LIKKTG-LPLQLAGEPFE-----TIQNAWPFVDNEKGRKLQAEVNKALAEMRADGTVEKISVKWFGADITK----",
        )
        self.assertEqual(
            alignment[1],
            "MKMKKW------TVL----VVAALLA-VLSACGN------------G-NSSSKEDDNVLHVGATGQSYPFAYKE--NGKLTGFDVEVMEAVAKKIDMKLDWKLLEFSGLMGELQTGKLDTISNQVAVTDERKETYNFTKPYAYAGTQIVVKK-DNTDIKSVDDLKGKTVAAVLGSNHAKNLESKDPDKKINIKTYETQEGTLKDVAYGRVDAYVNSRTVLIA-QIKKTG-LPLKLAGDPIV-----YEQVAFPFAKDDAHDKLRKKVNKALDELRKDGTLKKLSEKYFNEDITVEQKH",
        )
        self.assertEqual(
            alignment[2],
            "MKLAHLGRQALMGVM----AVALVAG--MSVKSF---------ADEG-LLNKVKERGTLLVGLEGTYPPFSFQGD-DGKLTGFEVEFAQQLAKHLGVEASLKPTKWDGMLASLDSKRIDVVINQVTISDERKKKYDFSTPYTISGIQALVKKGNEGTIKTADDLKGKKVGVGLGTNYEEWLRQN--VQGVDVRTYDDDPTKYQDLRVGRIDAILVDRLAALD-LVKKTN-DTLAVTGEAFS-----RQESGVALRK--GNEDLLKAVNDAIAEMQKDGTLQALSEKWFGADVTK----",
        )
        self.assertEqual(
            alignment[3],
            "MKKSLL------SLKLSGLLVPSVLALSLSACSS---------------PSSTLNQGTLKIAMEGTYPPFTSKNE-QGELVGFDVDIAKAVAQKLNLKPEFVLTEWSGILAGLQANKYDVIVNQVGITPERQNSIGFSQPYAYSRPEIIVAKNNTFNPQSLADLKGKRVGSTLGSNYEKQLI-D--TGDIKIVTYPGAPEILADLVAGRIDAAYNDRLVVNY-IIND-QKLPVRGAGQIGD-----AAPVGIALKK--GNSALKDQIDKALTEMRSDGTFEKISQKWFGQDVGQ---P",
        )
        self.assertEqual(
            alignment[4],
            "MKKALL------ALF----MVVSIAA--LAACGAGNDNQSKDNAKDGDLWASIKKKGVLTVGTEGTYEPFTYHDKDTDKLTGYDVEVITEVAKRLGLKVDFKETQWGSMFAGLNSKRFDVVANQVGKTD-REDKYDFSDKYTTSRAVVVTKK-DNNDIKSEADVKGKTSAQSLTSNYNKLAT-N--A-GAKVEGVEGMAQALQMIQQARVDMTYNDKLAVLN-YLKTSGNKNVKIAFETGE-----PQSTYFTFRK--GSGEVVDQVNKALKEMKEDGTLSKISKKWFGEDVSK----",
        )
        self.assertEqual(
            alignment[5],
            "MKKLLF------TTA----LLTGAIA--FSTFS-----------HAGEIADRVEKTKTLLVGTEGTYAPFTFHDK-SGKLTGFDVEVIRKVAEKLGLKVEFKETQWDAMYAGLNAKRFDVIANQTNPSPERLKKYSFTTPYNYSGGVIVTKS-SDNSIKSFEDLKGRKSAQSATSNWGKDAK-A--A-GAQILVVDGLAQSLELIKQGRAEATINDKLAVLD-YFKQHPNSGLKIAYDRGD-----KTPTAFAFLQ--GEDALITKFNQVLEALRQDGTLKQISIEWFGYDITQ----",
        )
        self.assertEqual(
            alignment[6],
            "MKSVL-------KVS----LAALTLA--FAVSSH---------A----------ADKKLVVATDTAFVPFEFKQ--GDKYVGFDVDLWAAIAKELKLDYELKPMDFSGIIPALQTKNVDLALAGITITDERKKAIDFSDGYYKSGLLVMVKAN-NNDVKSVKDLDGKVVAVKSGTGSVDYAKAN--IKTKDLRQFPNIDNAYMELGTNRADAVLHDTPNILY-FIKTAGNGQFKAVGDSLE-----AQQYGIAFPK--GSDELRDKVNGALKTLRENGTYNEIYKKWFGTEP-K----",
        )
        self.assertEqual(
            alignment[7],
            "MKKLVL------SLS----LV---LA--FSSATA---------------A-FAAIPQNIRIGTDPTYAPFESKNS-QGELVGFDIDLAKELCKRINTQCTFVENPLDALIPSLKAKKIDAIMSSLSITEKRQQEIAFTDKLYAADSRLVVAK-NSDIQPTVESLKGKRVGVLQGTTQETFGNEHWAPKGIEIVSYQGQDNIYSDLTAGRIDAAFQDEVAASEGFLKQPVGKDYKFGGPSVKDEKLFGVGTGMGLRK--EDNELREALNKAFAEMRADGTYEKLAKKYFDFDVYG---G",
        )
        self.assertEqual(
            alignment.column_annotations["clustal_consensus"],
            "**                       .  ::             *. *:          : :.      **    .  .:  *::::.   : :.   .        ..:   *.: . *        :  *     *:           .  ..        .: *:  .    :               .:            :   * :    .        .:                           : .::    :   .: .:  :: :** . :  ::*. :       ",
        )
        self.assertEqual(
            str(alignment),
            """\
V_Harveyi         0 MKNW--------IKV----AVAAI-A--LSAA-------------------TVQAATEVK
B_subtili         0 MKMKKW------TVL----VVAALLA-VLSACGN------------G-NSSSKEDDNVLH
FLIY_ECOL         0 MKLAHLGRQALMGVM----AVALVAG--MSVKSF---------ADEG-LLNKVKERGTLL
Deinococc         0 MKKSLL------SLKLSGLLVPSVLALSLSACSS---------------PSSTLNQGTLK
B_subtili         0 MKKALL------ALF----MVVSIAA--LAACGAGNDNQSKDNAKDGDLWASIKKKGVLT
YA80_HAEI         0 MKKLLF------TTA----LLTGAIA--FSTFS-----------HAGEIADRVEKTKTLL
E_coli_Gl         0 MKSVL-------KVS----LAALTLA--FAVSSH---------A----------ADKKLV
HISJ_E_CO         0 MKKLVL------SLS----LV---LA--FSSATA---------------A-FAAIPQNIR

V_Harveyi        26 VGMSGRYFPFTFVK--QDKLQGFEVDMWDEIGKRNDYKIEYVTANFSGLFGLLETGRIDT
B_subtili        36 VGATGQSYPFAYKE--NGKLTGFDVEVMEAVAKKIDMKLDWKLLEFSGLMGELQTGKLDT
FLIY_ECOL        44 VGLEGTYPPFSFQGD-DGKLTGFEVEFAQQLAKHLGVEASLKPTKWDGMLASLDSKRIDV
Deinococc        39 IAMEGTYPPFTSKNE-QGELVGFDVDIAKAVAQKLNLKPEFVLTEWSGILAGLQANKYDV
B_subtili        48 VGTEGTYEPFTYHDKDTDKLTGYDVEVITEVAKRLGLKVDFKETQWGSMFAGLNSKRFDV
YA80_HAEI        37 VGTEGTYAPFTFHDK-SGKLTGFDVEVIRKVAEKLGLKVEFKETQWDAMYAGLNAKRFDV
E_coli_Gl        28 VATDTAFVPFEFKQ--GDKYVGFDVDLWAAIAKELKLDYELKPMDFSGIIPALQTKNVDL
HISJ_E_CO        29 IGTDPTYAPFESKNS-QGELVGFDIDLAKELCKRINTQCTFVENPLDALIPSLKAKKIDA

V_Harveyi        84 ISNQITMTDARKAKYLFADPYVVDGAQITVRK-GNDSIQGVEDLAGKTVAVNLGSNFEQL
B_subtili        94 ISNQVAVTDERKETYNFTKPYAYAGTQIVVKK-DNTDIKSVDDLKGKTVAAVLGSNHAKN
FLIY_ECOL       103 VINQVTISDERKKKYDFSTPYTISGIQALVKKGNEGTIKTADDLKGKKVGVGLGTNYEEW
Deinococc        98 IVNQVGITPERQNSIGFSQPYAYSRPEIIVAKNNTFNPQSLADLKGKRVGSTLGSNYEKQ
B_subtili       108 VANQVGKTD-REDKYDFSDKYTTSRAVVVTKK-DNNDIKSEADVKGKTSAQSLTSNYNKL
YA80_HAEI        96 IANQTNPSPERLKKYSFTTPYNYSGGVIVTKS-SDNSIKSFEDLKGRKSAQSATSNWGKD
E_coli_Gl        86 ALAGITITDERKKAIDFSDGYYKSGLLVMVKAN-NNDVKSVKDLDGKVVAVKSGTGSVDY
HISJ_E_CO        88 IMSSLSITEKRQQEIAFTDKLYAADSRLVVAK-NSDIQPTVESLKGKRVGVLQGTTQETF

V_Harveyi       143 LRDYDKDGKINIKTYDT--GIEHDVALGRADAFIMDRLSALE-LIKKTG-LPLQLAGEPF
B_subtili       153 LESKDPDKKINIKTYETQEGTLKDVAYGRVDAYVNSRTVLIA-QIKKTG-LPLKLAGDPI
FLIY_ECOL       163 LRQN--VQGVDVRTYDDDPTKYQDLRVGRIDAILVDRLAALD-LVKKTN-DTLAVTGEAF
Deinococc       158 LI-D--TGDIKIVTYPGAPEILADLVAGRIDAAYNDRLVVNY-IIND-QKLPVRGAGQIG
B_subtili       166 AT-N--A-GAKVEGVEGMAQALQMIQQARVDMTYNDKLAVLN-YLKTSGNKNVKIAFETG
YA80_HAEI       155 AK-A--A-GAQILVVDGLAQSLELIKQGRAEATINDKLAVLD-YFKQHPNSGLKIAYDRG
E_coli_Gl       145 AKAN--IKTKDLRQFPNIDNAYMELGTNRADAVLHDTPNILY-FIKTAGNGQFKAVGDSL
HISJ_E_CO       147 GNEHWAPKGIEIVSYQGQDNIYSDLTAGRIDAAFQDEVAASEGFLKQPVGKDYKFGGPSV

V_Harveyi       199 E-----TIQNAWPFVDNEKGRKLQAEVNKALAEMRADGTVEKISVKWFGADITK----
B_subtili       211 V-----YEQVAFPFAKDDAHDKLRKKVNKALDELRKDGTLKKLSEKYFNEDITVEQKH
FLIY_ECOL       219 S-----RQESGVALRK--GNEDLLKAVNDAIAEMQKDGTLQALSEKWFGADVTK----
Deinococc       213 D-----AAPVGIALKK--GNSALKDQIDKALTEMRSDGTFEKISQKWFGQDVGQ---P
B_subtili       221 E-----PQSTYFTFRK--GSGEVVDQVNKALKEMKEDGTLSKISKKWFGEDVSK----
YA80_HAEI       210 D-----KTPTAFAFLQ--GEDALITKFNQVLEALRQDGTLKQISIEWFGYDITQ----
E_coli_Gl       202 E-----AQQYGIAFPK--GSDELRDKVNGALKTLRENGTYNEIYKKWFGTEP-K----
HISJ_E_CO       207 KDEKLFGVGTGMGLRK--EDNELREALNKAFAEMRADGTYEKLAKKYFDFDVYG---G

V_Harveyi       248
B_subtili       264
FLIY_ECOL       266
Deinococc       261
B_subtili       268
YA80_HAEI       257
E_coli_Gl       248
HISJ_E_CO       260
""",
        )
        self.assertEqual(
            format(alignment, "clustal"),
            """\
V_Harveyi_PATH                      MKNW--------IKV----AVAAI-A--LSAA------------------
B_subtilis_YXEM                     MKMKKW------TVL----VVAALLA-VLSACGN------------G-NS
FLIY_ECOLI                          MKLAHLGRQALMGVM----AVALVAG--MSVKSF---------ADEG-LL
Deinococcus_radiodurans             MKKSLL------SLKLSGLLVPSVLALSLSACSS---------------P
B_subtilis_GlnH_homo_YCKK           MKKALL------ALF----MVVSIAA--LAACGAGNDNQSKDNAKDGDLW
YA80_HAEIN                          MKKLLF------TTA----LLTGAIA--FSTFS-----------HAGEIA
E_coli_GlnH                         MKSVL-------KVS----LAALTLA--FAVSSH---------A------
HISJ_E_COLI                         MKKLVL------SLS----LV---LA--FSSATA---------------A
                                    **                       .  ::             *. *:  

V_Harveyi_PATH                      -TVQAATEVKVGMSGRYFPFTFVK--QDKLQGFEVDMWDEIGKRNDYKIE
B_subtilis_YXEM                     SSKEDDNVLHVGATGQSYPFAYKE--NGKLTGFDVEVMEAVAKKIDMKLD
FLIY_ECOLI                          NKVKERGTLLVGLEGTYPPFSFQGD-DGKLTGFEVEFAQQLAKHLGVEAS
Deinococcus_radiodurans             SSTLNQGTLKIAMEGTYPPFTSKNE-QGELVGFDVDIAKAVAQKLNLKPE
B_subtilis_GlnH_homo_YCKK           ASIKKKGVLTVGTEGTYEPFTYHDKDTDKLTGYDVEVITEVAKRLGLKVD
YA80_HAEIN                          DRVEKTKTLLVGTEGTYAPFTFHDK-SGKLTGFDVEVIRKVAEKLGLKVE
E_coli_GlnH                         ----ADKKLVVATDTAFVPFEFKQ--GDKYVGFDVDLWAAIAKELKLDYE
HISJ_E_COLI                         -FAAIPQNIRIGTDPTYAPFESKNS-QGELVGFDIDLAKELCKRINTQCT
                                            : :.      **    .  .:  *::::.   : :.   .  

V_Harveyi_PATH                      YVTANFSGLFGLLETGRIDTISNQITMTDARKAKYLFADPYVVDGAQITV
B_subtilis_YXEM                     WKLLEFSGLMGELQTGKLDTISNQVAVTDERKETYNFTKPYAYAGTQIVV
FLIY_ECOLI                          LKPTKWDGMLASLDSKRIDVVINQVTISDERKKKYDFSTPYTISGIQALV
Deinococcus_radiodurans             FVLTEWSGILAGLQANKYDVIVNQVGITPERQNSIGFSQPYAYSRPEIIV
B_subtilis_GlnH_homo_YCKK           FKETQWGSMFAGLNSKRFDVVANQVGKTD-REDKYDFSDKYTTSRAVVVT
YA80_HAEIN                          FKETQWDAMYAGLNAKRFDVIANQTNPSPERLKKYSFTTPYNYSGGVIVT
E_coli_GlnH                         LKPMDFSGIIPALQTKNVDLALAGITITDERKKAIDFSDGYYKSGLLVMV
HISJ_E_COLI                         FVENPLDALIPSLKAKKIDAIMSSLSITEKRQQEIAFTDKLYAADSRLVV
                                          ..:   *.: . *        :  *     *:           .

V_Harveyi_PATH                      RK-GNDSIQGVEDLAGKTVAVNLGSNFEQLLRDYDKDGKINIKTYDT--G
B_subtilis_YXEM                     KK-DNTDIKSVDDLKGKTVAAVLGSNHAKNLESKDPDKKINIKTYETQEG
FLIY_ECOLI                          KKGNEGTIKTADDLKGKKVGVGLGTNYEEWLRQN--VQGVDVRTYDDDPT
Deinococcus_radiodurans             AKNNTFNPQSLADLKGKRVGSTLGSNYEKQLI-D--TGDIKIVTYPGAPE
B_subtilis_GlnH_homo_YCKK           KK-DNNDIKSEADVKGKTSAQSLTSNYNKLAT-N--A-GAKVEGVEGMAQ
YA80_HAEIN                          KS-SDNSIKSFEDLKGRKSAQSATSNWGKDAK-A--A-GAQILVVDGLAQ
E_coli_GlnH                         KAN-NNDVKSVKDLDGKVVAVKSGTGSVDYAKAN--IKTKDLRQFPNIDN
HISJ_E_COLI                         AK-NSDIQPTVESLKGKRVGVLQGTTQETFGNEHWAPKGIEIVSYQGQDN
                                      ..        .: *:  .    :               .:        

V_Harveyi_PATH                      IEHDVALGRADAFIMDRLSALE-LIKKTG-LPLQLAGEPFE-----TIQN
B_subtilis_YXEM                     TLKDVAYGRVDAYVNSRTVLIA-QIKKTG-LPLKLAGDPIV-----YEQV
FLIY_ECOLI                          KYQDLRVGRIDAILVDRLAALD-LVKKTN-DTLAVTGEAFS-----RQES
Deinococcus_radiodurans             ILADLVAGRIDAAYNDRLVVNY-IIND-QKLPVRGAGQIGD-----AAPV
B_subtilis_GlnH_homo_YCKK           ALQMIQQARVDMTYNDKLAVLN-YLKTSGNKNVKIAFETGE-----PQST
YA80_HAEIN                          SLELIKQGRAEATINDKLAVLD-YFKQHPNSGLKIAYDRGD-----KTPT
E_coli_GlnH                         AYMELGTNRADAVLHDTPNILY-FIKTAGNGQFKAVGDSLE-----AQQY
HISJ_E_COLI                         IYSDLTAGRIDAAFQDEVAASEGFLKQPVGKDYKFGGPSVKDEKLFGVGT
                                        :   * :    .        .:                        

V_Harveyi_PATH                      AWPFVDNEKGRKLQAEVNKALAEMRADGTVEKISVKWFGADITK----
B_subtilis_YXEM                     AFPFAKDDAHDKLRKKVNKALDELRKDGTLKKLSEKYFNEDITVEQKH
FLIY_ECOLI                          GVALRK--GNEDLLKAVNDAIAEMQKDGTLQALSEKWFGADVTK----
Deinococcus_radiodurans             GIALKK--GNSALKDQIDKALTEMRSDGTFEKISQKWFGQDVGQ---P
B_subtilis_GlnH_homo_YCKK           YFTFRK--GSGEVVDQVNKALKEMKEDGTLSKISKKWFGEDVSK----
YA80_HAEIN                          AFAFLQ--GEDALITKFNQVLEALRQDGTLKQISIEWFGYDITQ----
E_coli_GlnH                         GIAFPK--GSDELRDKVNGALKTLRENGTYNEIYKKWFGTEP-K----
HISJ_E_COLI                         GMGLRK--EDNELREALNKAFAEMRADGTYEKLAKKYFDFDVYG---G
                                       : .::    :   .: .:  :: :** . :  ::*. :       


""",
        )
        counts = alignment.counts(substitution_matrix)
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (substitution score = 10664.0; 6948 aligned letters; 2353 identities; 4595 mismatches; 3745 positives; 608 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    substitution_score = 10664.0,
    aligned = 6948:
        identities = 2353,
        positives = 3745,
        mismatches = 4595.
    gaps = 608:
        left_gaps = 0:
            left_insertions = 0:
                open_left_insertions = 0,
                extend_left_insertions = 0;
            left_deletions = 0:
                open_left_deletions = 0,
                extend_left_deletions = 0;
        internal_gaps = 578:
            internal_insertions = 285:
                open_internal_insertions = 126,
                extend_internal_insertions = 159;
            internal_deletions = 293:
                open_internal_deletions = 125,
                extend_internal_deletions = 168;
        right_gaps = 30:
            right_insertions = 11:
                open_right_insertions = 8,
                extend_right_insertions = 3;
            right_deletions = 19:
                open_right_deletions = 7,
                extend_right_deletions = 12.
""",
        )
        self.assertEqual(counts.left_insertions, 0)
        self.assertEqual(counts.left_deletions, 0)
        self.assertEqual(counts.right_insertions, 11)
        self.assertEqual(counts.right_deletions, 19)
        self.assertEqual(counts.internal_insertions, 285)
        self.assertEqual(counts.internal_deletions, 293)
        self.assertEqual(counts.left_gaps, 0)
        self.assertEqual(counts.right_gaps, 30)
        self.assertEqual(counts.internal_gaps, 578)
        self.assertEqual(counts.insertions, 296)
        self.assertEqual(counts.deletions, 312)
        self.assertEqual(counts.gaps, 608)
        self.assertEqual(counts.aligned, 6948)
        self.assertEqual(counts.identities, 2353)
        self.assertEqual(counts.mismatches, 4595)
        self.assertEqual(counts.positives, 3745)
        self.check_reading_writing(path)

    def test_muscle(self):
        path = "Clustalw/muscle.aln"
        # includes the sequence length on the right hand side of each line
        with open(path) as stream:
            alignments = Align.parse(stream, "clustal")
            self.assertEqual(alignments.metadata["Program"], "MUSCLE")
            self.assertEqual(alignments.metadata["Version"], "3.8")
            alignment = next(alignments)
            with self.assertRaises(StopIteration):
                next(alignments)
        self.assertEqual(
            repr(alignment),
            "<Alignment object (3 rows x 687 columns) at 0x%x>" % id(alignment),
        )
        self.assertEqual(len(alignment), 3)
        self.assertEqual(alignment.sequences[0].id, "Test1seq")
        self.assertEqual(alignment.sequences[1].id, "AT3G20900.1-SEQ")
        self.assertEqual(alignment.sequences[2].id, "AT3G20900.1-CDS")
        self.assertEqual(
            alignment.sequences[0].seq,
            "AGTTACAATAACTGACGAAGCTAAGTAGGCTACTAATTAACGTCATCAACCTAATACATAGCACTTAGAAAAAAGTGAAGTAAGAAAATATAAAATAATAAAAGGGTGGGTTATCAATTGATAGTGTAAATCATCGTATTCCGGTGATATACCCTACCACAAAAACTCAAACCGACTTGATTCAAATCATCTCAATAAATTAGCGCCAAAATAATGAAAAAAATAATAACAAACAAAAACAAACCAAAATAAGAAAAAACATTACGCAAAACATAATAATTTACTCTTCGTTATTGTATTAACAAATCAAAGAGCTGAATTTTGATCACCTGCTAATACTACTTTCTGTATTGATCCTATATCAACGTAAACAAAGATACTAATAATTAACTAAAAGTACGTTCATCGATCGTGTTCGTTGACGAAGAAGAGCTCTATCTCCGGCGGAGCAAAGAAAACGATCTGTCTCCGTCGTAACACACGGTCGCTAGAGAAACTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCCGGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCGTGGTGACGTCAGCACCGCTGCTGGGGATGGAGAGGGAACAGAGTT",
        )
        self.assertEqual(
            alignment.sequences[1].seq,
            "ATGAACAAAGTAGCGAGGAAGAACAAAACATCAGGTGAACAAAAAAAAAACTCAATCCACATCAAAGTTACAATAACTGACGAAGCTAAGTAGGCTAGAAATTAAAGTCATCAACCTAATACATAGCACTTAGAAAAAAGTGAAGCAAGAAAATATAAAATAATAAAAGGGTGGGTTATCAATTGATAGTGTAAATCATAGTTGATTTTTGATATACCCTACCACAAAAACTCAAACCGACTTGATTCAAATCATCTCAAAAAACAAGCGCCAAAATAATGAAAAAAATAATAACAAAAACAAACAAACCAAAATAAGAAAAAACATTACGCAAAACATAATAATTTACTCTTCGTTATTGTATTAACAAATCAAAGAGATGAATTTTGATCACCTGCTAATACTACTTTCTGTATTGATCCTATATCAAAAAAAAAAAAGATACTAATAATTAACTAAAAGTACGTTCATCGATCGTGTGCGTTGACGAAGAAGAGCTCTATCTCCGGCGGAGCAAAGAAAACGATCTGTCTCCGTCGTAACACACAGTTTTTCGAGACCCTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCCGGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCCTGGTGACGTCAGCACCGCTGCTGGGGATGGAGAGGGAACAGAGTAG",
        )
        self.assertEqual(
            alignment.sequences[2].seq,
            "ATGAACAAAGTAGCGAGGAAGAACAAAACATCAGCAAAGAAAACGATCTGTCTCCGTCGTAACACACAGTTTTTCGAGACCCTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCCGGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCCTGGTGACGTCAGCACCGCTGCTGGGGATGGAGAGGGAACAGAGTAG",
        )
        self.assertEqual(
            alignment[0],
            "-----------------------------------------------------------------AGTTACAATAACTGACGAAGCTAAGTAGGCTACTAATTAACGTCATCAACCTAATACATAGCACTTAGAAAAAAGTGAAGTAAGAAAATATAAAATAATAAAAGGGTGGGTTATCAATTGATAGTGTAAATCATCGTATTCCGGTGATATACCCTACCACAAAAACTCAAACCGACTTGATTCAAATCATCTCAATAAATTAGCGCCAAAATAATGAAAAAAATAATAACAAACAAAAACAAACCAAAATAAGAAAAAACATTACGCAAAACATAATAATTTACTCTTCGTTATTGTATTAACAAATCAAAGAGCTGAATTTTGATCACCTGCTAATACTACTTTCTGTATTGATCCTATATCAACGTAAACAAAGATACTAATAATTAACTAAAAGTACGTTCATCGATCGTGTTCGTTGACGAAGAAGAGCTCTATCTCCGGCGGAGCAAAGAAAACGATCTGTCTCCGTCGTAACACACGGTCGCTAGAGAAACTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCCGGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCGTGGTGACGTCAGCACCGCTGCTGGGGATGGAGAGGGAACAGAGTT-",
        )
        self.assertEqual(
            alignment[1],
            "ATGAACAAAGTAGCGAGGAAGAACAAAACATCAGGTGAACAAAAAAAAAACTCAATCCACATCAAAGTTACAATAACTGACGAAGCTAAGTAGGCTAGAAATTAAAGTCATCAACCTAATACATAGCACTTAGAAAAAAGTGAAGCAAGAAAATATAAAATAATAAAAGGGTGGGTTATCAATTGATAGTGTAAATCATAGTTGATTTTTGATATACCCTACCACAAAAACTCAAACCGACTTGATTCAAATCATCTCAAAAAACAAGCGCCAAAATAATGAAAAAAATAATAACAAAAACAAACAAACCAAAATAAGAAAAAACATTACGCAAAACATAATAATTTACTCTTCGTTATTGTATTAACAAATCAAAGAGATGAATTTTGATCACCTGCTAATACTACTTTCTGTATTGATCCTATATCAAAAAAAAAAAAGATACTAATAATTAACTAAAAGTACGTTCATCGATCGTGTGCGTTGACGAAGAAGAGCTCTATCTCCGGCGGAGCAAAGAAAACGATCTGTCTCCGTCGTAACACACAGTTTTTCGAGACCCTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCCGGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCCTGGTGACGTCAGCACCGCTGCTGGGGATGGAGAGGGAACAGAGTAG",
        )
        self.assertEqual(
            alignment[2],
            "--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ATGAACAAAGTAGCGAGGAAGAA------------------------------CAAAACATC----------------------------------------------------------------------------------------------------------------------------------------------------------------------------AGCAAAGAAAACGATCTGTCTCCGTCGTAACACACAGTTTTTCGAGACCCTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCCGGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCCTGGTGACGTCAGCACCGCTGCTGGGGATGGAGAGGGAACAGAGTAG",
        )
        self.assertEqual(
            alignment.column_annotations["clustal_consensus"],
            "                                                                                                                                                                                                                                                                                      ***** *** **   *  ** *                               ********                                                                                                                                                                             *********************************** **   * ****  ******************************************************************************* ********************************************  ",
        )
        self.assertEqual(
            str(alignment),
            """\
Test1seq          0 ------------------------------------------------------------
AT3G20900         0 ATGAACAAAGTAGCGAGGAAGAACAAAACATCAGGTGAACAAAAAAAAAACTCAATCCAC
AT3G20900         0 ------------------------------------------------------------

Test1seq          0 -----AGTTACAATAACTGACGAAGCTAAGTAGGCTACTAATTAACGTCATCAACCTAAT
AT3G20900        60 ATCAAAGTTACAATAACTGACGAAGCTAAGTAGGCTAGAAATTAAAGTCATCAACCTAAT
AT3G20900         0 ------------------------------------------------------------

Test1seq         55 ACATAGCACTTAGAAAAAAGTGAAGTAAGAAAATATAAAATAATAAAAGGGTGGGTTATC
AT3G20900       120 ACATAGCACTTAGAAAAAAGTGAAGCAAGAAAATATAAAATAATAAAAGGGTGGGTTATC
AT3G20900         0 ------------------------------------------------------------

Test1seq        115 AATTGATAGTGTAAATCATCGTATTCCGGTGATATACCCTACCACAAAAACTCAAACCGA
AT3G20900       180 AATTGATAGTGTAAATCATAGTTGATTTTTGATATACCCTACCACAAAAACTCAAACCGA
AT3G20900         0 ------------------------------------------------------------

Test1seq        175 CTTGATTCAAATCATCTCAATAAATTAGCGCCAAAATAATGAAAAAAATAATAACAAACA
AT3G20900       240 CTTGATTCAAATCATCTCAAAAAACAAGCGCCAAAATAATGAAAAAAATAATAACAAAAA
AT3G20900         0 --------------------------------------ATGAACAAAGTAGCGAGGAAGA

Test1seq        235 AAAACAAACCAAAATAAGAAAAAACATTACGCAAAACATAATAATTTACTCTTCGTTATT
AT3G20900       300 CAAACAAACCAAAATAAGAAAAAACATTACGCAAAACATAATAATTTACTCTTCGTTATT
AT3G20900        22 A------------------------------CAAAACATC--------------------

Test1seq        295 GTATTAACAAATCAAAGAGCTGAATTTTGATCACCTGCTAATACTACTTTCTGTATTGAT
AT3G20900       360 GTATTAACAAATCAAAGAGATGAATTTTGATCACCTGCTAATACTACTTTCTGTATTGAT
AT3G20900        32 ------------------------------------------------------------

Test1seq        355 CCTATATCAACGTAAACAAAGATACTAATAATTAACTAAAAGTACGTTCATCGATCGTGT
AT3G20900       420 CCTATATCAAAAAAAAAAAAGATACTAATAATTAACTAAAAGTACGTTCATCGATCGTGT
AT3G20900        32 ------------------------------------------------------------

Test1seq        415 TCGTTGACGAAGAAGAGCTCTATCTCCGGCGGAGCAAAGAAAACGATCTGTCTCCGTCGT
AT3G20900       480 GCGTTGACGAAGAAGAGCTCTATCTCCGGCGGAGCAAAGAAAACGATCTGTCTCCGTCGT
AT3G20900        32 --------------------------------AGCAAAGAAAACGATCTGTCTCCGTCGT

Test1seq        475 AACACACGGTCGCTAGAGAAACTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCC
AT3G20900       540 AACACACAGTTTTTCGAGACCCTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCC
AT3G20900        60 AACACACAGTTTTTCGAGACCCTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCC

Test1seq        535 GGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCGTGGTGACGTCAGCACCGCT
AT3G20900       600 GGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCCTGGTGACGTCAGCACCGCT
AT3G20900       120 GGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCCTGGTGACGTCAGCACCGCT

Test1seq        595 GCTGGGGATGGAGAGGGAACAGAGTT- 621
AT3G20900       660 GCTGGGGATGGAGAGGGAACAGAGTAG 687
AT3G20900       180 GCTGGGGATGGAGAGGGAACAGAGTAG 207
""",
        )
        self.assertEqual(
            format(alignment, "clustal"),
            """\
Test1seq                            --------------------------------------------------
AT3G20900.1-SEQ                     ATGAACAAAGTAGCGAGGAAGAACAAAACATCAGGTGAACAAAAAAAAAA
AT3G20900.1-CDS                     --------------------------------------------------
                                                                                      

Test1seq                            ---------------AGTTACAATAACTGACGAAGCTAAGTAGGCTACTA
AT3G20900.1-SEQ                     CTCAATCCACATCAAAGTTACAATAACTGACGAAGCTAAGTAGGCTAGAA
AT3G20900.1-CDS                     --------------------------------------------------
                                                                                      

Test1seq                            ATTAACGTCATCAACCTAATACATAGCACTTAGAAAAAAGTGAAGTAAGA
AT3G20900.1-SEQ                     ATTAAAGTCATCAACCTAATACATAGCACTTAGAAAAAAGTGAAGCAAGA
AT3G20900.1-CDS                     --------------------------------------------------
                                                                                      

Test1seq                            AAATATAAAATAATAAAAGGGTGGGTTATCAATTGATAGTGTAAATCATC
AT3G20900.1-SEQ                     AAATATAAAATAATAAAAGGGTGGGTTATCAATTGATAGTGTAAATCATA
AT3G20900.1-CDS                     --------------------------------------------------
                                                                                      

Test1seq                            GTATTCCGGTGATATACCCTACCACAAAAACTCAAACCGACTTGATTCAA
AT3G20900.1-SEQ                     GTTGATTTTTGATATACCCTACCACAAAAACTCAAACCGACTTGATTCAA
AT3G20900.1-CDS                     --------------------------------------------------
                                                                                      

Test1seq                            ATCATCTCAATAAATTAGCGCCAAAATAATGAAAAAAATAATAACAAACA
AT3G20900.1-SEQ                     ATCATCTCAAAAAACAAGCGCCAAAATAATGAAAAAAATAATAACAAAAA
AT3G20900.1-CDS                     ----------------------------ATGAACAAAGTAGCGAGGAAGA
                                                                ***** *** **   *  ** *

Test1seq                            AAAACAAACCAAAATAAGAAAAAACATTACGCAAAACATAATAATTTACT
AT3G20900.1-SEQ                     CAAACAAACCAAAATAAGAAAAAACATTACGCAAAACATAATAATTTACT
AT3G20900.1-CDS                     A------------------------------CAAAACATC----------
                                                                   ********           

Test1seq                            CTTCGTTATTGTATTAACAAATCAAAGAGCTGAATTTTGATCACCTGCTA
AT3G20900.1-SEQ                     CTTCGTTATTGTATTAACAAATCAAAGAGATGAATTTTGATCACCTGCTA
AT3G20900.1-CDS                     --------------------------------------------------
                                                                                      

Test1seq                            ATACTACTTTCTGTATTGATCCTATATCAACGTAAACAAAGATACTAATA
AT3G20900.1-SEQ                     ATACTACTTTCTGTATTGATCCTATATCAAAAAAAAAAAAGATACTAATA
AT3G20900.1-CDS                     --------------------------------------------------
                                                                                      

Test1seq                            ATTAACTAAAAGTACGTTCATCGATCGTGTTCGTTGACGAAGAAGAGCTC
AT3G20900.1-SEQ                     ATTAACTAAAAGTACGTTCATCGATCGTGTGCGTTGACGAAGAAGAGCTC
AT3G20900.1-CDS                     --------------------------------------------------
                                                                                      

Test1seq                            TATCTCCGGCGGAGCAAAGAAAACGATCTGTCTCCGTCGTAACACACGGT
AT3G20900.1-SEQ                     TATCTCCGGCGGAGCAAAGAAAACGATCTGTCTCCGTCGTAACACACAGT
AT3G20900.1-CDS                     ------------AGCAAAGAAAACGATCTGTCTCCGTCGTAACACACAGT
                                                *********************************** **

Test1seq                            CGCTAGAGAAACTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCC
AT3G20900.1-SEQ                     TTTTCGAGACCCTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCC
AT3G20900.1-CDS                     TTTTCGAGACCCTTTGCTTCTTCGGCGCCGGTGGACACGTCAGCATCTCC
                                       * ****  ***************************************

Test1seq                            GGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCGTGGTGACGT
AT3G20900.1-SEQ                     GGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCCTGGTGACGT
AT3G20900.1-CDS                     GGTATCCTAGACTTCTTGGCTTTCGGGGTACAACAACCGCCTGGTGACGT
                                    **************************************** *********

Test1seq                            CAGCACCGCTGCTGGGGATGGAGAGGGAACAGAGTT-
AT3G20900.1-SEQ                     CAGCACCGCTGCTGGGGATGGAGAGGGAACAGAGTAG
AT3G20900.1-CDS                     CAGCACCGCTGCTGGGGATGGAGAGGGAACAGAGTAG
                                    ***********************************  


""",  # noqa: W293
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (1034 aligned letters; 974 identities; 60 mismatches; 962 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 1034:
        identities = 974,
        mismatches = 60.
    gaps = 962:
        left_gaps = 556:
            left_insertions = 65:
                open_left_insertions = 1,
                extend_left_insertions = 64;
            left_deletions = 491:
                open_left_deletions = 2,
                extend_left_deletions = 489;
        internal_gaps = 404:
            internal_insertions = 0:
                open_internal_insertions = 0,
                extend_internal_insertions = 0;
            internal_deletions = 404:
                open_internal_deletions = 4,
                extend_internal_deletions = 400;
        right_gaps = 2:
            right_insertions = 2:
                open_right_insertions = 2,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 65)
        self.assertEqual(counts.left_deletions, 491)
        self.assertEqual(counts.right_insertions, 2)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 0)
        self.assertEqual(counts.internal_deletions, 404)
        self.assertEqual(counts.left_gaps, 556)
        self.assertEqual(counts.right_gaps, 2)
        self.assertEqual(counts.internal_gaps, 404)
        self.assertEqual(counts.insertions, 67)
        self.assertEqual(counts.deletions, 895)
        self.assertEqual(counts.gaps, 962)
        self.assertEqual(counts.aligned, 1034)
        self.assertEqual(counts.identities, 974)
        self.assertEqual(counts.mismatches, 60)
        self.check_reading_writing(path)

    def test_kalign(self):
        """Make sure we can parse the Kalign header."""
        path = "Clustalw/kalign.aln"
        with open(path) as stream:
            alignments = Align.parse(stream, "clustal")
            self.assertEqual(alignments.metadata["Program"], "Kalign")
            self.assertEqual(alignments.metadata["Version"], "2.0")
            alignment = next(alignments)
            with self.assertRaises(StopIteration):
                next(alignments)
        self.assertTrue(
            np.array_equal(
                np.array(alignment, "U"),
                # fmt: off
np.array([['G', 'C', 'T', 'G', 'G', 'G', 'G', 'A', 'T', 'G', 'G', 'A', 'G', 'A',
           'G', 'G', 'G', 'A', 'A', 'C', 'A', 'G', 'A', 'G', 'T', '-', 'T'],
          ['G', 'C', 'T', 'G', 'G', 'G', 'G', 'A', 'T', 'G', 'G', 'A', 'G', 'A',
           'G', 'G', 'G', 'A', 'A', 'C', 'A', 'G', 'A', 'G', 'T', 'A', 'G']
         ], dtype='U')
                # fmt: on
            )
        )
        self.assertEqual(
            repr(alignment),
            "<Alignment object (2 rows x 27 columns) at 0x%x>" % id(alignment),
        )
        self.assertEqual(len(alignment), 2)
        self.assertEqual(alignment.sequences[0].id, "Test1seq")
        self.assertEqual(alignment.sequences[1].id, "AT3G20900")
        self.assertEqual(alignment.sequences[0].seq, "GCTGGGGATGGAGAGGGAACAGAGTT")
        self.assertEqual(alignment.sequences[1].seq, "GCTGGGGATGGAGAGGGAACAGAGTAG")
        self.assertEqual(alignment[0], "GCTGGGGATGGAGAGGGAACAGAGT-T")
        self.assertEqual(alignment[1], "GCTGGGGATGGAGAGGGAACAGAGTAG")
        self.assertEqual(
            str(alignment),
            """\
Test1seq          0 GCTGGGGATGGAGAGGGAACAGAGT-T 26
                  0 |||||||||||||||||||||||||-. 27
AT3G20900         0 GCTGGGGATGGAGAGGGAACAGAGTAG 27
""",
        )
        self.assertEqual(
            format(alignment, "clustal"),
            """\
Test1seq                            GCTGGGGATGGAGAGGGAACAGAGT-T
AT3G20900                           GCTGGGGATGGAGAGGGAACAGAGTAG


""",
        )
        counts = alignment.counts()
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (26 aligned letters; 25 identities; 1 mismatches; 1 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    aligned = 26:
        identities = 25,
        mismatches = 1.
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
        self.assertEqual(counts.aligned, 26)
        self.assertEqual(counts.identities, 25)
        self.assertEqual(counts.mismatches, 1)
        self.check_reading_writing(path)

    def test_probcons(self):
        path = "Clustalw/probcons.aln"
        # example taken from the PROBCONS documentation
        with open(path) as stream:
            alignments = Align.parse(stream, "clustal")
            self.assertEqual(alignments.metadata["Program"], "PROBCONS")
            self.assertEqual(alignments.metadata["Version"], "1.12")
            alignment = next(alignments)
            with self.assertRaises(StopIteration):
                next(alignments)
        self.assertTrue(
            np.array_equal(
                np.array(alignment, "U"),
                # fmt: off
np.array([['D', '-', 'V', 'L', 'L', 'G', 'A', 'N', 'G', 'G', 'V', 'L', 'V',
           'F', 'E', 'P', 'N', 'D', 'F', 'S', 'V', 'K', 'A', 'G', 'E', 'T',
           'I', 'T', 'F', 'K', 'N', 'N', 'A', 'G', 'Y', 'P', 'H', 'N', 'V',
           'V', 'F', 'D', 'E', 'D', 'A', 'V', 'P', 'S', 'G', '-', 'V', 'D',
           '-', 'V', 'S', 'K', 'I', 'S', 'Q', 'E', 'E', 'Y', 'L', 'T', 'A',
           'P', 'G', 'E', 'T', 'F', 'S', 'V', 'T', 'L', 'T', 'V', '-', '-',
           '-', 'P', 'G', 'T', 'Y', 'G', 'F', 'Y', 'C', 'E', 'P', 'H', 'A',
           'G', 'A', 'G', 'M', 'V', 'G', 'K', 'V', 'T', 'V'],
          ['-', '-', 'V', 'K', 'L', 'G', 'A', 'D', 'S', 'G', 'A', 'L', 'E',
           'F', 'V', 'P', 'K', 'T', 'L', 'T', 'I', 'K', 'S', 'G', 'E', 'T',
           'V', 'N', 'F', 'V', 'N', 'N', 'A', 'G', 'F', 'P', 'H', 'N', 'I',
           'V', 'F', 'D', 'E', 'D', 'A', 'I', 'P', 'S', 'G', '-', 'V', 'N',
           '-', 'A', 'D', 'A', 'I', 'S', 'R', 'D', 'D', 'Y', 'L', 'N', 'A',
           'P', 'G', 'E', 'T', 'Y', 'S', 'V', 'K', 'L', 'T', 'A', '-', '-',
           '-', 'A', 'G', 'E', 'Y', 'G', 'Y', 'Y', 'C', 'E', 'P', 'H', 'Q',
           'G', 'A', 'G', 'M', 'V', 'G', 'K', 'I', 'I', 'V'],
          ['-', '-', 'V', 'K', 'L', 'G', 'S', 'D', 'K', 'G', 'L', 'L', 'V',
           'F', 'E', 'P', 'A', 'K', 'L', 'T', 'I', 'K', 'P', 'G', 'D', 'T',
           'V', 'E', 'F', 'L', 'N', 'N', 'K', 'V', 'P', 'P', 'H', 'N', 'V',
           'V', 'F', 'D', 'A', 'A', 'L', 'N', 'P', 'A', 'K', 'S', 'A', 'D',
           'L', 'A', 'K', 'S', 'L', 'S', 'H', 'K', 'Q', 'L', 'L', 'M', 'S',
           'P', 'G', 'Q', 'S', 'T', 'S', 'T', 'T', 'F', 'P', 'A', 'D', 'A',
           'P', 'A', 'G', 'E', 'Y', 'T', 'F', 'Y', 'C', 'E', 'P', 'H', 'R',
           'G', 'A', 'G', 'M', 'V', 'G', 'K', 'I', 'T', 'V'],
          ['V', 'Q', 'I', 'K', 'M', 'G', 'T', 'D', 'K', 'Y', 'A', 'P', 'L',
           'Y', 'E', 'P', 'K', 'A', 'L', 'S', 'I', 'S', 'A', 'G', 'D', 'T',
           'V', 'E', 'F', 'V', 'M', 'N', 'K', 'V', 'G', 'P', 'H', 'N', 'V',
           'I', 'F', 'D', 'K', '-', '-', 'V', 'P', 'A', 'G', '-', 'E', 'S',
           '-', 'A', 'P', 'A', 'L', 'S', 'N', 'T', 'K', 'L', 'R', 'I', 'A',
           'P', 'G', 'S', 'F', 'Y', 'S', 'V', 'T', 'L', 'G', 'T', '-', '-',
           '-', 'P', 'G', 'T', 'Y', 'S', 'F', 'Y', 'C', 'T', 'P', 'H', 'R',
           'G', 'A', 'G', 'M', 'V', 'G', 'T', 'I', 'T', 'V'],
          ['V', 'H', 'M', 'L', 'N', 'K', 'G', 'K', 'D', 'G', 'A', 'M', 'V',
           'F', 'E', 'P', 'A', 'S', 'L', 'K', 'V', 'A', 'P', 'G', 'D', 'T',
           'V', 'T', 'F', 'I', 'P', 'T', 'D', 'K', '-', 'G', 'H', 'N', 'V',
           'E', 'T', 'I', 'K', 'G', 'M', 'I', 'P', 'D', 'G', '-', 'A', 'E',
           '-', 'A', '-', '-', '-', '-', '-', '-', '-', 'F', 'K', 'S', 'K',
           'I', 'N', 'E', 'N', 'Y', 'K', 'V', 'T', 'F', 'T', 'A', '-', '-',
           '-', 'P', 'G', 'V', 'Y', 'G', 'V', 'K', 'C', 'T', 'P', 'H', 'Y',
           'G', 'M', 'G', 'M', 'V', 'G', 'V', 'V', 'E', 'V']], dtype='U')
                # fmt: on
            )
        )
        self.assertEqual(
            repr(alignment),
            "<Alignment object (5 rows x 101 columns) at 0x%x>" % id(alignment),
        )
        self.assertEqual(len(alignment), 5)
        self.assertEqual(alignment.sequences[0].id, "plas_horvu")
        self.assertEqual(alignment.sequences[1].id, "plas_chlre")
        self.assertEqual(alignment.sequences[2].id, "plas_anava")
        self.assertEqual(alignment.sequences[3].id, "plas_proho")
        self.assertEqual(alignment.sequences[4].id, "azup_achcy")
        self.assertEqual(
            alignment.sequences[0].seq,
            "DVLLGANGGVLVFEPNDFSVKAGETITFKNNAGYPHNVVFDEDAVPSGVDVSKISQEEYLTAPGETFSVTLTVPGTYGFYCEPHAGAGMVGKVTV",
        )
        self.assertEqual(
            alignment.sequences[1].seq,
            "VKLGADSGALEFVPKTLTIKSGETVNFVNNAGFPHNIVFDEDAIPSGVNADAISRDDYLNAPGETYSVKLTAAGEYGYYCEPHQGAGMVGKIIV",
        )
        self.assertEqual(
            alignment.sequences[2].seq,
            "VKLGSDKGLLVFEPAKLTIKPGDTVEFLNNKVPPHNVVFDAALNPAKSADLAKSLSHKQLLMSPGQSTSTTFPADAPAGEYTFYCEPHRGAGMVGKITV",
        )
        self.assertEqual(
            alignment.sequences[3].seq,
            "VQIKMGTDKYAPLYEPKALSISAGDTVEFVMNKVGPHNVIFDKVPAGESAPALSNTKLRIAPGSFYSVTLGTPGTYSFYCTPHRGAGMVGTITV",
        )
        self.assertEqual(
            alignment.sequences[4].seq,
            "VHMLNKGKDGAMVFEPASLKVAPGDTVTFIPTDKGHNVETIKGMIPDGAEAFKSKINENYKVTFTAPGVYGVKCTPHYGMGMVGVVEV",
        )
        self.assertEqual(
            alignment.column_annotations["clustal_consensus"],
            " ::    .     : *  :.: .*:*: *  .    **:       *    . .  :*. .     ..  ...: .   .* *   * ** * **** : *",
        )
        self.assertEqual(
            alignment[0],
            "D-VLLGANGGVLVFEPNDFSVKAGETITFKNNAGYPHNVVFDEDAVPSG-VD-VSKISQEEYLTAPGETFSVTLTV---PGTYGFYCEPHAGAGMVGKVTV",
        )
        self.assertEqual(
            alignment[1],
            "--VKLGADSGALEFVPKTLTIKSGETVNFVNNAGFPHNIVFDEDAIPSG-VN-ADAISRDDYLNAPGETYSVKLTA---AGEYGYYCEPHQGAGMVGKIIV",
        )
        self.assertEqual(
            alignment[2],
            "--VKLGSDKGLLVFEPAKLTIKPGDTVEFLNNKVPPHNVVFDAALNPAKSADLAKSLSHKQLLMSPGQSTSTTFPADAPAGEYTFYCEPHRGAGMVGKITV",
        )
        self.assertEqual(
            alignment[3],
            "VQIKMGTDKYAPLYEPKALSISAGDTVEFVMNKVGPHNVIFDK--VPAG-ES-APALSNTKLRIAPGSFYSVTLGT---PGTYSFYCTPHRGAGMVGTITV",
        )
        self.assertEqual(
            alignment[4],
            "VHMLNKGKDGAMVFEPASLKVAPGDTVTFIPTDK-GHNVETIKGMIPDG-AE-A-------FKSKINENYKVTFTA---PGVYGVKCTPHYGMGMVGVVEV",
        )
        self.assertEqual(
            str(alignment),
            """\
plas_horv         0 D-VLLGANGGVLVFEPNDFSVKAGETITFKNNAGYPHNVVFDEDAVPSG-VD-VSKISQE
plas_chlr         0 --VKLGADSGALEFVPKTLTIKSGETVNFVNNAGFPHNIVFDEDAIPSG-VN-ADAISRD
plas_anav         0 --VKLGSDKGLLVFEPAKLTIKPGDTVEFLNNKVPPHNVVFDAALNPAKSADLAKSLSHK
plas_proh         0 VQIKMGTDKYAPLYEPKALSISAGDTVEFVMNKVGPHNVIFDK--VPAG-ES-APALSNT
azup_achc         0 VHMLNKGKDGAMVFEPASLKVAPGDTVTFIPTDK-GHNVETIKGMIPDG-AE-A------

plas_horv        57 EYLTAPGETFSVTLTV---PGTYGFYCEPHAGAGMVGKVTV 95
plas_chlr        56 DYLNAPGETYSVKLTA---AGEYGYYCEPHQGAGMVGKIIV 94
plas_anav        58 QLLMSPGQSTSTTFPADAPAGEYTFYCEPHRGAGMVGKITV 99
plas_proh        56 KLRIAPGSFYSVTLGT---PGTYSFYCTPHRGAGMVGTITV 94
azup_achc        51 -FKSKINENYKVTFTA---PGVYGVKCTPHYGMGMVGVVEV 88
""",
        )
        self.assertEqual(
            format(alignment, "clustal"),
            """\
plas_horvu                          D-VLLGANGGVLVFEPNDFSVKAGETITFKNNAGYPHNVVFDEDAVPSG-
plas_chlre                          --VKLGADSGALEFVPKTLTIKSGETVNFVNNAGFPHNIVFDEDAIPSG-
plas_anava                          --VKLGSDKGLLVFEPAKLTIKPGDTVEFLNNKVPPHNVVFDAALNPAKS
plas_proho                          VQIKMGTDKYAPLYEPKALSISAGDTVEFVMNKVGPHNVIFDK--VPAG-
azup_achcy                          VHMLNKGKDGAMVFEPASLKVAPGDTVTFIPTDK-GHNVETIKGMIPDG-
                                     ::    .     : *  :.: .*:*: *  .    **:       *   

plas_horvu                          VD-VSKISQEEYLTAPGETFSVTLTV---PGTYGFYCEPHAGAGMVGKVT
plas_chlre                          VN-ADAISRDDYLNAPGETYSVKLTA---AGEYGYYCEPHQGAGMVGKII
plas_anava                          ADLAKSLSHKQLLMSPGQSTSTTFPADAPAGEYTFYCEPHRGAGMVGKIT
plas_proho                          ES-APALSNTKLRIAPGSFYSVTLGT---PGTYSFYCTPHRGAGMVGTIT
azup_achcy                          AE-A-------FKSKINENYKVTFTA---PGVYGVKCTPHYGMGMVGVVE
                                     . .  :*. .     ..  ...: .   .* *   * ** * **** : 

plas_horvu                          V
plas_chlre                          V
plas_anava                          V
plas_proho                          V
azup_achcy                          V
                                    *


""",
        )
        counts = alignment.counts(substitution_matrix)
        self.assertEqual(
            repr(counts),
            "<AlignmentCounts object (substitution score = 2197.0; 904 aligned letters; 427 identities; 477 mismatches; 554 positives; 72 gaps) at 0x%x>"
            % id(counts),
        )
        self.assertEqual(
            str(counts),
            """\
AlignmentCounts object with
    substitution_score = 2197.0,
    aligned = 904:
        identities = 427,
        positives = 554,
        mismatches = 477.
    gaps = 72:
        left_gaps = 10:
            left_insertions = 8:
                open_left_insertions = 4,
                extend_left_insertions = 4;
            left_deletions = 2:
                open_left_deletions = 2,
                extend_left_deletions = 0;
        internal_gaps = 62:
            internal_insertions = 14:
                open_internal_insertions = 9,
                extend_internal_insertions = 5;
            internal_deletions = 48:
                open_internal_deletions = 17,
                extend_internal_deletions = 31;
        right_gaps = 0:
            right_insertions = 0:
                open_right_insertions = 0,
                extend_right_insertions = 0;
            right_deletions = 0:
                open_right_deletions = 0,
                extend_right_deletions = 0.
""",
        )
        self.assertEqual(counts.left_insertions, 8)
        self.assertEqual(counts.left_deletions, 2)
        self.assertEqual(counts.right_insertions, 0)
        self.assertEqual(counts.right_deletions, 0)
        self.assertEqual(counts.internal_insertions, 14)
        self.assertEqual(counts.internal_deletions, 48)
        self.assertEqual(counts.left_gaps, 10)
        self.assertEqual(counts.right_gaps, 0)
        self.assertEqual(counts.internal_gaps, 62)
        self.assertEqual(counts.insertions, 22)
        self.assertEqual(counts.deletions, 50)
        self.assertEqual(counts.gaps, 72)
        self.assertEqual(counts.aligned, 904)
        self.assertEqual(counts.identities, 427)
        self.assertEqual(counts.mismatches, 477)
        self.assertEqual(counts.positives, 554)
        self.check_reading_writing(path)

    def test_empty(self):
        """Checking empty file."""
        stream = StringIO()
        with self.assertRaises(ValueError):
            Align.parse(stream, "clustal")


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
