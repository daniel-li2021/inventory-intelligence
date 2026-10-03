"""Independent training-access and disjoint frozen-selection controls."""

from copy import deepcopy
from fractions import Fraction
from unittest.mock import patch
import unittest

from scripts.public_calibration_benchmark import training_view, select_disjoint, grid, verify_public, VERSION, sales
from scripts.public_sales_benchmark import TRAIN_END, END, select_items


class TrainingOnlySequence:
    def __init__(self, prefix): self.prefix = prefix
    def __getitem__(self, key):
        if not isinstance(key, slice) or key.start is not None or key.stop != TRAIN_END:
            raise AssertionError("selector attempted to access future observations")
        return self.prefix[:]


class PublicCalibrationOracles(unittest.TestCase):
    def extraction(self):
        values = {'old': [9] * TRAIN_END, 'low': [1] * TRAIN_END,
                  'high': [4] * TRAIN_END, 'zero': [0] * TRAIN_END,
                  'zero2': [0] * TRAIN_END, 'sparse': [1] + [0] * (TRAIN_END - 1)}
        return dict(audit=dict(status='assessable'),
                    series={k: TrainingOnlySequence(v) for k,v in values.items()},
                    source_seen_days={k:['2010-12-01'] for k in values})

    def test_selection_never_accesses_future_quantities_and_keeps_exact_training_features(self):
        adapted = self.extraction()
        # Any access to this future-only item must fail, including training slicing.
        adapted['series']['future'] = object()
        adapted['source_seen_days']['future'] = ['2011-11-11']
        view = training_view(adapted)
        self.assertNotIn('future', view['series'])
        selected = select_disjoint(view, ['old'], limit=4, seed=1709)
        self.assertNotIn('old', selected['selected'])
        self.assertEqual(selected['training_known_items'], 5)
        self.assertEqual(selected['training_volume_median'], TRAIN_END)
        f=selected['features']
        self.assertEqual(f['high']['training_units'], 4*TRAIN_END)
        self.assertEqual(f['high']['positive_day_rate'], 1)
        self.assertEqual(f['high']['bin'], 'dense:high_volume')
        self.assertEqual(f['low']['bin'], 'dense:low_volume')
        self.assertEqual(f['sparse']['positive_day_rate'], Fraction(1,TRAIN_END))
        self.assertEqual(sum(k.startswith('zero') for k in selected['selected']), 1)
        self.assertEqual(selected, select_disjoint(view, ['old'], limit=4, seed=1709))

    def test_consumed_subset_hash_reconstructs_without_reading_future_outcomes(self):
        view=training_view(self.extraction())
        full=deepcopy(view)
        for values in full['series'].values(): values[TRAIN_END:] = [999999]*(END+1-TRAIN_END)
        self.assertEqual(select_items(view), select_items(full))
        guarded=training_view(self.extraction())
        self.assertEqual(select_items(view), select_items(guarded))

    def test_exclusion_identity_and_incomplete_inputs_fail_closed(self):
        view=training_view(self.extraction())
        for excluded in ([],['old','old'],['missing']):
            with self.assertRaises(ValueError): select_disjoint(view, excluded, limit=1)
        with self.assertRaises(ValueError): select_disjoint(view, ['old'], limit=5)
        adapted=self.extraction(); adapted['audit']['status']='not_assessable'
        with self.assertRaises(ValueError): training_view(adapted)
        adapted=self.extraction(); adapted['series']['low']=TrainingOnlySequence([1])
        with self.assertRaises(ValueError): training_view(adapted)

    def test_grid_has_exact_frozen_denominators_without_added_models(self):
        configs=grid()
        self.assertEqual(len(configs),24)
        self.assertEqual({v['method'] for v in configs.values()},{'mean','sba'})
        self.assertEqual(sum(v['quantile'] is not None for v in configs.values()),16)
        self.assertEqual({v['lead_days'] for v in configs.values()},{2,5})
        self.assertEqual({v['delay'] for v in configs.values()},{0,3})
        self.assertEqual(32*len(configs),768)

    def test_semantic_metadata_mutations_are_rejected_even_after_rehashing(self):
        manifest=dict(source_sha256={},subset_sha256='new',excluded_subset_sha256='old',
                      selected_bin_counts={'zero':1},dates={'holdout_days':28})
        public=dict(protocol_version=VERSION,freeze_sha256='hash',source_sha256={},
            subset_sha256='new',excluded_subset_sha256='old',selected_items=32,excluded_items=32,
            overlap_items=0,selected_bin_counts={'zero':1},dates=manifest['dates'],configurations=grid(),
            arms=768,paired_contrasts=512,observed_sales_only=True,availability='unknown',
            unconstrained_demand='unknown',attribution=sales.ATTRIBUTION,
            source_url=sales.SOURCE_URL,license_url=sales.LICENSE_URL)
        with patch('scripts.public_calibration_benchmark.sales.sha256_file',return_value='hash'):
            verify_public(public,manifest)
            for change in (dict(observed_sales_only=False),dict(unconstrained_demand='known'),
                           dict(selected_items=31),dict(overlap_items=1),dict(configurations={}),
                           dict(subset_sha256='old'),dict(dates={'holdout_days':29})):
                with self.assertRaisesRegex(ValueError,'semantic boundary'):
                    verify_public(dict(public,**change),manifest)


if __name__=='__main__': unittest.main()
