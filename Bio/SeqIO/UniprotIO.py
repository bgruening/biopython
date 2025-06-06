# Copyright 2010 by Andrea Pierleoni
# Revisions copyright 2010, 2016 by Peter Cock
# All rights reserved.
#
# This file is part of the Biopython distribution and governed by your
# choice of the "Biopython License Agreement" or the "BSD 3-Clause License".
# Please see the LICENSE file that should have been included as part of this
# package.
"""Bio.SeqIO support for the "uniprot-xml" file format.

See Also:
http://www.uniprot.org

The UniProt XML format essentially replaces the old plain text file format
originally introduced by SwissProt ("swiss" format in Bio.SeqIO).

"""

import warnings
from xml.etree import ElementTree
from xml.parsers.expat import errors

from Bio import BiopythonDeprecationWarning, SeqFeature
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from .Interfaces import SequenceIterator, _BytesIOSource

NS = "{http://uniprot.org/uniprot}"
REFERENCE_JOURNAL = "%(name)s %(volume)s:%(first)s-%(last)s(%(pub_date)s)"


class UniprotIterator(SequenceIterator):
    """Parser for UniProt XML files, returning SeqRecord objects."""

    modes = "bt"

    def __init__(
        self,
        source: _BytesIOSource,
        alphabet: None = None,
        return_raw_comments: bool = False,
    ) -> None:
        """Iterate over UniProt XML as SeqRecord objects.

        parses an XML entry at a time from any UniProt XML file
        returns a SeqRecord for each iteration

        Arguments:
         - source   - input stream opened in binary mode, or a path to a file
         - alphabet - optional alphabet, not used. Leave as None.
         - return_raw_comments - if True, return comment fields as complete XML
           to allow further processing.

        This generator can be used in Bio.SeqIO.
        """
        if alphabet is not None:
            raise ValueError("The alphabet argument is no longer supported")
        super().__init__(source, fmt="UniProt XML")
        if self.mode == "t":
            warnings.warn(
                "Opening a UniProt XML file in text mode is "
                "deprecated, as it may lead to garbled characters. "
                "We recommend opening the file in binary mode; "
                "parsing UniProt XML files opened in text mode will "
                "no longer be supported in a future release of "
                "Biopython.",
                BiopythonDeprecationWarning,
            )
        self.return_raw_comments = return_raw_comments
        self._data = ElementTree.iterparse(
            self.stream, events=("start", "start-ns", "end")
        )

    def __next__(self):
        try:
            for event, elem in self._data:
                if event == "start-ns" and not (
                    elem[1].startswith("http://www.w3.org/") or NS == f"{{{elem[1]}}}"
                ):
                    raise ValueError(
                        f"SeqIO format 'uniprot-xml' only parses xml with namespace: {NS} but xml has namespace: {{{elem[1]}}}"
                    )
                if event == "end" and elem.tag == NS + "entry":
                    record = self._create_record(elem)
                    elem.clear()
                    return record
            raise StopIteration
        except ElementTree.ParseError as exception:
            if errors.messages[exception.code] == errors.XML_ERROR_NO_ELEMENTS:
                assert exception.position == (1, 0)  # line 1, column 0
                raise ValueError("Empty file.") from None
            else:
                raise

    def _parse_name(self, element):
        self._record.name = element.text
        self._record.dbxrefs.append(self._dbname + ":" + element.text)

    def _parse_protein(self, element):
        """Parse protein names (PRIVATE)."""
        descr_set = False
        for protein_element in element:
            if protein_element.tag in [
                NS + "recommendedName",
                NS + "submittedName",
                NS + "alternativeName",
            ]:  # recommendedName tag are parsed before
                # use protein fields for name and description
                for rec_name in protein_element:
                    ann_key = "%s_%s" % (
                        protein_element.tag.replace(NS, ""),
                        rec_name.tag.replace(NS, ""),
                    )
                    self._append_to_annotations(ann_key, rec_name.text)
                    if (rec_name.tag == NS + "fullName") and not descr_set:
                        self._record.description = rec_name.text
                        descr_set = True
            elif protein_element.tag == NS + "component":
                pass  # not parsed
            elif protein_element.tag == NS + "domain":
                pass  # not parsed

    def _append_to_annotations(self, key, value):
        annotations = self._record.annotations
        if key not in annotations:
            annotations[key] = []
        if value not in annotations[key]:
            annotations[key].append(value)

    def _parse_accession(self, element):
        self._append_to_annotations(
            "accessions", element.text
        )  # to cope with SwissProt plain text parser
        self._record.dbxrefs.append(self._dbname + ":" + element.text)

    def _parse_gene(self, element):
        for genename_element in element:
            if "type" in genename_element.attrib:
                ann_key = "gene_%s_%s" % (
                    genename_element.tag.replace(NS, ""),
                    genename_element.attrib["type"],
                )
                if genename_element.attrib["type"] == "primary":
                    self._record.annotations[ann_key] = genename_element.text
                else:
                    self._append_to_annotations(ann_key, genename_element.text)

    def _parse_organism(self, element):
        organism_name = com_name = sci_name = ""
        for organism_element in element:
            if organism_element.tag == NS + "name":
                if organism_element.text:
                    if organism_element.attrib["type"] == "scientific":
                        sci_name = organism_element.text
                    elif organism_element.attrib["type"] == "common":
                        com_name = organism_element.text
                    else:
                        # e.g. synonym
                        self._append_to_annotations(
                            "organism_name", organism_element.text
                        )
            elif organism_element.tag == NS + "dbReference":
                self._record.dbxrefs.append(
                    organism_element.attrib["type"]
                    + ":"
                    + organism_element.attrib["id"]
                )
            elif organism_element.tag == NS + "lineage":
                for taxon_element in organism_element:
                    if taxon_element.tag == NS + "taxon":
                        self._append_to_annotations("taxonomy", taxon_element.text)
        if sci_name and com_name:
            organism_name = f"{sci_name} ({com_name})"
        elif sci_name:
            organism_name = sci_name
        elif com_name:
            organism_name = com_name
        self._record.annotations["organism"] = organism_name

    def _parse_reference(self, element):
        reference = SeqFeature.Reference()
        authors = []
        scopes = []
        tissues = []
        journal_name = ""
        pub_type = ""
        pub_date = ""
        for ref_element in element:
            if ref_element.tag == NS + "citation":
                pub_type = ref_element.attrib["type"]
                if pub_type == "submission":
                    pub_type += " to the " + ref_element.attrib["db"]
                if "name" in ref_element.attrib:
                    journal_name = ref_element.attrib["name"]
                pub_date = ref_element.attrib.get("date", "")
                j_volume = ref_element.attrib.get("volume", "")
                j_first = ref_element.attrib.get("first", "")
                j_last = ref_element.attrib.get("last", "")
                for cit_element in ref_element:
                    if cit_element.tag == NS + "title":
                        reference.title = cit_element.text
                    elif cit_element.tag == NS + "authorList":
                        for person_element in cit_element:
                            authors.append(person_element.attrib["name"])
                    elif cit_element.tag == NS + "dbReference":
                        self._record.dbxrefs.append(
                            cit_element.attrib["type"] + ":" + cit_element.attrib["id"]
                        )
                        if cit_element.attrib["type"] == "PubMed":
                            reference.pubmed_id = cit_element.attrib["id"]
                        elif ref_element.attrib["type"] == "MEDLINE":
                            reference.medline_id = cit_element.attrib["id"]
            elif ref_element.tag == NS + "scope":
                scopes.append(ref_element.text)
            elif ref_element.tag == NS + "source":
                for source_element in ref_element:
                    if source_element.tag == NS + "tissue":
                        tissues.append(source_element.text)
        if scopes:
            scopes_str = "Scope: " + ", ".join(scopes)
        else:
            scopes_str = ""
        if tissues:
            tissues_str = "Tissue: " + ", ".join(tissues)
        else:
            tissues_str = ""

        # locations cannot be parsed since they are actually written in
        # free text inside scopes so all the references are put in the
        # annotation.
        reference.location = []
        reference.authors = ", ".join(authors)
        if journal_name:
            if pub_date and j_volume and j_first and j_last:
                reference.journal = REFERENCE_JOURNAL % {
                    "name": journal_name,
                    "volume": j_volume,
                    "first": j_first,
                    "last": j_last,
                    "pub_date": pub_date,
                }
            else:
                reference.journal = journal_name
        reference.comment = " | ".join((pub_type, pub_date, scopes_str, tissues_str))
        self._append_to_annotations("references", reference)

    def _parse_comment(self, element):
        """Parse comments (PRIVATE).

        Comment fields are very heterogeneus. each type has his own (frequently mutated) schema.
        To store all the contained data, more complex data structures are needed, such as
        annotated dictionaries. This is left to end user, by optionally setting:

        return_raw_comments=True

        The original XML is returned in the annotation fields.

        Available comment types at december 2009:
         - "allergen"
         - "alternative products"
         - "biotechnology"
         - "biophysicochemical properties"
         - "catalytic activity"
         - "caution"
         - "cofactor"
         - "developmental stage"
         - "disease"
         - "domain"
         - "disruption phenotype"
         - "enzyme regulation"
         - "function"
         - "induction"
         - "miscellaneous"
         - "pathway"
         - "pharmaceutical"
         - "polymorphism"
         - "PTM"
         - "RNA editing"
         - "similarity"
         - "subcellular location"
         - "sequence caution"
         - "subunit"
         - "tissue specificity"
         - "toxic dose"
         - "online information"
         - "mass spectrometry"
         - "interaction"

        """
        simple_comments = [
            "allergen",
            "biotechnology",
            "biophysicochemical properties",
            "catalytic activity",
            "caution",
            "cofactor",
            "developmental stage",
            "disease",
            "domain",
            "disruption phenotype",
            "enzyme regulation",
            "function",
            "induction",
            "miscellaneous",
            "pathway",
            "pharmaceutical",
            "polymorphism",
            "PTM",
            "RNA editing",  # positions not parsed
            "similarity",
            "subunit",
            "tissue specificity",
            "toxic dose",
        ]

        if element.attrib["type"] in simple_comments:
            ann_key = f"comment_{element.attrib['type'].replace(' ', '')}"
            for text_element in element.iter(NS + "text"):
                if text_element.text:
                    self._append_to_annotations(ann_key, text_element.text)
        elif element.attrib["type"] == "subcellular location":
            for subloc_element in element.iter(NS + "subcellularLocation"):
                for el in subloc_element:
                    if el.text:
                        ann_key = "comment_%s_%s" % (
                            element.attrib["type"].replace(" ", ""),
                            el.tag.replace(NS, ""),
                        )
                        self._append_to_annotations(ann_key, el.text)
        elif element.attrib["type"] == "interaction":
            for interact_element in element.iter(NS + "interactant"):
                ann_key = f"comment_{element.attrib['type']}_intactId"
                self._append_to_annotations(
                    ann_key, interact_element.attrib["intactId"]
                )
        elif element.attrib["type"] == "alternative products":
            for alt_element in element.iter(NS + "isoform"):
                ann_key = "comment_%s_isoform" % element.attrib["type"].replace(" ", "")
                for id_element in alt_element.iter(NS + "id"):
                    self._append_to_annotations(ann_key, id_element.text)
        elif element.attrib["type"] == "mass spectrometry":
            ann_key = f"comment_{element.attrib['type'].replace(' ', '')}"
            start = end = 0
            for el in element.iter(NS + "location"):
                pos_els = list(el.iter(NS + "position"))
                # this try should be avoided, maybe it is safer to skip position parsing for mass spectrometry
                try:
                    if pos_els:
                        end = int(pos_els[0].attrib["position"])
                        start = end - 1
                    else:
                        start = int(next(el.iter(NS + "begin")).attrib["position"])
                        start -= 1
                        end = int(next(el.iter(NS + "end")).attrib["position"])
                except (ValueError, KeyError):
                    # undefined positions or erroneously mapped
                    pass
            mass = element.attrib["mass"]
            method = element.attrib["method"]
            if start == end == 0:
                self._append_to_annotations(ann_key, f"undefined:{mass}|{method}")
            else:
                self._append_to_annotations(ann_key, f"{start}..{end}:{mass}|{method}")
        elif element.attrib["type"] == "sequence caution":
            pass  # not parsed: few information, complex structure
        elif element.attrib["type"] == "online information":
            for link_element in element.iter(NS + "link"):
                ann_key = f"comment_{element.attrib['type'].replace(' ', '')}"
                for id_element in link_element.iter(NS + "link"):
                    self._append_to_annotations(
                        ann_key,
                        f"{element.attrib['name']}@{link_element.attrib['uri']}",
                    )

        # return raw XML comments if needed
        if self.return_raw_comments:
            ann_key = f"comment_{element.attrib['type'].replace(' ', '')}_xml"
            self._append_to_annotations(ann_key, ElementTree.tostring(element))

    def _parse_dbReference(self, element):
        self._record.dbxrefs.append(element.attrib["type"] + ":" + element.attrib["id"])
        # e.g.
        # <dbReference type="PDB" key="11" id="2GEZ">
        #   <property value="X-ray" type="method"/>
        #   <property value="2.60 A" type="resolution"/>
        #   <property value="A/C/E/G=1-192, B/D/F/H=193-325" type="chains"/>
        # </dbReference>
        if "type" in element.attrib:
            if element.attrib["type"] == "PDB":
                method = ""
                resolution = ""
                for ref_element in element:
                    if ref_element.tag == NS + "property":
                        dat_type = ref_element.attrib["type"]
                        if dat_type == "method":
                            method = ref_element.attrib["value"]
                        if dat_type == "resolution":
                            resolution = ref_element.attrib["value"]
                        if dat_type == "chains":
                            pairs = ref_element.attrib["value"].split(",")
                            for elem in pairs:
                                pair = elem.strip().split("=")
                                if pair[1] != "-":
                                    # TODO - How best to store these, do SeqFeatures make sense?
                                    feature = SeqFeature.SeqFeature()
                                    feature.type = element.attrib["type"]
                                    feature.qualifiers["name"] = element.attrib["id"]
                                    feature.qualifiers["method"] = method
                                    feature.qualifiers["resolution"] = resolution
                                    feature.qualifiers["chains"] = pair[0].split("/")
                                    start = int(pair[1].split("-")[0]) - 1
                                    end = int(pair[1].split("-")[1])
                                    feature.location = SeqFeature.SimpleLocation(
                                        start, end
                                    )
                                    # self._record.features.append(feature)

        for ref_element in element:
            if ref_element.tag == NS + "property":
                pass  # this data cannot be fitted in a seqrecord object with a simple list. however at least ensembl and EMBL parsing can be improved to add entries in dbxrefs

    def _parse_proteinExistence(self, element):
        self._append_to_annotations("proteinExistence", element.attrib["type"])

    def _parse_keyword(self, element):
        self._append_to_annotations("keywords", element.text)

    def _parse_position(self, element, offset=0):
        try:
            position = int(element.attrib["position"]) + offset
        except KeyError:
            position = None
        status = element.attrib.get("status", "")
        if status == "unknown":
            assert position is None
            return SeqFeature.UnknownPosition()
        elif not status:
            return SeqFeature.ExactPosition(position)
        elif status == "greater than":
            return SeqFeature.AfterPosition(position)
        elif status == "less than":
            return SeqFeature.BeforePosition(position)
        elif status == "uncertain":
            return SeqFeature.UncertainPosition(position)
        else:
            raise NotImplementedError(f"Position status {status!r}")

    def _parse_feature(self, element):
        feature = SeqFeature.SeqFeature()
        for k, v in element.attrib.items():
            feature.qualifiers[k] = v
        feature.type = element.attrib.get("type", "")
        if "id" in element.attrib:
            feature.id = element.attrib["id"]
        for feature_element in element:
            if feature_element.tag == NS + "location":
                position_elements = feature_element.findall(NS + "position")
                if position_elements:
                    element = position_elements[0]
                    start_position = self._parse_position(element, -1)
                    end_position = self._parse_position(element)
                else:
                    element = feature_element.findall(NS + "begin")[0]
                    start_position = self._parse_position(element, -1)
                    element = feature_element.findall(NS + "end")[0]
                    end_position = self._parse_position(element)
                feature.location = SeqFeature.SimpleLocation(
                    start_position, end_position
                )
            elif feature_element.tag == NS + "ligand":
                # Support multiple ligand entries per feature
                name = None
                db_ref = None
                for child in feature_element:
                    if child.tag == NS + "name":
                        name = child.text.strip() if child.text else None
                    elif child.tag == NS + "dbReference":
                        db_ref = child.attrib.get("id")
                # Append to a list of ligands in qualifiers
                lig_list = feature.qualifiers.setdefault("ligands", [])
                lig_list.append({"name": name, "db_ref": db_ref})
                continue
            else:
                try:
                    feature.qualifiers[feature_element.tag.replace(NS, "")] = (
                        feature_element.text
                    )
                except Exception:  # TODO - Which exceptions?
                    pass  # skip unparsable tag
        self._record.features.append(feature)

    def _parse_evidence(self, element):
        for k, v in element.attrib.items():
            ann_key = k
            self._append_to_annotations(ann_key, v)

    def _parse_sequence(self, element):
        record = self._record
        for k, v in element.attrib.items():
            if k in ("length", "mass", "version"):
                record.annotations[f"sequence_{k}"] = int(v)
            else:
                record.annotations[f"sequence_{k}"] = v
        record.seq = Seq("".join(element.text.split()))
        record.annotations["molecule_type"] = "protein"

    def _parse_organismHost(self, element):
        for organism_element in element:
            if organism_element.tag == NS + "name":
                self._append_to_annotations("organism_host", organism_element.text)

    def _parse_geneLocation(self, element):
        self._append_to_annotations("geneLocation", element.attrib["type"])

    def _create_record(self, entry):
        assert entry.tag == NS + "entry"
        # ============================================#
        # Initialize SeqRecord
        record = SeqRecord(None, id="")
        self._record = record

        # Entry attribs parsing
        # Unknown dataset should not happen!
        self._dbname = entry.attrib.get("dataset", "UnknownDataset")
        # add attribs to annotations
        for k, v in entry.attrib.items():
            if k in ("version"):
                # original
                # self.ParsedSeqRecord.annotations["entry_%s" % k] = int(v)
                # To cope with swissProt plain text parser. this can cause errors
                # if the attrib has the same name of an other annotation
                record.annotations[k] = int(v)
            else:
                # record.annotations["entry_%s" % k] = v
                # to cope with swissProt plain text parser:
                record.annotations[k] = v

        # Top-to-bottom entry children parsing
        for element in entry:
            if element.tag == NS + "name":
                self._parse_name(element)
            elif element.tag == NS + "accession":
                self._parse_accession(element)
            elif element.tag == NS + "protein":
                self._parse_protein(element)
            elif element.tag == NS + "gene":
                self._parse_gene(element)
            elif element.tag == NS + "geneLocation":
                self._parse_geneLocation(element)
            elif element.tag == NS + "organism":
                self._parse_organism(element)
            elif element.tag == NS + "organismHost":
                self._parse_organismHost(element)
            elif element.tag == NS + "keyword":
                self._parse_keyword(element)
            elif element.tag == NS + "comment":
                self._parse_comment(element)
            elif element.tag == NS + "dbReference":
                self._parse_dbReference(element)
            elif element.tag == NS + "reference":
                self._parse_reference(element)
            elif element.tag == NS + "feature":
                self._parse_feature(element)
            elif element.tag == NS + "proteinExistence":
                self._parse_proteinExistence(element)
            elif element.tag == NS + "evidence":
                self._parse_evidence(element)
            elif element.tag == NS + "sequence":
                self._parse_sequence(element)
            else:
                pass

        # remove duplicate dbxrefs
        record.dbxrefs = sorted(set(record.dbxrefs))

        # use first accession as id
        if not record.id:
            record.id = record.annotations["accessions"][0]
        return record
