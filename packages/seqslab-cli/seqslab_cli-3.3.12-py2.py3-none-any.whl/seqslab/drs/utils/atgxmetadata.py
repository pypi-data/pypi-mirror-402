"""
Copyright (C) 2023, Atgenomix Incorporated.
All Rights Reserved.
This program is an unpublished copyrighted work which is proprietary to
Atgenomix Incorporated and contains confidential information that is not to
be reproduced or disclosed to any other person or entity without prior
written consent from Atgenomix, Inc. in each and every instance.
Unauthorized reproduction of this program as well as unauthorized
preparation of derivative works based upon the program or distribution of
copies by sale, rental, lease or lending are violations of federal copyright
laws and state trade secret laws, punishable by civil and criminal penalties.
"""

# Standard Library
import re


class AtgxMetaData:
    def __init__(self):
        self.metadata = {
            "alternate_identifiers": [],
            "dates": [],
            "types": [],
            "privacy": "",
            "primary_publication": [],
            "contributors": [],
            "licenses": [],
            "extra_properties": [],
        }

    def set_extra_properties(self, extras):
        self.metadata["extra_properties"] = extras
        return self.metadata

    def set_dates(self, dates):
        self.metadata["dates"] = dates
        return self.metadata

    def set_types(self, types):
        self.metadata["types"] = types
        return self.metadata

    def get_dictionary(self):
        return self.metadata

    @staticmethod
    def alternate_identifier_info(id, src):
        return {"identifier": id, "identifier_source": src}

    @staticmethod
    def date_info(date, type_value, type_value_iri=None):
        return {
            "date": date,
            "type": AtgxMetaData.annotation(type_value, type_value_iri),
        }

    @staticmethod
    def data_type(
        info_value=None,
        info_iri=None,
        method_value=None,
        method_iri=None,
        platform_value=None,
        platform_iri=None,
        instr_value=None,
        instr_iri=None,
    ):
        ret = {
            "information": AtgxMetaData.type_item(info_value, info_iri),
            "method": AtgxMetaData.type_item(method_value, method_iri),
            "platform": AtgxMetaData.type_item(platform_value, platform_iri),
            "instrument": AtgxMetaData.type_item(instr_value, instr_iri),
        }
        return AtgxMetaData.remove_none_from_dict(ret)

    @staticmethod
    def privacy(src):
        return {"privacy": src}

    @staticmethod
    def primary_publications(title, date, type_value="publication"):
        return {
            "title": title,
            "venue": "",
            "dates": [AtgxMetaData.date_info(date, type_value)],
            "authors": [],
        }

    @staticmethod
    def contributors():
        return []

    @staticmethod
    def licenses():
        return []

    @staticmethod
    def extra_properties(category, values=[], category_iri=None):
        primitive = (
            int,
            bool,
            float,
            str,
        )
        if type(values) in primitive:
            val = [str(values)]
        elif isinstance(values, list):
            val = values
        else:
            raise Exception(
                "Given values is not in primitive types int, bool, float, str nor list type."
            )
        ret = {"category": category, "values": val, "categoryIRI": category_iri}
        return AtgxMetaData.remove_none_from_dict(ret)

    @staticmethod
    def remove_none_from_dict(dictionary):
        for key, value in list(dictionary.items()):
            if not value:
                del dictionary[key]
            elif isinstance(value, dict):
                AtgxMetaData.remove_none_from_dict(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        AtgxMetaData.remove_none_from_dict(item)

        return dictionary

    @staticmethod
    def annotation(value=None, value_iri=None):
        ret = {"value": value, "valueIRI": value_iri}
        return AtgxMetaData.remove_none_from_dict(ret)

    @staticmethod
    def organization(name, value=None, value_iri=None):
        return {"name": name, "role": AtgxMetaData.annotation(value, value_iri)}

    @staticmethod
    def person(first_name=None, middle_initial=None, last_name=None, email=None):
        ret = {
            "firstName": first_name,
            "middleInitial": middle_initial,
            "lastName": last_name,
            "email": email,
        }
        return AtgxMetaData.remove_none_from_dict(ret)

    @staticmethod
    def type_item(value, value_iri=None):
        ret = {"value": value, "value_iri": value_iri}
        return AtgxMetaData.remove_none_from_dict(ret)


def create_drs_metadata(hdr_meta, sample_meta):
    md = AtgxMetaData()
    extra_properties = []
    dates = []
    types = []

    platform = "Illumina"
    method = ""
    instrument = ""
    for key in sample_meta:
        if sample_meta[key]:
            extra_properties.append(
                AtgxMetaData.extra_properties(key, sample_meta[key])
            )

    for key in hdr_meta:
        extra_properties.append(AtgxMetaData.extra_properties(key, hdr_meta[key]))
        if re.search(r"Date", key, re.IGNORECASE):
            dates.append(AtgxMetaData.date_info(hdr_meta[key], "sequencing"))
        if re.search(r"Application", key, re.IGNORECASE):
            method = hdr_meta[key]
        if re.search(r"Instrument Type", key, re.IGNORECASE):
            instrument = hdr_meta[key]
    types.append(
        AtgxMetaData.data_type(
            platform_value=platform, method_value=method, instr_value=instrument
        )
    )

    md.set_dates(dates)
    md.set_types(types)
    md.set_extra_properties(extra_properties)
    return md.get_dictionary()
