# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from itertools import chain

from .missing import convert_missing_scalar

SKIP_KEYS = {
    "unexpandedDescriptors",
    "shortDelayedDescriptorReplicationFactor",
    "delayedDescriptorReplicationFactor",
    "extendedDelayedDescriptorReplicationFactor",
    "delayedDescriptorAndDataRepetitionFactor",
    "extendedDelayedDescriptorAndDataRepetitionFactorassociatedFieldSignificance",
    "dataPresentIndicator",
    "operator",
}


class UncompressedBufrKey:
    def __init__(self, key, name: str, rank):
        self.key = key
        self.name = name
        self.rank = rank
        self.ranked_name = f"#{rank}#{name}" if rank > 0 else name

    @classmethod
    def from_key(cls, key: str) -> "UncompressedBufrKey":
        rank_text, sep, name = key.rpartition("#")
        try:
            if sep == "#":
                rank = int(rank_text[1:])
            else:
                rank = 1
        except Exception:
            rank = 1

        return cls(key, name, rank)

    def rerank(self, base_rank: int) -> str:
        rel_rank = self.rank - base_rank + 1
        if rel_rank > 0:
            return f"#{rel_rank}#{self.name}"
        else:
            return self.ranked_name


class RefRank:
    def __init__(self, value=-1):
        self.value = value

    def reset(self):
        self.value = -1

    def set(self, value: int):
        if self.value == -1:
            self.value = value


class UncompressedExtractor:
    def __init__(self, base_result, message, subset_count, data_columns, data_filters, add_filters):
        self.message = message
        self.data_columns = data_columns
        self.subset_count = subset_count
        self.base_result = base_result
        self.data_filters = data_filters
        self.add_filters = add_filters

        # create set of all data keys to extract from a given subset
        # contains re-ranked keys
        subset_keys = set()
        ref_rank = {}
        simple_filters = {f.key: f for f in data_filters.values() if not f.column.multi}
        simple_columns = {c.name: c for c in data_columns.values() if not c.multi}

        # setup rank tracker for the keys that need to be collected
        # subset keys contain the ranked keys to collect and also contain the
        # name of the multi-rank keys to collect

        for col in chain([f.column for f in simple_filters.values()], simple_columns.values()):
            for key in col.keys:
                if key not in subset_keys:
                    b = UncompressedBufrKey.from_key(key)
                    subset_keys.add(b.ranked_name)
                    if b.name not in ref_rank:
                        ref_rank[b.name] = RefRank()

        self.subset_keys = subset_keys
        self.ref_rank = ref_rank

        # the multi-rank keys are treated separately. They can only appear in the data filters and
        # are not added to the result since they are not associated with a single value (rank)
        self.multi_rank_filter_keys = [f.name for f in self.data_filters.values() if f.column.multi]
        self.multi_rank_data_keys = [c.name for c in self.data_columns.values() if c.multi]

    def extract(self):
        subset_values = dict()
        multi_rank_data_values = {x: [] for x in self.multi_rank_data_keys}
        multi_rank_filter_values = {x: [] for x in self.multi_rank_filter_keys}

        subset = 0
        for key in self.message:
            # only the data section is processed here

            # start new subset
            if key == "subsetNumber":
                if subset >= 1:
                    current_result = self.generate_subset_result(
                        subset_values, multi_rank_filter_values, multi_rank_data_values
                    )

                    if current_result:
                        yield current_result

                subset += 1
                subset_values.clear()
                multi_rank_filter_values = {x: [] for x in self.multi_rank_filter_keys}
                multi_rank_data_values = {x: [] for x in self.multi_rank_data_keys}

                for x in self.ref_rank.values():
                    x.reset()

            elif subset >= 1:
                self.process_key(key, subset_values, multi_rank_filter_values, multi_rank_data_values)

        # last subset
        current_result = self.generate_subset_result(subset_values, multi_rank_filter_values, multi_rank_data_values)
        if current_result:
            yield current_result

    def process_key(self, key, subset_values, multi_rank_filter_values, multi_rank_data_values):
        def _get_value(key):
            return convert_missing_scalar(self.message.get(key))

        b = UncompressedBufrKey.from_key(key)
        if b.name in self.ref_rank:
            self.ref_rank[b.name].set(b.rank)
            reranked_key = b.rerank(self.ref_rank[b.name].value)
            if reranked_key in self.subset_keys:
                subset_values[reranked_key] = _get_value(key)
        else:
            if b.name in self.multi_rank_data_keys:
                multi_rank_data_values[b.name].append(_get_value(key))
            if b.name in self.multi_rank_filter_keys:
                multi_rank_filter_values[b.name].append(_get_value(key))

    def generate_subset_result(self, subset_values, multi_rank_filter_values, multi_rank_data_values):

        def _get_value_subset(key):
            if key in multi_rank_filter_values:
                return multi_rank_filter_values.get(key)
            elif key in multi_rank_data_values:
                return multi_rank_data_values.get(key)
            else:
                return subset_values.get(key)

        current_result = dict(self.base_result)

        # generate result for previous subset
        matched = True
        matched_keys = {}
        for f in self.data_filters.values():
            match, value = f.match_accessor(_get_value_subset)
            if not match:
                matched = False
                break

            if self.add_filters and not f.column.multi:
                matched_keys[f.key] = value

        if matched:
            for key, c in self.data_columns.items():
                # LOG.debug(f"getting data column key: {key}")
                if not c.multi:
                    if key not in current_result:
                        v = c.get_value(_get_value_subset)
                        current_result[key] = v
                else:
                    for k, v in c.get_ranked_items(_get_value_subset):
                        current_result[k] = v

            if matched_keys:
                current_result.update(matched_keys)

            if current_result:
                # print("yielding:", current_result)
                return dict(current_result)

        return None


class UncompressedExtractorAll:
    def __init__(
        self, base_result, message, subset_count, add_data, data_filters, add_filters, data_required_columns_keys
    ):
        self.message = message
        self.subset_count = subset_count
        self.base_result = base_result
        self.add_data = add_data
        self.data_filters = data_filters
        self.add_filters = add_filters
        self.data_required_columns_keys = data_required_columns_keys

        # create set of all data keys to extract from a given subset
        # contains re-ranked keys
        ref_rank = {}
        simple_filters = {f.key: f for f in self.data_filters.values() if not f.column.multi}

        allowed_keys = set()
        if not self.add_data:
            allowed_keys.update(simple_filters.keys())
            if self.data_required_columns_keys:
                allowed_keys.update(self.data_required_columns_keys)

        self.allowed_keys = allowed_keys
        self.ref_rank = ref_rank

        # the multi-rank keys are treated separately. They can only appear in the data filters and
        # are not added to the result since they are not associated with a single value (rank)
        self.multi_rank_keys = [f.name for f in self.data_filters.values() if f.column.multi]
        if not self.add_data:
            self.allowed_keys.update(self.multi_rank_keys)

    def extract(self):
        subset_values = dict()
        multi_rank_values = {x: [] for x in self.multi_rank_keys}

        subset = 0
        for key in self.message:
            # only the data section is processed here

            # start new subset
            if key == "subsetNumber":
                if subset >= 1:
                    current_result = self.generate_subset_result(subset, subset_values, multi_rank_values)

                    if current_result:
                        yield current_result

                subset += 1
                subset_values.clear()
                multi_rank_values = {x: [] for x in self.multi_rank_keys}

                for x in self.ref_rank.values():
                    x.reset()

            elif subset >= 1:
                self.process_key(key, subset_values, multi_rank_values)

        # last subset
        current_result = self.generate_subset_result(subset, subset_values, multi_rank_values)
        if current_result:
            yield current_result

    def process_key(self, key, subset_values, multi_rank_values):
        # print(f" -> processing key: {key}")
        b = UncompressedBufrKey.from_key(key)

        def _get_value(key):
            return convert_missing_scalar(self.message.get(key))

        if b.name in SKIP_KEYS:
            return

        if self.allowed_keys and not (key in self.allowed_keys or b.name in self.allowed_keys):
            return

        v = _get_value(key)
        # self.ref_rank[b.name].set(b.rank)
        # reranked_key = b.rerank(self.ref_rank[b.name].value)

        if b.name in self.ref_rank:
            self.ref_rank[b.name].set(b.rank)
        else:
            self.ref_rank[b.name] = RefRank(b.rank)
        reranked_key = b.rerank(self.ref_rank[b.name].value)
        subset_values[reranked_key] = v

        if b.name in self.multi_rank_keys:
            multi_rank_values[b.name].append(v)

    def generate_subset_result(self, subset, subset_values, multi_rank_values):

        def _get_value_subset(key):
            if key in multi_rank_values:
                return multi_rank_values.get(key)
            else:
                return subset_values.get(key)

        current_result = dict(self.base_result)

        # generate result for previous subset
        matched = True
        matched_keys = {}
        for f in self.data_filters.values():
            match, value = f.match_accessor(_get_value_subset)
            if not match:
                matched = False
                break

            if self.add_filters and not f.column.multi:
                matched_keys[f.key] = value

        if matched:
            if not self.add_data and matched_keys:
                for k in matched_keys:
                    subset_values.pop(k, None)

            if self.add_data:
                current_result["subsetNumber"] = subset

            current_result.update(subset_values)

            if current_result:
                # print("yielding:", current_result)
                return dict(current_result)

        return None
